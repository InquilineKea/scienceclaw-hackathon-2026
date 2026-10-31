#!/usr/bin/env python3
"""Export saved JSON curves to a static explorer, using Python's standard library."""
from pathlib import Path
import argparse,json,shutil,hashlib

def build(run,out,dataset_url,article_url=''):
    run=Path(run);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    def read(name):return json.loads((run/name).read_text())
    context=read('RUN_CONTEXT.json');results=read('RESULTS.json');checks=read('CHECKS.json')
    if not checks or not all(c.get('passed') is True for c in checks):raise ValueError('Numerical check suite did not pass')
    manifest=read('MANIFEST.json')
    for name,m in manifest.items():
        b=(run/name).read_bytes()
        if len(b)!=m['bytes'] or hashlib.sha256(b).hexdigest()!=m['sha256']:raise ValueError('Changed raw file: '+name)
    suites=[]
    def suite(id,title,question,xlabel,ylabel,limit,cases):
        if not cases:return
        suites.append({'id':id,'title':title,'question':question,'xLabel':xlabel,'yLabel':ylabel,'limit':limit,'cases':cases,'defaultCompare':len(cases)-1 if len(cases)>1 else 0})
    def case(c,points,extra=None):
        pars={**(extra or {}),**c.get('parameters',{})}
        label=' · '.join(str(k)+'='+format(v,'.4g') if isinstance(v,float) else str(k)+'='+str(v) for k,v in pars.items() if k not in ['mobility','rupture'])
        return {'label':label,'parameters':pars,'points':points}
    def points(c,key,xkey='control',validkey='converged',scale=1):
        return [{'x':p[xkey] if xkey else i,'y':p[key]*scale,'valid':bool(p.get(validkey,False))} for i,p in enumerate(c['curve'])]
    def history_points(c,key,xkey='control',require_settled=False):
        out=[];history_valid=True
        for i,p in enumerate(c['curve']):
            history_valid=history_valid and p['converged'] and (not require_settled or p['ruptureAvalancheSettled'])
            out.append({'x':p[xkey] if xkey else i,'y':p[key],'valid':bool(history_valid)})
        return out
    for key,title,yl,flag in [('tangentShearModulus','Strain-driven stiffness','Tangent shear modulus','tangentValid'),('incrementalNonaffinity','Nonaffine rearrangement','Incremental nonaffinity','nonaffinityValid')]:
        cases=[case(c,points(c,key,validkey=flag),{'W':g['lattice']['W']}) for g in read('data/rigidity.json') for c in g['cases']]
        suite(key,title,'How does changing strain move the network through its mechanical crossover?','Shear strain γ',yl,'Finite 2D networks. Derivatives and increments require valid neighboring equilibria. Peaks are not established thermodynamic critical points.',cases)
    data=read('data/sliding-memory.json')
    suite('sliding','Sliding and locking','Do matched initial spring moduli produce different load–hold–unload paths?','Ordered protocol sample','Shear stress','The locking parameter controls an assumed plastic mobility. It is not an AGE concentration. Time is dimensionless. A failed recorded state invalidates the following history.',[case(c,history_points(c,'Pxy',xkey=None)) for c in data['cases']])
    failure=read('data/sliding-failure.json')
    suite('rupture','Sliding with rupture','Does reducing mobility change where damage accumulates?','Constrained tensile strain','Tension','A common elastic rupture threshold is prescribed. Recorded history must remain converged with settled rupture avalanches.',[case(c,history_points(c,'Pxx',require_settled=True)) for c in failure['cases']])
    cuts=read('data/targeted-damage.json')
    def cut_points(c):
        base=c['curve'][0]['Pxx'];pts=history_points(c,'Pxx')
        for p in pts:
            p['y']=p['y']/base if abs(base)>1e-12 else None
            p['valid']=p['valid'] and abs(base)>1e-12
        return pts
    suite('cuts','Damage placement','Does cutting the highest-tension bonds differ from random cutting?','Fraction of initial bonds cut','Retained tension / initial tension','Laterally constrained tension at a fixed 0.12 strain. The initial reference and the preceding recorded history must converge.',[case(c,cut_points(c)) for c in cuts['cases']])
    inc=read('data/inclusions.json')
    suite('inclusions','Inclusion contact and compression','How do finite disk contacts change the compression response?','Uniaxial compression strain','Compression reaction','Area fraction is a two-dimensional disk parameter, not cell volume fraction. Initial contact and prestress may be present.',[case(c,points(c,'Pxx',scale=-1)) for c in inc['cases']])
    pc=read('data/stiffness-percolation.json')['cases'];groups={}
    for c in pc:
        par=c['parameters'];key=(par['seed'],par['placement']);groups.setdefault(key,[]).append(c)
    suite('placement','Placement of stiff bonds','Does clustering stiff bonds alter the small-strain modulus?','Fraction of existing bonds stiffened ×20','Small-strain shear modulus','The graph is unchanged. A change in stiffness alone does not demonstrate rigidity percolation.',[case({'parameters':{'seed':seed,'placement':mode}},[{'x':c['parameters']['stiffFraction'],'y':c['smallShearModulus'],'valid':all(p['converged'] for p in c['curve'])} for c in sorted(cs,key=lambda c:c['parameters']['stiffFraction'])]) for (seed,mode),cs in groups.items()])
    mem=read('data/plastic-memory-matrix.json')['cases'];groups={}
    for c in mem:
        p=c['parameters'];groups.setdefault((p['amplitude'],p['locking']),[]).append(c)
    suite('memory','Plastic memory','How do hold time and loading amplitude affect residual deformation?','Hold time (model units)','Residual strain','Provisional zero-stress crossings interpolated from a coarse unloading grid. Missing crossings remain unavailable. Residual estimates are non-monotonic in locking and are not a robust memory ranking.',[case({'parameters':{'amplitude':a,'locking':lock}},[{'x':c['parameters']['holdTime'],'y':c['residualStrainInterpolated'] if c['residualStrainInterpolated'] is not None else None,'valid':c['residualStrainInterpolated'] is not None and all(p['converged'] for p in c['curve'])} for c in sorted(cs,key=lambda c:c['parameters']['holdTime'])]) for (a,lock),cs in groups.items()])
    fb=read('data/lox-feedback.json')
    suite('feedback','Hypothetical LOX feedback','Do increasing and decreasing gain paths settle on the same branch?','Production-gain parameter','Stiffness proxy','A declared three-stage ODE model. Bistability requires independently verified stable equilibria; these gains are not fitted to LOX biology.',[{'label':label,'parameters':{'path':key,'coupling':1},'points':[{'x':p['g'],'y':p['stiffness'],'valid':p['converged']} for p in fb[key]]} for key,label in [('up','Increasing gain'),('down','Decreasing gain')]])
    th=read('data/helix-coil-sensitivity.json')
    suite('thermal','Helix–coil sensitivity','How do declared stabilization assumptions change a finite statistical model?','Dimensionless temperature','Folded-site fraction','Exact 81-site transfer matrix, not atomistic MD. Coefficients are assumed; no Celsius mapping or avian–human prediction.',[case({'parameters':{k:c[k] for k in ['hypothesisHypFraction','hypothesisHydration','hypothesisCrosslink']}},[{'x':t,'y':y,'valid':0<=y<=1+1e-12} for t,y in zip(c['T_over_reference'],c['foldedFraction'])]) for c in th['cases']])
    figs=[];dest=out/'figures';dest.mkdir(exist_ok=True)
    for name,caption in [('01-strain-rigidity.png','Finite strain crossovers; invalid samples appear as gaps.'),('02-sliding-locking.png','Matched initial spring stiffness and varied hypothetical mobility. Residual-strain roots are provisional and non-monotonic; final zero-stress residuals were not saved.'),('02b-sliding-failure.png','Rupture under a shared threshold and distinct sliding rates.'),('03-plastic-memory.png','Provisional residual-strain interpolation. Blank cells have no resolved zero-crossing; they do not indicate zero memory. Locking does not produce a monotonic residual-strain ranking.'),('04-stiffening-and-damage.png','Stiff-bond placement and adaptive cuts.'),('05-inclusion-compression.png','Explicit finite disk contact under compression.'),('06-lox-feedback.png','Stable and unstable mathematical equilibria, plus dynamic paths.'),('07-helix-coil.png','Finite statistical sensitivity; no melting MD or Celsius mapping.'),('inclusion-contact.gif','Saved compression states; periodic crossing edges are omitted. Convergence is shown on every frame.'),('sliding-memory.gif','Saved load–hold–unload states; no chemical reaction is animated.')]:
        shutil.copyfile(run/'figures'/name,dest/name);figs.append({'src':'figures/'+name,'alt':caption,'caption':caption})
    count=results['numericalSamples'];links=[{'label':'Frozen raw data and logs','url':dataset_url},{'label':'Model source and methods','url':'https://github.com/InquilineKea/scienceclaw-hackathon-2026/tree/main/collagen-transition-atlas'},{'label':'Large-file recovery instructions','url':'https://github.com/InquilineKea/scienceclaw-hackathon-2026/blob/main/LARGE_DATASETS.md'}]
    if article_url:links.insert(0,{'label':'Read the results article','url':article_url})
    payload={'badges':[context['gpu'],str(len(checks))+' / '+str(len(checks))+' checks passed',str(count['converged'])+' / '+str(count['samples'])+' mechanical samples converged','Small pilot: 36 junctions, one seed' if context['profile']=='commission' else 'Profile: '+context['profile']],'suites':suites,'figures':figs,'links':links,'rawManifestSHA256':hashlib.sha256((run/'MANIFEST.json').read_bytes()).hexdigest()}
    (out/'transition-view.json').write_text(json.dumps(payload,allow_nan=False)+'\n')
    return {'suites':len(suites),'curves':sum(len(s['cases']) for s in suites),'figures':len(figs),'rawManifestSHA256':payload['rawManifestSHA256']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('out');ap.add_argument('--dataset-url',required=True);ap.add_argument('--article-url',default='');a=ap.parse_args();print(json.dumps(build(a.run,a.out,a.dataset_url,a.article_url),indent=2))
