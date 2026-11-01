"""Original independent stdlib checks of data fidelity, pairing and excluded cases."""
from pathlib import Path
import sys
import json,math,statistics,hashlib
P=Path(__file__).parent;P=P.parent if P.name=='integration' else P;R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('/private/tmp/scienceclaw-final-media-publication');d=json.loads((P/'web/crosslinks.json').read_text());src=json.loads((R/'collagen-network-atlas/data/density.json').read_text());assert len(d['rows'])==len(src['rows'])==6300
index=lambda r:(r['family'],r['seed'],r['angle'],r['count'],r['pattern']);S={index(r):r for r in src['rows']};assert len(S)==6300
for r in d['rows']:
 for k,v in r.items():assert v==S[index(r)].get(k),(index(r),k)
assert sum(r['count']==0 for r in d['rows'])==252
assert d['agingDefault']['defaults']['count']==12 and d['parameters']=={'stiffness':.2,'rupture':.3}
D={index(r):r for r in d['rows']};examples=[]
for family,pattern in [('isotropic','distributed'),('isotropic','clustered'),('modular','clustered')]:
 x={'family':family,'pattern':pattern,'count':12,'angle':0}
 for metric in ['stiffness','work','failureStrain']:
  a=[D[(family,s,0,12,pattern)] for s in [17,29,43]];b=[D[(family,s,0,0,'distributed')] for s in [17,29,43]];x[metric]={'mean_paired_ratio':statistics.mean(r[metric]/z[metric] for r,z in zip(a,b)),'qualified':all(not r[metric+'Unresolved'] and not z[metric+'Unresolved'] for r,z in zip(a,b))}
 examples.append(x)
m=json.loads((P/'web/microrheology.json').read_text());assert len(m['rows'])==2560 and len(m['meshComparisons'])==1600
raw=json.loads((R/'collagen-network-atlas/microrheology/results.json').read_text());rawrows=[r for c in raw['results'] for r in c['rows']];export=[r for r in m['rows'] if r['model']=='drag'];assert len(export)==960
key=lambda r:(r['n'],r['family'],r['seed'],r['pattern'],r['direction'],r['omega'],r['damaged']);lookup={key(r):r for r in export}
for r in rawrows:
 q=lookup[key(r)];assert all(q[k]==v for k,v in r.items());assert q['resolved']==(r['residual']<1e-7 and math.isfinite(r['selfAmplitude']) and r['selfAmplitude']>0)
bad=[r for r in export if not r['resolved']];assert len(bad)==2 and all(r['n']==14 and r['family']=='modular' and r['seed']==43 and r['pattern']=='distributed' and r['damaged'] and r['omega']==0 for r in bad)
poro=json.loads((R/'collagen-fenicsx-poroelastic/web/results.json').read_text());fine=[r for r in poro['rows'] if r['model']=='poro' and r['level']==2];assert [r for r in m['rows'] if r['model']=='poro']==fine
common=[]
for seed in [17,29,43,67,83]:
 if all(lookup[(14,'modular',seed,p,di,0,dam)]['resolved'] for p in ['distributed','clustered'] for di in [0,1] for dam in [False,True]):common.append(seed)
assert common==[17,29,67,83]
f=json.loads((P/'web/micro-fields.json').read_text());assert len(f['cases'])==4
for family in ['isotropic','modular']:
 cs=[c for c in f['cases'] if c['family']==family];assert cs[0]['X']==cs[1]['X'] and cs[0]['edges']==cs[1]['edges'] and cs[0]['probe']==cs[1]['probe'] and cs[0]['lesion']==cs[1]['lesion']
 for c in cs:
  assert c['n']==14 and c['seed']==17 and len(c['X'])==392 and len(c['free'])==288
  for q in c['fields']:assert len(q['real'])==len(q['imag'])==288 and all(math.isfinite(x) for x in q['real']+q['imag'])
r=json.loads((P/'web/crosslink-replay.json').read_text());assert len(r['cases'])==4
for c in r['cases']:
 assert all(a['q']<=b['q'] for a,b in zip(c['frames'],c['frames'][1:]));assert all(len(q['x'])==2*c['net']['N'] and len(q['forces'])==len(c['net']['edges']) and len(q['linkForces'])==len(c['net']['links']) for q in c['frames'])
 for kind in ['alive','linkAlive']:
  assert all(not (not x and y) for a,b in zip(c['frames'],c['frames'][1:]) for x,y in zip(a[kind],b[kind]))
assert hashlib.sha256((P/'web/data.json').read_bytes()).hexdigest()==hashlib.sha256((R/'collagen-evidence-atlas/web/data.json').read_bytes()).hexdigest()
checks=m['meshComparisons']; chosen=[]
for seed in [17,29,43,67,83]:
 rows=[r for r in checks if r['n']==10 and r['family']=='isotropic' and r['pattern']=='distributed' and r['seed']==seed and r['permeability']==0.001 and r['omega']==0.1 and r['metric']=='selfAmplitude']
 if len(rows)==2 and all(r['resolved'] for r in rows):chosen.append(seed)
assert chosen==[29,67,83]
lookup_f={(r['model'],r['seed'],r['direction'],r['damaged']):r for r in m['rows'] if r['n']==10 and r['family']=='isotropic' and r['pattern']=='distributed' and r['omega']==0.1 and (r['model']=='drag' or r['permeability']==0.001)}
qr={model:statistics.mean(statistics.mean(lookup_f[(model,s,d,True)]['selfAmplitude']/lookup_f[(model,s,d,False)]['selfAmplitude'] for d in [0,1]) for s in chosen) for model in ['drag','poro']}
assert abs(qr['poro']-1.0255820508283633)<1e-12 and abs(qr['drag']-1.0339678385345195)<1e-12
qualified_example={'seeds':chosen,'poro_ratio':qr['poro'],'matched_drag_ratio':qr['drag'],'matches_original_qualified_summary':True}
result={'qualified_poro_example':qualified_example,'density_rows_exact':6300,'shared_zero_controls':252,'uniform_drag_rows_exact':960,'fine_poro_rows_exact':1600,'mesh_comparisons_preserved':1600,'uniform_drag_unresolved_static_rows':2,'matched_modular_static_seed_set':common,'fixed_field_cases':4,'force_replay_cases':4,'no_healing_or_interpolation_added':True,'measured_3D_data_unchanged':True,'density_example_summaries':examples,'scope':'Saved-data integrity and matched aggregation checks; no new solver or biological validation.'};(P/'DATA-VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
