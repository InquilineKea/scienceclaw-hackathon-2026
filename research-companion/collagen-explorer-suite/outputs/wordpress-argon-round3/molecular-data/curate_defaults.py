from pathlib import Path
import json,collections,hashlib
R=Path(__file__).resolve().parent;D=R/'ready';BASE=Path('/path/to/user/Documents/GitHub/gaia-hackathon-2026/OpenBCI-PostFable/Science/oxidative-tensegrity')
def table(id,rows,title=None):
 cols=[]
 for r in rows:
  for k,v in r.items():
   if not isinstance(v,(list,dict)) and k not in cols:cols.append(k)
 return {'id':id,'title':title or id,'columns':cols,'rows':[[r.get(c) for c in cols] for r in rows]}
p=D/'hne-candidate-precision.json';d=json.loads(p.read_text());src=Path('/path/to/Codex/2026-10-30/referenced-chatgpt-conversation-this-is-an/outputs/gaff2-periodic-fix-2026-11-01/gcp-results/results/periodic-validation.json');v=json.loads(src.read_text());rows=[]
for state,r in v['states'].items():
 for f in r['frames']:rows.append({'state':state,**{k:x for k,x in f.items() if not isinstance(x,(dict,list))}})
d['tables'][1]=table('final-periodic-configurations',rows);d['provenanceNote']='Current data recovered locally from completed GCP export; public report and supplement URLs identify the finished campaign. The complete binary archive remains local; no invented public raw-file path.';d['sourceURLs'].append('https://humanavianaisymbiosis.wordpress.com/2026/10/31/gromacs-collagen-4hne-reproducibility-supplement/#gaff2-periodic-fix-20261101');p.write_text(json.dumps(d,separators=(',',':')))
p=D/'mace-fragments.json';d=json.loads(p.read_text());rows=[]
for model,file in [('MACE-OFF','crosslink_mace_off.json'),('MACE-MP','crosslink_mace_mp.json')]:
 v=json.loads((BASE/'results/alchemi_brev'/file).read_text())
 for chem,c in v['crosslinks'].items():
  assert len(c['E_eV'])==len(c['L_A'])
  for i,(energy,length) in enumerate(zip(c['E_eV'],c['L_A'])):rows.append({'model':model,'chemistry':chem,'sample_index':i,'relative_energy_eV':energy,'length_A':length,'reference_L0_A':c['L0_A'],'fractional_extension':length/c['L0_A']-1})
d['tables'][-1]=table('fragment-scan-curves',rows,'Actual saved scan lengths and relative energies');p.write_text(json.dumps(d,separators=(',',':')))
p=D/'coupled-3d-law.json';d=json.loads(p.read_text());v=json.loads((BASE/'experiments/dityrosine-solvent-coupled-3d-20261031/viewer-data.json').read_text());signals=[];pairs=[];group=collections.defaultdict(dict);specmap={s['id']:s for s in v['specs']}
for c in v['cases']:
 for sig in c['signals']:
  r={'specid':c['specid'],'seed':c['seed'],'parent_z':c['parent_z'],'geometry':c['geometry'],'network_accepted':c['accepted'],'residual':c['residual'],'mean_force':c.get('mean_force'),'force_cv':c.get('force_cv'),**sig};signals.append(r)
  key=(c['specid'],c['seed'],c['parent_z'],sig['control'],sig['alpha'],sig['F50'])
  group[key][c['geometry']]=r
for key,g in group.items():
 if 'narrow' not in g or 'broad' not in g:continue
 a,b=g['broad'],g['narrow'];accepted=a['network_accepted'] and b['network_accepted'] and a['interpretation_valid'] and b['interpretation_valid'];r={'specid':key[0],'seed':key[1],'parent_z':key[2],'signal_control':key[3],'alpha':key[4],'F50':key[5],'common_accepted':accepted,**{k:specmap[key[0]].get(k) for k in ['phase','arm','source','environment','member','replica']}}
 for k in ['YAP_mean','mean_force','force_cv']:
  r['broad_'+k]=a[k];r['narrow_'+k]=b[k];r['broad_minus_narrow_'+k]=a[k]-b[k] if accepted and a[k] is not None and b[k] is not None else None
 pairs.append(r)
d['tables']=[t for t in d['tables'] if t['id'] not in ['conditional-signals','paired-geometry-contrasts']]
d['tables']+=[table('conditional-signals',signals,'Saved assumed YAP/gene response-law readouts; not biological measurements'),table('paired-geometry-contrasts',pairs,'Broad−narrow contrasts on common accepted same-seed cases only')];d['provenanceNote']='Recovered local verified scientific viewer export and exact saved CSVs; reportURL is the public campaign record. Public raw-file URL has not been asserted.';p.write_text(json.dumps(d,separators=(',',':')))
# Suggest exact intuitive selections instead of arbitrary first-column defaults.
defs={
 'reference-1dzi':('reference-contacts','collagen_auth_residue','distance_angstrom','collagen_chain','Reference atom-contact distances alongside actual fixed PDB geometry'),
 'carbonyl-scenarios':('timecourses','time_days','fraction','state','Filter tissue,pool,scenario first; terminalquantiles table is separately assumed-input uncertainty, not a time-dependent fan'),
 'coupled-3d-law':('paired-geometry-contrasts','narrow_YAP_mean','broad_YAP_mean','arm','Filter parent_z,alpha,F50,signal_control; common_accepted=true only; comparecoupled/diagonal specs and retain individualseedpoints'),
 'wet-transfer-gates':('derivative-curves','step','error','direction','Use actual derivative-tablecolumns when known; retain units across different generalizedcoordinate directions'),
 'mace-fragments':('cross-model-summary','k_rel_MACE-OFF','k_rel_MACE-MP','chemistry','Parity for relativecurvature disagreement; actual molecule snapshots are independentstartingfragments'),
 'snt-ligand-ensemble':('replicas','epsilon','reach_mean_A','variant','Filter formalcharge; replica means are dots, sampleSD separate; nevermix frameSD withbetweenreplicaSD'),
 'hydroxylation-prestress':('prestress-networks','prestress_contraction','mean_probe_stiffness','topology','Filterseed/bendingcoefficient; molecular ringpuckering occupiesaseparatepanel withoutMD→networkcalibration'),
 'four-bead-calibration':('distribution-histograms','bin_low','density','population','Filtercondition,heldout_replica,coordinate; compare actualtrain/heldout/CGcounts onsharedbinning'),
 'comparative-evidence-design':('observed-mammals','historical_max_lifespan_years','pentosidine_quadratic_coefficient','cohort','Speciespriorities andL9design require categoricalmatrix/table, notfictitious3Dphysicaldata'),
 'short-crosslink-md':('short-md-replicas','replica','free_tail_CA_marker_mean_A','model','SeparateGLU andDITYcontext; withinrunSD notindependent uncertainty'),
 'decorin-collagen-gag':('component-separation','pair','initial_min_distance_nm','pair','Compare reported heavyatomgaps; fixedpreparedgeometry clarifiesunboundcomponentseparation'),
 'hne-candidate-precision':('matched-precision-diagnostic','runtime','absolute_energy_error_kJmol','state','Matchedversion mixed/double numericalcomparison; currentfreshsampling shown separately'),
 'martini-pulling-virial':('force-and-pressure-diagnostic','metric','value','unit','Do notpooldifferentunits ononeaxis; selectedmetriccards clarifyforce vsvirial/ensemble gate'),
 'cross-scale-provenance':('model-boundaries','campaign','geometry','limit','Evidence/provenance matrix rather than numericplot'),
}
index=[]
for p in D.glob('*.json'):
 d=json.loads(p.read_text());id=d['id']
 if id in defs:
  t,x,y,color,note=defs[id];tab=next(t0 for t0 in d['tables'] if t0['id']==t)
  # Prefer exact named saved columns; special derivative dataset fields may vary.
  if id=='wet-transfer-gates':
   cols=tab['columns'];x=next((k for k in cols if 'step' in k),cols[0]);y=next((k for k in cols if 'error' in k),cols[-1]);color=next((k for k in cols if 'direction' in k),cols[0])
  d['defaultView']={'tableId':t,'x':x,'y':y,'color':color,'note':note};assert x in tab['columns'] and y in tab['columns'],(id,x,y,tab['columns'])
 d.setdefault('provenanceNote','Extracted from public PDB/workbook/archive or recovered user-owned scientific outputs. Source reportURLs identify context; exact local-source hashes are retained in the extraction manifests. No unpublished credential or execution log is included.')
 p.write_text(json.dumps(d,separators=(',',':'),allow_nan=False));index.append({'id':id,'file':str(p),'title':d['title'],'postIds':d['postIds'],'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'tables':[{k:t[k] for k in ['id','title','columns']}|{'rows':len(t['rows'])} for t in d.get('tables',[])],'geometry':list(d.get('geometry',{})),'molecules':len(d.get('molecules',[])),'defaultView':d.get('defaultView')})
(R/'inventory.json').write_text(json.dumps(index,indent=2));print('Ready',len(index),'datasets',sum(x['bytes'] for x in index),'bytes; coupledpairedrows',len(pairs))
