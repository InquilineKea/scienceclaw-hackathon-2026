#!/usr/bin/env python3
"""Independent standard-library readback of frozen numerical output."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def independent_folded_fraction(T,hyp,hydration,crosslink,sites=81):
    """Scaled probability/count recurrence, independent of PyTorch/autograd."""
    weight=math.exp((.8+.25*hyp+.15*hydration+.10*crosslink)/T-1)
    boundary=math.exp(-(.45+.25*crosslink)/T)
    v0,v1=1.,weight;m0,m1=0.,weight
    for _ in range(sites-1):
        n0=v0+boundary*v1;n1=weight*(v1+boundary*v0)
        c0=m0+boundary*m1;c1=weight*(m1+v1+boundary*(m0+v0))
        scale=n0+n1;v0,v1=n0/scale,n1/scale;m0,m1=c0/scale,c1/scale
    return (m0+m1)/(v0+v1)/sites

def audit(run):
    run=Path(run)
    def read(name):return json.loads((run/name).read_text())
    errors=[];manifest=read('MANIFEST.json');actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
    if actual!=set(manifest)|{'MANIFEST.json'}:errors.append('Manifest coverage differs from directory')
    for name,m in manifest.items():
        p=run/name
        if not p.is_file():errors.append('Missing '+name);continue
        b=p.read_bytes()
        if len(b)!=m['bytes'] or hashlib.sha256(b).hexdigest()!=m['sha256']:errors.append('Checksum mismatch '+name)
    out={'manifestSHA256':hashlib.sha256((run/'MANIFEST.json').read_bytes()).hexdigest(),'manifestFiles':len(manifest),'integrityErrors':errors,'checks':read('CHECKS.json'),'context':read('RUN_CONTEXT.json'),'suites':{},'caveats':['Only recorded protocol samples are included in convergence counts; internal optimizer iterates and intermediate plastic-hold steps are not a trajectory archive.','A later converged point after an unconverged path-dependent update is insufficient to validate the entire history. Fully recorded converged paths are the conservative comparison subset.','Residual-strain root estimates have finite bisection resolution; the final zero-stress residual itself was not archived.','Prescribed microscopic rupture thresholds, plastic mobility and disk contact laws are model assumptions.','No atomistic thermal melting MD was run.']}
    for p in sorted((run/'data').glob('*.json')):
        data=json.loads(p.read_text());groups=data if isinstance(data,list) else [data];cases=[c for g in groups for c in g.get('cases',[])];curves=[c for c in cases if 'curve' in c]
        if curves:
            pts=[pt for c in curves for pt in c['curve']]
            out['suites'][p.stem]={'cases':len(curves),'samples':len(pts),'convergedSamples':sum(x['converged'] for x in pts),'fullyConvergedRecordedPaths':sum(all(x['converged'] for x in c['curve']) for c in curves),'maxResidual':max(x['residual'] for x in pts)}
    rig=[]
    for g in read('data/rigidity.json'):
        for c in g['cases']:
            row={'W':g['lattice']['W'],**c['parameters'],'realizedZ':c['graph']['z'],'graphLambda2':c['graph']['lambda2'],'validSamples':sum(p['converged'] for p in c['curve']),'sampleCount':len(c['curve']),'peakNonaffinityStrain':c['peakNonaffinityStrain'],'peakIsInterior':c['peakIsInterior']}
            for which,p in [('initial',c['curve'][0]),('final',c['curve'][-1])]:row[which+'Tangent']=p['tangentShearModulus'] if p['tangentValid'] else None
            rig.append(row)
    out['rigidity']=rig
    sm=[]
    for c in read('data/sliding-memory.json')['cases']:
        hold=[p for p in c['curve'] if p['stage'] in ['fast_load','hold']];eligible=all(p['converged'] for p in hold)
        sm.append({**c['parameters'],'allRecordedLoadHoldConverged':eligible,'stressRetainedAfterHold':c['stressRetainedAfterHold'] if eligible else None,'rawStressRetention':c['stressRetainedAfterHold'],'plasticDissipation':c['plasticDissipation'],'residualStrainEstimate':c['residualStrain'],'residualRootConverged':c['residualRootConverged']})
    out['slidingMemory']=sm
    paired={}
    for c in read('data/sliding-memory.json')['cases']:paired.setdefault(c['parameters']['seed'],[]).append(c)
    matched=[]
    for seed,cases in paired.items():
        base=cases[0];curve=[p for p in base['curve'] if p['stage']=='fast_load'];spread=0.
        for c in cases[1:]:
            other=[p for p in c['curve'] if p['stage']=='fast_load']
            spread=max(spread,max(abs(p['Pxy']-q['Pxy']) for p,q in zip(curve,other)))
        matched.append({'seed':seed,'identicalInitialGraphs':all(c['initialAlive']==base['initialAlive'] for c in cases),'maximumPreHoldStressDifference':spread,'lockingCases':len(cases)})
    out['matchedInitialControls']=matched
    out['slidingFailure']=[{**c['parameters'],'fullyConvergedRecordedPath':all(p['converged'] and p['ruptureAvalancheSettled'] for p in c['curve']),'rawStrainAt20PercentBondLoss':c['strainAt20PercentBondLoss'],'failureCensored':c['failureCensored'],'finalBrokenFraction':c['curve'][-1]['brokenFraction'],'maxValidTension':c['maximumValidTension']} for c in read('data/sliding-failure.json')['cases']]
    out['inclusions']=[{**c['parameters'],'fullyConvergedRecordedPath':all(p['converged'] for p in c['curve']),'initialContacts':c['curve'][0]['contacts'],'finalContacts':c['curve'][-1]['contacts'],'initialCompressionReaction':-c['curve'][0]['Pxx'] if c['curve'][0]['converged'] else None,'finalCompressionReaction':-c['curve'][-1]['Pxx'] if c['curve'][-1]['converged'] else None} for c in read('data/inclusions.json')['cases']]
    out['placement']=[{**c['parameters'],'eligible':all(p['converged'] for p in c['curve']),'rawSmallShearModulus':c['smallShearModulus']} for c in read('data/stiffness-percolation.json')['cases']]
    out['cuts']=[{**c['parameters'],'fullyConvergedRecordedPath':all(p['converged'] for p in c['curve']),'initialTension':c['curve'][0]['Pxx'],'finalTension':c['curve'][-1]['Pxx'],'finalValid':c['curve'][-1]['converged']} for c in read('data/targeted-damage.json')['cases']]
    fb=read('data/lox-feedback.json');rooterrors=[]
    for row in fb['equilibria']:
        for e in row['equilibria']:
            s,c,l=e['stiffness'],e['contractility'],e['lox'];res=max(abs(.25+row['coupling']*l-s),abs(s**4/(1+s**4)-c),abs(.05+row['productionGain']*c-l));rooterrors.append(res)
    same={round(p['g'],12):p for p in fb['down']};diff=[abs(p['stiffness']-same[round(p['g'],12)]['stiffness']) for p in fb['up'] if round(p['g'],12) in same and p['converged'] and same[round(p['g'],12)]['converged']]
    out['feedback']={'parameterPairs':len(fb['equilibria']),'pairsWithTwoStableEquilibria':sum(r['stableEquilibria']==2 for r in fb['equilibria']),'maximumEquilibriumResidual':max(rooterrors),'dynamicSamples':len(fb['up'])+len(fb['down']),'dynamicConverged':sum(p['converged'] for key in ['up','down'] for p in fb[key]),'maximumMatchedBranchSeparation':max(diff,default=None),'bistableAtCouplingOne':[r['productionGain'] for r in fb['equilibria'] if abs(r['coupling']-1)<1e-8 and r['stableEquilibria']==2]}
    th=read('data/helix-coil-sensitivity.json');rows=[]
    for c in th['cases']:
        q=c['foldedFraction'];temps=c['T_over_reference'];cross=next((temps[i]+(.5-q[i])/(q[i+1]-q[i])*(temps[i+1]-temps[i]) for i in range(len(q)-1) if q[i]>=.5>=q[i+1] and q[i]!=q[i+1]),None)
        comparison=[abs(value-independent_folded_fraction(T,c['hypothesisHypFraction'],c['hypothesisHydration'],c['hypothesisCrosslink'])) for T,value in zip(temps,q)]
        rows.append({k:v for k,v in c.items() if k.startswith('hypothesis')}|{'halfFoldedDimensionlessTemperature':cross,'monotoneDecreasing':all(q[i]>=q[i+1]-1e-12 for i in range(len(q)-1)),'bounded':all(-1e-12<=x<=1+1e-12 for x in q),'maxIndependentProbabilityRecurrenceDifference':max(comparison)})
    out['thermal']=rows
    out['mechanicalTotal']={key:sum(s[key] for s in out['suites'].values()) for key in ['cases','samples','convergedSamples','fullyConvergedRecordedPaths']}
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('output');a=p.parse_args();data=audit(a.run);Path(a.output).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');print(json.dumps({k:data[k] for k in ['manifestFiles','integrityErrors','mechanicalTotal','feedback']},indent=2))
