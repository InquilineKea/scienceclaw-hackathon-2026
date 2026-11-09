from pathlib import Path
import json,hashlib,urllib.request,ssl,tarfile,io,struct,concurrent.futures
root=Path('outputs/martini-cpu-diagnosis/runtime-review');meta=json.loads((root/'selected-packages.json').read_text());ctx=ssl.create_default_context(cafile='/opt/homebrew/etc/ca-certificates/cert.pem')
def ar(b):
 assert b[:8]==b'!<arch>\n';i=8;out={}
 while i<len(b):
  head=b[i:i+60];assert head[58:60]==b'`\n';name=head[:16].decode().strip().rstrip('/');n=int(head[48:58]);i+=60;out[name]=b[i:i+n];i+=n+(n%2)
 return out
def elf_needed(b):
 if b[:4]!=b'\x7fELF':return []
 assert b[4]==2 and b[5]==1
 phoff=struct.unpack_from('<Q',b,32)[0];entsize,num=struct.unpack_from('<HH',b,54);loads=[];dynamic=None
 for i in range(num):
  typ,flags,off,va,pa,sz,mem,align=struct.unpack_from('<IIQQQQQQ',b,phoff+i*entsize)
  if typ==1:loads.append((va,off,sz))
  if typ==2:dynamic=(off,sz)
 if dynamic is None:return []
 tags=[]
 for j in range(dynamic[0],sum(dynamic),16):
  tag,val=struct.unpack_from('<qQ',b,j)
  if tag==0:break
  tags.append((tag,val))
 strings=next((v for t,v in tags if t==5),None)
 if strings is None:return []
 so=next(off+strings-va for va,off,sz in loads if va<=strings<va+sz);names=[]
 for t,v in tags:
  if t==1:names.append(b[so+v:b.index(b'\0',so+v)].decode())
 return names
def review(item):
 name,m=item;p=root/(Path(m['Filename']).name)
 if not p.exists():
  with urllib.request.urlopen('https://deb.debian.org/debian/'+m['Filename'],context=ctx,timeout=90) as r:p.write_bytes(r.read())
 b=p.read_bytes();assert len(b)==int(m['Size']) and hashlib.sha256(b).hexdigest()==m['SHA256'];members=ar(b);controls={};needed={};count=0
 for fn,payload in members.items():
  if fn.startswith('control.tar'):
   with tarfile.open(fileobj=io.BytesIO(payload)) as t:
    for x in t.getmembers():
     if x.isfile():controls[x.name]=t.extractfile(x).read().decode(errors='replace')
  if fn.startswith('data.tar'):
   with tarfile.open(fileobj=io.BytesIO(payload)) as t:
    for x in t.getmembers():
     count+=1;assert not x.name.startswith('/') and '..' not in Path(x.name).parts
     if x.isfile() and ('/bin/' in x.name or '.so' in x.name):
      blob=t.extractfile(x).read();deps=elf_needed(blob)
      if deps:needed[x.name]=deps
 return name,{'sha256_verified':True,'files':count,'controls':controls,'ELF_dependencies':needed}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:report=dict(ex.map(review,meta.items()))
(root/'deb-static-review.json').write_text(json.dumps(report,indent=2)+'\n')
for n,d in report.items():
 print(n,'CONTROL SCRIPTS',{k:v for k,v in d['controls'].items() if k.rsplit('/',1)[-1] in ['preinst','postinst','prerm','postrm','triggers']});print('ELF',d['ELF_dependencies'])
