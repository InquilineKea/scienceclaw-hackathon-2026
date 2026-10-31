"""Create bounded public archives; deterministic ZIP timestamps, no external code."""
from pathlib import Path
import hashlib,json,zipfile,base64
root=Path('.')
allowed_publication={'media.json','public-media-http.json','public-media-frames.json'}
excluded={'MANIFEST.json','TEXT-MANIFEST.json','media-input.json','preview.jpg'}
files=sorted(p for p in root.rglob('*') if p.is_file() and p.suffix not in ('.zip',) and p.name not in excluded and (p.parts[0]!='publication' or p.name in allowed_publication))
def bundle(name,members,manifest_name):
    manifest={str(p):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in members}
    manifest_text=json.dumps(manifest,indent=2)+'\n'
    Path(manifest_name).write_text(manifest_text)
    def write(z,name,data):
        info=zipfile.ZipInfo('fracture-atlas/'+name,(2026,10,31,12,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,data,compresslevel=9)
    with zipfile.ZipFile(name,'w') as z:
        for p in members:write(z,str(p),p.read_bytes())
        write(z,manifest_name,manifest_text)
    with zipfile.ZipFile(name) as z:assert z.testzip() is None
    payload=Path(name).read_bytes();return {'filename':name,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'members':len(members)+1}
full=bundle('fracture-atlas-complete.zip',files,'MANIFEST.json')
text=bundle('fracture-atlas-data-source.zip',[p for p in files if p.suffix not in ('.png','.gif')],'TEXT-MANIFEST.json')
Path('publication/archive-metadata.json').write_text(json.dumps({'complete':full,'data_source':text},indent=2))
print(json.dumps({'complete':full,'data_source':text},indent=2))
