"""Original standard-library-only central-force control experiment. No repo imports."""
import math, random, json, csv, sys, time, hashlib, shutil
from pathlib import Path
from collections import defaultdict
FAMILIES=['triangular2d','fcc3d','disordered3d']
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cg(rows,b,tol=1e-9):
    n=len(b);x=[0.]*n;r=b[:];diag=[max(row.get(i,0.),1e-20) for i,row in enumerate(rows)]
    z=[r[i]/diag[i] for i in range(n)];p=z[:];rz=dot(r,z);bn=math.sqrt(dot(b,b))
    if bn<1e-20:return x,0.,0
    packed=[list(row.items()) for row in rows]
    for it in range(1500):
        ap=[sum(v*p[j] for j,v in row) for row in packed];den=dot(p,ap)
        if den<=1e-30:break
        a=rz/den;x=[v+a*w for v,w in zip(x,p)];r=[v-a*w for v,w in zip(r,ap)]
        if math.sqrt(dot(r,r))/bn<tol:break
        z=[r[i]/diag[i] for i in range(n)];nr=dot(r,z);beta=nr/rz; p=[z[i]+beta*p[i] for i in range(n)];rz=nr
    # Explicit recomputation, not the recursive residual.
    res=math.sqrt(sum((sum(v*x[j] for j,v in row)-b[i])**2 for i,row in enumerate(packed)))/bn
    return x,res,it+1

def dense(a,b):
    a=[list(r)+[v] for r,v in zip(a,b)];n=len(b)
    for j in range(n):
        k=max(range(j,n),key=lambda k:abs(a[k][j]));a[j],a[k]=a[k],a[j]
        if abs(a[j][j])<1e-14:raise ValueError('singular reference')
        v=a[j][j];a[j]=[q/v for q in a[j]]
        for k in range(n):
            if k!=j:
                v=a[k][j];a[k]=[q-v*w for q,w in zip(a[k],a[j])]
    return [r[-1] for r in a]

def geometry(family,seed):
    rng=random.Random(seed);d=2 if family=='triangular2d' else 3
    if d==2:
        labels=[(i,j) for j in range(7) for i in range(7)]
        pts=[[(i+.5*(j%2))/6.5,j/6] for i,j in labels]
        links=[(a,b) for a in range(len(pts)) for b in range(a) if abs(math.dist([(labels[a][0]+.5*(labels[a][1]%2)),labels[a][1]*math.sqrt(3)/2],[(labels[b][0]+.5*(labels[b][1]%2)),labels[b][1]*math.sqrt(3)/2])-1)<1e-8]
        jitter=.015
    else:
        labels=[(i,j,k) for k in range(5) for j in range(5) for i in range(5) if (i+j+k)%2==0]
        pts=[[x/4 for x in q] for q in labels]
        links=[(a,b) for a in range(len(pts)) for b in range(a) if sum((labels[a][i]-labels[b][i])**2 for i in range(3))==2]
        jitter=.006 if family=='fcc3d' else .055
    for p in pts:
        if 0<p[-1]<1:
            for i in range(d):p[i]+=rng.uniform(-jitter,jitter)
    total=sum(math.dist(pts[a],pts[b]) for a,b in links);area=1/total;edges=[]
    for a,b in links:
        v=[pts[b][i]-pts[a][i] for i in range(d)];l=math.sqrt(dot(v,v));n=[v0/l for v0 in v]
        edges.append({'a':a,'b':b,'l':l,'n':n,'k':area/l,'volume':area*l,'threshold':rng.uniform(.064,.096)})
    return {'family':family,'seed':seed,'dimension':d,'points':pts,'edges':edges,'area':area,'solid_budget':1.,'mean_degree':2*len(edges)/len(pts),'orientation_tensor':[[sum(e['volume']*e['n'][i]*e['n'][j] for e in edges) for j in range(d)] for i in range(d)]}

def solve(g,active,mode,tol=1e-9):
    d=g['dimension'];pts=g['points'];nn=len(pts)*d;axis=d-1 if mode=='tension' else 0
    fixed={i*d+j:(1. if j==axis and p[-1]>.999 else 0.) for i,p in enumerate(pts) if p[-1]<.001 or p[-1]>.999 for j in range(d)}
    free=[i for i in range(nn) if i not in fixed];idx={q:i for i,q in enumerate(free)};rows=[defaultdict(float) for q in free];b=[0.]*len(free)
    for ei in active:
        e=g['edges'][ei];q=[e['a']*d+i for i in range(d)]+[e['b']*d+i for i in range(d)];v=[-n for n in e['n']]+e['n']
        for ii,i in enumerate(q):
            if i not in idx:continue
            r=idx[i]
            for jj,j in enumerate(q):
                val=e['k']*v[ii]*v[jj]
                if j in idx:rows[r][idx[j]]+=val
                else:b[r]-=val*fixed[j]
    x,res,it=cg(rows,b,tol);u=[fixed.get(i,x[idx[i]] if i in idx else 0.) for i in range(nn)]
    strains={ei:sum((u[g['edges'][ei]['b']*d+j]-u[g['edges'][ei]['a']*d+j])*g['edges'][ei]['n'][j] for j in range(d))/g['edges'][ei]['l'] for ei in active}
    stiff=sum(g['edges'][i]['k']*(strains[i]*g['edges'][i]['l'])**2 for i in active)
    return u,strains,stiff,res,it

def damage_set(g,pattern):
    n=len(g['edges']);count=round(.10*n)
    if pattern=='intact':return []
    ids=list(range(n))
    if pattern=='distributed':random.Random(g['seed']+19000).shuffle(ids)
    else:ids.sort(key=lambda i:sum(((g['points'][g['edges'][i]['a']][j]+g['points'][g['edges'][i]['b']][j])/2-.5)**2 for j in range(g['dimension'])))
    return sorted(ids[:count])

def simulate(g,pattern,mode,step,tol):
    removed=damage_set(g,pattern);active=set(range(len(g['edges'])))-set(removed);initial=None;frames=[];curves=[];worst=0.;failure=None;work=0.;prevf=0.;preve=0.;energy_errors=[];solve_log=[]
    for si in range(round(.24/step)+1):
        eps=si*step;avalanche=[]
        # Re-equilibrate until all tension/compression strain thresholds are satisfied.
        for av in range(len(g['edges'])+1):
            u,s,k,r,it=solve(g,sorted(active),mode,tol);worst=max(worst,r);solve_log.append({'strain':eps,'avalanche':av,'residual':r,'iterations':it,'active':len(active)})
            if not math.isfinite(r) or r>max(1e-7,100*tol):
                return {'status':'solver_failed','at_strain':eps,'max_residual':worst,'curve':curves,'frames':frames,'solves':solve_log,'removed':removed,'failure_strain':failure,'work':work}
            if initial is None:initial=k
            broken=[i for i in active if abs(s[i]*eps)>g['edges'][i]['threshold']]
            if not broken:break
            # At fixed displacement each removal must reduce minimized elastic energy.
            before=.5*k*eps*eps;active.difference_update(broken);avalanche.extend(broken)
            _,_,after,rr,_=solve(g,sorted(active),mode,tol)
            energy_errors.append(max(0.,.5*after*eps*eps-before))
        f=k*eps;work+=.5*(prevf+f)*(eps-preve);prevf=f;preve=eps
        if failure is None and eps>0 and k<.1*initial:failure=eps
        curves.append({'strain':eps,'force':f,'stiffness':k,'elastic_energy':.5*k*eps*eps,'work_trapezoid':work,'broken_count':len(g['edges'])-len(active),'new_failures':avalanche,'residual':r})
        frames.append({'strain':eps,'displacement':[v*eps for v in u],'active':sorted(active)})
        if failure is not None:break
    return {'status':'completed','max_residual':worst,'initial_stiffness':initial,'failure_strain':failure,'censored':failure is None,'work':work,'peak_force':max(q['force'] for q in curves),'energy_increase_on_damage':max(energy_errors,default=0.),'removed':removed,'removed_volume':sum(g['edges'][i]['volume'] for i in removed),'removed_mean_grip_distance':sum(min((g['points'][g['edges'][i]['a']][-1]+g['points'][g['edges'][i]['b']][-1])/2,1-(g['points'][g['edges'][i]['a']][-1]+g['points'][g['edges'][i]['b']][-1])/2) for i in removed)/max(1,len(removed)),'curve':curves,'frames':frames,'solves':solve_log}

def references():
    rows=[{0:4.,1:-1.},{0:-1.,1:3.,2:-1.},{1:-1.,2:2.}];b=[1.,2.,3.];x,r,it=cg(rows,b,1e-12);y=dense([[row.get(j,0.) for j in range(3)] for row in rows],b)
    err=max(abs(v-w) for v,w in zip(x,y));assert err<1e-10
    g={'dimension':2,'points':[[0.,0.],[0.,.5],[0.,1.]],'edges':[{'a':0,'b':1,'n':[0.,1.],'l':.5,'k':2.},{'a':1,'b':2,'n':[0.,1.],'l':.5,'k':2.}]}
    u,s,k,r,it=solve(g,[0,1],'tension',1e-12);assert abs(k-1)<1e-12 and abs(u[3]-.5)<1e-12
    # Affine gradient check of independently accumulated edge energy.
    g=geometry('fcc3d',101);u,s,k,r,it=solve(g,list(range(len(g['edges']))),'tension',1e-12);eps=1e-6
    def energy(x):return sum(.5*e['k']*sum((x[e['b']*3+j]-x[e['a']*3+j])*e['n'][j] for j in range(3))**2 for e in g['edges'])
    free_node=next(i for i,p in enumerate(g['points']) if .1<p[-1]<.9);z=u[:];z[3*free_node]+=eps;z2=u[:];z2[3*free_node]-=eps;grad=(energy(z)-energy(z2))/(2*eps);assert abs(grad)<1e-7
    return {'cg_dense_max_abs_error':err,'analytic_two_springs_K':1.,'fcc_free_gradient_abs':abs(grad),'fcc_residual':r,'scope':'Independent dense linear algebra and analytic series-spring/energy-gradient checks; not an independent full network implementation.'}

def main():
    out=Path(sys.argv[1]);out.mkdir(exist_ok=False);start=time.time();(out/'raw').mkdir();(out/'geometry').mkdir()
    config={'model':'linearized central-force brittle truss; original implementation','families':FAMILIES,'seeds':list(range(101,111)),'normalizations':['equal_budget','matched_tension_K'],'damage':['intact','clustered','distributed'],'loading':['tension','shear'],'max_strain':.24,'step':.01,'refined_step':.005,'force_tolerance':1e-9,'refined_tolerance':1e-10,'match_target_K':1.,'no_cloud_cost':True,'no_experimental_calibration':True}
    (out/'config.json').write_text(json.dumps(config,indent=2));(out/'reference-checks.json').write_text(json.dumps(references(),indent=2));summary=[]
    # Geometry and actual damage outcomes calculated once per seed/loading, since uniform k scaling leaves strain thresholds and equilibrium displacements unchanged.
    for family in FAMILIES:
      for seed in config['seeds']:
        g=geometry(family,seed);(out/'geometry'/f'{family}-{seed}.json').write_text(json.dumps(g));_,_,K,res,_=solve(g,list(range(len(g['edges']))),'tension');assert K>0 and res<1e-7
        for pattern in config['damage']:
          for mode in config['loading']:
            for refinement,step,tol in [('base',.01,1e-9),('refined',.005,1e-10)]:
              r=simulate(g,pattern,mode,step,tol);ident=f'{family}-{seed}-{pattern}-{mode}-{refinement}';(out/'raw'/f'{ident}.json').write_text(json.dumps(r))
              for norm,scale in [('equal_budget',1.),('matched_tension_K',1/K)]:
                summary.append({'case_id':ident+'-'+norm,'raw_id':ident,'family':family,'seed':seed,'pattern':pattern,'loading':mode,'refinement':refinement,'normalization':norm,'material_scale':scale,'intact_tension_K':K*scale,'node_count':len(g['points']),'edge_count':len(g['edges']),'mean_degree':g['mean_degree'],'status':r['status'],'work':r['work']*scale,'work_over_intact_K':r['work']/K,'peak_force':r.get('peak_force',0)*scale,'initial_K':r.get('initial_stiffness',0)*scale,'failure_strain':r.get('failure_strain'),'censored':r.get('censored',True),'max_residual':r['max_residual'],'removed_volume':r.get('removed_volume'),'removed_mean_grip_distance':r.get('removed_mean_grip_distance'),'energy_increase_on_damage':r.get('energy_increase_on_damage')})
        print(json.dumps({'family':family,'seed':seed,'cases_so_far':len(summary),'elapsed_seconds':round(time.time()-start,2)}),flush=True)
    with (out/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    (out/'summary.json').write_text(json.dumps(summary));(out/'execution.json').write_text(json.dumps({'elapsed_seconds':time.time()-start,'raw_simulations':360,'reported_normalization_cases':len(summary),'failed':sum(q['status']!='completed' for q in summary),'max_residual':max(q['max_residual'] for q in summary),'cloud_cost_usd':0},indent=2))
if __name__=='__main__':main()
