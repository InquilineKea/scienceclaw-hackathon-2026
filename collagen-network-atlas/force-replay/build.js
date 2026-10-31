'use strict';
const fs=require('node:fs'),A=require('../aging.js');
const saved=JSON.parse(fs.readFileSync('../data/density.json','utf8')).rows,cases=[];
for(const family of ['isotropic','modular'])for(const pattern of ['distributed','clustered']){
 const net=A.build(family,17,{count:24,pattern}),r=A.simulate(net,0,{steps:960});
 const old=saved.find(x=>x.family===family&&x.pattern===pattern&&x.count===24&&x.angle===0&&x.seed===17);
 for(const k of ['work','stiffness','failureStrain'])if(Math.abs(r.metrics[k]-old[k])>1e-12)throw Error('Replay differs: '+k);
 cases.push({family,pattern,net,metrics:r.metrics,frames:r.frames});
}
let fmax=0,qmax=0,minX=0,maxX=1,minY=0,maxY=1;
for(const c of cases)for(const f of c.frames){qmax=Math.max(qmax,f.q);for(const z of [...f.forces,...f.linkForces])fmax=Math.max(fmax,Math.abs(z));for(let i=0;i<f.x.length;i+=2){minX=Math.min(minX,f.x[i]);maxX=Math.max(maxX,f.x[i]);minY=Math.min(minY,f.x[i+1]);maxY=Math.max(maxY,f.x[i+1]);}}
const result={seed:17,count:24,angle:0,steps:960,sourceSnapshot:'7689daeea6371b76e6e5aa95ff7d560a1d4d4a94',scope:'Quasistatic solved states; playback speed is not physical time. Shared global force and coordinate scales. Traces freeze at stopping criteria.',fmax,qmax,minX,maxX,minY,maxY,cases};
fs.writeFileSync('replay.json',JSON.stringify(result));fs.writeFileSync('replay-data.js','globalThis.FORCE_REPLAY='+JSON.stringify(result)+';\n');console.log(cases.map(c=>({family:c.family,pattern:c.pattern,frames:c.frames.length,criterion:c.metrics.criterion})));
