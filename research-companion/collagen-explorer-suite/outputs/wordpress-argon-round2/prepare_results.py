from pathlib import Path
import json,csv,zipfile,xml.etree.ElementTree as E,hashlib
R=Path(__file__).resolve().parent;p=R/'extra-source';d=R/'candidate/docs/results-lab';d.mkdir(exist_ok=True)
def rows(name):return list(csv.DictReader((p/name).open()))
def convert(r):
 out={}
 for k,v in r.items():
  try:out[k]=float(v)
  except (ValueError,TypeError):out[k]=v
 return out
org={'provenance':json.loads((p/'manifest.json').read_text()),'limitations':['Synthetic network/organoid model outputs; gene values are assumed dimensionless model readouts, not measured expression.','One saved trajectory per gel; variation across gels is not replicate uncertainty.','Archived 389-pair aggregate is included separately; pair identities and exact selection definition are not available here. No pairwise matching is reconstructed.'],'gels':[convert(x) for x in rows('gels.csv')],'trajectories':[convert(x) for x in rows('organoid.csv')],'matched_day7_aggregate':[convert(x) for x in rows('analysis_day7_matched.csv')]}
(d/'organoid.json').write_text(json.dumps(org,allow_nan=False,separators=(',',':')))
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(p/'collagen-calibration-results.xlsx') as z:
 assert sum(x.file_size for x in z.infolist())<20000000
 assert not any('vba' in x.filename.lower() or 'externallinks' in x.filename.lower() for x in z.infolist())
 def sheet(i):
  a=[]
  for row in E.fromstring(z.read(f'xl/worksheets/sheet{i}.xml')).findall('.//m:sheetData/m:row',ns):
   cells={}
   for c in row:
    col=''.join(t for t in c.get('r','') if t.isalpha());idx=0
    for t in col:idx=idx*26+ord(t)-64
    assert c.find('m:f',ns) is None,'formula found'
    cells[idx-1]=''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext('m:v',default='',namespaces=ns)
   a.append(cells)
  return [convert({a[0][k]:v for k,v in row.items() if k in a[0] and not a[0][k].startswith('Source:')}) for row in a[1:]]
 rheo={'source_url':'https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/collagen-calibration-results.xlsx','workbook_sha256':hashlib.sha256((p/'collagen-calibration-results.xlsx').read_bytes()).hexdigest(),'data_source':'Ruiz-Mateos Brea et al., CC BY 4.0, https://doi.org/10.5281/zenodo.17413651','limitations':['Measured small-strain bovine hydrogel rheology with saved model fits and held-out predictions; not molecular or cell-force calibration.','Observed standard deviation is between saved replicates, not a predictive confidence interval.','Bootstrap parameter intervals do not supply pointwise predictive intervals.','Use leave_file and leave_concentration separately; extrapolation can be unstable. No models are refit by this viewer.'],'predictions':sheet(3),'scores':sheet(2),'measurements':sheet(8),'frequency_curves':sheet(7),'bootstrap_parameters':sheet(5)}
(d/'rheology.json').write_text(json.dumps(rheo,allow_nan=False,separators=(',',':')))
print({k:{x:len(v) for x,v in val.items() if isinstance(v,list)} for k,val in [('organoid',org),('rheology',rheo)]})
