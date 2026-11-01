"""Independent original stdlib angular quadrature probe; no measured outcomes or imports."""
import math,itertools,json
from pathlib import Path
P=Path(__file__).parent

def scalar(e,d0):
 if e<0 and d0 is not None:
  z=e/d0;return d0*d0*(math.expm1(z)-z),d0*math.expm1(z)
 if e<=.04:return .5*e*e,e
 x=e-.04;return .5*.04**2+.04*x+.05**2*(math.expm1(x/.05)-x/.05),.04+.05*math.expm1(x/.05)

def returnmap(e,d0,Y):
 if Y is None:return scalar(e,d0)
 w,t=scalar(e,d0)
 if t<=Y:return w,t
 lo=0.;hi=e;target=.05*e+Y
 for _ in range(55):
  mid=(lo+hi)/2
  if scalar(mid,d0)[1]+.05*mid>target:hi=mid
  else:lo=mid
 elastic=(lo+hi)/2;s=e-elastic;w,t=scalar(elastic,d0);return w+.5*.05*s*s+Y*s,t

def lebedev(order):
 out=[]
 for i in range(3):
  for sign in [-1,1]:n=[0.,0.,0.];n[i]=sign;out.append((n,1/21 if order==26 else .0126984126984127))
 for zero in range(3):
  for a,b in itertools.product([-1,1],repeat=2):n=[0.,0.,0.];indices=[i for i in range(3) if i!=zero];n[indices[0]]=a/math.sqrt(2);n[indices[1]]=b/math.sqrt(2);out.append((n,4/105 if order==26 else .0225749559082892))
 for signs in itertools.product([-1,1],repeat=3):out.append(([s/math.sqrt(3) for s in signs],9/280 if order==26 else .02109375))
 if order==50:
  for long in range(3):
   for signs in itertools.product([-1,1],repeat=3):out.append(([s*(3 if j==long else 1)/math.sqrt(11) for j,s in enumerate(signs)],.0201733355379189))
 assert abs(sum(w for n,w in out)-1)<1e-12
 return out

def gauss_sphere(n,m):
 out=[]
 for i in range(n):
  x=math.cos(math.pi*(i+.75)/(n+.5))
  for _ in range(30):
   p0=1.;p1=x
   for j in range(2,n+1):p0,p1=p1,((2*j-1)*x*p1-(j-1)*p0)/j
   derivative=n*(x*p1-p0)/(x*x-1);delta=p1/derivative;x-=delta
   if abs(delta)<1e-15:break
  # Re-evaluate derivative at the converged node.
  p0=1.;p1=x
  for j in range(2,n+1):p0,p1=p1,((2*j-1)*x*p1-(j-1)*p0)/j
  derivative=n*(x*p1-p0)/(x*x-1);w=2/((1-x*x)*derivative*derivative)
  for j in range(m):phi=2*math.pi*j/m;r=math.sqrt(1-x*x);out.append(([r*math.cos(phi),r*math.sin(phi),x],w/(2*m)))
 assert abs(sum(w for a,w in out)-1)<1e-12
 return out

def mm(A,B):return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def energy_stress(F,quad,d0,Y):
 E=0.;S=[0.]*9
 for n,weight in quad:
  v=[sum(F[i][j]*n[j] for j in range(3)) for i in range(3)];l=math.sqrt(sum(x*x for x in v));w,t=returnmap(l-1,d0,Y);weight*=15;E+=weight*w
  for i in range(3):
   for j in range(3):S[3*i+j]+=weight*t*v[i]/l*n[j]
 return E,S

def rel(a,b):return abs(a-b)/max(abs(a),abs(b),1e-15)
def vector_rel(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))/max(math.sqrt(sum(x*x for x in a)),math.sqrt(sum(y*y for y in b)),1e-15)

def main():
 grids={26:lebedev(26),50:lebedev(50),128:gauss_sphere(8,16),512:gauss_sphere(16,32),1152:gauss_sphere(24,48),2048:gauss_sphere(32,64),8192:gauss_sphere(64,128)};Flist={'mixed_6pct':[[1.06,.081,.013],[.007,.963,.031],[.011,.002,1.021]],'simple_shear_20pct':[[1,.2,0],[0,1,0],[0,0,1]],'stretch_compression':[[1.15,0,0],[0,.92,0],[0,0,.97]]};angle=.37;R=[[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]];out=[]
 for name,F in Flist.items():
  for d0,Y in itertools.product([None,.0025,.01,.04],[None,.01,.04]):
   values={k:energy_stress(F,q,d0,Y) for k,q in grids.items()};rotations={k:energy_stress(mm(F,R),q,d0,Y)[0] for k,q in grids.items()};Eref,Pref=values[8192]
   out.append(dict(probe=name,d0=d0,yield_force=Y,zero_previous_slip=True,reference_energy=Eref,grids={str(k):{'energy_relative_difference_vs8192':rel(v[0],Eref),'Piola_relative_difference_vs8192':vector_rel(v[1],Pref),'right_rotation_energy_relative_difference':rel(v[0],rotations[k])} for k,v in values.items()}))
 report={'scope':'Controlled local energy/tangent integration, not full FE re-equilibration or experimental scoring','reference_grid':'64polar Gauss-Legendre x128azimuth =8192 positive sphere points; comparison2048checks reference convergence','records':out,'max_errors':{str(k):{'energy':max(r['grids'][str(k)]['energy_relative_difference_vs8192'] for r in out),'Piola':max(r['grids'][str(k)]['Piola_relative_difference_vs8192'] for r in out),'right_rotation_energy':max(r['grids'][str(k)]['right_rotation_energy_relative_difference'] for r in out)} for k in grids}}
 (P/'ANGULAR-QUADRATURE-REFERENCE-EXTENDED.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['max_errors'],indent=2))
if __name__=='__main__':main()
