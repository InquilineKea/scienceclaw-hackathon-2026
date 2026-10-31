from pathlib import Path
import json,math,statistics,csv,hashlib
D=json.loads(Path('results.json').read_text());R=D['results'];rows=[];checks=[]
for c in R:
 checks+=c['checks']
 for r in c['rows']:
  r['resolved']=r['residual']<1e-7 and math.isfinite(r['selfAmplitude']) and r['selfAmplitude']>0
  rows.append(r)
paired=[]
for c in R:
 for dr in [0,1]:
  for w in [0,.03,.1,.3,1,3]:
   a=next(r for r in c['rows'] if not r['damaged'] and r['direction']==dr and r['omega']==w);b=next(r for r in c['rows'] if r['damaged'] and r['direction']==dr and r['omega']==w)
   paired.append(dict(family=c['family'],seed=c['seed'],n=c['n'],pattern=c['pattern'],direction=dr,omega=w,resolved=a['resolved'] and b['resolved'],localRatio=b['selfAmplitude']/a['selfAmplitude'] if a['resolved'] and b['resolved'] else None,remoteRatio=b['farRms']/a['farRms'] if a['resolved'] and b['resolved'] and a['farRms']>0 else None,phaseChange=b['phaseLag']-a['phaseLag']))
summary=[]
for n in [10,14]:
 for family in ['isotropic','modular']:
  for pattern in ['distributed','clustered']:
   for w in [0,.03,.1,.3,1,3]:
    ss=[r for r in paired if r['n']==n and r['family']==family and r['pattern']==pattern and r['omega']==w and r['resolved']]
    entry=dict(n=n,family=family,pattern=pattern,omega=w,resolvedPairs=len(ss),expectedPairs=10)
    for key in ['localRatio','remoteRatio']:
     seedmeans=[statistics.mean(r[key] for r in ss if r['seed']==seed and r[key] is not None) for seed in [17,29,43,67,83] if any(r['seed']==seed and r[key] is not None for r in ss)]
     entry[key]=dict(mean=statistics.mean(seedmeans),min=min(seedmeans),max=max(seedmeans),seeds=len(seedmeans)) if seedmeans else None
    for damaged in [False,True]:
     rr=[r for r in rows if r['n']==n and r['family']==family and r['pattern']==pattern and r['omega']==w and r['damaged']==damaged and r['resolved']]
     entry['damaged' if damaged else 'intact']={key:statistics.mean(r[key] for r in rr) if rr else None for key in ['selfAmplitude','farRms']}
    summary.append(entry)
assert len(R)==40 and len(rows)==960 and len(paired)==480
assert all(r['selfImag']<=1e-7 for r in rows if r['omega']>0 and r['resolved'])
validation=dict(configurations=40,harmonicSystems=960,resolved=sum(r['resolved'] for r in rows),unresolved=[{k:r[k] for k in ['n','family','seed','pattern','damaged','direction','omega','residual']} for r in rows if not r['resolved']],maxResolvedResidual=max(r['residual'] for r in rows if r['resolved']),maxHessianStepRelative=max(c.get('hessianStepRelative',0) for c in checks),maxHessianAsymmetry=max(c.get('asymmetry',0) for c in checks),maxLinearizationError=max(c.get('linearizationRelative',0) for c in checks),maxRestResidual=max(c.get('restResidual',0) for c in checks),passiveImaginarySign=True,elapsedSeconds=D['elapsedSeconds'])
Path('validation.json').write_text(json.dumps(validation,indent=2)+'\n');Path('summary.json').write_text(json.dumps(summary,indent=2)+'\n');Path('paired.json').write_text(json.dumps(paired,separators=(',',':'))+'\n')
with Path('paired.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(paired[0]),lineterminator='\n');w.writeheader();w.writerows(paired)
anims=[{'family':c['family'],'pattern':c['pattern'],'size':c['size'],'probe':c['probe'],'lesion':c['lesion'],**c['animation']} for c in R if c['animation']]
Path('animation.json').write_text(json.dumps(anims,separators=(',',':'))+'\n');Path('animation-data.js').write_text('globalThis.MICRO_ANIMATION='+json.dumps(anims,separators=(',',':'))+';\n')
print(json.dumps(validation,indent=2));print('At omega .1, n14:');print(json.dumps([r for r in summary if r['n']==14 and r['omega']==.1],indent=2))
