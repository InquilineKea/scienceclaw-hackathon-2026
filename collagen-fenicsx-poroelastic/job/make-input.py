from pathlib import Path
import hashlib,json,zipfile
files=['coupled.py','plot.py','isolation.py','networks.json.gz','baseline.json.gz'];hashes={}
with zipfile.ZipFile('poro-inputs.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 for n in files:
  b=Path(n).read_bytes();hashes[n]=hashlib.sha256(b).hexdigest();z.writestr(n,b)
Path('INPUT_MANIFEST.json').write_text(json.dumps(hashes,indent=2)+'\n');print('Input ZIP',Path('poro-inputs.zip').stat().st_size,'SHA256',hashlib.sha256(Path('poro-inputs.zip').read_bytes()).hexdigest())
