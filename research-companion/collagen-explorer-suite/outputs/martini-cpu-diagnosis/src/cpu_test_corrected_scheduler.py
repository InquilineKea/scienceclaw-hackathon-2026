"""Original bounded, offline non-root GROMACS CPU diagnostic runner."""
from pathlib import Path
import os,subprocess,time,json,re,math,datetime,hashlib
root=Path('outputs/martini-cpu-diagnosis').resolve();inputs=root/'input';out=root/'runs';out.mkdir(exist_ok=False);image='codex/martini-cpu-diagnostic:20261031';deadline=time.monotonic()+1800;reports=[]
def save():
 (out/'status.json').write_text(json.dumps({'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'local_cpu_only':True,'wall_limit_seconds':1800,'reports':reports},indent=2)+'\n')
def run(folder,name,args,binary='gmx',seconds=120):
 cmd=['docker','create','--name','codex-martini-cpu-'+name,'--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','4','--memory','8g','--memory-swap','8g','--pids-limit','128','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=512m,mode=1777','--mount',f'type=bind,src={inputs},dst=/input,readonly','--mount',f'type=bind,src={folder},dst=/output','--workdir','/output','--entrypoint','/opt/cpu-runtime/usr/bin/'+binary,image]+args
 cid=subprocess.check_output(cmd,text=True).strip();start=time.monotonic();(folder/(name+'-container.json')).write_text(subprocess.check_output(['docker','inspect',cid],text=True))
 try:
  with (folder/(name+'.log')).open('w') as f:
   child=subprocess.Popen(['docker','start','--attach',cid],stdout=f,stderr=subprocess.STDOUT)
   try:rc=child.wait(timeout=max(1,min(seconds,deadline-time.monotonic())))
   except subprocess.TimeoutExpired:
    subprocess.run(['docker','stop','--timeout','20',cid],stdout=subprocess.DEVNULL,timeout=30);rc=child.wait(timeout=30)
  return {'returncode':rc,'wall_seconds':time.monotonic()-start,'log':(folder/(name+'.log')).read_text()}
 finally:subprocess.run(['docker','rm','-f',cid],stdout=subprocess.DEVNULL,check=True)
def mdp(changes):
 lines=[];seen=set()
 for line in (inputs/'source-relative.mdp').read_text().splitlines():
  k=line.split('=',1)[0].strip().lower().replace('_','-')
  if k in changes:lines.append(k+' = '+str(changes[k]));seen.add(k)
  else:lines.append(line)
 lines.extend(k+' = '+str(v) for k,v in changes.items() if k not in seen);return '\n'.join(lines)+'\n'
def prepare(name,dt,extra=None):
 folder=out/name;folder.mkdir();changes={'nsteps':math.ceil(800/dt),'dt':dt,'table-extension':10,'nstlist':100,'verlet-buffer-tolerance':0.0001,'nstxout-compressed':1000,'compressed-x-grps':'Collagen_Observable','nstlog':100,'nstenergy':100,'nstcalcenergy':100,'ld-seed':20261031};changes.update(extra or {});(folder/'test.mdp').write_text(mdp(changes));r=run(folder,name+'-grompp',['grompp','-f','test.mdp','-c','/input/start.gro','-r','/input/start.gro','-p','/input/system.top','-n','/input/complete.ndx','-o','test.tpr','-po','processed.mdp','-pp','processed.top']);record={'name':name,'phase':'grompp','dt_ps':dt,'changes':changes,'returncode':r['returncode'],'tail':r['log'][-1800:]};reports.append(record);save();assert r['returncode']==0,(name,r['log'][-2500:]);return folder,record
v=out/'version';v.mkdir();r=run(v,'version',['--version']);assert r['returncode']==0;r=run(v,'version-double',['--version'],binary='gmx_d');assert r['returncode']==0
folder,record=prepare('baseline',.0055)
r=run(folder,'timing',['mdrun','-s','test.tpr','-deffnm','timing','-nsteps','1000','-ntmpi','1','-ntomp','4','-nb','cpu','-bonded','cpu','-update','cpu','-pin','off','-cpt','.2','-reprod'],seconds=180)
perf=re.findall(r'Performance:\s+([\d.]+)',r['log']);warnings=[l for l in r['log'].splitlines() if 'WARNING' in l or 'Fatal error' in l];record.update({'phase':'timing','returncode':r['returncode'],'timing_ns_per_day':float(perf[-1]) if perf else None,'timing_wall_seconds':r['wall_seconds'],'warnings':warnings});save();print(json.dumps(record),flush=True)
if r['returncode'] or warnings:raise SystemExit('CPU timing failed; preserved outputs.')
# A separate bounded smoke test does not count as the800ps regression trajectory.
nsday=record['timing_ns_per_day'];estimate=.8/nsday*86400 if nsday else 1e9;remaining=deadline-time.monotonic();record['estimated_800ps_seconds']=estimate;save()
if estimate*(1+.0055/.002)>remaining*.9:
 record['phase']='insufficient_budget_for_paired_800ps_test';record['reason']='Do not silently substitute a short smoke test for a pass beyond the original586.6ps failure window.';save();print(json.dumps({'timing_ns_per_day':nsday,'estimated_800ps_seconds':estimate,'remaining_seconds':remaining,'decision':'paired test cannot fit authorized local wall budget'}),flush=True);raise SystemExit(0)
for name,dt in [('baseline',.0055),('dt2fs',.002)]:
 if name=='baseline':folder=out/name;record=reports[-1]
 else:folder,record=prepare(name,dt)
 record['phase']='dynamics';save();r=run(folder,name+'-mdrun',['mdrun','-s','test.tpr','-deffnm','regression','-ntmpi','1','-ntomp','4','-nb','cpu','-bonded','cpu','-update','cpu','-pin','off','-cpt','.2','-reprod','-maxh',str(max(.01,(deadline-time.monotonic()-30)/3600))],seconds=max(1,deadline-time.monotonic()-20));txt=r['log'];warnings=[l for l in txt.splitlines() if any(q in l for q in ['WARNING','Fatal error','skipped','File input/output error'])];record.update({'phase':'finished','returncode':r['returncode'],'wall_seconds':r['wall_seconds'],'warnings':warnings,'tail':txt[-2000:]});save();print(json.dumps(record),flush=True)
(out/'finished.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n')
