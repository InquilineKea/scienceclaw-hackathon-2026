'use strict';
(function(){
 const M=globalThis.CollagenAtlas,A=globalThis.AtlasDirectional,D=globalThis.ATLAS_DIRECTIONAL_DATA,$=id=>document.getElementById(id);
 const names={aligned:'Aligned bundles',isotropic:'Disordered',hierarchical:'Hierarchical',modular:'Modular',loops:'Loop-rich geometry',bottleneck:'Bottlenecked',heterogeneous:'Degree heterogeneous'};
 const colors={aligned:'#b65a35',isotropic:'#427e6a',hierarchical:'#a58540',modular:'#7d699c',loops:'#4c83ac',bottleneck:'#8b685c',heterogeneous:'#bb5d81'};
 const format=v=>Number.isFinite(v)?Number(v.toPrecision(3)).toString():'—';
 let worker=null,result=null,loading=false,serial=0;
 const params=new URLSearchParams(location.search),rawAngle=Number(params.get('angle'));
 $('loadAngle').value=Number.isFinite(rawAngle)?Math.max(0,Math.min(180,rawAngle)):0;
 for(const f of M.families){const o=document.createElement('option');o.value=f;o.textContent=names[f];$('angleFamily').append(o);}
 $('angleFamily').value=M.families.includes(params.get('network'))?params.get('network'):'aligned';
 if(['17','29','43','mean'].includes(params.get('directionSeed')))$('angleSeed').value=params.get('directionSeed');
 function surface(id){const el=$(id),r=el.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2),w=r.width,h=r.height;el.width=Math.round(w*d);el.height=Math.round(h*d);const c=el.getContext('2d');c.scale(d,d);return{c,w,h};}
 function selectedSeeds(){return $('angleSeed').value==='mean'?D.seeds:[Number($('angleSeed').value)];}
 function aggregate(family,angle,key){
  const seeds=selectedSeeds(),rows=D.rows.filter(r=>r.family===family&&r.angle===angle&&seeds.includes(r.seed));
  const valid=rows.length===seeds.length&&rows.every(r=>key==='stiffness'?r.stiffnessValid:r.valid);
  const values=rows.map(r=>r[key]),value=values.reduce((s,v)=>s+v,0)/values.length;
  const sd=values.length>1?Math.sqrt(values.reduce((s,v)=>s+(v-value)**2,0)/(values.length-1)):0;
  return{value,sd,valid,capped:key==='work'&&rows.some(r=>r.censored),count:rows.length};
 }
 function plot(id,key){
  const{c,w,h}=surface(id),pad={l:58,r:18,t:24,b:39},angles=[...D.angles,180],all=M.families.flatMap(f=>D.angles.map(a=>aggregate(f,a,key))),max=Math.max(...all.filter(p=>p.valid).map(p=>p.value+p.sd))*1.08||1;
  const x=a=>pad.l+a/180*(w-pad.l-pad.r),y=v=>h-pad.b-v/max*(h-pad.t-pad.b);c.font='10px system-ui';c.fillStyle='#64736e';c.strokeStyle='#dce2da';
  for(let i=0;i<=4;i++){const v=i*max/4,Y=y(v);c.beginPath();c.moveTo(pad.l,Y);c.lineTo(w-pad.r,Y);c.stroke();c.fillText(format(v*1000),3,Y+3);}
  for(let a=0;a<=180;a+=30)c.fillText(a+'°',x(a)-9,h-19);c.fillText('Loading direction θ (0° = X; 90° = Y)',pad.l,h-3);c.fillText(key==='stiffness'?'Kθ / E₀ × 10³':'Wθ / E₀ × 10³',pad.l,12);
  for(const family of M.families){
   const highlighted=family===$('angleFamily').value;c.strokeStyle=colors[family];c.fillStyle=colors[family];c.lineWidth=highlighted?2.8:1.2;c.globalAlpha=highlighted?1:.62;
   let previous=null;
   for(const a of angles){const p=aggregate(family,a===180?0:a,key);
    if(!p.valid){previous=null;continue;}
    const X=x(a),Y=y(p.value);
    if(previous&&!p.capped&&!previous.p.capped){c.beginPath();c.moveTo(previous.X,previous.Y);c.lineTo(X,Y);c.stroke();}
    if(highlighted&&p.sd){c.lineWidth=.8;c.beginPath();c.moveTo(X,y(Math.max(0,p.value-p.sd)));c.lineTo(X,y(p.value+p.sd));c.moveTo(X-3,y(p.value+p.sd));c.lineTo(X+3,y(p.value+p.sd));c.moveTo(X-3,y(Math.max(0,p.value-p.sd)));c.lineTo(X+3,y(Math.max(0,p.value-p.sd)));c.stroke();c.lineWidth=2.8;}
    c.beginPath();c.arc(X,Y,p.capped?4:highlighted?3:1.7,0,2*Math.PI);if(p.capped){c.fillStyle='#f4f3ee';c.fill();c.stroke();c.fillStyle=colors[family];}else c.fill();previous={X,Y,p};
   }
  }
  c.globalAlpha=1;c.strokeStyle='#1d302e';c.setLineDash([4,4]);c.beginPath();c.moveTo(x(Number($('loadAngle').value)),pad.t);c.lineTo(x(Number($('loadAngle').value)),h-pad.b);c.stroke();c.setLineDash([]);
 }
 function table(){
  const a=Math.round(Number($('loadAngle').value)/15)*15,angle=a===180?0:a;
  let html='<table><caption>Sampled directions every 15° · '+($('angleSeed').value==='mean'?'mean of seeds 17, 29, 43':'seed '+$('angleSeed').value)+'</caption><thead><tr><th>Network</th><th>K at '+a+'° × 10³</th><th>K max/min</th><th>W at '+a+'° × 10³</th><th>W max/min</th></tr></thead><tbody>';
  for(const family of M.families){const k=D.angles.map(a=>aggregate(family,a,'stiffness')),v=D.angles.map(a=>aggregate(family,a,'work')),kp=aggregate(family,angle,'stiffness'),wp=aggregate(family,angle,'work'),ratio=points=>points.every(p=>p.valid&&!p.capped)&&Math.min(...points.map(p=>p.value))>0?format(Math.max(...points.map(p=>p.value))/Math.min(...points.map(p=>p.value))):'unresolved';html+='<tr'+(family===$('angleFamily').value?' class="angle-selected"':'')+'><th>'+names[family]+'</th><td>'+(kp.valid?format(kp.value*1000):'invalid')+'</td><td>'+ratio(k)+'</td><td>'+(wp.valid?format(wp.value*1000)+(wp.capped?' †':''):'invalid')+'</td><td>'+ratio(v)+'</td></tr>';}
  $('directionTable').innerHTML=html+'</tbody></table>';
 }
 function drawNetwork(){
  const{c,w,h}=surface('angleNetwork'),net=result?.net||M.build($('angleFamily').value,17),angle=Number($('loadAngle').value),b=A.boundary(net,angle,.1),frame=result&&!loading?result.frames[Math.round(Number($('angleReplay').value)/1000*(result.frames.length-1))]:null,X=frame?.x||net.X;
  const sc=Math.min(w-90,h-60)/2,px=x=>w/2+(x-.5)*sc,py=y=>h/2-(y-.5)*sc;
  const maxForce=Math.max(1e-8,...(frame?.forces||[]).map(Math.abs));c.lineWidth=1;
  net.edges.forEach((e,k)=>{const alive=frame?.alive[k]??true,f=frame?.forces[k]||0;c.strokeStyle=!alive?'#d56c7b':f<0?'#76b4df':'#e4b075';c.globalAlpha=alive?.45+.55*Math.min(1,Math.abs(f)/maxForce):.5;c.setLineDash(alive?[]:[3,3]);c.lineWidth=alive?1+2*Math.abs(f)/maxForce:1;c.beginPath();c.moveTo(px(X[2*e.i]),py(X[2*e.i+1]));c.lineTo(px(X[2*e.j]),py(X[2*e.j+1]));c.stroke();});c.setLineDash([]);c.globalAlpha=1;
  for(const i of b.nodes){const x=px(X[2*i]),y=py(X[2*i+1]);c.fillStyle='#8bd9df';c.fillRect(x-2,y-2,4,4);const dx=b.deriv.get(2*i),dy=b.deriv.get(2*i+1),L=Math.hypot(dx,dy);if(L>1e-9){const xx=x+dx/L*17,yy=y-dy/L*17,a=Math.atan2(-dy,dx);c.strokeStyle='#b6dd8e';c.lineWidth=1.5;c.beginPath();c.moveTo(x,y);c.lineTo(xx,yy);c.moveTo(xx-4*Math.cos(a-.5),yy-4*Math.sin(a-.5));c.lineTo(xx,yy);c.lineTo(xx-4*Math.cos(a+.5),yy-4*Math.sin(a+.5));c.stroke();}}
  c.font='11px system-ui';c.fillStyle='#cbdcc8';c.fillText('X →',w-45,h-14);c.fillText('Y ↑',14,20);
  $('angleFrame').textContent=frame?'ε = '+frame.q.toFixed(4)+' · damaged volume '+(frame.damage*100).toFixed(1)+'%':'Reference geometry · boundary arrows show displacement direction';
 }
 function refresh(){
  $('angleOutput').textContent=$('loadAngle').value+'°';$('angleOutput').value=$('loadAngle').value+'°';plot('angleStiffness','stiffness');plot('angleWork','work');table();drawNetwork();
 }
 function compute(){
  const id=++serial;if(worker)worker.terminate();result=null;loading=true;$('angleReplay').disabled=true;$('exportDirection').disabled=true;$('angleStatus').textContent='Computing '+names[$('angleFamily').value]+' at '+$('loadAngle').value+'°…';
  drawNetwork();worker=new Worker('directional-worker.js');
  worker.onmessage=({data})=>{if(id!==serial)return;worker.terminate();worker=null;loading=false;if(data.error){$('angleStatus').textContent='Computation failed: '+data.error;return;}result=data;$('angleReplay').value=400;$('angleReplay').disabled=false;$('exportDirection').disabled=false;
   const m=data.metrics;$('angleStatus').textContent=names[data.net.family]+' · seed '+data.net.seed+' · θ = '+data.angle+'° · K × 10³ = '+format(m.stiffness*1000)+' · W × 10³ = '+format(m.work*1000)+' · '+m.criterion+'.'+(!m.valid?' Invalid equilibrium; do not interpret work.':'')+(m.censored?' † Capped work; failure toughness unresolved.':'');drawNetwork();};
  worker.onerror=()=>{loading=false;$('angleStatus').textContent='The browser worker could not finish. The saved directional curves are still available.';worker?.terminate();worker=null;};
  worker.postMessage({family:$('angleFamily').value,seed:$('angleSeed').value==='mean'?17:Number($('angleSeed').value),angle:Number($('loadAngle').value)});
 }
 $('loadAngle').oninput=()=>{if(worker){worker.terminate();worker=null;++serial;}loading=true;$('angleReplay').disabled=true;$('exportDirection').disabled=true;$('angleStatus').textContent='Release the slider to solve this direction.';refresh();};$('loadAngle').onchange=compute;
 $('angleFamily').onchange=()=>{refresh();compute();};$('angleSeed').onchange=()=>{refresh();compute();};$('angleReplay').oninput=drawNetwork;
 $('shareDirection').onclick=async()=>{const u=new URL(location.href);u.search='';u.searchParams.set('angle',$('loadAngle').value);u.searchParams.set('network',$('angleFamily').value);u.searchParams.set('directionSeed',$('angleSeed').value);u.hash='direction';try{await navigator.clipboard.writeText(u.href);$('angleStatus').textContent='Directional comparison link copied.';}catch{$('angleStatus').textContent=u.href;}};
 $('exportDirection').onclick=()=>{if(!result||loading)return;const blob=new Blob([JSON.stringify({modelHash:D.modelHash,directionalHash:D.directionalHash,protocol:D.protocol,result},null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='fracture-atlas-direction-'+result.angle+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
 $('directionLegend').innerHTML=M.families.map(f=>'<span><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4" fill="'+colors[f]+'"/></svg>'+names[f]+'</span>').join('');
 const dwork=D.checks.filter(r=>r.label==='half load step'),dtol=D.checks.filter(r=>r.label==='tighter tolerance');$('directionChecks').textContent=D.rows.length+' runs · '+D.seeds.length+' seeds · 12 directions (0°–165°); 180° repeats 0°. '+D.rows.filter(r=>!r.valid).length+' unconverged runs; '+D.rows.filter(r=>r.censored).length+' capped runs. In 9 spot checks, halving the load step changed work by up to '+format(Math.max(...dwork.map(r=>Math.abs(r.workRelativeChange)))*100)+'%; tightening the force tolerance changed stiffness by up to '+format(Math.max(...dtol.map(r=>Math.abs(r.stiffnessRelativeChange)))*100)+'%. These are numerical checks, not biological validation.';
 window.addEventListener('resize',refresh);requestAnimationFrame(()=>{refresh();compute();});
})();
