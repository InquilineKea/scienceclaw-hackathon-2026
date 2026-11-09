"""Owned static integration/data packaging. Does not execute generated browser code."""
from pathlib import Path
import json,re,shutil,hashlib
R=Path(__file__).resolve().parent;C=R/'candidate';G=C/'collagen-studies';ROOT=R.parents[1]

def replace(p,a,b):
 s=p.read_text();assert s.count(a)==1,(str(p),s.count(a),a[:80]);p.write_text(s.replace(a,b))
def writejson(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,separators=(',',':'),ensure_ascii=False,allow_nan=False))

# Complete files recovered from external drafts; partial strings/rules are not executed.
for f in (R/'drafts/argon-openmm').iterdir():shutil.copy2(f,C/'openmm'/f.name)
for f in (R/'drafts/argon-snt').iterdir():shutil.copy2(f,C/'snt'/f.name)

# Do not turn absent saved forces into zero force measurements.
p=G/'spatial-viewer.js';s=p.read_text().replace('forces.push([0, 0, 0]);','forces.push(null);').replace('if (maxForce <= 1e-12) hasForces = false;','if (!forces?.some(validVec)) hasForces = false;')
s=s.replace('if (state.hasForces && state.forces) {','if (state.hasForces && validVec(state.forces?.[i])) {')
s=s.replace('force: state.hasForces ? [...state.forces[i]] : null,','force: state.hasForces && validVec(state.forces[i]) ? [...state.forces[i]] : null,')
s=s.replace("const DISP_STEPS = [0, 1, 2, 5, 10];","const DISP_STEPS = [0, 1, 2, 5, 10, 25, 100];dispInput.max='6';")
s=s.replace("return { setModel, selectNode, setPreset, getView, setView, resize, dispose };", "function setDisplayMagnification(value){state.dispMag=Math.max(0,Math.min(100,Number(value)||1));dispSpan.textContent='Disp '+state.dispMag+'x ';const idx=DISP_STEPS.indexOf(state.dispMag);if(idx>=0)dispInput.value=String(idx);updateGeometryTransforms();}\n  return { setModel, selectNode, setPreset, getView, setView, resize, dispose, setDisplayMagnification };")
s=s.replace("const groups = [];\n    const labels", "const groups = [];\n    const labels")
p.write_text(s)

# Typed vectors stay arrays; display magnification never replaces original saved coordinates.
p=C/'openmm/evidence-lens.js';s=p.read_text().replace("const pos = n.position || n.xyz || [n.x ?? 0, n.y ?? 0, n.z ?? 0];", "const pos = Array.isArray(n)?n:(n.position || n.xyz || [n.x ?? 0, n.y ?? 0, n.z ?? 0]);")
s=s.replace("refPos: model.referenceNodes?.[idx]?.position || model.referenceNodes?.[idx]?.xyz || null,", "refPos: Array.isArray(model.referenceNodes?.[idx])?model.referenceNodes[idx]:(model.referenceNodes?.[idx]?.position || model.referenceNodes?.[idx]?.xyz || null),")
a=s.index('  function adaptModelForViewer(');b=s.index('  function syncViewerAndInspector()',a)
s=s[:a]+'''  let lastDisplayedModel=null;
  function adaptModelForViewer(rawModel){return {...rawModel,nodes:rawModel.nodes.map(n=>Array.isArray(n)?n.slice():n.position||n.xyz),referenceNodes:rawModel.referenceNodes?.map(n=>Array.isArray(n)?n.slice():n.position||n.xyz)};}
\n'''+s[b:]
s=s.replace("if (typeof viewer.setModel === 'function') viewer.setModel(vModel);", "if (typeof viewer.setModel === 'function' && lastDisplayedModel!==m.id){viewer.setModel(vModel);lastDisplayedModel=m.id;}viewer.setDisplayMagnification?.(dispMag);")
s=s.replace('onSelectNode: (nodeOrIdx) => {','onPick: (nodeOrIdx) => {\n        if(nodeOrIdx?.type===\'edge\')return;')
s=s.replace('1× True Scale (nm / kJ·mol⁻¹·nm⁻¹)','1× displacement display (saved coordinates)')
p.write_text(s)

p=C/'snt/molecular-bench.js';s=p.read_text().replace("if (!node) return ['N/A', 'N/A', 'N/A'];", "if (!node) return ['N/A', 'N/A', 'N/A'];\n  if(Array.isArray(node)&&node.length>=3)return node;")
s=s.replace("const groups = model.groups && typeof model.groups === 'object' ? Object.entries(model.groups) : [];", "const groups = Array.isArray(model.groups)?[...new Set(model.groups)].map(x=>[String(x),String(x)]):(model.groups&&typeof model.groups==='object'?Object.entries(model.groups):[]);")
s=s.replace("const dd = el('dd', '', v);", "const dd = el('dd', '', typeof v==='object'?JSON.stringify(v):v);")
s=s.replace("const preset = btn.dataset.preset;", "const preset = ({front:'xy',side:'yz',top:'xz',reset:'fit'})[btn.dataset.preset]||'iso';")
s=s.replace("if (!pick", "if (!pick")
s=s.replace("function renderPickedNode(pick, sourceLabel, model) {", "function renderPickedNode(pick, sourceLabel, model) {\n    if(pick?.type==='edge')return;")
p.write_text(s)

# Existing Architecture worker/model remain byte-identical; pause inspection to make readouts usable.
p=C/'architecture/demo.js';s=p.read_text().replace('setSelectedFiber(id){selectedFiber=id;dirty=true;updateReadouts();}', 'setSelectedFiber(id){setPlay(false);selectedFiber=id;dirty=true;updateReadouts();}');p.write_text(s)

# Additive classic bridge exposes only selected copied rows from the original model.
(C/'mechanics/mechanics-bridge.js').write_text('''globalThis.CollagenMechanicsSnapshot=()=>{if(typeof DATA==='undefined'||typeof findRow!=='function')return null;const row=findRow();if(!row)return null;const keys=['seed','collagen_density','density_profile','chemistry','location'];const eq=x=>keys.every(k=>x[k]===row[k]);return {row:{...row},sites:DATA.sites.filter(eq).map(x=>({...x})),curves:DATA.curves.filter(eq).map(x=>({...x}))};};\n''')

# Exact stored OpenMM numerical-control values, not a collagen parameterization.
d=json.loads((C/'openmm/artifacts/results/openmm_cuda_20261031T090236Z.json').read_text());pos=[[0,0,0],[.12,0,0]];models=[]
for key,tag in [('Reference','initial_reference'),('CUDA','initial_cuda')]:models.append({'id':tag,'label':key+' initial harmonic dimer (numerical control)','nodes':pos,'edges':[[0,1]],'groups':['control mass','control mass'],'labels':['Particle0','Particle1'],'forces':d['initial'][key]['forces_kj_mol_nm'],'units':'nm','forceUnits':'kJ/mol/nm','evidence':'Executed numerical infrastructure control, not collagen'})
models.append({'id':'final_cuda','label':'CUDA final stored endpoint, 1000fs','nodes':d['final_positions_nm'],'referenceNodes':pos,'edges':[[0,1]],'groups':['control mass','control mass'],'labels':['Particle0','Particle1'],'units':'nm','evidence':'Executed numerical infrastructure control; final force vector not stored'})
url='https://humanavianaisymbiosis.wordpress.com/scienceclaw-comparative-collagen-aging-research-hub/'
writejson(C/'openmm/evidence-lens-data.json',{'tiers':[{'id':'observed','title':'11 mammalian pentosidine cohorts','kind':'Published observations','scope':'Comparative observational evidence','claims':['Historical skin pentosidine age coefficients and lifespan associations are observed cohort summaries.'],'doesNotEstablish':['Causal collagen protection across species or common-site tissue mechanics.','Cloud or molecular simulation validation of those associations.'],'sourceURLs':[url]},{'id':'synthetic','title':'432 SciPy tensile simulations','kind':'Synthetic mechanics','scope':'Assumed dimensionless network rules','claims':['27 model conditions ×16 network realizations were computed under the archived rules.'],'doesNotEstablish':['Calibrated animal-specific MPa, chemical aging or clinical strength.'],'sourceURLs':[url]},{'id':'infrastructure','title':'OpenMM CUDA harmonic-dimer check','kind':'Executed infrastructure check','scope':'2particles;1000steps;1fs','claims':['Recorded CUDA/Reference force agreement and bounded NVE energy drift passed the check.'],'doesNotEstablish':['A collagen force field, reactive chemistry, binding or biological prediction.'],'sourceURLs':['https://openmm-cuda-experiment-log.stochasticcockatoo.chatgpt.site/']}],'models':models,'checks':[{'quantity':'Initial potential energy','Reference':d['initial']['Reference']['potential_kj_mol'],'CUDA':d['initial']['CUDA']['potential_kj_mol'],'difference':abs(d['initial']['Reference']['potential_kj_mol']-d['initial']['CUDA']['potential_kj_mol']),'units':'kJ/mol'},{'quantity':'Initial force component comparison','Reference':d['initial']['Reference']['forces_kj_mol_nm'][0][0],'CUDA':d['initial']['CUDA']['forces_kj_mol_nm'][0][0],'difference':d['initial_force_max_abs_difference_kj_mol_nm'],'units':'kJ/mol/nm'},{'quantity':'Final relative total-energy drift','Reference':'Not separately integrated','CUDA':d['relative_energy_drift'],'difference':d['relative_energy_drift'],'units':'dimensionless'}],'metadata':{'platform':d['platform_properties']['DeviceName'],'steps':d['parameters']['steps'],'dt_fs':d['parameters']['dt_fs'],'biological_validation':False,'relative_energy_drift':d['relative_energy_drift']}})

# All source tables preserved; focused default tables are explicit row subsets, not recomputed fits.
postmap={str(x['id']):x for x in json.loads((R.parent/'wordpress-argon-visuals/public-review-packet.json').read_text())};catalog=[];receipt=[]
for folder,category in [('mechanics-data/gallery-ready','Network mechanics'),('molecular-data/gallery-ready','Molecular & evidence')]:
 for f in sorted((R/folder).glob('*.json')):
  data=json.loads(f.read_text())
  if not isinstance(data,dict) or not data.get('title'):continue
  
  for table in data.get('tables',[]):
   table['rows']=[dict(zip(table['columns'],row)) if isinstance(row,list) else row for row in table.get('rows',[])]
  original_id=str(data['id']);sid=data.get('slug') or original_id;data['id']=sid
  postids=data.get('postIds') or ([int(original_id)] if original_id.isdigit() else []);data['postIds']=postids
  dv=data.get('defaultView') or {};tid=dv.get('table') or dv.get('tableId');base=next((t for t in data.get('tables',[]) if t['id']==tid),None)
  filters=dv.get('filters',{});focus=base
  if base and filters:
   indices=[i for i,row in enumerate(base['rows']) if all(row.get(k)==v for k,v in filters.items())];assert indices,(sid,filters)
   focus={**base,'id':'curated-default','title':'Focused comparison · '+base.get('title',base['id']),'rows':[base['rows'][i] for i in indices],'source':{'curated_from':base['id'],'filters':filters,'original_row_indices':indices,'scope':'Exact saved-row subset; no aggregation, interpolation or new fit.'}}
   data['tables'].insert(0,focus)
  elif base and data['tables'].index(base)>0:data['tables']=[base]+[t for t in data['tables'] if t is not base]
  if focus:
   data['defaultView']={**dv,'table':focus['id']};data['views']=[{'id':'recommended','title':'Start here: focused comparison','description':dv.get('note','Exact saved values; filters: '+json.dumps(filters)), 'table':focus['id'],'x':dv.get('x'),'y':dv.get('y'),'color':dv.get('color')}]
   if sid=='bonded-particle-bundle':focus['preserveRowOrder']=True
  report=next((postmap.get(str(p),{}).get('url') for p in postids if postmap.get(str(p),{}).get('url')),None)
  models=data.get('models',[]);actual3d=any(any(abs(n[2])>1e-10 for n in m.get('nodes',[])) for m in models)
  geometry_type='Saved 3D coordinates' if actual3d else 'Planar/schematic geometry' if models else 'Saved scalar/evidence tables'
  meta={'id':sid,'title':data['title'],'category':category,'evidence':data.get('evidence','Saved research output'),'geometryType':geometry_type,'summary':data.get('limitations',[''])[0] if data.get('limitations') else '', 'dataURL':'./data/'+sid+'.json','reportURL':report,'postIds':postids}
  writejson(G/'data'/f'{sid}.json',data);catalog.append(meta);receipt.append({'id':sid,'source_file':str(f.relative_to(R)),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'tables':len(data.get('tables',[])),'rows':sum(len(t['rows']) for t in data.get('tables',[])),'models':len(models),'default_table':data.get('defaultView',{}).get('table')})
catalog.sort(key=lambda x:(0 if x['id']=='reference-1dzi' else 1 if x['id']=='coupled-3d-law' else 2,x['category'],x['title']))
writejson(G/'catalog.json',{'studies':catalog,'scope':'Saved-data dashboards; distinct experiments retain separate evidence, controls and units.'});writejson(R/'catalog-preparation.json',receipt)
print('Prepared',len(catalog),'study dashboards and Sites data; no generated code executed.')
