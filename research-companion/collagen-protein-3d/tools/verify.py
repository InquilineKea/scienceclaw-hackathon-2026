#!/usr/bin/env python3
"""Independent stdlib integrity / paired endpoint / source-geometry verification."""
import argparse,csv,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parents[1];OUT=ROOT/'site' if (ROOT/'site').exists() else BASE/'docs/research-companion/collagen-protein-3d';D=OUT/'data';S=BASE/'outputs/collagen-protein-3d';RAW=BASE/'work/3d-results'
def main():
 m=json.loads((D/'manifest.json').read_text())
 for f in m['files']:
  b=(OUT/f['path']).read_bytes();assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
 cases=json.loads((D/'cases.json').read_text());source=json.loads((S/'FULL-CASE-SUMMARIES.json').read_text())
 assert cases==[{k:v for k,v in c.items() if k!='traceback'} for c in source]
 assert len(cases)==1088 and sum(c['accepted'] for c in cases)==1082
 graphs={}
 for p in D.glob('geometry-*.json'):
  for g in json.loads(p.read_text()):
   original=json.loads((RAW/'study/graphs'/(g['id']+'.json')).read_text());assert g==original
   assert len(g['edges'])==4*g['n'] and len(g['x0'])==g['n'];graphs[g['id']]=g
 assert len(graphs)==64
 curves=json.loads((D/'curves.json').read_text());assert len(curves)==1082
 byid={c['id']:c for c in cases}
 for c in curves:
  case=byid[c['id']];assert case['accepted']
  raw=list(csv.DictReader((RAW/'study/production/cases'/c['id']/'tensile.csv').open()))
  assert c['strain']==[float(r['strain']) for r in raw]
  assert c['stress']==[float(r['force'])/graphs[case['graph']]['length']**2 for r in raw]
  assert math.isclose(c['stress'][-1],case['stress_at_window_end'],abs_tol=1e-12)
 analysis=json.loads((D/'ANALYSIS.json').read_text());checked=0;counts=[]
 for row in analysis['paired_nonlinear_contrasts']:
  pool=[c for c in cases if all(c[k]==row[k] for k in ['n','clustered','aligned','role','k','D'])]
  binding={c['seed']:c for c in pool if c['law']=='binding' and c['accepted']};locked={c['seed']:c for c in pool if c['law']=='locked' and c['accepted']}
  seeds=sorted(binding.keys()&locked.keys());assert seeds==row['seeds'];counts.append(len(seeds))
  for seed in seeds:
   assert binding[seed]['collagen_hash']==locked[seed]['collagen_hash']
   assert binding[seed]['adapter_hash']==locked[seed]['adapter_hash']
  for metric,key in [('stress_at_window_end','stress20_locked_vs_binding_fraction'),('recoil_fraction','recoil_fraction_locked_minus_binding')]:
   vals=[(locked[s][metric]-binding[s][metric])/(binding[s][metric] if metric=='stress_at_window_end' else 1) for s in seeds]
   recorded=row['effects'][key];assert len(vals)==recorded['n']
   assert all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(vals,recorded['values']))
  checked+=1
 assert counts.count(8)==58 and counts.count(7)==6
 coupling=0
 for row in analysis['organization_law_interactions']:
  factor=row['organization_factor'];fixed=row['fixed_other_factor'];pool=[c for c in cases if c['accepted'] and all(c[k]==row[k] for k in ['n','role','k','D']) and c['clustered' if factor=='alignment' else 'aligned']==bool(fixed)]
  maps={(int(c['aligned' if factor=='alignment' else 'clustered']),c['law'],c['seed']):c for c in pool}
  seeds=sorted(s for s in [11,23,37,41,53,67,79,97] if all((a,l,s) in maps for a in [0,1] for l in ['binding','locked']))
  assert seeds==row['seeds']
  for metric in ['stress_at_window_end','recoil_fraction']:
   vals=[(maps[(1,'locked',s)][metric]-maps[(1,'binding',s)][metric])-(maps[(0,'locked',s)][metric]-maps[(0,'binding',s)][metric]) for s in seeds]
   expected=row['locked_minus_binding_difference_in_differences'][metric]['values'];assert all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(vals,expected))
  coupling+=1
 result={'organization_law_DID_strata_recomputed':coupling,'status':'pass','sha256_files':len(m['files']),'case_summaries_exact':1088,'accepted_curves_exact_against_raw_CSV':1082,'initial_graphs_exact':64,'paired_law_strata_recomputed':checked,'complete_8_seed_strata':58,'incomplete_7_seed_strata':6,'failed_cases_retained':6,'private_traceback_fields_excluded':True}
 (ROOT/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--study',type=Path,default=S);ap.add_argument('--raw',type=Path,default=RAW);args=ap.parse_args();S=args.study;RAW=args.raw;main()
