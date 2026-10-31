"""Original stdlib constitutive reference; no production solver/package import.

Controlled local probes only: no experimental displacement scoring or fitting.
"""
import json,math,itertools
from pathlib import Path
P=Path(__file__).parent
HARDENING=.05;TENSION_ONSET=.04;TENSION_SCALE=.05

def w(e,d0):
 if e<0 and d0 is not None:
  x=e/d0;ex=math.exp(x);return d0*d0*(math.expm1(x)-x),d0*math.expm1(x),ex
 if e<=TENSION_ONSET:return .5*e*e,e,1.
 x=e-TENSION_ONSET;z=x/TENSION_SCALE
 return .5*TENSION_ONSET**2+TENSION_ONSET*x+TENSION_SCALE**2*(math.expm1(z)-z),TENSION_ONSET+TENSION_SCALE*math.expm1(z),math.exp(z)

def response(ef,prior,d0,yield_force):
 if yield_force is None:
  energy,T,C=w(ef,d0);return dict(s=0.,stored=energy,dissipation=0.,incremental=energy,T=T,C=C,active=False,kkt=0.)
 trial=ef-prior;ww,T,C=w(trial,d0)
 if T-HARDENING*prior<=yield_force+1e-14:
  s=prior;active=False
 else:
  # Solve for elastic extension, not for an arbitrary Newton-dependent slip.
  lo=0.;hi=trial;target=HARDENING*ef+yield_force
  for _ in range(100):
   mid=(lo+hi)/2
   if w(mid,d0)[1]+HARDENING*mid>target:hi=mid
   else:lo=mid
  ee=(lo+hi)/2;s=ef-ee;active=True
 ww,T,C=w(ef-s,d0);stored=ww+.5*HARDENING*s*s;diss=yield_force*(s-prior)
 return dict(s=s,stored=stored,dissipation=diss,incremental=stored+diss,T=T,C=C*HARDENING/(C+HARDENING) if active else C,active=active,kkt=T-HARDENING*s-yield_force)


def directions():
 q=[]
 for i in range(3):
  for sign in [-1,1]:n=[0.,0.,0.];n[i]=sign;q.append((n,1/21))
 for zero in range(3):
  axes=[i for i in range(3) if i!=zero]
  for a,b in itertools.product([-1,1],repeat=2):n=[0.,0.,0.];n[axes[0]]=a/math.sqrt(2);n[axes[1]]=b/math.sqrt(2);q.append((n,4/105))
 for signs in itertools.product([-1,1],repeat=3):q.append(([a/math.sqrt(3) for a in signs],9/280))
 return q
Q=directions()
def matmul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mv(A,x):return [sum(row[j]*x[j] for j in range(3)) for row in A]
def flat(A):return [x for row in A for x in row]
def norm(a):return math.sqrt(sum(x*x for x in a))
def field(F,d0,Y,prior=None,delta=None):
 prior=[0.]*len(Q) if prior is None else prior;E=0.;Pi=[[0.]*3 for _ in range(3)];Hv=[[0.]*3 for _ in range(3)];slips=[]
 for k,(n,weight) in enumerate(Q):
  v=mv(F,n);length=norm(v);a=[x/length for x in v];r=response(length-1,prior[k],d0,Y);weight*=15;E+=weight*r['incremental'];slips.append(r['s'])
  for i in range(3):
   for j in range(3):Pi[i][j]+=weight*r['T']*a[i]*n[j]
  if delta is not None:
   dv=mv(delta,n);dl=sum(x*y for x,y in zip(a,dv));dforce=[r['C']*dl*a[i]+r['T']/length*(dv[i]-a[i]*dl) for i in range(3)]
   for i in range(3):
    for j in range(3):Hv[i][j]+=weight*dforce[i]*n[j]
 return E,Pi,Hv,slips


def local_checks():
 rows=[]
 for d0,Y in itertools.product([None,.0025,.01,.04],[None,.01,.04]):
  worst_grad=0.;worst_tangent=0.;worst_kkt=0.;hold=0.
  for ef,prior in itertools.product([-.1,-.015,-.001,.007,.023,.057,.103,.217],[0.,.006]):
   if Y is None and prior:continue
   r=response(ef,prior,d0,Y);eps=1e-7;rp=response(ef+eps,prior,d0,Y);rm=response(ef-eps,prior,d0,Y);worst_grad=max(worst_grad,abs((rp['incremental']-rm['incremental'])/(2*eps)-r['T']));worst_tangent=max(worst_tangent,abs((rp['T']-rm['T'])/(2*eps)-r['C']));assert r['s']>=prior-1e-12 or Y is None;assert r['dissipation']>=-1e-12
   if r['active']:worst_kkt=max(worst_kkt,abs(r['kkt']))
   else:assert r['kkt']<=1e-12
   if Y is not None:hold=max(hold,abs(response(ef,r['s'],d0,Y)['s']-r['s']))
  assert worst_grad<1e-7 and worst_tangent<1e-6 and worst_kkt<1e-12 and hold<1e-12
  rows.append(dict(d0=d0,yield_force=Y,max_incremental_gradient_error=worst_grad,max_condensed_tangent_error=worst_tangent,max_active_kkt_error=worst_kkt,hold_slip_increment=hold))
 return rows


def finite_F_checks():
 F=[[1.06,.081,.013],[.007,.963,.031],[.011,.002,1.021]];D=[[math.sin(i*3+j+.3)*.3 for j in range(3)] for i in range(3)];angle=.37;R=[[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]];rows=[]
 for d0,Y in itertools.product([None,.0025,.01,.04],[None,.01,.04]):
  E,T,Hv,_=field(F,d0,Y,delta=D);eps=1e-6;plus=[[F[i][j]+eps*D[i][j] for j in range(3)] for i in range(3)];minus=[[F[i][j]-eps*D[i][j] for j in range(3)] for i in range(3)];Ep,Tp,_,_=field(plus,d0,Y);Em,Tm,_,_=field(minus,d0,Y);grad=abs((Ep-Em)/(2*eps)-sum(a*b for a,b in zip(flat(T),flat(D))));fd=[(a-b)/(2*eps) for a,b in zip(flat(Tp),flat(Tm))];hvp=norm([a-b for a,b in zip(fd,flat(Hv))])/max(norm(fd),norm(flat(Hv)),1e-12);rotE,rotT,_,_=field(matmul(R,F),d0,Y);expectedT=matmul(R,T);objE=abs(rotE-E);objP=norm([a-b for a,b in zip(flat(rotT),flat(expectedT))]);assert grad<1e-7 and hvp<1e-5 and objE<1e-12 and objP<1e-11;rows.append(dict(d0=d0,yield_force=Y,energy_direction_error=grad,relative_Hvp_error=hvp,objectivity_energy_error=objE,objectivity_Piola_error=objP))
 # Right-rotation probes test material quadrature isotropy, not frame objectivity.
 angular=[]
 for d0 in [None,.0025,.01,.04]:
  E,_,_,_=field(F,d0,None);ER,_,_,_=field(matmul(F,R),d0,None);angular.append(dict(d0=d0,right_rotation_energy_relative_difference=abs(ER-E)/max(abs(E),abs(ER),1e-12)))
 return rows,angular


def cyclic_work():
 out=[]
 for d0,Y in itertools.product([None,.0025,.01,.04],[.01,.04]):
  errors=[]
  for steps in [100,200,400]:
   path=[.12*i/steps for i in range(steps+1)]+[.12]*(5)+[.12*(1-i/steps) for i in range(1,steps+1)]+[.2*i/steps for i in range(1,steps+1)];s=0.;last_e=0.;last_T=0.;work=0.;diss=0.;last=None
   for ef in path:
    r=response(ef,s,d0,Y);work+=(ef-last_e)*(r['T']+last_T)/2;diss+=r['dissipation'];s=r['s'];last_e=ef;last_T=r['T'];last=r
   error=abs(work-last['stored']-diss)/max(abs(work),1e-12);errors.append(dict(steps_per_leg=steps,relative_work_energy_dissipation_error=error,terminal_slip=s,total_dissipation=diss))
  assert errors[-1]['relative_work_energy_dissipation_error']<2e-4
  out.append(dict(d0=d0,yield_force=Y,resolutions=errors))
 return out


def main():
 local=local_checks();finite,angular=finite_F_checks();work=cyclic_work();moment_error=max(abs(sum(w*n[i]*n[j]*n[k]*n[l] for n,w in Q)-((int(i==j)*int(k==l)+int(i==k)*int(j==l)+int(i==l)*int(j==k))/15)) for i,j,k,l in itertools.product(range(3),repeat=4));assert moment_error<1e-14
 report=dict(scope='Controlled independent stdlib material reference; not production-code or experimental validation',H=HARDENING,tension_onset=TENSION_ONSET,tension_scale=TENSION_SCALE,directions=26,quadrature_fourth_moment_error=moment_error,local_return_checks=local,finite_F_checks=finite,angular_isotropy_diagnostic=angular,cyclic_work_checks=work);(P/'INDEPENDENT-MATERIAL-REFERENCE.json').write_text(json.dumps(report,indent=2));print(json.dumps({'local_cases':len(local),'finite_F_cases':len(finite),'cyclic_cases':len(work),'fourth_moment_error':moment_error,'angular_isotropy_diagnostic':angular},indent=2))
if __name__=='__main__':main()
