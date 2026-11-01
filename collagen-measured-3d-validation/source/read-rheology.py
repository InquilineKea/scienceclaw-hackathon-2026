"""Original stdlib cached XLSX cell reader; no spreadsheet formulas executed."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,posixpath
P=Path(__file__).parent;NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def read(file):
 with zipfile.ZipFile(file) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():ss=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml'))]
  relationships={r.attrib['Id']:posixpath.normpath('xl/'+r.attrib['Target']) if not r.attrib['Target'].startswith('/') else r.attrib['Target'][1:] for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))};out=[]
  for sh in E.fromstring(z.read('xl/workbook.xml')).find('m:sheets',NS):
   key=sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'];path=relationships[key];cells={}
   for c in E.fromstring(z.read(path)).iter('{'+NS['m']+'}c'):
    v=c.find('m:v',NS);t=c.attrib.get('t');val=v.text if v is not None else None
    if t=='s' and val is not None:val=ss[int(val)]
    elif t=='inlineStr':val=''.join(c.find('m:is',NS).itertext())
    elif val is not None:
     try:val=float(val)
     except ValueError:pass
    if val is not None:cells[c.attrib['r']]=val
   out.append({'sheet':sh.attrib['name'],'cells':cells})
 return out
if __name__=='__main__':
 out=read(P/'data/41567_2024_2632_MOESM21_ESM.xlsx');(P/'data/rheology-cached-cells.json').write_text(json.dumps(out));
 for s in out:print(s['sheet'],len(s['cells']),[(k,v) for k,v in s['cells'].items() if isinstance(v,str)][:35])
