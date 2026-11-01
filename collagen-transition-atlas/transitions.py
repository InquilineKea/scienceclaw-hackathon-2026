"""Original mechanism extensions. Dimensionless 2-D hypotheses, not tissue predictions.

Uses the frozen user-owned network baseline. All new constitutive assumptions are
explicit; no AGE chemistry, melting MD, or patient-specific predictions are implied.
"""
import math

import numpy as np
import torch
from core_network import Batch, SystemSpec


def specifications(lat, cases):
    specs=[]
    for c in cases:
        rng=np.random.default_rng(c.get('seed',17));alive=np.ones(lat.Nb,dtype=bool)
        # Interrupt every periodic fibre line; then dilute to the requested z.
        if not c.get('uncut_control'):
            for line in range(lat.n_lines):alive[rng.choice(np.where(lat.line==line)[0])]=False
            target=round(c.get('z',3.4)*lat.N/2)
            available=np.where(alive)[0]
            if target>len(available):raise ValueError('Requested z exceeds finite-fibre lattice capacity')
            alive[rng.choice(available,len(available)-target,replace=False)]=False
        specs.append(SystemSpec(alive,np.ones(lat.Nb),np.ones(lat.Nb),np.full(lat.Nb,c.get('rupture',.20)),
                    np.zeros(lat.N),c.get('kappa',1e-4),0.,0.,meta=c.copy()))
    return specs


class MechanismBatch(Batch):
    def __init__(self,lat,specs,device='cpu'):
        super().__init__(lat,specs,device=device,dtype=torch.float64)
        self.rest=torch.ones((self.B,lat.Nb),device=device,dtype=self.dtype)
        self.radii=None;self.pair_i=None;self.pair_j=None
        self.last_diagnostics=None;self.Flast=self.F0.clone()

    def add_inclusions(self,fractions,seed=123):
        # Disks represent finite inclusions at fibre junctions. This is a
        # centre-connected rope/fibre surrogate, not a cell-resolved tissue.
        rng=np.random.default_rng(seed);relative=rng.uniform(.85,1.15,self.lat.N)
        radii=[]
        for phi in fractions:
            radii.append(relative*np.sqrt(phi*self.lat.area/(math.pi*np.sum(relative**2))))
        self.radii=torch.as_tensor(np.asarray(radii),device=self.device,dtype=self.dtype)
        i,j=np.triu_indices(self.lat.N,1)
        self.pair_i=torch.as_tensor(i,device=self.device);self.pair_j=torch.as_tensor(j,device=self.device)

    def contact_terms(self,x,F):
        delta=x[:,self.pair_j]-x[:,self.pair_i]
        fractional=delta@torch.linalg.inv(F).transpose(1,2)
        box=torch.as_tensor(self.lat.L,device=self.device,dtype=self.dtype)
        image=torch.round(fractional/box)*box
        delta=delta-image@F.transpose(1,2)
        length=torch.linalg.vector_norm(delta,dim=-1).clamp_min(1e-12)
        overlap=(self.radii[:,self.pair_i]+self.radii[:,self.pair_j]-length).clamp_min(0)
        return 50.*(overlap**2).sum(1),(overlap>1e-8).sum(1)

    def energy(self,x,F,per_system=False):
        d=self.bond_vectors(x,F);length=torch.linalg.vector_norm(d,dim=-1).clamp_min(1e-12)
        alive=self.alive.to(self.dtype)
        e=.5*(self.mu*alive*(length-self.rest)**2/self.rest).sum(1)
        din,dout=d[:,self.bend_in],d[:,self.bend_out]
        theta=torch.atan2(din[...,0]*dout[...,1]-din[...,1]*dout[...,0],(din*dout).sum(-1))
        kp=self.kappa*torch.sqrt(self.kb[:,self.bend_in]*self.kb[:,self.bend_out])*alive[:,self.bend_in]*alive[:,self.bend_out]
        e=e+.5*(kp*theta**2).sum(1)
        if self.radii is not None:e=e+self.contact_terms(x,F)[0]
        return e if per_system else e.sum()

    def relax_checked(self,F,tol=3e-8,rounds=5,iters=200):
        x=self.x.detach().clone().requires_grad_(True)
        opt=torch.optim.LBFGS([x],lr=1.,max_iter=iters,history_size=25,tolerance_grad=tol,
                              tolerance_change=1e-18,line_search_fn='strong_wolfe')
        previous=self.energy(x,F,True).detach();settled=torch.zeros(self.B,device=self.device,dtype=torch.bool)
        def closure():
            opt.zero_grad();energy=self.energy(x,F);energy.backward();return energy
        for n in range(rounds):
            opt.step(closure)
            values=self.energy(x,F,True)
            grad=torch.autograd.grad(values.sum(),x)[0]
            residual=grad.abs().flatten(1).max(1).values
            delta=(values.detach()-previous).abs()
            settled=delta<=1e-8*values.detach().abs()+1e-14
            if bool(((residual<tol)&settled).all()):break
            previous=values.detach()
        self.x=x.detach();self.Flast=F.detach().clone()
        self.last_diagnostics={'residual':residual.detach(),'converged':((residual<tol)&settled).detach(),
                               'energyChange':delta.detach(),'rounds':n+1}
        # Small commissioning networks permit an independent, translation-fixed
        # dense Newton correction. Retain strict tolerances; never relabel a
        # failed LBFGS result by merely increasing the acceptance threshold.
        if self.lat.W<=6 and not bool(self.last_diagnostics['converged'].all()):
            self.refine_small(F,tol=tol)
        return self.last_diagnostics

    def refine_small(self,F,tol=3e-8,max_steps=30):
        before=self.last_diagnostics['residual'].clone();counts=torch.zeros(self.B,dtype=torch.long,device=self.device)
        for i in range(self.B):
            if bool(self.last_diagnostics['converged'][i]):continue
            one=MechanismBatch(self.lat,[self.specs[i]],self.device)
            one.x=self.x[i:i+1].clone();one.alive=self.alive[i:i+1].clone();one.rest=self.rest[i:i+1].clone()
            one.mu=self.mu[i:i+1].clone();one.kb=self.kb[i:i+1].clone()
            if self.radii is not None:
                one.radii=self.radii[i:i+1].clone();one.pair_i=self.pair_i;one.pair_j=self.pair_j
            Fi=F[i:i+1];fixed=one.x[:,0:1].clone();q=one.x[:,1:].reshape(-1).detach()
            def coords(v):return torch.cat((fixed,v.reshape(1,-1,2)),dim=1)
            def energy(v):return one.energy(coords(v),Fi)
            previous=float(energy(q));change=float(self.last_diagnostics['energyChange'][i]);accepted=0
            for step in range(max_steps):
                q=q.detach().requires_grad_(True);value=energy(q);g=torch.autograd.grad(value,q)[0]
                full=coords(q).detach().requires_grad_(True)
                residual=torch.autograd.grad(one.energy(full,Fi),full)[0].abs().max()
                if float(residual)<tol and change<=1e-8*abs(float(value))+1e-14:break
                H=torch.autograd.functional.hessian(energy,q).detach();H=(H+H.T)/2
                eigen,Q=torch.linalg.eigh(H)
                floor=max(1e-10,float(eigen.abs().max())*1e-9)
                direction=-(Q@((Q.T@g.detach())/eigen.clamp_min(floor)))
                direction*=min(1.,.1/max(float(direction.abs().max()),1e-30))
                slope=float(g.detach()@direction);start=float(value);alpha=1.;found=False
                for _ in range(24):
                    candidate=q.detach()+alpha*direction;candidate_energy=float(energy(candidate))
                    if math.isfinite(candidate_energy) and candidate_energy<=start+1e-4*alpha*slope:
                        q=candidate;change=abs(candidate_energy-previous);previous=candidate_energy;accepted+=1;found=True;break
                    alpha*=.5
                if not found:break
            full=coords(q.detach()).requires_grad_(True);value=one.energy(full,Fi)
            residual=torch.autograd.grad(value,full)[0].abs().max().detach()
            self.x[i]=full.detach()[0];self.last_diagnostics['residual'][i]=residual
            self.last_diagnostics['energyChange'][i]=change
            self.last_diagnostics['converged'][i]=(residual<tol)&(change<=1e-8*abs(float(value))+1e-14)
            counts[i]=accepted
        self.last_diagnostics['preRefinementResidual']=before
        self.last_diagnostics['newtonAcceptedSteps']=counts

    def advance(self,F,**kwargs):
        self.move_affine(self.Flast,F);return self.relax_checked(F,**kwargs)

    def slip(self,F,mobility,dt,yield_strain=.025):
        """Irreversible positive rest-length growth; fixed-x energy cannot rise.
        Mobility is a hypothesis parameter; it is not a measured AGE concentration.
        """
        before=self.energy(self.x,F,True).detach()
        with torch.no_grad():
            length=torch.linalg.vector_norm(self.bond_vectors(self.x,F),dim=-1)
            target=torch.maximum(self.rest,length/(1+yield_strain))
            rate=torch.as_tensor(mobility,device=self.device,dtype=self.dtype)[:,None]
            self.rest+=self.alive*(target-self.rest)*(1-torch.exp(-rate*dt))
        after=self.energy(self.x,F,True).detach()
        if bool((after>before+1e-10).any()):raise RuntimeError('Plastic update produced energy')
        return before-after

    def break_elastic(self,F):
        length=torch.linalg.vector_norm(self.bond_vectors(self.x,F),dim=-1)
        broken=self.alive&(length/self.rest-1>self.eps_r)
        self.alive&=~broken;return broken.sum(1)


def network_stats(lat,spec):
    alive=spec.alive;adj=[set() for _ in range(lat.N)]
    for i,j in zip(lat.bi[alive],lat.bj[alive]):adj[int(i)].add(int(j));adj[int(j)].add(int(i))
    degree=np.array([len(x) for x in adj]);L=np.diag(degree.astype(float))
    for i,nb in enumerate(adj):
        for j in nb:L[i,j]=-1
    eig=np.linalg.eigvalsh(L);seen=set();sizes=[]
    for i in range(lat.N):
        if i in seen:continue
        stack=[i];seen.add(i);size=0
        while stack:
            j=stack.pop();size+=1
            for k in adj[j]:
                if k not in seen:seen.add(k);stack.append(k)
        sizes.append(size)
    return {'z':float(degree.mean()),'degreeVariance':float(degree.var()),'lambda2':float(eig[1]),
            'zeroModesGraph':int((eig<1e-8).sum()),'largestComponentFraction':max(sizes)/lat.N,
            'spectralRadius':float(eig[-1])}


def row(batch,i,control,stage,extra=None):
    F=batch.Flast;P=batch.stress(F).detach().cpu().numpy();E=batch.energy(batch.x,F,True).detach().cpu().numpy()
    d=batch.last_diagnostics
    result={'control':float(control),'stage':stage,'Pxx':float(P[i,0,0]),'Pxy':float(P[i,0,1]),
            'Pyy':float(P[i,1,1]),'energy':float(E[i]),'residual':float(d['residual'][i]),
            'converged':bool(d['converged'][i]),'aliveBonds':int(batch.alive[i].sum())}
    if extra:result.update(extra)
    return result


def field_roots(a,g,s0=.25,l0=.05,n=4):
    def H(s):return s**n/(1+s**n)
    def f(l):return l0+g*H(s0+a*l)-l
    hi=l0+g+1e-6;grid=np.linspace(0,hi,2001);roots=[]
    for x,y in zip(grid[:-1],grid[1:]):
        if f(x)*f(y)>0:continue
        for _ in range(45):
            m=(x+y)/2
            if f(x)*f(m)<=0:y=m
            else:x=m
        l=(x+y)/2
        if roots and abs(l-roots[-1]['lox'])<1e-6:continue
        s=s0+a*l;gain=a*g*n*s**(n-1)/(1+s**n)**2
        # Three first-order stages, all time constants one:
        # dS=S0+aL-S, dC=H(S)-C, dL=L0+gC-L.
        largest_real=gain**(1/3)-1
        roots.append({'lox':l,'stiffness':s,'contractility':H(s),'loopGain':gain,
                      'largestJacobianRealPart':float(largest_real),'stable':bool(largest_real<0)})
    return roots


def feedback_path(a,g_values,initial):
    s,c,l=initial;out=[];dt=.025
    for g in g_values:
        residual=math.inf
        for k in range(16000):
            h=s**4/(1+s**4);ds=.25+a*l-s;dc=h-c;dl=.05+g*c-l
            s+=dt*ds;c+=dt*dc;l+=dt*dl;residual=max(abs(ds),abs(dc),abs(dl))
            if residual<1e-9:break
        out.append({'g':float(g),'stiffness':float(s),'contractility':float(c),'lox':float(l),'residual':float(residual),'converged':bool(residual<1e-7)})
    return out


def helix_coil(temperatures,hyp,hydration,xlink,device='cpu',sites=81):
    """Exact finite-chain transfer matrix. T is dimensionless; no Celsius mapping.
    Coefficients are explicit sensitivity assumptions, not fitted melting data.
    """
    T=torch.tensor(temperatures,dtype=torch.float64,device=device)
    field=((.8+.25*hyp+.15*hydration+.10*xlink)/T-1.).requires_grad_(True)
    coupling=(.45+.25*xlink)/T
    v=torch.stack([torch.zeros_like(field),field],1)
    for _ in range(sites-1):
        v=torch.stack([torch.logaddexp(v[:,0],v[:,1]-coupling),
                       field+torch.logaddexp(v[:,1],v[:,0]-coupling)],1)
    logZ=torch.logsumexp(v,1)
    fraction=torch.autograd.grad(logZ.sum(),field)[0]/sites
    return fraction.detach().cpu().tolist()
