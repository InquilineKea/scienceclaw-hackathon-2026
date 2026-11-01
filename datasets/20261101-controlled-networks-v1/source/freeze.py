from pathlib import Path
import json,hashlib,shutil,datetime,re
b=Path(__file__).resolve().parent.parent;repo=Path(__import__('sys').argv[1]);dest=repo/'datasets/20261101-controlled-networks-v1';assert not dest.exists()
def manifest(root):return {str(p.relative_to(root)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(root.rglob('*')) if p.is_file() and p!=root/'MANIFEST.json'}
for r in (b/'runs').iterdir():
 if r.is_dir() and not (r/'MANIFEST.json').exists():
  if (r/'execution.json').exists():(r/'FINISHED.json').write_text(json.dumps({'status':'completed','scope':'event-resolved primary' if r.name.startswith('event') else 'increment-sensitive diagnostic; not primary results'},indent=2))
  (r/'MANIFEST.json').write_text(json.dumps({'files':manifest(r)},indent=2))
dest.mkdir(parents=True)
for name in ['source','runs','visualizations']:shutil.copytree(b/name,dest/name)
shutil.copytree(b/'receipts',dest/'logs')
for name in ['RESULTS.md','SECURITY_AND_METHOD_REVIEW.md','analysis.json','event-analysis.json','isolation.sb','active-run.json','event-run.json']:shutil.copyfile(b/name,dest/name)
(dest/'README.md').write_text('# Frozen controlled-network study — 1 November 2026\n\nRead [RESULTS.md](RESULTS.md) for methods, all numerical outcomes and limitations. Explore [visualizations/index.html](visualizations/index.html) or the [1,600-row FEniCSx table](visualizations/fenicsx-table.html). Raw input geometries, trajectories, solve logs, failures and both earlier diagnostic/final event-resolved results are retained under separate run IDs in runs/. This is an original uncalibrated central-force surrogate, not a new FEniCSx solve or validated collagen tissue model.\n\nMANIFEST.json seals every payload file except itself. Publication receipts live outside this frozen folder. No payload file exceeds 95 MiB; Git stores every raw file directly.\n')
(dest/'FINISHED.json').write_text(json.dumps({'status':'completed','kind':'archive','study':'controlled-network-comparison','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primary_run':json.loads((b/'event-run.json').read_text())['run_id'],'raw_scientific_cases':558,'failed_preflight_attempts':1,'event_solve_failures':0,'finite_step_diagnostic_preserved':True,'cloud_cost_usd':0,'provenance':'Original standard-library implementation; source-table FEniCSx reanalysis. See exact model limits in RESULTS.md.'},indent=2))
files=manifest(dest)
for path in files:
 raw=(dest/path).read_bytes()
 if re.search(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',raw):raise ValueError('Credential-like payload, stop publication: '+path)
assert max(v['bytes'] for v in files.values())<95*1024*1024
(dest/'MANIFEST.json').write_text(json.dumps({'algorithm':'SHA-256','files':files},indent=2))
for p,v in files.items():assert hashlib.sha256((dest/p).read_bytes()).hexdigest()==v['sha256']
receipt={'dataset':str(dest),'files':len(files),'bytes':sum(v['bytes'] for v in files.values()),'largest_file':max(v['bytes'] for v in files.values()),'manifest_sha256':hashlib.sha256((dest/'MANIFEST.json').read_bytes()).hexdigest()};(b/'receipts/freeze.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
