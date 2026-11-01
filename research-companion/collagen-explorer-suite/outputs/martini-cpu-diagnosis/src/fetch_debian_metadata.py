from pathlib import Path
import urllib.request,ssl,lzma,hashlib,json
root=Path('outputs/martini-cpu-diagnosis/runtime-review');root.mkdir(exist_ok=True);ctx=ssl.create_default_context(cafile='/opt/homebrew/etc/ca-certificates/cert.pem');base='https://deb.debian.org/debian/'
for name,url in [('Packages.xz',base+'dists/bookworm/main/binary-arm64/Packages.xz'),('InRelease',base+'dists/bookworm/InRelease')]:
 p=root/name
 if not p.exists():
  with urllib.request.urlopen(url,context=ctx,timeout=60) as r:p.write_bytes(r.read())
index=lzma.decompress((root/'Packages.xz').read_bytes()).decode();packages={}
for para in index.split('\n\n'):
 rows={};key=None
 for l in para.splitlines():
  if l.startswith(' '):continue
  if ': ' in l:key,val=l.split(': ',1);rows[key]=val
 if rows.get('Package') in ['gromacs','libgromacs7','gromacs-data','libfftw3-single3','libfftw3-double3','libmuparser2v5','libgomp1']:packages[rows['Package']]=rows
assert len(packages)==7
(root/'selected-packages.json').write_text(json.dumps(packages,indent=2)+'\n');print(json.dumps({k:{f:v.get(f) for f in ['Version','Filename','Size','Depends','SHA256']} for k,v in packages.items()},indent=2))
