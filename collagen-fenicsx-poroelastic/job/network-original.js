'use strict';
// Original finite-network harmonic probe experiment. Standard Node only.
const fs=require('node:fs'),M=require('./solid-source/model.js'),A=require('./solid-source/aging.js');
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),norm=a=>Math.sqrt(dot(a,a));
function build(family,seed,n,pattern){
 const size=(n-1)/5,net=M.build(family,seed,{n,edges:Math.round(82*n*n/36),phi:.06*size,lengthBias:size});
 net.X=net.X.map(x=>x*size);net.edges.forEach(e=>e.L*=size);net.hinges.forEach(h=>h.K/=size);net.p.phi*=size;
 const keys=new Set(net.edges.map(e=>e.i*net.N+e.j)),rng=M.rng(seed+20261031),ks=net.edges.map(e=>.08*e.A/e.L).sort((a,b)=>a-b),kref=ks[Math.floor(ks.length/2)],links=[];
 for(let i=0;i<net.N;i++)for(let j=i+1;j<net.N;j++){const dx=net.X[2*i]-net.X[2*j],dy=net.X[2*i+1]-net.X[2*j+1],L=Math.hypot(dx,dy);if(keys.has(i*net.N+j)||L>.46)continue;const mx=(net.X[2*i]+net.X[2*j])/2,my=(net.X[2*i+1]+net.X[2*j+1])/2,r=rng();links.push({i,j,L,k:.2*kref/.08,threshold:.3,rank:pattern==='distributed'?r:Math.hypot(mx-size/2,my-size/2)+.04*r});}
 links.sort((a,b)=>a.rank-b.rank);net.links=links.slice(0,Math.round(24*n*n/36));
 const free=[];for(let i=0;i<net.N;i++){const x=i%n,y=Math.floor(i/n);if(x&&x<n-1&&y&&y<n-1)free.push(2*i,2*i+1);}
 const near=(x,y)=>Array.from({length:net.N},(_,i)=>i).filter(i=>free.includes(2*i)).sort((i,j)=>Math.hypot(net.X[2*i]-x,net.X[2*i+1]-y)-Math.hypot(net.X[2*j]-x,net.X[2*j+1]-y));
 const probe=near(.35*size,.5*size).slice(0,4),lesion=net.edges.map((e,idx)=>({idx,r:Math.hypot((net.X[2*e.i]+net.X[2*e.j])/2-.55*size,(net.X[2*e.i+1]+net.X[2*e.j+1])/2-.5*size)})).sort((a,b)=>a.r-b.r).slice(0,3).map(e=>e.idx);
 return{net,free,probe,lesion,kref,size};
}
function hessian(o,state,h){const {net,free,kref}=o,N=free.length,K=Array.from({length:N},()=>new Float64Array(N));for(let j=0;j<N;j++){const x=net.X.slice(),y=net.X.slice();x[free[j]]+=h;y[free[j]]-=h;const a=A.energy(net,x,state).g,b=A.energy(net,y,state).g;for(let i=0;i<N;i++)K[i][j]=(a[free[i]]-b[free[i]])/(2*h*kref);}let asym=0,scale=0;for(let i=0;i<N;i++)for(let j=0;j<N;j++){asym=Math.max(asym,Math.abs(K[i][j]-K[j][i]));scale=Math.max(scale,Math.abs(K[i][j]));}for(let i=0;i<N;i++)for(let j=0;j<i;j++)K[i][j]=K[j][i]=(K[i][j]+K[j][i])/2;return{K,asym:asym/scale,zeroDiagonal:K.filter((r,i)=>r[i]<=1e-12).length};}
function mv(K,x){const r=new Float64Array(x.length);for(let i=0;i<x.length;i++){let s=0;for(let j=0;j<x.length;j++)s+=K[i][j]*x[j];r[i]=s;}return r;}
function solve(K,b,w){
 // Complex-symmetric preconditioned conjugate gradients; verify true residual.
 const N=b.length,xr=new Float64Array(N),xi=new Float64Array(N),rr=Float64Array.from(b),ri=new Float64Array(N),pr=new Float64Array(N),pi=new Float64Array(N);
 const pre=(r,i)=>{const a=new Float64Array(N),c=new Float64Array(N);for(let j=0;j<N;j++){const z=K[j][j],den=z*z+w*w;a[j]=(r[j]*z+i[j]*w)/den;c[j]=(i[j]*z-r[j]*w)/den;}return[a,c];};
 const cd=(a,c,b,d)=>[dot(a,b)-dot(c,d),dot(a,d)+dot(c,b)],div=(a,c)=>{const den=c[0]**2+c[1]**2;return[(a[0]*c[0]+a[1]*c[1])/den,(a[1]*c[0]-a[0]*c[1])/den];};
 let [zr,zi]=pre(rr,ri),rho=cd(rr,ri,zr,zi);pr.set(zr);pi.set(zi);let it=0;
 for(;it<3000;it++){const ar=mv(K,pr),ai=mv(K,pi);for(let i=0;i<N;i++){ar[i]-=w*pi[i];ai[i]+=w*pr[i];}const alpha=div(rho,cd(pr,pi,ar,ai));if(!alpha.every(Number.isFinite))break;
 for(let i=0;i<N;i++){xr[i]+=alpha[0]*pr[i]-alpha[1]*pi[i];xi[i]+=alpha[0]*pi[i]+alpha[1]*pr[i];rr[i]-=alpha[0]*ar[i]-alpha[1]*ai[i];ri[i]-=alpha[0]*ai[i]+alpha[1]*ar[i];}if(Math.hypot(norm(rr),norm(ri))/norm(b)<1e-9)break;
 [zr,zi]=pre(rr,ri);const next=cd(rr,ri,zr,zi),beta=div(next,rho);for(let i=0;i<N;i++){const a=pr[i],c=pi[i];pr[i]=zr[i]+beta[0]*a-beta[1]*c;pi[i]=zi[i]+beta[0]*c+beta[1]*a;}rho=next;
 }
 const ar=mv(K,xr),ai=mv(K,xi);for(let i=0;i<N;i++){ar[i]-=w*xi[i]+b[i];ai[i]+=w*xr[i];}return{real:Array.from(xr),imag:Array.from(xi),residual:Math.hypot(norm(ar),norm(ai))/norm(b),iterations:it};
}
function metrics(o,b,s){const {net,free,size,probe}=o;let re=0,im=0;for(let i=0;i<free.length;i++){re+=b[i]*s.real[i];im+=b[i]*s.imag[i];}const cx=probe.reduce((a,i)=>a+net.X[2*i],0)/4,cy=probe.reduce((a,i)=>a+net.X[2*i+1],0)/4;let far=0,count=0;const bins=Array.from({length:10},(_,i)=>({r:(i+.5)*.2,sum:0,count:0}));
 for(let j=0;j<free.length;j+=2){const i=free[j]/2,r=Math.hypot(net.X[2*i]-cx,net.X[2*i+1]-cy),amp2=s.real[j]**2+s.imag[j]**2+s.real[j+1]**2+s.imag[j+1]**2,k=Math.floor(r/.2);if(k<bins.length){bins[k].sum+=amp2;bins[k].count++;}if(r>=.6){far+=amp2;count++;}}
 return{selfAmplitude:Math.hypot(re,im),selfReal:re,selfImag:im,phaseLag:Math.atan2(-im,re),farRms:Math.sqrt(far/count),farNodes:count,bins:bins.map(v=>({r:v.r,count:v.count,rms:v.count?Math.sqrt(v.sum/v.count):null}))};
}
function run(family,seed,n,pattern){const o=build(family,seed,n,pattern),rows=[],checks=[],fields=[];for(const damaged of [false,true]){const state=A.state(o.net);if(damaged)o.lesion.forEach(k=>state.alive[k]=false);const h=hessian(o,state,1e-6),hh=hessian(o,state,5e-7);let err=0,sc=0;for(let i=0;i<h.K.length;i++)for(let j=0;j<h.K.length;j++){err+= (h.K[i][j]-hh.K[i][j])**2;sc+=hh.K[i][j]**2;}checks.push({damaged,hessianStepRelative:Math.sqrt(err/sc),asymmetry:h.asym,zeroDiagonal:h.zeroDiagonal,restResidual:Math.max(...A.energy(o.net,o.net.X,state).g.map(Math.abs))});
 for(const direction of [0,1]){const b=o.free.map(k=>o.probe.includes(Math.floor(k/2))&&k%2===direction?.25:0);for(const omega of [0,.03,.1,.3,1,3]){const s=solve(hh.K,b,omega);const row={family,seed,n,pattern,damaged,direction,omega,...metrics(o,b,s),residual:s.residual,iterations:s.iterations};rows.push(row);if(seed===17&&n===14&&direction===0&&omega===.1)fields.push({damaged,...s});
 if(omega===.1){const max=Math.max(...s.real.map(Math.abs)),amplitude=1e-5/max;for(const factor of [1,.5]){const dx=s.real.map(v=>v*amplitude*factor),x=o.net.X.slice();o.free.forEach((k,i)=>x[k]+=dx[i]);const grad=A.energy(o.net,x,state).g,linear=mv(hh.K,dx).map(v=>v*o.kref),actual=o.free.map(k=>grad[k]);checks.push({damaged,direction,factor,linearizationRelative:norm(actual.map((v,i)=>v-linear[i]))/Math.max(norm(linear),1e-20),maxProbeDisplacement:1e-5*factor});}}
 }} }
 return{family,seed,n,pattern,size:o.size,nodeCount:o.net.N,fiberCount:o.net.edges.length,connectorCount:o.net.links.length,probe:o.probe,lesion:o.lesion,lesionVolume:o.lesion.reduce((a,k)=>a+o.net.edges[k].A*o.net.edges[k].L,0),collagenVolume:o.net.p.phi,kref:o.kref,checks,rows,animation:fields.length?{net:o.net,free:o.free,fields}:null};}
module.exports={build,hessian,solve,metrics,run};
if(require.main===module){const start=Date.now(),results=[];for(const n of [10,14])for(const family of ['isotropic','modular'])for(const seed of [17,29,43,67,83])for(const pattern of ['distributed','clustered']){const r=run(family,seed,n,pattern);results.push(r);fs.writeFileSync('partial.json',JSON.stringify(results));console.log(JSON.stringify({n,family,seed,pattern,maxResidual:Math.max(...r.rows.map(x=>x.residual)),seconds:(Date.now()-start)/1000}));}fs.writeFileSync('results.json',JSON.stringify({elapsedSeconds:(Date.now()-start)/1000,results}));}
