from pathlib import Path
import json,random,csv,statistics,hashlib
p=Path('results.json');d=json.loads(p.read_text());rows=d['rows'];metrics=['participation','maxShare','spread','patch'];summary=[]
for r in rows:
 for k in ['spread','patch']:
  if r['damageAtSample'] is None or r['coarse']['damageAtSample'] is None or r['damageAtSample']>.15 or r['coarse']['damageAtSample']>.15:r['unresolved'][k]=True
for family in ['isotropic','modular']:
 for k in metrics:
  diffs=[];means=[];coverage=[]
  for seed in d['seeds']:
   vals=[]
   for angle in d['angles']:
    a=next(r for r in rows if r['family']==family and r['seed']==seed and r['angle']==angle and r['pattern']=='distributed');b=next(r for r in rows if r['family']==family and r['seed']==seed and r['angle']==angle and r['pattern']=='clustered')
    if not a['unresolved'][k] and not b['unresolved'][k]:vals.append(b[k]-a[k]);diffs.append(b[k]-a[k])
   coverage.append(len(vals))
   if len(vals)>=6:means.append(statistics.mean(vals))
  rng=random.Random(20261031);boot=sorted(statistics.mean(rng.choices(means,k=len(means))) for _ in range(10000)) if means else []
  mean=statistics.mean(means) if means else None
  summary.append(dict(family=family,metric=k,meanDelta=mean,ci=[boot[249],boot[9749]] if boot else None,resolvedPairs=len(diffs),totalPairs=120,seeds=len(means),anglesPerSeed=coverage,positivePairs=sum(v>0 for v in diffs),negativePairs=sum(v<0 for v in diffs),positiveSeedMeans=sum(v>0 for v in means),negativeSeedMeans=sum(v<0 for v in means)))
d['rows']=rows;Path('checked-results.json').write_text(json.dumps(d,separators=(',',':'))+'\n');Path('summary.json').write_text(json.dumps(summary,indent=2)+'\n')
keys=['family','seed','angle','pattern','participation','maxShare','spread','patch','damageAtSample','strainAtDamage']
with Path('results.csv').open('w') as f:
 w=csv.writer(f);w.writerow(keys+[k+'Unresolved' for k in metrics]);w.writerows([[r[k] for k in keys]+[r['unresolved'][k] for k in metrics] for r in rows])
labels={'participation':'Effective load-bearing fiber fraction','maxShare':'Largest single-fiber force share','spread':'Damage radius / domain diagonal','patch':'Largest connected damage patch fraction'}
tr=''
for s in summary:
 fmt=lambda v:f'{100*v:+.2f}'
 tr+=f"<tr><th>{s['family']} · {labels[s['metric']]}</th><td>{fmt(s['meanDelta']) if s['meanDelta'] is not None else 'unresolved'}</td><td>{' to '.join(fmt(v) for v in s['ci']) if s['ci'] else '—'}</td><td>{s['resolvedPairs']}/120</td><td>{s['seeds']}/10</td><td>{s['positivePairs']} / {s['negativePairs']}</td></tr>"
Path('table.html').write_text('<table><thead><tr><th>Architecture / metric</th><th>Clustered − distributed (×100)</th><th>95% seed-bootstrap interval</th><th>Resolved pairs</th><th>Seeds ≥6 angles</th><th>Positive / negative angle pairs</th></tr></thead><tbody>'+tr+'</tbody></table>')
print(json.dumps(summary,indent=2))
