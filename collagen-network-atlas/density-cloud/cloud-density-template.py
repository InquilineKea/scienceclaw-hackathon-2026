"""Original disposable CPU job. Only public original model files are embedded."""
import base64
import ctypes
import errno
import hashlib
import json
import os
import pathlib
import platform
import resource
import signal
import socket
import subprocess
import sys
import time
import zipfile
import zlib

PAYLOAD = '__PAYLOAD__'
FILES_SHA256 = __HASHES__
root=pathlib.Path('/tmp/fracture-density-work');root.mkdir(mode=0o755,exist_ok=False)
work=root/'source';work.mkdir();result=root/'result';output=pathlib.Path('/output')
files=json.loads(zlib.decompress(base64.b64decode(PAYLOAD)))
for name,content in files.items():
    if '/' in name or name.startswith('.'):raise RuntimeError('Unsafe source name')
    data=content.encode();assert hashlib.sha256(data).hexdigest()==FILES_SHA256[name]
    (work/name).write_bytes(data)
os.chown(root,65534,65534);os.chown(work,65534,65534)

def isolated_child():
    os.setsid();os.setgroups([]);os.setgid(65534);os.setuid(65534)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_NOFILE,(512,512))
    resource.setrlimit(resource.RLIMIT_FSIZE,(2*1024**3,2*1024**3))
    # Linux x86_64 seccomp filter. Deny sockets/connect/bind/listen/send/receive.
    if platform.machine()!='x86_64':raise RuntimeError('Unsupported seccomp architecture')
    class Filter(ctypes.Structure):_fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
    class Program(ctypes.Structure):_fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
    instructions=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),(0x20,0,0,0)]
    for call in [41,42,43,44,45,49,50,288,299,307]:instructions.extend([(0x15,0,1,call),(0x06,0,0,0x50000|errno.EPERM)])
    instructions.append((0x06,0,0,0x7fff0000))
    array=(Filter*len(instructions))(*(Filter(*r) for r in instructions));program=Program(len(instructions),array);libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(38,1,0,0,0)!=0 or libc.prctl(22,2,ctypes.byref(program),0,0)!=0:raise RuntimeError('Network isolation failed')
    try:socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    except OSError as e:
        if e.errno!=errno.EPERM:raise
    else:raise RuntimeError('Socket unexpectedly allowed')

start=time.time();record={'runtime_image':'docker.io/library/node@sha256:94c973596a8581a87ba42746ceb0b0e0b5246d098de45b1ce04dcc967cfc5dfb','compute':'Nebius CPU-only, 4 vCPUs','gpuUsed':False,'uid':65534,'network':'seccomp blocks socket/connect/bind/listen/send/receive; socket denial checked before each child','workloadTimeoutSeconds':1200,'startedUnix':start,'sourceHashes':FILES_SHA256}
env={'PATH':'/usr/local/bin:/usr/bin:/bin','DENSITY_WORKERS':'4','LANG':'C.UTF-8'}
log=root/'execution.log'
try:
    with log.open('wb') as f:
        test=subprocess.run(['/usr/local/bin/node',str(work/'check-density.js')],cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=isolated_child,timeout=60)
        if test.returncode:raise RuntimeError('Model analysis checks failed')
        process=subprocess.Popen(['/usr/local/bin/node',str(work/'benchmark-density.js'),str(result)],cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=isolated_child)
        try:record['returncode']=process.wait(timeout=1200)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            record['returncode']=124
except Exception as e:record.update(returncode=125,error=str(e))
record['elapsedSeconds']=time.time()-start;record['success']=record.get('returncode')==0 and (result/'FINISHED.json').is_file()
(root/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
archive=root/'density-results.zip'
with zipfile.ZipFile(archive,'x') as z:
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p==archive:continue
        z.write(p,str(p.relative_to(root)),compress_type=zipfile.ZIP_STORED if p.suffix=='.gz' else zipfile.ZIP_DEFLATED)
assert archive.stat().st_size<1024**3
summary={**record,'archiveBytes':archive.stat().st_size,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
# Only the parent writes to the mounted private bucket; no cloud credential is injected.
with archive.open('rb') as a,(output/'density-results.zip').open('xb') as b:
    import shutil
    shutil.copyfileobj(a,b)
(output/'density-result-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
sys.exit(0 if record['success'] else 1)
