// Original dependency-free 3D periodic spring / junction-angle mechanics.
import fs from 'node:fs';
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
const dot=(a,b)=>{let s=0;for(let i=0;i<a.length;i++)s+=a[i]*b[i];return s};
const maxabs=a=>{let m=0;for(let x of a)m=Math.max(m,Math.abs(x));return m};
function rng(seed){return ()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296}}
function shuffled(n,r){let a=Array.from({length:n},(_,i)=>i);for(let i=n-1;i>0;i--){let j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function setup(net,pattern='baseline',density=0,z=3.8){
 let {positions:x,edges:e,angles:a,seed}=net,N=x.length,active=e.map(()=>true),deg=new Int32Array(N);for(let [i,j] of e){deg[i]++;deg[j]++}
 const connected=()=>{let adj=Array.from({length:N},()=>[]);e.forEach(([i,j],k)=>{if(active[k]){adj[i].push(j);adj[j].push(i)}});let seen=new Set([0]),s=[0];while(s.length)for(let j of adj[s.pop()])if(!seen.has(j)){seen.add(j);s.push(j)}return seen.size===N};
 let count=e.length;for(let k of shuffled(e.length,rng(seed+8500))){if(count<=Math.round(z*N/2))break;let [i,j]=e[k];if(deg[i]>2&&deg[j]>2){active[k]=false;if(connected()){deg[i]--;deg[j]--;count--}else active[k]=true}}
 let v=e.map(([i,j,sx,sy,sz])=>[x[j][0]-x[i][0]+sx,x[j][1]-x[i][1]+sy,x[j][2]-x[i][2]+sz]);let rest=v.map(v=>Math.hypot(...v)),mean=rest.reduce((s,l,k)=>s+(active[k]?l:0),0)/count;
 let c0=a.map(([i,j,s])=>s*dot(v[i],v[j])/rest[i]/rest[j]);
 let r=rng(seed+375),center=[r(),r(),r()],nlock=Math.round(density*N),sites=shuffled(N,rng(seed+300));
 const dist=i=>x[i].reduce((s,t,k)=>s+Math.min(Math.abs(t-center[k]),1-Math.abs(t-center[k]))**2,0);
 let clusterSites=Array.from({length:N},(_,i)=>i).sort((i,j)=>dist(i)-dist(j));
 if(pattern==='clustered')sites=clusterSites;
 if(pattern==='distributed'&&nlock){let selected=[];for(let degree of [2,3,4]){let count=clusterSites.slice(0,nlock).filter(i=>deg[i]===degree).length;selected.push(...sites.filter(i=>deg[i]===degree).slice(0,count))}let chosen=new Set(selected);sites=[...selected,...sites.filter(i=>!chosen.has(i))]}
 let locked=new Set(sites.slice(0,nlock));
 // Both arms share a junction. Angle stiffness modification is local to it.
 let junction=a.map(([ei,ej])=>{let [i,j]=e[ei],[u,w]=e[ej];return i===u||i===w?i:j});
 let aw=a.map((_,k)=>.001*mean*(locked.has(junction[k])?10:1));
 return {x,e,a,N,v,rest,c0,aw,active,mean,locked:[...locked],lock_spread:nlock?sites.slice(0,nlock).reduce((s,i)=>s+dist(i),0)/nlock:0,z:2*count/N};
}
function state(m,u,g,plane=1,needRows=false){
 let {e,a,N,v:base,rest,c0,aw,active}=m;let E=0,stress=0,grad=new Float64Array(3*N),rows=[],vv=[],ll=[],forces=[];
 const add=(ids,j,r)=>{E+=r*r/2;for(let k=0;k<ids.length;k++)grad[ids[k]]+=j[k]*r;if(needRows)rows.push([ids,j]);};
 for(let k=0;k<e.length;k++){
  let [i,j]=e[k],v=[0,0,0];for(let d=0;d<3;d++)v[d]=base[k][d]+u[3*j+d]-u[3*i+d]+(d===0?g*base[k][plane]:0);
  let l=Math.hypot(...v),n=v.map(t=>t/l);vv.push(n);ll.push(l);forces.push(active[k]?(l-rest[k])/rest[k]:0);
  if(!active[k])continue;let w=1/Math.sqrt(rest[k]),r=(l-rest[k])*w,jac=[...n.map(t=>-t*w),...n.map(t=>t*w)],ids=[3*i,3*i+1,3*i+2,3*j,3*j+1,3*j+2];add(ids,jac,r);stress+=r*w*n[0]*base[k][plane];
 }
 for(let k=0;k<a.length;k++){
  let [p,q,sg]=a[k];if(!active[p]||!active[q])continue;let na=vv[p],nb=vv[q],co=dot(na,nb),w=Math.sqrt(aw[k]),r=(sg*co-c0[k])*w;
  let da=na.map((t,d)=>sg*(nb[d]-co*t)/ll[p]*w),db=nb.map((t,d)=>sg*(na[d]-co*t)/ll[q]*w),ids=[],jac=[];
  for(let [node,vec,sign] of [[e[p][0],da,-1],[e[p][1],da,1],[e[q][0],db,-1],[e[q][1],db,1]])for(let d=0;d<3;d++){ids.push(3*node+d);jac.push(sign*vec[d])}
  add(ids,jac,r);stress+=r*(da[0]*base[p][plane]+db[0]*base[q][plane]);
 }
 grad.fill(0,0,3);return {E,stress,grad,rows,lengths:ll,forces};
}
function pcg(rows,grad,N){
 let D=grad.length,diag=new Float64Array(D),b=Float64Array.from(grad,t=>-t);
 // Sum duplicate entries in local rows before diagonal assembly (shared junction).
 let rr=rows.map(([ids,j])=>{let m=new Map();ids.forEach((id,k)=>{if(id>=3)m.set(id,(m.get(id)||0)+j[k])});let ii=[...m.keys()],jj=[...m.values()];ii.forEach((id,k)=>diag[id]+=jj[k]**2);return [ii,jj]});
 let lambda=1e-10;for(let i=3;i<D;i++)diag[i]+=lambda;diag.fill(1,0,3);
 function mv(v){let out=Float64Array.from(v,t=>lambda*t);for(let [ids,j] of rr){let s=0;for(let k=0;k<ids.length;k++)s+=j[k]*v[ids[k]];for(let k=0;k<ids.length;k++)out[ids[k]]+=j[k]*s}out.fill(0,0,3);return out}
 let x=new Float64Array(D),r=b.slice(),z=Float64Array.from(r,(v,i)=>v/diag[i]),p=z.slice(),rz=dot(r,z),tol=Math.max(1e-12,maxabs(b)*1e-3);
 for(let it=0;it<Math.min(500,D)&&maxabs(r)>tol;it++){let ap=mv(p),den=dot(p,ap);if(den<=0||!Number.isFinite(den))break;let alpha=rz/den;for(let i=3;i<D;i++){x[i]+=alpha*p[i];r[i]-=alpha*ap[i]}z=Float64Array.from(r,(v,i)=>v/diag[i]);let next=dot(r,z),beta=next/rz;for(let i=3;i<D;i++)p[i]=z[i]+beta*p[i];rz=next}
 return x;
}
function lbfgs(m,start,g,plane,tol){
 let u=start.slice(),initial=state(m,u,g,plane,true),diag=new Float64Array(u.length);
 for(let [ids,j] of initial.rows){let local=new Map();ids.forEach((id,k)=>local.set(id,(local.get(id)||0)+j[k]));for(let [id,v] of local)diag[id]+=v*v}
 let pre=Float64Array.from(diag,(v,i)=>i<3?0:1/Math.sqrt(Math.max(v,1))),q=Float64Array.from(u,(v,i)=>pre[i]?v/pre[i]:0),hist=[];
 let evaluate=q=>{let uu=Float64Array.from(q,(v,i)=>v*pre[i]),s=state(m,uu,g,plane);return {u:uu,...s,gq:Float64Array.from(s.grad,(v,i)=>v*pre[i])}};
 let cur=evaluate(q),it=0;
 for(;it<3000&&maxabs(cur.grad)>tol;it++){
  let h=cur.gq.slice(),alpha=[];
  for(let k=hist.length-1;k>=0;k--){let x=hist[k],v=x.rho*dot(x.s,h);alpha[k]=v;for(let i=3;i<h.length;i++)h[i]-=v*x.y[i]}
  let last=hist.at(-1),scale=last?dot(last.s,last.y)/dot(last.y,last.y):1;for(let i=3;i<h.length;i++)h[i]*=scale;
  for(let k=0;k<hist.length;k++){let x=hist[k],beta=x.rho*dot(x.y,h);for(let i=3;i<h.length;i++)h[i]+=x.s[i]*(alpha[k]-beta)}
  let dir=Float64Array.from(h,v=>-v),gd=dot(cur.gq,dir);if(!(gd<0)){hist=[];dir=Float64Array.from(cur.gq,v=>-v);gd=-dot(cur.gq,cur.gq)}
  let step=1,trial,qq,ok=false;for(let ls=0;ls<40;ls++){qq=Float64Array.from(q,(v,i)=>v+step*dir[i]);trial=evaluate(qq);if(trial.E<=cur.E+1e-4*step*gd+1e-20){ok=true;break}step*=.5}if(!ok)break;
  let ss=Float64Array.from(qq,(v,i)=>v-q[i]),yy=Float64Array.from(trial.gq,(v,i)=>v-cur.gq[i]),sy=dot(ss,yy);if(sy>1e-25){hist.push({s:ss,y:yy,rho:1/sy});if(hist.length>30)hist.shift()}
  q=qq;cur=trial;
 }
 return {u:cur.u,...cur,residual:maxabs(cur.grad),iterations:it,accepted:maxabs(cur.grad)<=tol&&Number.isFinite(cur.E)};
}
function relax(m,start,g,plane,tol=1e-7){
 let u=start.slice(),s,its=0;
 for(;its<18;its++){
  s=state(m,u,g,plane,true);if(maxabs(s.grad)<=tol)break;let step=pcg(s.rows,s.grad,m.N),gd=dot(s.grad,step);if(!(gd<0))break;let t=1,ok=false;
  for(let j=0;j<35;j++){let trial=Float64Array.from(u,(v,i)=>v+t*step[i]),et=state(m,trial,g,plane).E;if(et<=s.E+1e-4*t*gd+1e-20){u=trial;ok=true;break}t*=.5}if(!ok)break;
 }
 s=state(m,u,g,plane);let res={u,...s,residual:maxabs(s.grad),iterations:its,accepted:maxabs(s.grad)<=tol&&Number.isFinite(s.E)};
 if(!res.accepted){let alt=lbfgs(m,u,g,plane,tol);if(alt.residual<res.residual&&alt.E<=res.E+1e-14)res=alt}
 return res;
}
function simulate(net,cfg){
 let m=setup(net,cfg.pattern,cfg.density),u=new Float64Array(3*m.N),n0=m.active.filter(Boolean).length,frames=[],removedEnergy=0,relaxEnergy=0,work=0,prevStress=0,prevG=0,maxResidual=0;
 for(let k=0;k<=cfg.steps;k++){
  let g=.5*k/cfg.steps,s=relax(m,u,g,cfg.plane),avalanche=0;let preStress=s.stress;
  if(!s.accepted){frames.push({gamma:g,accepted:false,residual:s.residual});break}u=s.u;
  for(let event=0;event<=n0;event++){
   let failed=[];m.active.forEach((on,i)=>{if(on&&s.lengths[i]/m.rest[i]-1>cfg.threshold)failed.push(i)});if(!failed.length)break;
   let before=s.E;for(let i of failed)m.active[i]=false;let after=state(m,u,g,cfg.plane).E;removedEnergy+=before-after;avalanche+=failed.length;s=relax(m,u,g,cfg.plane);relaxEnergy+=after-s.E;u=s.u;if(!s.accepted)break;
  }
  maxResidual=Math.max(maxResidual,s.residual);if(!s.accepted){frames.push({gamma:g,accepted:false,residual:s.residual});break}
  work+=(g-prevG)*(preStress+prevStress)/2;prevG=g;prevStress=s.stress;
  let f={gamma:g,accepted:true,stress:s.stress,preStress,energy:s.E,damage:1-m.active.filter(Boolean).length/n0,avalanche,removedEnergy,relaxEnergy,work,residual:s.residual};
  if(cfg.spatial&&k%Math.max(1,Math.floor(cfg.steps/40))===0){f.u=Array.from(u);f.forces=s.forces;f.active=m.active.slice()}
  frames.push(f);if(cfg.checkpoint&&k%10===0)fs.writeFileSync(cfg.checkpoint,JSON.stringify({...cfg,seed:net.seed,frames,status:'partial'}));if(f.damage>.98)break;
 }
 let good=frames.filter(f=>f.accepted),peak=good.reduce((a,b)=>b.stress>a.stress?b:a,good[0]);
 return {...cfg,seed:net.seed,nodes:m.N,edges:n0,z:m.z,lock_count:m.locked.length,lock_spread:m.lock_spread,locked:m.locked,frames,maxResidual,status:frames.every(f=>f.accepted)?'converged':'unresolved',peakStress:peak?.stress,peakGamma:peak?.gamma,workToPeak:peak?.work,last:good.at(-1)};
}
export {setup,state,relax,simulate};
if(!isMainThread){parentPort.postMessage(simulate(workerData.net,workerData.cfg))}
else if(process.argv[2]==='run'){
 let nets=JSON.parse(fs.readFileSync(new URL('networks.json',import.meta.url))),out=process.argv[3]||'runs-100',steps=Number(process.argv[4]||100);fs.mkdirSync(new URL(out+'/',import.meta.url),{recursive:true});let jobs=[];
 for(let net of nets)for(let plane of [1,2])for(let threshold of [.2,.1])for(let [pattern,density] of [['baseline',0],['clustered',.15],['distributed',.15],['clustered',.3],['distributed',.3]])jobs.push({net,cfg:{plane,threshold,pattern,density,steps,spatial:net.seed===29&&plane===1&&threshold===.2}});
 let cursor=0,done=0;await Promise.all(Array.from({length:Number(process.env.WORKERS||4)},async()=>{while(cursor<jobs.length){let i=cursor++,j=jobs[i],name=`seed${j.net.seed}-p${j.cfg.plane}-t${j.cfg.threshold}-${j.cfg.pattern}-${j.cfg.density}.json`,path=new URL(out+'/'+name,import.meta.url);if(fs.existsSync(path)){done++;continue}let result=await new Promise((res,rej)=>{let w=new Worker(new URL(import.meta.url),{workerData:j});w.once('message',res);w.once('error',rej)});fs.writeFileSync(path,JSON.stringify(result));console.log(++done,'/',jobs.length,name,result.status,result.last?.damage,result.maxResidual)}}));
}
