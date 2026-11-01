"""Own bounded supervisor. Operates only containers carrying this study's exact label."""
import subprocess,json,time,datetime,threading,re,traceback
from pathlib import Path
p=Path('/tmp/codex-martini3-20261031-01a18fb8');project=p/'benchmark-project';setup=p/'preflight-v003';attempt_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=p/('production-'+attempt_id);out.mkdir(exist_ok=False)
image='nvcr.io/hpc/gromacs@sha256:04d5ac4416523624bbfcb36c85a63fd8a6ac8acf7c2eeb1af89dd03c60d45daf';label='codex.collagen-study=martini3-20261031-01a18fb8';deadline=datetime.datetime(2026,11,1,3,30,tzinfo=datetime.timezone.utc).timestamp();stop=threading.Event();reports=[]
def save():
 (out/'status.json.tmp').write_text(json.dumps({'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hard_deadline_utc':'2026-11-01T03:30:00Z','requested_ns_per_case':45,'cases':reports,'budget_ceiling_usd':50},indent=2)+'\n');(out/'status.json.tmp').replace(out/'status.json')
def guard():
 while not stop.wait(min(30,max(0,deadline-time.time()))):
  if time.time()>=deadline:
   ids=subprocess.check_output(['sudo','-n','docker','ps','-q','--filter','label='+label],text=True).split()
   (out/'hard-deadline.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containers':ids})+'\n')
   if ids:subprocess.run(['sudo','-n','docker','stop','--time','90']+ids,timeout=120,check=False)
   return
threading.Thread(target=guard,daemon=True).start()
def run(case,stage,args,gpu=False):
 name='codex-martini-'+attempt_id.lower()+'-'+case.lower()+'-'+stage
 cmd=['sudo','-n','docker','create','--name',name,'--label',label,'--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--cpus','16','--memory','32g','--memory-swap','32g','--pids-limit','256','--env','CUDA_CACHE_PATH=/tmp/cuda-cache','--env','GMX_MAXCONSTRWARN=0','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=1g,mode=1777']
 for src,dst,ro in [(project,'input',True),(setup,'setup',True),(p/'preconditioned-starts','starts',True),(out,'output',False)]:cmd+=['--mount',f'type=bind,src={src},dst=/{dst}'+(',readonly' if ro else '')]
 if gpu:cmd+=['--gpus','device=0']
 cmd+=['--workdir','/output/'+case,'--entrypoint','/usr/local/gromacs/avx_512/bin/gmx',image]+args;cid=subprocess.check_output(cmd,text=True).strip()
 (out/case/(stage+'-container-inspect.json')).write_text(subprocess.check_output(['sudo','-n','docker','inspect',cid],text=True))
 try:
  with (out/case/(stage+'.log')).open('w') as f:
   child=subprocess.Popen(['sudo','-n','docker','start','--attach',cid],stdout=f,stderr=subprocess.STDOUT)
   if stage=='mdrun':
    time.sleep(2)
    state=json.loads(subprocess.check_output(['sudo','-n','docker','inspect',cid],text=True))[0]['State']
    reports[-1]['container_id']=cid;reports[-1]['observed_container_state']=state['Status'];reports[-1]['phase']='running' if state['Running'] else 'startup_failed';save()
   return child.wait(timeout=max(1,deadline-time.time()+150))
 finally:subprocess.run(['sudo','-n','docker','rm','-f',cid],stdout=subprocess.DEVNULL,check=False)
def edit(txt,changes):
 lines=[];seen=set()
 for line in txt.splitlines():
  k=line.split('=',1)[0].strip().lower().replace('_','-')
  if k in changes:lines.append(k+' = '+str(changes[k]));seen.add(k)
  else:lines.append(line)
 lines.extend(k+' = '+str(v) for k,v in changes.items() if k not in seen);return '\n'.join(lines)+'\n'
try:
 for case in ['div_CG','triv_CG']:
  if time.time()>deadline-600:break
  (out/case).mkdir();record={'case':case,'phase':'preflight','start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};reports.append(record);save()
  changes={'nsteps':8181818,'table-extension':10,'nstlist':100,'verlet-buffer-tolerance':0.0001,'nstxout-compressed':10000,'compressed-x-grps':'Collagen_Observable'}
  (out/case/'pilot45.mdp').write_text(edit((setup/case/'relative-pairs.mdp').read_text(),changes))
  rc=run(case,'grompp',['grompp','-f',f'/output/{case}/pilot45.mdp','-c',f'/starts/{case}/pre_1000pN.gro','-r',f'/starts/{case}/pre_1000pN.gro','-p',f'/input/{case}/system.top','-n',f'/setup/{case}/complete.ndx','-o',f'/output/{case}/pilot45.tpr','-po',f'/output/{case}/processed.mdp','-pp',f'/output/{case}/processed.top'])
  assert rc==0,(case,'grompp failed');record['phase']='launching';save()
  rc=run(case,'mdrun',['mdrun','-s',f'/output/{case}/pilot45.tpr','-deffnm',f'/output/{case}/pilot45','-ntmpi','1','-ntomp','8','-nb','gpu','-bonded','gpu','-update','cpu','-maxh','3.35','-cpt','.2','-pin','on'],gpu=True)
  txt=(out/case/'mdrun.log').read_text();mainlog=out/case/'pilot45.log'; scientific_log=mainlog.read_text(errors='replace') if mainlog.exists() else ''; warnings=[l for l in (txt+'\n'+scientific_log).splitlines() if any(s in l for s in ['WARNING','Fatal error','skipped','File input/output error'])]; steps=re.findall(r'Step\s+Time\s*\n\s*(\d+)\s+([\d.]+)',scientific_log);last_time=float(steps[-1][1]) if steps else None;phase='failed' if rc or warnings else ('completed' if last_time is not None and last_time>=44999.99 else 'incomplete');record.update({'phase':phase,'returncode':rc,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'warnings':warnings,'last_logged_time_ps':last_time});save()
  if rc or record['warnings']:break
except BaseException:
 (out/'supervisor-error.txt').write_text(traceback.format_exc());
 if reports:reports[-1]['phase']='failed';reports[-1]['supervisor_exception']=True
 save();raise
finally:
 stop.set();(out/'supervisor-finished.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'retrieval_and_vm_stop_required':True})+'\n')
