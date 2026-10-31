#!/usr/bin/env python3
"""Compare exported scan JSON using Python's standard library only.
No model loading, imported molecular code, network access, or GPU work.
Usage: python3 compare_scans.py OFF.json MP.json OUTPUT_DIRECTORY
"""
import csv, hashlib, json, math, sys
from pathlib import Path

def load(p):
    def reject(x): raise ValueError('Nonfinite JSON token '+x)
    return json.loads(Path(p).read_text(),parse_constant=reject)
def finite(x):
    if not isinstance(x,(int,float)) or not math.isfinite(x): raise ValueError('Nonfinite or nonnumeric value')
    return x

def solve(a,b):
    a=[list(r)+[v] for r,v in zip(a,b)]
    for i in range(3):
        m=max(range(i,3),key=lambda k:abs(a[k][i]));a[i],a[m]=a[m],a[i]
        if abs(a[i][i])<1e-18:raise ValueError('Singular fit')
        v=a[i][i];a[i]=[x/v for x in a[i]]
        for j in range(3):
            if j!=i:
                v=a[j][i];a[j]=[x-v*y for x,y in zip(a[j],a[i])]
    return [r[-1] for r in a]

def refit(L,E):
    imin=min(range(len(E)),key=E.__getitem__)
    near=sorted(range(len(L)),key=lambda i:abs(L[i]-L[imin]))[:5]
    x=[L[i]-L[imin] for i in near];y=[E[i] for i in near]
    v=[[1,t,t*t] for t in x]
    a=[[sum(row[i]*row[j] for row in v) for j in range(3)] for i in range(3)]
    b=[sum(row[i]*z for row,z in zip(v,y)) for i in range(3)]
    coef=solve(a,b)
    slopes=[(E[1]-E[0])/(L[1]-L[0])]
    for i in range(1,len(L)-1):
        h1=L[i]-L[i-1];h2=L[i+1]-L[i]
        slopes.append(-h2/(h1*(h1+h2))*E[i-1]+(h2-h1)/(h1*h2)*E[i]+h1/(h2*(h1+h2))*E[i+1])
    slopes.append((E[-1]-E[-2])/(L[-1]-L[-2]))
    return 2*coef[2],max(slopes),imin

def validate(d):
    for key in ['seconds','steps','final_fmax']:finite(d[key])
    cs=d['crosslinks'];checks={}
    if len(cs)!=8:raise ValueError('Expected eight proxy fragments')
    for name,v in cs.items():
        L=list(map(finite,v['L_A']));E=list(map(finite,v['E_eV']))
        if len(L)!=21 or len(E)!=21:raise ValueError('Expected 21 scan points')
        if not all(b>a for a,b in zip(L,L[1:])):raise ValueError('Non-increasing distance grid')
        if abs(min(E))>1e-8:raise ValueError('Curve not zero-referenced at minimum')
        for key in ['L0_A','k_eV_A2','k_rel','peak_force_eV_A']:finite(v[key])
        k,peak,imin=refit(L,E)
        k_ok=math.isclose(k,v['k_eV_A2'],rel_tol=1e-6,abs_tol=1e-8)
        peak_ok=math.isclose(peak,v['peak_force_eV_A'],rel_tol=1e-7,abs_tol=1e-9)
        relative_ok=math.isclose(v['k_rel'],v['k_eV_A2']/cs['pyridinoline']['k_eV_A2'],rel_tol=1e-8,abs_tol=1e-10)
        checks[name]={'refitted_k_eV_A2':k,'recomputed_peak_slope_eV_A':peak,'k_reproduced':k_ok,'peak_reproduced':peak_ok,'normalization_reproduced':relative_ok,'minimum_grid_index':imin,'minimum_at_boundary':imin in [0,len(L)-1],'negative_curvature':k<0}
    return checks

def main():
    offpath,mppath,dest=map(Path,sys.argv[1:]);dest.mkdir(parents=True,exist_ok=True)
    off,mp=load(offpath),load(mppath)
    offcheck,mpcheck=validate(off),validate(mp)
    if set(off['crosslinks'])!=set(mp['crosslinks']):raise ValueError('Fragment sets differ')
    rows=[]
    for name,a in off['crosslinks'].items():
        b=mp['crosslinks'][name]
        if a['smiles']!=b['smiles']:raise ValueError('SMILES mismatch '+name)
        if not all(math.isclose(x,y,rel_tol=0,abs_tol=1e-8) for x,y in zip(a['L_A'],b['L_A'])):raise ValueError('Distance grids differ '+name)
        dif=[y-x for x,y in zip(a['E_eV'],b['E_eV'])]
        rows.append({'source_proxy_label':name,'k_OFF_eV_A2':a['k_eV_A2'],'k_MP_eV_A2':b['k_eV_A2'],'k_MP_over_OFF':b['k_eV_A2']/a['k_eV_A2'],'k_relative_change_percent':100*(b['k_eV_A2']/a['k_eV_A2']-1),'peak_slope_OFF_eV_A':a['peak_force_eV_A'],'peak_slope_MP_eV_A':b['peak_force_eV_A'],'k_rel_OFF':a['k_rel'],'k_rel_MP':b['k_rel'],'curve_RMSE_eV':math.sqrt(sum(x*x for x in dif)/len(dif)),'curve_max_absolute_difference_eV':max(map(abs,dif)),'min_distance_OFF_A':a['L_A'][offcheck[name]['minimum_grid_index']],'min_distance_MP_A':b['L_A'][mpcheck[name]['minimum_grid_index']]})
    orders={label:sorted(d['crosslinks'],key=lambda n:d['crosslinks'][n]['k_eV_A2'],reverse=True) for label,d in [('OFF',off),('MP',mp)]}
    n=len(rows);rho=1-6*sum((orders['OFF'].index(x)-orders['MP'].index(x))**2 for x in orders['OFF'])/(n*(n*n-1))
    result={'scope':'Descriptive comparison of proxy-fragment scans; not a validation against molecular or tissue reference data','sources':{'OFF':{'model':off['source'],'sha256':hashlib.sha256(offpath.read_bytes()).hexdigest(),'seconds':off['seconds'],'steps':off['steps'],'reported_final_free_atom_fmax_eV_A':off['final_fmax']},'MP':{'model':mp['source'],'sha256':hashlib.sha256(mppath.read_bytes()).hexdigest(),'seconds':mp['seconds'],'steps':mp['steps'],'reported_final_free_atom_fmax_eV_A':mp['final_fmax']}},'matched_fragments':8,'points_per_fragment':21,'same_source_SMILES_and_distance_grids':True,'independent_arithmetic_checks':{'OFF':offcheck,'MP':mpcheck},'all_arithmetic_checks_pass':all(v['k_reproduced'] and v['peak_reproduced'] and v['normalization_reproduced'] for checks in [offcheck,mpcheck] for v in checks.values()),'rows':rows,'descending_k_order':orders,'descriptive_spearman_k_rank_correlation':rho,'MACE_MP_to_OFF_reported_runtime_ratio':mp['seconds']/off['seconds'],'cost_at_observed_L4_catalog_rate':{'USD_per_hour':.845421,'OFF_compute_equivalent_USD':off['seconds']*.845421/3600,'MP_compute_equivalent_USD':mp['seconds']*.845421/3600,'invoice_verified':False},'caveats':['Source labels describe truncated or approximate neutral proxies; native glucosepane/PYD/4-HNE chemistry is not validated.','Both use the MACE architecture; differing checkpoints/training data are not independent experimental validation.','MACE-MP-0b2 targets materials with MPTrj/PBE+U data; MACE-OFF23 targets neutral organic chemistry with SPICE/wB97M+D3 data.','Each curve is independently minimum-zeroed; offsets and absolute total energies must not be compared between model families.','Different relaxed coordinates may contribute to the curve difference; this is not a same-geometry energy-force benchmark.','k is a five-point local quadratic fit; peak slope is not rupture force or a reaction event.','The pyridinoline-proxy normalizer can conceal model disagreement; raw k and shape comparisons are retained.','Final per-structure coordinates/forces were not exported by the legacy scan; aggregate force convergence is not independent geometry validation.','Timings include setup/compilation and are not repeated controlled benchmarks.']}
    (dest/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    with (dest/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'arithmetic_checks_pass':result['all_arithmetic_checks_pass'],'models':result['sources'],'rows':rows,'rank_correlation':rho},indent=2))
if __name__=='__main__':main()
