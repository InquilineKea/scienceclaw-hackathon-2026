"""Original analysis and publication figures; executed only in the reviewed remote image."""
import json,gzip,csv,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter
from matplotlib.collections import LineCollection
from matplotlib.tri import Triangulation


def generate(out):
 d=json.loads((out/'results.json').read_text());rows=d['rows'];lookup={(r['n'],r['family'],r['seed'],r['pattern'],r['damaged'],r['direction'],r['omega'],r['model'],r['level'],r['permeability']):r for r in rows}
 def get(c,damaged,dr,w,model,level=None,k=None):return lookup[(*c,damaged,dr,w,model,level,k)]
 previous=json.loads(gzip.decompress(Path(__file__).with_name('baseline.json.gz').read_bytes()))['results'];matches=[]
 for c in previous:
  for old in c['rows']:
   new=get((c['n'],c['family'],c['seed'],c['pattern']),old['damaged'],old['direction'],old['omega'],'drag')
   if old['residual']<1e-7 and new['resolved']:
    for key in ['selfAmplitude','farRms']:matches.append(abs(new[key]-old[key])/max(abs(old[key]),1e-12))
 assert matches and max(matches)<1e-5,('Uniform-drag replay mismatch',max(matches))
 comparisons=[];cases=sorted(set((r['n'],r['family'],r['seed'],r['pattern']) for r in rows))
 for c in cases:
  for dr in [0,1]:
   for w in [.03,.1,.3,1,3]:
    for k in [.001,.1]:
     b0=get(c,False,dr,w,'drag');b1=get(c,True,dr,w,'drag')
     for metric in ['selfAmplitude','farRms']:
      fine0=get(c,False,dr,w,'poro',2,k);fine1=get(c,True,dr,w,'poro',2,k);coarse0=get(c,False,dr,w,'poro',1,k);coarse1=get(c,True,dr,w,'poro',1,k)
      valid=all(r['resolved'] for r in [b0,b1,fine0,fine1,coarse0,coarse1])
      fr=fine1.get(metric,0)/fine0[metric] if valid and fine0[metric]>0 else None;cr=coarse1.get(metric,0)/coarse0[metric] if valid and coarse0[metric]>0 else None
      mesh=max(abs(fine0[metric]-coarse0[metric])/max(abs(fine0[metric]),abs(coarse0[metric]),1e-15),abs(fine1[metric]-coarse1[metric])/max(abs(fine1[metric]),abs(coarse1[metric]),1e-15)) if valid else None
      delta_pp=100*abs(fr-cr) if valid else None
      comparisons.append({'n':c[0],'family':c[1],'seed':c[2],'pattern':c[3],'direction':dr,'omega':w,'permeability':k,'metric':metric,'poroDamageRatio':fr,'dragDamageRatio':b1[metric]/b0[metric] if b0['resolved'] and b1['resolved'] else None,'meshRelative':mesh,'meshDamageDifferencePP':delta_pp,'resolved':bool(valid and mesh<=.05 and delta_pp<=.5)})
 with (out/'comparisons.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(comparisons[0]),lineterminator='\n');w.writeheader();w.writerows(comparisons)
 (out/'comparisons.json').write_text(json.dumps(comparisons))
 summary=[]
 for n in [10,14]:
  for family in ['isotropic','modular']:
   for pattern in ['distributed','clustered']:
    for k in [.001,.1]:
     for metric in ['selfAmplitude','farRms']:
      rr=[r for r in comparisons if r['n']==n and r['family']==family and r['pattern']==pattern and r['omega']==.1 and r['permeability']==k and r['metric']==metric]
      seedmeans=[];dragmeans=[]
      for seed in [17,29,43,67,83]:
       vv=[r for r in rr if r['seed']==seed and r['resolved']]
       if len(vv)==2:seedmeans.append(float(np.mean([r['poroDamageRatio'] for r in vv])));dragmeans.append(float(np.mean([r['dragDamageRatio'] for r in vv])))
      summary.append({'n':n,'family':family,'pattern':pattern,'permeability':k,'metric':metric,'resolvedDirectionPairs':sum(r['resolved'] for r in rr),'seedsBothDirections':len(seedmeans),'poroMean':float(np.mean(seedmeans)) if seedmeans else None,'poroRange':[min(seedmeans),max(seedmeans)] if seedmeans else None,'matchedDragMean':float(np.mean(dragmeans)) if dragmeans else None})
 (out/'summary.json').write_text(json.dumps(summary,indent=2))
 checks=[v for c in d['records'] for v in c['operatorChecks']];controls=[v for c in d['records'] for v in c['couplingChecks']]
 validation={'versions':d['versions'],'records':len(d['records']),'systems':len(rows),'resolvedSystems':sum(r['resolved'] for r in rows),'maxResolvedResidual':max(r['residual'] for r in rows if r['resolved']),'dragBaselineMaxRelative':max(matches),'maxAlphaZeroDeviation':max(r['alphaZeroDeviation'] for r in controls),'maxAffineDivergenceRelative':max(r['affineDivergenceRelative'] for r in checks),'maxDarcyRefinementRatio':max(c['operatorChecks'][1]['darcyManufacturedL2']/c['operatorChecks'][0]['darcyManufacturedL2'] for c in d['records']),'comparisonCount':len(comparisons),'resolvedMeshComparisons':sum(r['resolved'] for r in comparisons),'maxResponseMeshRelative':max(r['meshRelative'] for r in comparisons if r['meshRelative'] is not None),'elapsedSeconds':d['seconds']}
 (out/'validation.json').write_text(json.dumps(validation,indent=2))
 plt.rcParams.update({'font.size':11,'figure.facecolor':'#faf8f0','axes.facecolor':'#faf8f0','savefig.facecolor':'#faf8f0'})
 for metric,label,filename in [('selfAmplitude','Local compliance magnitude','local-poro-vs-drag'),('farRms','Remote RMS displacement','remote-poro-vs-drag')]:
  fig,axs=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
  for ax,(family,pattern) in zip(axs.flat,[(f,p) for f in ['isotropic','modular'] for p in ['distributed','clustered']]):
   for model,col in [('drag','#777777'),('poro','#26725a')]:
    for damaged,ls in [(False,'-'),(True,'--')]:
     xs=[.03,.1,.3,1,3];yy=[]
     for freq in xs:
      rr=[r for r in rows if r['n']==14 and r['family']==family and r['pattern']==pattern and r['model']==model and r['damaged']==damaged and r['omega']==freq and r['resolved'] and (model=='drag' or r['level']==2 and r['permeability']==.001)]
      yy.append(np.mean([r[metric] for r in rr]) if rr else np.nan)
     ax.loglog(xs,yy,ls,color=col,marker='o',label=f'{model}, '+('damaged' if damaged else 'intact'))
   ax.set_title(('Disordered' if family=='isotropic' else 'Modular')+' / '+pattern);ax.set_xlabel('Dimensionless frequency Ω');ax.set_ylabel(label+' (normalized)');ax.grid(alpha=.2);ax.legend(fontsize=8)
  fig.suptitle(label+': matched solid, added fluid coupling\n196 nodes; five seeds × x/y drive; α=1, storage=0.1, mobility=0.001; drained boundary',fontsize=14)
  fig.savefig(out/(filename+'.png'),dpi=160);fig.savefig(out/(filename+'.svg'));plt.close(fig)
 # Direct damage-ratio comparison, showing mesh-qualified seed means.
 fig,axs=plt.subplots(1,2,figsize=(12,5),constrained_layout=True)
 for ax,metric,title in zip(axs,['selfAmplitude','farRms'],['Local damage response','Remote damage response']):
  rr=[r for r in summary if r['n']==14 and r['metric']==metric and r['permeability']==.001]
  for i,r in enumerate(rr):
   if r['poroMean'] is None:continue
   mean=100*(r['poroMean']-1);lo,hi=[100*(v-1) for v in r['poroRange']];ax.errorbar(i-.1,mean,yerr=[[mean-lo],[hi-mean]],fmt='o',color='#26725a',capsize=4);ax.plot(i+.1,100*(r['matchedDragMean']-1),'s',color='#777777')
   ax.text(i,hi+.3,f"n={r['seedsBothDirections']}",ha='center',fontsize=9)
  ax.axhline(0,color='#aaa',lw=1);ax.set_xticks(range(4),['Disordered\ndistributed','Disordered\nclustered','Modular\ndistributed','Modular\nclustered'],fontsize=9);ax.set_title(title);ax.set_ylabel('Damaged/intact change (%)');ax.grid(axis='y',alpha=.2)
 fig.suptitle('Added fluid coupling can change the effect of the same three-fiber lesion\nΩ=0.1; green: poroelastic mean/range; gray: matched uniform-drag mean; ranges are not confidence intervals',fontsize=12)
 fig.savefig(out/'damage-comparison.png',dpi=160);plt.close(fig)
 animations=json.loads((out/'animation.json').read_text())
 for difference,name in [(False,'poro-versus-drag-motion'),(True,'poro-damage-change')]:
  fig,axs=plt.subplots(2,2,figsize=(10,9),constrained_layout=True);artists=[];pmax=0.;umax=0.
  for c in animations:
   ff=c['fields'];pd=next(f for f in ff if f['model']=='poro' and f['damaged']);pi=next(f for f in ff if f['model']=='poro' and not f['damaged']);bd=next(f for f in ff if f['model']=='drag' and f['damaged'])
   pp=np.array(pd['pressureReal'])+1j*np.array(pd['pressureImag']);uu=np.array(pd['real'])+1j*np.array(pd['imag']);bb=np.array((pi if difference else bd)['real'])+1j*np.array((pi if difference else bd)['imag'])
   if difference:pp-=np.array(pi['pressureReal'])+1j*np.array(pi['pressureImag']);uu-=bb
   pmax=max(pmax,float(np.max(np.abs(pp))));umax=max(umax,float(np.max(np.abs(uu))),float(np.max(np.abs(bb))) if not difference else 0.)
  for ax,c in zip(axs.flat,animations):
   ff=c['fields'];pd=next(f for f in ff if f['model']=='poro' and f['damaged']);pi=next(f for f in ff if f['model']=='poro' and not f['damaged']);bd=next(f for f in ff if f['model']=='drag' and f['damaged']);X=np.array(c['X']).reshape(-1,2);free=np.array(c['free']);nodes=free[::2]//2
   pp=np.array(pd['pressureReal'])+1j*np.array(pd['pressureImag']);uu=np.array(pd['real'])+1j*np.array(pd['imag']);bb=np.array((pi if difference else bd)['real'])+1j*np.array((pi if difference else bd)['imag'])
   if difference:pp-=np.array(pi['pressureReal'])+1j*np.array(pi['pressureImag']);uu-=bb
   pts=np.array(pd['pressurePoints']);tri=np.array(pd['pressureCells']);t=Triangulation(pts[:,0],pts[:,1],tri);field=ax.tripcolor(t,np.zeros(len(tri)),vmin=-pmax,vmax=pmax,cmap='RdBu_r',shading='flat',alpha=.6)
   ax.add_collection(LineCollection([[X[e['i']],X[e['j']]] for e in c['edges']],colors='#bbbbbb',linewidths=.4));ax.add_collection(LineCollection([[X[c['edges'][i]['i']],X[c['edges'][i]['j']]] for i in c['lesion']],colors='#a11a1a',linewidths=1.8,linestyles='dashed'))
   q=ax.quiver(X[nodes,0],X[nodes,1],np.zeros(len(nodes)),np.zeros(len(nodes)),color='#17583d',scale_units='xy',angles='xy',scale=umax/.16,width=.004)
   qb=None
   if not difference:qb=ax.quiver(X[nodes,0],X[nodes,1],np.zeros(len(nodes)),np.zeros(len(nodes)),color='#777777',scale_units='xy',angles='xy',scale=umax/.16,width=.002)
   ax.scatter(X[c['probe'],0],X[c['probe'],1],s=12,c='#d58610');ax.set_aspect('equal');ax.set_title(('Disordered' if c['family']=='isotropic' else 'Modular')+' / '+c['pattern']);ax.set_xticks([]);ax.set_yticks([]);artists.append((field,q,qb,pp,uu,bb,tri))
  fig.colorbar(artists[0][0],ax=list(axs.flat),label=('Damage-induced pressure change' if difference else 'Damaged poroelastic pressure')+' (normalized)',shrink=.65)
  title=fig.suptitle('');fig.supxlabel('196 nodes; seed 17; x drive; Ω=0.1; mobility 0.001. Shared pressure/vector scales; arrows enlarged.\n'+('Green: damaged−intact poroelastic displacement. Red dashed: three cut fibers.' if difference else 'Green: poroelastic; gray: uniform drag, both damaged. Red dashed: three cut fibers.'),fontsize=10)
  def update(i, artists=artists, title=title, difference=difference):
   phase=2*np.pi*i/40;z=np.exp(1j*phase)
   for field,q,qb,pp,uu,bb,tri in artists:
    field.set_array(np.mean((pp*z).real[tri],axis=1));v=(uu*z).real.reshape(-1,2);q.set_UVC(v[:,0],v[:,1])
    if qb is not None:v=(bb*z).real.reshape(-1,2);qb.set_UVC(v[:,0],v[:,1])
   title.set_text(('Poroelastic damage-induced change' if difference else 'Matched uniform drag versus added Biot fluid coupling')+f'\nPhase {phase:.2f} radians; harmonic reconstruction')
   return []
  update(8);fig.savefig(out/(name+'-still.png'),dpi=140);FuncAnimation(fig,update,frames=41,interval=100).save(out/(name+'.gif'),writer=PillowWriter(fps=10),dpi=100);plt.close(fig)
 files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.iterdir() if p.is_file() and p.name not in ['partial.json','MANIFEST.json']}
 (out/'MANIFEST.json').write_text(json.dumps({'files':files},indent=2))
 print(json.dumps(validation),flush=True)
