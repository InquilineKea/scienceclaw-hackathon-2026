from pathlib import Path
import subprocess,sys,json,time,datetime,hashlib,os
base=Path(__file__).resolve().parent.parent
runid='event-controls-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
run=base/'runs'/runid;run.parent.mkdir(exist_ok=True)
python=Path(sys.executable).resolve()
profile='''(version 1)
(deny default)
(allow process-exec (subpath "/Library/Frameworks/Python.framework"))
(allow process-fork)
(allow sysctl-read)
(allow file-read-metadata)
(allow file-read* (literal "/") (subpath "/usr") (subpath "/System") (subpath "/Library/Frameworks/Python.framework") (subpath "/Library/Apple") (subpath "/private/var/db/dyld") (literal "/dev/urandom") (literal "/dev/random") (literal "/dev/null") (subpath BASE))
(allow file-write* (subpath BASE) (literal "/dev/null"))
'''.replace('BASE',json.dumps(str(base)))
(base/'isolation.sb').write_text(profile)
env={'PATH':'/usr/bin:/bin','HOME':str(base),'TMPDIR':str(base)}
cmd=['/usr/bin/sandbox-exec','-f',str(base/'isolation.sb'),str(python),'-I','-S']
probe="import pathlib,socket,errno\ntry:pathlib.Path('/Users/simfish/.ssh/config').read_text();raise AssertionError('private read allowed')\nexcept PermissionError:pass\ns=socket.socket()\ntry:s.connect(('127.0.0.1',9));raise AssertionError('network allowed')\nexcept OSError as e:assert e.errno in (errno.EPERM,errno.EACCES),repr(e)\nprint('private-read and network denied')"
p=subprocess.run(cmd+['-c',probe],env=env,capture_output=True,text=True,timeout=15);(base/'receipts'/(runid+'-isolation.json')).write_text(json.dumps({'code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2))
if p.returncode:raise SystemExit(p.stderr)
(base/'event-run.json').write_text(json.dumps({'run_id':runid,'path':str(run),'timeout_seconds':1200,'original_source_sha256':hashlib.sha256((base/'source/event_followup.py').read_bytes()).hexdigest()},indent=2))
print(run,flush=True)
with (base/'receipts'/(runid+'-stdout.log')).open('x') as stdout,(base/'receipts'/(runid+'-stderr.log')).open('x') as stderr:
  try:p=subprocess.run(cmd+[str(base/'source/event_followup.py'),str(run)],env=env,cwd=base,stdout=stdout,stderr=stderr,timeout=1200);code=p.returncode
  except subprocess.TimeoutExpired:code=124
print(json.dumps({'exit_code':code,'run_id':runid}),flush=True)
raise SystemExit(code)
