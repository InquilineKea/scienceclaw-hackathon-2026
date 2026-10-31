"""Original bounded Pages assembly from completed scientific outputs; no network."""
from pathlib import Path
import json,hashlib,zipfile,shutil
P=Path(__file__).parent;R=Path('/private/tmp/scienceclaw-final-media-publication');D=R/'collagen-nonlinear-heldout';W=D/'web';W.mkdir(exist_ok=True)
commit=json.loads((P/'SCIENCE-COMMIT.json').read_text())['sha'];url=f'https://github.com/InquilineKea/scienceclaw-hackathon-2026/tree/{commit}/collagen-nonlinear-heldout'
names=['index.html','page.js','results.json','fields.json','numerical-controls.json','comparison.svg','selection.svg','comparison.jpg','selection.jpg','nonlinear-prediction-3d.gif','REPORT.md']
for n in names:shutil.copyfile(P/n,W/n)
s=(W/'index.html').read_text().replace('id="source" href="https://github.com/InquilineKea/scienceclaw-hackathon-2026"',f'id="source" href="{url}"');(W/'index.html').write_text(s)
z=W/'nonlinear-3d-results.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as a:
 for f in sorted(D.rglob('*')):
  if f.is_file() and f!=z:a.write(f,'nonlinear-3d/'+str(f.relative_to(D)))
route=R/'docs/nonlinear-3d';route.mkdir(exist_ok=True)
for f in W.iterdir():shutil.copyfile(f,route/f.name)
records={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in W.iterdir()}
meta=R/'docs/DEPLOYMENT.json';d=json.loads(meta.read_text());d['nonlinear_3d']={'scope':'Adaptively reused measured-boundary-conditioned 3D continuum surrogate comparison, fixed masks and honest numerical gates; no measured fiber graph or chemical aging validation.','scientific_commit':commit,'files':records};meta.write_text(json.dumps(d,indent=2)+'\n')
readme=R/'README.md';s=readme.read_text();s+='\n\n## Nonlinear buckling and sliding prediction test\n\n[Open the nonlinear 3D comparison](https://inquilinekea.github.io/scienceclaw-hackathon-2026/nonlinear-3d/) for the twelve-arm selection, harmonic baseline, guarded displacement/local-strain scores, numerical qualification and interactive final-field comparison. [Report](collagen-nonlinear-heldout/REPORT.md). This is an adaptively reused conditional benchmark, not a fresh biological validation.\n';readme.write_text(s)
(P/'PUBLIC-WEB-RECORD.json').write_text(json.dumps({'scientific_commit':commit,'source_url':url,'route':'https://inquilinekea.github.io/scienceclaw-hackathon-2026/nonlinear-3d/','files':records},indent=2))
print('Assembled route and bounded archive',z.stat().st_size)
