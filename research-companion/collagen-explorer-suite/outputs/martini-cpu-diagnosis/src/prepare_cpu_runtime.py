"""Static staging only: copy reviewed package bytes; never execute a package or hook."""
from pathlib import Path
import ast,json,tarfile,io,hashlib,os
r=Path('outputs/martini-cpu-diagnosis/runtime-review');meta=json.loads((r/'selected-packages.json').read_text());ns={'struct':__import__('struct')};tree=ast.parse(Path('outputs/martini-cpu-diagnosis/src/review_debs.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['ar','elf_needed']],type_ignores=[]),'original_static_parsers','exec'),ns)
context=Path('outputs/martini-cpu-diagnosis/cpu-image');context.mkdir(exist_ok=False);root=context/'rootfs';root.mkdir();symlinks=[];manifest={};deps={}
for name,m in meta.items():
 p=r/Path(m['Filename']).name;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==m['SHA256']
 for filename,payload in ns['ar'](b).items():
  if not filename.startswith('data.tar'):continue
  with tarfile.open(fileobj=io.BytesIO(payload)) as t:
   for x in t.getmembers():
    rel=Path(x.name);parts=rel.parts
    if '..' in parts or rel.is_absolute():raise ValueError(x.name)
    path=rel.as_posix().lstrip('./');want=path in ['usr/bin/gmx','usr/bin/gmx_d'] or (path.startswith('usr/lib/aarch64-linux-gnu/') and '.so' in path and '_mpi' not in path) or (path.startswith('usr/share/gromacs/top/') and path.count('/')==4 and path.endswith('.dat'))
    if not want:continue
    dest=root/path
    if x.isfile():
     dest.parent.mkdir(parents=True,exist_ok=True);blob=t.extractfile(x).read();dest.write_bytes(blob);dest.chmod(0o755 if '/bin/' in path else 0o644);manifest[path]={'package':name,'sha256':hashlib.sha256(blob).hexdigest()};needed=ns['elf_needed'](blob)
     if needed:deps[path]=needed
    elif x.issym():symlinks.append((path,x.linkname))
for path,target in symlinks:
 dest=root/path;assert not dest.exists() and not dest.is_symlink()
 # Package library symlinks must stay within the staged runtime.
 assert not target.startswith('/') and '..' not in Path(target).parts,(path,target)
 dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(target);manifest[path]={'symlink':target}
base_names=set()
with tarfile.open(r/'debian12-image.tar') as t:
 m=json.load(t.extractfile('manifest.json'))
 for layer in m[0]['Layers']:
  with tarfile.open(fileobj=t.extractfile(layer)) as a:
   base_names|={Path(x.name).name for x in a.getmembers()}
available={Path(p).name for p in manifest}|base_names;missing={n for names in deps.values() for n in names if n not in available};assert not missing,missing
(context/'STAGED-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');(context/'ELF-DEPENDENCIES.json').write_text(json.dumps(deps,indent=2)+'\n')
(context/'Dockerfile').write_text('''FROM debian@sha256:321341744acb788e251ebd374aecc1a42d60ce65da7bd4ee9207ff6be6686a62
COPY rootfs/ /opt/cpu-runtime/
ENV LD_LIBRARY_PATH=/opt/cpu-runtime/usr/lib/aarch64-linux-gnu:/opt/cpu-runtime/usr/lib/aarch64-linux-gnu/blas:/opt/cpu-runtime/usr/lib/aarch64-linux-gnu/lapack
ENV GMXLIB=/opt/cpu-runtime/usr/share/gromacs/top
ENV OMP_NUM_THREADS=4
USER 1000:1000
WORKDIR /output
ENTRYPOINT ["/opt/cpu-runtime/usr/bin/gmx"]
''');print('Statically staged',len(manifest),'files/links; all ELF dependency names resolve; no package installer/build/runtime executed.')
