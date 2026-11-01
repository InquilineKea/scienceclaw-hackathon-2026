"""Original stdlib export of existing saved comparisons; never executes source JS or solvers."""
from pathlib import Path
import sys
import json,csv,hashlib,shutil,subprocess,math
P=Path(__file__).parent;P=P.parent if P.name=='integration' else P;R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('/private/tmp/scienceclaw-final-media-publication');I=P/'inputs';I.mkdir(exist_ok=True);manifest=[]
def read(rel):
 s=R/rel;b=s.read_bytes();t=I/s.name
 if t.exists() and t.read_bytes()!=b:t=I/(rel.split('/')[0]+'-'+s.name)
 t.write_bytes(b);manifest.append({'source':rel,'private_input':str(t.relative_to(P)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});return b.decode()
def js(rel):return json.loads(read(rel).split('=',1)[1].strip().rstrip(';'))
def save(name,x):
 b=json.dumps(x,separators=(',',':'),allow_nan=False).encode();(P/'web'/name).write_bytes(b);return {'file':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
d=json.loads(read('collagen-network-atlas/data/density.json'));a=json.loads(read('collagen-network-atlas/data/aging.json'))
keys=['family','seed','angle','count','pattern','stiffness','work','failureStrain','workBeforeDamage','workBeforeCollagenDamage','firstDamageStrain','lastIntactStrain','finalDamage','linkDamage','valid','censored','criterion','stiffnessUnresolved','workUnresolved','failureStrainUnresolved','workBeforeDamageUnresolved','workBeforeCollagenDamageUnresolved']
exports=[save('crosslinks.json',{'rows':[{k:r.get(k) for k in keys} for r in d['rows']],'families':sorted({r['family'] for r in d['rows']}),'seeds':d['seeds'],'angles':d['angles'],'counts':d['counts'],'parameters':d['parameters'],'resolution':d['resolution'],'scope':d['scope'],'agingDefault':{'defaults':a['defaults'],'scope':a['scope'],'rows':a['rows'],'baseline':a['baseline']},'source':'Saved960step density sweep with per-metric qualification flags. No new solver or chronological-age mapping.'})]
replay=json.loads(read('collagen-network-atlas/force-replay/replay.json'));exports.append(save('crosslink-replay.json',replay))
drag=json.loads(read('collagen-network-atlas/microrheology/results.json'));poro=json.loads(read('collagen-fenicsx-poroelastic/web/results.json'));comp=list(csv.DictReader(read('collagen-fenicsx-poroelastic/web/comparisons.csv').splitlines()));validation=json.loads(read('collagen-fenicsx-poroelastic/web/validation.json'));summary=json.loads(read('collagen-fenicsx-poroelastic/web/summary.json'))
rows=[]
for c in drag['results']:
 for r in c['rows']:
  q=dict(r,model='drag',level=None,permeability=None);q['resolved']=math.isfinite(r['residual']) and r['residual']<1e-7 and math.isfinite(r['selfAmplitude']) and r['selfAmplitude']>0;rows.append(q)
rows += [r for r in poro['rows'] if r['model']=='poro' and r['level']==2]
for r in comp:
 for k in list(r):
  if k=='resolved':r[k]=r[k]=='True'
  elif k not in ['family','pattern','metric']:r[k]=float(r[k]) if r[k] not in ['','None'] else None
exports.append(save('microrheology.json',{'rows':rows,'meshComparisons':comp,'qualifiedSummary':summary,'validation':validation,'seeds':[17,29,43,67,83],'omegas':[0,.03,.1,.3,1,3],'sizes':[10,14],'scope':'Saved linear harmonic responses; same paired geometry/probe/lesion, dimensionless frequencies. Fine-pressure poro rows preserve algebraic and separate mesh qualification.'}))
f=js('collagen-fenicsx-poroelastic/web/data.js');exports.append(save('micro-fields.json',{'cases':f['animation'],'context':{'n':14,'nodes':196,'seed':17,'direction':0,'omega':.1,'permeability':.001,'pressureLevel':2},'scope':'Saved phasor examples only, reconstructed phase is not progressive damage. Both patterns share probe/lesion and common vector scales.'}))
record={'source_snapshot':subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','rev-parse','origin/main'],cwd=R,text=True).strip(),'inputs':manifest,'exports':exports,'copied_values_without_fitting':True,'new_simulations':False};(P/'DATA-PROVENANCE.json').write_text(json.dumps(record,indent=2));print(json.dumps({'density_rows':len(d['rows']),'micro_rows':len(rows),'mesh_comparisons':len(comp),'exports':exports},indent=2))
