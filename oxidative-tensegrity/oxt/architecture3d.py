"""Original periodic architecture generators and measured matching diagnostics.
No network, package installation, file mutation or implicit parameter calibration.
"""
import math
from itertools import product,combinations
import numpy as np
from .network3d import Lattice3D,SystemSpec3D

class Graph3D:
    def __init__(self,X,bi,bj,shift,fiber,L,kind,metadata=None):
        self.X=np.asarray(X,float).reshape(-1,3);self.N=len(self.X)
        self.bi=np.asarray(bi,int);self.bj=np.asarray(bj,int);self.shift=np.asarray(shift,float).reshape(-1,3)
        self.fiber=np.asarray(fiber,int);self.L=np.asarray(L,float);self.volume=float(np.prod(self.L));self.Nb=len(self.bi)
        self.kind=kind;self.metadata=dict(metadata or {});self.rebuild()
    def rebuild(self):
        d=self.X[self.bj]-self.X[self.bi]+self.shift
        self.rest_len=np.linalg.norm(d,axis=1)
        if np.any(self.rest_len<1e-7):raise ValueError('zero/near-zero reference segment')
        unit=d/self.rest_len[:,None];spokes=[[] for _ in range(self.N)]
        for e,(i,j) in enumerate(zip(self.bi,self.bj)):
            spokes[i].append((e,1));spokes[j].append((e,-1))
        ai=[];aj=[];asu=[];asv=[];ac=[];an=[];b_in=[];b_out=[]
        for n,sp in enumerate(spokes):
            for (e,se),(f,sf) in combinations(sp,2):
                if self.fiber[e]==self.fiber[f] and se!=sf:
                    incoming,outgoing=(e,f) if se<0 else (f,e)
                    b_in.append(incoming);b_out.append(outgoing)
                # All junction pairs share the same generic angular-lock law.
                ai.append(e);aj.append(f);asu.append(se);asv.append(sf);ac.append(float(np.dot(unit[e]*se,unit[f]*sf)));an.append(n)
        self.bend_in=np.asarray(b_in,int);self.bend_out=np.asarray(b_out,int)
        self.bend_theta0=np.arctan2(np.linalg.norm(np.cross(d[self.bend_in],d[self.bend_out]),axis=1),np.sum(d[self.bend_in]*d[self.bend_out],axis=1))
        self.ang_u=np.asarray(ai,int);self.ang_v=np.asarray(aj,int);self.ang_su=np.asarray(asu,float);self.ang_sv=np.asarray(asv,float);self.ang_cos0=np.asarray(ac,float);self.ang_node=np.asarray(an,int)
    def crack_plane(self,axis=0):
        a=self.X[self.bi];b=self.X[self.bj]+self.shift
        levels=np.unique(self.X[:,axis]);m=np.searchsorted(levels,self.L[axis]/2);m=max(1,min(m,len(levels)-1));c=.5*(levels[m-1]+levels[m])
        crossing=(a[:,axis]-c)*(b[:,axis]-c)<0;sign=np.where(b[:,axis]>c,1.,-1.);pa=[k for k in range(3) if k!=axis]
        return crossing,sign,.5*(a+b)[:,pa]-.5*self.L[pa]
    def plane_area(self,axis=0):return float(np.prod(np.delete(self.L,axis)))

def diluted_fcc(W=2,seed=0):
    lat=Lattice3D(W)
    return Graph3D(lat.X,lat.bi,lat.bj,lat.shift,lat.line,lat.L,'diluted_FCC',dict(W=W,seed=seed))

def phantom_fcc(W=2,seed=0):
    """At each FCC vertex, pair its six fibre axes into three binary junctions.
    Co-located copies share no mechanical degree of freedom; no implicit contact.
    """
    lat=Lattice3D(W);rng=np.random.default_rng(seed);slot=np.empty((lat.N,6),int)
    for n in range(lat.N):
        axes=rng.permutation(6)
        for pair in range(3):slot[n,axes[2*pair:2*pair+2]]=3*n+pair
    i=slot[lat.bi,lat.bdir];j=slot[lat.bj,lat.bdir]
    return Graph3D(np.repeat(lat.X,3,axis=0),i,j,lat.shift,lat.line,lat.L,'phantom_FCC',dict(W=W,seed=seed,binary_junctions=True))

def closest_segments(p,u,q,v):
    """Exact box-constrained closest points; endpoints plus feasible stationary point."""
    w=p-q;a=float(u@u);b=float(u@v);c=float(v@v);d=float(u@w);e=float(v@w);den=a*c-b*b
    cand=[(0.,np.clip(e/c,0,1)),(1.,np.clip((e+b)/c,0,1)),(np.clip(-d/a,0,1),0.),(np.clip((b-d)/a,0,1),1.)]
    if den>1e-14*a*c:
        t=(b*e-c*d)/den;s=(a*e-b*d)/den
        if 0<=t<=1 and 0<=s<=1:cand.append((t,s))
    t,s=min(cand,key=lambda ts:np.linalg.norm(p+ts[0]*u-q-ts[1]*v))
    A=p+t*u;B=q+s*v
    return float(np.linalg.norm(A-B)),float(t),float(s),A,B

def stochastic_fibers(W=2,seed=0,n_fibers=18,capture_fraction=.28,length_fraction=1.2):
    """Finite rods joined at closest encounters within a declared capture radius.
    One junction per rod pair; free fibre ends retained; encounter midpoint is the
    stress-free junction. Radius and rod number are explicit model parameters.
    """
    rng=np.random.default_rng(seed);L=np.full(3,math.sqrt(2)*W);centers=rng.random((n_fibers,3))*L
    unit=rng.normal(size=(n_fibers,3));unit/=np.linalg.norm(unit,axis=1)[:,None]
    rods=unit*(length_fraction*L[0]);starts=centers-rods/2
    offsets=np.array(list(product([-1,0,1],repeat=3)))*L
    encounters=[]
    for i,j in combinations(range(n_fibers),2):
        base=np.rint((centers[i]-centers[j])/L)*L
        candidates=[(*closest_segments(starts[i],rods[i],starts[j]+base+o,rods[j]),base+o) for o in offsets]
        dist,t,s,A,B,image=min(candidates,key=lambda c:c[0])
        if dist<=capture_fraction*L[0] and .02<t<.98 and .02<s<.98:encounters.append((dist,i,j,t,s,.5*(A+B),image))
    X=[];points=[[] for _ in range(n_fibers)];accepted=0
    for dist,i,j,t,s,mid,image in sorted(encounters,key=lambda c:c[0]):
        if any(abs(t-q[0])<.035 for q in points[i]) or any(abs(s-q[0])<.035 for q in points[j]):continue
        node=len(X);X.append(mid%L);points[i].append((t,node,mid));points[j].append((s,node,mid-image));accepted+=1
    bi=[];bj=[];shift=[];fiber=[]
    for f,ps in enumerate(points):
        for t in (0.,1.):
            pos=starts[f]+t*rods[f];n=len(X);X.append(pos%L);ps.append((t,n,pos))
        ps.sort()
        for left,right in zip(ps[:-1],ps[1:]):
            _,i,A=left;_,j,B=right;bi.append(i);bj.append(j);shift.append(B-A-(X[j]-X[i]));fiber.append(f)
    return Graph3D(X,bi,bj,shift,fiber,L,'stochastic_3D',dict(W=W,seed=seed,n_fibers=n_fibers,capture_fraction=capture_fraction,length_fraction=length_fraction,encounters=accepted,free_end_count=2*n_fibers))

def curve_graph(graph,amplitude=0.,seed=0):
    """Independent periodic node waviness, followed by full rest-geometry reset.
    This is a measured tortuosity/curvature intervention, not prescribed helix physics.
    """
    if amplitude<0:raise ValueError('negative curvature amplitude')
    if amplitude:
        rng=np.random.default_rng(seed);graph.X=graph.X+rng.normal(0.,amplitude,(graph.N,3));graph.rebuild()
    return graph

def make_spec(graph,z=3.2,seed=0,alignment_bias=0.,lock_fraction=.08,placement='uniform',EA=1.,EI=.003,eps_r=.1,embedding_density=1e-3):
    rng=np.random.default_rng(seed)
    allowed=np.ones(graph.Nb,bool);cut_count=0
    for fid in np.unique(graph.fiber):
        ids=np.flatnonzero(graph.fiber==fid)
        deg=np.bincount(np.r_[graph.bi[ids],graph.bj[ids]],minlength=graph.N)
        if np.all(deg[deg>0]==2):
            allowed[rng.choice(ids)]=False;cut_count+=1
    n=min(int(allowed.sum()),max(0,round(z*graph.N/2)))
    graph.metadata.update(requested_z=z,finite_fiber_cut_count=cut_count)
    d=graph.X[graph.bj]-graph.X[graph.bi]+graph.shift;cos2=(d[:,0]/graph.rest_len)**2
    weight=np.exp(np.clip(alignment_bias*(cos2-1/3),-20,20));keys=-np.log(rng.uniform(1e-12,1.,graph.Nb))/weight
    keys[~allowed]=np.inf
    alive=np.zeros(graph.Nb,bool);alive[np.argsort(keys)[:n]]=True
    degree=np.bincount(np.r_[graph.bi[alive],graph.bj[alive]],minlength=graph.N);eligible=np.flatnonzero(degree>=2);count=min(len(eligible),round(lock_fraction*graph.N));rigid=np.zeros(graph.N)
    if placement=='uniform':chosen=rng.permutation(eligible)[:count]
    elif placement=='clustered':
        delta=graph.X[eligible]-.5*graph.L;delta-=np.rint(delta/graph.L)*graph.L;chosen=eligible[np.argsort(np.sum(delta*delta,axis=1))[:count]]
    elif placement=='gradient':chosen=eligible[np.argsort(graph.X[eligible,0])[:count]]
    else:raise ValueError('unknown link placement')
    rigid[chosen]=.002
    # Fixed axial material EA; segment coefficient is EA/l_rest. The bending
    # factors give EI/sqrt(l_in*l_out), explicit quadrature convention.
    spec=SystemSpec3D(alive,EA/graph.rest_len,1/graph.rest_len,np.full(graph.Nb,eps_r),rigid,EI,0.,embedding_density*graph.volume/max(graph.N,1),meta=dict(generator=graph.kind,seed=seed,lock_fail_rad=.5,EA=EA,EI=EI))
    return spec

def diagnostics(graph,spec,cross_section=1.):
    alive=spec.alive;degree=np.bincount(np.r_[graph.bi[alive],graph.bj[alive]],minlength=graph.N)
    d=graph.X[graph.bj]-graph.X[graph.bi]+graph.shift;v=d[alive]/graph.rest_len[alive,None];length=graph.rest_len[alive];weights=length/max(float(length.sum()),1e-30)
    Q=np.einsum('n,ni,nj->ij',weights,v,v) if len(v) else np.zeros((3,3));adj=[[] for _ in range(graph.N)]
    for e in np.flatnonzero(alive):adj[graph.bi[e]].append(graph.bj[e]);adj[graph.bj[e]].append(graph.bi[e])
    unseen=set(range(graph.N));sizes=[]
    while unseen:
        stack=[unseen.pop()];size=0
        while stack:
            n=stack.pop();size+=1
            for j in adj[n]:
                if j in unseen:unseen.remove(j);stack.append(j)
        sizes.append(size)
    tortuosity=[]
    for fid in np.unique(graph.fiber):
        member=graph.fiber==fid;net=np.sum(d[member],axis=0);chord=float(np.linalg.norm(net))
        if chord>1e-9:tortuosity.append(float(np.sum(graph.rest_len[member]))/chord)
    return dict(mean_tortuosity=float(np.mean(tortuosity)) if tortuosity else None,nodes=graph.N,edges=graph.Nb,alive_edges=int(alive.sum()),z_all=float(degree.mean()),z_nonisolated=float(degree[degree>0].mean()) if (degree>0).any() else 0.,degree_max=int(degree.max()),junction_nodes=int((degree>=3).sum()),discretization_degree2_nodes=int((degree==2).sum()),isolates=int((degree==0).sum()),largest_component_fraction=max(sizes)/graph.N,contour_length=float(length.sum()),fiber_volume_fraction=float(length.sum()*cross_section/graph.volume),orientation_tensor=Q.tolist(),S_x=float((3*Q[0,0]-1)/2),locked_nodes=int((spec.rigid_node>0).sum()),reference_energy_expected=0.,min_rest_length=float(graph.rest_len.min()),max_bend_rest=float(graph.bend_theta0.max()) if len(graph.bend_theta0) else 0.)

GENERATORS={'diluted_FCC':diluted_fcc,'phantom_FCC':phantom_fcc,'stochastic_3D':stochastic_fibers}
