from pathlib import Path
import json,ssl,urllib.request,hashlib,concurrent.futures
R=Path(__file__).resolve().parent;D=R/'sources';D.mkdir(exist_ok=True)
items=[('1DZI.pdb','https://files.rcsb.org/download/1DZI.pdb'),('1K6F.pdb','https://files.rcsb.org/download/1K6F.pdb'),('comparative_collagen_mechanics_public_data.xlsx','https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/comparative_collagen_mechanics_public_data.xlsx'),('viscoelastic_public_summary_tables.xlsx','https://humanavianaisymbiosis.wordpress.com/wp-content/uploads/2026/10/viscoelastic_public_summary_tables.xlsx')]
ctx=ssl.create_default_context(cafile='/opt/homebrew/etc/ca-certificates/cert.pem')
def get(it):
 name,url=it
 with urllib.request.urlopen(url,context=ctx,timeout=45) as h:b=h.read(30000001)
 assert len(b)<=30000000
 (D/name).write_bytes(b);return {'name':name,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(get,items))
(R/'download-manifest.json').write_text(json.dumps(rows,indent=2));print(rows)
