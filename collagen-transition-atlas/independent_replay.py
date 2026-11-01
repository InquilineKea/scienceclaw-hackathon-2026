"""Check saved states with scalar math, without importing the numerical worker.

Energy is checked for every stored frame in six uniform-spring suites. Finite
force differences are checked at the last converged frame of each case. This
corroborates saved residuals but does not prove uniqueness or stability.
"""
import argparse
import json
import math
from pathlib import Path


def matrix(name,c,p):
 q=p['control'];stage=p['stage']
 if name=='inclusions':return [[1-q,0.],[0.,1.]]
 if name=='sliding-failure':return [[1+q,0.],[0.,1.]]
 if name=='targeted-damage':return [[1.12,0.],[0.,1.]]
 if name=='plastic-memory-matrix':q*=c['parameters']['amplitude']
 if name=='sliding-memory' and stage=='hold':q=.5
 return [[1.,q],[0.,1.]]

def make_energy(lat,c,p,F):
 edges=lat['edges'];shifts=lat['imageShifts'];alive=p['frame']['alive'];rest=p['frame']['restLength'];kappa=c['parameters']['kappa'];n=len(lat['nodes'])
 incoming={(b,k%3):k for k,(a,b) in enumerate(edges)}
 bends=[(incoming[(a,k)],3*a+k) for a in range(n) for k in range(3)]
 rad=c.get('radii');box=[lat['W'],lat['W']*math.sqrt(3)/2]
 def energy(x):
  d=[(x[b][0]-x[a][0]+F[0][0]*s[0]+F[0][1]*s[1],x[b][1]-x[a][1]+F[1][0]*s[0]+F[1][1]*s[1]) for (a,b),s in zip(edges,shifts)]
  terms=[.5*(max(math.hypot(*v),1e-12)-r)**2/r for v,r,on in zip(d,rest,alive) if on]
  for i,j in bends:
   if alive[i] and alive[j]:
    u,v=d[i],d[j];theta=math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1]);terms.append(.5*kappa*theta*theta)
  if rad is not None:
   det=F[0][0]*F[1][1]-F[0][1]*F[1][0]
   for a in range(n):
    for b in range(a+1,n):
     dx=x[b][0]-x[a][0];dy=x[b][1]-x[a][1]
     fx=(F[1][1]*dx-F[0][1]*dy)/det;fy=(-F[1][0]*dx+F[0][0]*dy)/det
     ix=round(fx/box[0])*box[0];iy=round(fy/box[1])*box[1]
     length=max(math.hypot(dx-F[0][0]*ix-F[0][1]*iy,dy-F[1][0]*ix-F[1][1]*iy),1e-12)
     terms.append(50*max(0.,rad[a]+rad[b]-length)**2)
  return math.fsum(terms)
 return energy

def audit(run):
 rows=[];energy_differences=[];frames=0
 for name in ['rigidity','sliding-memory','plastic-memory-matrix','sliding-failure','targeted-damage','inclusions']:
  data=json.loads((Path(run)/'data'/(name+'.json')).read_text());groups=data if isinstance(data,list) else [data]
  for group in groups:
   for c in group['cases']:
    points=[p for p in c['curve'] if 'frame' in p]
    for p in points:
     e=make_energy(group['lattice'],c,p,matrix(name,c,p))(p['frame']['coordinates']);energy_differences.append(abs(e-p['energy']));frames+=1
    eligible=[p for p in points if p['converged']]
    if not eligible:continue
    p=eligible[-1];x=[v[:] for v in p['frame']['coordinates']];energy=make_energy(group['lattice'],c,p,matrix(name,c,p));maxima=[]
    for h in [1e-5,5e-6]:
     maximum=0.
     for v in x:
      for axis in range(2):
       old=v[axis];v[axis]=old+h;plus=energy(x);v[axis]=old-h;minus=energy(x);v[axis]=old
       maximum=max(maximum,abs((plus-minus)/(2*h)))
     maxima.append(maximum)
    rows.append({'suite':name,'parameters':c['parameters'],'stage':p['stage'],'control':p['control'],'savedResidual':p['residual'],'finiteDifferenceSteps':[1e-5,5e-6],'finiteDifferenceMaxResiduals':maxima})
 return {'method':'Independent scalar-math energy evaluation and central finite differences on frozen saved coordinates; no NumPy/PyTorch execution','energyFramesChecked':frames,'maximumAbsoluteEnergyDifference':max(energy_differences),'forceCasesChecked':len(rows),'maximumFiniteDifferenceResidualAtSmallerStep':max(r['finiteDifferenceMaxResiduals'][-1] for r in rows),'cases':rows,'limitations':['Only stored frames in the six uniform-spring suites were replayed; stiff-bond placement has no saved coordinates.','Finite differences have truncation and cancellation error, especially at disk contacts; they do not replace the original force/energy acceptance test.','The last recorded converged frame is a spot check of the force, not validation of an earlier invalid history.','No equilibrium was recomputed and no raw state or convergence flag was changed.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('output');a=p.parse_args();r=audit(a.run);Path(a.output).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['cases','limitations']},indent=2))
