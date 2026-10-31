"""Original remote launcher: verified inputs, unprivileged child, bounded output."""
import hashlib,json,os,pathlib,resource,signal,subprocess,sys,time,zipfile,shutil
INPUT_SHA='c1fe9a23de45415845e3a1843c431b92ed8f82193f3c666a0936ae74a91e87fa'
HASHES={'coupled.py': 'acd6d984e069b2ac8bc15733a82ace4e30ed894d9dec0291aa06aaa3926bc168', 'plot.py': '49b6ee61b78f61681be181fe4fea0b80a134ba6f611b21cd285f8ffb7356cee6', 'isolation.py': '20bd4971a4e11fd5b118f5dd8a9d383a17d85440de687ed2004ecf71e5af6928', 'networks.json.gz': '8fced75260f077f7d5c44fe7760ee9839aeab501537b352f31e3f54c45959c5c', 'baseline.json.gz': 'c2056d4fa09785a2b54b12dd608b9ab5d69bea8ec62252a5505c16a51ef94d76'}
image='ghcr.io/fenics/dolfinx/dolfinx@sha256:f3e532f96eb91454f13e7aae5289990cd0348124302c003a2002b4cfadb26b1a'
source=pathlib.Path('/output/poro-inputs-v2.zip');assert hashlib.sha256(source.read_bytes()).hexdigest()==INPUT_SHA
root=pathlib.Path('/tmp/fenicsx-poro-work');root.mkdir(mode=0o755,exist_ok=False);work=root/'source';work.mkdir()
with zipfile.ZipFile(source) as z:
 assert set(z.namelist())==set(HASHES)
 for name in z.namelist():
  assert '/' not in name and not name.startswith('.')
  b=z.read(name);assert hashlib.sha256(b).hexdigest()==HASHES[name];(work/name).write_bytes(b);(work/name).chmod(0o444)
for p in [root,work]:os.chown(p,65534,65534)
for name in ['cache','mpl','jit']:
 p=root/name;p.mkdir();os.chown(p,65534,65534)
def child():
 os.setsid();os.setgroups([]);os.setgid(65534);os.setuid(65534);resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_NOFILE,(1024,1024));resource.setrlimit(resource.RLIMIT_FSIZE,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(1700,1750))
# Only numerical-image paths are inherited. No provider/user secrets enter the child.
env={k:os.environ[k] for k in ['PATH','PYTHONPATH','LD_LIBRARY_PATH','PETSC_DIR','PETSC_ARCH','VIRTUAL_ENV'] if k in os.environ}
env.update(LANG='C.UTF-8',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',XDG_CACHE_HOME=str(root/'cache'),MPLCONFIGDIR=str(root/'mpl'))
started=time.time();record={'image':image,'gpuUsed':False,'compute':'4 vCPU CPU-only','uid':65534,'network':'Runtime initialized without user secrets; socket denial installed and tested before scientific work','workloadTimeoutSeconds':1800,'inputSha256':INPUT_SHA,'sourceHashes':HASHES}
result=root/'result'
try:
 with (root/'execution.log').open('wb') as log:
  process=subprocess.Popen([sys.executable,str(work/'coupled.py'),str(result)],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=child)
  try:record['returncode']=process.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
   record['returncode']=124
except Exception as e:record.update(returncode=125,error=str(e))
record['seconds']=time.time()-started;record['success']=record.get('returncode')==0 and (result/'FINISHED.json').is_file();(root/'execution.json').write_text(json.dumps(record,indent=2))
archive=root/'poro-results.zip'
with zipfile.ZipFile(archive,'x') as z:
 for p in sorted(root.rglob('*')):
  if p.is_file() and p!=archive and not any(v in p.parts for v in ['cache','mpl','jit','__pycache__']) and p.name!='partial.json':z.write(p,str(p.relative_to(root)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.png','.gif','.gz'] else zipfile.ZIP_DEFLATED)
assert archive.stat().st_size<512*1024**2
receipt={**record,'archiveBytes':archive.stat().st_size,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
shutil.copyfile(archive,'/output/poro-results-v2.zip');pathlib.Path('/output/poro-summary-v2.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True);sys.exit(0 if record['success'] else 1)
