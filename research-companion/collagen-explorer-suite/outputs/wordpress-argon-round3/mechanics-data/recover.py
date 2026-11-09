"""Owned static saved-data extraction. Never executes study source or workbook formulas."""
from pathlib import Path
import json,csv,hashlib,shutil,math,re,ssl,urllib.request,concurrent.futures
ROOT=Path(__file__).resolve().parent
POSTS={x['id']:x for x in json.loads((ROOT/'posts.json').read_text())}
BASE=Path('/path/to/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs')
REPO=Path('/path/to/user/Documents/GitHub/gaia-hackathon-2026/OpenBCI-PostFable/Science/oxidative-tensegrity')
SOURCES=[]
def source(p,url=None):
 p=Path(p);b=p.read_bytes();entry={'local_original':str(p),'sourceURL':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};SOURCES.append(entry);return entry

def clean(x):
 if isinstance(x,float) and not math.isfinite(x):return None
 if isinstance(x,list):return [clean(v) for v in x]
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 return x

def num(v):
 if v=='':return None
 if v.lower() in ['true','false']:return v.lower()=='true'
 try:return float(v)
 except ValueError:return v

def csv_table(p,id='results',title=None,url=None):
 src=source(p,url); rows=list(csv.DictReader(Path(p).open())); rows=[{k:num(v) for k,v in x.items()} for x in rows];return {'id':id,'title':title or id,'columns':list(rows[0]) if rows else [],'rows':rows,'source':src}
def js_table(p,key,id='results',title=None,url=None):
 d=json.loads(Path(p).read_text());rows=d[key] if key else d;return {'id':id,'title':title or id,'columns':list(rows[0]) if rows and isinstance(rows[0],dict) else [],'rows':rows,'source':source(p,url)}
def study(id,slug,tables,limits,geometry=None,extra=None):
 p=POSTS[id];d={'id':str(id),'slug':slug,'title':p['title'].replace('&nbsp;',' '),'sourceURLs':[p['url']], 'evidence':'Saved synthetic dimensionless mechanical study; no molecular or tissue calibration','units':'Dimensionless model units unless a column explicitly names units','limitations':limits,'tables':tables,'geometry':geometry}
 if extra:d.update(extra)
 q=ROOT/'studies'/f'{id}-{slug}.json';q.parent.mkdir(exist_ok=True);q.write_text(json.dumps(clean(d),allow_nan=False,separators=(',',':')));print(q.name,q.stat().st_size)
 return d

def beam_example(p):
 e=json.loads(Path(p).read_text())[0];pos=e['pos'];u=e['u'];return {'nodes':[pos[i:i+3] for i in range(0,len(pos),3)],'edges':[v[:2] for v in e['edges']],'displacements':[u[6*i:6*i+3] for i in range(len(pos)//3)],'rotations':[u[6*i+3:6*i+6] for i in range(len(pos)//3)],'displacementLayout':'Interleaved6DOFpernode: translation0:3,rotation3:6','units':'dimensionless','label':'Saved 3D cavity example; seed3100, bending_asymmetric, dispersed damage0.4. Fixed example independent of other selected scalar rows.','recordBinding':e['row'],'source':source(p)}

se=Path('/path/to/Codex/2026-10-31/se/outputs')
p=se/'organoid-finite-attachment-followup';study(593,'finite-attachment',[csv_table(p/'results.csv')],['Accepted solver states only are eligible for mechanical contrasts; preserve accepted/status columns.','Attachment stiffness and layer thickness are assumed dimensionless controls, not molecular or cell calibration.','620 saved cases; geometry is not embedded in this table.'])
p=se/'organoid-damage-beam-followup';study(574,'shell-patch-damage',[csv_table(p/'results.csv')],['Saved beam-network/cavity model, not organoid growth or biochemical YAP validation.','Accepted/status and endpointRechecked gates must remain explicit; rejected rows are not zero-valued outcomes.','The example geometry is one saved realization, not a reconstruction of the chosen scalar row.'],beam_example(p/'examples.json'))
p=BASE/'collagen-degree-clustering-20261031';rows=[json.loads(s) for s in (p/'results/records.jsonl').read_text().splitlines() if s.strip()];study(670,'degree-controlled-triangles',[{'id':'records','title':'Exact saved degree-controlled records','columns':list(rows[0]),'rows':rows,'source':source(p/'results/records.jsonl')}],['Degree-controlled triangle changes have effects dependent on size/density; do not pool into one universal clustering effect.','Whole-sample zero modes differ from boundary-clamped stiffness.','One optimized graph per paired starting group; not biological replicates.'])
p=BASE/'collagen-topology-budget-20261031';rows=[json.loads(s) for s in (p/'results/records.jsonl').read_text().splitlines() if s.strip()];study(659,'matched-budget-topologies',[{'id':'records','title':'Exact saved four-arm topology records','columns':list(rows[0]),'rows':rows,'source':source(p/'results/records.jsonl')}],['Matched material/orientation budget is not exact matching of all graph features.','Clamped axial/shear response does not establish whole-sample infinitesimal rigidity.','Synthetic FCC candidate scaffold; no tissue calibration.'])
p=BASE/'collagen-percolation-rigidity-20261031';geom=json.loads((p/'results/geometry_W3.json').read_text());study(656,'percolation-rigidity',[csv_table(p/'results/GRAPH_SUMMARY.csv','graph'),csv_table(p/'results/MECHANICAL_SUMMARY.csv','mechanics'),csv_table(p/'results/RANK_CONTROLS.csv','rank-controls')],['Geometric spanning, clamped stiffness and free-sample infinitesimal rigidity are distinct tests.','Finite FCC lattices, 18 dilution steps; thresholds are not infinite-system transitions.','Central and weak-bending models require separate acceptance flags.'],extra={'rawGeometry':geom,'geometrySource':source(p/'results/geometry_W3.json')})
p=BASE/'collagen-bpm-nebius-pilot-20261031';study(494,'bonded-particle-bundle',[csv_table(p/'RESULTS.csv')],['Seven accepted36particle trajectories; paired numerical/output controls are not independent geometry replicates.','LAMMPS bpm/rotational is a coarse mechanical surrogate, not collagen molecular chemistry.','External loop work contains kinetic/contact/viscous terms and is not molecular friction free energy.'],extra={'savedViewer':json.loads((p/'VIEWER_DATA.json').read_text()),'viewerSource':source(p/'VIEWER_DATA.json')})
p=Path('/path/to/Codex/2026-10-30/can-you-read-https-drive-google/outputs/colbuilder-study/pyd-ownership-surrogate');s=(p/'ownership-clustering-actual-solver.html').read_text();tag='<script id="data" type="application/json">';start=s.index(tag)+len(tag);d=json.loads(s[start:s.index('</script>',start)]);study(677,'junction-ownership',[{'id':'cases','title':'Saved scalar ownership controls','columns':list(d['summary']['cases'][0]),'rows':d['summary']['cases'],'source':source(p/'ownership-clustering-actual-solver.html')}],['One-dimensional three-backbone,31node shear-lag mechanical surrogate.','Schematic owner offsets are presentation layout, not saved3D collagen coordinates.','Changing number of backbone owners is not an atomistic prediction of pyridinoline or glucosepane chemistry.','Full-end vs staggered grips are separate controls; compare exact same arm count.'],extra={'savedCases':d['cases'],'savedSummary':d['summary']})
(ROOT/'manifest.json').write_text(json.dumps(SOURCES,indent=2))
