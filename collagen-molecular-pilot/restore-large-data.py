#!/usr/bin/env python3
"""Restore release-backed files byte-for-byte; never replace an existing file.

Usage: python3 -I restore-large-data.py LARGE_DATASETS.json DESTINATION
Uses only the Python standard library. No login required for public datasets.
"""
import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

REPOSITORY = 'InquilineKea/scienceclaw-hackathon-2026'

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def safe_name(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or '..' in p.parts or '\\' in name or
            str(p) != name or any(ord(c) < 32 for c in name)):
        raise ValueError('Unsafe path in dataset index')
    return p

def restore(index, destination, opener=None):
    if index.get('schemaVersion') != 1 or index.get('repository') != REPOSITORY:
        raise ValueError('Unknown dataset index')
    root = Path(destination).absolute()
    for parent in [root, *root.parents]:
        if parent.is_symlink(): raise ValueError('Symlink in destination path')
    root.mkdir(parents=True, exist_ok=True)
    records = []
    for name, item in index['files'].items():
        target = root.joinpath(*safe_name(name).parts)
        for parent in [target, *target.parents]:
            if parent.is_symlink(): raise ValueError('Symlink in destination path')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.is_file() and target.stat().st_size == item['bytes'] and digest(target) == item['sha256']:
                records.append({'path':name, 'status':'already_verified'}); continue
            raise ValueError('Refusing to replace existing file: ' + name)
        h = hashlib.sha256(); total = 0
        # The temporary file is on the same filesystem. link() is an exclusive,
        # atomic publication; unlike replace(), it cannot clobber a racing writer.
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.restore-', delete=False) as out:
            temp = Path(out.name)
            try:
                for part in item['parts']:
                    url = part['url']
                    prefix = 'https://github.com/' + REPOSITORY + '/releases/download/'
                    if not url.startswith(prefix) or len(url[len(prefix):].split('/')) != 2:
                        raise ValueError('Unexpected asset URL')
                    if not re.fullmatch(r'[A-Za-z0-9._/-]+', url[len(prefix):]):
                        raise ValueError('Unsafe asset URL')
                    ph = hashlib.sha256(); size = 0
                    request = urllib.request.Request(url, headers={'User-Agent':'ScienceClaw-data-restore/1'})
                    with (opener(request) if opener else urllib.request.urlopen(request, timeout=120)) as response:
                        for block in iter(lambda: response.read(1024 * 1024), b''):
                            size += len(block)
                            if size > part['bytes']: raise ValueError('Oversized downloaded part')
                            ph.update(block); h.update(block); out.write(block)
                    if size != part['bytes'] or ph.hexdigest() != part['sha256']:
                        raise ValueError('Downloaded part checksum mismatch')
                    total += size
                if total != item['bytes'] or h.hexdigest() != item['sha256']:
                    raise ValueError('Reconstructed file checksum mismatch')
                out.flush(); os.fsync(out.fileno())
                os.link(temp, target)
                records.append({'path':name,'status':'restored','bytes':total,'sha256':h.hexdigest()})
            finally:
                temp.unlink(missing_ok=True)
    return records

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('index'); ap.add_argument('destination'); args = ap.parse_args()
    print(json.dumps(restore(json.loads(Path(args.index).read_text()), args.destination), indent=2))
