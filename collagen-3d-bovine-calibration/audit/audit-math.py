"""Independent equation audit using Python stdlib only; imports no solver/package code."""
import json, math, hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def eval_model(m,u,g,plane,active=None):
 active=m['active'] if active is None else active; vv=[]; lens=[]; uni=[]; grad=[[0.,0.,0.] for _ in m['x']];terms=[];stress=0.
 for k,e in enumerate(m['e']):
  i,j=e[:2];v=[m['v'][k][d]+u[j][d]-u[i][d]+(g*m['v'][k][plane] if d==0 else 0.) for d in range(3)];l=math.sqrt(dot(v,v));n=[a/l for a in v];vv.append(v);lens.append(l);uni.append(n)
  if active[k]:
   stretch=l-m['rest'][k];en=stretch**2/(2*m['rest'][k]);t=stretch/m['rest'][k];terms.append(('edge',k,en))
   for d in range(3):grad[i][d]-=t*n[d];grad[j][d]+=t*n[d]
   stress+=t*n[0]*m['v'][k][plane]
 for k,(a,b,sg) in enumerate(m['a']):
  if not(active[a] and active[b]):continue
  co=dot(uni[a],uni[b]);err=sg*co-m['c0'][k];weight=m['aw'][k];en=weight*err**2/2;terms.append(('angle',k,en))
  aa=[sg*(uni[b][d]-co*uni[a][d])/lens[a] for d in range(3)];bb=[sg*(uni[a][d]-co*uni[b][d])/lens[b] for d in range(3)]
  for edge,v in [(a,aa),(b,bb)]:
   i,j=m['e'][edge][:2]
   for d in range(3):grad[i][d]-=weight*err*v[d];grad[j][d]+=weight*err*v[d]
  stress+=weight*err*(aa[0]*m['v'][a][plane]+bb[0]*m['v'][b][plane])
 return sum(t[2] for t in terms),grad,stress,terms
results=[]
for m in json.loads((P/'models.json').read_text()):
 if m['pattern']!='baseline':continue
 n=len(m['x']);u=[[0. if i==0 else math.sin((3*i+d)*1.2)*1e-4 for d in range(3)] for i in range(n)];g=.03;E,grad,stress,terms=eval_model(m,u,g,1);errors=[]
 for eps in [1e-6,1e-7,1e-8]:
  mx=0.
  for dof in [3,7,12,26,47,83,115,217,3*n-1]:
   i,d=divmod(dof,3);up=[v[:] for v in u];um=[v[:] for v in u];up[i][d]+=eps;um[i][d]-=eps;fd=(eval_model(m,up,g,1)[0]-eval_model(m,um,g,1)[0])/(2*eps);mx=max(mx,abs(fd-grad[i][d]))
  se=abs((eval_model(m,u,g+eps,1)[0]-eval_model(m,u,g-eps,1)[0])/(2*eps)-stress);errors.append(dict(eps=eps,max_sampled_gradient_error=mx,stress_error=se))
 translation=max(abs(sum(v[d] for v in grad)) for d in range(3));rest=eval_model(m,[[0.,0.,0.] for _ in range(n)],0,1)[0];edge=next(k for k,on in enumerate(m['active']) if on);active=m['active'][:];active[edge]=False;after=eval_model(m,u,g,1,active)[0];removed=sum(t[2] for t in terms if (t[0]=='edge' and t[1]==edge) or (t[0]=='angle' and edge in m['a'][t[1]][:2]));deletionerror=abs(E-after-removed)
 results.append(dict(seed=m['seed'],gradient_and_stress=errors,translation_force_sum=translation,rest_energy=rest,deleted_edge=edge,deletion_energy_error=deletionerror))
 assert min(r['max_sampled_gradient_error'] for r in errors)<1e-7 and min(r['stress_error'] for r in errors)<1e-8 and translation<1e-10 and rest<1e-20 and deletionerror<1e-14
out=dict(scope='Independent stdlib equation checks; no numerical relaxation or biological validation',records=results,source_sha256={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['cpu-solver.py','solver.mjs','models.json']})
(Path(__file__).parent/'equation-checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
