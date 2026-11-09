from pathlib import Path
import json,hashlib,ast,re
R=Path(__file__).resolve().parent;D=R/'studies';B=Path('/path/to/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs')
def source(p):
 p=Path(p);b=p.read_bytes();return {'local_original':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def fn_hash(p):
 s=p.read_text();f=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name=='geometry');return hashlib.sha256(ast.get_source_segment(s,f).encode()).hexdigest()
gp=B/'collagen-percolation-rigidity-20261031/results/geometry_W3.json';geom=json.loads(gp.read_text());refhash=fn_hash(B/'collagen-percolation-rigidity-20261031/source/graphs.py')
for filename,slug,pat,key in [('659-matched-budget-topologies','collagen-topology-budget-20261031','W3-k10-s1-*.json','task.id'),('670-degree-controlled-triangles','collagen-degree-clustering-20261031','W3-k10-s3-*.json','id')]:
 p=D/(filename+'.json');d=json.loads(p.read_text());assert fn_hash(B/slug/'source/graphs.py')==refhash;examples=[]
 for st in sorted((B/slug/'results/states').glob(pat)):
  state=json.loads(st.read_text());ids=state['edge_ids'];id=state.get('id') or state['task']['id'];row=next(x for x in d['tables'][0]['rows'] if x[key]==id)
  computed=hashlib.sha256(json.dumps({'positions':geom['integer_positions'],'edge_ids':ids},sort_keys=True,separators=(',',':')).encode()).hexdigest();assert computed==row['graph.graph_sha256'],(id,computed,row['graph.graph_sha256'])
  examples.append({'id':id,'nodes':geom['positions'],'edges':[geom['edges'][i] for i in ids],'units':'dimensionless','label':'Saved exact FCC graph '+id+'; coordinates shared with preserved W3geometry, identical geometry() source verified','recordBinding':{'id':id,'key':key,'graphSHA256':computed},'source':source(st),'coordinateSource':source(gp),'geometryFunctionSHA256':refhash})
 d['geometry']=examples[0];d['spatialExamples']=examples;d['limitations'].append('Only the listed four spatial examples have exact record bindings; other scalar cases have no supplied geometry and must keep an independent-example label.');p.write_text(json.dumps(d,separators=(',',':')))
p=D/'494-bonded-particle-bundle.json';d=json.loads(p.read_text());examples=[];root=B/'collagen-bpm-nebius-pilot-20261031'
for name,v in d['savedViewer'].items():
 commands=root/'raw/out/final'/name/'commands.in';bonds=[tuple(map(int,m.groups())) for m in re.finditer(r'^create_bonds single/bond (\d+) (\d+) (\d+)$',commands.read_text(),re.M)];assert len(bonds)==v['record']['baseline_backbone']+v['record']['baseline_crosslinks'];frames=[]
 for f in v['frames']:
  broken={tuple(sorted((int(e[1]),int(e[2])))) for e in v['events'] if e[0]<=f['step']};active=[(t,a,b) for t,a,b in bonds if tuple(sorted((a,b))) not in broken]
  frames.append({'step':f['step'],'time':f['time'],'nodes':f['xyz'],'edges':[[a-1,b-1] for t,a,b in active],'edgeTypes':[t for t,a,b in active]})
 assert len(frames[-1]['edges'])==v['record']['final_backbone']+v['record']['final_crosslinks']
 examples.append({'id':name,'nodes':frames[0]['nodes'],'edges':frames[0]['edges'],'edgeTypes':frames[0]['edgeTypes'],'frames':frames,'units':'dimensionless reduced LAMMPS units','label':'Saved '+name+'36particle trajectory; exact input bonds and native step-stamped break events; time is reduced model time','recordBinding':{'name':name,'key':'name'},'source':source(commands),'trajectorySource':d['viewerSource']})
d['geometry']=next(x for x in examples if x['id']=='weak_links');d['spatialExamples']=examples;p.write_text(json.dumps(d,separators=(',',':')))
print('Enriched',[(p.name,p.stat().st_size) for p in [D/'659-matched-budget-topologies.json',D/'670-degree-controlled-triangles.json',D/'494-bonded-particle-bundle.json']])
