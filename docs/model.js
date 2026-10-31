/* Original dependency-free 2D research toy. No imports, network, or file access.
   All constitutive parameters are hypothetical; see METHODS.md. */
(function(root){
'use strict';
const families=['aligned','isotropic','hierarchical','modular','loops','bottleneck','heterogeneous'];
const defaults={n:6,edges:82,phi:.06,diameter:.025,crimp:.04,bend:20,compression:.08,
 rupture:.24,disorder:.18,sacrificial:0,elastin:0,distribution:0,lengthBias:1,
 density:1,damping:.12,pulse:8,acceleration:.018,collapse:20};
const sum=a=>a.reduce((s,x)=>s+x,0), dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
function rng(seed){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}
function build(family='isotropic',seed=1,params={}){
 const p={...defaults,...params},r=rng(seed),n=p.n,N=n*n,X=[];
 for(let y=0;y<n;y++)for(let x=0;x<n;x++)X.push(x/(n-1)+(x&&x<n-1?(r()-.5)*.30/(n-1):0),y/(n-1)+(y&&y<n-1?(r()-.5)*.30/(n-1):0));
 const candidates=[],hub=[Math.floor(n/3)*n+Math.floor(n/3),Math.floor(2*n/3)*n+Math.floor(2*n/3)];
 for(let i=0;i<N;i++)for(let j=i+1;j<N;j++){
  const dx=X[2*j]-X[2*i],dy=X[2*j+1]-X[2*i+1],L=Math.hypot(dx,dy),cross=(X[2*i]<.5)!==(X[2*j]<.5),quad=k=>(X[2*k]>=.5?1:0)+(X[2*k+1]>=.5?2:0);
  let score=p.lengthBias*L+.16*r();
  if(family==='aligned')score+=.65*Math.abs(dy)/L;
  if(family==='modular')score+=(quad(i)!==quad(j)?.70:0);
  if(family==='bottleneck')score+=(cross?4:0);
  if(family==='heterogeneous')score-=hub.includes(i)||hub.includes(j)?.65:0;
  if(family==='hierarchical'){
   const trunk=k=>Math.abs(X[2*k+1]-.5)<.15;
   score-=trunk(i)&&trunk(j)?.30:0;score+=quad(i)!==quad(j)&&!(trunk(i)||trunk(j))?.45:0;
  }
  if(family==='loops')score+=.32*Math.abs(Math.abs(dx)-Math.abs(dy))/L;
  candidates.push({i,j,L,score,cross});
 }
 candidates.sort((a,b)=>a.score-b.score||a.i-b.i||a.j-b.j);
 const parent=Array.from({length:N},(_,i)=>i),find=x=>{while(parent[x]!==x){parent[x]=parent[parent[x]];x=parent[x];}return x;},selected=[],keys=new Set();
 function add(e){selected.push(e);keys.add(e.i*N+e.j);}
 for(const e of candidates)if(find(e.i)!==find(e.j)){parent[find(e.i)]=find(e.j);add(e);}
 for(const e of candidates){if(selected.length>=Math.max(N-1,p.edges))break;if(keys.has(e.i*N+e.j)||family==='bottleneck'&&e.cross)continue;add(e);}
 const weights=selected.map(e=>Math.exp(p.distribution*(2*r()-1))),den=sum(selected.map((e,k)=>e.L*weights[k]));
 const edges=selected.map((e,k)=>({...e,A:p.phi*weights[k]/den,threshold:p.rupture*(1+p.disorder*(2*r()-1)),sac:r()<p.sacrificial}));
 const adj=Array.from({length:N},()=>[]);edges.forEach((e,k)=>{adj[e.i].push([e.j,k]);adj[e.j].push([e.i,k]);});
 const hinges=[];
 // One most nearly antiparallel fiber continuation per junction. No cross-over junctions.
 adj.forEach((nb,j)=>{let best=null;
  for(let a=0;a<nb.length;a++)for(let b=a+1;b<nb.length;b++){
   const [i,ei]=nb[a],[k,ek]=nb[b],ux=X[2*i]-X[2*j],uy=X[2*i+1]-X[2*j+1],vx=X[2*k]-X[2*j],vy=X[2*k+1]-X[2*j+1];
   const ang=Math.atan2(ux*vy-uy*vx,ux*vx+uy*vy);
   if(!best||Math.abs(ang)>Math.abs(best.angle))best={i,j,k,ei,ek,angle:ang};
  }
  if(best&&Math.abs(best.angle)>Math.PI*.60){const a=edges[best.ei],b=edges[best.ek];hinges.push({...best,K:p.bend*Math.sqrt(a.A*b.A)*p.diameter**2/(16*((a.L+b.L)/2))});}
 });
 return{family,seed,p,N,X,edges,hinges,adj};
}
function state(net){return{alive:net.edges.map(()=>true),sac:net.edges.map(e=>e.sac),released:0,sacrificialDissipation:0,damageDissipation:0};}
function axial(e,p){
 const toe=.08,c=p.crimp;
 if(e<0){const b=.025,u=-e,soft=.08,t=p.compression;
  if(u<=b)return{f:t*e,w:.5*t*e*e};
  const z=Math.max(0,u-.6);return{f:-t*(b+soft*(u-b))-p.collapse*z**3,w:t*(.5*b*b+b*(u-b)+.5*soft*(u-b)**2)+p.collapse*z**4/4};
 }
 if(e<=c)return{f:toe*e,w:.5*toe*e*e};
 const q=e-c;return{f:toe*c+q+4*q*q*q,w:.5*toe*c*c+toe*c*q+.5*q*q+q**4};
}
function energy(net,x,s,details=false){
 const g=new Float64Array(x.length),forces=details?[]:null,strains=details?[]:null,edgeU=details?[]:null;let U=0;
 net.edges.forEach((e,k)=>{
  const dx=x[2*e.j]-x[2*e.i],dy=x[2*e.j+1]-x[2*e.i+1],L=Math.max(1e-10,Math.hypot(dx,dy)),strain=L/e.L-1,a=axial(strain,net.p);
  let f=(s.alive[k]?a.f:0)*e.A+net.p.elastin*e.A*strain,w=((s.alive[k]?a.w:0)+.5*net.p.elastin*strain*strain)*e.A*e.L;
  if(s.alive[k]&&s.sac[k]&&strain>0){f+=.3*e.A*strain;w+=.15*e.A*e.L*strain*strain;}
  U+=w;const fx=f*dx/L,fy=f*dy/L;g[2*e.i]-=fx;g[2*e.i+1]-=fy;g[2*e.j]+=fx;g[2*e.j+1]+=fy;
  if(details){forces.push(f);strains.push(strain);edgeU.push(w);}
 });
 for(const h of net.hinges){if(!s.alive[h.ei]||!s.alive[h.ek])continue;
  const ux=x[2*h.i]-x[2*h.j],uy=x[2*h.i+1]-x[2*h.j+1],vx=x[2*h.k]-x[2*h.j],vy=x[2*h.k+1]-x[2*h.j+1],u2=Math.max(1e-12,ux*ux+uy*uy),v2=Math.max(1e-12,vx*vx+vy*vy);
  let d=Math.atan2(ux*vy-uy*vx,ux*vx+uy*vy)-h.angle;d=Math.atan2(Math.sin(d),Math.cos(d));
  const t=h.K*d;U+=.5*h.K*d*d;
  const ai=[t*uy/u2,-t*ux/u2],ak=[-t*vy/v2,t*vx/v2];
  for(let c=0;c<2;c++){g[2*h.i+c]+=ai[c];g[2*h.k+c]+=ak[c];g[2*h.j+c]-=ai[c]+ak[c];}
 }
 return{U,g,forces,strains,edgeU};
}
function boundary(net,mode,q){
 const fixed=new Map(),deriv=new Map(),a=mode==='tensionY'?1:0;
 function set(i,c,v,d=0){fixed.set(2*i+c,v);deriv.set(2*i+c,d);}
 for(let i=0;i<net.N;i++){
  const x=net.X[2*i],y=net.X[2*i+1];
  if(mode==='shear'){
   if(y===0){set(i,0,x);set(i,1,y);}if(y===1){set(i,0,x+q,1);set(i,1,y);}
  }else if(mode==='biaxial'){
   if(x===0||x===1)set(i,0,.5+(x-.5)*(1-q),-(x-.5));
   if(y===0||y===1)set(i,1,.5+(y-.5)*(1-q),-(y-.5));
  }else if(mode==='pulse'){
   if(x===0){set(i,0,x);set(i,1,y);}
  }else if(mode!=='free'){
   const v=a?y:x,sign=mode==='compression'||mode==='confined'?-1:1;
   if(v===0){set(i,a,0);if((a?x:y)===0)set(i,1-a,0);}
   if(v===1)set(i,a,1+sign*q,sign);
   if(mode==='confined'&&(y===0||y===1))set(i,1,y);
  }
 }
 return{fixed,deriv,free:Array.from({length:2*net.N},(_,i)=>i).filter(i=>!fixed.has(i))};
}
function relax(net,x,s,b,opt={}){
 x=x.slice();for(const [i,v]of b.fixed)x[i]=v;
 const ids=b.free,m=ids.length,maxIter=opt.maxIter||1400,tol=opt.tol||2e-7,history=[];let ev=energy(net,x,s),g=ids.map(i=>ev.g[i]),it=0;
 for(;it<maxIter;it++){
  if(Math.max(0,...g.map(Math.abs))<tol)break;
  let d=g.slice(),alpha=[];
  for(let k=history.length-1;k>=0;k--){const h=history[k];alpha[k]=dot(h.s,d)*h.rho;d=d.map((v,i)=>v-alpha[k]*h.y[i]);}
  const last=history[history.length-1],scale=last?dot(last.s,last.y)/dot(last.y,last.y):1;
  d=d.map(v=>v*scale);
  for(let k=0;k<history.length;k++){const h=history[k],beta=dot(h.y,d)*h.rho;d=d.map((v,i)=>v+h.s[i]*(alpha[k]-beta));}
  d=d.map(v=>-v);if(dot(d,g)>=0){d=g.map(v=>-v);history.length=0;}
  const maxD=Math.max(...d.map(Math.abs));if(maxD>.04)d=d.map(v=>v*.04/maxD);
  const slope=dot(g,d);let step=1,newEv=null,nx;
  for(let ls=0;ls<30;ls++){nx=x.slice();for(let k=0;k<m;k++)nx[ids[k]]+=step*d[k];newEv=energy(net,nx,s);if(Number.isFinite(newEv.U)&&newEv.U<=ev.U+1e-4*step*slope)break;step*=.5;}
  if(step<1e-9)break;
  const ng=ids.map(i=>newEv.g[i]),ss=d.map(v=>step*v),yy=ng.map((v,i)=>v-g[i]),sy=dot(ss,yy);
  if(sy>1e-18){history.push({s:ss,y:yy,rho:1/sy});if(history.length>9)history.shift();}
  x=nx;ev=newEv;g=ng;
 }
 const residual=Math.max(0,...g.map(Math.abs));return{x,residual,iterations:it,converged:residual<tol};
}
function damage(net,x,s,heal=false){
 const before=energy(net,x,s),e=energy(net,x,s,true);let changed=false;
 net.edges.forEach((edge,k)=>{
  if(s.alive[k]&&e.strains[k]>edge.threshold){s.alive[k]=false;changed=true;}
 });
 const postBreak=energy(net,x,s);s.damageDissipation+=Math.max(0,before.U-postBreak.U);
 net.edges.forEach((edge,k)=>{
  if(s.alive[k]&&s.sac[k]&&e.strains[k]>.075){s.sac[k]=false;s.released++;changed=true;s.sacrificialDissipation+=.15*edge.A*edge.L*e.strains[k]**2;}
  // Reform only at zero extension: no mechanical energy is created at reattachment.
  if(heal&&s.alive[k]&&edge.sac&&!s.sac[k]&&e.strains[k]<=0){s.sac[k]=true;changed=true;}
 });
 return changed;
}
function connectivity(net,alive,mode='tension'){
 const a=mode==='shear'||mode==='tensionY'?1:0,seen=new Set(),q=[];
 for(let i=0;i<net.N;i++)if(net.X[2*i+a]===0){seen.add(i);q.push(i);}
 for(let h=0;h<q.length;h++)for(const [j,e]of net.adj[q[h]])if(alive[e]&&!seen.has(j)){seen.add(j);q.push(j);}
 const targets=Array.from({length:net.N},(_,i)=>i).filter(i=>net.X[2*i+a]===1);
 return{spanning:targets.some(i=>seen.has(i)),reachable:seen.size/net.N,rightFraction:targets.filter(i=>seen.has(i)).length/targets.length};
}
function simulate(net,mode='tension',opt={}){
 if(mode==='pulse'||mode==='free')return dynamic(net,mode,opt);
 const steps=opt.steps||60,cap=opt.cap??(mode==='shear'?.90:mode==='tension'||mode==='tensionY'?.85:.30),s=state(net),frames=[],curve=[];
 let x=net.X.slice(),work=0,peak=0,stop=null,failures=0,maxResidual=0,previousQ=0,previousForce=0,collapseUsed=false;
 let schedule=Array.from({length:steps+1},(_,i)=>cap*i/steps);
 if(opt.cycle)schedule=schedule.concat(Array.from({length:steps},(_,i)=>cap*(1-(i+1)/steps)));
 for(let z=0;z<schedule.length;z++){
  const q=schedule[z],b=boundary(net,mode,q);let result;
  for(let avalanche=0;avalanche<=net.edges.length+1;avalanche++){
   result=relax(net,x,s,b,opt);x=result.x;
   if(!result.converged){result=relax(net,x,s,b,{...opt,maxIter:(opt.maxIter||1400)*2});x=result.x;}
   if(!result.converged)break;
   if(!damage(net,x,s,!!opt.cycle))break;
  }
  maxResidual=Math.max(maxResidual,result.residual);if(!result.converged)failures++;
  const ev=energy(net,x,s,true),force=sum([...b.deriv].map(([i,d])=>ev.g[i]*d));
  collapseUsed=collapseUsed||ev.strains.some((e,k)=>s.alive[k]&&e<-.6);
  work+=.5*(force+previousForce)*(q-previousQ);peak=Math.max(peak,force);
  const lost=sum(net.edges.map((e,k)=>s.alive[k]?0:e.A*e.L))/net.p.phi,conn=connectivity(net,s.alive,mode);
  const mags=ev.forces.map(Math.abs),den=sum(mags),loc=den>0?sum(mags.map(f=>f*f))/(den*den):0;
  const row={q,force,work,energy:ev.U,damage:lost,retained:conn.rightFraction,spanning:conn.spanning,localization:loc,residual:result.residual,converged:result.converged};
  curve.push(row);if(opt.frames!==false)frames.push({x:x.slice(),alive:s.alive.slice(),sac:s.sac.slice(),forces:ev.forces,strains:ev.strains,...row});
  if(!stop&&(lost>=.20||!conn.spanning||peak>1e-5&&q>.08&&force<.5*peak))stop={index:z,q,work,reason:lost>=.20?'20% collagen volume ruptured':!conn.spanning?'lost spanning collagen path':'reaction below 50% of running peak'};
  previousQ=q;previousForce=force;
  if(stop&&!opt.cycle)break;
 }
 const end=curve[curve.length-1],stiffness=curve.length>1?curve[1].force/curve[1].q:0;
 return{mode,curve,frames,metrics:{work:stop?stop.work:work,censored:!stop,criterion:stop?.reason||'strain cap reached',failureStrain:stop?.q??null,strength:peak,stiffness,finalDamage:end.damage,retained:end.retained,localization:end.localization,maxResidual,unconvergedSteps:failures,valid:failures===0,collapseUsed,hysteresis:opt.cycle?work:null,sacrificialDissipation:s.sacrificialDissipation,damageDissipation:s.damageDissipation,cap,steps}};
}
function dynamic(net,mode,opt={}){
 const p=net.p,dt=opt.dt||.0125,T=p.pulse,endTime=2*T,steps=Math.ceil(endTime/dt),mass=p.density/net.N,s=state(net),b=boundary(net,mode,0),frames=[],curve=[];
 let x=net.X.slice(),v=new Float64Array(x.length),work=0,viscous=0,peak=0,stop=null,maxStrain=0,collapseUsed=false;
 for(let step=0;step<=steps;step++){
  const time=step*dt,acc=time<=T?p.acceleration*Math.sin(Math.PI*time/T):0,ev=energy(net,x,s,true);
  const reaction=sum([...b.fixed.keys()].filter(i=>i%2===0).map(i=>ev.g[i]-mass*acc));peak=Math.max(peak,Math.abs(reaction));
  collapseUsed=collapseUsed||ev.strains.some((e,k)=>s.alive[k]&&e<-.6);
  const kin=.5*mass*dot(v,v),lost=sum(net.edges.map((e,k)=>s.alive[k]?0:e.A*e.L))/p.phi,conn=connectivity(net,s.alive);
  maxStrain=Math.max(maxStrain,...ev.strains);
  const internalized=ev.U+viscous+s.damageDissipation+s.sacrificialDissipation;
  if(!stop&&(lost>=.20||!conn.spanning))stop={work:internalized,externalWork:work,peak,time,reason:lost>=.20?'20% collagen volume ruptured':'lost spanning collagen path'};
  if(step%Math.max(1,Math.round(steps/100))===0||step===steps){const row={q:time,force:reaction,work:internalized,externalWork:work,energy:ev.U,kinetic:kin,damage:lost,retained:conn.rightFraction,acceleration:acc};curve.push(row);if(opt.frames!==false)frames.push({...row,x:x.slice(),alive:s.alive.slice(),sac:s.sac.slice(),forces:ev.forces,strains:ev.strains});}
  if(step===steps)break;
  // Symplectic Euler with exact linear damping substep; damping acts on
  // deformation velocity only, so uniform free translation has no drag.
  const vxMean=sum(Array.from({length:net.N},(_,i)=>v[2*i]))/net.N,vyMean=sum(Array.from({length:net.N},(_,i)=>v[2*i+1]))/net.N;
  for(const i of b.free){
   const external=i%2===0?mass*acc:0;
   v[i]+=dt*(external-ev.g[i])/mass;
   const mean=mode==='free'?(i%2===0?vxMean+dt*acc:vyMean):0,old=v[i];v[i]=mean+(v[i]-mean)*Math.exp(-p.damping*dt);
   viscous+=.5*mass*((old-mean)**2-(v[i]-mean)**2);
   const dx=dt*v[i];x[i]+=dx;work+=external*dx;
  }
  for(const [i,z]of b.fixed){x[i]=z;v[i]=0;}
  damage(net,x,s,false);
 }
 const end=curve[curve.length-1],balance=work-end.energy-end.kinetic-viscous-s.damageDissipation-s.sacrificialDissipation;
 return{mode,curve,frames,metrics:{work:stop?stop.work:end.work,externalWork:stop?.externalWork??work,totalExternalWork:work,censored:!stop,criterion:stop?.reason||'pulse window ended',failureStrain:null,failureTime:stop?.time??null,strength:stop?.peak??peak,stiffness:null,finalDamage:end.damage,retained:end.retained,localization:null,maxResidual:null,unconvergedSteps:0,valid:Number.isFinite(work),hysteresis:null,sacrificialDissipation:s.sacrificialDissipation,damageDissipation:s.damageDissipation,viscousDissipation:viscous,kinetic:end.kinetic,energyBalanceError:balance,maxStrain,collapseUsed,dt,steps}};
}
function eigen(A,vectors=false){
 const n=A.length,a=A.map(r=>r.slice()),V=vectors?Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>+(i===j))):null;
 for(let sweep=0;sweep<90;sweep++){
  let mx=0;
  for(let p=0;p<n;p++)for(let q=p+1;q<n;q++){
   const apq=a[p][q];mx=Math.max(mx,Math.abs(apq));if(Math.abs(apq)<1e-13)continue;
   const tau=(a[q][q]-a[p][p])/(2*apq),t=(tau>=0?1:-1)/(Math.abs(tau)+Math.sqrt(1+tau*tau)),c=1/Math.sqrt(1+t*t),s=t*c;
   a[p][p]-=t*apq;a[q][q]+=t*apq;a[p][q]=a[q][p]=0;
   for(let k=0;k<n;k++)if(k!==p&&k!==q){const kp=a[k][p],kq=a[k][q];a[k][p]=a[p][k]=c*kp-s*kq;a[k][q]=a[q][k]=s*kp+c*kq;}
   if(V)for(let k=0;k<n;k++){const kp=V[k][p],kq=V[k][q];V[k][p]=c*kp-s*kq;V[k][q]=s*kp+c*kq;}
  }
  if(mx<1e-11)break;
 }
 const order=Array.from({length:n},(_,i)=>i).sort((i,j)=>a[i][i]-a[j][j]);return{values:order.map(i=>a[i][i]),vectors:V?order.map(i=>V.map(row=>row[i])):null};
}
function mincut(net,source,target,alive=net.edges.map(()=>true)){
 const n=net.N,cap=Array.from({length:n},()=>new Float64Array(n));net.edges.forEach((e,k)=>{if(alive[k])cap[e.i][e.j]=cap[e.j][e.i]=1;});let flow=0;
 for(;;){const prev=Array(n).fill(-1),q=[source];prev[source]=source;
  for(let h=0;h<q.length&&prev[target]<0;h++)for(let j=0;j<n;j++)if(prev[j]<0&&cap[q[h]][j]>0){prev[j]=q[h];q.push(j);}
  if(prev[target]<0)break;
  let j=target;while(j!==source){const i=prev[j];cap[i][j]--;cap[j][i]++;j=i;}flow++;
 }return flow;
}
function graphMetrics(net,mechanical=true){
 const n=net.N,m=net.edges.length,degrees=net.adj.map(a=>a.length),degree=sum(degrees)/n;
 const L=Array.from({length:n},()=>Array(n).fill(0)),W=L.map(r=>r.slice()),NL=L.map(r=>r.slice()),bw=Array(m).fill(0),weights=net.edges.map(e=>e.A/e.L),mw=sum(weights)/m;
 let xx=0,xy=0,yy=0,volume=0;
 net.edges.forEach((e,k)=>{const w=weights[k]/mw;for(const [M,z]of [[L,1],[W,w]]){M[e.i][e.i]+=z;M[e.j][e.j]+=z;M[e.i][e.j]-=z;M[e.j][e.i]-=z;}
  const dx=(net.X[2*e.j]-net.X[2*e.i])/e.L,dy=(net.X[2*e.j+1]-net.X[2*e.i+1])/e.L,V=e.A*e.L;volume+=V;xx+=V*dx*dx;xy+=V*dx*dy;yy+=V*dy*dy;
 });
 for(let i=0;i<n;i++)for(let j=0;j<n;j++)NL[i][j]=L[i][j]/Math.sqrt(degrees[i]*degrees[j]);
 const eig=eigen(L).values,weig=eigen(W).values,neig=eigen(NL).values;
 let triangles=0;
 net.adj.forEach((nb,i)=>{let links=0;for(let a=0;a<nb.length;a++)for(let b=a+1;b<nb.length;b++)if(L[nb[a][0]][nb[b][0]]<0)links++;triangles+=nb.length>1?2*links/(nb.length*(nb.length-1)):0;});
 const remaining=new Set(Array.from({length:n},(_,i)=>i)),core=degrees.slice();let kcore=0;
 while(remaining.size){let v=[...remaining].reduce((a,b)=>core[a]<core[b]?a:b);kcore=Math.max(kcore,core[v]);remaining.delete(v);for(const [j]of net.adj[v])if(remaining.has(j)&&core[j]>core[v])core[j]--;}
 for(let source=0;source<n;source++){
  const stack=[],pred=Array.from({length:n},()=>[]),sigma=Array(n).fill(0),dist=Array(n).fill(-1),q=[source];sigma[source]=1;dist[source]=0;
  for(let h=0;h<q.length;h++){const v=q[h];stack.push(v);for(const [w,e]of net.adj[v]){if(dist[w]<0){dist[w]=dist[v]+1;q.push(w);}if(dist[w]===dist[v]+1){sigma[w]+=sigma[v];pred[w].push([v,e]);}}}
  const delta=Array(n).fill(0);while(stack.length){const w=stack.pop();for(const [v,e]of pred[w]){const c=sigma[v]/sigma[w]*(1+delta[w]);bw[e]+=c;delta[v]+=c;}}
 }
 const groups=Array.from({length:n},(_,i)=>(net.X[2*i]>=.5?1:0)+(net.X[2*i+1]>=.5?2:0));let modularity=0;
 for(let i=0;i<n;i++)for(let j=0;j<n;j++)if(groups[i]===groups[j])modularity+=((i!==j&&L[i][j]<0?1:0)-degrees[i]*degrees[j]/(2*m))/(2*m);
 const out={degree,degreeVariance:sum(degrees.map(d=>(d-degree)**2))/n,coordinationExcess:degree-4,cycles:m-n+1,kcore,edgeConnectivity:Math.min(...Array.from({length:n-1},(_,i)=>mincut(net,0,i+1))),maxBetweenness:Math.max(...bw)/(n*(n-1)),clustering:triangles/n,modularity,anisotropy:Math.sqrt((xx-yy)**2+4*xy*xy)/volume,alignmentX:xx/volume,lambda2:eig[1],lambda3minus2:eig[2]-eig[1],weightedLambda2:weig[1],normalizedLambda2:neig[1],meanLength:sum(net.edges.map(e=>e.L))/m,volume};
 if(mechanical){
  const b=boundary(net,'tension',0),ids=b.free,s=state(net),h=1e-5,H=ids.map(()=>Array(ids.length).fill(0));
  ids.forEach((j,c)=>{const xp=net.X.slice(),xm=net.X.slice();xp[j]+=h;xm[j]-=h;const gp=energy(net,xp,s).g,gm=energy(net,xm,s).g;ids.forEach((i,r)=>H[r][c]=(gp[i]-gm[i])/(2*h));});
  for(let i=0;i<H.length;i++)for(let j=i+1;j<H.length;j++)H[i][j]=H[j][i]=(H[i][j]+H[j][i])/2;
  const ev=eigen(H,true),v=ev.vectors[0];out.hessianMin=ev.values[0];out.softModes=ev.values.filter(x=>x<1e-5).length;out.softIPR=sum(v.map(x=>x**4));out.hessianMax=ev.values.at(-1);
 }
 return out;
}
const api={families,defaults,rng,build,state,axial,energy,boundary,relax,damage,connectivity,simulate,dynamic,eigen,mincut,graphMetrics};
if(typeof module!=='undefined')module.exports=api;root.CollagenAtlas=api;
})(globalThis);
