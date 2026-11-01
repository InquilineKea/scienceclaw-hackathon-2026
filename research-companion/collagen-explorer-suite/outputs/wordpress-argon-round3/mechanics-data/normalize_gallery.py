"""Owned data-only adapter. No study programs are imported or executed."""
from pathlib import Path
import json,math,hashlib,collections
R=Path(__file__).resolve().parent;S=R/'public-studies';T=R/'gallery-ready';T.mkdir(exist_ok=True)
PASS=[True,1,'true','True','pass','passed','converged']
def qualify(id,t):
 cols=t['columns'];tid=t['id'];field=None
 if id in ['574','593','659','670','205'] and 'accepted' in cols:field='accepted'
 elif id=='457' and 'accepted_1_or_0' in cols:field='accepted_1_or_0'
 elif id=='128' and 'success' in cols:field='success'
 elif id=='192':
  if 'accepted' in cols:field='accepted'
  elif 'mechanics_accepted' in cols:field='mechanics_accepted'
 elif id=='235':
  if 'converged' in cols:field='converged'
  elif 'matched_pair_eligible' in cols:field='matched_pair_eligible'
 elif id=='258':
  if 'converged' in cols:field='converged'
  elif tid=='time-step-pairs.csv' and 'eligible' in cols:field='eligible'
 return {'field':field,'passValues':PASS.copy()} if field else None

def standard_model(g,id=None):
 if not g or not g.get('nodes'):return None
 nodes=g['nodes'];ref=None
 if 'displacements' in g:
  assert len(nodes)==len(g['displacements']);ref=nodes
  nodes=[[a+b for a,b in zip(p,u)] for p,u in zip(nodes,g['displacements'])]
 m={'id':str(id or g.get('id') or 'saved-example'),'label':g.get('label','Saved spatial example'),'nodes':nodes,'edges':g.get('edges',[]),'units':g.get('units','dimensionless'),'evidence':'Saved synthetic spatial coordinates and connectivity; no tissue or molecular calibration','recordBinding':g.get('recordBinding'),'frames':[]}
 if ref:m['referenceNodes']=ref;m['displacementScale']=1;m['evidence']+='; actual equilibrium translations, rotations excluded'
 if g.get('source'):m['source']=g['source']
 if g.get('coordinateSource'):m['coordinateSource']=g['coordinateSource']
 if g.get('geometryFunctionSHA256'):m['geometryFunctionSHA256']=g['geometryFunctionSHA256']
 if g.get('edgeTypes'):m['edgeTypes']=g['edgeTypes']
 for f in g.get('frames',[]):
  fNodes=f.get('nodes',f.get('xyz'));assert len(fNodes)==len(nodes)
  frame={'nodes':fNodes,'edges':f.get('edges',m['edges']),'label':('Saved step '+str(f['step'])+' · ' if 'step' in f else '')+('reduced time '+str(f['time']) if 'time' in f else 'saved static state')}
  for k in ['step','time','edgeTypes']:
   if k in f:frame[k]=f[k]
  m['frames'].append(frame)
 if len(nodes)==36 and g.get('id') in ['no_links_no_friction','no_links_friction','weak_links','strong_links']:m['groups']=[i//12 for i in range(36)];m['labels']=['Fibre '+str(i//12+1)+' · particle '+str(i%12+1) for i in range(36)]
 return m

def owner_models(d):
 models=[]
 for c in d['savedCases']:
  n=c['nodes_per_owner'];L=c['L'];count=len(c['frames'][0]['displacements']);assert count==3*n,(c['case_id'],count,n)
  ref=[[L*(i%n)/(n-1),(i//n-1)*.25,0] for i in range(count)]
  edges=[[e['a'],e['b']] for e in c['edge_topology']];frames=[]
  for f in c['frames']:
   u=f['displacements'];assert len(u)==count
   frames.append({'nodes':[[ref[i][0]+u[i],ref[i][1],0] for i in range(count)],'edges':edges,'label':'Saved1D imposed Δ/L='+str(f['imposed_delta_over_L'])+' · transverse offsets illustrative only','imposedDeltaOverL':f['imposed_delta_over_L']})
  models.append({'id':c['case_id'],'label':c['case_id']+' — saved1D shear-lag schematic, display-only owner offsets','nodes':frames[0]['nodes'],'edges':edges,'referenceNodes':ref,'frames':frames,'groups':[i//n for i in range(count)],'labels':['Backbone '+str(i//n+1)+' · axial node '+str(i%n+1) for i in range(count)],'units':'x: dimensionless model length; y: arbitrary owner-display offset; z: zero','evidence':'Illustrative planar layout of saved1Dscalar displacements and condensed mechanical edges; not real3Dcollagen coordinates or chemical bond geometry','recordBinding':{'key':'case_id','id':c['case_id']},'edgeKinds':[e['kind'] for e in c['edge_topology']],'displacementScale':1,'layoutIllustrative':True})
 return models

receipt=[]
for p in sorted(S.glob('*.json')):
 original=json.loads(p.read_text());d=json.loads(p.read_text());id=d['id'];models=[]
 if id=='677':models=owner_models(d)
 else:
  gs=d.get('spatialExamples') or ([d['geometry']] if d.get('geometry') else [])
  for i,g in enumerate(gs):
   m=standard_model(g,str(g.get('id') or 'saved-example-'+str(i+1)))
   if m:models.append(m)
 for m in models:
  assert all(len(x)==3 and all(math.isfinite(a) for a in x) for x in m['nodes'])
  for f in [{'nodes':m['nodes'],'edges':m['edges']}]+m['frames']:
   assert len(f['nodes'])==len(m['nodes'])
   assert all(len(e)==2 and all(isinstance(a,int) and 0<=a<len(m['nodes']) for a in e) for e in f['edges'])
 for t in d['tables']:t['qualification']=qualify(id,t)
 d['models']=models;d['sourceDataSHA256']=hashlib.sha256(p.read_bytes()).hexdigest();d['adapter']={'method':'Exact saved-table preservation; static JSON/CSV/OOXML/PDF extraction; copied stored geometry plus explicitly documented display layout','noNewPhysics':True,'numericTableRowsUnchanged':True}
 # Avoid duplicating large spatial auxiliaries; enough source provenance remains in models.
 for key in ['geometry','spatialExamples','rawGeometry','savedViewer','savedCases','savedSummary']:d.pop(key,None)
 assert len(d['tables'])==len(original['tables'])
 for a,b in zip(original['tables'],d['tables']):assert a['rows']==b['rows'] and a['columns']==b['columns']
 q=T/p.name;q.write_text(json.dumps(d,allow_nan=False,separators=(',',':')))
 receipt.append({'id':id,'file':q.name,'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'models':len(models),'modelNodes':[len(m['nodes']) for m in models],'modelFrames':[len(m['frames']) for m in models],'tables':len(d['tables']),'rows':[len(t['rows']) for t in d['tables']],'qualifications':{t['id']:t['qualification'] for t in d['tables']},'tableSemanticIdentity':True})
(T/'normalization-receipt.json').write_text(json.dumps({'studies':receipt,'allTableRowsSemanticallyIdentical':True,'allGeometryIndicesValid':True,'noImportedCodeExecuted':True,'noNewFittingOrSimulations':True},indent=2));print('Normalized',len(receipt),'studies;',sum(x['models'] for x in receipt),'models;',sum(x['bytes'] for x in receipt),'bytes')
