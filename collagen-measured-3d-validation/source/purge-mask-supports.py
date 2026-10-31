"""Original pre-outcome correction: exact nonoverlap of axis-aligned35µm PIV supports."""
from pathlib import Path
import json,math,itertools,hashlib
P=Path(__file__).parent
for specimen in ['Pos004','Pos007','Pos008']:
 p=P/'data'/specimen/'frozen-mask.json';m=json.loads(p.read_text());g=json.loads((P/'data'/specimen/'geometry.json').read_text());nodes=[[v*1e6 for v in n] for n in g['nodes']];buckets={}
 for n,fixed in zip(nodes,m['boundary']):
  if fixed:buckets.setdefault(tuple(math.floor(v/35) for v in n),[]).append(n)
 original=list(m['score']);purged=[]
 for n,eligible in zip(nodes,original):
  overlap=False
  if eligible:
   key=[math.floor(v/35) for v in n]
   for shift in itertools.product([-1,0,1],repeat=3):
    for q in buckets.get(tuple(key[d]+shift[d] for d in range(3)),[]):
     if all(abs(n[d]-q[d])<35+1e-8 for d in range(3)):overlap=True;break
    if overlap:break
  purged.append(eligible and not overlap)
 m['score']=purged;m['piv_support_guard']='Score nodes are excluded if any prescribed node differs by<35µm on ALL axes; exact axis-aligned interrogation-support nonoverlap, applied before outcomes. Original radial/outer35µm guards also retained.';m['counts']['pre_support_purge_score_nodes']=sum(original);m['counts']['reference_eligible_score_nodes']=sum(purged);m['counts']['octants']=[sum(s and sum((n[d]>0)<<d for d in range(3))==k for n,s in zip(nodes,purged)) for k in range(8)];assert sum(purged)>=200 and sum(v>=20 for v in m['counts']['octants'])>=4;m['mask_frozen_before_outcome_inspection']=True;p.write_text(json.dumps(m,separators=(',',':')));print(specimen,m['counts'])
