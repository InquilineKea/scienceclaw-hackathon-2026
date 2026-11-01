from pathlib import Path
import json,re,shutil
R=Path(__file__).resolve().parent; C=R/'candidate';G=C/'collagen-studies'
p=G/'observatory.js';s=p.read_text();a=s.index('function isRowQualified(');b=s.index('async function init()',a)
s=s[:a]+'''function isRowQualified(row) {
 const q=getCurrentTable()?.qualification;if(!q)return true;
 const yes=v=>v===true||v===1||v==='true'||v==='True';
 if(q.mode==='all_true')return q.columns.every(k=>yes(row[k]));
 return (q.passValues||[true]).includes(row[q.field]);
}
function tableHasQualification(tbl){return Boolean(tbl?.qualification);}

'''+s[b:]
s=s.replace('const xCandidates = numCols.length ? numCols : cols;', 'const xCandidates = cols;')
s=s.replace('    forces: f.forces || mdl.forces','    edges: f.edges ?? mdl.edges,\n    forces: Object.hasOwn(f,\'forces\') ? f.forces : mdl.forces')
s=s.replace('if (!pick) return;', "if (!pick || pick.type==='edge') return;")
s=s.replace('    renderAllDataViews();\n    updateSpatialStage(true);', "    renderAllDataViews();\n    if(!preferredTableId && data.views?.[0])applyCuratedView(data.views[0]);\n    updateSpatialStage(true);")
s=s.replace('  let omittedNonPos = 0;', "  const categoricalX=!isNumericColumn(rows,state.xCol);\n  const categories=categoricalX?[...new Set(rows.map(r=>String(r[state.xCol]??'Missing')))]:[];\n  if(categoricalX){state.logX=false;el('log-x-chk').checked=false;}\n  let omittedNonPos = 0;")
s=s.replace('    const rawX = Number(r?.[state.xCol]);\n    const rawY = Number(r?.[state.yCol]);', "    const numeric=v=>v===null||v===undefined||v===''?NaN:Number(v);\n    const rawX=categoricalX?categories.indexOf(String(r[state.xCol]??'Missing')):numeric(r[state.xCol]);\n    const rawY=numeric(r[state.yCol]);")
s=s.replace('${plottedPts.length} plotted / ${rows.length} total rows','${plottedPts.length} plotted / ${validPts.length} finite filtered / ${rows.length} table rows')
s=s.replace('for (let i = 0; i < plottedPts.length; i++) {\n    const p = plottedPts[i];','for (let i = 0; i < validPts.length; i++) {\n    const p = validPts[i];')
s=s.replace('tx.textContent = formatVal(vx);',"tx.textContent = categoricalX ? (categories[Math.round(vx)]||'').slice(0,22) : formatVal(vx);")
s=s.replace('.sort((a, b) => a.px - b.px);', '.sort((a,b)=>tbl.preserveRowOrder?a.idx-b.idx:a.px-b.px);')
s=s.replace("    c.addEventListener('click', () => selectRecord(p.idx));", "    c.setAttribute('tabindex','0');c.setAttribute('role','button');c.setAttribute('aria-label',title.textContent);\n    c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectRecord(p.idx);}});\n    c.addEventListener('click', () => selectRecord(p.idx));")
s=s.replace('    viewer.setModel?.(eff);', "    const oldView=viewer.getView?.();const sameModel=pane.previousModel===mdl.id;viewer.setModel?.(eff);if(sameModel&&oldView)viewer.setView?.(oldView);pane.previousModel=mdl.id;")
s=s.replace('`Node #${idx}`;', '`'+ '${mdl.labels?.[idx] || "Node #"+idx}' +'`;')
p.write_text(s)
# Public shared assets are identical copies, not new dependencies.
for slug in ['mechanics','openmm']:
 for name in ['spatial-viewer.js','spatial-viewer.css']:
  shutil.copy2(G/name,C/slug/name)
 shutil.copytree(G/'vendor',C/slug/'vendor',dirs_exist_ok=True)
# SNT hosts a focused self-contained subset and a small exact-coordinate preview.
sg=C/'snt/explore';sg.mkdir(exist_ok=True)
for name in ['index.html','observatory.js','observatory.css','spatial-viewer.js','spatial-viewer.css']:
 if (G/name).exists():shutil.copy2(G/name,sg/name)
shutil.copytree(G/'vendor',sg/'vendor',dirs_exist_ok=True)
cat=json.loads((G/'catalog.json').read_text());ids=['snt-ligand-ensemble','hydroxylation-prestress','four-bead-calibration','reference-1dzi','reference-1k6f'];cat['studies']=[x for x in cat['studies'] if x['id'] in ids];(sg/'data').mkdir(exist_ok=True)
preview=[]
for sid in ids:
 d=json.loads((G/'data'/f'{sid}.json').read_text());shutil.copy2(G/'data'/f'{sid}.json',sg/'data'/f'{sid}.json')
 if sid in ids[:3]:
  for model in d['models'][:2]:
   m={k:v for k,v in model.items() if k!='frames'};m['id']=sid+'-'+str(m['id']);m['studyId']=sid;m['explorerURL']='./explore/?study='+sid;preview.append(m)
(sg/'catalog.json').write_text(json.dumps(cat))
(C/'snt/molecular-preview-data.json').write_text(json.dumps({'models':preview,'studies':[{'title':x['title'],'href':'./explore/?study='+x['id']} for x in cat['studies']],'limitations':['Saved short pilots and exact reference structures only; no new dynamics, equilibrium proof or molecular-to-network calibration.']}))
shutil.copy2(R/'martini-diagnostic-data.json',C/'mechanics/martini/diagnostic-data.json')
# Add external, scoped enhancements without editing original scripts/data.
for slug,js,css in [('mechanics','mechanics-enhancements.js','mechanics-enhancements.css'),('snt','molecular-bench.js','molecular-bench.css'),('openmm','evidence-lens.js','evidence-lens.css')]:
 p=C/slug/'index.html';t=p.read_text();hook=f'<link rel="stylesheet" href="./spatial-viewer.css?v=3"><link rel="stylesheet" href="./{css}?v=3">' if slug!='snt' else f'<link rel="stylesheet" href="./explore/spatial-viewer.css?v=3"><link rel="stylesheet" href="./{css}?v=3">'
 if js not in t:
  t=t.replace('</head>',hook+'</head>');extra='<script src="./mechanics-bridge.js?v=3"></script>' if slug=='mechanics' else '';t=t.replace('</body>',extra+f'<script type="module" src="./{js}?v=3"></script></body>')
  p.write_text(t)
# Architecture inspector stylesheet and prominent additive entry.
p=C/'architecture/demo.html';t=p.read_text();
if 'demo-inspector.css' not in t:t=t.replace('</head>','<link rel="stylesheet" href="./demo-inspector.css?v=3"></head>')
p.write_text(t)
for slug in ['architecture','mechanics','snt','openmm']:
 p=C/slug/'index.html';t=p.read_text();nav='<nav aria-label="Research explorer additions" style="padding:14px;background:#e7f4f2;color:#134e4a;display:flex;gap:20px;flex-wrap:wrap"><a href="https://inquilinekea.github.io/scienceclaw-hackathon-2026/collagen-studies/">33 saved-study dashboards &amp; 3D molecular viewer</a>'
 if slug=='architecture':nav+='<a href="./demo.html">Open 3D architecture inspector</a>'
 nav+='</nav>'
 if 'Research explorer additions' not in t:t=re.sub(r'(<body[^>]*>)',lambda m:m[1]+nav,t,count=1)
 p.write_text(t)
# Complete scoped layout rules; no external fonts/assets.
with (C/'snt/molecular-bench.css').open('a') as f:f.write('''
.mb-has-bench{max-width:1280px!important;width:100%;box-sizing:border-box}.mb-bench{font-family:system-ui,sans-serif;border:1px solid #b9d9d5;border-radius:18px;padding:clamp(12px,2vw,28px);margin:24px 0;background:#f7fbfa;color:#183b3a}.mb-title{font-size:clamp(23px,3vw,34px);line-height:1.15}.mb-eyebrow,.mb-slot-label,.mb-cat-badge{font-size:12px;font-weight:700;color:#0f766e}.mb-toolbar,.mb-btn-group,.mb-study-links,.mb-badge-wrap{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.mb-control-group{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.mb-select,.mb-btn,.mb-study-btn{padding:10px;border:1px solid #96b9b4;border-radius:8px;background:white;max-width:100%;color:#134e4a}.mb-toolbar{margin:18px 0}.mb-stage-grid,.mb-info-grid{display:grid;grid-template-columns:1fr;gap:16px}.mb-stage-grid.mb-is-compare,.mb-info-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.mb-viewport-card,.mb-panel{min-width:0;border:1px solid #c5dcd7;border-radius:12px;padding:12px;background:white}.mb-canvas-host{min-height:420px}.mb-viewport-bar,.mb-viewport-footer{display:flex;gap:10px;justify-content:space-between;flex-wrap:wrap}.mb-fit-note,.mb-stats,.mb-note-body,.mb-pick-hint{font-size:13px;line-height:1.5}.mb-meta-list,.mb-coord-grid{display:grid;grid-template-columns:minmax(100px,1fr) 2fr;gap:8px;overflow-wrap:anywhere}.mb-meta-list dd,.mb-coord-grid dd{margin:0}.mb-legend{display:flex;gap:8px;flex-wrap:wrap}.mb-legend-chip{font-size:12px;padding:5px;background:#e6f3f0;border-radius:6px}.mb-limits{margin-top:18px}.mb-status-error{color:#9f1239}.mb-sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}[hidden]{display:none!important}@media(max-width:700px){.mb-stage-grid.mb-is-compare,.mb-info-grid{grid-template-columns:1fr}.mb-canvas-host{min-height:340px}.mb-toolbar{align-items:stretch}.mb-select{width:100%}}
''')
with (C/'openmm/evidence-lens.css').open('a') as f:f.write('''
.el-3d-grid,.el-detail-cols{display:grid;grid-template-columns:minmax(0,2fr) minmax(230px,1fr);gap:18px}.el-3d-grid>*{min-width:0}.el-viewport{min-height:420px}.el-inspector{padding:16px;background:#f0f7f6;border-radius:12px}.el-toolbar,.el-pbtn-group{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.el-select,.el-pbtn{padding:9px;border:1px solid #a2bdb8;background:white;border-radius:7px;max-width:100%}.el-kv-row{display:grid;grid-template-columns:1fr 1.5fr;gap:10px;padding:8px 0;border-bottom:1px solid #d3e2df}.el-kv-v{overflow-wrap:anywhere}.el-table-wrap{overflow:auto}.el-table{border-collapse:collapse;width:100%;font-size:13px}.el-table th,.el-table td{padding:10px;text-align:left;border-bottom:1px solid #d3e2df}.el-mono{font-family:ui-monospace,monospace}.el-metric{padding:12px;display:flex;flex-direction:column;gap:5px}.el-metric strong{overflow-wrap:anywhere}.el-3d-shell{padding:18px;border:1px solid #a2bdb8;border-radius:14px;margin-top:20px}[hidden]{display:none!important}@media(max-width:700px){.el-3d-grid,.el-detail-cols,.el-tier-grid{grid-template-columns:1fr}.el-viewport{min-height:340px}.el-section{padding:10px}.el-toolbar{align-items:stretch}}
''')
print('Static integrations complete; no generated browser code executed.')
