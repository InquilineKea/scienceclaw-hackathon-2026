from pathlib import Path
import json,shutil
G=Path(__file__).resolve().parent/'candidate/collagen-studies'
p=G/'data/rigidity-audit.json';d=json.loads(p.read_text());rows=[]
for case in d['spectra']:
 for boundary in ['constrained','unconstrained']:
  spec=case.get(boundary,{})
  for i,v in enumerate(spec.get('eigenvalues',[])):
   rows.append({'case_id':case['case_id'],'family':case['family'],'architecture':case['architecture'],'accepted':case['accepted'],'boundary':boundary,'mode_index':i,'signed_eigenvalue':v,'zero_tolerance':spec['eigenvalue_tolerance'],'scope':spec['scope']})
d['tables'].append({'id':'signed-eigenspectra','title':'Full signed Hessian spectra · filter one case before connecting modes','columns':list(rows[0]),'rows':rows,'qualification':{'field':'accepted','passValues':[True]},'source':'Exact saved eigenvalues enumerated by archived mode order; no mass-weighted frequency or refit.'})
d['views'].append({'id':'spectrum','title':'Signed eigenvalue spectrum (choose case filter)','table':'signed-eigenspectra','x':'mode_index','y':'signed_eigenvalue','color':'case_id','filterValue':rows[0]['case_id'],'description':'Signed archived Hessian eigenvalues; change case filter, inspect zero_tolerance and boundary in exact saved records. Not a vibrational frequency spectrum.'})
p.write_text(json.dumps(d,separators=(',',':')))
p=G/'data/snt-ligand-ensemble.json';d=json.loads(p.read_text())
for t in d['tables']:
 if t['id'] in ['curated-default','conditions']:t['uncertainty']={'y':'reach_mean_A','sd':'reach_between_replicate_SD_A','label':'±1 between-replica SD (3 replicas); not a confidence interval'}
p.write_text(json.dumps(d,separators=(',',':')))
p=G/'observatory.js';s=p.read_text().replace('    validPts.push({ idx: i, px, py, rawX, rawY, grp });',"    const uncertainty=tbl.uncertainty;const sd=uncertainty?.y===state.yCol?Number(r[uncertainty.sd]):NaN;validPts.push({ idx: i, px, py, rawX, rawY, grp,sd });")
s=s.replace('  if (minX === maxX)',"  for(const p of validPts){if(Number.isFinite(p.sd)&&!state.logY){minY=Math.min(minY,p.rawY-p.sd);maxY=Math.max(maxY,p.rawY+p.sd);}}\n  if (minX === maxX)")
s=s.replace("  const gPts = document.createElementNS(ns, 'g');", """  if(tbl.uncertainty?.y===state.yCol&&!state.logY){const errorBars=document.createElementNS(ns,'g');errorBars.setAttribute('aria-label',tbl.uncertainty.label);for(const p of plottedPts){if(!Number.isFinite(p.sd))continue;const line=document.createElementNS(ns,'line');line.setAttribute('x1',sx(p.px));line.setAttribute('x2',sx(p.px));line.setAttribute('y1',sy(p.rawY-p.sd));line.setAttribute('y2',sy(p.rawY+p.sd));line.setAttribute('stroke',colorMap.get(p.grp));line.setAttribute('stroke-width','2');errorBars.append(line);}svg.append(errorBars);warnEl.textContent+=' · '+tbl.uncertainty.label;}
  const gPts = document.createElementNS(ns, 'g');""")
p.write_text(s)
sg=G.parent/'snt/explore';shutil.copy2(p,sg/p.name);shutil.copy2(G/'data/snt-ligand-ensemble.json',sg/'data/snt-ligand-ensemble.json')
print(len(rows),'exact signed-eigenvalue rows exposed; source SD displayed without invented CI')
