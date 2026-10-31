import hashlib
import json
import subprocess
from pathlib import Path

root='https://ghcr.io/v2/fenics/dolfinx/dolfinx/'
def curl(url,headers=[]):return subprocess.check_output(['/usr/bin/curl','-fsSL',*sum((['-H',h] for h in headers),[]),url])
t=json.loads(curl('https://ghcr.io/token?service=ghcr.io&scope=repository:fenics/dolfinx/dolfinx:pull'))['token'];headers=['Authorization: Bearer '+t,'Accept: application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json']
b=curl(root+'manifests/v0.10.0-r1',headers);index=json.loads(b);Path('image-index.json').write_bytes(b)
if 'manifests' in index:
 item=next(x for x in index['manifests'] if x.get('platform',{}).get('architecture')=='amd64');digest=item['digest'];b=curl(root+'manifests/'+digest,headers)
else:digest='sha256:'+hashlib.sha256(b).hexdigest()
m=json.loads(b);assert digest=='sha256:'+hashlib.sha256(b).hexdigest();Path('image-manifest.json').write_bytes(b);c=curl(root+'blobs/'+m['config']['digest'],headers);assert 'sha256:'+hashlib.sha256(c).hexdigest()==m['config']['digest'];Path('image-config.json').write_bytes(c);cfg=json.loads(c)
print(json.dumps({'image':'ghcr.io/fenics/dolfinx/dolfinx@'+digest,'created':cfg.get('created'),'architecture':cfg.get('architecture'),'bytes':sum(x['size'] for x in m['layers']),'entrypoint':cfg.get('config',{}).get('Entrypoint'),'cmd':cfg.get('config',{}).get('Cmd'),'historyCommands':len(cfg.get('history',[]))},indent=2))
