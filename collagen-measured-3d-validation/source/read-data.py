"""Original standard-library inert readers; never import Saenopy or unpickle arrays."""
from pathlib import Path
import zipfile,io,struct,ast,json,hashlib,math
P=Path(__file__).parent

def npy(b):
 assert b[:6]==b'\x93NUMPY';v=b[6];assert v in (1,2);start=10 if v==1 else 12;n=struct.unpack('<H' if v==1 else '<I',b[8:start])[0];assert n<65536
 h=ast.literal_eval(b[start:start+n].decode('latin1'));dtype=h['descr'];shape=h['shape'];assert len(shape)<=2 and isinstance(h['fortran_order'],bool);assert dtype in ['<f8','<f4','<i8','<i4','|b1','|u1','<u4','<u2'];fmt={'<f8':'d','<f4':'f','<i8':'q','<i4':'i','|b1':'?','|u1':'B','<u4':'I','<u2':'H'}[dtype];a=[x[0] for x in struct.iter_unpack('<'+fmt,b[start+n:])];count=math.prod(shape);assert count==len(a)
 if len(shape)==2:
  N,M=shape;a=[[a[i+j*N] if h['fortran_order'] else a[i*M+j] for j in range(M)] for i in range(N)]
 return a,h

def main():
 file=P/'data/4_OrganoidTFM_evaluated.zip'
 with zipfile.ZipFile(file) as outer:
  names=outer.namelist();assert len(names)==1;payload=outer.read(names[0])
 with zipfile.ZipFile(io.BytesIO(payload)) as z:
  names=z.namelist();print('PIV members',[n for n in names if n.startswith('mesh_piv')]);arrays={}
  for key in ['nodes','tetrahedra','displacements_measured']:
   name='mesh_piv/0/'+key+'.npy';a,h=npy(z.read(name));assert len(h['shape'])==2 and h['shape'][1]==(4 if key=='tetrahedra' else 3);arrays[key]=a
   print(key,h)
  nodes=arrays['nodes'];assert all(math.isfinite(v) for n in nodes for v in n);assert all(isinstance(v,int) and 0<=v<len(nodes) for t in arrays['tetrahedra'] for v in t);bounds=[[min(n[d] for n in nodes),max(n[d] for n in nodes)] for d in range(3)];unique=[len(set(n[d] for n in nodes)) for d in range(3)]
  (P/'geometry.json').write_text(json.dumps({'nodes':nodes,'tetrahedra':arrays['tetrahedra'],'units':'m','source':'Published Saenopy example PIV sampling mesh, not measured collagen fiber connectivity'},separators=(',',':')))
  (P/'data/measured-displacements.json').write_text(json.dumps({'u':[[v if math.isfinite(v) else None for v in row] for row in arrays['displacements_measured']],'valid':[all(math.isfinite(v) for v in row) for row in arrays['displacements_measured']],'units':'m','source':'mesh_piv/0/displacements_measured.npy; image-derived PIV, not inverse-force reconstructed displacements'},separators=(',',':'),allow_nan=False))
  metadata={'source_zip_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'source_inner_sha256':hashlib.sha256(payload).hexdigest(),'bounds_m':bounds,'unique_coordinate_counts':unique,'nodes':len(nodes),'tetrahedra':len(arrays['tetrahedra']),'outcome_values_not_summarized':True};(P/'evidence/PIV-GEOMETRY-INVENTORY.json').write_text(json.dumps(metadata,indent=2));print(metadata)
if __name__=='__main__':main()
