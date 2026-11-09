from pathlib import Path
import subprocess,os,time,json,re
root=Path('outputs/martini-cpu-diagnosis').resolve();inputs=root/'forced-warning-input';out=root/'forced-warning-runs';out.mkdir(exist_ok=False);image='codex/martini-cpu-diagnostic:20261031';main='codex-martini-cpu-conservative2fs';deadline=(root/'runs/version/version-container.json').stat().st_mtime+1800;assert time.time()+40<deadline
running=subprocess.run(['docker','inspect','--format','{{.State.Running}}',main],capture_output=True,text=True).stdout.strip()=='true'
if running:subprocess.run(['docker','update','--cpus','3','--memory','7g','--memory-swap','7g',main],capture_output=True,check=True)
def run(folder,args,name):
 cmd=['docker','run','--rm','--name','codex-martini-cpu-stress-'+name,'--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','1','--memory','1g','--memory-swap','1g','--pids-limit','64','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777','--env','OMP_NUM_THREADS=1','--env','GMX_MAXCONSTRWARN=0','--mount',f'type=bind,src={inputs},dst=/input,readonly','--mount',f'type=bind,src={folder},dst=/output','--workdir','/output',image]+args
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=45);(folder/(name+'.log')).write_text(r.stdout+r.stderr);return r
reports=[]
try:
 for name,nstlist,rlist in [('forced_warning',1,3.0)]:
  folder=out/name;folder.mkdir();s=f'''integrator = md
dt = 0.0055
nsteps = 300
continuation = yes
constraints = none
constraint-algorithm = lincs
lincs-order = 4
lincs-iter = 1
cutoff-scheme = Verlet
nstlist = {nstlist}
verlet-buffer-tolerance = -1
rlist = {rlist}
rcoulomb = 1.1
rvdw = 1.1
coulombtype = Reaction-field
epsilon-r = 15
epsilon-rf = 0
vdwtype = Cut-off
vdw-modifier = Potential-shift-Verlet
tcoupl = no
pcoupl = no
pbc = xyz
comm-mode = Linear
nstcomm = 100
ld-seed = 20261031
nstlog = 1
nstenergy = 1
nstcalcenergy = 1
nstxout = 1
nstvout = 0
nstfout = 0
''';(folder/'test.mdp').write_text(s);p=run(folder,['grompp','-f','test.mdp','-c','/input/start.gro','-p','/input/system.top','-o','test.tpr','-po','processed.mdp'],name+'-grompp');assert p.returncode==0,(name,(p.stdout+p.stderr)[-2000:]);r=run(folder,['mdrun','-s','test.tpr','-deffnm','stress','-ntmpi','1','-ntomp','1','-nb','cpu','-bonded','cpu','-update','cpu','-pin','off','-reprod'],name+'-mdrun');txt=r.stdout+r.stderr;reports.append({'name':name,'nstlist':nstlist,'rlist_nm':rlist,'returncode':r.returncode,'warnings':[l for l in txt.splitlines() if any(q in l for q in ['WARNING','Fatal error'])],'constraint_diagnostic_pdb_files':[p.name for p in folder.glob('step*.pdb')],'tail':txt[-1300:]})
finally:
 if running:subprocess.run(['docker','update','--cpus','4','--memory','8g','--memory-swap','8g',main],capture_output=True,check=False)
(out/'summary.json').write_text(json.dumps({'scope':'Adversarial high-velocity dimer collision fixture, not collagen conditions and not a root-cause proof. Compares neighbor coverage at identical integration settings.','combined_resource_limit':'Primary temporarily3CPU/7GiB plus stress1CPU/1GiB, restored afterward.','cases':reports},indent=2)+'\n');print(json.dumps(reports))
