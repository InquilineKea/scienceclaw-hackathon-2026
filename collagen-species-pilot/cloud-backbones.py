"""Original disposable CPU job. Only public original model files are embedded."""
import base64, ctypes, errno, hashlib, json, os, pathlib, platform, resource, signal, socket, subprocess, sys, time, zipfile, zlib
PAYLOAD = pathlib.Path('/output/cdsm-inputs.json.zlib').read_bytes()
assert hashlib.sha256(PAYLOAD).hexdigest() == '4c52dd0c1a1c042d6c50214b24dffd6d608386a1c1d1de3712b4ae0535bc2af2'
FILES_SHA256 = {'vendor/LICENSE': 'c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4', 'vendor/step1_backbone_builder.py': '9d94365a72f29fc038b0f24249d59dac9c4e9a16d9b6dce6c201de316f18c50e', 'vendor/thparams/THpropensities.dat': 'bb7a88428f3f24b283d1009196e3cdbd909513a390bdd86a4fd4cd9c87a7259f', 'vendor/thparams/THparams_nonsmooth.dat': '0d4dd9e009969ba81b299f9e2b984091655cd989940bda3c6a90e713cf396955', 'vendor/thparams/THparams_IR.dat': 'b1a17c02aec33f8d3cc8d958391604ef9c237dfe8966a15b9d6066ea06c47faa', 'vendor/thparams/THparams_AR.dat': 'df4d03ca2dddedfc187d4a89933135f2790c3480feae0415b494bac7162c674d', 'inputs/pilot.json': 'd1d3c373a90e36fd9135a1ca617d397756d6c7588460f48bca55540bd5f1cd91', 'run-backbones.py': 'b13033c78adbb5c7cbd031241bc256cf985c803c8f66b2b572e57dce4dfc6932'}
root=pathlib.Path('/tmp/cdsm-species-work');root.mkdir(mode=0o755,exist_ok=False)
work=root/'source';work.mkdir();result=root/'result';output=pathlib.Path('/output')
files=json.loads(zlib.decompress(PAYLOAD))
for name,content in files.items():
    if name.startswith('/') or '..' in pathlib.PurePosixPath(name).parts:raise RuntimeError('Unsafe source name')
    data=content.encode();assert hashlib.sha256(data).hexdigest()==FILES_SHA256[name]
    (work/name).parent.mkdir(parents=True,exist_ok=True)
    (work/name).write_bytes(data)
    (work/name).chmod(0o444)
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

start=time.time();record={'runtime_image':'docker.io/library/node@sha256:94c973596a8581a87ba42746ceb0b0e0b5246d098de45b1ce04dcc967cfc5dfb','compute':'Nebius CPU-only, 2 vCPUs','gpuUsed':False,'uid':65534,'network':'seccomp blocks socket/connect/bind/listen/send/receive; socket denial checked before each child','workloadTimeoutSeconds':300,'startedUnix':start,'sourceHashes':FILES_SHA256}
env={'PATH':'/usr/local/bin:/usr/bin:/bin','LANG':'C.UTF-8'}
log=root/'execution.log'
try:
    with log.open('wb') as f:
        process=subprocess.Popen(['/usr/bin/python3',str(work/'run-backbones.py'),str(result)],cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=isolated_child)
        try:record['returncode']=process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            record['returncode']=124
except Exception as e:record.update(returncode=125,error=str(e))
record['elapsedSeconds']=time.time()-start;record['success']=record.get('returncode')==0 and (result/'backbones.json').is_file()
(root/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
archive=root/'cdsm-results.zip'
with zipfile.ZipFile(archive,'x') as z:
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p==archive:continue
        z.write(p,str(p.relative_to(root)),compress_type=zipfile.ZIP_STORED if p.suffix=='.gz' else zipfile.ZIP_DEFLATED)
assert archive.stat().st_size<20*1024**2
summary={**record,'archiveBytes':archive.stat().st_size,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
# Only the parent writes to the mounted private bucket; no cloud credential is injected.
with archive.open('rb') as a,(output/'cdsm-results.zip').open('xb') as b:
    import shutil
    shutil.copyfileobj(a,b)
(output/'cdsm-result-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
sys.exit(0 if record['success'] else 1)
