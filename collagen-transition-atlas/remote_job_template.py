#!/usr/bin/env python3
"""Original remote wrapper; prepared source and pinned wheel metadata are inserted."""
import base64
import hashlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path

SOURCE_B64 = 'SOURCE_ARCHIVE_BASE64'
SOURCE_SHA = 'SOURCE_ARCHIVE_SHA256'
WHEELS = [] # PINNED_WHEELS
REVISION='JOB_REVISION'
START=time.time();workspace=Path('/tmp/collagen-transition-job-'+REVISION);workspace.mkdir(exist_ok=False)
source=workspace/'source';source.mkdir();runs=workspace/'runs';runs.mkdir();os.chown(runs,65534,65534)
output=Path('/output');key=REVISION+'-'+SOURCE_SHA[:12]
status={'startedUnix':START,'steps':[],'authorizedBudgetUSD':15,'providerTimeoutHours':1,'status':'starting'}
clean={'PATH':'/opt/conda/bin:/usr/local/bin:/usr/bin:/bin','LD_LIBRARY_PATH':'/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/opt/conda/lib','LANG':'C.UTF-8','MPLCONFIGDIR':'/tmp/transition-mpl','XDG_CACHE_HOME':'/tmp/transition-cache','TORCH_HOME':'/tmp/transition-torch','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4'}
for name in ['transition-mpl','transition-cache','transition-torch']:
    p=Path('/tmp')/name;p.mkdir(exist_ok=False);os.chown(p,65534,65534)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def persist(local,name):
    # Mountpoint/Object Storage allows sequential writes, not ZIP header seeks.
    dest=output/name
    if dest.exists():raise FileExistsError('Refusing to replace '+name)
    with Path(local).open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst,1048576)
    a=digest(local);b=digest(dest)
    if a!=b:raise RuntimeError('Stored bytes differ: '+name)
    return {'object':name,'bytes':Path(local).stat().st_size,'sha256':a}

def archive_snapshot(label):
    status['elapsedSeconds']=time.time()-START
    (workspace/'job-execution.json').write_text(json.dumps(status,indent=2)+'\n')
    files={}
    for p in sorted(workspace.rglob('*')):
        if p.is_file() and p.name!='OUTPUT_MANIFEST.json' and 'wheels' not in p.relative_to(workspace).parts:
            if p.is_symlink():raise ValueError('Unexpected symlink')
            files[str(p.relative_to(workspace))]={'bytes':p.stat().st_size,'sha256':digest(p)}
    (workspace/'OUTPUT_MANIFEST.json').write_text(json.dumps(files,indent=2)+'\n')
    local=Path('/tmp')/('collagen-transition-'+key+'-'+label+'.zip')
    with zipfile.ZipFile(local,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in [*files,'OUTPUT_MANIFEST.json']:z.write(workspace/name,name)
    with zipfile.ZipFile(local) as z:
        if z.testzip() is not None:raise RuntimeError('Local archive CRC failed')
    receipt=persist(local,local.name)
    receipt.update(status=status['status'],elapsedSeconds=status['elapsedSeconds'],steps=status['steps'])
    r=Path('/tmp')/('result-summary-'+key+'-'+label+'.json');r.write_text(json.dumps(receipt,indent=2)+'\n');persist(r,r.name)
    print('CHECKPOINT '+json.dumps(receipt),flush=True)

def run_step(name,args,seconds):
    log=workspace/(name+'.log');begin=time.time();offset=0
    with log.open('wb') as f:
        p=subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,env=clean,cwd=workspace,start_new_session=True)
        while p.poll() is None:
            if time.time()-begin>seconds:os.killpg(p.pid,signal.SIGKILL);p.wait();break
            with log.open('rb') as reader:
                reader.seek(offset);new=reader.read();offset=reader.tell()
            if new:print(new.decode('utf-8',errors='replace'),end='',flush=True)
            time.sleep(1)
        with log.open('rb') as reader:
            reader.seek(offset);new=reader.read()
        if new:print(new.decode('utf-8',errors='replace'),end='',flush=True)
    rc=p.returncode
    status['steps'].append({'name':name,'returncode':rc,'elapsedSeconds':time.time()-begin})
    print(json.dumps(status['steps'][-1]),flush=True)
    if rc:raise RuntimeError(name+' failed: '+str(rc))

try:
    probe=workspace/'storage-preflight.json';probe.write_text(json.dumps({'sourceSHA256':SOURCE_SHA,'purpose':'sequential-write-readback'})+'\n')
    print('STORAGE_PREFLIGHT '+json.dumps(persist(probe,'storage-preflight-'+key+'.json')),flush=True)
    shutil.copyfile(__file__,workspace/'dispatched-input.py')
    blob=base64.b64decode(SOURCE_B64);assert hashlib.sha256(blob).hexdigest()==SOURCE_SHA
    (workspace/'source.zip').write_bytes(blob)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for n in z.namelist():
            if n.startswith('/') or '..' in Path(n).parts:raise ValueError('Unsafe source archive')
            p=source/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n));p.chmod(0o444)
    (workspace/'hardware.txt').write_bytes(subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader']))
    wh=workspace/'wheels';wh.mkdir()
    for item in WHEELS:
        if not item['url'].startswith('https://files.pythonhosted.org/'):raise ValueError('Unexpected wheel host')
        with urllib.request.urlopen(item['url'],timeout=120) as response:data=response.read(item['bytes']+1)
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Wheel checksum mismatch')
        (wh/item['filename']).write_bytes(data)
    target=Path('/tmp/transition-deps');target.mkdir(exist_ok=False)
    run_step('install-reviewed-wheels',[sys.executable,'-I','-m','pip','install','--no-index','--no-deps','--no-compile','--disable-pip-version-check','--target',str(target),*[str(wh/x['filename']) for x in WHEELS]],180)
    wrapper=str(source/'sandbox_exec.py');runner=str(source/'run_transitions.py')
    run_step('numerical-checks',[sys.executable,'-I',wrapper,runner,'--out',str(runs/'checks'),'--profile','checks','--device','cuda','--minutes','4'],300)
    status['status']='checks_passed';archive_snapshot('checks')
    run_step('commission',[sys.executable,'-I',wrapper,runner,'--out',str(runs/'commission'),'--profile','commission','--device','cuda','--minutes','38'],2400)
    status['status']='commission_complete';archive_snapshot('commission')
    # The first recovered sweep had no fully converged histories. Spend the
    # bounded run on the smaller refined suite before any larger study.
    status['status']='complete'
except Exception as exc:
    status['status']='failed';status['error']=str(exc);status['traceback']=traceback.format_exc();print(status['traceback'],flush=True)
finally:
    archive_snapshot('final')
    if status['status']!='complete':sys.exit(1)
