'use strict';
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const M=require('./model.js'),D=JSON.parse(fs.readFileSync(path.join(__dirname,'baseline.json'),'utf8'));
const hash=crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'model.js'))).digest('hex');
if(hash!==D.modelHash)throw Error('Model fingerprint mismatch');
const out=process.argv[2];if(!out)throw Error('New output directory required');fs.mkdirSync(out);
const cases=[['aligned','tension'],['isotropic','tension'],['isotropic','shear'],['isotropic','confined'],['isotropic','pulse'],['isotropic','free']];
const reports=[];
for(const [family,mode] of cases){
 const net=M.build(family,17),ref=D.rows.find(r=>r.group==='topology'&&r.seed===17&&r.family===family&&r.mode===mode);
 if(!ref)throw Error('Missing stored comparison');
 const result=M.simulate(net,mode),m=result.metrics;
 const fields=['work','strength','finalDamage','retained'];
 const comparisons=fields.map(key=>({key,stored:ref[key],fresh:m[key],pass:Number.isFinite(m[key])&&Math.abs(m[key]-ref[key])<=1e-9+1e-6*Math.abs(ref[key])}));
 const residualOK=['pulse','free'].includes(mode)?true:m.valid&&m.maxResidual<2e-7;
 const dynamicOK=mode!=='pulse'||Math.abs(m.energyBalanceError/m.totalExternalWork)<.001;
 const record={family,mode,seed:17,modelHash:hash,geometry:net,result,comparisons,residualOK,dynamicOK,pass:comparisons.every(x=>x.pass)&&residualOK&&dynamicOK};
 fs.writeFileSync(path.join(out,family+'-'+mode+'.json'),JSON.stringify(record,null,2),{flag:'wx'});
 reports.push({family,mode,pass:record.pass,comparisons,residualOK,dynamicOK});console.log(JSON.stringify(reports.at(-1)));
}
fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify({modelHash:hash,reports,pass:reports.every(r=>r.pass)},null,2),{flag:'wx'});
if(!reports.every(r=>r.pass))process.exitCode=1;

