#!/usr/bin/env python3
"""Verify the published archive bytes using only Python's standard library."""
from pathlib import Path
import hashlib,json

root=Path(__file__).resolve().parent
manifest=json.loads((root/'ARCHIVE_MANIFEST.json').read_text())
failures=[]
for name,record in manifest['files'].items():
    path=root/name
    if not path.is_file():failures.append(name+': missing');continue
    payload=path.read_bytes()
    if len(payload)!=record['bytes'] or hashlib.sha256(payload).hexdigest()!=record['sha256']:
        failures.append(name+': hash/size mismatch')
if failures:
    raise SystemExit('\n'.join(failures))
print(json.dumps({'verified_files':len(manifest['files']),
                  'bytes':sum(x['bytes'] for x in manifest['files'].values()),'status':'passed'}))
