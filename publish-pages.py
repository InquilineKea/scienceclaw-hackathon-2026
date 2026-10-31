"""Copy a bounded, buildless browser application into the GitHub Pages /docs source."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent
source=root/'collagen-network-atlas';dest=root/'docs'
files=['index.html','style.css','app.js','model.js','load-guide.js','worker.js','METHODS.md','EVIDENCE.md','data/benchmark.js','data/replays.js','data/results.json','data/summary.csv','data/curves.csv','figures/benchmark.svg']
dest.mkdir(exist_ok=True)
allowed=set(files)|{'.nojekyll','DEPLOYMENT.json'}
unexpected=[str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and str(p.relative_to(dest)) not in allowed]
if unexpected:raise SystemExit('Unexpected files in Pages directory; review before replacing: '+str(unexpected))
for name in files:
    target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,target)
(dest/'.nojekyll').write_text('')
data=json.loads((source/'data/results.json').read_text())
model_hash=hashlib.sha256((source/'model.js').read_bytes()).hexdigest()
assert data['modelHash']==model_hash
metadata={'site':'Fracture Atlas','model_sha256':model_hash,'baseline_runs':len(data['rows']),'historical_archive_snapshot':'02b533d81e2de8a05227ab37284f2f553398735c','scope':'Browser UI and exact frozen numerical assets. No server, package installation or scientific rerun. Loading annotations are display-only.','files':{name:{'bytes':(dest/name).stat().st_size,'sha256':hashlib.sha256((dest/name).read_bytes()).hexdigest()} for name in files}}
(dest/'DEPLOYMENT.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps({'pages_source':'docs','files':len(files)+2,'bytes':sum(r['bytes'] for r in metadata['files'].values()),'model_sha256':model_hash}))
