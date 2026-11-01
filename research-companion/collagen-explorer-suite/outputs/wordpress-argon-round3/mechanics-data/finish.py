from pathlib import Path
import json,re,hashlib,ssl,urllib.request,csv,io,concurrent.futures,zipfile,xml.etree.ElementTree as E
R=Path(__file__).resolve().parent;D=R/'studies';posts={p['id']:p for p in json.loads((R/'posts.json').read_text())};B=Path('/path/to/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs')
def src(p,url=None):
 p=Path(p);b=p.read_bytes();return {'local_original':str(p),'sourceURL':url,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(d):
 f=D/(d['id']+'-'+d['slug']+'.json');f.write_text(json.dumps(d,allow_nan=False,separators=(',',':')));print(f.name,f.stat().st_size)
def make(id,slug,tables,limits,**extra):
 p=posts[id];d={'id':str(id),'slug':slug,'title':p['title'].replace('&nbsp;',' '),'sourceURLs':[p['url']],'evidence':'Saved synthetic dimensionless model outputs; no molecular or tissue calibration','units':'Dimensionless unless an explicit column unit is stated','limitations':limits,'tables':tables,'geometry':None,**extra};save(d)
def flat(d,stem='',out=None):
 out={} if out is None else out
 for k,v in d.items():
  n=(stem+'.' if stem else '')+k
  if isinstance(v,dict):flat(v,n,out)
  elif not isinstance(v,list):out[n]=v
 return out
for name in ['659-matched-budget-topologies','670-degree-controlled-triangles']:
 d=json.loads((D/(name+'.json')).read_text());old=d['tables'][0];rows=[flat(x) for x in old['rows']];d['tables']=[{**old,'id':'flat-records','title':'Saved scalar columns (nested JSON keys flattened without arithmetic)','columns':list(dict.fromkeys(k for row in rows for k in row)),'rows':rows}];save(d)
d=json.loads((D/'656-percolation-rigidity.json').read_text());geom=d.pop('rawGeometry');source=d.pop('geometrySource');p=sorted((B/'collagen-percolation-rigidity-20261031/results/states').glob('production-W3-*.json'))[0];state=json.loads(p.read_text());d['geometry']={'nodes':geom['positions'],'edges':[geom['edges'][i] for i in state['edge_ids']],'units':'dimensionless','label':'Fixed saved W3 specimen '+p.stem+'; independent of selected summary row','recordBinding':state['task'],'source':source,'stateSource':src(p)};save(d)
d=json.loads((D/'494-bonded-particle-bundle.json').read_text());v=d['savedViewer']['weak_links'];d['geometry']={'nodes':v['frames'][0]['xyz'],'edges':[],'frames':v['frames'],'units':'dimensionless reduced LAMMPS coordinates','label':'Weak-link36particle bundle: saved particle positions only; connectivity not encoded in this viewer data','recordBinding':v['record']};save(d)
# Parse printed PDF tables at their printed precision, never reconstruct missing histories.
p=R/'downloads/aging-preliminary.txt';text=p.read_text();cases=[];conditions=[];mode=None;starts=None
for line in text.splitlines():
 if 'Topology' in line and 'Scenario' in line:
  if 'Seed' in line:
   mode='cases';keys=['Topology','z','Seed','Scenario','Peak','First break','Span loss','Broken %','Work','Cycle diss.']
  else:
   mode='conditions';keys=['Topology','z','Scenario','Peak mean','Peak SD','E initial','Broken %','Cycle diss.','Fail / n']
  starts=[];at=0
  for key in keys:
   i=line.index(key,at);starts.append(i);at=i+len(key)
  continue
 if not mode or not re.match(r'^\s*(uniform|axial_bias|transverse_bias|modular|nested)\s+\d',line):continue
 values=[line[starts[i]:starts[i+1] if i+1<len(starts) else None].strip() for i in range(len(starts))]
 if mode=='cases':
  k=['topology','z','seed','scenario','peak_observed_stress','first_break_strain','span_loss_strain','broken_percent','work_to_endpoint','cycle_dissipation'];row=dict(zip(k,values))
  for key in k[1:]:
   if key!='scenario':row[key]=float(row[key]) if row[key] else None
  cases.append(row)
 else:
  k=['topology','z','scenario','peak_mean','peak_SD','E_initial','broken_percent','cycle_dissipation','fail_n'];row=dict(zip(k,values))
  for key in k[1:-1]:
   if key!='scenario':row[key]=float(row[key])
  row['fail_count'],row['n']=map(int,row.pop('fail_n').split('/'));conditions.append(row)
assert len(cases)==500 and len(conditions)==100,(len(cases),len(conditions))
source=src(R/'downloads/aging-preliminary.pdf','https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/collagen_aging_preliminary_report.pdf')
make(179,'sliding-stiffness-damage',[{'id':'cases','title':'500 individual outcomes at public PDF precision','columns':list(cases[0]),'rows':cases,'source':source},{'id':'conditions','title':'100 condition means and SD at public PDF precision','columns':list(conditions[0]),'rows':conditions,'source':source}],['Values extracted from public PDF at printed precision; full trajectory ZIP was not publicly uploaded.','Blank first-break/span-loss cells mean not observed by strain0.12, not zero.','Peak observed stress is not established ultimate strength; integrated endpoint work is not fracture toughness.','Same linear stiffness by construction in sliding arms; rigidity_only alters axial stiffness as separate control.'])
# Download exact public CSV provenance for the CPU/audit studies.
ctx=ssl.create_default_context(cafile='/opt/homebrew/etc/ca-certificates/cert.pem')
def get_table(slug,ref,file):
 url=f'https://raw.githubusercontent.com/InquilineKea/gaia-hackathon-2026-codex-openbci-motion-tracking/{ref}/OpenBCI-PostFable/Science/oxidative-tensegrity/research-records/codex-20261031/{slug}/analysis/{file}';dest=R/'raw'/slug/file;dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():
  with urllib.request.urlopen(url,context=ctx,timeout=45) as h:b=h.read(5000001)
  assert len(b)<5000001;dest.write_bytes(b)
 rows=list(csv.DictReader(dest.open()));
 for row in rows:
  for k,v in row.items():
   try:row[k]=float(v) if v else None
   except ValueError:pass
 return {'id':file,'title':file,'columns':list(rows[0]),'rows':rows,'source':src(dest,url)}
recipes=[(258,'graph-audit-largest-size-controls','dd6ffe8bd38b05f7c1fd3d262d282c3f33e3adbb',['graph-audit-summary.csv','mechanical-cases.csv','paired-time-step-contrasts.csv','time-step-pairs.csv']),(235,'controlled-topology-cpu','a02164fcf2e7a82363a334557b7be8c99394734b',['production-cases.csv','paired-contrasts.csv','paired-summary.csv','graph-summary.csv'])]
for id,slug,ref,files in recipes:
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:tables=list(pool.map(lambda f:get_table(slug,ref,f),files))
 make(id,slug,tables,['Synthetic CPU network study; never pool small-strain linearization with nonlinear H100 relaxation histories.','Use paired seed/graph groups and retained accepted/residual gates; uncertainty is finite-seed variation, not human tissue variability.','Graph connectedness and whole-mechanical rigidity are separate claims.'],sourceCommit=ref)
# Historical modulus ratios and separate FEniCSx acceptance denominators, documented public narrative values.
make(165,'historical-denominators',[{'id':'historical-ratios','title':'Historical fixed interval z_target3.0to4.4','columns':['campaign','grid','seeds','modulus_ratio'],'rows':[{'campaign':'earlier','grid':'12x12','seeds':2,'modulus_ratio':51.025},{'campaign':'expanded','grid':'16x16','seeds':4,'modulus_ratio':68.736}],'source':{'sourceURL':posts[165]['url'],'extraction':'Exact published narrative values; not recomputed'}},{'id':'numerical-gates','title':'Distinct acceptance denominators','columns':['gate','accepted','total'],'rows':[{'gate':'algebraic solves','accepted':4158,'total':4160},{'gate':'mesh comparisons','accepted':1341,'total':1600}],'source':{'sourceURL':posts[165]['url'],'extraction':'Exact published narrative values; denominators must stay separate'}}],['Historical campaigns have different grid size and seed counts; ratios are not paired experimental uncertainty.','Algebraic solvability does not establish mesh-qualified comparison or material calibration.','The newly published controlled-networks dashboard already supplies all1600FEniCSx comparison rows; link it rather than duplicate results.'],relatedExplorer='https://inquilinekea.github.io/scienceclaw-hackathon-2026/controlled-networks-20261101/')
