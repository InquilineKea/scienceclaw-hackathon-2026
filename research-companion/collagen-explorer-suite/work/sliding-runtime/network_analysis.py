"""Original conditional molecular-to-network analysis, run in reviewed remote NumPy runtime."""
import csv,json,math,itertools,sys
from pathlib import Path
import numpy as np
ROOT=Path(sys.argv[1]);OUT=Path(sys.argv[2]);OUT.mkdir(exist_ok=False)
PAIRS={'GLU_LINKED':'GLU_CONTROL','PYD':'PYD_LYS_CONTROL','DPD':'DPD_LYS_CONTROL'}
def dump(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def interval(values):
 a=np.asarray(values,float);return {'mean':float(a.mean()),'min':float(a.min()),'max':float(a.max()),'n':len(a)}
def fit(rows):
 forward=[r for r in rows if r['stage']=='forward'];x=np.array([float(r['slip_nm']) for r in forward]);y=np.array([float(r['force_kJ_mol_nm']) for r in forward]);q=np.array([float(r['q_nm']) for r in forward])
 # Use the externally commanded ramp as an instrument: regressing force on
 # instantaneous slip directly induces a negative thermal-noise correlation,
 # because the spring readout itself is kb*(q-slip).
 A=np.column_stack([q,np.ones(len(q))]);force_slope,offset=np.linalg.lstsq(A,y,rcond=None)[0];slip_slope,_=np.linalg.lstsq(A,x,rcond=None)[0]
 slope=force_slope/slip_slope if slip_slope>1e-6 else -1.
 pred=force_slope*q+offset;r2=1-float(np.sum((y-pred)**2))/max(1e-20,float(np.sum((y-y.mean())**2)))
 baseline=np.mean([float(r['force_kJ_mol_nm']) for r in rows if r['stage']=='zero_load'][-10:])
 fwd=np.mean([float(r['force_kJ_mol_nm']) for r in forward][-5:])-baseline
 hold=np.mean([float(r['force_kJ_mol_nm']) for r in rows if r['stage']=='hold'][-5:])-baseline
 return {'slope_kJ_mol_nm2':float(slope),'slope_pN_nm':float(slope*1.660539067),'r_squared':r2,'forward_force_pN':float(fwd*1.660539067),'hold_force_pN':float(hold*1.660539067),'hold_forward_ratio':float(hold/fwd) if fwd>1e-6 else None,'actual_slip_span_nm':float(np.ptp(x))}
summary=json.loads((ROOT/'summary.json').read_text());molecular=[]
for result in summary['runs']:
 name=result['case'];p=ROOT/name/f"sliding_rep{result['replica']}_ramp{result['ramp_ps']}"/'curve.csv'
 rows=list(csv.DictReader(p.open()));record=dict(result,**fit(rows));record['transfer_gate']=record['slope_pN_nm']>0 and record['actual_slip_span_nm']>.015 and record['r_squared']>.3
 molecular.append(record)
dump(OUT/'molecular-summary.json',{'records':molecular,'failures':summary['failures'],'interval_scope':'replica spread conditional on one prepared conformation and solvent build per model','native_control_scope':'LYS restored; hydroxylation and charge confounded'})

def mesh(seed):
 rng=np.random.default_rng(seed);xy=[];grid={}
 for j in range(11):
  for i in range(11):
   p=np.array([i+.5*(j%2)-5,j*math.sqrt(3)/2-4.33])
   if np.linalg.norm(p)<1.5:continue
   grid[(i,j)]=len(xy);xy.append(p)
 xy=np.array(xy);N=len(xy);edges=[]
 for i in range(N):
  for j in range(i+1,N):
   if abs(np.linalg.norm(xy[j]-xy[i])-1)<1e-5 and rng.random()<.88:edges.append((i,j))
 # Explicit linear bending Hessian for opposite collinear unit segments.
 bend=np.zeros((2*N,2*N));adj={i:set() for i in range(N)}
 for i,j in edges:adj[i].add(j);adj[j].add(i)
 for j,neigh in adj.items():
  for i,k in itertools.combinations(neigh,2):
   if np.linalg.norm(xy[i]+xy[k]-2*xy[j])<1e-5:
    v=xy[i]-xy[j];perp=np.array([-v[1],v[0]]);b=np.zeros(2*N)
    for n,c in [(i,1),(j,-2),(k,1)]:b[2*n:2*n+2]=c*perp
    bend+=.03*np.outer(b,b)
 outer=np.array([i for i,p in enumerate(xy) if abs(p[0])>4.4 or abs(p[1])>3.5]);adh=np.array([i for i,p in enumerate(xy) if 1.5<=np.linalg.norm(p)<2.15 and i not in outer])
 assert len(adh)>=6
 return xy,edges,bend,outer,adh
def stiffness(xy,edges,bend,selection,kj):
 K=bend.copy()
 for e,(i,j) in enumerate(edges):
  v=xy[j]-xy[i];v/=np.linalg.norm(v);b=np.zeros(len(K));b[2*i:2*i+2]=-v;b[2*j:2*j+2]=v
  # Condensed series element: min_s .5*(extension-s)^2+.5*kj*s^2.
  # Unselected edges retain a reference kj=1. No physical mapping is implied.
  k=(kj/(1+kj)) if e in selection else .5;K+=k*np.outer(b,b)
 return K
def solve(K,ids,prescribed):
 fixed=np.array([k for i in ids for k in (2*i,2*i+1)]);free=np.setdiff1d(np.arange(len(K)),fixed);u=np.zeros(len(K));u[fixed]=prescribed.reshape(-1)
 A=K[np.ix_(free,free)];eig=np.linalg.eigvalsh(A)
 if eig[0]<1e-9:raise ValueError('Unstable or disconnected constrained network')
 u[free]=np.linalg.solve(A,-K[np.ix_(free,fixed)]@u[fixed]);reaction=K@u
 assert np.max(abs(reaction[free]))<1e-8
 return u,reaction,float(.5*u@reaction)
checks={}
tx,te,tb,to,ta=mesh(4700);TK=stiffness(tx,te,tb,set(range(len(te))),1.)
translation=np.tile([1.,-.7],len(tx));checks['rigid_translation_force_max']=float(np.max(abs(TK@translation)))
assert checks['rigid_translation_force_max']<1e-10
disp=np.column_stack([.01*tx[to,1],np.zeros(len(to))]);tu,tf,energy=solve(TK,to,disp)
checks['global_force_balance_max']=float(np.max(abs(tf.reshape(-1,2).sum(0))));assert checks['global_force_balance_max']<1e-9
eps=1e-6;direction=np.random.default_rng(1).normal(size=len(TK));fd=((tu+eps*direction)@TK@(tu+eps*direction)-(tu-eps*direction)@TK@(tu-eps*direction))/(4*eps)
checks['energy_force_derivative_error']=abs(float(fd-direction@tf));assert checks['energy_force_derivative_error']<1e-8
checks['hessian_symmetry_max']=float(np.max(abs(TK-TK.T)));assert checks['hessian_symmetry_max']<1e-12
for kj in (.1,1.,10.):
 slip=1/(1+kj);E=.5*(1-slip)**2+.5*kj*slip**2;assert abs(2*E-kj/(1+kj))<1e-12
checks['series_element_independent_energy_check']=True
dump(OUT/'network-validation.json',checks)
net=[];failures=[];examples=[];placement_previews=[]
for seed in range(12):
 xy,edges,bend,outer,adh=mesh(4700+seed);rng=np.random.default_rng(9800+seed);count=round(.35*len(edges));uniform=set(rng.choice(len(edges),count,replace=False).tolist())
 # Same junction count, enriched beside the right-hand cell pole.
 clustered=set(sorted(range(len(edges)),key=lambda e:np.linalg.norm((xy[edges[e][0]]+xy[edges[e][1]])/2-np.array([2.,0.])))[:count])
 if seed==0:
  placement_previews=[{'topology':t,'xy':xy.tolist(),'edges':edges,'selected_edges':sorted(sel),'adhesion_nodes':adh.tolist()} for t,sel in [('uniform',uniform),('clustered',clustered)]]
 fixed=np.unique(np.r_[outer,adh]);pres=np.array([-.04*xy[i]/np.linalg.norm(xy[i]) if i in adh else [0.,0.] for i in fixed])
 shear=np.column_stack([.01*xy[outer,1],np.zeros(len(outer))])
 for linked,control in PAIRS.items():
  for rate in (40,80):
   for rep in range(3):
    l=next((r for r in molecular if r['case']==linked and r['replica']==rep and r['ramp_ps']==rate),None);c=next((r for r in molecular if r['case']==control and r['replica']==rep and r['ramp_ps']==rate),None)
    if not l or not c or not l['transfer_gate'] or not c['transfer_gate']:
     failures.append({'seed':seed,'linked':linked,'replica':rep,'ramp_ps':rate,'reason':'molecular transfer gate failed or trajectory unavailable'});continue
    ratio=l['slope_pN_nm']/c['slope_pN_nm']
    for scale in (.1,1.,10.):
     for topology,sel in [('uniform',uniform),('clustered',clustered)]:
      try:
       K=stiffness(xy,edges,bend,sel,scale*ratio);Kc=stiffness(xy,edges,bend,sel,scale)
       _,_,E=solve(K,outer,shear);_,_,Ec=solve(Kc,outer,shear)
       for mode,factor in [('fixed_microscopic_laws',1.),('matched_initial_bulk_stiffness',Ec/E)]:
        u,F,energy=solve(K*factor,fixed,pres);_,Fc,_=solve(Kc,fixed,pres);fn=F.reshape(-1,2)[adh];fc=Fc.reshape(-1,2)[adh];rad=xy[adh]/np.linalg.norm(xy[adh],axis=1)[:,None]
        magnitude=np.linalg.norm(fn,axis=1);ref=np.linalg.norm(fc,axis=1);record={'seed':seed,'linked':linked,'control':control,'replica':rep,'ramp_ps':rate,'junction_mapping_scale':scale,'topology':topology,'comparison':mode,'molecular_slope_ratio':ratio,'mean_adhesion_force':float(magnitude.mean()),'control_mean_adhesion_force':float(ref.mean()),'force_ratio_to_control':float(magnitude.mean()/ref.mean()),'maximum_adhesion_force':float(magnitude.max()),'adhesion_force_CV':float(magnitude.std()/magnitude.mean()),'bulk_matching_factor':factor,'bulk_shear_energy':E*factor,'control_bulk_shear_energy':Ec,'energy':energy,'nodes':len(xy),'edges':len(edges),'modified_junctions':len(sel),'adhesion_sites':len(adh)}
        net.append(record)
        if seed==0 and rep==0:
         examples.append({'key':{k:record[k] for k in ('linked','topology','comparison','ramp_ps','junction_mapping_scale')},'xy':xy.tolist(),'edges':edges,'selected_edges':sorted(sel),'adhesion_nodes':adh.tolist(),'forces':fn.tolist(),'control_forces':fc.tolist(),'displacements':u.reshape(-1,2).tolist()})
      except Exception as e:failures.append({'seed':seed,'linked':linked,'replica':rep,'ramp_ps':rate,'reason':str(e)})
dump(OUT/'network-results.json',{'records':net,'exclusions':failures,'examples':examples,'placement_previews':placement_previews,'scope':'conditional dimensionless small-strain network sensitivity; no calibrated cell-scale time or absolute traction','mapping_scales':[.1,1,10],'seed_count':12,'bending_coefficient':.03,'fiber_stretch_coefficient':1,'unmodified_junction_coefficient':1,'lattice_dilution':.88,'modified_junction_fraction':.35,'contraction_displacement_lattice_units':.04})
with (OUT/'network-results.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(net[0]) if net else ['seed','linked','replica','ramp_ps','topology','comparison','force_ratio_to_control']);w.writeheader();w.writerows(net)
print(json.dumps({'molecular_records':len(molecular),'molecular_gate_pass':sum(r['transfer_gate'] for r in molecular),'network_records':len(net),'excluded_network_inputs':len(failures)}))
