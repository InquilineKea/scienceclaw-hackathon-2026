"""Original stdlib-only paired analysis; no imported scientific packages."""
import csv,json,statistics,random,math,collections,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDS=['side','density','bending','contrast','law','tau_ratio','cell']
METRICS=['hold_auc','ramp_force','hold_end_force','max_ramp_force','ramp_CV','retention','residual_force','dissipation']
def load(path):
 rows=[]
 for r in csv.DictReader(path.open()):
  rows.append({k:float(v) for k,v in r.items()})
 return rows
def contrast(a,b):return 2*(b-a)/(abs(a)+abs(b)) if abs(a)+abs(b)>1e-15 else 0.
def bootstrap(values,key):
 rng=random.Random(81271+int(hashlib.sha256(repr(key).encode()).hexdigest()[:8],16));n=len(values);boots=sorted(sum(rng.choice(values) for _ in values)/n for _ in range(4000));return boots[99],boots[3899]
def summarize(rows,metrics=METRICS):
 groups=collections.defaultdict(lambda:collections.defaultdict(dict))
 for r in rows:groups[tuple(r[k] for k in FIELDS)][int(r['seed'])][int(r['architecture'])]=r
 out=[]
 for key,seeds in groups.items():
  pairs=[(seed,d[0],d[1]) for seed,d in sorted(seeds.items()) if 0 in d and 1 in d]
  for metric in metrics:
   vals=[contrast(a[metric],b[metric]) for _,a,b in pairs]
   if not vals:continue
   lo,hi=bootstrap(vals,(key,metric));mean=statistics.mean(vals)
   out.append(dict(zip(FIELDS,key),metric=metric,n_pairs=len(vals),uniform_mean=statistics.mean(a[metric] for _,a,b in pairs),clustered_mean=statistics.mean(b[metric] for _,a,b in pairs),mean_contrast=mean,bootstrap_low=lo,bootstrap_high=hi,positive_seed_fraction=sum(x>1e-8 for x in vals)/len(vals),direction='positive' if lo>1e-6 else 'negative' if hi< -1e-6 else 'unresolved',small_mean=abs(mean)<.05,seed_values=[{'seed':s,'contrast':v} for (s,_,_),v in zip(pairs,vals)]))
 return out
rows=load(ROOT/'main-results.csv');assert len(rows)==5520,('unexpected main sweep count',len(rows)); exclusions=list(csv.DictReader((ROOT/'main-failures.csv').open())); assert len(exclusions)==2;summ=summarize(rows)
primary=[r for r in summ if r['metric']=='hold_auc'];counts=dict(collections.Counter(r['direction'] for r in primary));coverage={'scenarios':len(primary),'paired_network_histories':len(rows)//2,'histories':len(rows),'attempted_histories':5760,'excluded_graph_blocks':exclusions,'directions':counts,'small_mean_scenarios':sum(r['small_mean'] for r in primary),'minimum_pairs':min(r['n_pairs'] for r in primary),'maximum_pairs':max(r['n_pairs'] for r in primary)}
# Counterfactual range across parameter values at otherwise matched design settings.
leverage=[]
for factor in ['law','tau_ratio','contrast','bending','cell','density']:
 keys=[k for k in FIELDS if k!=factor];groups=collections.defaultdict(list)
 for r in primary:
  if r['law']==0 and factor in ['law','tau_ratio']:continue
  groups[tuple(r[k] for k in keys)].append(r)
 ranges=[]
 for g in groups.values():
  if len({r[factor] for r in g})<2:continue
  ranges.append(max(r['mean_contrast'] for r in g)-min(r['mean_contrast'] for r in g))
 leverage.append({'factor':factor,'matched_blocks':len(ranges),'median_contrast_range':statistics.median(ranges),'mean_contrast_range':statistics.mean(ranges),'maximum_contrast_range':max(ranges)})
leverage.sort(key=lambda r:r['mean_contrast_range'],reverse=True)
# Look for resolved sign reversals from changing a law or time ratio alone.
reversals=[]
for factor in ['law','tau_ratio']:
 keys=[k for k in FIELDS if k!=factor];groups=collections.defaultdict(list)
 for r in primary:
  if r['law']==0:continue
  groups[tuple(r[k] for k in keys)].append(r)
 for key,g in groups.items():
  pos=[r for r in g if r['direction']=='positive'];neg=[r for r in g if r['direction']=='negative']
  if pos and neg:reversals.append({'changed_factor':factor,'held_fixed':dict(zip(keys,key)),'positive':max(pos,key=lambda r:r['mean_contrast']),'negative':min(neg,key=lambda r:r['mean_contrast'])})
# Exact invariance when the selected label changes no mechanical coefficient.
null=[r for r in primary if r['contrast']==1 and r['tau_ratio']==1];nullerr=max(abs(v['contrast']) for r in null for v in r['seed_values']);assert nullerr<1e-8
checks={'main_count':len(rows),'all_finite':all(math.isfinite(v) for r in rows for v in r.values()),'maximum_equilibrium_residual':max(r['equilibrium_residual'] for r in rows),'maximum_force_balance_error':max(r['force_balance'] for r in rows),'maximum_relative_shear_matching_error':max(abs(r['shear_matched']/r['shear_reference']-1) for r in rows),'selection_null_max_absolute_contrast':nullerr,'minimum_dissipation':min(r['dissipation'] for r in rows),'max_Newton_iterations':max(r['max_Newton_iterations'] for r in rows)}
assert checks['all_finite'] and checks['maximum_equilibrium_residual']<1e-9 and checks['maximum_force_balance_error']<1e-7
refinements={}
for tag,path in [('timestep',ROOT/'timestep-check/timestep-results.csv'),('domain',ROOT/'domain-check/domain-results.csv')]:
 other=load(path);assert len(other)==308,(tag,'incomplete',len(other));ss=summarize(other,['hold_auc']);refinements[tag]={'histories':len(other),'summary':ss}
 if tag=='timestep':
  orig={(int(r['seed']),r['density'],r['bending'],r['contrast'],r['law'],r['tau_ratio'],r['cell'],r['architecture']):r for r in rows};errors=[];contrast_errors=[]
  for r in other:
   key=(int(r['seed']),r['density'],r['bending'],r['contrast'],r['law'],r['tau_ratio'],r['cell'],r['architecture']);a=orig[key];errors.append(abs(r['hold_auc']/a['hold_auc']-1))
  for s in ss:
   a=next(r for r in primary if all(r[k]==s[k] for k in FIELDS));contrast_errors.append(abs(s['mean_contrast']-a['mean_contrast']))
  refinements[tag].update({'median_relative_hold_auc_change':statistics.median(errors),'max_relative_hold_auc_change':max(errors),'max_change_in_mean_paired_contrast':max(contrast_errors)})
 else:
  comparisons=[]
  for s in ss:
   a=next(r for r in primary if all(r[k]==s[k] for k in FIELDS if k!='side'));comparisons.append({'law':s['law'],'tau_ratio':s['tau_ratio'],'cell':s['cell'],'main_mean':a['mean_contrast'],'larger_domain_mean':s['mean_contrast'],'main_direction':a['direction'],'larger_domain_direction':s['direction']})
  refinements[tag]['comparisons']=comparisons
summary={'scope':'Dimensionless screening, not validated collagen/adhesion predictions. Pointwise paired geometry-seed intervals; no biological uncertainty or calibrated parameter prior.','coverage':coverage,'primary_metric':'hold_auc','leverage':leverage,'resolved_single_factor_sign_reversals':reversals,'checks':checks,'refinements':refinements,'scenario_results':summ}
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
with (ROOT/'paired-contrasts.csv').open('w') as f:
 fields=[k for k in summ[0] if k!='seed_values'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in summ)
print(json.dumps({'coverage':coverage,'leverage':leverage,'sign_reversal_count':len(reversals),'checks':checks,'timestep':{k:v for k,v in refinements['timestep'].items() if k!='summary'},'domain_comparisons':refinements['domain']['comparisons']},indent=2))
