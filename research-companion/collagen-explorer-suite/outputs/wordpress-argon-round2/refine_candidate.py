"""Owned, static integration corrections to the external drafts; no draft execution."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
C=ROOT/'candidate/docs'

# Keep strict style-src self; static chain-color classes replace inline style attributes.
f=C/'species-ui.js';s=f.read_text()
s=s.replace('class="chain-dot" style="background:${CHAIN_COLORS[cIdx]}"','class="chain-dot chain-color-${cIdx}"')
s=s.replace('class="inspector-chain-pill" style="background:${CHAIN_COLORS[cIdx]}"','class="inspector-chain-pill chain-color-${cIdx}"')
s=s.replace('Math.max(280, canvasBeaver.clientWidth || 520)','Math.max(1, Math.min(canvasBeaver.clientWidth || 520, canvasHuman.clientWidth || 520))')
s=s.replace('Math.max(280, canvas.clientWidth || W)','Math.max(1, canvas.clientWidth || W)')
s=s.replace('const x = ev.clientX - rect.left;\n      const y = ev.clientY - rect.top;', 'const pixel=window.devicePixelRatio||1;\n      const x=(ev.clientX-rect.left)*(canvas.width/pixel)/Math.max(1,rect.width);\n      const y=(ev.clientY-rect.top)*(canvas.height/pixel)/Math.max(1,rect.height);')
s=s.replace('selectResidue(2, 44, false);', "const initial=getCurrentContext();let first={c:0,r:0};outer:for(let c=0;c<3;c++)for(let r=0;r<initial.n;r++)if(isMismatch(initial.tasks,c,r)){first={c,r};break outer;}selectResidue(first.c,first.r,false);")
f.write_text(s)
f=C/'species.css';f.write_text(f.read_text()+'\n#structures .chain-color-0{background:#20775b}#structures .chain-color-1{background:#8950a0}#structures .chain-color-2{background:#c96b32}\n')

# Rebuild large element dropdowns only when topology/labels change, not every replay frame.
f=C/'canvas-probe.js';s=f.read_text();start=s.index('    function syncControls() {');end=s.index('    panelSel.onchange',start)
s=s[:start]+'''    let optionSignature='';
    function syncControls() {
      const pid=activePanelId(),sc=scenes.get(pid);
      if(selected&&!scenes.get(selected.panelId)?.items?.some(x=>x.key===selected.key))selected=null;
      const items=sc?.items||[];
      const sig=pid+'|'+items.map(x=>x.key+':'+(x.shortLabel||x.label)).join('|');
      if(sig!==optionSignature){
        optionSignature=sig;itemSel.replaceChildren(new Option('Click a node/segment or choose…',''));
        for(const it of items)itemSel.append(new Option(it.shortLabel||it.label,it.key));
      }
      itemSel.value=selected?.panelId===pid?selected.key:'';
      if(selected){const selectedScene=scenes.get(selected.panelId),it=selectedScene.items.find(x=>x.key===selected.key);panelSel.value=selected.panelId;readout.textContent=describe(selectedScene,it)}
      else readout.textContent=config.emptyText||'Click a displayed node, fiber, or connector (or use the element selector) to inspect its model state.';
    }
''' +s[end:]
s=s.replace('phase=${ph.phaseDeg.toFixed(1)}°','dominant-component lag (−arg u)=${ph.phaseDeg.toFixed(1)}°')
f.write_text(s)

# A sample filtered out by a slab must not remain selected in hidden numerical state.
f=C/'spatial-inspector.js';s=f.read_text().replace("sampleSel.value = hasSelected ? String(state.selectedId) : '';", "if(!hasSelected)state.selectedId=null;\n        sampleSel.value = hasSelected ? String(state.selectedId) : '';");f.write_text(s)

# Install one same-origin, collapsible navigation panel on all existing explorer entrypoints.
entries=['index.html','aging.html','species.html','topology-aging.html','transitions/index.html','evidence-atlas/index.html','bovine-3d/index.html','measured-3d/index.html','nonlinear-3d/index.html','poroelasticity/index.html','microrheology/index.html','force-replay/index.html','force-robustness/index.html']
for rel in entries:
 f=C/rel;s=f.read_text();prefix='../' if '/' in rel else ''
 if 'explorer-navigation.css' not in s:
  tag='<link rel="stylesheet" href="'+prefix+'explorer-navigation.css">'
  if '</head>' in s:s=s.replace('</head>',tag+'</head>',1)
  elif '<style>' in s:s=s.replace('<style>',tag+'<style>',1)
  else:
   assert '<main>' in s;s=s.replace('<main>',tag+'<main>',1)
 if 'explorer-navigation.js' not in s:
  tag='<script src="'+prefix+'explorer-navigation.js" defer></script>'
  if '</body>' in s:s=s.replace('</body>',tag+'</body>',1)
  elif '</html>' in s:s=s.replace('</html>',tag+'</html>',1)
  else:s+=tag
 f.write_text(s)

# Version only presentation assets, so repeat visitors do not retain prior UI scripts.
changed_names={'species-ui.js','species.css','canvas-probe.js','canvas-probe.css','spatial-inspector.js','spatial-camera.css','explorer-navigation.js','explorer-navigation.css','app.js','aging-ui.js','page.js','style.css'}
for rel in entries:
 f=C/rel;s=f.read_text()
 def version(m):
  attr,url=m.group(1),m.group(2);base=url.split('?')[0]
  if not base.startswith(('https:','http:','data:')) and base.split('/')[-1] in changed_names:
   return attr+'"'+base+'?v=20261101-argon2"'
  return m.group(0)
 s=re.sub(r'((?:src|href)=)"([^"]+)"',version,s);f.write_text(s)
f=C/'evidence-atlas/app.js';s=f.read_text();s=re.sub(r'(\./network-scenes\.js)(?:\?[^\'\"]*)?',r'\1?v=20261101-argon2',s);f.write_text(s)
print('Static integration refinements complete.')
