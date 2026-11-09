const CM=(()=>{// Original geometrically nonlinear, naturally curved discrete rods. No dependencies.
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),norm=a=>Math.sqrt(dot(a,a));
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const I=[1,0,0,0,1,0,0,0,1];
function mat(F,v){return [dot(F.slice(0,3),v),dot(F.slice(3,6),v),dot(F.slice(6,9),v)]}
function build(model,{amplitude=.08,segments=6,mu=1,kappa=.001,preserveBudget=true,junctionK=0}={}){
 if(!Number.isFinite(junctionK)||junctionK<0)throw Error('Invalid junction restraint');
 const X=model.positions.map(p=>p.slice()),bonds=[],hinges=[],twists=[],chains=[],disabled=new Set(model.disabled||[]),deleted=new Set(model.deleted||[]);let totalContour=0;
 for(let f=0;f<model.edges.length;f++){
  if(disabled.has(f))continue;let[i,j,...shift]=model.edges[f];if(deleted.has(i)||deleted.has(j))continue;
  let v=X[j].map((x,k)=>x-X[i][k]+shift[k]),l=norm(v);if(l<1e-6)throw Error('Coincident connected junctions');let n=v.map(x=>x/l),axis=Math.abs(n[0])<.8?[1,0,0]:[0,1,0],e1=cross(n,axis);e1=e1.map(x=>x/norm(e1));let e2=cross(n,e1),phase=(Number.isFinite(model.fiberPhases?.[f])?model.fiberPhases[f]:f*2.399963229728653),t1=e1.map((x,k)=>x*Math.cos(phase)+e2[k]*Math.sin(phase)),t2=cross(n,t1);let ids=[i],bids=[];
  for(let k=1;k<segments;k++){let t=k/segments;ids.push(X.length);X.push(X[i].map((x,d)=>x+t*v[d]+amplitude*l*(Math.sin(2*Math.PI*t)*t1[d]+.25*Math.sin(Math.PI*t)*t2[d])))}ids.push(j);
  let contour=0;
  for(let k=0;k<segments;k++){let sh=k===segments-1?shift:[0,0,0],a=ids[k],b=ids[k+1],v0=X[b].map((x,d)=>x-X[a][d]+sh[d]),l0=norm(v0);contour+=l0;bids.push(bonds.length);bonds.push({a,b,shift:sh,v0,l0,fiber:f})}
  for(let k=0;k<bids.length-1;k++){let p=bonds[bids[k]],q=bonds[bids[k+1]],a=p.v0.map(v=>v/p.l0),b=q.v0.map(v=>v/q.l0),theta0=Math.atan2(norm(cross(a,b)),Math.max(-1,Math.min(1,dot(a,b))));hinges.push({p:bids[k],q:bids[k+1],theta0,h:(p.l0+q.l0)/2})}
  for(let k=0;k<bids.length-2;k++){let p=bonds[bids[k]],q=bonds[bids[k+1]],r=bonds[bids[k+2]];if(amplitude>0){let h=(p.l0+q.l0+r.l0)/3,epsilon=.01*h*h,t=twistGeometry(p.v0,q.v0,r.v0,epsilon);twists.push({ids:bids.slice(k,k+3),co:t.co,si:t.si,h,epsilon})}}
  totalContour+=contour;chains.push({fiber:f,ids,bids,chord:l,contour,slack:contour/l-1});
 }
 // Pair outward end tangents at each shared junction. Cosine springs are stress-free at rest.
 const junctions=[],incident=new Map();
 if(junctionK>0){for(let c of chains){for(let [node,bid,sign] of [[c.ids[0],c.bids[0],1],[c.ids.at(-1),c.bids.at(-1),-1]]){if(!incident.has(node))incident.set(node,[]);incident.get(node).push({bid,sign})}}
 for(let [node,ends] of incident)for(let i=0;i<ends.length;i++)for(let j=i+1;j<ends.length;j++){let a=ends[i],b=ends[j],p=bonds[a.bid],q=bonds[b.bid],sign=a.sign*b.sign;junctions.push({node,p:a.bid,q:b.bid,sign,co0:sign*dot(p.v0,q.v0)/(p.l0*q.l0)})}}
 if(!bonds.length)throw Error('No connected fibers');let A=preserveBudget?model.budget/totalContour:model.area,EA=mu*A,D=3*X.length,diag=new Float64Array(D);
 for(let b of bonds)for(let k=0;k<3;k++){diag[3*b.a+k]+=EA/b.l0;diag[3*b.b+k]+=EA/b.l0}
 for(let h of hinges){let p=bonds[h.p],q=bonds[h.q],w=kappa/h.h*(1/p.l0**2+1/q.l0**2);for(let node of [p.a,p.b,q.b])for(let d=0;d<3;d++)diag[3*node+d]+=w}
 for(let h of junctions){let p=bonds[h.p],q=bonds[h.q],w=junctionK*(1/p.l0**2+1/q.l0**2);for(let node of new Set([p.a,p.b,q.a,q.b]))for(let d=0;d<3;d++)diag[3*node+d]+=w}
 let pre=Float64Array.from(diag,(v,i)=>i<3?0:1/Math.sqrt(Math.max(1e-10,v)));
 return {X,bonds,hinges,twists,junctions,junctionK,chains,EA,kappa,A,pre,D,originalNodes:model.positions.length,volume:model.L**3,settings:{amplitude,segments,mu,kappa,preserveBudget,junctionK},meanSlack:chains.reduce((s,c)=>s+c.slack,0)/chains.length};
}
function twistGeometry(a,b,c,epsilon){let n1=cross(a,b),n2=cross(b,c),l1=Math.sqrt(dot(n1,n1)+epsilon*epsilon),l2=Math.sqrt(dot(n2,n2)+epsilon*epsilon),u=n1.map(x=>x/l1),v=n2.map(x=>x/l2),lb=norm(b),h=b.map(x=>x/lb);return {u,v,h,l1,l2,lb,co:dot(u,v),si:dot(h,cross(u,v))}}
function evaluate(m,u,F=I){
 let g=new Float64Array(m.D),P=Array(9).fill(0),vectors=[],lengths=[],unit=[],axialEnergy=0,bendingEnergy=0,twistEnergy=0,junctionEnergy=0,maxMaterialStrain=0;
 function contribution(b,f){for(let k=0;k<3;k++){g[3*b.a+k]-=f[k];g[3*b.b+k]+=f[k];for(let l=0;l<3;l++)P[3*k+l]+=f[k]*b.v0[l]}}
 for(let b of m.bonds){let v=mat(F,b.v0).map((x,k)=>x+u[3*b.b+k]-u[3*b.a+k]),l=norm(v);if(l<1e-10)return {energy:Infinity,g,P};let n=v.map(x=>x/l),extension=l-b.l0,f=n.map(x=>x*m.EA/b.l0*extension);vectors.push(v);lengths.push(l);unit.push(n);axialEnergy+=m.EA/(2*b.l0)*extension**2;maxMaterialStrain=Math.max(maxMaterialStrain,Math.abs(extension/b.l0));contribution(b,f)}
 for(let h of m.hinges){let a=unit[h.p],b=unit[h.q],c=Math.max(-1,Math.min(1,dot(a,b))),sin=norm(cross(a,b)),theta=Math.atan2(sin,c),delta=theta-h.theta0,w=m.kappa/h.h;bendingEnergy+=w*delta*delta/2;
  // theta/sin(theta) has finite limit for an initially straight rod.
  let dc=sin>1e-10?-w*delta/sin:h.theta0<1e-10?-w:0;
  let fa=a.map((v,k)=>dc*(b[k]-c*v)/lengths[h.p]),fb=b.map((v,k)=>dc*(a[k]-c*v)/lengths[h.q]);contribution(m.bonds[h.p],fa);contribution(m.bonds[h.q],fb);
 }
 for(let h of m.junctions||[]){let a=unit[h.p],b=unit[h.q],co=dot(a,b),delta=h.sign*co-h.co0,w=m.junctionK*delta*h.sign;junctionEnergy+=m.junctionK*delta*delta/2;contribution(m.bonds[h.p],a.map((v,k)=>w*(b[k]-co*v)/lengths[h.p]));contribution(m.bonds[h.q],b.map((v,k)=>w*(a[k]-co*v)/lengths[h.q]))}
 for(let t of m.twists){let [pi,qi,ri]=t.ids,a=vectors[pi],b=vectors[qi],c=vectors[ri],z=twistGeometry(a,b,c,t.epsilon),w=.5*m.kappa/t.h,dc=z.co-t.co,ds=z.si-t.si;twistEnergy+=w/2*(dc*dc+ds*ds);let du=z.v.map((x,k)=>w*(dc*x+ds*cross(z.v,z.h)[k])),dv=z.u.map((x,k)=>w*(dc*x+ds*cross(z.h,z.u)[k])),dh=cross(z.u,z.v).map(x=>w*ds*x),dn1=du.map((x,k)=>(x-z.u[k]*dot(z.u,du))/z.l1),dn2=dv.map((x,k)=>(x-z.v[k]*dot(z.v,dv))/z.l2),ga=cross(b,dn1),gc=cross(dn2,b),gb=cross(dn1,a).map((x,k)=>x+cross(c,dn2)[k]+(dh[k]-z.h[k]*dot(z.h,dh))/z.lb);contribution(m.bonds[pi],ga);contribution(m.bonds[qi],gb);contribution(m.bonds[ri],gc)}
 g.fill(0,0,3);return {energy:axialEnergy+bendingEnergy+twistEnergy+junctionEnergy,axialEnergy,bendingEnergy,twistEnergy,junctionEnergy,g,P:P.map(x=>x/m.volume),lengths,maxMaterialStrain};
}
function relax(m,start,F,{tolerance=1e-6,maxIterations=1800}={}){
 let q=Float64Array.from(start,(v,i)=>m.pre[i]?v/m.pre[i]:0),hist=[],it=0;
 function ev(q){let u=Float64Array.from(q,(v,i)=>v*m.pre[i]),s=evaluate(m,u,F);return {u,...s,gq:Float64Array.from(s.g,(v,i)=>v*m.pre[i])}}
 let cur=ev(q),scale=Math.max(1,m.EA),target=tolerance*scale;
 for(;it<maxIterations;it++){
  if(Math.max(...cur.g.map((v,i)=>m.pre[i]?Math.abs(v):0))<=target)break;
  let h=cur.gq.slice(),alph=[];
  for(let k=hist.length-1;k>=0;k--){let a=hist[k],v=a.rho*dot(a.s,h);alph[k]=v;for(let i=3;i<h.length;i++)h[i]-=v*a.y[i]}
  let last=hist.at(-1),hscale=last?dot(last.s,last.y)/dot(last.y,last.y):1;for(let i=3;i<h.length;i++)h[i]*=hscale;
  for(let k=0;k<hist.length;k++){let a=hist[k],beta=a.rho*dot(a.y,h);for(let i=3;i<h.length;i++)h[i]+=a.s[i]*(alph[k]-beta)}
  let dir=Float64Array.from(h,v=>-v),gd=dot(cur.gq,dir);if(!(gd<0)){hist=[];dir=Float64Array.from(cur.gq,v=>-v);gd=-dot(cur.gq,cur.gq)}
  let t=1,next,qq,ok=false;for(let ls=0;ls<35;ls++){qq=Float64Array.from(q,(v,i)=>v+t*dir[i]);next=ev(qq);if(Number.isFinite(next.energy)&&next.energy<=cur.energy+1e-4*t*gd+1e-20){ok=true;break}t*=.5}if(!ok)break;
  let s=Float64Array.from(qq,(v,i)=>v-q[i]),y=Float64Array.from(next.gq,(v,i)=>v-cur.gq[i]),sy=dot(s,y);if(sy>1e-22){hist.push({s,y,rho:1/sy});if(hist.length>18)hist.shift()}q=qq;cur=next;
 }
 let residual=Math.max(...cur.g.map((v,i)=>m.pre[i]?Math.abs(v):0));return {...cur,residual,iterations:it,accepted:residual<=target&&Number.isFinite(cur.energy),tolerance:target};
}
function Fxx(e){return [1+e,0,0,0,1,0,0,0,1]}
function metrics(m,s,F){let positions=m.X.map((x,i)=>mat(F,x).map((v,k)=>v+s.u[3*i+k])),endRatios=m.chains.map(c=>{let b=m.bonds[c.bids.at(-1)],end=positions[c.ids.at(-1)].map((v,k)=>v+mat(F,b.shift)[k]),chord=norm(sub(end,positions[c.ids[0]])),contour=c.bids.reduce((sum,k)=>sum+s.lengths[k],0);return chord/contour});return {positions,endRatios,straightenedFraction:endRatios.filter(x=>x>=.99).length/endRatios.length,meanStraightness:endRatios.reduce((a,b)=>a+b,0)/endRatios.length}}
return {build,evaluate,relax,Fxx,metrics,mat,I};
})();
const ND=(()=>{// Original deterministic periodic graph generator. Standard JavaScript only.
function rng(seed){let a=seed>>>0;return ()=>{a=(a+0x6D2B79F5)>>>0;let t=Math.imul(a^(a>>>15),1|a);t^=t+Math.imul(t^(t>>>7),61|t);return ((t^(t>>>14))>>>0)/4294967296}}
function pairRandom(seed,i,j){let a=Math.imul((seed^Math.imul(i+1,73856093)^Math.imul(j+1,19349663))>>>0,2246822519);a^=a>>>13;return ((Math.imul(a,3266489917)^(a>>>16))>>>0)+1}
function delta(a,b,L){let shift=b.map((x,k)=>-Math.round((x-a[k])/L)*L),v=b.map((x,k)=>x-a[k]+shift[k]);return {shift,v,length:Math.hypot(...v)}}
function analyze(model){const deleted=new Set(model.deleted||[]),disabled=new Set(model.disabled||[]),live=model.positions.map((_,i)=>i).filter(i=>!deleted.has(i)),degree=Array(model.positions.length).fill(0),adj=degree.map(()=>[]);let lengths=[],alignment=0;
 model.edges.forEach(([i,j,...shift],k)=>{if(disabled.has(k)||deleted.has(i)||deleted.has(j))return;degree[i]++;degree[j]++;adj[i].push(j);adj[j].push(i);let v=model.positions[j].map((x,d)=>x-model.positions[i][d]+shift[d]),l=Math.hypot(...v);lengths.push(l);alignment+=(v[0]/l)**2});
 let seen=new Set(),components=[];for(let i of live){if(seen.has(i))continue;let queue=[i],size=0;seen.add(i);while(queue.length){let j=queue.pop();size++;for(let k of adj[j])if(!seen.has(k)){seen.add(k);queue.push(k)}}components.push(size)}
 let hist=[];for(let i of live)hist[degree[i]]=(hist[degree[i]]||0)+1;return {junctions:live.length,fibers:lengths.length,meanDegree:live.length?2*lengths.length/live.length:0,minDegree:live.length?Math.min(...live.map(i=>degree[i])):0,maxDegree:live.length?Math.max(...live.map(i=>degree[i])):0,isolated:live.filter(i=>degree[i]===0).length,components:components.length,largestComponent:components.length?Math.max(...components):0,degree,degreeHistogram:Array.from(hist,x=>x||0),lengths,meanLength:lengths.length?lengths.reduce((s,x)=>s+x,0)/lengths.length:0,meanCos2X:lengths.length?alignment/lengths.length:0};}
function generate(base,options={}){
 const c={layout:'current',count:32,seed:17,rule:'radius',k:8,cutoff:.4,retention:.8,bias:0,keepConnected:true,...options};
 if(!['current','uniform','clusters','layers'].includes(c.layout)||!['radius','knn','mutual'].includes(c.rule))throw Error('Unknown layout or connection rule.');
 if(!Number.isInteger(c.seed)||c.seed<0||c.seed>999999||!Number.isInteger(c.count)||c.count<8||c.count>64||!Number.isInteger(c.k)||c.k<1||c.k>16||!Number.isFinite(c.cutoff)||c.cutoff<.05||c.cutoff>.87||!Number.isFinite(c.retention)||c.retention<0||c.retention>1||!Number.isFinite(c.bias)||c.bias<0||c.bias>8)throw Error('Distribution settings are out of range.');
 const L=base.L,random=rng(c.seed),active=base.positions.filter((_,i)=>!(base.deleted||[]).includes(i));let positions=[];
 if(c.layout==='current')positions=active.map(p=>p.slice());else{
  const centers=Array.from({length:3},()=>[random(),random(),random()]);const normal=()=>Math.sqrt(-2*Math.log(Math.max(1e-12,random())))*Math.cos(2*Math.PI*random());
  for(let attempts=0;positions.length<c.count&&attempts<10000;attempts++){
   let q=Array.from({length:3},()=>random());if(c.layout==='clusters'){let center=centers[positions.length%3];q=center.map(x=>((x+.13*normal())%1+1)%1)}if(c.layout==='layers')q[2]=(((positions.length%3+.5)/3+.025*normal())%1+1)%1;
   let p=q.map(x=>x*L);if(positions.every(v=>delta(v,p,L).length>.025*L))positions.push(p);
  }if(positions.length!==c.count)throw Error('Unable to place separated junctions; choose another seed.');
 }
 if(positions.length<4)throw Error('At least four active junctions are required.');
 let all=[],neighbors=positions.map(()=>[]);for(let i=0;i<positions.length;i++)for(let j=i+1;j<positions.length;j++){let d=delta(positions[i],positions[j],L);if(d.length<1e-7)throw Error('Coincident junctions. Move them apart before rebuilding.');if(d.length<=c.cutoff*L+1e-10){let edge={i,j,...d};all.push(edge);neighbors[i].push({j,length:d.length});neighbors[j].push({j:i,length:d.length})}}
 let choices=neighbors.map(ns=>new Set(ns.sort((a,b)=>a.length-b.length||a.j-b.j).slice(0,c.k).map(n=>n.j)));
 let candidates=all.filter(e=>c.rule==='radius'||(c.rule==='knn'?(choices[e.i].has(e.j)||choices[e.j].has(e.i)):(choices[e.i].has(e.j)&&choices[e.j].has(e.i))));
 // Weighted exponential race: fixed pair priorities give nested retention at fixed geometry/settings.
 for(let e of candidates){let u=pairRandom(c.seed,e.i,e.j)/4294967297,weight=Math.exp(c.bias*(e.v[0]/e.length)**2);e.priority=-Math.log(u)/weight}candidates.sort((a,b)=>a.priority-b.priority||a.i-b.i||a.j-b.j);
 let count=Math.round(c.retention*candidates.length),picked=new Set(),parent=positions.map((_,i)=>i);function root(i){while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i]}return i}
 if(c.keepConnected){for(let i=0;i<candidates.length;i++){let e=candidates[i],a=root(e.i),b=root(e.j);if(a!==b){parent[a]=b;picked.add(i)}}if(new Set(parent.map((_,i)=>root(i))).size>1)throw Error('Candidate graph is disconnected. Increase range or neighbors, or turn off Keep one connected component. No extra long links were added.');count=Math.max(count,picked.size)}
 for(let i=0;picked.size<count&&i<candidates.length;i++)picked.add(i);
 const es=[...picked].sort((a,b)=>a-b).map(i=>{let e=candidates[i];return [e.i,e.j,...e.shift]});if(es.length>450)throw Error(`${es.length} fibers exceeds the interactive limit of 450. Reduce retained fibers, range or neighbors.`);if(!es.length)throw Error('No fibers selected. Increase retained fibers, range or neighbors.');
 let totalLength=es.reduce((s,e)=>s+Math.hypot(...positions[e[1]].map((x,k)=>x-positions[e[0]][k]+e[k+2])),0);
 let model={kind:c.layout==='current'?base.kind:'stochastic',L,positions,edges:es,disabled:[],deleted:[],fiberPhases:es.map(e=>2*Math.PI*pairRandom(c.seed,e[0],e[1])/4294967297),area:base.area,budget:base.budget,seed:c.seed,architecture:'custom',generation:{schema:'periodic-distribution-v1',...c,candidates:candidates.length,requestedFibers:Math.round(c.retention*candidates.length),actualFibers:es.length,backboneFloorApplied:es.length>Math.round(c.retention*candidates.length)}};
 return {model,stats:analyze(model)};
}
return {generate,analyze,delta};
})();
const CC=(()=>{// Original comparison diagnostics; force is the axial stretching contribution only.
const {build,relax,Fxx}=CM;
const {analyze}=ND;
function validateModel(m){
 if(!m||!Array.isArray(m.positions)||m.positions.length<4||m.positions.length>150||!Number.isFinite(m.L)||m.L<=0||!Number.isFinite(m.area)||m.area<=0||!Number.isFinite(m.budget)||m.budget<=0||!m.positions.every(p=>Array.isArray(p)&&p.length===3&&p.every(Number.isFinite))||!Array.isArray(m.edges)||m.edges.length>2000||!m.edges.every(e=>Array.isArray(e)&&e.length===5&&e.every(Number.isFinite)&&Number.isInteger(e[0])&&Number.isInteger(e[1])&&e[0]>=0&&e[1]>=0&&e[0]<m.positions.length&&e[1]<m.positions.length&&e[0]!==e[1]))throw Error('Invalid or oversized graph.');
 for(let field of ['disabled','deleted'])if(m[field]!==undefined&&(!Array.isArray(m[field])||!m[field].every(i=>Number.isInteger(i)&&i>=0&&i<(field==='disabled'?m.edges.length:m.positions.length))))throw Error('Invalid graph exclusions.');
 if(m.fiberPhases!==undefined&&(!Array.isArray(m.fiberPhases)||!m.fiberPhases.every(Number.isFinite)))throw Error('Invalid crimp phases.');
 let a=analyze(m);if(!a.fibers||a.fibers>450)throw Error('Use 1–450 active fibers.');return a;
}
function loadStats(m,state){
 const signed=m.bonds.map((b,i)=>m.EA*(state.lengths[i]/b.l0-1));
 const fibers=m.chains.map(c=>{let ns=c.bids.map(i=>signed[i]);return {fiber:c.fiber,maxAbs:Math.max(...ns.map(Math.abs)),maxTension:Math.max(0,...ns),minCompression:Math.min(0,...ns),axialEnergy:c.bids.reduce((s,i)=>{let b=m.bonds[i];return s+m.EA/(2*b.l0)*(state.lengths[i]-b.l0)**2},0)}});
 const total=fibers.reduce((s,f)=>s+f.axialEnergy,0),count=Math.max(1,Math.ceil(.2*fibers.length)),top=fibers.slice().sort((a,b)=>b.axialEnergy-a.axialEnergy).slice(0,count).reduce((s,f)=>s+f.axialEnergy,0);
 return {signed,fibers,maxAbs:Math.max(0,...signed.map(Math.abs)),axialEnergy:total,top20EnergyFraction:total>1e-20?top/total:null};
}
function commonStrains(runs){if(runs.length!==2||runs.some(r=>!r?.frames?.length))return [];return runs[0].frames.filter(f=>f.accepted&&runs[1].frames.some(g=>g.accepted&&Math.abs(g.strain-f.strain)<1e-10)).map(f=>f.strain)}
function frameAt(run,strain){return run?.frames?.find(f=>f.accepted&&Math.abs(f.strain-strain)<1e-10)||null}
function effectiveModels(models){return models.map(m=>({...m,budget:models[0].budget,area:models[0].area}))}
function* solvePair(models,settings,protocol={}){
 models=effectiveModels(models);
 const {maxStrain=.04,increment=.01,tolerance=2e-6,maxIterations=12000}=protocol;
 if(!(maxStrain>=0&&maxStrain<=.2&&increment>=.002&&increment<=.02&&maxIterations>=1&&maxIterations<=12000))throw Error('Invalid loading protocol.');
 const steps=Math.max(1,Math.ceil(maxStrain/increment)),modelsBuilt=[],displacements=[],stopped=[false,false];
 for(let i=0;i<2;i++){try{let a=validateModel(models[i]);if(a.components!==1)throw Error('Disconnected graph: connect all active junctions before calculating.');let m=build(models[i],settings);modelsBuilt[i]=m;displacements[i]=new Float64Array(m.D);yield {type:'ready',case:i,nodes:m.X.length,EA:m.EA,area:m.A}}catch(e){stopped[i]=true;yield {type:'error',case:i,message:e.message}}}
 for(let k=0;k<=steps;k++)for(let i=0;i<2;i++){
  if(stopped[i])continue;const strain=maxStrain*k/steps;yield {type:'progress',case:i,strain,step:k,steps};
  try{let m=modelsBuilt[i],s=relax(m,displacements[i],Fxx(strain),{tolerance,maxIterations});displacements[i]=s.u;
   let frame={strain,stress:s.P[0],energy:s.energy,axialEnergy:s.axialEnergy,bendingEnergy:s.bendingEnergy,twistEnergy:s.twistEnergy,residual:s.residual,tolerance:s.tolerance,accepted:s.accepted,iterations:s.iterations,u:s.u,lengths:s.lengths};yield {type:'frame',case:i,frame};if(!s.accepted)stopped[i]=true;
  }catch(e){stopped[i]=true;yield {type:'error',case:i,message:e.message}}
 }
 yield {type:'done'};
}
function curveRows(runs){return runs.flatMap((r,i)=>(r?.frames||[]).map(f=>({case:i?'B':'A',strain:f.strain,nominalStress:f.stress,energy:f.energy,axialEnergy:f.axialEnergy,bendingEnergy:f.bendingEnergy,twistEnergy:f.twistEnergy,residual:f.residual,forceTolerance:f.tolerance,accepted:f.accepted,iterations:f.iterations})));}
return {validateModel,loadStats,commonStrains,frameAt,effectiveModels,solvePair,curveRows};
})();
// Original data/quality helpers, no Three.js or external dependencies.
function participation(values){let a=values.map(Math.abs),s=a.reduce((x,y)=>x+y,0),q=a.reduce((x,y)=>x+y*y,0);return a.length&&q>1e-22?s*s/(a.length*q):null}
function quality(r){let f=r.frames?.at(-1),ratio=f?Math.max(0,...f.peakForces)/f.tolerance:0;return {ratio,eligible:r.status==='complete'&&r.frames.every(f=>f.accepted)&&f.strain>=.04-1e-10&&f.stress>0&&Number.isFinite(participation(f.peakForces))&&ratio>=20}}
function frontier(records){let ok=records.filter(r=>quality(r).eligible);return ok.filter(a=>!ok.some(b=>b!==a&&b.stiffness>=a.stiffness&&b.evenness>=a.evenness&&(b.stiffness>a.stiffness||b.evenness>a.evenness))).map(r=>r.index)}
function sample(r,e){let frames=r.frames.filter(f=>f.accepted);if(!frames.length)throw Error('No accepted frames');e=Math.max(0,Math.min(e,frames.at(-1).strain));let hi=frames.findIndex(f=>f.strain>=e-1e-12);if(hi<0)hi=frames.length-1;let b=frames[hi],a=frames[Math.max(0,hi-1)],t=b.strain===a.strain?0:(e-a.strain)/(b.strain-a.strain),lerp=(x,y)=>x+(y-x)*t;return {strain:e,exact:Math.abs(e-a.strain)<1e-9||Math.abs(e-b.strain)<1e-9,stress:lerp(a.stress,b.stress),positions:a.positions.map((p,i)=>p.map((x,k)=>lerp(x,b.positions[i][k]))),segmentForces:a.segmentForces.map((x,i)=>lerp(x,b.segmentForces[i])),peakForces:a.peakForces.map((x,i)=>lerp(x,b.peakForces[i]))}}


// Original bounded browser solver; no dependencies or rendering imports.
const {build,relax,Fxx,metrics}=CM;
const {loadStats,validateModel}=CC;

function validateInput(x){if(!x||!Number.isFinite(x.amplitude)||x.amplitude<0||x.amplitude>.12||!Number.isFinite(x.restraint)||x.restraint<0||x.restraint>10)throw Error('Use crimp 0–12% and junction restraint 0–10×.');return {amplitude:x.amplitude,restraint:x.restraint}}
function* solveCustom(base,input){let {amplitude,restraint}=validateInput(input);validateModel(base.model);if(base.model.positions.length!==16||base.model.edges.length!==96)throw Error('Live presets require the fixed 16-junction / 96-fiber reference.');let settings={amplitude,junctionK:restraint*.0001,segments:4,mu:1,kappa:.0001,preserveBudget:true},protocol={strains:[0,.01,.02,.03,.04],tolerance:2e-7,maxIterations:24000},m=build(base.model,settings),start=Date.now(),r={preset:'custom',custom:true,label:'Custom mechanical scenario',config:base.config,model:base.model,graphStats:base.graphStats,settings,protocol,EA:m.EA,restPositions:m.X,meanSlack:m.meanSlack,junctionPairs:m.junctions.length,chains:m.chains.map(c=>({fiber:c.fiber,ids:c.ids,bids:c.bids,shift:m.bonds[c.bids.at(-1)].shift})),frames:[],status:'pending'},u=new Float64Array(m.D);
for(let strain of protocol.strains){if(Date.now()-start>110000)throw Error('Calculation time bound reached; no extrapolated result.');yield {type:'progress',strain,completed:r.frames.length,total:5};let F=Fxx(strain),s=relax(m,u,F,protocol),v=metrics(m,s,F),loads=loadStats(m,s),peaks=loads.fibers.map(f=>f.maxAbs);u=s.u;r.frames.push({strain,stress:s.P[0],energy:s.energy,axialEnergy:s.axialEnergy,bendingEnergy:s.bendingEnergy,twistEnergy:s.twistEnergy,junctionEnergy:s.junctionEnergy,residual:s.residual,tolerance:s.tolerance,accepted:s.accepted,iterations:s.iterations,positions:v.positions,segmentForces:loads.signed,peakForces:peaks,evenness:participation(peaks),top20EnergyFraction:loads.top20EnergyFraction,meanStraightness:v.meanStraightness});yield {type:'frame',strain,accepted:s.accepted,residual:s.residual,tolerance:s.tolerance,completed:r.frames.length,total:5};if(!s.accepted){r.status='unresolved';yield {type:'rejected',record:r,message:`Force check did not pass at ${(100*strain).toFixed(0)}% strain. Previous accepted result remains displayed.`};return}}
r.status='complete';let end=r.frames.at(-1);r.stiffness=end.stress/.04;r.evenness=end.evenness;r.wall_ms=Date.now()-start;yield {type:'done',record:r};}


self.onmessage=({data})=>{try{for(let event of solveCustom(data.base,data.input))self.postMessage(event)}catch(e){self.postMessage({type:'error',message:e.message})}};