"""Own stdlib data transformation only; never imports or executes recovered code."""
import json,pathlib,hashlib,math,re
BASE=pathlib.Path(__file__).parent
OUT=BASE/'gallery-ready';OUT.mkdir(exist_ok=True)
GATES={
 ('coupled-3d-law','fit-gates'):['transfer_accepted'],('coupled-3d-law','molecular-curves'):['accepted'],('coupled-3d-law','network-cases'):['accepted'],('coupled-3d-law','conditional-signals'):['network_accepted','interpretation_valid'],('coupled-3d-law','paired-geometry-contrasts'):['common_accepted'],
 ('mace-fragments','fragment-relaxations'):['validation_pass','geometry_sanity_pass','energy_nonincrease_pass','converged'],
 ('hne-candidate-precision','matched-precision-diagnostic'):['passed'],('hne-candidate-precision','final-periodic-configurations'):['passed'],
 ('short-crosslink-md','short-md-replicas'):['all_runtime_checks_pass'],('hydroxylation-prestress','molecular-replicas'):['all_finite'],('hydroxylation-prestress','structural-validation'):['hydroxyl_chirality_preserved'],('four-bead-calibration','force-extension'):['mechanical_equilibrium_check']}
def sanitize(v):
 if isinstance(v,dict):return {k:sanitize(x) for k,x in v.items()}
 if isinstance(v,list):return [sanitize(x) for x in v]
 if isinstance(v,str) and '/Users/' in v:return re.sub(r'/Users/[^\s"\n]+','[local recovered source; see private provenance manifest]',v)
 return v

def model(m,i,evidence):
 nodes=m.get('nodes',m.get('coordinates_A'))
 b=m.get('edges',m.get('bonds',[]))
 r={'id':str(m.get('id',i)),'label':m.get('label',m.get('name',str(m.get('id',i)))),'nodes':nodes,'edges':[x[:2] for x in b],'units':m.get('units','Å'),'evidence':m.get('interpretation',m.get('note',evidence)),'frames':[]}
 for k in ['groups','labels','elements','atomic_numbers','recordBinding','amine_index','scaffold_n_index','hyp_sites','final_time_ps']:
  if k in m:r[k]=m[k]
 if 'initial_nodes' in m:r['referenceNodes']=m['initial_nodes'];r['referenceLabel']='Saved initial coordinates; not aligned to final structure'
 if 'initial_coordinates_A' in m:r['referenceNodes']=m['initial_coordinates_A'];r['referenceLabel']='Saved initial coordinates; not aligned to final structure'
 if 'forces_eV_A' in m:r['forces']=m['forces_eV_A'];r['forceUnits']='eV/Å'
 for j,f in enumerate(m.get('frames',[])):
  q={'nodes':f['nodes']}
  if 'time_ps' in f:q.update(time=f['time_ps'],timeUnits='ps',label=f"{f['time_ps']:g} ps")
  elif 'nominal_time_ps' in f:q.update(time=f['nominal_time_ps'],timeUnits='nominal ps; CG sampling coordinate, not physical kinetics',label=f"Nominal CG {f['nominal_time_ps']:g} ps")
  elif 'saved_frame_index' in f:q.update(label=f"Saved frame {f['saved_frame_index']} (time unavailable)",saved_frame_index=f['saved_frame_index'])
  else:q['label']=f'Saved frame {j} (time unavailable)'
  r['frames'].append(q)
 return r

inventory=[];checks=[]
for file in sorted((BASE/'ready').glob('*.json')):
 d=json.loads(file.read_text());models=[];e=d.get('evidence','Recovered saved data')
 if 'geometry' in d:models.append(model(d['geometry'],d['id']+'-fixed',e))
 for i,m in enumerate(d.get('molecules',[])):models.append(model(m,i,e))
 for i,m in enumerate(d.get('mappings',[])):
  n=len(m['nodes']);r=model(m,i,e);r['id']='mapping-'+r['id'];r['label']='Exact 9-Cα centroid projection: '+r['id']
  r['nodes']=m['nodes']+m['bead_positions_A'];r['groups']=m.get('groups',['Cα']*n)+['derived CG centroid']*4
  r['labels']=m.get('labels',[None]*n)+[{'projection':'centroid','bead':j+1,'source_CA_indices':g} for j,g in enumerate(m['bead_groups'])]
  r['edges']=m['edges']+[[a+n,b+n] for a,b in m['bead_edges']]
  r['mappingGuides']=[[idx,n+j] for j,g in enumerate(m['bead_groups']) for idx in g]
  r['edgeMeaning']='Cα chain adjacency and CG backbone adjacency; mappingGuides are illustrative projection guides, not chemical bonds or crosslinks'
  models.append(r)
 if 'spatial' in d:
  sp=d['spatial'];meshes=sp['meshes'];spec={s['id']:s for s in d['specifications']}
  for j,m in enumerate(meshes):
   r=model({'id':f'reference-mesh-{j}','label':f"Reference mesh: seed {m['seed']}, z {m['parent_z']}, {m['geometry']}",'nodes':m['positions'],'edges':m['edges'],'units':'normalized model length','recordBinding':{k:m[k] for k in ['seed','parent_z','geometry']}},j,'Saved reference fiber geometry, not deformed fiber coordinates')
   models.append(r)
  # Four matched law arms × two geometries at one exact seed/connectivity; selected examples only.
  candidates=[s for s in d['specifications'] if s.get('phase')=='aimnet' and s.get('arm') in ['full_coupled','diagonal_only'] and s.get('member')=='0' ]
  # member may be numeric: select exact m0/r0 identity, without inferring geometry.
  candidates=[s for s in d['specifications'] if s.get('phase')=='aimnet' and s.get('arm') in ['full_coupled','diagonal_only'] and s.get('replica')==0]
  selectedids={s['id'] for s in candidates}
  firstseed=min(m['seed'] for m in meshes);firstz=min(m['parent_z'] for m in meshes)
  for j,c in enumerate(sp['cases']):
   if c['specid'] not in selectedids or c['seed']!=firstseed or c['parent_z']!=firstz or c['geometry'] not in ['broad','narrow']:continue
   m=next(m for m in meshes if all(m[k]==c[k] for k in ['seed','parent_z','geometry']));n=len(m['positions']);s=spec[c['specid']]
   binding={k:c[k] for k in ['specid','seed','parent_z','geometry','accepted','residual']}
   r={'id':f'selected-network-case-{j}','label':f"Selected example: {s['arm']}, {c['geometry']}, seed {c['seed']}, z {c['parent_z']}",'nodes':m['positions']+c['sites'],'edges':m['edges'],'groups':['reference fiber node']*n+['deformed attachment site']*len(c['sites']),'units':'normalized model length','evidence':'Exact selected saved case. Reference fibers are undeformed; attachment sites and their forces are saved deformed outputs. No full fiber deformation is available.','recordBinding':binding,'forces':[None]*n+c['force_vectors'],'forceUnits':'normalized model force','frames':[]}
   models.append(r)
  d['modelSelectionNote']='24 saved reference meshes plus selected matched AIMNet m0/r0 full-coupled/diagonal-only narrow/broad examples at the smallest saved seed and parent_z. All scalar cases remain in tables. Reference fibers carry null force values.'
 for t in d.get('tables',[]):
  gates=GATES.get((d['id'],t['id']),[])
  if gates:
   for gate in gates:
    ix=t['columns'].index(gate);assert all(isinstance(r[ix],bool) or r[ix] is None for r in t['rows']), (d['id'],t['id'],gate)
   t['qualification']={'mode':'all_true','columns':gates,'missing':'unqualified','label':'Saved checks pass','scope':'Only the named saved runtime/numerical/mechanical checks; no broader biological or chemical validation implied'}
  else:t['qualification']=None
 for key in ['molecules','geometry','mappings','spatial']:d.pop(key,None)
 d['models']=models;d=sanitize(d)
 for m in models:
  assert m['nodes'] and all(len(n)==3 and all(isinstance(x,(float,int)) and math.isfinite(x) for x in n) for n in m['nodes'])
  assert all(len(x)==2 and all(isinstance(i,int) and 0<=i<len(m['nodes']) for i in x) for x in m['edges'])
  for key in ['groups','labels','elements','forces','referenceNodes']:
   if key in m:assert len(m[key])==len(m['nodes']),(file.name,m['id'],key)
  for f in m['frames']:assert len(f['nodes'])==len(m['nodes'])
 payload=json.dumps(d,separators=(',',':'),allow_nan=False).encode();assert b'/Users/' not in payload
 dest=OUT/file.name;dest.write_bytes(payload)
 inventory.append({'id':d['id'],'file':file.name,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'models':len(models),'frames':sum(len(m['frames']) for m in models),'tables':[{'id':t['id'],'rows':len(t['rows']),'qualification':t['qualification']} for t in d.get('tables',[])],'defaultView':d.get('defaultView')})
 checks.append({'dataset':d['id'],'exact_table_rows_and_columns':all(a['rows']==b['rows'] and a['columns']==b['columns'] for a,b in zip(json.loads(file.read_text()).get('tables',[]),d.get('tables',[]))),'node_edge_shape_checks':'pass','host_paths_absent':True})
(OUT/'inventory.json').write_text(json.dumps(inventory,indent=2));(OUT/'validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps({'datasets':len(inventory),'models':sum(x['models'] for x in inventory),'frames':sum(x['frames'] for x in inventory),'bytes':sum(x['bytes'] for x in inventory),'checks':all(c['exact_table_rows_and_columns'] for c in checks)}))
