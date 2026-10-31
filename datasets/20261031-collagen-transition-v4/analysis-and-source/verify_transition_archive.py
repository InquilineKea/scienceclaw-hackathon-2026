from pathlib import Path
import sys,zipfile,json,hashlib,shutil,stat
src=Path(sys.argv[1]);base=Path(sys.argv[2]);expected=sys.argv[3]
b=src.read_bytes();sha=hashlib.sha256(b).hexdigest()
if sha!=expected:raise ValueError('Archive checksum mismatch')
base.mkdir(parents=True,exist_ok=False)
with (base/src.name).open('xb') as f:f.write(b)
with zipfile.ZipFile(src) as z:
 if z.testzip() is not None:raise ValueError('CRC failure')
 names=z.namelist()
 if len(names)!=len(set(names)):raise ValueError('Duplicate archive paths')
 manifest=json.loads(z.read('OUTPUT_MANIFEST.json'))
 if set(names)!=set(manifest)|{'OUTPUT_MANIFEST.json'}:raise ValueError('Coverage differs')
 for name,m in manifest.items():
  if name.startswith('/') or '..' in Path(name).parts:raise ValueError('Unsafe archive member')
  mode=z.getinfo(name).external_attr>>16
  if stat.S_ISLNK(mode):raise ValueError('Symbolic link rejected')
  data=z.read(name)
  if len(data)!=m['bytes'] or hashlib.sha256(data).hexdigest()!=m['sha256']:raise ValueError('Member mismatch '+name)
  out=base/'extracted'/name;out.parent.mkdir(parents=True,exist_ok=True)
  with out.open('xb') as f:f.write(data)
 (base/'extracted/OUTPUT_MANIFEST.json').write_bytes(z.read('OUTPUT_MANIFEST.json'))
receipt={'archive':src.name,'bytes':len(b),'sha256':sha,'verifiedMembers':len(manifest),'status':'passed'}
(base/'VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
