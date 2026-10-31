/* Original direction-controlled experiment. Reuses the unchanged energy/relaxation law.
   Perimeter displacement u = strain * n (n dot (X-center)); interior nodes relax. */
(function(root){
'use strict';
const M=typeof module!=='undefined'?require('./model.js'):root.CollagenAtlas;
const version='affine-perimeter-tension-v1';
function direction(angle){const a=((Number(angle)%180)+180)%180*Math.PI/180;return [Math.cos(a),Math.sin(a)];}
function boundary(net,angle,q){
 const n=direction(angle),fixed=new Map(),deriv=new Map(),nodes=[];
 for(let i=0;i<net.N;i++){
  const x=net.X[2*i],y=net.X[2*i+1];
  if(x!==0&&x!==1&&y!==0&&y!==1)continue;
  const projection=n[0]*(x-.5)+n[1]*(y-.5);nodes.push(i);
  for(let c=0;c<2;c++){const d=n[c]*projection;fixed.set(2*i+c,net.X[2*i+c]+q*d);deriv.set(2*i+c,d);}
 }
 return{fixed,deriv,nodes,free:Array.from({length:net.X.length},(_,i)=>i).filter(i=>!fixed.has(i))};
}
function simulate(net,angle,opt={}){
 const steps=opt.steps??240,cap=opt.cap??.85,probe=opt.probe??.002,tol=opt.tol??2e-9,maxIter=opt.maxIter??4800;
 if(!Number.isFinite(angle)||steps<2||cap<=probe||probe<=0)throw Error('Invalid directional parameters');
 const s=M.state(net),frames=[],curve=[],schedule=[0,probe,...Array.from({length:steps},(_,i)=>cap*(i+1)/steps).filter(q=>q>probe)];
 let x=net.X.slice(),work=0,peak=0,previousQ=0,previousForce=0,stop=null,maxResidual=0,failures=0,stiffness=null,stiffnessValid=false;
 for(const q of schedule){
  const b=boundary(net,angle,q);let result;
  for(let avalanche=0;avalanche<=net.edges.length+1;avalanche++){
   result=M.relax(net,x,s,b,{tol,maxIter});x=result.x;
   if(!result.converged){result=M.relax(net,x,s,b,{tol,maxIter:maxIter*2});x=result.x;}
   if(!result.converged||!M.damage(net,x,s))break;
  }
  maxResidual=Math.max(maxResidual,result.residual);if(!result.converged)failures++;
  const ev=M.energy(net,x,s,true),force=[...b.deriv].reduce((v,[i,d])=>v+ev.g[i]*d,0);
  work+=(force+previousForce)*.5*(q-previousQ);peak=Math.max(peak,force);
  const damage=net.edges.reduce((v,e,k)=>v+(s.alive[k]?0:e.A*e.L),0)/net.p.phi;
  const row={q,force,work,energy:ev.U,damage,residual:result.residual,converged:result.converged};curve.push(row);
  if(opt.frames!==false)frames.push({...row,x:x.slice(),alive:s.alive.slice(),forces:ev.forces});
  if(q===probe){stiffness=force/probe;stiffnessValid=result.converged&&damage===0;}
  if(!result.converged){stop={reason:'unconverged equilibrium',q};break;}
  if(damage>=.20||peak>1e-5&&q>.08&&force<.5*peak){stop={reason:damage>=.20?'20% fiber volume ruptured':'reaction below 50% of running peak',q};break;}
  previousQ=q;previousForce=force;
 }
 const end=curve.at(-1),valid=failures===0;
 return{mode:'directional',angle,curve,frames,metrics:{stiffness,stiffnessValid,work,valid,censored:valid&&!stop,criterion:stop?.reason||'strain cap reached',failureStrain:valid&&stop?stop.q:null,finalDamage:end.damage,strength:peak,maxResidual,unconvergedSteps:failures,probe,steps,cap,tol,damageDissipation:s.damageDissipation,sacrificialDissipation:s.sacrificialDissipation}};
}
const api={version,direction,boundary,simulate};root.AtlasDirectional=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
