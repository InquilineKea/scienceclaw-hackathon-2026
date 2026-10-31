"""Append-only GitHub Release transport for sealed files larger than 95 MiB.

Original standard-library code. Existing host-side gh session only. No installers,
asset deletion, force pushes, tag replacement, or credential-bearing downloads.
"""
import hashlib, json, os, re, shutil, subprocess, tempfile, uuid
from pathlib import Path

REPOSITORY = 'InquilineKea/scienceclaw-hackathon-2026'
PART_BYTES = 1024 ** 3
PARTS_PER_RELEASE = 900  # GitHub allows 1000 assets; reserve room for metadata/retries.
RESERVED = '_release'

def encoded(value): return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()

def inspect_file(path, secret=None, part_bytes=PART_BYTES):
    """Bounded-memory hash and secret scan, including chunk/read boundaries."""
    h = hashlib.sha256(); parts = []; total = 0; tail = b''
    with Path(path).open('rb') as f:
        while True:
            ph = hashlib.sha256(); size = 0
            while size < part_bytes:
                b = f.read(min(1024 * 1024, part_bytes - size))
                if not b: break
                if secret and secret.search(tail + b): raise ValueError('Potential credential in ' + str(Path(path).name))
                tail = (tail + b)[-512:]; h.update(b); ph.update(b); size += len(b)
            if not size: break
            parts.append({'bytes':size,'sha256':ph.hexdigest()}); total += size
    return {'path':Path(path), 'bytes':total,'sha256':h.hexdigest(),'parts':parts}

class Releases:
    def __init__(self, work, env):
        self.work = Path(work); self.env = dict(env); self.gh = shutil.which('gh')
        if not self.gh: raise RuntimeError('Existing GitHub CLI is required')
        self.base = 'repos/' + REPOSITORY + '/releases'; self.cache = {}

    def api(self, endpoint, method='GET', data=None, file=None, missing=False):
        args = [self.gh,'api','--method',method,endpoint]
        body = None
        if data is not None: args += ['--input','-']; body = encoded(data)
        if file is not None: args += ['--input',str(file),'-H','Content-Type: application/octet-stream']
        r = subprocess.run(args, input=body, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
        if r.returncode:
            if missing and b'HTTP 404' in r.stderr: return None
            raise RuntimeError('GitHub Releases request failed; data retained for retry (HTTP/auth/connection).')
        return json.loads(r.stdout) if r.stdout else None

    def get(self, tag):
        release = self.api(self.base + '/tags/' + tag, missing=True)
        if release is not None: return release
        # Drafts have no public Git tag yet. The authenticated release list is
        # required to recover them after an interrupted attempt.
        page = 1
        while True:
            batch = self.api(self.base + '?per_page=100&page=' + str(page))
            matches = [r for r in batch if r['tag_name'] == tag]
            if len(matches) > 1: raise ValueError('Ambiguous release tag; refusing mutation')
            if matches: return matches[0]
            if len(batch) < 100: return None
            page += 1

    def assets(self, release, refresh=False):
        rid = release['id']
        if rid not in self.cache or refresh:
            assets = []; page = 1
            while True:
                batch = self.api(self.base + '/' + str(rid) + '/assets?per_page=100&page=' + str(page))
                assets += batch
                if len(batch) < 100: break
                page += 1
            self.cache[rid] = assets
        return self.cache[rid]

    def ensure(self, tag, identity, head, prefix):
        release = self.get(tag)
        marker = 'ScienceClaw sealed-data identity: ' + identity
        if release:
            if marker not in (release.get('body') or '').splitlines():
                raise ValueError('Release tag belongs to other content; refusing collision: ' + tag)
            return release
        # A pre-existing Git tag without our release is also a collision.
        ref = self.api('repos/' + REPOSITORY + '/git/ref/tags/' + tag, missing=True)
        if ref is not None: raise ValueError('Unowned existing Git tag: ' + tag)
        body = marker + '\n\nLossless scientific archive; no new simulation or biological validation.\n\n'
        body += 'Dataset index: https://github.com/' + REPOSITORY + '/tree/main/' + prefix + '/_release\n\n'
        body += 'Use LARGE_DATASETS.json and restore-large-data.py to verify and reconstruct every original large file. '
        body += 'MANIFEST.json contains the original file checksums. Assets are never replaced by this workflow.\n'
        try:
            return self.api(self.base,'POST',{'tag_name':tag,'target_commitish':head,
                'name':'Frozen scientific data: ' + tag,'body':body,'draft':True,'prerelease':False})
        except RuntimeError:
            release = self.get(tag)
            if release and marker in (release.get('body') or '').splitlines(): return release
            raise

    def verify(self, asset, size, checksum):
        if asset.get('state') != 'uploaded' or asset.get('size') != size: return False
        if asset.get('digest'): return asset['digest'] == 'sha256:' + checksum
        # Older GitHub responses may omit digest; authenticate only through gh.
        path = self.work / ('verify-' + uuid.uuid4().hex)
        with path.open('xb') as f:
            r = subprocess.run([self.gh,'api', self.base + '/assets/' + str(asset['id']),
                '-H','Accept: application/octet-stream'], stdout=f, stderr=subprocess.PIPE, env=self.env)
        try:
            return r.returncode == 0 and inspect_file(path)['sha256'] == checksum and path.stat().st_size == size
        finally: path.unlink(missing_ok=True)

    def put(self, release, name, file, size, checksum):
        """Reuse verified assets; retain interrupted starter assets without deleting."""
        assets = self.assets(release)
        candidates = sorted([a for a in assets if a['name'] == name or a['name'].startswith(name + '.retry-')], key=lambda a:a['id'])
        for a in candidates:
            if self.verify(a,size,checksum): return a
            if a.get('state') == 'uploaded': raise ValueError('Existing asset differs; refusing overwrite: ' + a['name'])
        if not release['draft']: raise ValueError('Published release is missing a valid asset; refusing mutation')
        if len(assets) >= 999: raise ValueError('Release asset capacity exhausted by prior attempts; all files remain local')
        chosen = name if not candidates else name + '.retry-' + uuid.uuid4().hex[:12]
        endpoint = 'https://uploads.github.com/repos/' + REPOSITORY + '/releases/' + str(release['id']) + '/assets?name=' + chosen
        try: asset = self.api(endpoint,'POST',file=file)
        except RuntimeError:
            # An upload may have completed even if the response was interrupted.
            self.assets(release,refresh=True)
            for a in self.cache[release['id']]:
                if a['name'] == chosen and self.verify(a,size,checksum): return a
            raise
        self.cache[release['id']].append(asset)
        if not self.verify(asset,size,checksum): raise ValueError('Uploaded asset failed size/checksum verification')
        return asset

    def put_bytes(self, release, name, data):
        path = self.work / ('metadata-' + uuid.uuid4().hex)
        try:
            path.write_bytes(data)
            return self.put(release,name,path,len(data),hashlib.sha256(data).hexdigest())
        finally: path.unlink(missing_ok=True)

    def publish(self, release, commit):
        current = self.get(release['tag_name'])
        if current['draft']:
            current = self.api(self.base + '/' + str(current['id']),'PATCH',
                               {'draft':False,'target_commitish':commit,'make_latest':'false'})
        if current['draft']: raise RuntimeError('Release publication remains pending')
        return current['html_url']

def prepare(publisher, payload, large, kind, runid, fingerprint, prefix, releases=None):
    """Prepare all assets, returning Git payload plus a final publication callback."""
    head = publisher.fetch(); existing = publisher.tree(head,prefix)
    base = {prefix + '/' + n:hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
            for n,b in payload.items()}
    generated = ['_release/LARGE_DATASETS.json','_release/restore-large-data.py','_release/README.md']
    saved = None
    if existing:
        if set(existing) != set(base) | {prefix + '/' + n for n in generated} or any(existing.get(n) != h for n,h in base.items()):
            raise ValueError('Existing run differs; no release assets or run files were replaced')
        saved = {n:publisher.command(['show',head + ':' + prefix + '/' + n]).stdout for n in generated}
        index = json.loads(saved[generated[0]])
        if index.get('manifestSHA256') != fingerprint or index.get('repository') != REPOSITORY or set(index['files']) != set(large):
            raise ValueError('Existing large-data index differs')
    api = releases or Releases(publisher.work,publisher.env)
    identity = kind + '/' + runid + '/' + fingerprint
    tagbase = 'data-' + kind + '-' + runid + '-' + fingerprint[:20]
    index_new = {'schemaVersion':1,'repository':REPOSITORY,'kind':kind,'runId':runid,
                 'manifestSHA256':fingerprint,'partBytes':PART_BYTES,'files':{}}
    release_map = {}; counter = 0
    for name, info in sorted(large.items()):
        item = {'bytes':info['bytes'],'sha256':info['sha256'],'parts':[]}
        if saved and (index['files'][name]['bytes'] != info['bytes'] or index['files'][name]['sha256'] != info['sha256']):
            raise ValueError('Existing raw-data fingerprint differs')
        with info['path'].open('rb') as f:
            for number, part in enumerate(info['parts']):
                tag = tagbase + '-s' + str(counter // PARTS_PER_RELEASE + 1).zfill(4); counter += 1
                if tag not in release_map: release_map[tag] = api.ensure(tag,identity,head,prefix)
                release = release_map[tag]
                asset_name = hashlib.sha256(name.encode()).hexdigest()[:16] + '-part-' + str(number+1).zfill(6) + '-' + part['sha256'] + '.bin'
                path = publisher.work / ('part-' + uuid.uuid4().hex)
                ph = hashlib.sha256(); remaining = part['bytes']
                try:
                    with path.open('xb') as out:
                        while remaining:
                            b = f.read(min(1024 * 1024,remaining))
                            if not b: raise ValueError('Source truncated during upload')
                            out.write(b); ph.update(b); remaining -= len(b)
                    if ph.hexdigest() != part['sha256']: raise ValueError('Source changed during upload')
                    asset = api.put(release,asset_name,path,part['bytes'],part['sha256'])
                finally: path.unlink(missing_ok=True)
                item['parts'].append({**part,'url':asset['browser_download_url'],'releaseTag':tag,'assetName':asset['name']})
            if f.read(1): raise ValueError('Source grew during upload')
        index_new['files'][name] = item
    if saved:
        if index_new != index: raise ValueError('Existing large-data index has different asset mapping')
        metadata = saved
    else:
        readme = '# Release-backed raw data\n\nAll original files are covered by the adjacent MANIFEST.json. '
        readme += 'Small files are in Git; the large files below are stored losslessly in GitHub Releases. '
        readme += 'The GitHub source-code ZIP alone does not include release assets.\n\n'
        for name, item in index_new['files'].items():
            readme += '* `' + name + '`: ' + str(item['bytes']) + ' bytes; SHA-256 `' + item['sha256'] + '`.\n'
            for i,p in enumerate(item['parts']): readme += '  * [Download part ' + str(i+1) + '](' + p['url'] + ')\n'
        readme += '\nDownload this directory’s `LARGE_DATASETS.json` and `restore-large-data.py`, then run:\n\n'
        readme += '```sh\npython3 -I restore-large-data.py LARGE_DATASETS.json /path/to/recovery\n```\n\n'
        readme += 'Restoration verifies every part and whole-file checksum, and refuses to replace differing existing files. '
        readme += 'The uploader never deletes or replaces assets or tags; administrators can still alter repository content. '
        readme += 'Keep the local copy and manifest as an independent copy.\n'
        metadata = {generated[0]:encoded(index_new), generated[1]:Path(__file__).with_name('restore-large-data.py').read_bytes(),generated[2]:readme.encode()}
    for release in release_map.values():
        api.put_bytes(release,'LARGE_DATASETS.json',metadata[generated[0]])
        api.put_bytes(release,'MANIFEST.json',payload['MANIFEST.json'])
        api.put_bytes(release,'restore-large-data.py',metadata[generated[1]])
    def finish(commit):
        urls = [api.publish(r,commit) for r in release_map.values()]
        return {'largeFiles':len(large),'largeBytes':sum(x['bytes'] for x in large.values()),
                'releases':urls,'datasetIndex':'https://github.com/' + REPOSITORY + '/blob/' + commit + '/' + prefix + '/_release/LARGE_DATASETS.json'}
    return {**payload,**metadata}, finish
