import csv,json,collections,statistics,random
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def pairs(path):
 d=collections.defaultdict(lambda:collections.defaultdict(dict))
 for r in csv.DictReader(path.open()):
  r={k:float(v) for k,v in r.items()};key=tuple(r[k] for k in ['density','bending','contrast','law','tau_ratio','cell']);d[key][int(r['seed'])][int(r['architecture'])]=r
 out={}
 for k,g in d.items():out[k]={s:2*(v[1]['hold_auc']-v[0]['hold_auc'])/(v[1]['hold_auc']+v[0]['hold_auc']) for s,v in g.items() if 0 in v and 1 in v}
 return out
a=pairs(root/'main-results.csv');b=pairs(root/'embedded-check/embedded-results.csv');result=[]
for k,values in b.items():
 common=sorted(set(a[k])&set(values));diff=[values[s]-a[k][s] for s in common];rng=random.Random(91011);boots=sorted(statistics.mean(rng.choice(diff) for _ in diff) for _ in range(4000));result.append(dict(zip(['density','bending','contrast','law','tau_ratio','cell'],k),n_common_seeds=len(common),main_common_mean=statistics.mean(a[k][s] for s in common),embedded_common_mean=statistics.mean(values[s] for s in common),mean_change=statistics.mean(diff),change_bootstrap_low=boots[99],change_bootstrap_high=boots[3899]))
summary={'scope':'Exploratory nested-core boundary diagnostic. Same core nodes, retained edges and selected-edge identities. Added unmodified surrounding matrix; initial shear re-matched. Common accepted seeds only. This tests embedding and boundary distance together, not pure parameter identification.','histories':sum(1 for _ in csv.DictReader((root/'embedded-check/embedded-results.csv').open())),'excluded_graph_blocks':list(csv.DictReader((root/'embedded-check/embedded-failures.csv').open())),'comparisons':result};(root/'embedded-check/summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
