'use strict';
// Original bounded parallel sweep; standard Node APIs only. No network or installs.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os');
const {Worker,isMainThread,parentPort}=require('node:worker_threads');
const A=require('./aging.js'),M=require('./model.js'),D=require('./density.js');
if(!isMainThread){
 parentPort.on('message',task=>{
  try {
   const net=A.build(task.family,task.seed,{count:task.count,pattern:task.pattern,stiffness:.2,rupture:.3});
   const coarse=A.simulate(net,task.angle,{steps:480,frames:false}),fine=A.simulate(net,task.angle,{steps:960,frames:false});
   const c=D.summarize(coarse),f=D.summarize(fine);
   parentPort.postMessage({task,coarse:c,metrics:f,check:D.compareResolution(c,f),eligibleSites:net.crosslink.eligibleSites,nodeCount:net.N,fiberCount:net.edges.length,fineCurve:fine.curve,coarseCurve:coarse.curve});
  }catch(e){parentPort.postMessage({task,error:String(e.stack||e)});}
 });
}else{
 const out=path.resolve(process.argv[2]||'');if(!process.argv[2]||fs.existsSync(out))throw Error('Provide a new output directory');fs.mkdirSync(out,{recursive:true});
 const smoke=process.argv.includes('--smoke'),seeds=smoke?[17]:[17,29,43],angles=smoke?[0]:Array.from({length:12},(_,i)=>i*15),counts=smoke?[0,12,24]:Array.from({length:13},(_,i)=>i*2);
 const families=smoke?['isotropic']:M.families,tasks=[];
 for(const family of families)for(const seed of seeds)for(const angle of angles)for(const count of counts)for(const pattern of count===0?['distributed']:['distributed','clustered'])tasks.push({family,seed,angle,count,pattern});
 const nWorkers=Math.max(1,Math.min(8,os.availableParallelism(),Number(process.env.DENSITY_WORKERS)||8)),rows=[],workers=[],started=new Date().toISOString();let next=0,done=0,failed=false;
 const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 const files=['model.js','directional.js','aging.js','density.js','benchmark-density.js','check-density.js'];
 const sources={};for(const name of files){fs.copyFileSync(path.join(__dirname,name),path.join(out,name));sources[name]=hash(path.join(out,name));}
 const rawFile=fs.createWriteStream(path.join(out,'raw-curves.ndjson.gz'),{flags:'wx'}),raw=require('node:zlib').createGzip({level:6});raw.pipe(rawFile);
 const timer=setTimeout(()=>{failed=true;for(const w of workers)w.terminate();raw.end();fs.writeFileSync(path.join(out,'FAILED.json'),JSON.stringify({reason:'20-minute workload limit',done,expected:tasks.length}));process.exitCode=2;},1200000);
 function finish(){
  clearTimeout(timer);for(const w of workers)w.terminate();rawFile.once('finish',()=>{
   rows.sort((a,b)=>a.family.localeCompare(b.family)||a.seed-b.seed||a.angle-b.angle||a.count-b.count||a.pattern.localeCompare(b.pattern));
   const data={schema:1,version:D.version,started,finished:new Date().toISOString(),compute:{runtime:process.version,architecture:process.arch,platform:process.platform,workers:nWorkers,gpuUsed:false},sourceHashes:sources,seeds,angles,counts,parameters:{stiffness:.2,rupture:.3},resolution:{coarse:480,displayed:960,threshold:.05},scope:'Original dimensionless collagen skeleton; hypothetical added connectors. Density=count/36 nodes, not chemical concentration. Damage onset and failure are mechanical events, not a thermodynamic phase transition.',rows};
   fs.writeFileSync(path.join(out,'density.json'),JSON.stringify(data)+'\n');
   fs.writeFileSync(path.join(out,'density-data.js'),'globalThis.ATLAS_DENSITY_DATA='+JSON.stringify(data)+';\n');
   const keys=['family','seed','angle','count','pattern','densityPerNode','eligibleSiteFraction','stiffness','work','failureStrain','workBeforeDamage','energyBeforeDamage','firstDamageStrain','lastIntactStrain','workBeforeCollagenDamage','firstCollagenDamageStrain','strainAtPeak','workToPeak','largestCollagenDamageIncrement','valid','censored','criterion','stiffnessUnresolved','workUnresolved','failureStrainUnresolved','workBeforeDamageUnresolved','workBeforeCollagenDamageUnresolved'];
   fs.writeFileSync(path.join(out,'density.csv'),keys.join(',')+'\n'+rows.map(r=>keys.map(k=>JSON.stringify(r[k]??null)).join(',')).join('\n')+'\n');
   const manifest={version:D.version,files:{}};for(const name of fs.readdirSync(out)){const p=path.join(out,name);manifest.files[name]={bytes:fs.statSync(p).size,sha256:hash(p)};}fs.writeFileSync(path.join(out,'MANIFEST.json'),JSON.stringify(manifest,null,2)+'\n');
   fs.writeFileSync(path.join(out,'FINISHED.json'),JSON.stringify({status:'completed',uniqueConfigurations:rows.length,solverRuns:rows.length*2,invalid:rows.filter(r=>!r.valid).length,capped:rows.filter(r=>r.censored).length,workUnresolved:rows.filter(r=>r.workUnresolved).length,manifestSha256:hash(path.join(out,'MANIFEST.json'))},null,2)+'\n');
   console.log(JSON.stringify({status:'completed',configurations:rows.length,solves:rows.length*2,seconds:(Date.now()-Date.parse(started))/1000}));
  });raw.end();
 }
 function dispatch(w){if(next<tasks.length)w.postMessage(tasks[next++]);}
 for(let i=0;i<nWorkers;i++){
  const w=new Worker(__filename,{env:{},resourceLimits:{maxOldGenerationSizeMb:512}});workers.push(w);
  w.on('message',r=>{if(failed)return;if(r.error){failed=true;clearTimeout(timer);fs.writeFileSync(path.join(out,'FAILED.json'),JSON.stringify(r));for(const x of workers)x.terminate();raw.end();process.exitCode=2;return;}
   raw.write(JSON.stringify(r)+'\n');
   rows.push({...r.task,densityPerNode:r.task.count/r.nodeCount,eligibleSiteFraction:r.task.count/r.eligibleSites,eligibleSites:r.eligibleSites,nodeCount:r.nodeCount,fiberCount:r.fiberCount,...r.metrics,...r.check,coarse:r.coarse});
   done++;if(done%100===0)console.log(JSON.stringify({completed:done,total:tasks.length,seconds:(Date.now()-Date.parse(started))/1000}));if(done===tasks.length)finish();else dispatch(w);
  });
  w.on('error',e=>{if(failed)return;failed=true;clearTimeout(timer);for(const x of workers)x.terminate();raw.end();fs.writeFileSync(path.join(out,'FAILED.json'),JSON.stringify({error:String(e),done}));process.exitCode=2;});dispatch(w);
 }
}
