"""Original vectorized implementation of the archived 3D energy; remote execution only."""
import os,json,math,time,itertools
from pathlib import Path
import numpy as np
import scipy
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.optimize import minimize
from true_hessian_check import check_state
from concurrent.futures import ProcessPoolExecutor,as_completed
P=Path(__file__).resolve().parent
class Model:
 def __init__(self,d):
  self.d=d;self.x=np.array(d['x']);self.e=np.array(d['e']);self.a=np.array(d['a']);self.N=len(self.x);self.D=3*self.N;self.v=np.array(d['v']);self.rest=np.array(d['rest']);self.c0=np.array(d['c0']);self.aw=np.array(d['aw']);self.active=np.array(d['active'],bool);self.ii=self.e[:,0];self.jj=self.e[:,1];self.ai=self.a[:,0];self.aj=self.a[:,1];self.sg=self.a[:,2]
  axes=np.arange(3);self.eids=np.concatenate((3*self.ii[:,None]+axes,3*self.jj[:,None]+axes),axis=1);self.aids=np.concatenate((self.eids[self.ai],self.eids[self.aj]),axis=1)
 def state(self,u,g,plane,jac=False):
  u=u.reshape(-1,3);v=self.v+u[self.jj]-u[self.ii];v[:,0]+=g*self.v[:,plane];length=np.maximum(np.linalg.norm(v,axis=1),1e-15);unit=v/length[:,None];co=np.sum(unit[self.ai]*unit[self.aj],axis=1);em=self.active;am=em[self.ai]&em[self.aj];we=np.sqrt(em/self.rest);wa=np.sqrt(am*self.aw);re=(length-self.rest)*we;ra=(self.sg*co-self.c0)*wa
  eg=np.concatenate((-unit,unit),axis=1)*we[:,None];da=self.sg[:,None]*(unit[self.aj]-co[:,None]*unit[self.ai])/length[self.ai,None]*wa[:,None];db=self.sg[:,None]*(unit[self.ai]-co[:,None]*unit[self.aj])/length[self.aj,None]*wa[:,None];ag=np.concatenate((-da,da,-db,db),axis=1)
  grad=np.zeros(self.D);np.add.at(grad,self.eids.ravel(),(eg*re[:,None]).ravel());np.add.at(grad,self.aids.ravel(),(ag*ra[:,None]).ravel());grad[:3]=0
  E=float((re@re+ra@ra)/2);stress=float(np.sum(re*we*unit[:,0]*self.v[:,plane])+np.sum(ra*(da[:,0]*self.v[self.ai,plane]+db[:,0]*self.v[self.aj,plane])))
  J=None
  if jac:
   ne=len(re);rr=np.concatenate((np.repeat(np.arange(ne),6),np.repeat(ne+np.arange(len(ra)),12)));cc=np.concatenate((self.eids.ravel(),self.aids.ravel()));vv=np.concatenate((eg.ravel(),ag.ravel()));J=coo_matrix((vv,(rr,cc)),shape=(ne+len(ra),self.D)).tocsr()[:,3:]
  return dict(E=E,stress=stress,grad=grad,J=J,lengths=length,forces=np.where(em,(length-self.rest)/self.rest,0))
 def relax(self,u,g,plane,tol=1e-7):
  u=u.copy();it=0
  for it in range(120):
   s=self.state(u,g,plane,True);res=np.max(np.abs(s['grad']))
   if res<=tol:break
   J=s['J'];H=J.T@J;diag=np.maximum(H.diagonal(),1);step=np.r_[np.zeros(3),spsolve(H+diags(diag*1e-10),-s['grad'][3:])];gd=s['grad']@step
   if not np.isfinite(step).all() or gd>=0:break
   f=1;ok=False
   for ls in range(35):
    trial=u+f*step
    if self.state(trial,g,plane)['E']<=s['E']+1e-4*f*gd+1e-20:u=trial;ok=True;break
    f*=.5
   if not ok:break
  s=self.state(u,g,plane);res=float(np.max(np.abs(s['grad'])))
  if res>tol:
   J=self.state(u,g,plane,True)['J'];pre=1/np.sqrt(np.maximum(np.asarray(J.power(2).sum(axis=0)).ravel(),1));start=u[3:]/pre
   def fun(q):
    ss=self.state(np.r_[np.zeros(3),q*pre],g,plane);return ss['E'],ss['grad'][3:]*pre
   opt=minimize(fun,start,jac=True,method='L-BFGS-B',options={'gtol':1e-12,'ftol':1e-16,'maxiter':5000,'maxls':50,'maxcor':30});trial=np.r_[np.zeros(3),opt.x*pre];ss=self.state(trial,g,plane)
   if np.max(np.abs(ss['grad']))<res and ss['E']<=s['E']+1e-14:u=trial;s=ss;res=float(np.max(np.abs(ss['grad'])))
  return u,s,res,res<=tol and math.isfinite(s['E'])
def simulate(task):
 d,plane,threshold,steps=task;name=f"s{steps}-seed{d['seed']}-p{plane}-t{threshold}-{d['pattern']}-{d['density']}";out=P/'results'/f'{name}.json';m=Model(d);u=np.zeros(m.D);n0=int(m.active.sum());frames=[];W=0.;deleted=0.;relaxed=0.;laststress=0.;lastg=0.;started=time.time();peak_record=None;peak_state=None;initial_state=None;last_state=None
 for k in range(steps+1):
  g=.5*k/steps;u,s,res,ok=m.relax(u,g,plane);pre=s['stress'];av=0
  if ok and (peak_record is None or pre>peak_record['stress']):peak_record={'gamma':g,'stress':pre};peak_state={'gamma':g,'u':u.tolist(),'active':m.active.tolist(),'stage':'pre-avalanche'}
  if ok and k==1:initial_state={'gamma':g,'u':u.tolist(),'active':m.active.tolist()}
  if ok:
   for event in range(n0+1):
    fail=m.active&(s['lengths']/m.rest-1>threshold)
    if not fail.any():break
    old=s['E'];m.active[fail]=False;after=m.state(u,g,plane)['E'];deleted+=old-after;av+=int(fail.sum());u,s,res,ok=m.relax(u,g,plane);relaxed+=after-s['E']
    if not ok:break
  if not ok:frames.append(dict(gamma=g,accepted=False,residual=res));break
  W+=(g-lastg)*(pre+laststress)/2;lastg=g;laststress=s['stress'];f=dict(gamma=g,accepted=True,stress=s['stress'],preStress=pre,energy=s['E'],damage=1-int(m.active.sum())/n0,avalanche=av,removedEnergy=deleted,relaxEnergy=relaxed,work=W,residual=res)
  if d['seed']==29 and plane==1 and k%max(1,steps//40)==0:f.update(u=u.tolist(),forces=s['forces'].tolist(),active=m.active.tolist())
  last_state={'gamma':g,'u':u.tolist(),'active':m.active.tolist()}
  if s['stress']>peak_record['stress']:peak_record={'gamma':g,'stress':s['stress']};peak_state=dict(last_state,stage='post-avalanche')
  f['relativeEnergyError']=abs(W-s['E']-deleted-relaxed)/max(abs(W),1e-12);frames.append(f)
  if k%20==0:(P/'results'/f'{name}.partial.json').write_text(json.dumps(dict(seed=d['seed'],plane=plane,threshold=threshold,steps=steps,pattern=d['pattern'],density=d['density'],frames=frames,status='partial')))
 good=[f for f in frames if f['accepted']];peak=max(good,key=lambda f:max(f['stress'],f['preStress'])) if good else None
 trajectory_complete=bool(frames and all(f['accepted'] for f in frames) and lastg>=.5)
 peak_resolved=bool(trajectory_complete and peak and peak['gamma']<lastg and laststress<.8*max(peak['stress'],peak['preStress']) and len([f for f in good if f['gamma']>peak['gamma']])>=3)
 result=dict(peakResolved=peak_resolved,peakRightCensored=bool(peak and peak['gamma']>=lastg),trajectoryComplete=trajectory_complete,workThroughLastAccepted=good[-1]['work'] if good else None,workThroughCap=good[-1]['work'] if trajectory_complete else None,terminalRelativeEnergyError=good[-1]['relativeEnergyError'] if good else None,initial_state=initial_state,peak_state=peak_state,terminal_state=last_state,seed=d['seed'],plane=plane,threshold=threshold,steps=steps,pattern=d['pattern'],density=d['density'],nodes=m.N,edges=n0,z=d['z'],lock_count=len(d['locked']),locked=d['locked'],lock_spread=d['lock_spread'],frames=frames,status='converged' if all(f['accepted'] for f in frames) else 'unresolved',peakStress=max(peak['stress'],peak['preStress']) if peak else None,peakGamma=peak['gamma'] if peak else None,workToPeak=peak['work'] if peak_resolved else None,last=good[-1] if good else None,seconds=time.time()-started,maxResidual=max(f['residual'] for f in good) if good else None)
 if steps==200 and result['status']=='converged':
  stability=[]
  for label in ['initial_state','peak_state','terminal_state']:
   snap=result[label]
   if snap is None:continue
   m.active=np.array(snap['active'],bool)
   stability.append(check_state(m,np.array(snap['u']),snap['gamma'],plane,label))
  result['selected_state_stability']=stability
 out.write_text(json.dumps(result,allow_nan=False));return name,result['status'],result['last']['damage'] if good else None,result['seconds']
def checks(models):
 records=[];arch=json.loads((P/'checks.json').read_text())
 for d in models:
  if d['pattern']!='baseline':continue
  m=Model(d);u=np.sin(np.arange(m.D)*1.2)*1e-4;u[:3]=0;di=np.cos(np.arange(m.D)*.7)/math.sqrt(m.D);di[:3]=0;s=m.state(u,.03,1);eps=1e-6;fd=(m.state(u+eps*di,.03,1)['E']-m.state(u-eps*di,.03,1)['E'])/(2*eps);ge=abs(fd-s['grad']@di);se=abs((m.state(u,.03+eps,1)['E']-m.state(u,.03-eps,1)['E'])/(2*eps)-s['stress']);uu,ss,res,ok=m.relax(np.zeros(m.D),.001,1,tol=1e-9);ref=next(c for c in arch['calibration'] if c['seed']==d['seed'])['planes'][0]['values'][1]['energy'];error=abs(ss['E']-ref)/ref
  records.append(dict(seed=d['seed'],gradientError=ge,stressError=se,smallStrainEnergyRelativeDifference=error,residual=res,accepted=bool(ok)));assert ge<1e-7 and se<1e-7 and error<1e-3 and ok
 (P/'remote-checks.json').write_text(json.dumps(dict(records=records,numpy=np.__version__,scipy=scipy.__version__),indent=2));print('CHECKS PASS',flush=True)
if __name__=='__main__':
 (P/'results').mkdir(exist_ok=True);models=json.loads((P/'models.json').read_text());checks(models)
 # Pair both resolutions; round-robin seeds gives broad coverage at a bounded timeout.
 tasks=[]
 for plane,threshold,conf in itertools.product([1,2],[.2,.1],[('baseline',0),('clustered',.15),('distributed',.15),('clustered',.3),('distributed',.3)]):
  for seed in [29,30,31,32]:
   d=next(d for d in models if d['seed']==seed and (d['pattern'],d['density'])==conf)
   for steps in [100,200]:tasks.append((d,plane,threshold,steps))
 with ProcessPoolExecutor(max_workers=4) as pool:
  for i,future in enumerate(as_completed([pool.submit(simulate,t) for t in tasks])):print(i+1,'/160',future.result(),flush=True)
 print('COMPLETE',flush=True)
