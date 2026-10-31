"""Original standard-library read-only verification of this task's public media."""
from pathlib import Path
import hashlib,json,urllib.parse,subprocess
manifest=json.loads(Path('publication/media.json').read_text())
out=Path('/private/tmp/fracture-atlas-media-check');out.mkdir(exist_ok=True)
records=[]
for key,m in manifest.items():
    url=m['source_url']
    assert urllib.parse.urlparse(url).hostname=='humanavianaisymbiosis.wordpress.com'
    filename=key+('.gif' if m['mime_type']=='image/gif' else '.png')
    destination=out/filename
    result=subprocess.run(['/usr/bin/curl','--fail','--silent','--show-error','--location','--max-time','45','--output',str(destination),'--write-out','%{http_code} %{content_type}',url],check=True,capture_output=True,text=True)
    payload=destination.read_bytes()
    code,content_type=result.stdout.split(' ',1)
    assert code=='200'
    records.append({'asset':key,'url':url,'status':int(code),'content_type':content_type,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
Path('publication/public-media-http.json').write_text(json.dumps(records,indent=2))
print(json.dumps([{'asset':r['asset'],'status':r['status'],'bytes':r['bytes']} for r in records]))
