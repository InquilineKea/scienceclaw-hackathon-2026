from pathlib import Path
import json,shutil
C=Path(__file__).resolve().parent/'candidate';G=C/'collagen-studies'
p=C/'architecture/demo-inspector.js';s=p.read_text().replace('Math.max(0,...fFrame.peakForces)/fFrame.tolerance','fFrame.residual/fFrame.tolerance').replace('Force/tol ${ratio.toFixed(0)}×','Residual/tolerance ${ratio.toFixed(3)}×');p.write_text(s)
p=G/'spatial-viewer.js';s=p.read_text().replace("String(model.groups[origI]) : 'Chain A'", "String(model.groups[origI]) : (model.elements?.[origI]||'Coordinate group')").replace('`Node ${idx}`','`${model.elements?.[origI]||"Node"} ${idx}`');p.write_text(s)
p=G/'observatory.js';s=p.read_text();needle="  let omittedNonPos = 0;";s=s.replace(needle,"""  let matrix=document.getElementById('categorical-record-cards');
  if(!matrix){matrix=document.createElement('div');matrix.id='categorical-record-cards';svg.before(matrix);}
  matrix.replaceChildren();
  const matrixMode=rows.length>0&&!isNumericColumn(rows,state.yCol);
  matrix.hidden=!matrixMode;svg.hidden=matrixMode;
  if(matrixMode){for(const row of rows.slice(0,50)){const card=document.createElement('article');card.className='evidence-record-card';for(const [k,v] of Object.entries(row)){const line=document.createElement('p');const key=document.createElement('strong');key.textContent=k+': ';line.append(key,document.createTextNode(formatVal(v)));card.append(line);}matrix.append(card);}countEl.textContent=`${rows.length} saved categorical records · evidence matrix (no numeric axis implied)`;return;}
  let omittedNonPos = 0;""")
s=s.replace("  svg.appendChild(gPts);", """  svg.appendChild(gPts);
  if(state.studyData?.defaultView?.plotKind==='histogram' && state.xCol==='bin_low' && state.yCol==='density'){
    const bars=document.createElementNS(ns,'g');bars.setAttribute('aria-label','Saved shared-bin density histograms');
    for(const p of plottedPts){const hi=Number(rows[p.idx].bin_high);if(!Number.isFinite(hi))continue;const rect=document.createElementNS(ns,'rect');rect.setAttribute('x',sx(p.px));rect.setAttribute('y',sy(p.py));rect.setAttribute('width',Math.max(1,sx(hi)-sx(p.px)));rect.setAttribute('height',Math.max(0,sy(Math.max(0,minY))-sy(p.py)));rect.setAttribute('fill',colorMap.get(p.grp));rect.setAttribute('opacity','.22');const title=document.createElementNS(ns,'title');title.textContent=`${p.grp}: [${p.rawX},${hi}] density=${p.rawY}`;rect.append(title);bars.append(rect);}svg.insertBefore(bars,gPts);warnEl.textContent+=' · Exact saved shared bins; density overlay, not a fitted distribution.';
  }
""")
p.write_text(s)
p=G/'observatory.css';p.write_text(p.read_text()+"\n.evidence-record-card{border:1px solid #cbd5e1;background:#f8fafc;border-left:4px solid #0d9488;border-radius:8px;margin:12px 0;padding:12px;overflow-wrap:anywhere}.evidence-record-card p{margin:6px 0}.badge-row{flex-wrap:wrap} .study-header h2,.study-title{overflow-wrap:anywhere}.badge{white-space:normal!important}\n")
# Distinct representative conditions; exact coordinate objects retained.
preview=[]
for sid,selectors in [('snt-ligand-ensemble',['SNT5382_F_q0_eps1_r0','SNT5382_F_q0_eps4_r0']),('hydroxylation-prestress',['HYP_none_r0','HYP_native_r0']),('four-bead-calibration',['mapping-HYP_native_r0','HYP_native_hold0'])]:
 d=json.loads((G/'data'/f'{sid}.json').read_text());chosen=[next((m for m in d['models'] if m['id']==key),None) for key in selectors]
 for m in chosen:
  if not m:continue
  a={k:v for k,v in m.items() if k!='frames'};a['label']=str(m['id']);a['id']=sid+'-'+m['id'];a['studyId']=sid;preview.append(a)
p=C/'snt/molecular-preview-data.json';d=json.loads(p.read_text());d['models']=preview;p.write_text(json.dumps(d))
for slug in ['mechanics','openmm','snt/explore']:
 for name in ['spatial-viewer.js','spatial-viewer.css']:shutil.copy2(G/name,C/slug/name)
for name in ['observatory.js','observatory.css']:shutil.copy2(G/name,C/'snt/explore'/name)
print('Evidence matrices, saved histograms, native-control previews and residual labels refined.')
