"""Original stdlib diagnostics of residual orientation/length differences."""
import json,math,statistics
from pathlib import Path
P=Path(__file__).parent;models=json.loads((P/'models.json').read_text());rows=[]
for m in models:
 if m['pattern']=='baseline':continue
 locked=set(m['locked']);vectors=[];lengths=[];edgeids=[];base=.001*m['mean']
 for k,(a,b,sg) in enumerate(m['a']):
  if m['active'][a] and m['active'][b] and m['aw'][k]>base*1.1:
   for e in [a,b]:
    length=m['rest'][e];v=[x/length for x in m['v'][e]];vectors.append(v);lengths.append(length);edgeids.append(e)
 tensor=[[sum(v[i]*v[j] for v in vectors)/len(vectors) for j in range(3)] for i in range(3)]
 rows.append(dict(seed=m['seed'],density=m['density'],pattern=m['pattern'],selected_junctions=len(locked),locked_angle_arms=len(vectors),unique_incident_segments=len(set(edgeids)),orientation_second_moment=tensor,arm_weighted_mean_segment_length=statistics.fmean(lengths),arm_weighted_median_segment_length=statistics.median(lengths),periodic_mean_squared_distance_to_cluster_center=m['lock_spread']))
pairs=[]
for seed in [29,30,31,32]:
 for den in [.15,.3]:
  c=next(x for x in rows if (x['seed'],x['density'],x['pattern'])==(seed,den,'clustered'));d=next(x for x in rows if (x['seed'],x['density'],x['pattern'])==(seed,den,'distributed'))
  pairs.append(dict(seed=seed,density=den,orientation_tensor_Frobenius_difference=math.sqrt(sum((c['orientation_second_moment'][i][j]-d['orientation_second_moment'][i][j])**2 for i in range(3) for j in range(3))),mean_length_ratio_clustered_over_distributed=c['arm_weighted_mean_segment_length']/d['arm_weighted_mean_segment_length']))
out=dict(rows=rows,pairs=pairs,scope='Degree and angular budget matched; local orientation and segment-length correlations are diagnostics, not held fixed. One paired placement draw per seed; no claim of placement-only causality.')
(P/'placement-geometry-diagnostics.json').write_text(json.dumps(out,indent=2));print(json.dumps(pairs,indent=2))
