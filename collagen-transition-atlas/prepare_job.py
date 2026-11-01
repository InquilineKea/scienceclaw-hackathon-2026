#!/usr/bin/env python3
"""Prepare an exclusive, reproducible remote job input using only the stdlib."""
import argparse
import ast
import base64
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path


def prepare(dest,revision):
    if not re.fullmatch(r'v[1-9][0-9]*',revision):raise ValueError('Revision must be v followed by a positive integer')
    source=Path(__file__).resolve().parent;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    names=['core_network.py','transitions.py','run_transitions.py','plot_results.py','sandbox_exec.py','METHODS.md','SECURITY_REVIEW.md','BASE_PROVENANCE.json','runtime-review/container-review.json','runtime-review/wheel-review.json']
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in names:
            info=zipfile.ZipInfo(name,date_time=(2026,10,31,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(source/name).read_bytes())
    blob=buf.getvalue();sha=hashlib.sha256(blob).hexdigest();wheels=json.loads((source/'runtime-review/wheel-review.json').read_text());wheelmanifest=[{k:r[k] for k in ['filename','url','sha256','bytes']} for r in wheels]
    code=(source/'remote_job_template.py').read_text().replace("'SOURCE_ARCHIVE_BASE64'",repr(base64.b64encode(blob).decode())).replace("'SOURCE_ARCHIVE_SHA256'",repr(sha)).replace('[] # PINNED_WHEELS',repr(wheelmanifest))
    code=code.replace("'JOB_REVISION'",repr(revision));filename='cloud_job_'+revision+'.py'
    ast.parse(code);(dest/filename).write_text(code);(dest/'source.zip').write_bytes(blob)
    manifest={'sourceZipSHA256':sha,'bootstrapSHA256':hashlib.sha256(code.encode()).hexdigest(),'sourceFiles':{name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in names}}
    (dest/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'input':str(dest/filename),'bytes':len(code.encode()),**manifest},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination');p.add_argument('--revision',required=True);a=p.parse_args();prepare(a.destination,a.revision)
