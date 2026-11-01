/* Original bounded, dependency-free scientific worker. Local modules only. */
'use strict';
importScripts('solver/model.js','solver/directional.js','solver/aging.js','solver/micro.js');
const A=globalThis.AtlasAging,L=globalThis.LiveMicro;
const requireValue=(ok,message)=>{if(!ok)throw Error(message)};
self.onmessage=({data:c})=>{try{
 requireValue(CollagenAtlas.families.includes(c.family),'Unknown network');
 requireValue([17,29,43,67,83].includes(c.seed),'Unknown seed');
 requireValue(Number.isFinite(c.angle)&&c.angle>=0&&c.angle<=180,'Invalid angle');
 if(c.kind==='force'){
  requireValue(Number.isInteger(c.count)&&c.count>=0&&c.count<=24,'Invalid connector count');
  const cases=[];for(const pattern of ['distributed','clustered']){postMessage({type:'progress',message:'Solving '+pattern+' quasistatic loading at 960 steps…'});const net=A.build(c.family,c.seed,{count:c.count,stiffness:.2,rupture:.3,pattern}),r=A.simulate(net,c.angle,{steps:960});cases.push({family:c.family,pattern,net,metrics:r.metrics,frames:r.frames});}
  let fmax=0,minX=0,maxX=1,minY=0,maxY=1,qmax=0;for(const c of cases)for(const f of c.frames){qmax=Math.max(qmax,f.q);for(const v of [...f.forces,...f.linkForces])fmax=Math.max(fmax,Math.abs(v));for(let j=0;j<f.x.length;j+=2){minX=Math.min(minX,f.x[j]);maxX=Math.max(maxX,f.x[j]);minY=Math.min(minY,f.x[j+1]);maxY=Math.max(maxY,f.x[j+1]);}}
  postMessage({type:'result',data:{...c,cases,fmax:Math.max(fmax,1e-12),minX,maxX,minY,maxY,qmax,computed:true}});
 }else if(c.kind==='micro'){
  requireValue([10,14].includes(c.n),'Invalid size');requireValue(Number.isFinite(c.density)&&c.density>=0&&c.density<=24/36+1e-12,'Invalid density');requireValue([0,.03,.1,.3,1,3].includes(c.omega),'Invalid frequency');
  const cases=[],theta=c.angle*Math.PI/180;
  for(const pattern of ['distributed','clustered']){
   postMessage({type:'progress',message:'Building '+pattern+' intact/damaged tangent matrices…'});
   const o=L.build(c.family,c.seed,c.n,pattern,c.density),fields=[],checks=[];
   const b=o.free.map(k=>o.probe.includes(Math.floor(k/2))?.25*(k%2?Math.sin(theta):Math.cos(theta)):0);
   for(const damaged of [false,true]){
    const state=A.state(o.net);if(damaged)o.lesion.forEach(k=>state.alive[k]=false);
    const h=L.hessian(o,state,1e-6),hh=L.hessian(o,state,5e-7);let er=0,sc=0;
    for(let i=0;i<h.K.length;i++)for(let j=0;j<h.K.length;j++){er+=(h.K[i][j]-hh.K[i][j])**2;sc+=hh.K[i][j]**2;}
    const stepRelative=Math.sqrt(er/Math.max(sc,1e-30)),s=L.solve(hh.K,b,c.omega),finite=[...s.real,...s.imag].every(Number.isFinite),metric=finite?L.metrics(o,b,s):null,resolved=finite&&Number.isFinite(s.residual)&&s.residual<1e-7&&stepRelative<1e-5&&hh.asym<1e-5&&metric.selfAmplitude>0;
    checks.push({damaged,stepRelative,asymmetry:hh.asym,residual:s.residual,resolved});
    fields.push({model:'drag',damaged,...s,metrics:metric,resolved});
   }
   cases.push({n:c.n,family:c.family,seed:c.seed,pattern,size:o.size,X:o.net.X,free:o.free,edges:o.net.edges,links:o.net.links,probe:o.probe,lesion:o.lesion,fields,checks,connectorCount:o.net.links.length});
  }
  postMessage({type:'result',data:{...c,cases,computed:true}});
 }else throw Error('Unknown experiment');
 }catch(e){postMessage({type:'error',message:e.message});}};
