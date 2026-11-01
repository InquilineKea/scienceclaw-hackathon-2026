from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,hashlib,csv,math,ast,struct
R=Path(__file__).resolve().parent;D=R/'ready';POSTS={x['id']:x for x in json.loads((R/'source-posts.json').read_text())};receipts=[]
def meta(id,title,posts,evidence,limits,units):return {'id':id,'title':title,'postIds':posts,'sourceURLs':[POSTS[p]['url'] for p in posts if p in POSTS],'evidence':evidence,'limitations':limits,'units':units}
def val(v):
 if v in ['True','False']:return v=='True'
 if v=='':return None
 try:x=float(v);return int(x) if x.is_integer() else x
 except (ValueError,TypeError):return v

def write(d):
 p=D/(d['id']+'.json');p.write_text(json.dumps(d,separators=(',',':'),allow_nan=False));print(d['id'],p.stat().st_size)
def object_table(id,rows,title=None):
 cols=[]
 for row in rows:
  for k,v in row.items():
   if not isinstance(v,(list,dict)) and k not in cols:cols.append(k)
 return {'id':id,'title':title or id,'columns':cols,'rows':[[r.get(k) for k in cols] for r in rows]}
# Public workbook numeric and descriptive tables only; cached values, no formula execution.
f=R/'sources/comparative_collagen_mechanics_public_data.xlsx';ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(f) as z:
 assert not any(any(t in i.filename.lower() for t in ['vba','externallinks']) for i in z.infolist());assert sum(i.file_size for i in z.infolist())<5000000
 def sheet(i,id,title):
  rows=[]
  for row in E.fromstring(z.read(f'xl/worksheets/sheet{i}.xml')).findall('.//m:sheetData/m:row',ns):
   cells={}
   for c in row:
    col=''.join(x for x in c.get('r','') if x.isalpha());index=0
    for x in col:index=index*26+ord(x)-64
    assert c.find('m:f',ns) is None,'formula in extracted table'
    cells[index-1]=''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext('m:v',default='',namespaces=ns)
   rows.append(cells)
  cols=[rows[0][j] for j in sorted(rows[0])];return {'id':id,'title':title,'columns':cols,'rows':[[val(r.get(j,'')) for j in sorted(rows[0])] for r in rows[1:]]}
 d=meta('comparative-evidence-design','Comparative collagen evidence, missing measurements and proposed L9 design',[42,41,40],'Published observed tables plus explicitly proposed study/design rows',['Historical lifespan records are retained as source-specific values, not silently replaced by modern maxima.','Species triage scores are subjective prioritization, not measured collagen effects or predictions.','Missing-measurement cells remain missing; species longevity is not a calibrated matrix-strength modifier.','L9levels screen main effects; two-factor interactions alias. All27replicated construct rows are proposed/not run.','Observational species tissues and randomized acellular constructs are distinct inferential arms.'],{'pentosidine_quadratic_coefficient':'pmol/mg collagen/year², not instantaneous rate','skin_strength':'MPa before perforation, not tensile modulus','L9levels':'categorical proposed intervention levels'})
 d['sourceURLs'].append('https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/comparative_collagen_mechanics_public_data.xlsx');d['tables']=[sheet(2,'observed-mammals','Observed source-specific mammal pentosidine cohorts'),sheet(3,'observed-skin','Observed skin perforation endpoints and caveats'),sheet(4,'observed-endpoints','Observed collagen chemistry endpoints'),sheet(15,'species-priorities','Subjective species priorities with source/missing fields'),sheet(16,'orthogonal-L9','Proposed L9design with3replicates (27not-run rows)'),sheet(17,'ethical-targets','Proposed ethically governed tissue acquisition targets')];write(d)
# Completed short MD pilots: scalar rows and actual saved solute heavy-atom geometry only.
b=Path('/path/to/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs/collagen-glucosepane-dityrosine-20261031');p=b/'RESULT_SUMMARY.json';summary=json.loads(p.read_text());d=meta('short-crosslink-md','Glucosepane and dityrosine: short paired structural pilots',[164],'Twelve accepted50ps linked/control trajectories in distinct local contexts',['30ps unrestrained tails per50ps trajectory; not converged equilibrium mechanics.','Glucosepane and dityrosine use distinct contexts/force fields and support no cross-chemistry stiffness ranking.','Geometry/runtime checks do not validate force-field physical accuracy, hydrated constitutive transfer or reaction dynamics.','Original attempt/precision identifiers retained; no pooling as independent matched biological replicates.'],{'time':'ps','coordinates':'Å','constraint_error':'nm','temperature':'K','density':'g/mL'})
d['tables']=[object_table('short-md-replicas',summary['rows'],'Saved12replica structural/runtime summaries')];d['status']={k:v for k,v in summary.items() if k!='rows'};d['molecules']=[]
def npy(p):
 a=p.read_bytes();assert a[:6]==b'\x93NUMPY';off=10 if a[6]==1 else 12;hlen=struct.unpack('<H' if a[6]==1 else '<I',a[8:off])[0];h=ast.literal_eval(a[off:off+hlen].decode());assert not h['fortran_order'];shape=h['shape'];n=math.prod(shape);assert n<10000000;code={'<f4':'f','<f8':'d'}[h['descr']];v=list(struct.unpack('<'+str(n)+code,a[off+hlen:]));return shape,v
for row in summary['rows']:
 name=row['model'];rep=row['replica'];m=json.loads((b/f'prepared/{name}/{name}.json').read_text());atoms=m['atoms'];keep=[i for i,a in enumerate(atoms) if a['element']!='H'];mapping={old:i for i,old in enumerate(keep)};bonds=[[mapping[i],mapping[j]] for i,j,*_ in m['bonds'] if i in mapping and j in mapping];path=b/f'retrieved/{row["origin_attempt"]}/run/{name}/replica_{rep}/solute_frames_nm.npy'
 if not path.exists():path=b/f'retrieved/attempt-002/run/{name}/replica_{rep}/solute_frames_nm.npy'
 shape,a=npy(path);assert shape[1]==len(atoms) and shape[2]==3;frames=[]
 for frame in range(shape[0]):
  xyz=[[10*a[(frame*shape[1]+i)*3+j] for j in range(3)] for i in keep];frames.append({'saved_frame_index':frame,'nodes':xyz})
 d['molecules'].append({'id':name+'_r'+str(rep),'name':name,'nodes':frames[0]['nodes'],'elements':[atoms[i]['element'] for i in keep],'bonds':bonds,'labels':[{'atom':atoms[i]['name'],'resindex':atoms[i]['resindex']} for i in keep],'frames':frames,'units':'Å','recordBinding':{'model':name,'replica':rep,'origin_attempt':row['origin_attempt']},'note':'Saved solute frames only; frame index is retained because this export does not itself carry timestamps. Solvent omitted from display.'});receipts.append({'local_source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
write(d)
# Decorin/collagen/GAG projected residue geometry, explicit arbitrary encounter-pose limitation.
b=Path('/path/to/Codex/2026-10-31/referenced-chatgpt-conversation-this-is-an-2/outputs/collagen-gag-pipeline');p=b/'inputs/target_pilot/prepared/collagen_PYD_decorin_DS40_encounter.json';m=json.loads(p.read_text());nodes=[];labels=[];groups=[];resmap={}
for i,res in enumerate(m['residues']):
 ids=list(res['map'].values());heavy=[j for j in ids if m['atoms'][j]['element']!='H'];ca=res['map'].get('CA');pos=m['atoms'][ca]['xyz'] if ca is not None else [sum(m['atoms'][j]['xyz'][k] for j in heavy)/len(heavy) for k in range(3)];nodes.append(pos);chain=res['chain'];group='decorin' if chain=='D' else 'DS/CS40GAG' if chain=='H' else 'modeledN-glycan' if chain in ['J','K','L'] else 'collagenCoupon';groups.append(group);labels.append({'chain':chain,'residue':res['id'],'resname':res['name'],'projection':'Cα' if ca is not None else 'heavy-atom residue centroid','component':group});resmap[i]=len(nodes)-1
edges=set()
for i,j in m['bonds']:
 a=m['atoms'][i]['resindex'];c=m['atoms'][j]['resindex']
 if a!=c:edges.add(tuple(sorted([resmap[a],resmap[c]])))
d=meta('decorin-collagen-gag','Why separated-component stability is not bound-interface mechanics',[152],'Prepared arbitrary encounter pose + bounded20ps solvated stability test',['Reference geometry is a prepared arbitrary nonintersecting encounter seed, not a validated binding pose.','Protein nodes show Cα; carbohydrates/caps show heavy-atom residue centroids, connected by projected inter-residue covalent bonds.','773703atom solvation/pilot includes9900solute atoms; solvent and ions omitted from this residue-level display.','20ps bounded stability and retained geometry do not establish binding, interface mechanics or equilibrium.','Separate200ps branch remains unverified here; no GAGmediated sliding/viscosity parameter is supplied.'],{'coordinates':'Å','pilot_duration':'ps','reported_initial_min_separation':'nm'})
d['geometry']={'nodes':nodes,'edges':[list(x) for x in sorted(edges)],'units':'Å','groups':groups,'labels':labels,'label':'Prepared collagen/decorin/GAG encounter seed (Cα/residue-centroid projection)','recordBinding':{'type':'fixed_prepared_encounter','binding_pose_validated':False,'note':'Independent starting model, not a trajectory frame or bound interface.'}};d['tables']=[object_table('component-separation',[{'pair':'decorin–collagen','initial_min_distance_nm':1.139,'evidence':'Reported initial heavy-atom separation in original post152; not a binding distance'},{'pair':'GAG–collagen','initial_min_distance_nm':3.485,'evidence':'Reported initial heavy-atom separation in original post152; not a binding distance'}])];accept=json.loads((b/'inputs/solvated_pilot/accepted-pilot.json').read_text());d['status']={k:v for k,v in accept.items() if k in ['accepted','pilot','full_tendon_run','equilibrium_or_binding_validation','criteria','final_state_attributes']};receipts.append({'local_source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size});write(d)
(R/'remaining-extraction-receipts.json').write_text(json.dumps(receipts,indent=2))
