"""Event-resolved follow-up to the preserved finite-increment diagnostic sweep."""
import sys,json,time,csv,math
from pathlib import Path
# Only the newly authored sibling implementation is loaded; never repository code.
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compare import geometry,solve,damage_set,FAMILIES,references

def event_sim(g,pattern,mode,tol):
 removed=damage_set(g,pattern);active=set(range(len(g['edges'])))-set(removed);eps=0.;work=0.;diss=0.;frames=[];curve=[];logs=[];worst=0.;initial=None;failure=None;peak=0.;lastk=None
 while True:
  u,s,k,r,it=solve(g,sorted(active),mode,tol);worst=max(worst,r);logs.append({'strain':eps,'residual':r,'iterations':it,'active':len(active)})
  if r>1e-7 or not math.isfinite(r):return {'status':'solver_failed','solves':logs,'frames':frames,'curve':curve,'work':work,'max_residual':worst}
  if initial is None:initial=k
  if lastk is not None:diss+=max(0.,.5*(lastk-k)*eps*eps)
  broken=[i for i in active if abs(s[i])*eps>=g['edges'][i]['threshold']*(1-1e-10)]
  if broken:
   peak=max(peak,k*eps);lastk=k;active.difference_update(broken);continue
  elastic=.5*k*eps*eps
  curve.append({'strain':eps,'force_after':k*eps,'force_before':lastk*eps if lastk is not None else k*eps,'work_exact':work,'elastic_energy':elastic,'released_energy':diss,'energy_balance_abs':abs(work-elastic-diss),'stiffness':k,'residual':r,'broken_count':len(g['edges'])-len(active)})
  frames.append({'strain':eps,'displacement':[v*eps for v in u],'active':sorted(active)})
  if eps>0 and k<.1*initial:failure=eps;break
  if eps>=.24:break
  next_event=min([g['edges'][i]['threshold']/abs(s[i]) for i in active if abs(s[i])>1e-14]+[.24]);next_event=min(.24,max(next_event,eps+1e-12));work+=.5*k*(next_event**2-eps**2);peak=max(peak,k*next_event);eps=next_event;lastk=k
 return {'status':'completed','initial_stiffness':initial,'failure_strain':failure,'censored':failure is None,'work':work,'peak_force':peak,'max_residual':worst,'max_energy_balance_abs':max(q['energy_balance_abs'] for q in curve),'removed':removed,'removed_volume':sum(g['edges'][i]['volume'] for i in removed),'curve':curve,'frames':frames,'solves':logs}

def main():
 out=Path(sys.argv[1]);out.mkdir(exist_ok=False);(out/'raw').mkdir();(out/'geometry').mkdir();start=time.time();summary=[];checks=[]
 (out/'config.json').write_text(json.dumps({'seeds':list(range(101,111)),'families':FAMILIES,'loading':['tension','shear'],'damage':['intact','clustered','distributed'],'tolerance':1e-10,'control_tolerance':1e-12,'max_strain':.24,'failure':'remaining stiffness <10% of pattern initial stiffness','integration':'exact elastic integral between resolved break events','normalization':'equal material and matched intact axial K; shared trajectories by exact linear scaling'},indent=2));(out/'reference-checks.json').write_text(json.dumps(references(),indent=2))
 for family in FAMILIES:
  for seed in range(101,111):
   g=geometry(family,seed);(out/'geometry'/f'{family}-{seed}.json').write_text(json.dumps(g));_,_,K,_,_=solve(g,list(range(len(g['edges']))),'tension',1e-12)
   for pat in ['intact','clustered','distributed']:
    for mode in ['tension','shear']:
     ident=f'{family}-{seed}-{pat}-{mode}';r=event_sim(g,pat,mode,1e-10);(out/'raw'/f'{ident}.json').write_text(json.dumps(r))
     if seed==101:
      c=event_sim(g,pat,mode,1e-12);(out/'raw'/f'{ident}-tight.json').write_text(json.dumps(c));checks.append({'id':ident,'status':c['status'],'relative_work_difference':abs(c['work']-r['work'])/max(c['work'],1e-15),'censoring_changed':c.get('censored')!=r.get('censored')})
     for norm,scale in [('equal_budget',1.),('matched_tension_K',1/K)]:summary.append({'case_id':ident+'-'+norm,'raw_id':ident,'family':family,'seed':seed,'pattern':pat,'loading':mode,'refinement':'event','normalization':norm,'material_scale':scale,'intact_tension_K':K*scale,'status':r['status'],'work':r['work']*scale,'peak_force':r.get('peak_force',0)*scale,'initial_K':r.get('initial_stiffness',0)*scale,'failure_strain':r.get('failure_strain'),'censored':r.get('censored',True),'max_residual':r['max_residual'],'removed_volume':r.get('removed_volume'),'max_energy_balance_abs':r.get('max_energy_balance_abs')})
   print(json.dumps({'family':family,'seed':seed,'cases':len(summary),'elapsed_seconds':time.time()-start}),flush=True)
 (out/'summary.json').write_text(json.dumps(summary));(out/'tolerance-checks.json').write_text(json.dumps(checks,indent=2))
 with (out/'summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 (out/'execution.json').write_text(json.dumps({'elapsed_seconds':time.time()-start,'raw_cases':180,'additional_tight_checks':18,'normalization_rows':len(summary),'cloud_cost_usd':0,'max_relative_work_tolerance_difference':max(r['relative_work_difference'] for r in checks)},indent=2))
if __name__=='__main__':main()
