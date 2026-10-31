#!/usr/bin/env python3
"""Package one already finished run; never replace an existing archive."""
from pathlib import Path
import argparse,hashlib,json,zipfile
root=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run_id');args=ap.parse_args()
run=(root/'runs'/args.run_id).resolve()
if run.parent != (root/'runs').resolve() or not run.is_dir():raise SystemExit('Choose one existing run ID')
if not ((run/'FINISHED.json').exists() or (run/'FREEZE.json').exists()):raise SystemExit('Run is not finished')
manifest=json.loads((run/'MANIFEST.json').read_text())
for name,record in manifest.items():
 p=(run/name).resolve()
 if not p.is_relative_to(run) or p.is_symlink():raise SystemExit('Invalid manifest path')
 data=p.read_bytes()
 if hashlib.sha256(data).hexdigest()!=record['sha256'] or len(data)!=record['bytes']:raise SystemExit('Run has changed: '+name)
folder=root/'archives';folder.mkdir(exist_ok=True)
archive=folder/(run.name+'.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name in sorted(manifest):z.write(run/name,run.name+'/'+name)
 z.write(run/'MANIFEST.json',run.name+'/MANIFEST.json')
print(archive)
