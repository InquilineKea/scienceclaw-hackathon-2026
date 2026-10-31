from pathlib import Path
import subprocess,json,datetime,uuid,hashlib,shutil,os
root=Path.cwd(); base=root/'outputs/piper-audit-remediation-20261031'
run=base/'runs'/('atlas-sixcase-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);run.mkdir(parents=True)
src=run/'source';src.mkdir()
for name in ('model.js','baseline.json','reproduce.js'):shutil.copyfile(base/'prepared-pilot'/name,src/name)
(src/'package.json').write_text('{"type":"commonjs"}\n')
node=Path(shutil.which('node')).resolve()
# Deny by default; scientific source has no access to the user's home, credentials, or network.
quote=lambda p:json.dumps(str(p))
profile='''(version 1)
(deny default)
(allow process-exec (literal NODE))
(allow process-fork)
(allow sysctl-read)
(allow file-read-metadata)
(allow file-read-data (literal "/"))
(allow mach-lookup (global-name "com.apple.system.logger"))
(allow file-read* (subpath "/opt/homebrew") (subpath "/usr") (subpath "/System") (subpath "/Library/Apple") (subpath "/private/var/db/dyld") (literal "/dev/urandom") (literal "/dev/random") (literal "/dev/null") (literal NODE) (subpath SOURCE) (subpath RUN))
(allow file-write* (subpath RUN) (literal "/dev/null"))
'''.replace('NODE',quote(node)).replace('SOURCE',quote(src)).replace('RUN',quote(run))
(run/'isolation.sb').write_text(profile)
canary=root/'work'/'atlas-isolation-canary.txt';canary.write_text('Non-sensitive file used only to verify read denial.\n')
probe="const fs=require('fs'),net=require('net');let denied=false;try{fs.readFileSync(process.argv[1])}catch(e){denied=['EPERM','EACCES'].includes(e.code)}if(!denied)throw Error('Read isolation failed');const s=net.connect(9,'127.0.0.1');s.on('error',e=>{if(!['EPERM','EACCES'].includes(e.code))throw Error('Network isolation not established: '+e.code);console.log('read-denied; network-denied');});setTimeout(()=>{s.destroy();process.exit(2)},2000).unref();"
env={'PATH':'/usr/bin:/bin','HOME':str(run),'TMPDIR':str(run),'NODE_OPTIONS':''}
cmd=['/usr/bin/sandbox-exec','-f',str(run/'isolation.sb'),str(node)]
check=subprocess.run(cmd+['-e',probe,str(canary)],cwd=src,env=env,capture_output=True,text=True,timeout=10)
(run/'isolation-check.json').write_text(json.dumps({'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr},indent=2))
if check.returncode:print(json.dumps({'run':str(run),'blocked':'isolation check failed','stderr':check.stderr}));raise SystemExit(1)
config={'run_id':run.name,'model_sha256':hashlib.sha256((src/'model.js').read_bytes()).hexdigest(),'timeout_seconds':120,'seed':17,'cases':6,'node_executable':str(node),'network':'denied','credential_access':'denied','installations':0,'cloud_spend':0}
(run/'config.json').write_text(json.dumps(config,indent=2))
started=datetime.datetime.now(datetime.timezone.utc);print(json.dumps({'run':str(run),'started':started.isoformat()}),flush=True)
with (run/'stdout.log').open('x') as stdout,(run/'stderr.log').open('x') as stderr:
 try:result=subprocess.run(cmd+[str(src/'reproduce.js'),str(run/'results')],cwd=src,env=env,stdout=stdout,stderr=stderr,timeout=120);code=result.returncode;status='completed' if code==0 else 'failed'
 except subprocess.TimeoutExpired:code=124;status='timed_out'
receipt={'status':status,'exit_code':code,'elapsed_seconds':(datetime.datetime.now(datetime.timezone.utc)-started).total_seconds()}
(run/'execution.json').write_text(json.dumps(receipt,indent=2))
manifest={str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in run.rglob('*') if p.is_file()}
(run/'MANIFEST.json').write_text(json.dumps({'files':manifest},indent=2))
print(json.dumps({'run':str(run),**receipt}),flush=True)
raise SystemExit(code)
