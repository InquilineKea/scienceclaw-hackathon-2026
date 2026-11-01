const $=id=>document.getElementById(id),el=(t,c,txt)=>{let e=document.createElement(t);if(c)e.className=c;if(txt!==undefined)e.textContent=txt;return e};

export function attachDemoInspector({THREE,scene,camera,controls,renderer,getState,markDirty}){
  if(!scene||!camera||!renderer)return {update(){},dispose(){}};
  let selectedNode=null,isolate=false,clipAxis='none',clipVal=0.5,disposed=false;
  const clipPlane=new THREE.Plane(new THREE.Vector3(-1,0,0),100);
  const overlayGroup=new THREE.Group();
  overlayGroup.name='inspectorOverlay';
  scene.add(overlayGroup);

  const rot=$('rotate');
  if(rot){rot.checked=false;if(controls)controls.autoRotate=false;}
  if(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches){
    const mag=$('magnify');if(mag&&mag.value==='5')mag.value='1';
  }

  const stage=$('stage');
  const camBar=el('div','di-cam-bar');
  camBar.setAttribute('role','toolbar');
  camBar.setAttribute('aria-label','3D Camera Presets');
  const presets=[
    ['Iso','Isometric view',[1.55,0.95,2.45]],
    ['+X','Along tension axis X',[3.1,0.15,0.15]],
    ['XY','XY plane view',[0,0,3.2]],
    ['XZ','XZ plane view',[0,3.2,0.01]],
    ['Fit','Fit selected or network','fit'],
    ['Reset','Reset camera','reset']
  ];
  presets.forEach(([lbl,title,pos])=>{
    let b=el('button','di-btn',lbl);b.title=title;b.type='button';
    b.onclick=()=>setCam(pos);
    camBar.append(b);
  });
  stage?.append(camBar);

  const panel=el('section','di-panel');
  panel.setAttribute('aria-label','3D Fiber and Junction Inspector');
  panel.innerHTML=`
    <div class="di-head"><span>04 / 3D GEOMETRY & JUNCTION INSPECTOR</span><span id="diQualBadge" class="di-badge"></span></div>
    <div class="di-controls-row">
      <label>Fiber <select id="diFiberSel"><option value="">None</option></select></label>
      <label>Junction <select id="diNodeSel"><option value="">None</option></select></label>
      <label class="di-chk"><input type="checkbox" id="diIsolate"> Isolate selection &amp; neighbors</label>
      <label>Slice <select id="diClipAxis"><option value="none">Off</option><option value="x">X axis</option><option value="y">Y axis</option><option value="z">Z axis</option></select></label>
      <input type="range" id="diClipSlider" min="0" max="1" step="0.02" value="0.5" aria-label="Slice plane position" hidden>
    </div>
    <div class="di-cards">
      <div class="di-card" id="diFiberCard"></div>
      <div class="di-card" id="diNodeCard"></div>
    </div>
    <p class="di-legend"><strong>Note:</strong> Numerics use unmagnified equilibrium coordinates. Tube colors show axial stretch force only; bending, twist, and junction rotational restraint energies are not stored per-segment in preview frames. Inter-fiber angles reflect idealized rod tangents at shared nodes, not molecular bond angles.</p>
  `;
  stage?.parentElement?.append(panel);

  const fSel=$('diFiberSel'),nSel=$('diNodeSel'),isoChk=$('diIsolate'),cAxis=$('diClipAxis'),cSlide=$('diClipSlider'),fCard=$('diFiberCard'),nCard=$('diNodeCard'),qBadge=$('diQualBadge');

  fSel.onchange=()=>{
    let v=fSel.value===''?null:+fSel.value;
    getState().setSelectedFiber(v);
    update();
  };
  nSel.onchange=()=>{
    selectedNode=nSel.value===''?null:+nSel.value;
    markDirty();
    update();
  };
  isoChk.onchange=()=>{isolate=isoChk.checked;markDirty();update();};
  cAxis.onchange=()=>{
    clipAxis=cAxis.value;
    cSlide.hidden=clipAxis==='none';
    applyClipping();
    markDirty();
    update();
  };
  cSlide.oninput=()=>{
    clipVal=+cSlide.value;
    applyClipping();
    markDirty();
    update();
  };

  const ray=new THREE.Raycaster(),ptr=new THREE.Vector2();
  let downPt=null;
  const dom=renderer.domElement;
  const onDown=e=>{downPt=[e.clientX,e.clientY];};
  const onUp=e=>{
    if(disposed||!downPt||Math.hypot(e.clientX-downPt[0],e.clientY-downPt[1])>5)return;
    const rect=dom.getBoundingClientRect();
    ptr.set(((e.clientX-rect.left)/rect.width)*2-1,-((e.clientY-rect.top)/rect.height)*2+1);
    ray.setFromCamera(ptr,camera);
    const nodeGroup=scene.children.find(c=>c.isGroup&&c!==overlayGroup&&c.children[0]?.geometry?.type==='SphereGeometry');
    if(nodeGroup){
      const hits=ray.intersectObjects(nodeGroup.children,false);
      if(hits.length){
        const idx=nodeGroup.children.indexOf(hits[0].object);
        if(idx>=0){selectedNode=idx;nSel.value=String(idx);markDirty();update();return;}
      }
    }
    setTimeout(update,0);
  };
  dom.addEventListener('pointerdown',onDown);
  dom.addEventListener('pointerup',onUp);

  const curveCv=$('curve');
  let scrubbing=false;
  const scrub=e=>{
    const st=$('strain');if(!st||!curveCv)return;
    const r=curveCv.getBoundingClientRect(),x=e.clientX-r.left,w=r.width;
    const frac=Math.max(0,Math.min(1,(x-38)/Math.max(1,w-48)));
    st.value=(frac*(+st.max||4)).toFixed(2);
    st.dispatchEvent(new Event('input'));
  };
  if(curveCv){
    curveCv.style.cursor='ew-resize';
    curveCv.title='Click or drag to scrub applied strain';
    curveCv.addEventListener('pointerdown',e=>{scrubbing=true;scrub(e);});
    window.addEventListener('pointermove',e=>{if(scrubbing)scrub(e);});
    window.addEventListener('pointerup',()=>{scrubbing=false;});
  }

  function setCam(mode){
    const st=getState(),L=st.record?.model?.L||1,mag=st.magnification||1,strain=st.sample?.strain||0;
    if(!controls)return;
    if(mode==='reset'){
      camera.position.set(L*1.6,L*0.9,L*2.6);
      controls.target.set(0,0,0);
    }else if(mode==='fit'){
      let target=new THREE.Vector3(0,0,0),dist=L*2.6;
      if(selectedNode!==null&&st.sample?.positions[selectedNode]){
        target.copy(dispPos(st.record,st.sample,selectedNode,mag));
        dist=L*1.1;
      }else if(st.selectedFiber!==null){
        const ch=st.record.chains.find(c=>c.fiber===st.selectedFiber);
        if(ch){
          const pts=chainDispPts(st.record,st.sample,ch,mag);
          pts.forEach(p=>target.add(p));
          target.divideScalar(pts.length||1);
          dist=L*1.45;
        }
      }
      const dir=camera.position.clone().sub(controls.target).normalize();
      if(dir.lengthSq()<1e-6)dir.set(0.5,0.3,0.8).normalize();
      controls.target.copy(target);
      camera.position.copy(target).addScaledVector(dir,dist*(1+0.15*mag*strain));
    }else if(Array.isArray(mode)){
      controls.target.set(0,0,0);
      camera.position.set(mode[0]*L,mode[1]*L,mode[2]*L);
    }
    controls.update();
    markDirty();
    renderer.render(scene,camera);
  }

  function applyClipping(){
    const st=getState(),L=st.record?.model?.L||1,mag=st.magnification||1,strain=st.sample?.strain||0;
    if(clipAxis==='none'){
      renderer.localClippingEnabled=false;
      renderer.clippingPlanes=[];
      return;
    }
    renderer.localClippingEnabled=true;
    const span=L*(clipAxis==='x'?1+mag*strain:1)*1.2;
    const offset=(clipVal-0.5)*span;
    clipPlane.normal.set(clipAxis==='x'?-1:0,clipAxis==='y'?-1:0,clipAxis==='z'?-1:0);
    clipPlane.constant=offset;
    renderer.clippingPlanes=[clipPlane];
  }

  function dispPos(rec,samp,id,mag,shift=[0,0,0]){
    const L=rec.model.L,center=[L*(1+mag*samp.strain)/2,L/2,L/2];
    const ref=rec.restPositions[id].slice(),p=samp.positions[id].slice();
    for(let k=0;k<3;k++){ref[k]+=shift[k];p[k]+=shift[k]*(k===0?1+samp.strain:1);}
    return new THREE.Vector3(...ref.map((v,k)=>v+mag*(p[k]-v)-center[k]));
  }

  function chainDispPts(rec,samp,chain,mag){
    return chain.ids.map((id,j)=>dispPos(rec,samp,id,mag,j===chain.ids.length-1?chain.shift:[0,0,0]));
  }

  function chainRealPts(posArray,strain,chain){
    return chain.ids.map((id,j)=>{
      const p=posArray[id].slice();
      if(j===chain.ids.length-1)for(let k=0;k<3;k++)p[k]+=chain.shift[k]*(k===0?1+strain:1);
      return new THREE.Vector3(...p);
    });
  }

  function metricsForChain(rec,samp,chain){
    const restPts=chainRealPts(rec.restPositions,0,chain);
    const curPts=chainRealPts(samp.positions,samp.strain,chain);
    const len=pts=>{let s=0;for(let i=1;i<pts.length;i++)s+=pts[i].distanceTo(pts[i-1]);return s;};
    const Lc0=len(restPts),Lc=len(curPts);
    const Lx0=restPts[0].distanceTo(restPts.at(-1)),Lx=curPts[0].distanceTo(curPts.at(-1));
    const slack0=Math.max(0,Lc0-Lx0),slack=Math.max(0,Lc-Lx);
    const recruited=slack0>1e-9?Math.max(0,Math.min(1,(slack0-slack)/slack0)):1;
    const forces=chain.bids.map(b=>samp.segmentForces[b]||0);
    const peak=forces.reduce((m,v)=>Math.abs(v)>Math.abs(m)?v:m,0);
    return {Lc0,Lc,Lx0,Lx,crimp0:Lc0/Math.max(1e-9,Lx0),crimp:Lc/Math.max(1e-9,Lx),recruited,forces,peak,endA:chain.ids[0],endB:chain.ids.at(-1),shift:chain.shift};
  }

  function nodeInfo(rec,samp,nodeId){
    const incident=[];
    rec.chains.forEach(c=>{
      if(c.ids[0]===nodeId){
        const p0=new THREE.Vector3(...rec.restPositions[nodeId]),p1=new THREE.Vector3(...rec.restPositions[c.ids[1]]);
        const q0=new THREE.Vector3(...samp.positions[nodeId]),q1=new THREE.Vector3(...samp.positions[c.ids[1]]);
        incident.push({fiber:c.fiber,other:c.ids.at(-1),shift:c.shift,v0:p1.sub(p0).normalize(),v1:q1.sub(q0).normalize()});
      }
      if(c.ids.at(-1)===nodeId){
        const n=c.ids.length,sh=c.shift;
        const p0=new THREE.Vector3(...rec.restPositions[nodeId].map((x,k)=>x+sh[k]));
        const p1=new THREE.Vector3(...rec.restPositions[c.ids[n-2]]);
        const q0=new THREE.Vector3(...samp.positions[nodeId].map((x,k)=>x+sh[k]*(k===0?1+samp.strain:1)));
        const q1=new THREE.Vector3(...samp.positions[c.ids[n-2]]);
        incident.push({fiber:c.fiber,other:c.ids[0],shift:sh.map(x=>-x),v0:p1.sub(p0).normalize(),v1:q1.sub(q0).normalize()});
      }
    });
    const angles=[];
    for(let i=0;i<incident.length;i++){
      for(let j=i+1;j<incident.length;j++){
        const a0=Math.acos(Math.max(-1,Math.min(1,incident[i].v0.dot(incident[j].v0))))*180/Math.PI;
        const a1=Math.acos(Math.max(-1,Math.min(1,incident[i].v1.dot(incident[j].v1))))*180/Math.PI;
        angles.push({fA:incident[i].fiber,fB:incident[j].fiber,a0,a1,da:a1-a0});
      }
    }
    return {incident,angles};
  }

  let lastRecIndex=null;
  function syncDropdowns(rec){
    if(rec.index===lastRecIndex)return;
    lastRecIndex=rec.index;
    fSel.replaceChildren(el('option','','None (click or select)'));
    rec.chains.forEach(c=>{
      const o=el('option','',`Fiber #${c.fiber} (J${c.ids[0]}→J${c.ids.at(-1)})`);
      o.value=String(c.fiber);fSel.append(o);
    });
    nSel.replaceChildren(el('option','','None (click or select)'));
    for(let i=0;i<rec.model.positions.length;i++){
      const o=el('option','',`Junction J${i}`);
      o.value=String(i);nSel.append(o);
    }
    if(selectedNode!==null&&selectedNode>=rec.model.positions.length)selectedNode=null;
  }

  function clearOverlay(){
    for(let o of [...overlayGroup.children]){
      overlayGroup.remove(o);
      o.geometry?.dispose();
      o.material?.dispose();
    }
  }

  function update(){
    if(disposed)return;
    const st=getState(),rec=st.record,samp=st.sample,selF=st.selectedFiber,mag=st.magnification||1;
    if(!rec||!samp)return;
    syncDropdowns(rec);
    fSel.value=selF===null?'':String(selF);
    nSel.value=selectedNode===null?'':String(selectedNode);

    const fFrame=rec.frames.at(-1);
    const ratio=fFrame?fFrame.residual/fFrame.tolerance:0;
    const ok=rec.status==='complete'&&rec.frames.every(f=>f.accepted);
    qBadge.textContent=`${ok?'Accepted equilibria':'Unresolved'} · Residual/tolerance ${ratio.toFixed(3)}× · Motion ${mag}× (${samp.exact?'exact frame':'interpolated'})`;
    qBadge.className='di-badge'+(ok&&ratio>=20?'':' warn');

    clearOverlay();
    const L=rec.model.L;
    const activeFibers=new Set(),activeNodes=new Set();
    if(selF!==null){
      activeFibers.add(selF);
      const ch=rec.chains.find(c=>c.fiber===selF);
      if(ch){activeNodes.add(ch.ids[0]);activeNodes.add(ch.ids.at(-1));}
    }
    if(selectedNode!==null){
      activeNodes.add(selectedNode);
      rec.chains.forEach(c=>{
        if(c.ids[0]===selectedNode||c.ids.at(-1)===selectedNode){
          activeFibers.add(c.fiber);
          activeNodes.add(c.ids[0]);activeNodes.add(c.ids.at(-1));
        }
      });
    }

    const groups=scene.children.filter(c=>c.isGroup&&c!==overlayGroup);
    const netGroup=groups.find(g=>g.children[0]?.userData?.fiber!==undefined);
    const ndGroup=groups.find(g=>g.children[0]?.geometry?.type==='SphereGeometry');

    if(netGroup){
      netGroup.children.forEach(mesh=>{
        const fid=mesh.userData.fiber;
        if(isolate&&(selF!==null||selectedNode!==null)){
          mesh.material.opacity=activeFibers.has(fid)?1:0.06;
        }
      });
    }
    if(ndGroup){
      ndGroup.children.forEach((mesh,idx)=>{
        mesh.material.transparent=true;
        mesh.material.opacity=isolate&&(selF!==null||selectedNode!==null)?(activeNodes.has(idx)?1:0.12):1;
      });
    }

    if(selF!==null){
      const ch=rec.chains.find(c=>c.fiber===selF);
      if(ch){
        const pts=chainDispPts(rec,samp,ch,mag);
        const curve=new THREE.CatmullRomCurve3(pts,false,'centripetal');
        const geo=new THREE.TubeGeometry(curve,36,0.0135*L,8,false);
        const mat=new THREE.MeshBasicMaterial({color:'#ffe49e',wireframe:true,transparent:true,opacity:0.65,depthWrite:false});
        overlayGroup.add(new THREE.Mesh(geo,mat));
        const m=metricsForChain(rec,samp,ch);
        const per=m.shift.some(x=>x!==0)?`Periodic shift (${m.shift.join(',')})`:'Central cell';
        fCard.innerHTML=`
          <h4>Selected Fiber #${selF} <button type="button" class="di-mini" id="diClearF">Clear</button></h4>
          <div class="di-grid">
            <div><span>Endpoints</span><strong><a href="#" data-node="${m.endA}">J${m.endA}</a> → <a href="#" data-node="${m.endB}">J${m.endB}</a></strong><small>${per}</small></div>
            <div><span>Peak axial force</span><strong>${m.peak.toExponential(3)}</strong><small>${m.peak>=0?'Tension (+)':'Compression (−)'}</small></div>
            <div><span>Chord length (L<sub>x</sub>)</span><strong>${m.Lx.toFixed(4)}</strong><small>Rest: ${m.Lx0.toFixed(4)} (${((m.Lx/m.Lx0-1)*100).toFixed(2)}%)</small></div>
            <div><span>Contour length (L<sub>c</sub>)</span><strong>${m.Lc.toFixed(4)}</strong><small>Rest: ${m.Lc0.toFixed(4)} (${((m.Lc/m.Lc0-1)*100).toFixed(2)}%)</small></div>
            <div><span>Tortuosity (L<sub>c</sub>/L<sub>x</sub>)</span><strong>${m.crimp.toFixed(4)}</strong><small>Rest: ${m.crimp0.toFixed(4)}</small></div>
            <div><span>Slack recruitment</span><strong>${(m.recruited*100).toFixed(1)}%</strong><small>Unmagnified geometric uncrimping</small></div>
          </div>
          <div class="di-segs"><span>Segment axial forces (4 segments):</span> ${m.forces.map((f,i)=>`<code>S${i+1}: ${f.toExponential(2)}</code>`).join(' ')}</div>
        `;
        $('diClearF').onclick=()=>{getState().setSelectedFiber(null);update();};
        fCard.querySelectorAll('[data-node]').forEach(a=>a.onclick=e=>{e.preventDefault();selectedNode=+a.dataset.node;markDirty();update();});
      }
    }else{
      fCard.innerHTML=`<h4>Fiber Inspector</h4><p class="di-empty">Click any fiber tube in 3D or choose from the dropdown above to inspect unmagnified chord vs. contour length, crimp recruitment, endpoints, and 4-segment axial forces.</p>`;
    }

    if(selectedNode!==null&&rec.model.positions[selectedNode]){
      const pos=dispPos(rec,samp,selectedNode,mag);
      const ring=new THREE.Mesh(new THREE.SphereGeometry(0.032*L,14,12),new THREE.MeshBasicMaterial({color:'#ffcf70',wireframe:true,transparent:true,opacity:0.85}));
      ring.position.copy(pos);
      overlayGroup.add(ring);
      const info=nodeInfo(rec,samp,selectedNode);
      const r0=rec.restPositions[selectedNode],r1=samp.positions[selectedNode];
      const disp=Math.hypot(r1[0]-r0[0],r1[1]-r0[1],r1[2]-r0[2]);
      const angRows=info.angles.slice(0,6).map(a=>`<tr><td>F#${a.fA}–F#${a.fB}</td><td>${a.a0.toFixed(1)}°</td><td>${a.a1.toFixed(1)}°</td><td>${(a.da>=0?'+':'')+a.da.toFixed(1)}°</td></tr>`).join('');
      nCard.innerHTML=`
        <h4>Selected Junction J${selectedNode} <button type="button" class="di-mini" id="diClearN">Clear</button></h4>
        <div class="di-grid">
          <div><span>Degree</span><strong>${info.incident.length} connected fibers</strong><small>Restraint J = ${rec.settings?.junctionK??0}</small></div>
          <div><span>Unmagnified |u|</span><strong>${disp.toFixed(4)}</strong><small>Pos: (${r1.map(x=>x.toFixed(2)).join(', ')})</small></div>
        </div>
        <div class="di-segs"><span>Connected fibers:</span> ${info.incident.map(x=>`<a href="#" class="di-pill" data-fib="${x.fiber}">F#${x.fiber} → J${x.other}</a>`).join(' ')}</div>
        ${info.angles.length?`<table class="di-ang-tbl"><thead><tr><th>Pair (rod tangents)</th><th>Rest θ</th><th>Curr θ</th><th>Δθ</th></tr></thead><tbody>${angRows}</tbody></table>`:'<p class="di-empty">Single-fiber terminal node; no inter-fiber pair angle.</p>'}
      `;
      $('diClearN').onclick=()=>{selectedNode=null;markDirty();update();};
      nCard.querySelectorAll('[data-fib]').forEach(a=>a.onclick=e=>{e.preventDefault();getState().setSelectedFiber(+a.dataset.fib);update();});
    }else{
      nCard.innerHTML=`<h4>Junction (Node) Inspector</h4><p class="di-empty">Click a junction sphere in 3D or select a node above to inspect connected neighbor fibers and resting vs. deformed inter-fiber tangent angles.</p>`;
    }

    if(! $('fallback')?.disabled)renderer.render(scene,camera);
  }

  function dispose(){
    disposed=true;
    dom.removeEventListener('pointerdown',onDown);
    dom.removeEventListener('pointerup',onUp);
    clearOverlay();
    scene.remove(overlayGroup);
    renderer.localClippingEnabled=false;
    renderer.clippingPlanes=[];
    camBar.remove();
    panel.remove();
  }

  update();
  return {update,dispose};
}
