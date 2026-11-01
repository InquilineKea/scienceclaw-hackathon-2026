'use strict';
const $=id=>document.getElementById(id), NS='http://www.w3.org/2000/svg';
let curves,seeds,manifest,frames=[],revision=0;
const cache=new Map();
const fmt=x=>Number.isFinite(x)?(x>=.01?x.toPrecision(4):x.toExponential(2)):'unresolved';
function element(tag,attrs={},content){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(content!==undefined)e.textContent=content;return e;}
function line(svg,x1,y1,x2,y2,attrs={}){svg.append(element('line',{x1,y1,x2,y2,...attrs}));}
function text(svg,x,y,s,attrs={}){svg.append(element('text',{x,y,...attrs},s));}
async function json(path){const r=await fetch(path);if(!r.ok)throw Error(`${path}: HTTP ${r.status}`);return r.json();}
function selected(){return curves.find(c=>c.z_target===+$('z').value&&c.kappa===+$('kappa').value);}
function plot(c,f){
 const svg=$('plot');svg.replaceChildren();const key=$('metric').value,values=c[key],left=69,right=630,top=25,bottom=345;
 const positive=values.filter(v=>Number.isFinite(v)&&v>0);if(!positive.length){text(svg,70,70,'No positive finite response values.');return;}
 let low=Math.floor(Math.log10(Math.min(...positive))),high=Math.ceil(Math.log10(Math.max(...positive)));if(low===high)high++;
 const X=g=>left+(Math.log10(g)+3)/3*(right-left),Y=v=>bottom-(Math.log10(v)-low)/(high-low)*(bottom-top);
 for(let k=-3;k<=0;k++){const x=X(10**k);line(svg,x,top,x,bottom,{stroke:'#e6ebe6'});text(svg,x,bottom+25,`10${['⁻³','⁻²','⁻¹','⁰'][k+3]}`,{'text-anchor':'middle'});}
 const step=Math.max(1,Math.ceil((high-low)/6));for(let k=low;k<=high;k+=step){const y=Y(10**k);line(svg,left,y,right,y,{stroke:'#e6ebe6'});text(svg,left-10,y+4,`1e${k}`,{'text-anchor':'end'});}
 line(svg,left,top,left,bottom,{stroke:'#a8bdb5'});line(svg,left,bottom,right,bottom,{stroke:'#a8bdb5'});
 let d='',count=0;for(let i=0;i<values.length;i++){const v=values[i];if(!(Number.isFinite(v)&&v>0)){count=0;continue;}d+=`${count?'L':'M'}${X(c.gamma[i])},${Y(v)} `;count++;}
 svg.append(element('path',{d,fill:'none',stroke:'#087f82','stroke-width':2.6}));
 for(const [key,color] of [['gamma_c_K','#be5b2d'],['gamma_c_nonaffinity','#8861a5']]){const g=c[key];if(Number.isFinite(g)&&g>0)line(svg,X(g),top,X(g),bottom,{stroke:color,'stroke-width':1.8,'stroke-dasharray':'6 5'});}
 if(f)line(svg,X(f.gamma),top,X(f.gamma),bottom,{stroke:'#748582','stroke-dasharray':'2 5'});
 text(svg,(left+right)/2,397,'Simple shear strain γ (dimensionless)',{'text-anchor':'middle'});
 text(svg,15,(top+bottom)/2,$('metric').selectedOptions[0].text,{transform:`rotate(-90 15 ${(top+bottom)/2})`,'text-anchor':'middle'});
 $('metric-title').textContent=$('metric').selectedOptions[0].text;
}
function network(f){
 const svg=$('network');svg.replaceChildren();if(!f)return;const box=f.box;
 const corners=[[0,0],box[0],[box[0][0]+box[1][0],box[0][1]+box[1][1]],box[1]];
 const xs=corners.map(p=>p[0]),ys=corners.map(p=>p[1]);const minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);
 const scale=Math.min(500/(maxx-minx),350/(maxy-miny)),ox=(560-scale*(maxx-minx))/2,oy=(410-scale*(maxy-miny))/2;
 const P=p=>[ox+(p[0]-minx)*scale,410-oy-(p[1]-miny)*scale],points=corners.map(p=>P(p).join(',')).join(' ');
 const defs=element('defs'),clip=element('clipPath',{id:'cell'});clip.append(element('polygon',{points}));defs.append(clip);svg.append(defs);
 svg.append(element('polygon',{points,fill:'#f2f4ee',stroke:'#a8bdb5','stroke-width':1}));const group=element('g',{'clip-path':'url(#cell)'});
 const energy=f[$('color').value],valid=energy.filter(e=>e>0&&Number.isFinite(e)),mx=Math.max(...valid,1e-30),lo=Math.log10(mx)-5;
 for(let k=0;k<f.edges.length;k++){
   const pos=f.positions[f.edges[k][0]],v=f.edge_vectors[k],e=energy[k],t=e>0?Math.max(0,Math.min(1,(Math.log10(e)-lo)/5)):0;
   const color=`rgb(${Math.round(25+211*t)},${Math.round(83+83*t)},${Math.round(91-40*t)})`;
   // Draw periodic translated copies of each physical edge vector, clipped to cell.
   for(let a=-1;a<=1;a++)for(let b=-1;b<=1;b++){
     const p=[pos[0]+a*box[0][0]+b*box[1][0],pos[1]+a*box[0][1]+b*box[1][1]],q=[p[0]+v[0],p[1]+v[1]],s=P(p),r=P(q);
     if(Math.max(s[0],r[0])<0||Math.min(s[0],r[0])>560||Math.max(s[1],r[1])<0||Math.min(s[1],r[1])>410)continue;
     line(group,s[0],s[1],r[0],r[1],{stroke:color,'stroke-width':1.6});
   }
 }
 svg.append(group);$('gamma').textContent=fmt(f.gamma);
 $('frame-info').textContent=`${f.positions.length} displayed nodes · ${f.shown_edges}/${f.total_edges} edges · saved state ${+$('strain').value+1}/31 · converged`;
}
function render(){const c=selected(),f=frames[+$('strain').value];plot(c,f);network(f);}
function details(c){
 $('onset-k').textContent=fmt(c.gamma_c_K);$('onset-n').textContent=fmt(c.gamma_c_nonaffinity);
 const ratio=c.gamma_c_K/c.gamma_c_nonaffinity;$('ratio').textContent=ratio.toFixed(2)+'×';
 $('interpretation').textContent=`For z = ${c.z_target}, κ = ${c.kappa}, the mean-curve modulus criterion occurs ${ratio.toFixed(2)} times later in strain than the nonaffinity maximum. Neither definition alone establishes a physical critical point.`;
 $('seeds').replaceChildren();for(const s of seeds.filter(s=>s.z_target===c.z_target&&s.kappa===c.kappa)){const tr=document.createElement('tr');for(const v of [s.seed,s.nodes,s.z_actual.toFixed(4),fmt(s.gamma_c_K),fmt(s.gamma_c_nonaffinity)]){const td=document.createElement('td');td.textContent=v;tr.append(td);}$('seeds').append(tr);}
 $('fits').replaceChildren();for(const [key,label] of [['gamma_c_K','Modulus-onset fit'],['gamma_c_nonaffinity','Nonaffinity-onset fit']]){const fit=c.critical_exponents[key],div=document.createElement('div');div.className='fit';const title=document.createElement('strong');title.textContent=label;div.append(title);const detail=document.createElement('span');detail.textContent=fit.status==='determined'?`f = ${fmt(fit.f)} · conditional 95% CI [${fmt(fit.f_ci95[0])}, ${fmt(fit.f_ci95[1])}] · R² ${fmt(fit.r_squared)} · ${fit.n_points} points`:`Unresolved: ${fit.reason||'numerical fit gate not met'}`;div.append(detail);$('fits').append(div);}
}
async function select(){const ticket=++revision,c=selected();details(c);frames=[];plot(c);$('network').replaceChildren();$('frame-info').textContent='Loading saved network states…';$('strain').disabled=true;
 try{if(!cache.has(c.frames_file))cache.set(c.frames_file,json(c.frames_file));const result=await cache.get(c.frames_file);if(ticket!==revision)return;frames=result;$('strain').disabled=false;render();$('status').textContent='Loaded audited data. Controls select saved parameter cases; they do not run new simulations.';}
 catch(err){if(ticket!==revision)return;$('status').textContent=`Could not load network data: ${err.message}`;}}
async function verify(){const button=$('verify');button.disabled=true;try{if(!crypto.subtle)throw Error('SHA-256 requires localhost or HTTPS');let count=0;for(const f of manifest.artifact_files){$('verification').textContent=`Verifying ${++count}/${manifest.artifact_files.length}…`;const response=await fetch(f.path);if(!response.ok)throw Error(`HTTP ${response.status}: ${f.path}`);const bytes=await response.arrayBuffer(),hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');if(bytes.byteLength!==f.bytes||hash!==f.sha256)throw Error(`Mismatch: ${f.path}`);}$('verification').textContent=`Verified ${count}/${count} files by SHA-256 and byte length.`;}catch(err){$('verification').textContent=`Verification failed: ${err.message}`;}finally{button.disabled=false;}}
async function init(){try{[curves,seeds,manifest]=await Promise.all([json('data/curves.json'),json('data/seed-onsets.json'),json('data/manifest.json')]);for(const id of ['z','kappa'])$(id).addEventListener('change',select);for(const id of ['metric','color'])$(id).addEventListener('change',render);$('strain').addEventListener('input',render);$('verify').addEventListener('click',verify);await select();}catch(err){$('status').textContent=`Could not load companion data: ${err.message}. Serve this folder over HTTP(S), rather than opening index.html as a file.`;}}
init();
