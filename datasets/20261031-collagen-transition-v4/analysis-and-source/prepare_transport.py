"""Reproduce the v4 transport from frozen v2/v4 input directories (stdlib only).

This is packaging, not a generic simulation launcher. The remote input still
requires the exact preserved cloud_job_v2.py object at /output.
"""
from pathlib import Path
import ast,base64,gzip,json,hashlib,difflib,zipfile,io,argparse
ap=argparse.ArgumentParser();ap.add_argument('v2_directory');ap.add_argument('v4_directory');ap.add_argument('template');ap.add_argument('output_directory');args=ap.parse_args()
v2=Path(args.v2_directory);v4=Path(args.v4_directory);dest=Path(args.output_directory);dest.mkdir(parents=True,exist_ok=False)
old=(v2/'cloud_job_v2.py').read_bytes();new=(v4/'cloud_job_v4.py').read_bytes();a=(v2/'source.zip').read_bytes();b=(v4/'source.zip').read_bytes();za=zipfile.ZipFile(io.BytesIO(a));zb=zipfile.ZipFile(io.BytesIO(b));changes={}
for name in zb.namelist():
 x=za.read(name).decode();y=zb.read(name).decode();ops=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,x,y,autojunk=False).get_opcodes():
  if tag=='equal':ops.append([i,j])
  elif k!=l:ops.append(y[k:l])
 changes[name]=ops
payload={'files':changes,'template':Path(args.template).read_text(),'oldBootstrapSHA256':hashlib.sha256(old).hexdigest(),'newBootstrapSHA256':hashlib.sha256(new).hexdigest(),'newSourceSHA256':hashlib.sha256(b).hexdigest()}
packed=base64.b85encode(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),compresslevel=9,mtime=0)).decode()
code='''# Original transport; reconstructs checksum-pinned reviewed source from text deltas.
import ast,base64,gzip,json,hashlib,sys,os,zipfile,io
from pathlib import Path
PAYLOAD = '''+repr(packed)+'''
p=json.loads(gzip.decompress(base64.b85decode(PAYLOAD)))
old=Path('/output/cloud_job_v2.py').read_bytes()
assert hashlib.sha256(old).hexdigest()==p['oldBootstrapSHA256']
values={}
for node in ast.parse(old).body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['SOURCE_B64','WHEELS']:
  values[node.targets[0].id]=ast.literal_eval(node.value)
za=zipfile.ZipFile(io.BytesIO(base64.b64decode(values['SOURCE_B64'])))
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,ops in p['files'].items():
  x=za.read(name).decode();y=''.join(x[o[0]:o[1]] if isinstance(o,list) else o for o in ops)
  info=zipfile.ZipInfo(name,date_time=(2026,10,31,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,y.encode())
b=buf.getvalue()
assert hashlib.sha256(b).hexdigest()==p['newSourceSHA256']
code=p['template'].replace("'SOURCE_ARCHIVE_BASE64'",repr(base64.b64encode(b).decode())).replace("'SOURCE_ARCHIVE_SHA256'",repr(p['newSourceSHA256'])).replace('[] # PINNED_WHEELS',repr(values['WHEELS'])).replace("'JOB_REVISION'",repr('v4'))
assert hashlib.sha256(code.encode()).hexdigest()==p['newBootstrapSHA256']
out=Path('/tmp/cloud_job_v4.py')
with out.open('x') as f:f.write(code)
print('TRANSPORT reconstructed exact reviewed input '+p['newBootstrapSHA256'],flush=True)
os.execv(sys.executable,[sys.executable,'-I',str(out)])
'''
ast.parse(code)
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,ops in changes.items():
  x=za.read(name).decode();y=''.join(x[o[0]:o[1]] if isinstance(o,list) else o for o in ops)
  assert y.encode()==zb.read(name)
  info=zipfile.ZipInfo(name,date_time=(2026,10,31,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,y.encode())
assert buf.getvalue()==b
out=dest/'transport_v4c.py'
with out.open('x') as f:f.write(code)
r={'input':str(out),'bytes':len(code.encode()),'inputSHA256':hashlib.sha256(code.encode()).hexdigest(),'reconstructedBootstrapSHA256':payload['newBootstrapSHA256'],'sourceZipSHA256':payload['newSourceSHA256'],'dependencyObject':'cloud_job_v2.py','dependencySHA256':payload['oldBootstrapSHA256'],'encoding':'base85/gzip text deltas plus reproducible ZIP; both reconstructed hashes checked before execution','localDataOnlyReconstruction':'byte-identical canonical source ZIP'}
(dest/'TRANSPORT_TEXTDELTA_MANIFEST.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
