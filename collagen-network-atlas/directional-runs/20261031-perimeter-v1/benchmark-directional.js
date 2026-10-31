'use strict';
// Original bounded, append-only directional benchmark; no external dependencies.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),M=require('./model.js'),A=require('./directional.js');
const out=path.resolve(process.argv[2]||'');if(!process.argv[2]||fs.existsSync(out))throw Error('Supply a new output directory');fs.mkdirSync(out,{recursive:true});
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,f))).digest('hex');
const rows=[],seeds=[17,29,43],angles=Array.from({length:12},(_,i)=>i*15),start=Date.now();
for(const family of M.families){for(const seed of seeds)for(const angle of angles){const r=A.simulate(M.build(family,seed),angle,{frames:false});rows.push({family,seed,angle,...r.metrics});}console.log(family,rows.length,Math.round((Date.now()-start)/1000)+'s');}
const checks=[];
for(const family of ['aligned','isotropic','loops'])for(const angle of [0,45,90]){
 const base=rows.find(r=>r.family===family&&r.seed===17&&r.angle===angle);
 for(const[label,opt]of [['half load step',{steps:480}],['tighter tolerance',{tol:2e-10,maxIter:9600}]]){
  const r=A.simulate(M.build(family,17),angle,{...opt,frames:false}).metrics;
  checks.push({family,seed:17,angle,label,baseWork:base.work,work:r.work,workRelativeChange:(r.work-base.work)/Math.max(base.work,1e-12),stiffnessRelativeChange:(r.stiffness-base.stiffness)/Math.max(base.stiffness,1e-12),valid:r.valid,censored:r.censored,criterion:r.criterion});
 }
}
const data={schema:1,protocol:A.version,modelHash:sha('model.js'),directionalHash:sha('directional.js'),benchmarkHash:sha('benchmark-directional.js'),seeds,angles,params:M.defaults,options:{steps:240,cap:.85,probe:.002,tol:2e-9,maxIter:4800},scope:'Independent fixed-perimeter directional tension experiment; not the original free-lateral X/Y grip protocols. 180 degrees is identical to 0. Work is a criterion-dependent work-density proxy, not crack fracture energy.',rows,checks};
fs.writeFileSync(path.join(out,'directional.json'),JSON.stringify(data,null,2)+'\n');fs.writeFileSync(path.join(out,'directional-data.js'),'globalThis.ATLAS_DIRECTIONAL_DATA='+JSON.stringify(data)+';\n');
const keys=Object.keys(rows[0]);fs.writeFileSync(path.join(out,'directional.csv'),keys.join(',')+'\n'+rows.map(r=>keys.map(k=>JSON.stringify(r[k]??null)).join(',')).join('\n')+'\n');
console.log(JSON.stringify({runs:rows.length,checks:checks.length,invalid:rows.filter(r=>!r.valid).length,capped:rows.filter(r=>r.censored).length,seconds:(Date.now()-start)/1000,output:out}));
