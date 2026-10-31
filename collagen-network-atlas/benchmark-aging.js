'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),A=require('./aging.js'),M=require('./model.js'),D=require('./data/directional.json');
const out=path.resolve(process.argv[2]||'');if(!process.argv[2]||fs.existsSync(out))throw Error('Provide a new output directory');fs.mkdirSync(out,{recursive:true});
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,f))).digest('hex'),rows=[],baseline=[],checks=[],start=Date.now();
for(const family of M.families){for(const seed of D.seeds){for(const angle of D.angles){const r=A.simulate(A.build(family,seed,{count:0}),angle,{frames:false});baseline.push({family,seed,angle,...r.metrics});}for(const pattern of ['distributed','clustered'])for(const angle of D.angles){const net=A.build(family,seed,{pattern}),r=A.simulate(net,angle,{frames:false});rows.push({family,seed,pattern,angle,count:12,stiffnessMultiplier:.2,rupture:.3,...r.metrics});}}console.log(family,rows.length+baseline.length,Math.round((Date.now()-start)/1000)+'s');}
for(const family of ['aligned','isotropic','loops'])for(const pattern of ['distributed','clustered'])for(const angle of [0,45,90]){
 const base=rows.find(r=>r.family===family&&r.seed===17&&r.pattern===pattern&&r.angle===angle);
 const r=A.simulate(A.build(family,17,{pattern}),angle,{steps:960,frames:false}).metrics;
 checks.push({family,seed:17,pattern,angle,kind:'half load step',baseWork:base.work,work:r.work,workRelativeChange:(r.work-base.work)/Math.max(base.work,1e-12),valid:r.valid,censored:r.censored});
}
const data={schema:1,version:A.version,modelHash:sha('model.js'),directionalHash:sha('directional.js'),agingHash:sha('aging.js'),benchmarkHash:sha('benchmark-aging.js'),defaults:A.defaults,seeds:D.seeds,angles:D.angles,options:{steps:480,cap:.85,probe:.002,tol:2e-9,maxIter:4800},scope:'Hypothetical extra connector springs on an unchanged collagen skeleton; no chronological age, AGE chemical concentration or calibrated chemistry. Paired baselines are freshly computed at the same resolution; the earlier directional dataset remains unchanged.',rows,baseline,checks};
fs.writeFileSync(path.join(out,'aging.json'),JSON.stringify(data,null,2)+'\n');fs.writeFileSync(path.join(out,'aging-data.js'),'globalThis.ATLAS_AGING_DATA='+JSON.stringify(data)+';\n');
const keys=Object.keys(rows[0]);fs.writeFileSync(path.join(out,'aging.csv'),keys.join(',')+'\n'+rows.map(r=>keys.map(k=>JSON.stringify(r[k]??null)).join(',')).join('\n')+'\n');
console.log(JSON.stringify({runs:rows.length,baselineRows:baseline.length,checks:checks.length,invalid:rows.filter(r=>!r.valid).length,capped:rows.filter(r=>r.censored).length,seconds:(Date.now()-start)/1000,output:out}));
