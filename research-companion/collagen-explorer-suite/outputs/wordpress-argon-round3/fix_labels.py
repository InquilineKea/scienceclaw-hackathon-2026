from pathlib import Path
import shutil
C=Path(__file__).resolve().parent/'candidate'
G=C/'collagen-studies'
for name in ['spatial-viewer.js','observatory.js']:
 p=G/name;s=p.read_text();s="const readableLabel=v=>v&&typeof v==='object'?Object.entries(v).map(([k,x])=>`${k}: ${x}`).join(' · '):String(v??'');\n"+s
 if name=='spatial-viewer.js':s=s.replace('String(model.labels[origI])','readableLabel(model.labels[origI])')
 else:
  s=s.replace('mdl.labels?.[idx] || "Node #"+idx','readableLabel(mdl.labels?.[idx]) || "Node #"+idx')
  s=s.replace("const bTag = mdl.recordBinding ? ' [Row-Bound]' : ' [Fixed Example]';", "const bTag = mdl.recordBinding && !mdl.recordBinding.type ? ' [Saved matching case]' : ' [Fixed reference/example]';")
  s=s.replace("const nLabel = (n && typeof n === 'object' && (n.label || n.id)) ? ` (${n.label || n.id})` : '';", "const nLabel=' ('+readableLabel(mdl.labels?.[nodeIdx]??n.label??nodeIdx)+')';")
 p.write_text(s)
for slug in ['mechanics','openmm','snt/explore']:
 for name in ['spatial-viewer.js','spatial-viewer.css'] :shutil.copy2(G/name,C/slug/name)
shutil.copy2(G/'observatory.js',C/'snt/explore/observatory.js')
p=C/'mechanics/mechanics-enhancements.js';s=p.read_text().replace('        nodes,\n        edges: [],\n        groups,\n        labels,\n        nodeValues,','        nodes:nodes.map(n=>[n.x,n.y,n.z]),\n        edges: [],\n        groups:nodes.map(n=>n.group),\n        labels:nodes.map(n=>n.label),\n        nodeValues:nodes.map(n=>n.value),').replace('state.viewer.selectNode(state.selectedAdhesion);','state.viewer.selectNode(nodes.findIndex(n=>n.id===state.selectedAdhesion));');p.write_text(s)
