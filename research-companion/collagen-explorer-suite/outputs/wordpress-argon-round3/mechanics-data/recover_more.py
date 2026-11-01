from pathlib import Path
import json,csv,io,hashlib,urllib.request,ssl,zipfile,xml.etree.ElementTree as E
import recover as a
R=a.ROOT
# Existing public WordPress source/data supplements contain literal escaped line breaks.
class Pre(__import__('html.parser',fromlist=['HTMLParser']).HTMLParser):
 def __init__(self):super().__init__();self.a=[];self.b=None;self.hh=None;self.last=''
 def handle_starttag(self,t,attrs):
  if t in ['h2','h3']:self.hh=[]
  if t=='pre':self.b=[]
 def handle_data(self,s):
  if self.b is not None:self.b.append(s)
  if self.hh is not None:self.hh.append(s)
 def handle_endtag(self,t):
  if t in ['h2','h3'] and self.hh is not None:self.last=''.join(self.hh);self.hh=None
  if t=='pre' and self.b is not None:self.a.append((self.last,''.join(self.b)));self.b=None
p=json.load(open('outputs/wordpress-argon-visuals/source-content.json'))
for postid,studyid,slug in [(127,128,'collagen-elastin-load-sharing'),(204,205,'interface-gripping')]:
 x=next(x for x in p if x['id']==postid);parser=Pre();parser.feed(x['content']);tables=[]
 for heading,text in parser.a:
  if not heading.endswith('.csv'):continue
  normalized=text.replace('\\n','\n');dest=R/'raw'/str(postid)/heading;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(normalized)
  t=a.csv_table(dest,heading,heading,url=x['link']);t['source']['extraction']='Public code block labeled '+heading+'; only literal newline escapes normalized; no source executed.';t['source']['original_block_sha256']=hashlib.sha256(text.encode()).hexdigest();tables.append(t)
 a.study(studyid,slug,tables,['Synthetic dimensionless two-network calculation; not measured collagen/elastin tissue mechanics.','Separate collagen-only and both-phase grips; parallel load sharing is not independent evidence of interface strengthening.','Saved solver success/residual gates retained; mechanical cycle work is not an atomistic dissipation law.'],extra={'sourceSupplementURL':x['link']})
# Selected local archived paper/source-backed outputs.
p=a.REPO/'experiments/junction-angle-20261031/controlled/results-v2'
a.study(192,'junction-angle-controlled',[a.csv_table(p/f,f) for f in ['cuda_radius8.csv','cuda_radius16.csv','signaling_summary_r8.csv','signaling_summary_r16.csv','geometry_balance_r8.csv','geometry_balance_r16.csv']],['Earlier two-dimensional segment-length-matched H100 ensemble, separate from later3Dcavity results.','YAP/gene values arise from assumed nonlinear response laws; force shape changes do not imply universal gene directions.','Coupon-stiffness and mean-force matching are distinct controls; preserve seed pairs.'])
# Exact source tables from frozen public repository; local copies are checked into that source campaign.
p=a.REPO/'results/topo'
a.study(538,'organoid-scaffold-pareto',[a.csv_table(p/f,f) for f in ['ga_W12_designs.csv','ga_W12_evals.csv','reeval_W12x8_means.csv','reeval_W16_designs.csv','reeval_W16_evals.csv']],['104 short-search2D designs,14 reverified; original search scores are not equal evidence to re-evaluation.','Pa calibration, cell-readable/YAP window and transport proxy are model assumptions.','Alignment may improve strain transfer without improving worst-axis toughness; no3Dextrusion.'])
p=a.REPO/'results'
a.study(222,'setpoint-negative-control',[a.csv_table(p/f, f) for f in ['setpoint_vs_scar/summary.csv','setpoint_vs_scar/trajectories.csv','setpoint_vs_scar_360/summary.csv','setpoint_vs_scar_360/trajectories.csv']],['Assumed-input stiffness dynamics with numerical upper clipping; reaching a bound is not an interior homeostatic setpoint.','90day and360day saved trajectories are separate durations, not experimental aging observations.'])
# Download public workbook/PDF as data, no macros, formulas or embedded programs executed.
D=R/'downloads';D.mkdir(exist_ok=True);ctx=ssl.create_default_context(cafile='/opt/homebrew/etc/ca-certificates/cert.pem')
for name,url in [('rigidity.xlsx','https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/collagen-rigidity-source-and-results-20261031.xlsx'),('aging-preliminary.pdf','https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/collagen_aging_preliminary_report.pdf')]:
 dest=D/name
 if not dest.exists():
  with urllib.request.urlopen(url,context=ctx,timeout=60) as h:b=h.read(50000001)
  assert len(b)<=50000000;dest.write_bytes(b)
 a.source(dest,url)
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(D/'rigidity.xlsx') as z:
 assert sum(v.file_size for v in z.infolist())<100000000
 assert not any('vba' in v.filename.lower() for v in z.infolist())
 shared=[]
 if 'xl/sharedStrings.xml' in z.namelist():shared=[''.join(e.itertext()) for e in E.fromstring(z.read('xl/sharedStrings.xml'))]
 wb=E.fromstring(z.read('xl/workbook.xml'));rel={e.get('Id'):e.get('Target').lstrip('/') for e in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))};tables=[]
 for sheet in wb.find('m:sheets',ns):
  name=sheet.get('name');target=rel[sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')];target=target if target.startswith('xl/') else 'xl/'+target
  if name != 'Results':continue
  if any(k in name.lower() for k in ['source','protocol','manifest']):continue
  rows=[]
  for row in E.fromstring(z.read(target)).findall('.//m:sheetData/m:row',ns):
   vals={}
   for c in row:
    assert c.find('m:f',ns) is None,'formula present'
    idx=0
    for ch in ''.join(t for t in c.get('r','') if t.isalpha()):idx=idx*26+ord(ch)-64
    v=''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext('m:v',default='',namespaces=ns)
    if c.get('t')=='s':v=shared[int(v)]
    vals[idx-1]=v
   rows.append(vals)
  if not rows:continue
  heads=rows[0];data=[{heads[k]:a.num(v) for k,v in row.items() if k in heads} for row in rows[1:]]
  tables.append({'id':name,'title':name,'columns':list(heads.values()),'rows':data,'source':{'sourceURL':'https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/collagen-rigidity-source-and-results-20261031.xlsx','sheet':name,'sha256':hashlib.sha256((D/'rigidity.xlsx').read_bytes()).hexdigest()}})
 print('XLSX sheets',[(t['id'],len(t['rows'])) for t in tables])
 a.study(457,'rigidity-audit',tables,['324 finite-network commissioning cases;310passed and14rejected states, not empirical collagen validation.','Free-network zero modes, boundary-clamped stiffness and singular buckling branch must remain distinct.','Continuum export arbitrary stress units; no cohesive, fatigue or relaxation law.'])
(R/'manifest-more.json').write_text(json.dumps(a.SOURCES,indent=2))
