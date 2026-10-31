"""Seal a complete archival collection, preserving successful and failed attempts."""
from pathlib import Path
import json,hashlib,shutil,re,datetime,zipfile,ast
ROOT=Path(__file__).resolve().parent.parent
base=ROOT/'outputs/collagen-transition-h100'
dest=ROOT/'outputs/large-data-archives/runs/20261031-collagen-transition-v4'
final=base/'attempts/aijob-e00dv1sg6b68gbz2hp/final/extracted/runs/commission'
assert (final/'FINISHED.json').exists(), 'Only seal after complete collection and scientific audit'
assert (base/'REPORT.md').exists()
for d in (base/'attempts').iterdir():assert (d/'OUTCOME.json').exists(), 'All submitted jobs need an outcome'
dest.mkdir(parents=True,exist_ok=False)
redactions=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def copy(src,relative):
 t=dest/relative;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,t)
# Entire downloaded job output and source archives remain byte-for-byte intact.
for d in sorted((base/'attempts').iterdir()):
 for p in sorted(d.rglob('*')):
  if not p.is_file():continue
  rel=Path('attempts')/p.relative_to(base/'attempts')
  if p.suffix.lower() in ['.jpg','.jpeg']:
   redactions.append({'file':str(rel),'originalSHA256':sha(p.read_bytes()),'publication':'Private provider UI screenshot retained locally; may contain unrelated account navigation. All scientific output preserved separately.'});continue
  if p.name=='console-log.txt':
   s=p.read_text();old=s
   # Provider UI navigation is not a scientific log. Preserve all workload messages.
   marker=s.find('- generic: Time')
   if marker>=0:s=s[marker:]
   else:
    lines=s.splitlines();start=next((i for i,l in enumerate(lines) if re.search(r'\btext Time\b',l)),0);s='\n'.join(lines[start:])+'\n'
   s=re.sub(r'(?:project|tenant|vpcsubnet|storagebucket)-[A-Za-z0-9]+','[private-resource-id]',s)
   s=re.sub(r'/Users/[^/\s]+','/Users/[local-user]',s)
   t=dest/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(s)
   redactions.append({'file':str(rel),'originalSHA256':sha(old.encode()),'publishedSHA256':sha(s.encode()),'publication':'Provider UI navigation removed; private resource IDs redacted. Workload stdout/stderr in recovered archives is unchanged.'});continue
  if p.name=='NEBIUS_RUN_RECEIPT.json':
   old=p.read_bytes();record=json.loads(old)
   for key in ['consoleURL','bucketId','outputBucket']:record.pop(key,None)
   published=json.dumps(record,indent=2)+'\n';t=dest/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(published)
   redactions.append({'file':str(rel),'originalSHA256':sha(old),'publishedSHA256':sha(published.encode()),'publication':'Private console/bucket identifiers omitted from public launch receipt; scientific job identity and costs retained.'});continue
  copy(p,rel)
for name in ['prepared-v2','prepared-v3','prepared-v4']:
 shutil.copytree(base/name,dest/'prepared-inputs'/name)
for name in ['REPORT.md','AUDIT.json','INDEPENDENT_REPLAY.json','IMPLEMENTATION_STATUS.md','INTERPRETATION_NOTES.md','mechanism-map.svg','mechanism-map-preview.jpg','COST_LEDGER.json']:
 copy(base/name,name)
source=ROOT/'work/scienceclaw-upload/collagen-transition-atlas'
for p in source.rglob('*'):
 if p.is_file() and 'web' not in p.relative_to(source).parts:copy(p,Path('analysis-and-source')/p.relative_to(source))
copy(ROOT/'work/verify_transition_archive.py','analysis-and-source/verify_transition_archive.py')
copy(Path(__file__),'analysis-and-source/seal_transition_bundle.py')
readme='''# Collagen transition atlas: frozen v4 commissioning record

This is a completed archival collection, not a claim that every numerical state converged. Read [REPORT.md](REPORT.md), [AUDIT.json](AUDIT.json), and [COST_LEDGER.json](COST_LEDGER.json).

- `attempts/` keeps all three real job identities, immutable inputs, observed outcomes, downloaded output ZIPs, verified extraction, and available stdout/stderr. v4 is the converged-solver revision. v2 remains a failed partial study. The first attempt's numerical data were lost after its archive writer failed on an Object Storage seek; the gap is explicit and is not reconstructed.
- `prepared-inputs/prepared-v3/` was prepared but never submitted. v4b was rejected at job creation for request size; v4c is the actual compact transport. All reconstruct the checksum-identified canonical source as documented.
- `attempts/aijob-e00dv1sg6b68gbz2hp/final/extracted/runs/commission/` contains the final recorded protocol samples, full suite JSON, source snapshots, figures, GIFs, checks, and manifest. Raw samples include invalid equilibria; they must not be silently treated as valid predictions.
- `analysis-and-source/` contains the inspected model and later readback/export helpers. The exact code actually executed is identified by the dispatched input, source ZIP, and run context. Later audit/export helpers were not executed as part of the H100 simulation.
- `PUBLICATION_REDACTIONS.json` describes removed account UI context. Scientific raw files and recovered job stdout/stderr are unchanged. Every retained file is covered by `MANIFEST.json`.

These finite 2D and normalized models do not establish tissue pressure/acceleration tolerance, chemical AGE reactions, species-specific melting temperatures, or a calibrated LOX signaling switch. Internal optimizer iterates and intermediate hold substeps were not recorded as trajectories; all recorded protocol samples are preserved. Thermal melting MD was not run.

Future studies must use a new directory and identity. Never replace this collection. Files larger than 95 MiB use the repository's GitHub Releases transport with full-file and part checksums; the manifest remains complete.
'''
(dest/'README.md').write_text(readme)
(dest/'PUBLICATION_REDACTIONS.json').write_text(json.dumps(redactions,indent=2)+'\n')
# Check every compressed result recursively as data, including for accidental secrets.
secret=re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')
for p in dest.rglob('*'):
 if not p.is_file():continue
 b=p.read_bytes();assert not secret.search(b), str(p)
 if p.suffix=='.zip':
  with zipfile.ZipFile(p) as z:
   for name in z.namelist():assert not secret.search(z.read(name)),str(p)+'::'+name
finished={'status':'complete','kind':'archive','finishedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':{'study':'collagen-transition-atlas','purpose':'Preserve all available inputs, raw outputs, numerical failures, analysis, figures and logs from the three recorded attempts','scientificStatus':'See individual attempt outcomes and AUDIT.json; archival completion is not universal numerical convergence','firstAttemptRawData':'unavailable after output-writer failure; gap preserved explicitly','remoteCredentialExposure':'No account secrets or SSH keys provided to scientific worker'}}
(dest/'FINISHED.json').write_text(json.dumps(finished,indent=2)+'\n')
manifest={str(p.relative_to(dest)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(dest.rglob('*')) if p.is_file()}
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'directory':str(dest),'files':len(manifest),'bytes':sum(r['bytes'] for r in manifest.values()),'manifestSHA256':sha((dest/'MANIFEST.json').read_bytes())},indent=2))
