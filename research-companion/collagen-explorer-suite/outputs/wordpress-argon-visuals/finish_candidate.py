"""Integrate the reviewed complete Argon camera draft; never execute page scripts."""
from pathlib import Path
import re
P=Path(__file__).resolve().parent
S=P/'snapshot/docs'; C=P/'candidate/docs'

def replace(text, old, new):
    assert text.count(old)==1, (old[:100],text.count(old))
    return text.replace(old,new)

def toolbar():
    return '''<div class="spatial-toolbar" aria-label="Linked 3D camera controls"><div class="preset-group"><button type="button" data-view-preset="iso">Isometric</button><button type="button" data-view-preset="xy">XY</button><button type="button" data-view-preset="xz">XZ</button><button type="button" data-view-preset="yz">YZ</button><button type="button" id="resetCamera">Reset view</button></div><label>Pitch <input id="pitch" type="range" min="-90" max="90" value="28"></label><label>Camera zoom <input id="zoom" type="range" min="0.5" max="2.5" step="0.05" value="1"></label><span id="cameraStatus" class="spatial-status" role="status" aria-live="polite"></span></div><p class="spatial-hint">Drag either pane to orbit both; wheel or pinch to zoom. Keyboard: arrows to orbit, +/− to zoom, 1–4 for XY/XZ/YZ/isometric, Home to reset. Camera zoom changes the view; displacement magnification changes arrow display only. Points and vectors are saved fields, not reconstructed fibers.</p>'''

def camera(yaw, canvases, callback, stop='function(){}'):
    return "const camera=SpatialCamera.create({yawInput:'%s',pitchInput:'pitch',zoomInput:'zoom',statusElement:'cameraStatus',resetButton:'resetCamera',canvases:%s,defaultYaw:28,defaultPitch:28,onChange:%s,onManualInteract:%s});\n" % (yaw,str(canvases),callback,stop)

# Repair touch handling and pause animation on manual camera interaction.
f=C/'spatial-camera.js';t=f.read_text()
t=replace(t,"canvas.focus({ preventScroll: true });","if (typeof opts.onManualInteract === 'function') opts.onManualInteract();\n        canvas.focus({ preventScroll: true });")
t=replace(t,"canvas.addEventListener('dblclick', function () {", "canvas.addEventListener('wheel', function(e) { e.preventDefault(); if (typeof opts.onManualInteract === 'function') opts.onManualInteract(); api.setZoom(state.zoom * Math.exp(-e.deltaY * 0.001)); }, {passive:false});\n      canvas.addEventListener('dblclick', function () {")
f.write_text(t)
f=C/'spatial-camera.css';t=f.read_text().replace('touch-action: pan-y pinch-zoom;','touch-action: none;');f.write_text(t+'\n.spatial-canvas{touch-action:none;cursor:grab;max-width:100%;height:auto}.spatial-pane canvas{aspect-ratio:auto}.spatial-toolbar label{display:grid;gap:4px}.replay-legend{display:flex;flex-wrap:wrap;gap:14px}.replay-status{line-height:1.6}.spatial-grid>*{min-width:0}\n')

# Genuine 3D periodic network: preserve all mechanics, clipping and frame logic.
f=C/'bovine-3d/page.js';t=(S/'bovine-3d/page.js').read_text()
t=replace(t,"for(let b of document.querySelectorAll('[data-tab]'))",camera('rotation',['clustered','distributed'],'()=>DATA&&renderSpatial()')+"for(let b of document.querySelectorAll('[data-tab]'))")
old="project=q=>{let x=q[0]-.5-g/2,y=q[1]-.5,z=q[2]-.5,rx=Math.cos(angle)*x-Math.sin(angle)*y,ry=Math.sin(angle)*x+Math.cos(angle)*y;return [W/2+240*rx,H/2-215*(z*.85+ry*.45)]}"
t=replace(t,old,"project=q=>camera.project(q,{center:[.5+g/2,.5,.5],width:W,height:H,scaleX:240,scaleY:215})")
t=replace(t,"ctx.globalAlpha=1;ctx.setLineDash([]);ctx.fillStyle='#7b3ab2';","ctx.globalAlpha=1;ctx.setLineDash([]);camera.drawAxes(ctx,W,H);ctx.fillStyle='#7b3ab2';")
t+="\nSpatialCamera.bindPauseOnHidden(()=>{if(playing){clearInterval(timer);playing=false;$('play').textContent='Play'}});\n"
f.write_text(t)

# Observed/predicted measured vectors: linked camera and an explicit residual view.
f=C/'measured-3d/page.js';t=(S/'measured-3d/page.js').read_text()
t=replace(t,"for(let b of document.querySelectorAll('[data-tab]'))",camera('rotation',['observed','predicted'],'()=>DATA&&render()','()=>{if(timer){clearInterval(timer);timer=null;$(\'rotate\').textContent=\'Rotate camera\'}}')+"for(let b of document.querySelectorAll('[data-tab]'))")
t=replace(t,"slider_unused_marker",'') if 'slider_unused_marker' in t else t
t=replace(t,"$('rotation').value=(Number($('rotation').value)+2)%361;render()","camera.stepYaw(2)")
old="let project=q=>{let[x,y,z]=q,xx=Math.cos(a)*x-Math.sin(a)*y,yy=Math.sin(a)*x+Math.cos(a)*y;return[W/2+.9*xx,H/2-.86*(.85*z+.45*yy)]}"
t=replace(t,old,"let project=q=>camera.project(q,{width:W,height:H,scaleX:.9,scaleY:.86})")
t=replace(t,"c.fillText('Positions µm · arrows magnified ×'+scale,14,H-16)","c.fillText('Positions µm · arrows magnified ×'+scale,14,H-16);camera.drawAxes(c,W,H)")
t=replace(t,"draw('predicted',DATA.field.predictions[name]);$('modelTitle').textContent=labels[name];","let vectors=DATA.field.predictions[name],residual=$('fieldMode').value==='residual';if(residual)vectors=vectors.map((u,i)=>u.map((v,k)=>v-DATA.field.observed[i][k]));draw('predicted',vectors);$('modelTitle').textContent=residual?'Residual: predicted − observed':labels[name];")
t+="\n$('fieldMode').onchange=()=>DATA&&render();SpatialCamera.bindPauseOnHidden(()=>{if(timer){clearInterval(timer);timer=null;$('rotate').textContent='Rotate camera'}});\n"
f.write_text(t)
f=C/'measured-3d/index.html';t=(S/'measured-3d/index.html').read_text();t=replace(t,'</title>','</title><link rel="stylesheet" href="../spatial-camera.css">')
idx=t.index('<canvas id="observed"');grid=t.rfind('<div class="grid">',0,idx);assert grid>=0
t=t[:grid]+toolbar()+'<label>Right pane <select id="fieldMode"><option value="prediction">Predicted displacement</option><option value="residual">Residual: predicted − observed</option></select></label><p class="spatial-hint">Both panes use the same 0–8 µm magnitude color scale; residual arrows are differences, not uncertainty estimates.</p>'+t[grid:]
t=t.replace('class="grid"','class="grid spatial-grid"').replace('<canvas id="observed"','<canvas class="spatial-canvas" tabindex="0" id="observed"').replace('<canvas id="predicted"','<canvas class="spatial-canvas" tabindex="0" id="predicted"')
t=replace(t,'<script src="page.js">','<script src="../spatial-camera.js"></script><script src="page.js">');f.write_text(t)

# Nonlinear field view: preserve report tables, split fixed-width panes for mobile.
f=C/'nonlinear-3d/page.js';original=(S/'nonlinear-3d/page.js').read_text();prefix=original[:original.index("let select=document.querySelector('#model')")]
tail=r'''const $=id=>document.getElementById(id),select=$('model'),slider=$('angle');let timer;
const camera=SpatialCamera.create({yawInput:'angle',pitchInput:'pitch',zoomInput:'zoom',statusElement:'cameraStatus',resetButton:'resetCamera',canvases:['canvas','predictionCanvas'],onChange:draw,onManualInteract:stop});
Object.keys(f.predictions).forEach(k=>{let o=document.createElement('option');o.value=k;o.textContent=k;select.append(o)});select.value='combined';
function stop(){if(timer){clearInterval(timer);timer=null;$('rotate').textContent='Rotate camera'}}
function pane(id,name,field){const canvas=$(id),c=canvas.getContext('2d'),W=canvas.width,H=canvas.height,project=q=>camera.project(q,{width:W,height:H,scaleX:.83,scaleY:.8});c.clearRect(0,0,W,H);c.fillStyle='#f8fafc';c.fillRect(0,0,W,H);c.fillStyle='#182c42';c.font='18px system-ui';c.fillText(name,20,30);c.fillStyle='#aab4bf';for(let q of f.cell_samples_um.filter((_,i)=>i%3===0)){let[x,y]=project(q);c.fillRect(x,y,2,2)}for(let i=0;i<f.nodes.length;i++){if(!f.score[i]||i%10)continue;let u=field[i],q=f.nodes[i],a=project(q),b=project(q.map((v,d)=>v+8*u[d])),mag=Math.hypot(...u),t=Math.min(1,mag/8);c.strokeStyle=`hsl(${42-35*t} 70% ${55-12*t}%)`;c.beginPath();c.moveTo(...a);c.lineTo(...b);c.stroke()}camera.drawAxes(c,W,H);c.fillStyle='#536376';c.font='13px system-ui';c.fillText('Same score mask · displacement ×8 · positions µm',15,H-18)}
function draw(){let residual=$('fieldMode').value==='residual',vectors=f.predictions[select.value];if(!vectors)return;if(residual)vectors=vectors.map((u,i)=>u.map((v,k)=>v-f.targets[i][k]));pane('canvas','Observed PIV',f.targets);pane('predictionCanvas',residual?'Residual: predicted − observed':select.value,vectors)}
select.onchange=$('fieldMode').onchange=draw;
$('rotate').onclick=()=>{if(timer)stop();else{timer=setInterval(()=>camera.stepYaw(2),80);$('rotate').textContent='Pause camera'}};SpatialCamera.bindPauseOnHidden(stop);draw()
})().catch(e=>{document.querySelector('#verdict').textContent='Could not load saved results: '+e.message});
'''
f.write_text(prefix+tail)
f=C/'nonlinear-3d/index.html';t=(S/'nonlinear-3d/index.html').read_text();t=replace(t,'</title>','</title><link rel="stylesheet" href="../spatial-camera.css">')
old=re.search(r'<canvas id="canvas"[^>]*></canvas>',t).group(0)
new=toolbar()+'''<label>Right pane <select id="fieldMode"><option value="prediction">Predicted displacement</option><option value="residual">Residual: predicted − observed</option></select></label><p class="spatial-hint">Common 0–8 µm magnitude color range. Residuals measure prediction error here, not uncertainty or a newly held-out experiment.</p><div class="spatial-grid"><div class="spatial-pane"><canvas id="canvas" width="525" height="520" tabindex="0" aria-label="Observed three-dimensional displacement vectors"></canvas></div><div class="spatial-pane"><canvas id="predictionCanvas" width="525" height="520" tabindex="0" aria-label="Predicted or residual three-dimensional displacement vectors"></canvas></div></div>'''
t=replace(t,old,new);t=replace(t,'<script src="page.js">','<script src="../spatial-camera.js"></script><script src="page.js">');f.write_text(t)

# Force replay remains planar: focus on one case on narrow screens, retain all four.
f=C/'force-replay/index.html';t=(S/'force-replay/index.html').read_text();t=replace(t,'</title>','</title><link rel="stylesheet" href="../spatial-camera.css">')
pos=t.index('<canvas id="view"');t=t[:pos]+'''<label>View <select id="caseFocus"><option value="all">Compare all four cases</option></select></label><label><input type="checkbox" id="ghost"> Show undeformed reference</label><p class="spatial-hint">Saved planar (2D) simulation states. Case focus enlarges one network; it does not add simulated depth.</p><div class="replay-legend"><span>Tension: orange</span><span>Compression: blue</span><span>Broken: magenta dashed</span><span>Connectors: dashed</span><span>Gripped nodes: teal</span></div><div id="replayStatus" class="replay-status" aria-live="polite"></div>'''+t[pos:];f.write_text(t)
f=C/'force-replay/replay-ui.js';t=(S/'force-replay/replay-ui.js').read_text()
t=replace(t,"let timer=null;","let timer=null;const focus=document.getElementById('caseFocus'),status=document.getElementById('replayStatus'),ghost=document.getElementById('ghost');d.cases.forEach((v,i)=>{let o=document.createElement('option');o.value=i;o.textContent=(v.family==='isotropic'?'Disordered':'Modular')+' / '+v.pattern;focus.append(o)});if(matchMedia('(max-width:750px)').matches)focus.value='0';focus.onchange=ghost.onchange=()=>draw();")
t=replace(t,"g.fillStyle='#f6f4ec';g.fillRect(0,0,1200,960);","const selected=focus.value==='all'?d.cases:[d.cases[Number(focus.value)]];c.width=focus.value==='all'?1200:600;c.height=focus.value==='all'?960:520;status.replaceChildren();g.fillStyle='#f6f4ec';g.fillRect(0,0,c.width,c.height);")
t=replace(t,"d.cases.forEach((v,n)=>{","selected.forEach((v,n)=>{")
t=replace(t,"[v.net.edges,v.net.links].forEach", "if(ghost.checked){g.strokeStyle='#b8c3c9';g.lineWidth=1;g.setLineDash([2,5]);for(const e of v.net.edges){g.beginPath();g.moveTo(px(v.net.X[e.i*2]),py(v.net.X[e.i*2+1]));g.lineTo(px(v.net.X[e.j*2]),py(v.net.X[e.j*2+1]));g.stroke()}g.setLineDash([])}\n[v.net.edges,v.net.links].forEach")
t=replace(t,"g.fillStyle='#203b32';g.font='16px system-ui';", "const row=document.createElement('p');row.textContent=(v.family==='isotropic'?'Disordered':'Modular')+' / '+v.pattern+': actual saved strain '+f.q.toFixed(4)+'; collagen lost '+(100*f.damage).toFixed(1)+'%; connectors broken '+(100*f.linkDamage).toFixed(1)+'%'+(q>v.frames.at(-1).q+1e-9?'; STOPPED: '+v.metrics.criterion:'; saved state');status.append(row);g.fillStyle='#203b32';g.font='16px system-ui';")
t+="\ndocument.addEventListener('visibilitychange',()=>{if(document.hidden&&timer){clearInterval(timer);timer=null;document.getElementById('play').textContent='Play'}});\n"
f.write_text(t)
print('Integrated complete Argon camera draft and original source-preserving visualization edits. No page code executed.')
