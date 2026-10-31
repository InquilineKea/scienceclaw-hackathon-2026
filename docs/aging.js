/* Original exploratory crosslink extension. No imports except the original model in Node.
   Added connector springs are separate from collagen fibers and their volume budget. */
(function(root){
'use strict';
const M=typeof module!=='undefined'?require('./model.js'):root.CollagenAtlas;
const D=typeof module!=='undefined'?require('./directional.js'):root.AtlasDirectional;
const defaults={count:12,stiffness:.2,rupture:.30,pattern:'distributed'};
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
function build(family='aligned',seed=17,parameters={}){
 const p={...defaults,...parameters};
 if(!Number.isInteger(p.count)||p.count<0||p.count>24||!Number.isFinite(p.stiffness)||p.stiffness<0||p.stiffness>2||!Number.isFinite(p.rupture)||p.rupture<=0||p.rupture>1||!['distributed','clustered'].includes(p.pattern))throw Error('Invalid crosslink parameters');
 const net=M.build(family,seed),keys=new Set(net.edges.map(e=>e.i*net.N+e.j)),random=M.rng(seed+20261031),candidates=[];
 const stiffnesses=net.edges.map(e=>e.A/e.L).sort((a,b)=>a-b),referenceK=stiffnesses[Math.floor(stiffnesses.length/2)];
 for(let i=0;i<net.N;i++)for(let j=i+1;j<net.N;j++){
  const dx=net.X[2*j]-net.X[2*i],dy=net.X[2*j+1]-net.X[2*i+1],L=Math.hypot(dx,dy);
  if(keys.has(i*net.N+j)||L>.46)continue;
  const mx=(net.X[2*i]+net.X[2*j])/2,my=(net.X[2*i+1]+net.X[2*j+1])/2,r=random();
  candidates.push({i,j,L,k:p.stiffness*referenceK,threshold:p.rupture,rank:p.pattern==='distributed'?r:Math.hypot(mx-.5,my-.5)+.04*r});
 }
 candidates.sort((a,b)=>a.rank-b.rank||a.i-b.i||a.j-b.j);if(candidates.length<p.count)throw Error('Too few local connector sites');
 return{...net,links:candidates.slice(0,p.count),crosslink:{...p,referenceK,eligibleSites:candidates.length}};
}
function state(net){return{...M.state(net),linkAlive:net.links.map(()=>true),linkDissipation:0};}
function energy(net,x,s,details=false){
 const e=M.energy(net,x,s,details),linkForces=[],linkStrains=[];let linkEnergy=0;
 net.links.forEach((l,k)=>{const dx=x[2*l.j]-x[2*l.i],dy=x[2*l.j+1]-x[2*l.i+1],L=Math.max(1e-10,Math.hypot(dx,dy)),dl=L-l.L,f=s.linkAlive[k]?l.k*dl:0,U=s.linkAlive[k]?.5*l.k*dl*dl:0;linkEnergy+=U;e.g[2*l.i]-=f*dx/L;e.g[2*l.i+1]-=f*dy/L;e.g[2*l.j]+=f*dx/L;e.g[2*l.j+1]+=f*dy/L;if(details){linkForces.push(f);linkStrains.push(dl/l.L);}});
 e.U+=linkEnergy;return{...e,linkEnergy,linkForces:details?linkForces:null,linkStrains:details?linkStrains:null};
}
// Same original L-BFGS algorithm, evaluated on collagen + connector energy.
function relax(net,x,s,b,opt={}){
 x=x.slice();for(const[i,v]of b.fixed)x[i]=v;
 const ids=b.free,m=ids.length,maxIter=opt.maxIter??4800,tol=opt.tol??2e-9,history=[];let ev=energy(net,x,s),g=ids.map(i=>ev.g[i]),it=0;
 for(;it<maxIter;it++){
  if(Math.max(0,...g.map(Math.abs))<tol)break;
  let d=g.slice(),alpha=[];
  for(let k=history.length-1;k>=0;k--){const h=history[k];alpha[k]=dot(h.s,d)*h.rho;d=d.map((v,i)=>v-alpha[k]*h.y[i]);}
  const last=history.at(-1),scale=last?dot(last.s,last.y)/dot(last.y,last.y):1;d=d.map(v=>v*scale);
  for(let k=0;k<history.length;k++){const h=history[k],beta=dot(h.y,d)*h.rho;d=d.map((v,i)=>v+h.s[i]*(alpha[k]-beta));}
  d=d.map(v=>-v);if(dot(d,g)>=0){d=g.map(v=>-v);history.length=0;}
  const maxD=Math.max(...d.map(Math.abs));if(maxD>.04)d=d.map(v=>v*.04/maxD);
  const slope=dot(g,d);let step=1,newEv,nx;
  for(let ls=0;ls<30;ls++){nx=x.slice();for(let k=0;k<m;k++)nx[ids[k]]+=step*d[k];newEv=energy(net,nx,s);if(Number.isFinite(newEv.U)&&newEv.U<=ev.U+1e-4*step*slope)break;step*=.5;}
  if(step<1e-9)break;
  const ng=ids.map(i=>newEv.g[i]),ss=d.map(v=>step*v),yy=ng.map((v,i)=>v-g[i]),sy=dot(ss,yy);
  if(sy>1e-18){history.push({s:ss,y:yy,rho:1/sy});if(history.length>9)history.shift();}
  x=nx;ev=newEv;g=ng;
 }
 const residual=Math.max(0,...g.map(Math.abs));return{x,residual,iterations:it,converged:residual<tol};
}
function damage(net,x,s){
 let changed=M.damage(net,x,s);const e=energy(net,x,s,true);
 net.links.forEach((l,k)=>{if(s.linkAlive[k]&&e.linkStrains[k]>l.threshold){s.linkAlive[k]=false;s.linkDissipation+=.5*l.k*(e.linkStrains[k]*l.L)**2;changed=true;}});return changed;
}
function simulate(net,angle,opt={}){
 const steps=opt.steps??480,cap=opt.cap??.85,probe=opt.probe??.002,tol=opt.tol??2e-9,maxIter=opt.maxIter??4800;
 if(!Number.isFinite(angle)||!Number.isInteger(steps)||steps<2||cap<=probe||probe<=0)throw Error('Invalid loading parameters');
 const s=state(net),frames=[],curve=[],schedule=[0,probe,...Array.from({length:steps},(_,i)=>cap*(i+1)/steps).filter(q=>q>probe)];
 let x=net.X.slice(),work=0,peak=0,previousQ=0,previousForce=0,stop=null,maxResidual=0,failures=0,stiffness=null,stiffnessValid=false,collapseUsed=false;
 for(const q of schedule){
  const b=D.boundary(net,angle,q);let result;
  for(let avalanche=0;avalanche<=net.edges.length+net.links.length+1;avalanche++){
   result=relax(net,x,s,b,{tol,maxIter});x=result.x;
   if(!result.converged){result=relax(net,x,s,b,{tol,maxIter:maxIter*2});x=result.x;}
   if(!result.converged||!damage(net,x,s))break;
  }
  maxResidual=Math.max(maxResidual,result.residual);if(!result.converged)failures++;
  const ev=energy(net,x,s,true),force=[...b.deriv].reduce((v,[i,d])=>v+ev.g[i]*d,0);
  work+=(force+previousForce)*.5*(q-previousQ);peak=Math.max(peak,force);
  const lost=net.edges.reduce((v,e,k)=>v+(s.alive[k]?0:e.A*e.L),0)/net.p.phi,linkDamage=s.linkAlive.length?s.linkAlive.filter(v=>!v).length/s.linkAlive.length:0;
  collapseUsed=collapseUsed||ev.strains.some((e,k)=>s.alive[k]&&e<-.6);
  const row={q,force,work,energy:ev.U,linkEnergy:ev.linkEnergy,damage:lost,linkDamage,residual:result.residual,converged:result.converged};curve.push(row);
  if(opt.frames!==false)frames.push({...row,x:x.slice(),alive:s.alive.slice(),linkAlive:s.linkAlive.slice(),forces:ev.forces,linkForces:ev.linkForces});
  if(q===probe){stiffness=force/probe;stiffnessValid=result.converged&&lost===0&&linkDamage===0;}
  if(!result.converged){stop={reason:'unconverged equilibrium',q};break;}
  if(lost>=.20||peak>1e-5&&q>.08&&force<.5*peak){stop={reason:lost>=.20?'20% collagen volume ruptured':'reaction below 50% of running peak',q};break;}
  previousQ=q;previousForce=force;
 }
 const end=curve.at(-1),valid=failures===0;
 return{mode:'age-crosslinks',angle,curve,frames,metrics:{stiffness,stiffnessValid,work,valid,censored:valid&&!stop,criterion:stop?.reason||'strain cap reached',failureStrain:valid&&stop?stop.q:null,finalDamage:end.damage,linkDamage:end.linkDamage,strength:peak,maxResidual,unconvergedSteps:failures,probe,steps,cap,tol,collapseUsed,damageDissipation:s.damageDissipation,linkDissipation:s.linkDissipation,sacrificialDissipation:s.sacrificialDissipation}};
}
const api={version:'age-connectors-v1',defaults,build,state,energy,damage,relax,simulate};root.AtlasAging=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
