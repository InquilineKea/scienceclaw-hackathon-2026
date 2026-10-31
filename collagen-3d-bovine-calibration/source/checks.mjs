import fs from 'node:fs';import {setup,state,relax} from './solver.mjs';
const nets=JSON.parse(fs.readFileSync(new URL('networks.json',import.meta.url))),records=[],cal=[];let worstGrad=0,worstStress=0,worstOld=0;
const old=JSON.parse(fs.readFileSync(new URL('../oxidative-tensegrity/experiments/junction-angle-20261031/three-d/verified/refined/rows.json',import.meta.url)));
for(let net of nets){
 let base=setup(net),D=base.N*3,u=Float64Array.from({length:D},(_,i)=>i<3?0:Math.sin(i*1.2)*1e-4),dir=Float64Array.from({length:D},(_,i)=>i<3?0:Math.cos(i*.7)/Math.sqrt(D)),eps=1e-6,s=state(base,u,.03,1),ep=state(base,Float64Array.from(u,(v,i)=>v+eps*dir[i]),.03,1).E,em=state(base,Float64Array.from(u,(v,i)=>v-eps*dir[i]),.03,1).E;
 let analytic=s.grad.reduce((a,v,i)=>a+v*dir[i],0),ge=Math.abs((ep-em)/(2*eps)-analytic),se=Math.abs((state(base,u,.03+eps,1).E-state(base,u,.03-eps,1).E)/(2*eps)-s.stress);worstGrad=Math.max(worstGrad,ge);worstStress=Math.max(worstStress,se);
 let mods=[];for(let plane of [1,2]){let vals=[];for(let g of [.0005,.001,.002]){let r=relax(base,new Float64Array(D),g,plane,1e-9);if(!r.accepted)throw Error('calibration convergence');vals.push({gamma:g,G:r.stress/g,energy:r.E,residual:r.residual})}mods.push({plane,values:vals,G:vals[1].G})}
 let G0=mods.reduce((s,x)=>s+x.G,0)/2;cal.push({seed:net.seed,nodes:base.N,z:base.z,G_dimensionless:G0,scale_Pa:9.522231628684587/G0,planes:mods,eta_Pa_s:3.8911402496361376/(2*Math.PI)});
 let full=setup(net,'baseline',0,4),r=relax(full,new Float64Array(D),.001,1,1e-9),arch=old.find(x=>x.seed===net.seed&&x.z_requested===4&&x.gamma===.001),er=Math.abs(r.E-arch.energy)/arch.energy;worstOld=Math.max(worstOld,er);records.push({seed:net.seed,restEnergy:state(base,new Float64Array(D),0).E,gradientError:ge,stressError:se,archivedEnergy:arch.energy,newEnergy:r.E,relativeEnergyDifference:er,residual:r.residual});
}
let out={records,worstGrad,worstStress,worstOld,calibration:cal,checksPass:worstGrad<1e-7&&worstStress<1e-7&&worstOld<.001};fs.writeFileSync(new URL('checks.json',import.meta.url),JSON.stringify(out,null,2));console.log(JSON.stringify(out,null,2));if(!out.checksPass)process.exitCode=1;
