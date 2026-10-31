"""Original stdlib-only result integrity check and bounded publication copier."""
from pathlib import Path
import hashlib,json,shutil,zipfile,sys
root=Path(__file__).resolve().parent
receipt=json.loads(Path(sys.argv[1]).read_text());archive=Path(sys.argv[2]);b=archive.read_bytes()
assert len(b)==receipt['archiveBytes'] and hashlib.sha256(b).hexdigest()==receipt['archiveSha256']
assert receipt['success'] and receipt['returncode']==0
out=root/'completed';out.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as z:
 for i in z.infolist():
  p=Path(i.filename);assert not p.is_absolute() and '..' not in p.parts
  assert i.file_size<512*1024**2
  target=out/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(i))
manifest=json.loads((out/'result/MANIFEST.json').read_text())
for name,v in manifest['files'].items():
 b=(out/'result'/name).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
for name,sha in receipt['sourceHashes'].items():assert hashlib.sha256((out/'source'/name).read_bytes()).hexdigest()==sha
shutil.copyfile(archive,root/'poro-results-v2.zip');(root/'RUN_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
for p in (out/'result').iterdir():
 if p.is_file() and p.name not in ['partial.json']:shutil.copyfile(p,root/'web'/p.name)
d={n:json.loads((out/'result'/f'{n}.json').read_text()) for n in ['animation','summary','validation']}
(root/'web/data.js').write_text('globalThis.PORO_DATA='+json.dumps(d,separators=(',',':'))+';\n')
print(json.dumps(d['validation'],indent=2))
