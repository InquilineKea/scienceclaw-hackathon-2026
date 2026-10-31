"""Plots and animations from saved numerical records only (no invented data)."""
import json,sys,math
from pathlib import Path
sys.path.insert(0,'/tmp/transition-deps')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter

COLORS=['#007f86','#e56b42','#7353ba','#b69722','#288847','#bd4984']

def render(root):
    root=Path(root);out=root/'figures';out.mkdir(exist_ok=False)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130,'savefig.bbox':'tight'})
    def load(name):return json.loads((root/'data'/name).read_text())
    def finish(fig,name,caption):
        fig.text(.02,.01,caption,fontsize=8,color='#444');fig.tight_layout(rect=[0,.06,1,.94])
        fig.savefig(out/(name+'.png'));fig.savefig(out/(name+'.svg'));plt.close(fig)
    groups=load('rigidity.json');W=max(g['lattice']['W'] for g in groups)
    selected=[g for g in groups if g['lattice']['W']==W and g['cases'][0]['parameters']['kappa']==1e-4][0]
    fig,axes=plt.subplots(1,2,figsize=(11,4));fig.suptitle('Strain-driven rigidity: finite network crossovers')
    zvalues=sorted(set(c['parameters']['z'] for c in selected['cases']))
    for n,z in enumerate(zvalues):
        cases=[c for c in selected['cases'] if c['parameters']['z']==z]
        for ax,key in zip(axes,['tangentShearModulus','incrementalNonaffinity']):
            validkey='tangentValid' if key=='tangentShearModulus' else 'nonaffinityValid'
            rows=np.array([[p[key] if p[validkey] else np.nan for p in c['curve']] for c in cases]);x=[p['control'] for p in cases[0]['curve']]
            with np.errstate(invalid='ignore'):y=np.nanmedian(rows,axis=0)
            ax.plot(x,y,color=COLORS[n%len(COLORS)],label='z='+str(z));ax.set_xlabel('Shear strain γ');ax.grid(alpha=.15)
    axes[0].set_ylabel('Tangent modulus (model units)');axes[1].set_ylabel('Incremental nonaffinity Γ');axes[1].set_yscale('symlog',linthresh=.001);axes[0].legend()
    finish(fig,'01-strain-rigidity','Finite 2D networks; median across available seeds. Unconverged samples are gaps. No critical exponent or tissue calibration.')
    data=load('sliding-memory.json');fig,axes=plt.subplots(1,3,figsize=(13,4));fig.suptitle('Sliding and locking: matched initial spring stiffness')
    for n,c in enumerate(x for x in data['cases'] if x['parameters']['seed']==17):
        label='locking='+str(c['parameters']['locking']);curve=c['curve'];axes[0].plot(range(len(curve)),[p['Pxy'] if p['converged'] else np.nan for p in curve],label=label,color=COLORS[n%6])
        if c['stressRetainedAfterHold'] is not None:axes[1].scatter(c['parameters']['locking'],c['stressRetainedAfterHold'],color=COLORS[n%6])
        if c['residualStrain'] is not None and c['residualRootConverged']:axes[2].scatter(c['parameters']['locking'],c['residualStrain'],color=COLORS[n%6])
    axes[0].set(xlabel='Ordered load / hold / unload samples',ylabel='Shear stress (model units)');axes[0].legend(fontsize=8)
    axes[1].set(xlabel='Hypothetical locking fraction',ylabel='Stress retained after hold');axes[2].set(xlabel='Hypothetical locking fraction',ylabel='Stress-free residual shear strain')
    finish(fig,'02-sliding-locking','Seed 17 illustrations. Mobility is an assumed law, not a measured AGE dose. Hold time is dimensionless.')
    failure=load('sliding-failure.json');fig,axes=plt.subplots(1,2,figsize=(11,4));fig.suptitle('Locking, sliding and rupture under increasing tension')
    for n,c in enumerate(x for x in failure['cases'] if x['parameters']['seed']==17):
        x=[p['control'] for p in c['curve']];color=COLORS[n%6];label='locking='+str(c['parameters']['locking'])
        axes[0].plot(x,[p['Pxx'] if p['converged'] and p['ruptureAvalancheSettled'] else np.nan for p in c['curve']],color=color,label=label)
        axes[1].plot(x,[p['brokenFraction'] for p in c['curve']],color=color)
    axes[0].set(xlabel='Constrained tensile strain',ylabel='Tension (model units)');axes[1].set(xlabel='Constrained tensile strain',ylabel='Broken bond fraction');axes[0].legend(fontsize=8)
    finish(fig,'02b-sliding-failure','Same initial spring moduli and rupture thresholds. Hypothetical locking changes plastic mobility only; no AGE reaction is simulated.')
    data=load('plastic-memory-matrix.json');fig,axes=plt.subplots(1,2,figsize=(10,4));fig.suptitle('Plastic memory depends on loading history')
    for ax,lock in zip(axes,[0,1]):
        cases=[c for c in data['cases'] if c['parameters']['locking']==lock];amps=sorted(set(c['parameters']['amplitude'] for c in cases));holds=sorted(set(c['parameters']['holdTime'] for c in cases))
        grid=np.full((len(amps),len(holds)),np.nan)
        for c in cases:
            if c['residualStrainInterpolated'] is not None and all(p['converged'] for p in c['curve']):grid[amps.index(c['parameters']['amplitude']),holds.index(c['parameters']['holdTime'])]=c['residualStrainInterpolated']
        im=ax.imshow(grid,origin='lower',aspect='auto',cmap='viridis',vmin=0,vmax=max(amps));ax.set_xticks(range(len(holds)),holds);ax.set_yticks(range(len(amps)),amps);ax.set(xlabel='Hold time (model units)',ylabel='Peak shear strain',title='Locking = '+str(lock));fig.colorbar(im,ax=ax,label='Residual strain (interpolated)')
    finish(fig,'03-plastic-memory','Phenomenological irreversible rest-length growth. Does not resolve fibre merging or junction rebinding.')
    data=load('stiffness-percolation.json');cuts=load('targeted-damage.json');fig,axes=plt.subplots(1,2,figsize=(11,4));fig.suptitle('Stiffening and damage depend on placement')
    for n,mode in enumerate(['random','clustered']):
        cases=[c for c in data['cases'] if c['parameters']['placement']==mode];fractions=sorted(set(c['parameters']['stiffFraction'] for c in cases));ys=[]
        for f in fractions:
            vals=[c['smallShearModulus'] for c in cases if c['parameters']['stiffFraction']==f and all(p['converged'] for p in c['curve'])];ys.append(np.mean(vals) if vals else np.nan)
        axes[0].plot(fractions,ys,'o-',color=COLORS[n],label=mode)
    for n,c in enumerate(x for x in cuts['cases'] if x['parameters']['seed']==17):
        base=c['curve'][0]['Pxx'];axes[1].plot([p['control'] for p in c['curve']],[p['Pxx']/base if p['converged'] and abs(base)>1e-12 else np.nan for p in c['curve']],'o-',color=COLORS[n],label=c['parameters']['cutMode'])
    axes[0].set(xlabel='Fraction of existing bonds stiffened ×20',ylabel='Small-strain shear modulus');axes[1].set(xlabel='Fraction of initial bonds cut',ylabel='Retained tension at fixed strain');axes[0].legend();axes[1].legend()
    finish(fig,'04-stiffening-and-damage','Stiffening leaves the original graph intact; it is not by itself a rigidity-percolation transition. Cut sweep extends to 65%.')
    data=load('inclusions.json');fig,axes=plt.subplots(1,2,figsize=(11,4));fig.suptitle('Compression with explicit finite-size inclusion contacts')
    for n,c in enumerate(x for x in data['cases'] if x['parameters']['seed']==17):
        label='φ='+str(c['parameters']['areaFraction']);x=[p['control'] for p in c['curve']]
        axes[0].plot(x,[-p['Pxx'] if p['converged'] else np.nan for p in c['curve']],label=label,color=COLORS[n%6]);axes[1].plot(x,[p['contacts'] for p in c['curve']],color=COLORS[n%6])
    axes[0].set(xlabel='Uniaxial compression strain',ylabel='Compression reaction (model units)');axes[1].set(xlabel='Uniaxial compression strain',ylabel='Overlapping disk pairs');axes[0].legend(fontsize=8)
    finish(fig,'05-inclusion-compression','2D polydisperse disks at network junctions. Area fraction is not tissue cell volume fraction; no physiological jamming threshold inferred.')
    fb=load('lox-feedback.json');fig,axes=plt.subplots(1,2,figsize=(11,4));fig.suptitle('LOX feedback: equilibria, stability and hysteresis')
    for r in fb['equilibria']:
        if abs(r['coupling']-1)<1e-8:
            for e in r['equilibria']:axes[0].scatter(r['productionGain'],e['stiffness'],s=10,c=COLORS[0] if e['stable'] else COLORS[1],marker='o' if e['stable'] else 'x')
    axes[1].plot([p['g'] for p in fb['up']],[p['stiffness'] for p in fb['up']],label='Increasing gain');axes[1].plot([p['g'] for p in fb['down']],[p['stiffness'] for p in fb['down']],label='Decreasing gain');axes[1].legend()
    axes[0].set(xlabel='LOX production-gain parameter',ylabel='Equilibrium stiffness proxy',title='Teal stable; orange unstable');axes[1].set(xlabel='LOX production-gain parameter',ylabel='Dynamical stiffness proxy')
    finish(fig,'06-lox-feedback','Hypothetical normalized three-stage feedback. Multiple stable equilibria and hysteresis are checked; loop gain alone is insufficient.')
    th=load('helix-coil-sensitivity.json');fig,ax=plt.subplots(figsize=(8,4));fig.suptitle('Helix–coil sensitivity: a statistical model, not melting MD')
    for n,c in enumerate(x for x in th['cases'] if x['hypothesisHydration']==.5 and x['hypothesisCrosslink']==0):ax.plot(c['T_over_reference'],c['foldedFraction'],label='Hyp sensitivity input='+str(c['hypothesisHypFraction']),color=COLORS[n])
    ax.set(xlabel='Dimensionless temperature T / reference',ylabel='Folded-site fraction',ylim=(0,1));ax.legend()
    finish(fig,'07-helix-coil','Exact 81-site transfer matrix with assumed coefficients. No Celsius mapping, validated chemistry, or avian-versus-human prediction.')
    # Save compact data for a browser explorer; all full numerical records remain in data/.
    compact={'limitations':json.loads((root/'RESULTS.json').read_text())['limitations'],'rigidity':[],'sliding':load('sliding-memory.json')['cases'],'inclusions':load('inclusions.json')['cases'],'feedback':fb,'thermal':th}
    for g in groups:
        for c in g['cases']:
            compact['rigidity'].append({'W':g['lattice']['W'],'parameters':c['parameters'],'graph':c['graph'],'curve':[{k:v for k,v in p.items() if k!='frame'} for p in c['curve']]})
    for category in ['sliding','inclusions']:
        for c in compact[category]:
            for p in c['curve']:p.pop('frame',None)
    (root/'explorer-data.json').write_text(json.dumps(compact,allow_nan=False)+'\n')
    animate_network(load('inclusions.json'),out/'inclusion-contact.gif','Compression and finite-size inclusions',pick=lambda c:c['parameters']['seed']==17 and c['parameters']['areaFraction']==.75)
    animate_network(load('sliding-memory.json'),out/'sliding-memory.gif','Load, hold and unload: sliding surrogate',pick=lambda c:c['parameters']['seed']==17 and c['parameters']['locking']==0)


def animate_network(data,path,title,pick):
    case=next(c for c in data['cases'] if pick(c));frames=[p for p in case['curve'] if 'frame' in p];lat=data['lattice'];edges=np.array(lat['edges']);shift=np.array(lat['imageShifts']);L=np.sqrt(lat['area']*2/math.sqrt(3));fig,ax=plt.subplots(figsize=(6,5));W=lat['W']
    def draw(index):
        ax.clear();p=frames[index];xy=np.array(p['frame']['coordinates']);alive=p['frame']['alive'];ax.set_aspect('equal');ax.set_xlim(-.6,W*1.7);ax.set_ylim(-.6,W*1.05)
        for k,(i,j) in enumerate(edges):
            if alive[k] and np.linalg.norm(shift[k])<1e-8:ax.plot(xy[[i,j],0],xy[[i,j],1],color='#007f86',lw=1,alpha=.65)
        if 'radii' in case:
            for center,r in zip(xy,case['radii']):ax.add_patch(plt.Circle(center,r,fc='#dfab45',ec='#885c10',alpha=.4))
        ax.scatter(xy[:,0],xy[:,1],s=6,c='#233645');ax.set_title(title+'\n'+p['stage']+' • control='+format(p['control'],'.3f')+' • '+('converged' if p['converged'] else 'UNCONVERGED'))
        ax.set_xlabel('Dimensionless x; periodic crossing edges omitted');ax.set_ylabel('Dimensionless y')
        return []
    ani=FuncAnimation(fig,draw,frames=len(frames),interval=180);ani.save(path,writer=PillowWriter(fps=6));plt.close(fig)

if __name__=='__main__':render(sys.argv[1])
