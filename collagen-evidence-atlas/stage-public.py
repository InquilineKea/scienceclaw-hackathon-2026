"""Original explicit allowlisted publication staging; no network, deletion or code execution."""
from pathlib import Path
import shutil,json,hashlib
P=Path(__file__).parent;D=Path('/private/tmp/scienceclaw-final-media-publication/collagen-evidence-atlas');D.mkdir(exist_ok=False)
names=['README.md','SECURITY.md','REVIEW-RESOLUTION.md','DATA-PROVENANCE.json','DATA-VALIDATION.json','BROWSER-VERIFICATION.json','prepare-data.mjs','validate-data.py','stage-public.py']
names+=['web/'+n for n in ['index.html','style.css','app.js','render.js','data.json','METHODS.md']]
names+=['argon/'+n for n in ['BRIEF.md','worker.py','design.json','design-receipt.json','REVIEW-PACKET.md','review.json','review-receipt.json','USAGE-SUMMARY.json']]
rows=[]
for n in names:
 s=P/n;t=D/n;assert s.is_file() and not s.is_symlink();t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,t);a=hashlib.sha256(s.read_bytes()).hexdigest();assert hashlib.sha256(t.read_bytes()).hexdigest()==a;rows.append({'file':n,'bytes':s.stat().st_size,'sha256':a})
(D/'SOURCE-MANIFEST.json').write_text(json.dumps({'scope':'Original visualization source, derived public data, final non-thought Argon design/review and usage/provenance. No credentials, hidden thinking, raw images, cloud-account metadata, dependencies or binaries.','files':rows},indent=2));print('Staged',len(rows),'files',sum(r['bytes'] for r in rows))
