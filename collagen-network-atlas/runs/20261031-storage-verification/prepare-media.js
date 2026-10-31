'use strict';
require('./run-guard.js').requireRun(__dirname,["data/media-input.json", "figures/benchmark.svg"]);
const fs=require('node:fs'),D=require('./data/results.json');require('./data/replays.js');const R=globalThis.ATLAS_REPLAYS;
const media={results:D,replays:R,scenarios:[
 {id:'tension',title:'Tension: strength and absorbed work trade places',keys:['aligned:tension','loops:tension'],labels:['Aligned bundles','Diagonal reinforcement'],subtitle:'X tension · frictionless grips · seed 17 · equal collagen volume 0.06'},
 {id:'shear',title:'A bottleneck depends on the direction of loading',keys:['bottleneck:shear','isotropic:shear'],labels:['Bottleneck in X','Disordered network'],subtitle:'Top moves in X; bottom fixed · seed 17 · same material and edge budgets'},
 {id:'pressure',title:'Confined compression: resistance is not failure toughness',keys:['isotropic:confined','bottleneck:confined'],labels:['Disordered network','Bottlenecked network'],subtitle:'X compression; Y boundary displacement locked · no solvent or pore pressure'},
 {id:'pulse',title:'Constrained acceleration: inertia loads the network',keys:['aligned:pulse','heterogeneous:pulse'],labels:['Aligned bundles','Degree heterogeneous'],subtitle:'Left clamped · a(t)=0.018 sin(pi t/8) for 0<t<8 · density=1 · seed 17'},
 {id:'free-vs-clamped',title:'Acceleration is not itself a stress specification',keys:['isotropic:free','isotropic:pulse'],labels:['Free: rigid translation','Left edge clamped'],subtitle:'Same graph, mass and body-force pulse · only the supports differ · seed 17'}
]};
fs.writeFileSync('data/media-input.json',JSON.stringify(media));
const names={aligned:'Aligned',isotropic:'Disordered',hierarchical:'Hierarchical',modular:'Modular',loops:'Diagonal loops',bottleneck:'Bottleneck',heterogeneous:'Heterogeneous'};
const txt=(x,y,t,size=14,color='#25483d')=>`<text x="${x}" y="${y}" font-family="sans-serif" font-size="${size}" fill="${color}">${t}</text>`;
let svg='<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="750" viewBox="0 0 1260 750"><title>450 collagen-inspired network computations</title><desc>Model work to the stopping criterion, means and sample standard deviations across five seeds. Capped runs do not determine toughness. Hypothetical dimensionless model.</desc><rect width="1260" height="750" fill="#f4f3ee"/>';
svg+=txt(35,48,'Fracture Atlas / a loading-dependent result',30)+txt(35,78,'36 nodes · 82 edges · collagen volume 0.06 · five seeds · no experimental calibration',16);
for(const [col,mode]of ['tension','shear','pulse'].entries()){
 const rr=D.summaries.filter(x=>x.mode===mode),mx=Math.max(...rr.map(x=>x.meanWork+x.sdWork))*1000,ox=35+col*415;
 svg+=txt(ox,130,{tension:'X tension',shear:'Shear',pulse:'Constrained pulse'}[mode],22);
 rr.forEach((r,i)=>{const y=173+i*60,x=ox+125,w=r.meanWork*1000/mx*230,lo=Math.max(0,(r.meanWork-r.sdWork)*1000/mx*230),hi=(r.meanWork+r.sdWork)*1000/mx*230;svg+=txt(ox,y+16,names[r.family]+(r.censored?'*':''),12)+`<rect x="${x}" y="${y}" width="${w}" height="21" fill="${r.censored?'#a6b09c':'#507c69'}"/><path d="M${x+lo} ${y+10}H${x+hi}M${x+lo} ${y+6}v8M${x+hi} ${y+6}v8" stroke="#263f35"/>`+txt(x,y+38,(r.meanWork*1000).toFixed(3)+' ± '+(r.sdWork*1000).toFixed(3),11);});
}
svg+=txt(35,635,'Work density × 10⁻³ E₀. Pulse work = stored elastic energy + irreversible and damping losses; kinetic energy excluded.',14)+txt(35,665,'Error bars: sample SD, n=5. *Includes runs ending before the criterion: observed protocol work, not complete toughness.',14)+txt(35,700,'No universal winner. X-tension Pareto frontier (mean work versus peak reaction): aligned bundles and diagonal reinforcement.',15);
fs.writeFileSync('figures/benchmark.svg',svg+'</svg>');
console.log('Prepared five simulation-derived animations and SVG figure input.');
