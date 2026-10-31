#!/usr/bin/env python3
"""Bounded, append-only mechanistic follow-up; never overwrites a run directory."""
import os,sys,math,time,json,argparse,hashlib,shutil,platform,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import torch
from transitions import MechanismBatch,Lattice,specifications,network_stats,field_roots,feedback_path,helix_coil

START=time.monotonic();DEADLINE=3600.;OUT=None;CFG={};RESULTS={'suites':{},'limitations':[]}

def checkpoint():
    if time.monotonic()-START>DEADLINE:raise TimeoutError('Declared scientific runtime limit reached')

def save(name,data):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise FileExistsError('Refusing to overwrite '+str(p))
    p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

def emit(event,**data):
    value={'elapsedSeconds':round(time.monotonic()-START,3),'event':event,**data}
    print(json.dumps(value),flush=True)
    with (OUT/'progress.jsonl').open('a') as f:f.write(json.dumps(value)+'\n')

def collect(batch,records,q,stage,frame=False,extras=None):
    checkpoint();P=batch.stress(batch.Flast).detach().cpu().numpy();E=batch.energy(batch.x,batch.Flast,True).detach().cpu().numpy()
    resid=batch.last_diagnostics['residual'].cpu().numpy();valid=batch.last_diagnostics['converged'].cpu().numpy()
    alive=batch.alive.cpu().numpy();rest=batch.rest.cpu().numpy()
    coords=batch.x.cpu().numpy() if frame else None
    contact=None
    if batch.radii is not None:
        ce,cn=batch.contact_terms(batch.x,batch.Flast);contact=(ce.detach().cpu().numpy(),cn.cpu().numpy())
    for i,r in enumerate(records):
        d={'control':float(q),'stage':stage,'Pxx':float(P[i,0,0]),'Pxy':float(P[i,0,1]),'Pyy':float(P[i,1,1]),
           'energy':float(E[i]),'residual':float(resid[i]),'converged':bool(valid[i]),'aliveBonds':int(alive[i].sum()),
           'meanRestLength':float(rest[i].mean())}
        d['energyChange']=float(batch.last_diagnostics['energyChange'][i])
        d['preRefinementResidual']=float(batch.last_diagnostics.get('preRefinementResidual',batch.last_diagnostics['residual'])[i])
        d['newtonAcceptedSteps']=int(batch.last_diagnostics['newtonAcceptedSteps'][i]) if 'newtonAcceptedSteps' in batch.last_diagnostics else 0
        if extras:
            for key,values in extras.items():d[key]=float(values[i])
        if contact:d.update(contactEnergy=float(contact[0][i]),contacts=int(contact[1][i]))
        if frame:d['frame']={'coordinates':coords[i].tolist(),'alive':alive[i].tolist(),'restLength':rest[i].tolist()}
        r['curve'].append(d)
        # Preserve every sampled protocol state even if a later state fails
        # before the suite-level JSON document is finished.
        with (OUT/'raw-samples.jsonl').open('a') as raw:
            raw.write(json.dumps({'latticeWidth':batch.lat.W,'parameters':r['parameters'],'sample':d},allow_nan=False)+'\n')

def initial_records(lat,specs):
    return [{'parameters':s.meta.copy(),'graph':network_stats(lat,s),'initialAlive':s.alive.tolist(),'curve':[]} for s in specs]

def lattice_record(lat):return {'W':lat.W,'nodes':lat.X.tolist(),'edges':np.stack([lat.bi,lat.bj],axis=1).tolist(),'imageShifts':lat.shift.tolist(),'area':lat.area}

def equilibrium(batch,F):return batch.advance(F,tol=CFG['tol'],rounds=CFG['rounds'],iters=CFG['iters'])

def tests(device):
    checks=[]
    def check(name,condition,**detail):
        checks.append({'name':name,'passed':bool(condition),**detail})
        if not condition:save('CHECKS_FAILED.json',checks);raise AssertionError(name)
    lat=Lattice(4);spec=specifications(lat,[{'uncut_control':True,'kappa':0}]);b=MechanismBatch(lat,spec,device)
    F=b.F_shear(1e-5);b.move_affine(b.F0,F);b.relax_checked(F,tol=1e-10,rounds=3,iters=100)
    G=float(b.stress(F)[0,0,1])/1e-5
    check('Analytic triangular lattice shear modulus',abs(G-math.sqrt(3)/4)<2e-5,measured=G,analytic=math.sqrt(3)/4)
    x=b.x.clone();x[0,2,0]+=.017;x.requires_grad_(True);E=b.energy(x,F);grad=torch.autograd.grad(E,x)[0]
    eps=1e-6;xp=x.detach().clone();xm=x.detach().clone();xp[0,2,0]+=eps;xm[0,2,0]-=eps
    finite=float((b.energy(xp,F)-b.energy(xm,F))/(2*eps));auto=float(grad[0,2,0])
    check('Force finite difference',abs(finite-auto)<1e-8,finiteDifference=finite,autograd=auto)
    angle=.37;R=torch.tensor([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]],dtype=b.dtype,device=device)
    rotated=b.energy(x@R.T,R[None]@F);translated=b.energy(x+3.7,F)
    check('Rigid rotation and translation invariance',abs(float(rotated-E))<1e-10 and abs(float(translated-E))<1e-10)
    F=b.F_stretch(.1,0);b.move_affine(b.Flast,F);b.relax_checked(F);before=b.rest.clone();b.slip(F,[0],.1)
    check('Zero sliding mobility leaves rest lengths unchanged',bool(torch.equal(before,b.rest)))
    dissipated=float(b.slip(F,[2],.1)[0]);check('Plastic update dissipates energy',dissipated>=-1e-10,dissipated=dissipated)
    b.add_inclusions([0]);ce,cn=b.contact_terms(b.x,F)
    check('Zero inclusion control has no contact energy',float(ce.sum())==0 and int(cn.sum())==0)
    b.add_inclusions([1.1]);x=b.x.clone();x[0,2,0]+=.017;x.requires_grad_(True)
    contact=b.contact_terms(x,F)[0].sum();cg=torch.autograd.grad(contact,x)[0]
    xp=x.detach().clone();xm=x.detach().clone();xp[0,2,0]+=eps;xm[0,2,0]-=eps
    cf=float((b.contact_terms(xp,F)[0].sum()-b.contact_terms(xm,F)[0].sum())/(2*eps))
    check('Nonzero contact force finite difference',abs(cf-float(cg[0,2,0]))<1e-6 and abs(cf)>1e-5,finiteDifference=cf,autograd=float(cg[0,2,0]))
    roots=field_roots(1,0);check('Zero-feedback control has one stable equilibrium',len(roots)==1 and roots[0]['stable'])
    roots=field_roots(1,3);check('Feedback stability evaluated at every equilibrium',all('largestJacobianRealPart' in x for x in roots))
    # Exercise the export boundary before an expensive mechanical sweep.
    exported=json.loads(json.dumps({'roots':roots,'path':feedback_path(1,np.array([0.,.1]),(.3,0,.05))},allow_nan=False))
    check('Feedback records serialize as strict JSON',all(type(r['stable']) is bool for r in exported['roots']) and all(type(r['converged']) is bool for r in exported['path']))
    q=helix_coil([.01,100],0,0,0,device)
    # At high T the unfolded-state entropy keeps a finite folded probability.
    check('Transfer-matrix folded fractions remain bounded',0<=q[1]<q[0]<=1+1e-12 and q[0]>.999)
    cpu=MechanismBatch(lat,spec,'cpu');Fc=cpu.F_shear(.03);xc=cpu.X[None]@Fc.transpose(1,2)
    gpu=MechanismBatch(lat,spec,device);Fg=gpu.F_shear(.03);xg=gpu.X[None]@Fg.transpose(1,2)
    ec=float(cpu.energy(xc,Fc));eg=float(gpu.energy(xg,Fg));check('CPU/GPU energy agreement',abs(ec-eg)<1e-10,CPU=ec,selectedDevice=eg)
    save('CHECKS.json',checks);emit('checks_passed',checks=len(checks))


def rigidity(device,profile):
    groups=[];sizes=[6] if profile=='commission' else [8,12]
    seeds=[17] if profile=='commission' else [17,29,43]
    zs=[3.0,3.6,4.2] if profile=='commission' else [2.8,3.2,3.6,4.0,4.4]
    kappas=[1e-4] if profile=='commission' else [1e-5,1e-4,1e-3]
    gammas=np.linspace(0,.8,9 if profile=='commission' else 33)
    for W in sizes:
        for kappa in kappas:
            checkpoint();lat=Lattice(W);cases=[{'seed':seed,'z':z,'kappa':kappa} for z in zs for seed in seeds]
            specs=specifications(lat,cases);batch=MechanismBatch(lat,specs,device);records=initial_records(lat,specs)
            previous=batch.x.clone();Fp=batch.F0.clone();previous_g=0
            for step,gamma in enumerate(gammas):
                F=batch.F_shear(float(gamma));affine=previous@(F@torch.linalg.inv(Fp)).transpose(1,2)
                equilibrium(batch,F)
                du=batch.x-affine;du=du-du.mean(1,keepdim=True)
                delta=float(gamma-previous_g);na=(du.square().sum(2).mean(1)/max(delta*delta,1e-30)).cpu().numpy() if step else np.zeros(batch.B)
                collect(batch,records,gamma,'shear',frame=True,extras={'incrementalNonaffinity':na})
                previous=batch.x.clone();Fp=F;previous_g=gamma
            for r in records:
                stress=np.array([p['Pxy'] for p in r['curve']]);K=np.gradient(stress,gammas)
                for j,(p,k) in enumerate(zip(r['curve'],K)):
                    p['tangentShearModulus']=float(k)
                    p['tangentValid']=all(q['converged'] for q in r['curve'][max(0,j-1):min(len(K),j+2)])
                    p['nonaffinityValid']=p['converged'] and (j==0 or r['curve'][j-1]['converged'])
                good=[p for p in r['curve'][1:] if p['nonaffinityValid']]
                peak=max(good,key=lambda p:p['incrementalNonaffinity']) if good else None
                r['peakNonaffinityStrain']=peak['control'] if peak else None
                r['peakIsInterior']=bool(peak and peak['control']<gammas[-1])
            groups.append({'lattice':lattice_record(lat),'cases':records})
            emit('rigidity_group',W=W,kappa=kappa,cases=len(records))
    save('data/rigidity.json',groups);RESULTS['suites']['rigidity']={'file':'data/rigidity.json','cases':sum(len(x['cases']) for x in groups)}


def sliding_and_memory(device,profile):
    lat=Lattice(6 if profile=='commission' else 10);seeds=[17] if profile=='commission' else [17,29,43]
    levels=[0,.5,1] if profile=='commission' else [0,.25,.5,.75,1]
    cases=[{'seed':seed,'z':3.4,'kappa':1e-4,'locking':lock,'mobility':2*math.exp(-6*lock)} for lock in levels for seed in seeds]
    specs=specifications(lat,cases);batch=MechanismBatch(lat,specs,device);records=initial_records(lat,specs)
    mobility=[c['mobility'] for c in cases];diss=np.zeros(len(cases));N=8 if profile=='commission' else 16
    for gamma in np.linspace(0,.5,N+1):
        F=batch.F_shear(float(gamma));equilibrium(batch,F);collect(batch,records,gamma,'fast_load',frame=True)
    initial=np.array([x['curve'][-1]['Pxy'] for x in records])
    for hold in range(1,N+1):
        diss+=batch.slip(F,mobility,2/N).cpu().numpy();equilibrium(batch,F)
        collect(batch,records,hold*2/N,'hold',frame=True,extras={'plasticDissipation':diss})
    final=np.array([x['curve'][-1]['Pxy'] for x in records])
    for r,a,z in zip(records,initial,final):r['stressRetainedAfterHold']=float(z/a) if abs(a)>1e-12 else None
    for gamma in np.linspace(.5,0,N+1)[1:]:
        equilibrium(batch,batch.F_shear(float(gamma)));collect(batch,records,gamma,'unload',frame=True)
    # Find the relaxed zero-shear-stress strain, rather than calling a clamped
    # zero-strain state a stress-free residual deformation.
    lo=torch.zeros(batch.B,device=device,dtype=batch.dtype);hi=torch.full_like(lo,.5)
    bracket_low=batch.stress(batch.Flast)[:,0,1].detach()
    equilibrium(batch,batch.F_shear(.5));bracket_high=batch.stress(batch.Flast)[:,0,1].detach()
    bracket=(bracket_low<=0)&(bracket_high>=0)
    for k in range(16):
        mid=(lo+hi)/2;F=batch.F0.clone();F[:,0,1]=mid;equilibrium(batch,F);stress=batch.stress(F)[:,0,1].detach()
        hi=torch.where(stress>0,mid,hi);lo=torch.where(stress<=0,mid,lo)
    for i,r in enumerate(records):
        r['residualStrain']=float((lo[i]+hi[i])/2) if bool(bracket[i]) else None
        r['residualRootBracketed']=bool(bracket[i]);r['residualRootConverged']=bool(batch.last_diagnostics['converged'][i])
        r['plasticDissipation']=float(diss[i])
    save('data/sliding-memory.json',{'lattice':lattice_record(lat),'cases':records})
    RESULTS['suites']['sliding_memory']={'file':'data/sliding-memory.json','cases':len(cases)};emit('sliding_memory_done',cases=len(cases))

    # Separate amplitude and hold-time matrix tests memory beyond the single
    # locking comparison. All loading histories remain explicitly recorded.
    amplitudes=[.15,.45] if profile=='commission' else [.1,.25,.5]
    holds=[.2,2.] if profile=='commission' else [.1,1.,4.]
    mcases=[{'seed':17,'z':3.4,'kappa':1e-4,'amplitude':a,'holdTime':h,'locking':l,'mobility':2*math.exp(-6*l)} for a in amplitudes for h in holds for l in [0,1]]
    mspecs=specifications(lat,mcases);m=MechanismBatch(lat,mspecs,device);mrec=initial_records(lat,mspecs)
    amps=torch.tensor([x['amplitude'] for x in mcases],dtype=m.dtype,device=device)
    for t in np.linspace(0,1,9):
        F=m.F0.clone();F[:,0,1]=amps*t;equilibrium(m,F);collect(m,mrec,t,'load',frame=t==1)
    for step in range(16):
        # mobility * dt encodes each distinct hold duration exactly.
        rates=[x['mobility']*x['holdTime'] for x in mcases]
        m.slip(F,rates,1/16);equilibrium(m,F)
    collect(m,mrec,1,'hold_end',frame=True)
    for t in np.linspace(1,0,9)[1:]:
        F=m.F0.clone();F[:,0,1]=amps*t;equilibrium(m,F);collect(m,mrec,t,'unload',frame=t==0)
    for r in mrec:
        pts=r['curve'];last_load=next(p for p in pts if p['stage']=='load' and p['control']==1)
        held=next(p for p in pts if p['stage']=='hold_end')
        r['stressRetainedAfterHold']=held['Pxy']/last_load['Pxy'] if abs(last_load['Pxy'])>1e-12 else None
        crossings=[];unload=[p for p in pts if p['stage']=='unload']
        prev=held
        for p in unload:
            if prev['Pxy']*p['Pxy']<=0 and prev['Pxy']!=p['Pxy']:
                f=prev['Pxy']/(prev['Pxy']-p['Pxy']);crossings.append(r['parameters']['amplitude']*(prev['control']+f*(p['control']-prev['control'])))
            prev=p
        r['residualStrainInterpolated']=crossings[0] if crossings else None
    save('data/plastic-memory-matrix.json',{'lattice':lattice_record(lat),'cases':mrec})
    RESULTS['suites']['plastic_memory_matrix']={'file':'data/plastic-memory-matrix.json','cases':len(mcases)};emit('memory_matrix_done',cases=len(mcases))


def sliding_failure(device,profile):
    lat=Lattice(6 if profile=='commission' else 10);seeds=[17] if profile=='commission' else [17,29,43]
    levels=[0,.5,1] if profile=='commission' else [0,.25,.5,.75,1]
    cases=[{'seed':seed,'z':3.4,'kappa':1e-4,'locking':lock,'mobility':2*math.exp(-6*lock),'rupture':.20} for lock in levels for seed in seeds]
    specs=specifications(lat,cases);b=MechanismBatch(lat,specs,device);records=initial_records(lat,specs)
    initial=b.alive.sum(1).cpu().numpy();plastic=np.zeros(b.B);fracture=np.zeros(b.B)
    strains=np.linspace(0,.85,18 if profile=='commission' else 35)
    for strain in strains:
        F=b.F_stretch(float(strain),0);equilibrium(b,F)
        plastic+=b.slip(F,[c['mobility'] for c in cases],.1).cpu().numpy();equilibrium(b,F)
        settled=False
        for avalanche in range(8):
            before=b.energy(b.x,F,True).detach();broken=b.break_elastic(F);after=b.energy(b.x,F,True).detach()
            fracture+=(before-after).cpu().numpy()
            if int(broken.sum())==0:settled=True;break
            equilibrium(b,F)
        remaining=b.alive.sum(1).cpu().numpy()
        collect(b,records,strain,'tension_with_sliding_and_rupture',frame=True,extras={'plasticDissipation':plastic,'fractureEnergyRemoved':fracture,'brokenFraction':1-remaining/initial})
        for r in records:r['curve'][-1]['ruptureAvalancheSettled']=settled
    for r in records:
        valid=[p for p in r['curve'] if p['converged'] and p['ruptureAvalancheSettled']]
        failed=next((p for p in valid if p['brokenFraction']>=.2),None)
        r['strainAt20PercentBondLoss']=failed['control'] if failed else None
        r['failureCensored']=failed is None
        r['maximumValidTension']=max((p['Pxx'] for p in valid),default=None)
    save('data/sliding-failure.json',{'lattice':lattice_record(lat),'cases':records})
    RESULTS['suites']['sliding_failure']={'file':'data/sliding-failure.json','cases':len(cases)};emit('sliding_failure_done',cases=len(cases))


def percolation(device,profile):
    lat=Lattice(6 if profile=='commission' else 10);seeds=[17] if profile=='commission' else [17,29,43]
    levels=np.linspace(0,1,7 if profile=='commission' else 13)
    cases=[];specs=[]
    for seed in seeds:
        for placement in ['random','clustered']:
            for fraction in levels:
                c={'seed':seed,'z':3.6,'kappa':1e-4,'stiffFraction':float(fraction),'placement':placement}
                s=specifications(lat,[c])[0];ids=np.where(s.alive)[0];rng=np.random.default_rng(seed+71)
                if placement=='random':order=rng.permutation(ids)
                else:
                    centres=(lat.X[lat.bi]+lat.X[lat.bj]+lat.shift)/2
                    distance=np.linalg.norm((centres-lat.L/2+lat.L/2)%lat.L-lat.L/2,axis=1);order=ids[np.argsort(distance[ids])]
                s.mu[order[:round(fraction*len(ids))]]=20.;cases.append(c);specs.append(s)
    b=MechanismBatch(lat,specs,device);records=initial_records(lat,specs)
    for gamma in [0.,.005,.01]:equilibrium(b,b.F_shear(gamma));collect(b,records,gamma,'small_shear')
    for r in records:r['smallShearModulus']=(r['curve'][-1]['Pxy']-r['curve'][0]['Pxy'])/.01
    save('data/stiffness-percolation.json',{'lattice':lattice_record(lat),'cases':records})
    RESULTS['suites']['stiffness_percolation']={'file':'data/stiffness-percolation.json','cases':len(cases)};emit('stiffness_percolation_done',cases=len(cases))
    cases=[{'seed':s,'z':3.6,'kappa':1e-4,'cutMode':mode} for s in seeds for mode in ['random','high_tension']]
    specs=specifications(lat,cases);b=MechanismBatch(lat,specs,device);records=initial_records(lat,specs);initial=b.alive.sum(1).cpu().numpy()
    F=b.F_stretch(.12,0);equilibrium(b,F);collect(b,records,0,'cut_sweep',frame=True)
    rngs=[np.random.default_rng(c['seed']+91) for c in cases]
    for fraction in np.linspace(0,.65,14)[1:]:
        lengths=torch.linalg.vector_norm(b.bond_vectors(b.x,F),dim=-1).detach().cpu().numpy();alive=b.alive.cpu().numpy()
        for i,c in enumerate(cases):
            count=int(round(fraction*initial[i]))-(int(initial[i])-int(alive[i].sum()))
            candidates=np.where(alive[i])[0]
            order=rngs[i].permutation(candidates) if c['cutMode']=='random' else candidates[np.argsort(-np.maximum(lengths[i,candidates]-1,0))]
            b.alive[i,torch.as_tensor(order[:max(0,count)],device=device)]=False
        equilibrium(b,F);collect(b,records,fraction,'cut_sweep',frame=True)
    save('data/targeted-damage.json',{'lattice':lattice_record(lat),'cases':records})
    RESULTS['suites']['targeted_damage']={'file':'data/targeted-damage.json','cases':len(cases)};emit('targeted_damage_done',cases=len(cases))


def inclusions(device,profile):
    lat=Lattice(6 if profile=='commission' else 10);seeds=[17] if profile=='commission' else [17,29,43]
    fractions=[0,.4,.75] if profile=='commission' else [0,.2,.4,.6,.75,.84]
    cases=[{'seed':seed,'z':3.2,'kappa':1e-4,'areaFraction':phi} for phi in fractions for seed in seeds]
    specs=specifications(lat,cases);b=MechanismBatch(lat,specs,device);b.add_inclusions([c['areaFraction'] for c in cases])
    records=initial_records(lat,specs);strains=np.linspace(0,.45,10 if profile=='commission' else 19)
    for e in strains:
        equilibrium(b,b.F_stretch(-float(e),0));collect(b,records,e,'compression',frame=True)
    for i,r in enumerate(records):
        pressure=-np.array([p['Pxx'] for p in r['curve']]);K=np.gradient(pressure,strains)
        r['radii']=b.radii[i].cpu().tolist()
        for j,(p,k) in enumerate(zip(r['curve'],K)):
            p['incrementalCompressionModulus']=float(k)
            p['tangentValid']=all(q['converged'] for q in r['curve'][max(0,j-1):min(len(K),j+2)])
    save('data/inclusions.json',{'lattice':lattice_record(lat),'cases':records})
    RESULTS['suites']['inclusions']={'file':'data/inclusions.json','cases':len(cases)};emit('inclusions_done',cases=len(cases))


def feedback_and_thermal(device):
    records=[]
    for a in np.linspace(.2,2.,19):
        for g in np.linspace(0,5.,51):
            roots=field_roots(float(a),float(g));records.append({'coupling':float(a),'productionGain':float(g),'equilibria':roots,'stableEquilibria':sum(r['stable'] for r in roots)})
    up=feedback_path(1.,np.linspace(0,5,101),(.30,0,.05))
    end=up[-1];down=feedback_path(1.,np.linspace(5,0,101),(end['stiffness'],end['contractility'],end['lox']))
    save('data/lox-feedback.json',{'equilibria':records,'up':up,'down':down,'interpretation':'Hypothetical three-stage saturating feedback. Bistability requires two stable equilibria and an intervening unstable equilibrium; gain alone is not sufficient.'})
    RESULTS['suites']['lox_feedback']={'file':'data/lox-feedback.json','cases':len(records)}
    temperatures=np.linspace(.35,1.8,117).tolist();thermal=[]
    for hyp in [0,.5,1]:
        for hydration in [0,.5,1]:
            for crosslink in [0,.5]:
                q=helix_coil(temperatures,hyp,hydration,crosslink,device)
                thermal.append({'hypothesisHypFraction':hyp,'hypothesisHydration':hydration,'hypothesisCrosslink':crosslink,'T_over_reference':temperatures,'foldedFraction':q})
    save('data/helix-coil-sensitivity.json',{'cases':thermal,'sites':81,'kind':'exact finite-chain statistical sensitivity model','calibrated':False,'atomisticMD':False,'celsiusMapping':None,'assumptions':{'siteStabilization':'.8+.25*Hyp+.15*hydration+.10*crosslink','boundaryPenalty':'.45+.25*crosslink','foldingEntropyCost':1}})
    save('THERMAL_MD_GATE.json',{'status':'not_run','reason':'No matched force-field-validated Hyp/crosslink/hydration ensemble or adequately sampled melting protocol exists in this new run. A short hot trajectory cannot determine an equilibrium melting point.','required':['Matched triple-helix sequences and termini','Verified Hyp and covalent crosslink parameters and stereochemistry','Explicit hydration definition and matched controls','Multiple independent replicas and reversible or enhanced sampling','Native contacts, hydrogen bonds and helix observables with block uncertainty','Heating/cooling rate and finite-length dependence','Compare avian and human material only under matched assay conditions']})
    RESULTS['suites']['helix_coil']={'file':'data/helix-coil-sensitivity.json','cases':len(thermal)};emit('feedback_thermal_done')


def main():
    global OUT,CFG,DEADLINE
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--device',default='cuda');ap.add_argument('--profile',choices=['checks','commission','pilot'],default='pilot');ap.add_argument('--minutes',type=float,default=65);args=ap.parse_args()
    OUT=Path(args.out).resolve();OUT.mkdir(parents=True,exist_ok=False);DEADLINE=args.minutes*60
    CFG={'tol':3e-8,'rounds':5,'iters':200}
    for p in Path(__file__).parent.glob('*.py'):shutil.copyfile(p,OUT/p.name)
    for p in Path(__file__).parent.glob('*.md'):shutil.copyfile(p,OUT/p.name)
    save('RUN_CONTEXT.json',{'profile':args.profile,'device':args.device,'runtimeMinutesLimit':args.minutes,'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'cudaRuntime':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'config':CFG,'sourceSHA256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}})
    try:
        if args.device=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA required but unavailable')
        tests(args.device)
        if args.profile!='checks':
            rigidity(args.device,args.profile);sliding_and_memory(args.device,args.profile);sliding_failure(args.device,args.profile);percolation(args.device,args.profile);inclusions(args.device,args.profile);feedback_and_thermal(args.device)
        RESULTS['elapsedSeconds']=time.monotonic()-START
        RESULTS['limitations']=['Dimensionless finite 2D network models; no pressure/acceleration calibration or universal critical exponents.','Locking and plasticity laws are declared hypotheses, not validated AGE chemistry.','Inclusion model uses disks at network junctions, not cells with membranes or volumes.','Helix-coil sensitivity is not atomistic MD or an experimentally calibrated melting temperature.','Feedback branches are mathematical equilibria, not measured LOX-cell signaling.','All saved curves include convergence flags; unconverged samples are ineligible for scientific conclusions.']
        counts={'samples':0,'converged':0}
        for p in (OUT/'data').glob('*.json'):
            obj=json.loads(p.read_text());groups=obj if isinstance(obj,list) else [obj]
            for group in groups:
                for case in group.get('cases',[]):
                    for point in case.get('curve',[]):counts['samples']+=1;counts['converged']+=int(point.get('converged',False))
        RESULTS['numericalSamples']=counts;save('RESULTS.json',RESULTS)
        if args.profile!='checks':
            from plot_results import render
            render(OUT)
        save('FINISHED.json',{'status':'complete','kind':'archive','provenance':{'study':'collagen-transition-atlas','profile':args.profile,'validation':'CHECKS.json and per-sample convergence flags; uncalibrated hypotheses','convergence':counts,'source':'RUN_CONTEXT.json'}})
        emit('finished',**counts)
    except Exception as exc:
        save('FAILED.json',{'status':'failed','error':str(exc),'traceback':traceback.format_exc(),'elapsedSeconds':time.monotonic()-START});emit('failed',error=str(exc));raise
    finally:
        manifest={}
        for p in sorted(OUT.rglob('*')):
            if p.is_file():manifest[str(p.relative_to(OUT))]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        save('MANIFEST.json',manifest)

if __name__=='__main__':main()
