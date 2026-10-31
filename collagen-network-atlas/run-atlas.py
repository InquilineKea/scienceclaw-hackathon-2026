#!/usr/bin/env python3
"""Original standard-library runner: reserve, snapshot, execute, seal; never reuse."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(folder):
    return {str(p.relative_to(folder)): {'bytes':p.stat().st_size, 'sha256':digest(p)}
            for p in sorted(folder.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}


def reserve(root, run_id=None):
    root = Path(root).resolve()
    run_id = run_id or (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
                        + '-' + uuid.uuid4().hex[:12])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}', run_id):
        raise ValueError('Run ID must be a simple name, never a path')
    parent = root / 'runs'
    if parent.is_symlink():
        raise ValueError('Refusing a symlinked runs directory')
    parent.mkdir(exist_ok=True)
    destination = parent / run_id
    destination.mkdir()  # Exclusive reservation, including concurrent processes.
    (destination/'data').mkdir()
    (destination/'figures').mkdir()
    (destination/'logs').mkdir()
    # Copy source, not previous exports, credentials, caches or nested archives.
    for p in sorted(root.iterdir()):
        if p.is_symlink():
            raise ValueError('Source symlinks are not allowed: '+p.name)
        if (p.is_file() and p.suffix in {'.js','.py','.swift','.html','.css','.md'}
                and p.name not in {'REPORT.md','FREEZE.md'}):
            shutil.copyfile(p,destination/p.name)
    sources=inventory(destination)
    write_new(destination/'RUN_CONTEXT.json', {'runId':run_id,'startedAt':now(),
              'sourceFiles':sources,'policy':'New directory; no resume or overwrite mode.'})
    return destination


def execute_stage(run, command, log_name, env, stdout_json=None):
    log=run/'logs'/log_name
    with log.open('xb') as f:
        result=subprocess.run(command,cwd=run,env=env,stdout=f,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Stage failed: '+command[-1]+'; see '+str(log.relative_to(run)))
    if stdout_json:
        write_new(run/stdout_json,json.loads(log.read_text()))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id',help='Optional unique name; an existing name is an error')
    ap.add_argument('--prepare-only',action='store_true',help='Reserve and snapshot without simulation')
    ap.add_argument('--render',action='store_true',help='Also render PNG/GIF on macOS with system Swift')
    ap.add_argument('--no-upload',action='store_true',help='Explicitly keep this run local')
    args=ap.parse_args()
    root=Path(__file__).resolve().parent
    if (root/'RUN_CONTEXT.json').exists() or (root/'FREEZE.md').exists():
        raise ValueError('Run from the live atlas root, not inside an archived run')
    node=shutil.which('node',path='/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin')
    if not args.prepare_only and not node:
        raise RuntimeError('Use an already trusted Node.js runtime; nothing is installed automatically')
    if args.render and sys.platform != 'darwin':
        raise RuntimeError('--render requires macOS system frameworks')
    run=reserve(root,args.run_id)
    print('Run directory: '+str(run),flush=True)
    if args.prepare_only:
        write_new(run/'PREPARED.json',{'preparedAt':now(),'simulationExecuted':False})
        write_new(run/'MANIFEST.json',inventory(run))
        return 0
    try:
        with tempfile.TemporaryDirectory(prefix='collagen-atlas-runtime-') as temp:
            env={'PATH':'/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin', 'HOME':temp,
                 'TMPDIR':temp,'ATLAS_RUN_DIR':str(run),'LANG':'en_US.UTF-8'}
            stages=[('check.js','checks.log','data/checks.json'),
                    ('benchmark-core.js','benchmark.log',None),
                    ('audit.js','audit.log',None),
                    ('prepare-media.js','media-input.log',None),
                    ('write-report.js','report.log',None)]
            for script,log,json_output in stages:
                execute_stage(run,[node,script],log,env,json_output)
            if args.render:
                execute_stage(run,['/usr/bin/swift','-module-cache-path',temp+'/swift-cache',
                                   'render-media.swift'],'render.log',env)
            result=json.loads((run/'data/results.json').read_text())
            assert result['modelHash']==digest(run/'model.js'),'Results/source hash mismatch'
            media=json.loads((run/'data/media-input.json').read_text())
            assert media['results']==result,'Rendering input/results mismatch'
            write_new(run/'FINISHED.json',{'finishedAt':now(),'status':'complete',
                      'rendered':args.render,'modelHash':result['modelHash'],
                      'runs':len(result['rows'])})
    except BaseException as exc:
        write_new(run/'FAILED.json',{'failedAt':now(),'status':'failed',
                  'error':type(exc).__name__+': '+str(exc),
                  'policy':'Keep this directory and start a fresh run to retry.'})
        write_new(run/'MANIFEST.json',inventory(run))
        raise
    write_new(run/'MANIFEST.json',inventory(run))
    print('Finished and checksummed: '+str(run),flush=True)
    if not args.no_upload:
        published=subprocess.run([sys.executable,'-I',str(root/'upload-run.py'),str(run),'--kind','atlas'])
        if published.returncode:
            print('Computation is complete; GitHub upload is pending and can be retried without rerunning.',file=sys.stderr)
            return 3
    return 0


if __name__=='__main__':
    sys.exit(main())
