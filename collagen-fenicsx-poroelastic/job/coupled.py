"""Original matched discrete-solid / FEniCSx Darcy-Biot frequency experiment."""
import os,sys,json,gzip,time,hashlib,warnings
from pathlib import Path
import numpy as np
import scipy,scipy.sparse as sp
from scipy.sparse.linalg import splu,MatrixRankWarning
import mpi4py
mpi4py.rc.finalize=False
from mpi4py import MPI
import dolfinx,basix.ufl,ufl
from dolfinx import fem,mesh
from dolfinx.fem import petsc as fp
from petsc4py import PETSc
assert MPI.COMM_WORLD.size==1
# Runtime initialization has completed; scientific work cannot open IP sockets.
from isolation import deny_network
deny_network()
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False)
JIT={'cache_dir':'/tmp/poro-jit'}
START=time.time()

def cells_for(n):
 c=[]
 for y in range(n-1):
  for x in range(n-1):
   a=y*n+x;b=a+1;c0=a+n;d=c0+1;c.extend([[a,b,d],[a,d,c0]])
 return c

def refined(c,level):
 pts=np.array(c['X']).reshape(-1,2).tolist();refs=[[(i,1.)] for i in range(len(pts))];cells=cells_for(c['n'])
 if level==2:
  mids={};cc=[]
  def midpoint(a,b):
   key=tuple(sorted((a,b)))
   if key not in mids:
    mids[key]=len(pts);pts.append(((np.array(pts[a])+pts[b])/2).tolist());refs.append([(a,.5),(b,.5)])
   return mids[key]
  for a,b,d in cells:
   ab=midpoint(a,b);bd=midpoint(b,d);da=midpoint(d,a);cc.extend([[a,ab,da],[ab,b,bd],[da,bd,d],[ab,bd,da]])
  cells=cc
 return np.array(pts),np.array(cells,dtype=np.int64),refs

def csr(a):
 a.assemble();ip,ix,v=a.getValuesCSR();r=sp.csr_matrix((v.copy(),ix.copy(),ip.copy()),shape=a.getSize());a.destroy();return r

def operators(c,level):
 pts,cells,refs=refined(c,level)
 domain=ufl.Mesh(basix.ufl.element('Lagrange','triangle',1,shape=(2,)))
 msh=mesh.create_mesh(MPI.COMM_SELF,cells,domain,pts)
 V=fem.functionspace(msh,basix.ufl.element('Lagrange','triangle',1,shape=(2,)))
 Q=fem.functionspace(msh,basix.ufl.element('Lagrange','triangle',1))
 u=ufl.TrialFunction(V);q=ufl.TestFunction(Q);p=ufl.TrialFunction(Q)
 def form(a):return fem.form(a,jit_options=JIT)
 mass=csr(fp.assemble_matrix(form(p*q*ufl.dx)))
 lap=csr(fp.assemble_matrix(form(ufl.inner(ufl.grad(p),ufl.grad(q))*ufl.dx)))
 gf=csr(fp.assemble_matrix(form(ufl.div(u)*q*ufl.dx)))
 vc=V.tabulate_dof_coordinates()[:,:2];qc=Q.tabulate_dof_coordinates()[:,:2]
 lookup={tuple(np.round(x,11)):i for i,x in enumerate(pts)}
 vi=[lookup[tuple(np.round(x,11))] for x in vc];qi=[lookup[tuple(np.round(x,11))] for x in qc]
 rr=[];cc=[];vv=[]
 for i,node in enumerate(vi):
  for a,w in refs[node]:
   for j in [0,1]:rr.append(2*i+j);cc.append(2*a+j);vv.append(w)
 T=sp.csr_matrix((vv,(rr,cc)),shape=(2*len(vc),len(c['X'])))
 allB=gf@T
 one=np.ones(len(qc));affine=np.array(c['X']);check=np.linalg.norm(allB@affine-2*(mass@one))/np.linalg.norm(2*(mass@one))
 assert check<1e-10,('affine divergence',check)
 assert abs(one@mass@one-c['size']**2)<1e-10
 assert np.linalg.norm(lap@one)<1e-9
 boundary=np.any(np.isclose(qc,0,atol=1e-10)|np.isclose(qc,c['size'],atol=1e-10),axis=1)
 interior=np.flatnonzero(~boundary)
 B=allB[:,c['free']].tocsr()
 # Manufactured Darcy-Poisson test on the two pressure meshes.
 x=ufl.SpatialCoordinate(msh);exact=ufl.sin(np.pi*x[0]/c['size'])*ufl.sin(np.pi*x[1]/c['size'])
 load=fp.assemble_vector(form((2*np.pi**2/c['size']**2)*exact*q*ufl.dx)).array.copy()
 sol=splu(lap[interior][:,interior].tocsc()).solve(load[interior]);fun=fem.Function(Q);fun.x.array[:]=0;fun.x.array[interior]=sol
 l2=np.sqrt(abs(fem.assemble_scalar(form((fun-exact)**2*ufl.dx))))
 return {'M':mass,'D':lap,'B':B,'interior':interior,'points':pts,'cells':cells,'qInputOrder':qi,'checks':{'level':level,'nodes':len(qc),'affineDivergenceRelative':float(check),'darcyManufacturedL2':float(l2),'massArea':float(one@mass@one)}}

def quantities(c,b,u):
 X=np.array(c['X']).reshape(-1,2);xy=np.mean(X[c['probe']],axis=0);free=np.array(c['free']);nodes=free[::2]//2;r=np.linalg.norm(X[nodes]-xy,axis=1);amp2=np.sum(np.abs(u.reshape(-1,2))**2,axis=1);z=b@u
 bins=[]
 for a in np.arange(0,2.4,.2):
  use=(r>=a)&(r<a+.2);bins.append({'r':float(a+.1),'count':int(use.sum()),'rms':float(np.sqrt(np.mean(amp2[use]))) if use.any() else None})
 return {'selfReal':float(z.real),'selfImag':float(z.imag),'selfAmplitude':float(abs(z)),'phaseLag':float(np.angle(np.conj(z))),'farRms':float(np.sqrt(np.mean(amp2[r>=.6]))),'farNodes':int((r>=.6).sum()),'bins':bins}

def linear_solve(A,rhs):
 try:
  with warnings.catch_warnings():
   warnings.simplefilter('error',MatrixRankWarning);u=splu(A.tocsc()).solve(rhs)
  res=np.linalg.norm(A@u-rhs)/np.linalg.norm(rhs)
  if not np.isfinite(res) or res>1e-8:return None,float(res)
  return u,float(res)
 except (RuntimeError,MatrixRankWarning):return None,None

def execute(c,ops):
 rows=[];fields=[];coupling_checks=[];N=len(c['free']);rhs=np.zeros((N,2),dtype=complex)
 for j,k in enumerate(c['free']):
  if k//2 in c['probe']:rhs[j,k%2]=.25
 for st in c['states']:
  K=sp.csr_matrix((st['data'],st['indices'],st['indptr']),shape=(N,N)).astype(complex);I=sp.eye(N,format='csr')
  for w in [0,.03,.1,.3,1,3]:
   base,res=linear_solve(K+1j*w*I,rhs)
   for dr in [0,1]:rows.append({'model':'drag','level':None,'permeability':None,'omega':w,'direction':dr,'damaged':st['damaged'],'resolved':base is not None,'residual':res,**(quantities(c,rhs[:,dr],base[:,dr]) if base is not None else {})})
   if w==0:continue
   for level,op in ops.items():
    ids=op['interior'];B=op['B'][ids];mass=op['M'][ids][:,ids];lap=op['D'][ids][:,ids];Z=sp.csr_matrix((len(ids),2),dtype=complex);target=np.vstack((rhs,np.zeros((len(ids),2),complex)))
    for permeability in [.001,.1]:
     fluid=permeability*lap+1j*w*.1*mass
     full=sp.bmat([[K+1j*w*I,-B.T],[1j*w*B,fluid]],format='csc');sol,err=linear_solve(full,target)
     for dr in [0,1]:
      row={'model':'poro','level':level,'permeability':permeability,'omega':w,'direction':dr,'damaged':st['damaged'],'resolved':sol is not None,'residual':err}
      if sol is not None:
       uu=sol[:N,dr];pp=sol[N:,dr];row.update(quantities(c,rhs[:,dr],uu));row['pressureRms']=float(np.sqrt(abs(pp.conj()@(mass@pp))/c['size']**2))
       if row['selfImag']>1e-7:raise RuntimeError('Nonpassive response')
       if c['n']==14 and c['seed']==17 and dr==0 and w==.1 and level==2 and permeability==.001:
        pfull=np.zeros(op['M'].shape[0],complex);pfull[ids]=pp;porder=np.zeros(len(op['points']),complex)
        for i,idx in enumerate(op['qInputOrder']):porder[idx]=pfull[i]
        fields.append({'model':'poro','damaged':st['damaged'],'real':uu.real.tolist(),'imag':uu.imag.tolist(),'pressureReal':porder.real.tolist(),'pressureImag':porder.imag.tolist(),'pressurePoints':op['points'].tolist(),'pressureCells':op['cells'].tolist()})
      rows.append(row)
     if c['seed']==17 and level==1 and w==.1 and permeability==.1:
      alpha0=sp.bmat([[K+1j*w*I,sp.csr_matrix(B.T.shape)],[sp.csr_matrix(B.shape),fluid]],format='csc');test,er=linear_solve(alpha0,target);deviation=float(np.linalg.norm(test[:N]-base)/np.linalg.norm(base));coupling_checks.append({'damaged':st['damaged'],'alphaZeroDeviation':deviation});assert deviation<1e-10
   if c['n']==14 and c['seed']==17 and w==.1 and base is not None:fields.append({'model':'drag','damaged':st['damaged'],'real':base[:,0].real.tolist(),'imag':base[:,0].imag.tolist()})
 return rows,fields,coupling_checks

cases=json.loads(gzip.decompress(Path(__file__).with_name('networks.json.gz').read_bytes()))
all_rows=[];records=[];animation=[]
for index,c in enumerate(cases):
 ops={level:operators(c,level) for level in [1,2]}
 assert ops[2]['checks']['darcyManufacturedL2']<.4*ops[1]['checks']['darcyManufacturedL2'],'Darcy refinement test'
 rows,fields,controls=execute(c,ops)
 for r in rows:r.update({k:c[k] for k in ['n','family','seed','pattern']})
 all_rows.extend(rows);records.append({**{k:c[k] for k in ['n','family','seed','pattern','size','probe','lesion']},'operatorChecks':[v['checks'] for v in ops.values()],'couplingChecks':controls})
 if fields:animation.append({**{k:c[k] for k in ['n','family','seed','pattern','size','X','free','edges','links','probe','lesion']},'fields':fields})
 (OUT/'partial.json').write_text(json.dumps({'rows':all_rows,'records':records}))
 print(json.dumps({'completed':index+1,'expected':len(cases),'seconds':time.time()-START}),flush=True)
report={'versions':{'dolfinx':dolfinx.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'petsc':PETSc.Sys.getVersion(),'scalarType':str(PETSc.ScalarType)},'seconds':time.time()-START,'rows':all_rows,'records':records}
(OUT/'results.json').write_text(json.dumps(report));(OUT/'animation.json').write_text(json.dumps(animation));
from plot import generate
generate(OUT)
(OUT/'FINISHED.json').write_text(json.dumps({'completed':len(cases),'systems':len(all_rows),'resolved':sum(r['resolved'] for r in all_rows),'seconds':time.time()-START}));print((OUT/'FINISHED.json').read_text(),flush=True)
