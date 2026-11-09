"""Apply only complete Argon JSON files and exact single-match patches, without executing drafts."""
from pathlib import Path
import json,sys,shutil
ROOT=Path(__file__).resolve().parent
dest=ROOT/'candidate'
if not dest.exists():shutil.copytree(ROOT/'snapshot',dest)
name=sys.argv[1]
t=(ROOT/(name+'.md')).read_text().strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
d=json.loads(t)
for item in d.get('files',[]):
    rel=Path(item['path']);assert rel.parts[0]=='docs' and '..' not in rel.parts
    q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(item['content'])
for item in d.get('replacements',[]):
    rel=Path(item['path']);assert rel.parts[0]=='docs' and '..' not in rel.parts
    q=dest/rel;s=q.read_text();assert s.count(item['old'])==1,(str(rel),s.count(item['old']),item['old'][:100]);q.write_text(s.replace(item['old'],item['new']))
(ROOT/(name+'-applied.json')).write_text(json.dumps({'files':[x['path'] for x in d.get('files',[])],'patched':[x['path'] for x in d.get('replacements',[])],'checks':d.get('checks',[]),'limitations':d.get('limitations',[])},indent=2))
print('Applied complete draft:',name)
