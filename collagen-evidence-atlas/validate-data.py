"""Original standard-library data-integrity checks for the visualization, no simulation rerun."""
from pathlib import Path
import json,math,hashlib
P=Path(__file__).parent;d=json.loads((P/'web/data.json').read_text());old=json.loads((P.parent/'collagen-nonlinear-heldout/fields.json').read_text());r=json.loads((P.parent/'collagen-nonlinear-heldout/results.json').read_text());ids=d['nodeIds'];expected=[i for i,b in enumerate(old['score']) if b];assert ids==expected and len(ids)==4355
max_rounding=0;model_checks=[]
for j,i in enumerate(ids):
 assert d['octants'][j]==sum((1<<k) if x>0 else 0 for k,x in enumerate(d['positions'][j]))
 for a,b in zip(d['positions'][j],old['nodes'][i]):max_rounding=max(max_rounding,abs(a-b))
 for a,b in zip(d['observed'][j],old['targets'][i]):max_rounding=max(max_rounding,abs(a-b))
for m in d['models']:
 sums=[0.0]*8;counts=[0]*8
 for j,i in enumerate(ids):
  for a,b in zip(m['vectors'][j],old['predictions'][m['key']][i]):max_rounding=max(max_rounding,abs(a-b))
  assert all(math.isfinite(x) for x in m['vectors'][j])
  e=sum((a-b)**2 for a,b in zip(m['vectors'][j],d['observed'][j]));o=d['octants'][j];sums[o]+=e;counts[o]+=1
 primary=math.sqrt(sum(s/n for s,n in zip(sums,counts))/8);saved=next(x for x in r['test'] if x['label']==m['key']);assert m['metrics']==saved['metrics'] and m['support']==saved['support'];drift=abs(primary-saved['metrics']['balanced_vector_RMSE_um']);assert drift<1e-5
 model_checks.append({'model':m['key'],'display_recomputed_equal_octant_RMSE_um':primary,'published_RMSE_um':saved['metrics']['balanced_vector_RMSE_um'],'rounding_drift_um':drift,'frozen_global_metrics_exactly_preserved':True})
assert max_rounding<=5.000001e-6
slab=[i for i,p in enumerate(d['positions']) if abs(p[2])<=30];assert len(slab)==744
result={'score_ids_exact':True,'eligible_vectors':len(ids),'default_Z60_slab_count':len(slab),'max_coordinate_or_vector_rounding_um':max_rounding,'model_checks':model_checks,'source_snapshot':d['sourceSnapshot'],'data_sha256':hashlib.sha256((P/'web/data.json').read_bytes()).hexdigest(),'scope':'Checks preserve exported values, frozen score membership and exact global metrics; not new biological/model validation.'};(P/'DATA-VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
