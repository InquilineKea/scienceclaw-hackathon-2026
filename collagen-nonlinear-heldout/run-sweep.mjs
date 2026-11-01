import fs from 'node:fs';import{spawn}from'node:child_process';import crypto from'node:crypto';
const root=new URL('.',import.meta.url).pathname, out=root+'runs';fs.mkdirSync(out,{recursive:true});
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(root+p)).digest('hex');
fs.writeFileSync(root+'audit/PRODUCTION-HASHES.json',JSON.stringify(Object.fromEntries(['solver.cpp','solver-local','material.mjs','PROTOCOL-FROZEN.md','inputs/Pos007-q110.bin'].map(p=>[p,hash(p)])),null,2));
const jobs=[];for(const b of[-1,.0025,.01,.04])for(const y of[-1,.01,.04])jobs.push({b,y,id:`Pos007-b${b}-y${y}-q110-s10`});let next=0;
async function worker(){while(next<jobs.length){const j=jobs[next++],prefix=out+'/'+j.id;fs.writeFileSync(prefix+'.config.json',JSON.stringify(j));console.log('START',j.id,new Date().toISOString());const result=await new Promise(resolve=>{const log=fs.openSync(prefix+'.log','w'),p=spawn(root+'solver-local',[root+'inputs/Pos007-q110.bin',prefix,''+j.b,''+j.y,'10'],{stdio:['ignore',log,log]});const t=setTimeout(()=>p.kill('SIGTERM'),900000);p.on('exit',(code,signal)=>{clearTimeout(t);fs.closeSync(log);resolve({code,signal,finished:new Date().toISOString()})})});fs.writeFileSync(prefix+'.exit.json',JSON.stringify(result));console.log('DONE',j.id,JSON.stringify(result))}}
await Promise.all([worker(),worker()]);
