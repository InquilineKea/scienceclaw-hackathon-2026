from pathlib import Path
import json,hashlib,ssl,urllib.request,concurrent.futures,datetime
R=Path(__file__).resolve().parent;commit='82f61b282180853357483cf81b938d756f63fe60';base='https://inquilinekea.github.io/scienceclaw-hackathon-2026/'
ctx=ssl.create_default_context(cafile='/opt/homebrew/etc/ca-certificates/cert.pem')
files=json.loads((R/'static-validation.json').read_text())['changed_files']
def check(rel):
 url=base+rel.removeprefix('docs/')+'?verify='+commit
 try:
  with urllib.request.urlopen(url,context=ctx,timeout=40) as h:b=h.read();status=h.status;ct=h.headers.get('Content-Type')
  a=(R/'candidate'/rel).read_bytes();return {'path':rel,'status':status,'content_type':ct,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'matches_candidate':b==a}
 except Exception as e:return {'path':rel,'error':str(e),'matches_candidate':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(check,files))
report={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':commit,'base':base,'all_match':all(x['matches_candidate'] for x in rows),'files':rows};(R/'public-file-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'all_match':report['all_match'],'files':len(rows),'failures':[x for x in rows if not x['matches_candidate']]}))
