from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,csv,hashlib,math
R=Path(__file__).resolve().parent;D=R/'studies'
def read(id):return json.loads(next(D.glob(id+'-*.json')).read_text())
def save(d):next(D.glob(d['id']+'-*.json')).write_text(json.dumps(d,allow_nan=False,separators=(',',':')))
def flat(d,p='',out=None):
 out={} if out is None else out
 for k,v in d.items():
  n=(p+'.' if p else '')+k
  if isinstance(v,dict):flat(v,n,out)
  elif not isinstance(v,list):out[n]=v
 return out
# Full324-case spectra and eight exact load-path controls, extracted only from raw JSON chunks.
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};p=R/'downloads/rigidity.xlsx';sha=hashlib.sha256(p.read_bytes()).hexdigest()
with zipfile.ZipFile(p) as z:
 ss=[]
 if 'xl/sharedStrings.xml' in z.namelist():ss=[''.join(e.itertext()) for e in E.fromstring(z.read('xl/sharedStrings.xml'))]
 def vals(row):
  a=[]
  for c in row:
   v=''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext('m:v',default='',namespaces=ns)
   if c.get('t')=='s':v=ss[int(v)]
   a.append(v)
  return a
 rows=[vals(x) for x in E.fromstring(z.read('xl/worksheets/sheet5.xml')).findall('.//m:row',ns)[1:]]
 def document(name):return json.loads(''.join(x[2] for x in sorted([x for x in rows if x[0]==name],key=lambda x:int(x[1]))))
 data=document('results/pilot_final/all_results.json');paths=document('results/controls/load_paths.json');d=read('457');d['spectra']=[{'case_id':x['case_id'],'accepted':x['accepted'],'family':x['spec']['family'],'architecture':x['spec']['architecture'],'constrained':x['hessian']['constrained'],'unconstrained':x['hessian']['unconstrained']} for x in data];source={'sourceURL':d['tables'][0]['source']['sourceURL'],'sheet':'Raw Files','relative_file':'results/controls/load_paths.json','workbookSHA256':sha};t=[flat(x) for x in paths['rows']];d['tables'].append({'id':'load-path-controls','title':'Eight saved matched axial-budget load-path controls','columns':list(dict.fromkeys(k for x in t for k in x)),'rows':t,'source':source});d['limitations'].append('Spectra retain signed eigenvalues and each saved tolerance. Near-zero free-network modes include rigid-body/component motions; do not interpret every zero as a nontrivial mechanism or tiny negative roundoff as buckling.');save(d)
# Exact join by saved case ID supplies ownership/grip labels to scalar table.
d=read('677');by={x['case_id']:x for x in d['savedCases']};rows=d['tables'][0]['rows']
for row in rows:
 c=by[row['case_id']]
 for k in ['ownership','placement','grips','arm_k','backbone_EA','L','nodes_per_owner','junction_multiplicity_count']:row[k]=c[k]
d['tables'][0]['columns']=list(rows[0]);save(d)
# Saved cycle histories for all four primary BPM conditions, maintaining recorded order.
d=read('494');rows=[]
for name,v in d['savedViewer'].items():
 for i,x in enumerate(v['history']):rows.append({'case':name,'recorded_index':i,**x})
d['tables'].append({'id':'recorded-cycles','title':'Saved reduced-time cycle histories; internal grip force sign','columns':list(rows[0]),'rows':rows,'source':d['viewerSource']});save(d)
# Earlier unmatched pilot remains separate from the controlled campaign.
d=read('192');root=Path('/path/to/user/Documents/GitHub/gaia-hackathon-2026/OpenBCI-PostFable/Science/oxidative-tensegrity/experiments/junction-angle-20261031/h100-results')
for f in ['cuda_radius8.csv','cuda_radius16.csv']:
 p=root/f;r=list(csv.DictReader(p.open()))
 for x in r:
  for k,v in x.items():
   try:x[k]=float(v) if v else None
   except ValueError:
    if v in ['True','False']:x[k]=v=='True'
 d['tables'].append({'id':'unmatched-pilot-'+f,'title':'Earlier unmatched pilot: '+f,'columns':list(r[0]),'rows':r,'source':{'local_original':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}})
save(d)
defaults={
 '593':('results','attachmentThickness','resistanceRatio','pattern',{'series':'main','dose':0.4,'attachmentK':100.0}),
 '574':('results','attachmentThickness','resistanceRatio','pattern',{'series':'main','arm':'bending_asymmetric','dose':0.4}),
 '670':('flat-records','graph.triangle_count','models.0.0001.responses.shear.coefficient','arm',{'task.W':3,'task.k':10}),
 '659':('flat-records','graph.mean_local_clustering_isolates_zero','responses.shear.coefficient','task.arm',{'task.W':3,'task.occupancy_index':10}),
 '656':('mechanics','p','load_bearing_probability','mode',{'W':3,'eta':0}),
 '494':('recorded-cycles','grip_displacement','internal_grip_force_x','case',{}),
 '677':('cases','ownership','linear_external_stiffness','placement',{'grips':'staggered','junction_count':6}),
 '128':('tension_sweep.csv','strain','stress','scenario',{'seed':11}),
 '205':('results/group_means.csv','stiffness','force20_mean','grip',{'law':'permanent','density':0.6}),
 '192':('cuda_radius16.csv','angle_sd_deg','force_cv','jitter',{'lock':0}),
 '538':('ga_W12_designs.csv','toughness','strain_transfer','label',{}),
 '222':('setpoint_vs_scar_360/trajectories.csv','day','logS','dose',{'bounds':'0.4:2.5','init_logS':-0.35667494393873245}),
 '457':('Results','free_bar_zero_modes','linear_Gxy_au','architecture',{}),
 '179':('cases','z','peak_observed_stress','scenario',{'topology':'uniform'}),
 '258':('mechanical-cases.csv','G0','retention','arm',{}),
 '235':('production-cases.csv','clustering','G0','arm',{}),
 '165':('historical-ratios','seeds','modulus_ratio','campaign',{})}
notes={
 '235':'accepted counts accepted rewiring proposals, not numerical validity; use converged and eligible_for_matched_comparison.',
 '258':'Use converged for numerical mechanics; graph accepted counts are rewiring counters. Time-step pairs and raw cases have distinct groups.',
 '656':'qualified/n_structures/spanning_count are counts, not boolean gates. Keep eta and mode separate.',
 '457':'accepted_1_or_0 is the actual310/324case validity gate.',
 '574':'accepted is boolean; every current final4352row passed its stated gates. Endpoint rechecks remain separate columns.',
 '593':'accepted is boolean; every current final620row passed its stated gates. Legacy_rigid is not pooled with main.',
 '494':'finite/bonds_monotone and source40checks underlie acceptance; seven protocol controls are not independent geometry replicates.',
 '179':'Printed PDF values; blank failure thresholds are right-censored at strain0.12, not zero.'}
for id,(table,x,y,color,filters) in defaults.items():
 d=read(id);t=next(t for t in d['tables'] if t['id']==table);cols=t['columns'];d['defaultView']={'table':table,'x':x,'y':y,'color':color,'filters':filters};d['gateSemantics']=notes.get(id,'Retain stated per-row solver/acceptance fields and scientific limitations; do not infer missing gates.');
 if x not in cols or y not in cols or color not in cols:d['defaultView']['needsAdapterReview']={'missing':[v for v in [x,y,color] if v not in cols]}
 save(d)
print('Curated default metadata; gate semantics;324spectra;8loadpathcontrols;BPMhistories;ownershiplabels')
