from pathlib import Path
import subprocess,sys,json,datetime,uuid,hashlib,shutil,importlib.util
root=Path.cwd();base=root/'outputs/piper-audit-remediation-20261031'
run=base/'python-runs'/('defaults-regression-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);run.mkdir(parents=True)
src=run/'source';shutil.copytree(base/'prepared-python',src)
python=Path(sys.executable).resolve();site=Path(importlib.util.find_spec('numpy').origin).parent.parent
profile='''(version 1)
(deny default)
(allow process-exec (literal PYTHON) (literal "/Library/Frameworks/Python.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"))
(allow process-fork)
(allow sysctl-read)
(allow file-read-metadata)
(allow file-read-data (literal "/") (literal SITE))
(allow mach-lookup (global-name "com.apple.system.logger"))
(allow file-read* (subpath "/usr") (subpath "/System") (subpath "/Library/Frameworks/Python.framework") (subpath "/Library/Apple") (subpath "/opt/homebrew") (subpath "/private/var/db/dyld") (literal "/dev/urandom") (literal "/dev/random") (literal "/dev/null") (literal PYTHON) (subpath NUMPY) (subpath SCIPY) (subpath NUMLIB) (subpath SCILIB) (subpath RUN))
(allow file-write* (subpath RUN) (literal "/dev/null"))
'''
values={'PYTHON':python,'SITE':site,'NUMPY':site/'numpy','SCIPY':site/'scipy','NUMLIB':site/'numpy.libs','SCILIB':site/'scipy.libs','RUN':run}
for key,val in values.items():profile=profile.replace(key,json.dumps(str(val)))
(run/'isolation.sb').write_text(profile)
canary=root/'work'/'atlas-isolation-canary.txt'
probe="import pathlib,socket,errno; denied=False\ntry:pathlib.Path("+repr(str(canary))+").read_text()\nexcept PermissionError:denied=True\nassert denied,'outside-file read unexpectedly allowed'\ns=socket.socket()\ntry:s.connect(('127.0.0.1',9));raise AssertionError('network unexpectedly allowed')\nexcept OSError as e:assert e.errno in (errno.EPERM,errno.EACCES),repr(e)\nprint('read-denied; network-denied')"
cmd=['/usr/bin/sandbox-exec','-f',str(run/'isolation.sb'),str(python),'-I','-S']
env={'PATH':'/usr/bin:/bin','HOME':str(run),'TMPDIR':str(run),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
check=subprocess.run(cmd+['-c',probe],cwd=src,env=env,capture_output=True,text=True,timeout=10)
(run/'isolation-check.json').write_text(json.dumps({'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr},indent=2))
if check.returncode:print(json.dumps({'run':str(run),'isolation_failed':True,'stderr':check.stderr}));raise SystemExit(1)
launch='import sys,runpy;sys.path.insert(0,'+repr(str(site))+');sys.path.insert(0,'+repr(str(src))+');sys.argv=['+repr(str(src/'python-regression.py'))+'];runpy.run_path(sys.argv[0],run_name="__main__")'
config={'run_id':run.name,'timeout_seconds':60,'python_executable':str(python),'python_version':sys.version,'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in src.iterdir() if p.is_file()},'new_packages':0,'cloud_cost':0}
(run/'config.json').write_text(json.dumps(config,indent=2))
start=datetime.datetime.now(datetime.timezone.utc);print(json.dumps({'run':str(run),'started':start.isoformat()}),flush=True)
with (run/'stdout.log').open('x') as stdout,(run/'stderr.log').open('x') as stderr:
 try:res=subprocess.run(cmd+['-c',launch],cwd=src,env=env,stdout=stdout,stderr=stderr,timeout=60);code=res.returncode;status='completed' if code==0 else 'failed'
 except subprocess.TimeoutExpired:code=124;status='timed_out'
receipt={'status':status,'exit_code':code,'elapsed_seconds':(datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()}
(run/'execution.json').write_text(json.dumps(receipt,indent=2))
files={str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in run.rglob('*') if p.is_file()}
(run/'MANIFEST.json').write_text(json.dumps({'files':files},indent=2));print(json.dumps({'run':str(run),**receipt}),flush=True)
raise SystemExit(code)
