from pathlib import Path
import json,csv,hashlib,collections,zipfile,xml.etree.ElementTree as E,math
R=Path(__file__).resolve().parent;D=R/'ready';D.mkdir(exist_ok=True);manifest=[]
POSTS={x['id']:x for x in json.loads((R/'source-posts.json').read_text())}
BASE=Path('/path/to/user/Documents/GitHub/gaia-hackathon-2026/OpenBCI-PostFable/Science/oxidative-tensegrity')
ATLAS=Path('/path/to/Codex/2026-10-30/can-you-read-https-drive-google/outputs/carbonyl-damage-atlas')
def value(v):
 if v in ['True','False']:return v=='True'
 if v=='':return None
 try:x=float(v);return int(x) if x.is_integer() else x
 except (ValueError,TypeError):return v

def csvtable(path,id,title=None,keep=None):
 with path.open() as h:r=csv.DictReader(h);cols=keep or r.fieldnames;rows=[[value(row.get(c,'')) for c in cols] for row in r]
 manifest.append({'local_source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'table_id':id});return {'id':id,'title':title or id,'columns':cols,'rows':rows}
def table_objects(id,rows,title=None):
 cols=[]
 for row in rows:
  for k,v in row.items():
   if k not in cols and not isinstance(v,(list,dict)):cols.append(k)
 return {'id':id,'title':title or id,'columns':cols,'rows':[[row.get(k) for k in cols] for row in rows]}
def write(d):
 p=D/(d['id']+'.json');p.write_text(json.dumps(d,separators=(',',':'),allow_nan=False));print(d['id'],p.stat().st_size,'tables',[(t['id'],len(t['rows'])) for t in d.get('tables',[])])
def meta(id,title,posts,evidence,limitations,units):return {'id':id,'title':title,'postIds':posts,'sourceURLs':[POSTS[p]['url'] for p in posts if p in POSTS],'evidence':evidence,'limitations':limitations,'units':units}

# Actual PDB reference structures: CA traces only; no invented sidechain or chemical lesion.
for code,posts in [('1DZI',[71,60,54]),('1K6F',[54,31])]:
 p=R/'sources'/(code+'.pdb');lines=p.read_text().splitlines();nodes=[];labels=[];groups=[];edges=[];prev={};chains=collections.Counter()
 for line in lines:
  if line.startswith('ENDMDL'):break
  if not line.startswith(('ATOM  ','HETATM')):continue
  atom=line[12:16].strip();res=line[17:20].strip();chain=line[21];idx=line[22:27].strip();alt=line[16]
  if alt not in [' ','A']:continue
  if atom!='CA' and res not in ['MG','MN','CA','ZN']:continue
  if res=='HOH':continue
  pos=[float(line[a:b]) for a,b in [(30,38),(38,46),(46,54)]];i=len(nodes);nodes.append(pos);labels.append({'chain':chain,'residue':idx,'resname':res,'atom':atom,'sourceSerial':int(line[6:11])});groups.append(chain);chains[chain]+=1
  if atom=='CA':
   if chain in prev and math.dist(nodes[prev[chain]],pos)<5.5:edges.append([prev[chain],i])
   prev[chain]=i
 d=meta('reference-'+code.lower(),('Integrin α2 I-domain and collagen-mimetic recognition interface' if code=='1DZI' else 'Collagen triple-helix PPG reference geometry'),posts,'Experimental PDB reference coordinates; unmodified engineered construct',['Cα backbone trace; sidechains and chemistry omitted.','No MG-H1/HNE lesion, affinity, occupancy or mechanical response is simulated.','PDB author chain/residue identifiers are retained; no full-length canonical collagen mapping is implied.'],{'coordinates':'Å','contact_distance':'Å'})
 d['sourceURLs']+=['https://www.rcsb.org/structure/'+code,'https://files.rcsb.org/download/'+code+'.pdb'];d['geometry']={'nodes':nodes,'edges':edges,'units':'Å','label':code+' original reference coordinates (Cα traces and metal ions)','groups':groups,'labels':labels,'recordBinding':{'type':'fixed_reference','pdb':code,'note':'Independent reference structure; not a geometry of scalar sweep cases or a damaged state.'},'chainCounts':dict(chains)}
 if code=='1DZI':d['tables']=[csvtable(ATLAS/'structural-contact-candidates.csv','reference-contacts','Reference collagen–integrin nearest atom contacts')]
 manifest.append({'local_source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'structure_id':code});write(d)

# Carbonyl kinetics: exactly saved nominal timecourses and terminal assumed-input quantiles.
d=meta('carbonyl-scenarios','Carbonyl damage: tissue turnover and lesion-location scenarios',[54,60],'Assumed-input scenario outputs, not empirical damage kinetics',['Quantiles summarize assumed parameter draws; they are not empirical confidence intervals.','Timecourses are saved nominal scenarios; terminal quantiles are not time-dependent prediction bands.','Sequence-eligible sites are not observed damaged residues or verified canonical-to-PDB mappings.'],{'time_days':'days','time_years':'years','fraction':'fraction of site-pool states'})
d['tables']=[csvtable(ATLAS/'illustrative-results/timecourses.csv','timecourses','Saved nominal tissue/pool timecourses'),csvtable(ATLAS/'illustrative-results/summary.csv','terminal-quantiles','Terminal assumed-input scenario quantiles'),csvtable(ATLAS/'structural-contact-candidates.csv','contact-candidates','PDB reference geometry contacts')];d['parameterRegistry']=json.loads((ATLAS/'parameter-registry.json').read_text());d['prioritySites']=json.loads((ATLAS/'priority-sites.json').read_text());write(d)

# Coupled law source: genuine reference meshes and 3D deformed attachment-site force vectors.
b=BASE/'experiments/dityrosine-solvent-coupled-3d-20261031';v=json.loads((b/'viewer-data.json').read_text());d=meta('coupled-3d-law','Coupled stretch–rotation laws and conditional 3D adhesion forces',[407,271,101],'Executed molecular calculations + conditional normalized 3D network transfers',['No wet linked/control pair passed law transfer; hydrated network/YAP inference withheld.','AIMNet members0/3 are related models; endpoint poses are not a converged equilibrium ensemble.','YAP/gene values are assumed one-way scalar-force response laws, not biological validation.','Reference network fibers remain undeformed reference meshes; saved deformed positions/forces are interface sites only.','Coupling comparisons require common accepted seeds; missing/failed cases must remain visibly unavailable.'],{'positions':'normalized unit-cell coordinates','force_vectors':'normalized model force','rho':'dimensionless local coupling','molecular_energy':'kJ/mol','theta':'radian'})
d['tables']=[csvtable(b/'fit-gates.csv','fit-gates','Original mixed-law acceptance gates'),csvtable(b/'molecular-curves.csv','molecular-curves','Saved mixed-coordinate molecular states'),table_objects('network-cases',v['cases'],'Saved 3D attachment-site cases'),table_objects('law-specifications',v['specs'],'Law transfer and coupling specifications')]
d['spatial']={'meshes':v['meshes'],'cases':[{k:c[k] for k in ['specid','seed','parent_z','geometry','accepted','residual','sites','force_vectors']} for c in v['cases']],'interpretation':v['interpretation'],'binding':'Join case→mesh on seed,parent_z,geometry; specid→specs.id. Do not substitute unresolved/missing cases. Full deformed fiber nodes are not saved.'}
d['specifications']=v['specs'];d['molecularSummary']=json.loads((b/'SUMMARY.json').read_text());d['sourceURLs']+=['https://humanavianaisymbiosis.wordpress.com/2026/10/31/what-molecular-coupling-changes-in-our-earlier-collagen-deformation-runs-interim-3d-results/'];manifest.append({'local_source':str(b/'viewer-data.json'),'sha256':hashlib.sha256((b/'viewer-data.json').read_bytes()).hexdigest(),'bytes':(b/'viewer-data.json').stat().st_size,'dataset_id':d['id']});write(d)

# Newer wet controls: intentionally separate chronology from original molecular campaign.
b=BASE/'experiments/wet-fit-controls-20261031';summary=json.loads((b/'SUMMARY.json').read_text());factor=json.loads((b/'FACTORIAL-SUMMARY.json').read_text());ewald=json.loads((b/'ewald-accuracy.json').read_text());d=meta('wet-transfer-gates','Why hydrated-law transfer remains blocked',[407,271,164,31],'Numerical derivative/profile diagnostics; no admissible hydrated transfer',['Keep these later controls separate from the earlier78accepted wet deformation states.','Fixed-pose derivative agreement does not establish relaxed solvent/mechanical equivalence.','0admissible wet pairs; no new3Dnetwork states from these controls.'],{'derivative_error':'as explicitly named in source columns; mixed generalized coordinates','energy':'kJ/mol'})
d['tables']=[table_objects('later-gate-summary',[{k:v for k,v in summary.items() if isinstance(v,(bool,int,float,str)) and not k.startswith(('synced','canonical'))}]),table_objects('factorial-controls',factor),csvtable(b/'derivative-curves.csv','derivative-curves','Saved finite-difference derivative checks')];d['fixedPoseEwald']=ewald;write(d)

# MACE fragment preparation pilot: actual saved initial/final atoms/bonds and local forces.
b=Path('/path/to/Codex/2026-10-31/referenced-chatgpt-conversation-this-is-an-3/outputs/public-scienceclaw-data/pilot_run');struct=json.loads((b/'structures.json').read_text());res=json.loads((b/'results.json').read_text());d=meta('mace-fragments','Small-molecule geometry pilot and model disagreement',[96],'Executed eight-conformer fragment geometry pilot; not collagen mechanics',['Minimal neutral fragments are not crosslinked triple helices or hydrated fibrils.','Nonreactive peak force is a scan proxy, not covalent rupture force.','can_update_tissue_stiffness=false; cross-model and conformer disagreement retained.'],{'coordinates':'Å','energy':'eV','force':'eV/Å','curvature':'eV/Å²'})
d['molecules']=[]
for s in struct:
 row=next(x for x in res['results'] if x['structure_id']==s['structure_id']);d['molecules'].append({'id':s['structure_id'],'name':s['name'],'interpretation':s['interpretation'],'atomic_numbers':s['atomic_numbers'],'bonds':s['bonds'],'initial_coordinates_A':s['initial_coordinates_A'],'coordinates_A':row['coordinates_A'],'forces_eV_A':row['forces_eV_A'],'seed':s['seed']})
d['tables']=[table_objects('fragment-relaxations',res['results'])];a=BASE/'results/alchemi_brev';off=json.loads((a/'crosslink_mace_off.json').read_text());mp=json.loads((a/'crosslink_mace_mp.json').read_text());comp=json.loads((a/'crosslink_model_comparison.json').read_text());d['tables'].append(table_objects('cross-model-summary',comp['chemistries']));scans=[]
for model,data in [('MACE-OFF',off),('MACE-MP',mp)]:
 for chem,c in data['crosslinks'].items():
  for i,e in enumerate(c['E_eV']):scans.append({'model':model,'chemistry':chem,'sample_index':i,'relative_energy_eV':e,'L0_A':c['L0_A'],'k_eV_A2':c['k_eV_A2'],'peak_force_eV_A':c['peak_force_eV_A']})
d['tables'].append(table_objects('fragment-scan-indices',scans,'Saved scan energies by original sample index; no reconstructed extension axis'));d['modelComparisonNotes']=comp.get('note');write(d)

(R/'local-source-manifest.json').write_text(json.dumps(manifest,indent=2))
