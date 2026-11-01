#!/usr/bin/env python3
"""Original stdlib-only data adapter. Does not execute simulation source."""
import argparse,csv,hashlib,json,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parents[3]
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'site' if (ROOT/'site').exists() else BASE/'docs/research-companion/collagen-protein-3d';DATA=OUT/'data'
STUDY=BASE/'outputs/collagen-protein-3d';RAW=BASE/'work/3d-results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,allow_nan=False,separators=(',',':'))+'\n')
def main():
 DATA.mkdir(parents=True,exist_ok=True)
 cases=json.loads((STUDY/'FULL-CASE-SUMMARIES.json').read_text());assert len(cases)==1088
 clean=[{k:v for k,v in c.items() if k!='traceback'} for c in cases]
 write(DATA/'cases.json',clean)
 graphs={p.stem:json.loads(p.read_text()) for p in (RAW/'study/graphs').glob('*.json')};assert len(graphs)==64
 for n in [512,1024]:
  for seed in [11,23,37,41,53,67,79,97]:
   write(DATA/f'geometry-{n}-{seed}.json',[g for g in graphs.values() if g['n']==n and g['seed']==seed])
 curves=[]
 for c in cases:
  if not c['accepted']:continue
  path=RAW/'study/production/cases'/c['id']/'tensile.csv'
  rows=list(csv.DictReader(path.open()));area=graphs[c['graph']]['length']**2
  curves.append({'id':c['id'],'strain':[float(r['strain']) for r in rows],'stress':[float(r['force'])/area for r in rows]})
  assert abs(curves[-1]['stress'][-1]-c['stress_at_window_end'])<1e-12
 write(DATA/'curves.json',curves)
 attempts=[]
 for folder in sorted((RAW/'attempts').iterdir()):
  status=json.loads((folder/'attempt-status.json').read_text())
  records=[]
  for p in sorted(folder.rglob('summary.json')):
   x=json.loads(p.read_text());records.append({k:x[k] for k in ['id','accepted','error','version','seconds'] if k in x})
  attempts.append({'attempt':folder.name,'status':status,'completed_case_records':records})
 write(DATA/'commissioning-attempts.json',attempts)
 for name in ['RESULTS.md','BIOLOGY.md','CONTRASTS.csv','CASE-SUMMARIES.csv','ANALYSIS.json','GEOMETRY-AUDIT.json']:
  shutil.copyfile(STUDY/name,DATA/name)
 shutil.copyfile(BASE/'outputs/collagen-fiber-protein/RESULTS.md',DATA/'CONTINUOUS-FIBER-NO-GO.md')
 # Copy only scientific source files (no launchers, account or runtime configuration).
 for name in ['study3d.py','validate3d.py']:
  shutil.copyfile(STUDY/'source'/name,DATA/(name+'.txt'))
 manifest={'schema_version':'1.0','experiment_id':'collagen-protein-3d-20261031','dimensions':3,'status':'completed_with_rejections','planned':1088,'accepted':1082,'rejected':6,'missing':0,'seeds':[11,23,37,41,53,67,79,97],'unit':'synthetic graph seed, not biological replicate','design':'2 sizes × 2 spatial organizations × 2 orientations × 8 seeds × 17 adapter conditions','organization_comparison':'Adapter-free controls; graph seeds paired by generator intervention. Organization changes regenerate edges, not an identical graph.','interaction_comparison':'Binding versus locked on identical scaffold and adapter geometry, at matched k, D, arm count and total adapter mass.','architecture_comparison':'Two-arm decorin-like versus four-arm fibronectin-like assemblies; hypothetical valency/site geometry, not real protein stoichiometry.','geometry':'All64 actual initial graph JSONs; no deformed geometry or molecular structures displayed.','raw_archive':{'bytes':861436037,'sha256':'a378501ae3d1321ac27aa675309bfd5006ca4683dde6b8be214c756d4584b8e5','files':9250,'availability':'Retained locally; not distributed by compact companion.'},'source_summary_sha256':sha(STUDY/'FULL-CASE-SUMMARIES.json'),'source_analysis_sha256':sha(STUDY/'ANALYSIS.json'),'limits':['Central-force struts, no continuous fibril bending.','No calibrated protein chemistry, assembly or kinetics.','Locked decorin is a counterfactual.','Fixed reduced-time recovery is not permanent deformation.','No observed major load-loss endpoint; no ultimate-strength ranking.','Later continuous-fiber refinement failed;160-case production not launched.'],'compute':'precomputed_only','files':[]}
 for p in sorted(DATA.iterdir()):
  if p.name!='manifest.json':manifest['files'].append({'path':'data/'+p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
 write(DATA/'manifest.json',manifest)
 print(json.dumps({'cases':len(clean),'curves':len(curves),'graphs':64,'artifacts':len(manifest['files']),'bytes':sum(p.stat().st_size for p in DATA.iterdir())}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--study',type=Path,default=STUDY);ap.add_argument('--raw',type=Path,default=RAW);args=ap.parse_args();STUDY=args.study;RAW=args.raw;main()
