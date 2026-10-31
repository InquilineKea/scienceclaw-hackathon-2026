"""Export reduced-unit elastic networks, preserving heterogeneous coefficients.

Commissioned scope is an orientation-preserving harmonic network with affine
embedding and phenomenological Langevin drag. No contact, rupture, chemical
reaction or calibrated solvent model is supplied. See the JSON sidecar.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING
import numpy as np
if TYPE_CHECKING:
    from .network import Lattice, SystemSpec


def _types(items):
    values=sorted(set(items));return {v:i+1 for i,v in enumerate(values)}


def export(spec: SystemSpec, lat: Lattice, out_dir: Path, name="network", gamma0=.02,
           period=200., cycles=5, damp=1., temp=0., timestep=.01, output_every=10):
    """Write a conservative reference plus a distinct, explicitly damped dynamics.

    Exact angular forces require the single-rank CPU library driver below.
    The commissioned domain preserves ordered junction orientation; both
    the callback and validate_frame reject inversions.
    """
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
        raise ValueError('name must be a simple filename stem')
    if not (0<abs(gamma0)<.25 and period>0 and cycles>=2 and damp>0 and temp>=0 and timestep>0):
        raise ValueError('invalid small-amplitude protocol')
    if not isinstance(output_every,int) or output_every<1 or timestep*output_every>period/20:
        raise ValueError('at least20 samples per cycle required')
    steps=cycles*period/timestep
    if abs(steps-round(steps))>1e-7:raise ValueError('duration must be an integer number of steps')
    scale=1+float(spec.prestrain)
    if not np.isfinite(scale) or scale<=0:raise ValueError('invalid prestrain')
    alive=np.asarray(spec.alive,dtype=bool);mu=np.asarray(spec.mu,dtype=float);kb=np.asarray(spec.kappa_b,dtype=float);kx=np.asarray(spec.rigid_node,dtype=float)
    if any(not np.all(np.isfinite(v)) or np.any(v<0) for v in [mu,kb,kx,np.array([spec.kappa,spec.mu_el,spec.k_gag])]):
        raise ValueError('coefficients must be finite and nonnegative')
    if alive.shape!=(lat.Nb,) or mu.shape!=alive.shape or kb.shape!=alive.shape or kx.shape!=(lat.N,):raise ValueError('coefficient shape mismatch')
    X=np.asarray(lat.X,dtype=float)*scale;L=np.asarray(lat.L,dtype=float)*scale
    # One combined bond preserves mu*alive+mu_el without duplicate topology.
    effective=mu*alive+float(spec.mu_el);bs=[(int(lat.bi[b])+1,int(lat.bj[b])+1,float(effective[b])) for b in range(lat.Nb) if effective[b]>0]
    bt=_types([v for _,_,v in bs]);angles=[]
    for bi,bo,n in zip(lat.bend_in,lat.bend_out,lat.bend_node):
        if alive[bi] and alive[bo]:
            k=float(spec.kappa)*math.sqrt(float(kb[bi])*float(kb[bo]))
            if k:angles.append((int(lat.bi[bi])+1,int(n)+1,int(lat.bj[bo])+1,(180.,k)))
    for u,v,su,sv,n in zip(lat.ang_u,lat.ang_v,lat.ang_su,lat.ang_sv,lat.ang_node):
        if alive[u] and alive[v] and kx[n]>0:
            i=lat.bj[u] if su>0 else lat.bi[u];j=lat.bj[v] if sv>0 else lat.bi[v]
            angles.append((int(i)+1,int(n)+1,int(j)+1,(60.,float(kx[n]))))
    at=_types([v for *_,v in angles]);nbt=max(1,len(bt));nat=max(1,len(at))
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    lines=[f'LAMMPS reduced elastic network: {name}', '',f'{lat.N} atoms',f'{len(bs)} bonds',f'{len(angles)} angles','','1 atom types',f'{nbt} bond types',f'{nat} angle types','',f'0 {L[0]:.17g} xlo xhi',f'0 {L[1]:.17g} ylo yhi','-0.5 0.5 zlo zhi','0 0 0 xy xz yz','','Masses','','1 1.0','','Atoms # molecular','']
    lines += [f'{i+1} 1 1 {x:.17g} {y:.17g} 0.0' for i,(x,y) in enumerate(X)]
    lines += ['','Bonds','']+[f'{i+1} {bt[k]} {a} {b}' for i,(a,b,k) in enumerate(bs)]
    lines += ['','Angles','']+[f'{i+1} {at[k]} {a} {n} {c}' for i,(a,n,c,k) in enumerate(angles)]
    (out_dir/f'{name}.data').write_text('\n'.join(lines)+'\n')
    coeffs=[f'bond_coeff {t} {k/2:.17g} 1.0' for k,t in bt.items()] or ['bond_coeff 1 0 1.0']
    coeffs += [f'angle_coeff {t} 0.0 {theta:.17g}' for (theta,k),t in at.items()] or ['angle_coeff 1 0 180.0']
    # Stored reference coordinates are immutable; target follows the current box shear.
    base=f'''units lj
dimension 2
boundary p p p
atom_style molecular
read_data {name}.data
bond_style harmonic
angle_style harmonic
{chr(10).join(coeffs)}
pair_style zero 1.0
pair_coeff * *
neighbor 0.3 bin
neigh_modify every 1 delay 0 check yes
comm_modify cutoff 3.0
fix planar all enforce2d
fix reference all store/state 0 xu yu
compute unwrapped all property/atom xu yu
variable gamma equal xy/ly
variable dx atom "c_unwrapped[1]-(f_reference[1]+v_gamma*f_reference[2])"
variable dy atom "c_unwrapped[2]-f_reference[2]"
variable fxg atom "-{spec.k_gag:.17g}*v_dx"
variable fyg atom "-{spec.k_gag:.17g}*v_dy"
variable eg atom "0.5*{spec.k_gag:.17g}*(v_dx*v_dx+v_dy*v_dy)"
variable sg atom "{spec.k_gag:.17g}*v_dx*v_dy"
fix gag all addforce v_fxg v_fyg 0.0 energy v_eg
fix_modify gag energy yes virial no
compute gagxy all reduce sum v_sg
fix anglelaw all external pf/callback 1 1
fix_modify anglelaw energy yes virial yes
compute p all pressure NULL bond angle fix
variable sxy equal "-c_p[4]+c_gagxy/vol"
thermo_style custom step time pe ebond eangle f_gag v_gamma v_sxy
thermo_modify norm no
'''
    (out_dir/f'{name}.base.in').write_text(base)
    deck=f'''# Reduced elastic network; no contact, damage or chemical kinetics.
# Run using python -m oxt.lammps_export, not bare lmp: exact angular callback required.
# Validate signed junction orientations in every saved frame before fitting.
include {name}.base.in
min_style fire
minimize 0 1e-10 20000 200000
reset_timestep 0
velocity all create {max(temp,1e-30):.17g} 4928 dist gaussian
fix integrate all nve
fix shear all deform 1 xy wiggle {gamma0*L[1]:.17g} {period:.17g} remap v flip no
compute peculiar all temp/deform
fix drag all langevin {temp:.17g} {temp:.17g} {damp:.17g} 48279 tally yes zero yes
fix_modify drag temp peculiar
variable clock equal time
fix sample all print {output_every} "$(time:%.17g) $(v_gamma:%.17g) $(v_sxy:%.17g) $(pe:%.17g) $(f_gag:%.17g) $(f_drag:%.17g)" file {name}_stress.txt screen no title "time gamma sigma_config potential tether_energy thermostat_exchange"
dump trajectory all custom {output_every} {name}.dump id xu yu fx fy
thermo {max(1,output_every*10)}
timestep {timestep:.17g}
run {int(round(steps))}
'''
    (out_dir/f'{name}.in').write_text(deck)
    meta=dict(schema=2,scope='Reduced elastic model, orientation-preserving signed-junction sector only; no contact/rupture/chemical kinetics; Langevin damping uncalibrated.',embedding='affine x_ref=x0+(xy/ly)*y0; y_ref=y0; references captured before minimization',stress='Conservative affine virtual-work stress: bond/angle virial plus k*sum(dx*dy)/volume; excludes kinetic and thermostat stress.',prestrain=float(spec.prestrain),reference_positions=X.tolist(),box=L.tolist(),angular_backend='exact single-rank CPU callback; native angle coefficients intentionally zero',angle_terms=[dict(nodes=[a-1,n-1,c-1],theta0_degrees=theta,stiffness=k) for a,n,c,(theta,k) in angles],bond_types=[dict(type=t,stiffness=k) for k,t in bt.items()],angle_types=[dict(type=t,stiffness=k,theta0_degrees=theta) for (theta,k),t in at.items()],period=period,timestep=timestep,output_every=output_every,required_postcheck='validate_frame for every saved frame; no accepted inversion',thermal_protocol='remap v + temp/deform bias removal; profile consistency must be checked for each application')
    (out_dir/f'{name}.meta.json').write_text(json.dumps(meta,indent=2)+'\n')
    return out_dir/f'{name}.in'


def validate_frame(spec,lat,positions,F):
    """Reject branches where unsigned LAMMPS angles differ from signed source law."""
    x=np.asarray(positions);F=np.asarray(F)
    if x.shape!=(lat.N,2) or F.shape!=(2,2) or not np.all(np.isfinite(x)):raise ValueError('invalid frame')
    d=x[lat.bj]-x[lat.bi]+np.asarray(lat.shift)@F.T
    for u,v,su,sv,n in zip(lat.ang_u,lat.ang_v,lat.ang_su,lat.ang_sv,lat.ang_node):
        if spec.alive[u] and spec.alive[v] and spec.rigid_node[n]>0:
            a,b=d[u]*su,d[v]*sv
            if a[0]*b[1]-a[1]*b[0]<=0:raise ValueError('signed junction orientation inverted; harmonic export invalid')
    # Guard against ambiguous minimum-image bond selection as well.
    fractional=d@np.linalg.inv(F@np.diag(lat.L)).T
    if np.any(np.abs(fractional)>=.5):raise ValueError('bond image outside commissioned minimum-image sector')
    return True


def fit_viscoelastic(stress_file: Path,period:float,*,sample_interval=None,discard_cycles=1):
    """Fit a measured-time fundamental, not a derivative per sample index.

    New files: time,gamma,sigma[,diagnostics]. Legacy two-column files require
    explicit sample_interval. G_loss multiplies gamma_dot/omega. Residuals
    describe non-fundamental response; they do not validate physical units.
    """
    if period<=0 or discard_cycles<0:raise ValueError('invalid period/window')
    d=np.loadtxt(stress_file,comments='#',skiprows=1,ndmin=2)
    if d.shape[1]==2:
        if sample_interval is None or sample_interval<=0:raise ValueError('legacy data require explicit sample_interval')
        t=np.arange(len(d))*sample_interval;g,s=d.T
    elif d.shape[1]>=3:t,g,s=d[:,:3].T
    else:raise ValueError('expected time,gamma,stress columns')
    if not np.all(np.isfinite(d)) or len(t)<12 or np.any(np.diff(t)<=0):raise ValueError('invalid time series')
    start=t[0]+discard_cycles*period;ncycles=int(np.floor((t[-1]-start)/period+1e-9))
    if ncycles<1:raise ValueError('need a complete retained cycle')
    keep=(t>=start-1e-9)&(t<=start+ncycles*period+1e-9);t,g,s=t[keep],g[keep],s[keep]
    if len(t)<12 or np.max(np.diff(t))>period/8:raise ValueError('insufficient phase sampling')
    w=2*math.pi/period;sn,cs=np.sin(w*t),np.cos(w*t);B=np.column_stack([sn,cs,np.ones(len(t))]);coef,_,rank,_=np.linalg.lstsq(B,g,rcond=None)
    if rank<3 or np.hypot(coef[0],coef[1])<1e-12:raise ValueError('no resolved sinusoidal strain')
    g1=coef[0]*sn+coef[1]*cs;q=coef[0]*cs-coef[1]*sn
    strain_res=float(np.sqrt(np.mean((g-B@coef)**2))/np.hypot(coef[0],coef[1]))
    if strain_res>1e-3:raise ValueError('strain is not a single-frequency sinusoid')
    A=np.column_stack([g1,q,np.ones(len(t))]);c,_,rank,_=np.linalg.lstsq(A,s,rcond=None)
    if rank<3:raise ValueError('unresolved response')
    return dict(G_storage=float(c[0]),G_loss=float(c[1]),tan_delta=float(c[1]/c[0]) if c[0] else None,stress_offset=float(c[2]),stress_residual_rms=float(np.sqrt(np.mean((s-A@c)**2))),strain_relative_residual=strain_res,retained_cycles=ncycles,retained_samples=len(t),time_start=float(t[0]),time_end=float(t[-1]))


class AngularController:
    """Exact signed-angle energy, force and virial; one MPI rank, CPU reference.

    Native harmonic-angle force regularization near straight hinges is not the
    derivative of the source atan2 energy. All angular contributions are supplied
    here while native angular coefficients are zero. This is not a GPU kernel.
    """
    def __init__(self,lmp,meta):
        self.lmp=lmp;self.error=None;self.N=len(meta['reference_positions']);terms=meta['angle_terms']
        self.nodes=np.array([x['nodes'] for x in terms],dtype=int).reshape(-1,3)
        self.k=np.array([x['stiffness'] for x in terms]);self.bend=np.array([x['theta0_degrees']==180 for x in terms]);self.sign=np.where(self.bend,-1.,1.);self.rest=np.where(self.bend,0.,math.pi/3)
        lmp.set_fix_external_callback('anglelaw',self.callback)

    def callback(self,caller,step,nlocal,tags,x,fexternal):
        try:
            if nlocal!=self.N:raise ValueError('exact angular adapter requires one MPI rank')
            fexternal[:]=0.;ids=np.asarray(tags,dtype=int)-1;inverse=np.empty(self.N,int);inverse[ids]=np.arange(nlocal)
            xx=np.asarray(x)[inverse,:2];lo,hi,xy,yz,xz,periodic,changed=self.lmp.extract_box();H=np.array([[hi[0]-lo[0],xy],[0.,hi[1]-lo[1]]]);inv=np.linalg.inv(H)
            ia,ic,ib=self.nodes.T;a=xx[ia]-xx[ic];b=xx[ib]-xx[ic]
            af=a@inv.T;bf=b@inv.T;a=(af-np.rint(af))@H.T;b=(bf-np.rint(bf))@H.T
            u=a*self.sign[:,None];v=b;aa=np.sum(u*u,axis=1);bb=np.sum(v*v,axis=1)
            if np.any(aa<1e-16) or np.any(bb<1e-16):raise ValueError('collapsed angular arm')
            theta=np.arctan2(u[:,0]*v[:,1]-u[:,1]*v[:,0],np.sum(u*v,axis=1))
            if np.any((~self.bend)&(theta<=0)):raise ValueError('signed junction orientation outside commissioned sector')
            delta=theta-self.rest
            ga=(self.k*delta/aa)[:,None]*np.column_stack([u[:,1],-u[:,0]])*self.sign[:,None]
            gb=(self.k*delta/bb)[:,None]*np.column_stack([-v[:,1],v[:,0]])
            ff=np.zeros((self.N,2));np.add.at(ff,ia,-ga);np.add.at(ff,ib,-gb);np.add.at(ff,ic,ga+gb)
            fexternal[:,:2]=ff[ids];energy=.5*float(np.sum(self.k*delta**2))
            tensor=-np.einsum('ni,nj->ij',a,ga)-np.einsum('ni,nj->ij',b,gb)
            self.lmp.fix_external_set_energy_global('anglelaw',energy)
            self.lmp.fix_external_set_virial_global('anglelaw',[tensor[0,0],tensor[1,1],0.,tensor[0,1],0.,0.])
        except Exception as exc:
            self.error=type(exc).__name__+': '+str(exc);fexternal[:]=np.nan
            self.lmp.fix_external_set_energy_global('anglelaw',float('nan'))


def attach_angle_controller(lmp,meta_file):
    return AngularController(lmp,json.loads(Path(meta_file).read_text()))


def run_export(deck):
    """CPU driver: forces and strain sampled at the same physical time.

    fix deform changes the box at end-of-step, after the force virial was
    evaluated. A run-0 refresh before sampling avoids pairing that stale virial
    with the new box strain. Explicit start/stop keep one continuous wiggle.
    """
    import os
    from lammps import lammps
    deck=Path(deck).resolve();old=Path.cwd();os.chdir(deck.parent);lmp=None
    try:
        lines=deck.read_text().splitlines();i=next(i for i,l in enumerate(lines) if l.startswith('include '));base=lines[i].split()[1]
        meta_file=deck.with_suffix('.meta.json');meta=json.loads(meta_file.read_text());stem=deck.stem
        lmp=lammps(cmdargs=['-log',stem+'.run.log','-screen','none','-nocite']);lmp.file(base);controller=attach_angle_controller(lmp,meta_file)
        setup=[];total=None
        for line in lines[i+1:]:
            if line.startswith(('fix sample ','dump trajectory ')):continue
            if line.startswith('run '):total=int(line.split()[1]);break
            setup.append(line)
        if total is None:raise ValueError('missing bounded run length')
        lmp.commands_string('\n'.join(setup));cadence=meta['output_every']
        with open(stem+'_stress.txt','w') as series:
            series.write('time gamma sigma_config potential tether_energy thermostat_exchange\n')
            previous=0
            for end in range(0,total+cadence,cadence):
                end=min(end,total)
                if end:lmp.command(f'run {end-previous} start 0 stop {total} pre yes post no')
                previous=end
                lmp.command(f'run 0 start 0 stop {total} pre yes post no')
                if controller.error:raise RuntimeError(controller.error)
                values=[lmp.get_thermo('time'),lmp.extract_variable('gamma',None,0),lmp.extract_variable('sxy',None,0),lmp.get_thermo('pe'),lmp.extract_fix('gag',0,0),lmp.extract_fix('drag',0,0)]
                series.write(' '.join(format(float(x),'.17g') for x in values)+'\n');series.flush()
                lmp.command(f'write_dump all custom {stem}.dump id xu yu fx fy modify append yes sort id')
                if end==total:break
    finally:
        if lmp is not None:lmp.close()
        os.chdir(old)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('deck',type=Path);args=parser.parse_args();run_export(args.deck)
