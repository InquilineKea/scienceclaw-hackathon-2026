"""Original stdlib extraction of public image-derived PIV fields, no inverse forces."""
from pathlib import Path
import zipfile,io,json,math,hashlib
from importlib.machinery import SourceFileLoader
P=Path(__file__).parent;R=SourceFileLoader('original_readers',str(P/'read-data.py')).load_module()
records=[]
with zipfile.ZipFile(P/'data/1_ClassicSingleCellTFM_evaluated.zip') as outer:
 for item in outer.infolist():
  specimen=item.filename.split('_')[0];raw=outer.read(item);arrays={}
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   for key in ['nodes','tetrahedra','displacements_measured']:
    arrays[key],h=R.npy(z.read('mesh_piv/0/'+key+'.npy'));assert len(h['shape'])==2 and h['shape'][1]==(4 if key=='tetrahedra' else 3)
  nodes=arrays['nodes'];tets=arrays['tetrahedra'];assert all(math.isfinite(v) for n in nodes for v in n);assert all(isinstance(v,int) and 0<=v<len(nodes) for t in tets for v in t)
  (P/'data'/specimen).mkdir(exist_ok=True)
  (P/'data'/specimen/'geometry.json').write_text(json.dumps({'nodes':nodes,'tetrahedra':tets,'units':'m','kind':'PIV sampling FE mesh, not collagen fiber connectivity'},separators=(',',':')))
  u=arrays['displacements_measured'];(P/'data'/specimen/'measured.json').write_text(json.dumps({'u':[[v if math.isfinite(v) else None for v in row] for row in u],'valid':[all(math.isfinite(v) for v in row) for row in u],'units':'m','source':'image-derived mesh_piv field, never inverse model output'},separators=(',',':'),allow_nan=False))
  records.append({'specimen':specimen,'nodes':len(nodes),'tetrahedra':len(tets),'bounds_m':[[min(n[d] for n in nodes),max(n[d] for n in nodes)] for d in range(3)],'unique_coordinates':[len(set(n[d] for n in nodes)) for d in range(3)],'source_sha256':hashlib.sha256(raw).hexdigest(),'outcomes_not_summarized':True})
(P/'evidence/CLASSIC-GEOMETRY-INVENTORY.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
with zipfile.ZipFile(P/'data/1_ClassicSingleCellTFM.zip') as z:
 infos=z.infolist();(P/'evidence/CLASSIC-IMAGE-INVENTORY.json').write_text(json.dumps([{'name':i.filename,'bytes':i.file_size} for i in infos],indent=2));print('Images',len(infos));print([i.filename for i in infos[:8]])
