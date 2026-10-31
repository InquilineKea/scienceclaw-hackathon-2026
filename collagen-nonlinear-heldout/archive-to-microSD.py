#!/usr/bin/env python3
"""Original stdlib private research archive; no cloud or publication operations.

Default: inspect the bounded source and print a plan without writing to microSD.
Write only after final publication records exist:
  python3 archive-to-microSD.py --archive
Later verification (read-only; source need not exist):
  python3 payload/archive-to-microSD.py --verify-only /path/to/archive

The source is exactly this script's containing research folder. External
symlinks, credentials and unrelated environment caches are never followed.
In-folder raw scientific transports, failures, audits and private scientific
sources are retained. This is a private archive, not the public allowlist.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import time
import unicodedata
import uuid
import zipfile

SOURCE = Path(__file__).resolve().parent
MOUNT = Path('/Volumes/microSD')
RELATIVE_DESTINATION = Path('Research Runs/2026-10-31/nonlinear-buckling-sliding-heldout-3d')
SKIP_DIRECTORIES = {'.git', '.hg', '.svn', '.ssh', '.aws', '.gnupg', '.secrets',
                    '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
                    '.mypy_cache', '.ruff_cache', '.cache', 'unrelated-scratch'}
SECRET_DIRECTORIES = {'.ssh', '.aws', '.gnupg', '.secrets'}
SKIP_FILES = {'.ds_store', '.netrc', '.npmrc', '.pypirc', 'credentials',
              'credentials.json', 'credentials.ini', 'auth.json', 'token.json',
              'tokens.json', 'secrets.json', 'secrets.toml'}
SECRET_FILE = re.compile(r'^(?:\.env(?:\..*)?|id_(?:rsa|dsa|ecdsa|ed25519)(?:\..*)?)$|\.(?:pem|p12|pfx|key)$', re.I)
SECRET_PATTERNS = [
    ('private_key_block', re.compile(rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')),
    ('aws_access_key', re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),
    ('github_token', re.compile(rb'\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b')),
    ('openai_token', re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b')),
    ('slack_token', re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b')),
]
TEXT_SUFFIXES = {'.txt', '.json', '.md', '.py', '.js', '.mjs', '.html', '.css',
                 '.xml', '.csv', '.tsv', '.yaml', '.yml', '.toml', '.ini', '.log', '.sh'}
SCAN_CHUNK = 1024*1024
MAX_ZIP_ENTRIES = 200000
MAX_ZIP_TEXT_BYTES = 512*1024**2


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(SCAN_CHUNK), b''):
            h.update(block)
    return h.hexdigest()


def signature(path):
    s = path.lstat()
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)


def filename_secret(parts):
    return any(part.casefold() in SKIP_FILES or part.casefold() in SECRET_DIRECTORIES or SECRET_FILE.search(part)
               for part in parts)


def scan_stream(stream):
    tail = b''
    for block in iter(lambda: stream.read(SCAN_CHUNK), b''):
        value = tail+block
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(value):
                return label
        tail = value[-512:]
    return None


def secret_reason(path):
    # Names plus high-confidence token/key markers, never printing match values.
    if filename_secret(path.parts):
        return 'credential_or_private_key_filename'
    with path.open('rb') as stream:
        found = scan_stream(stream)
    if found:
        return 'high_confidence_secret_marker:'+found
    # Inspect archive names and text without extracting or executing contents.
    # Public dependency wheels are retained as inert binaries when inside the
    # source; nested wheels cannot contain credentials introduced by this run.
    if path.suffix.casefold() in {'.zip', '.npz'}:
        try:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_ZIP_ENTRIES:
                    return 'zip_safety_limit_manual_review_required'
                scanned = 0
                for entry in entries:
                    parts = PurePosixPath(entry.filename).parts
                    if filename_secret(parts):
                        return 'credential_filename_inside_zip'
                    if entry.is_dir() or PurePosixPath(entry.filename).suffix.casefold() not in TEXT_SUFFIXES:
                        continue
                    scanned += entry.file_size
                    if scanned > MAX_ZIP_TEXT_BYTES:
                        return 'zip_text_scan_limit_manual_review_required'
                    with archive.open(entry) as stream:
                        found = scan_stream(stream)
                    if found:
                        return 'high_confidence_secret_marker_inside_zip:'+found
        except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
            return 'unreadable_or_encrypted_zip_manual_review_required'
    return None


def path_inventory(source):
    files = []
    excluded = []
    for base, dirs, names in os.walk(source, topdown=True, followlinks=False):
        base = Path(base)
        for name in sorted(dirs[:]):
            path = base/name
            relative = path.relative_to(source).as_posix()
            if path.is_symlink():
                dirs.remove(name)
                excluded.append(dict(path=relative, reason='symlink_directory_not_followed'))
            elif name.casefold() in SKIP_DIRECTORIES:
                dirs.remove(name)
                excluded.append(dict(path=relative, reason='credential_environment_or_unrelated_cache_directory'))
        dirs.sort()
        for name in sorted(names):
            path = base/name
            relative = path.relative_to(source).as_posix()
            if path.is_symlink():
                excluded.append(dict(path=relative, reason='symlink_file_not_followed'))
                continue
            if not stat.S_ISREG(path.lstat().st_mode):
                excluded.append(dict(path=relative, reason='nonregular_file'))
                continue
            if name.casefold() in SKIP_FILES or SECRET_FILE.search(name):
                excluded.append(dict(path=relative, reason='credential_cache_or_private_key_filename'))
                continue
            files.append((relative, path, signature(path)))
    files.sort()
    return files, excluded


def plan(source):
    raw, excluded = path_inventory(source)
    eligible = []
    folded = {}
    for relative, path, initial in raw:
        collision = unicodedata.normalize('NFC', relative).casefold()
        if collision in folded:
            raise RuntimeError('Case/Unicode path collision for removable-media copy: '+relative)
        folded[collision] = relative
        reason = secret_reason(path)
        if signature(path) != initial:
            raise RuntimeError('Source changed while planning: '+relative)
        if reason:
            excluded.append(dict(path=relative, reason=reason))
        else:
            eligible.append((relative, path, initial))
    return eligible, sorted(excluded, key=lambda x: x['path']), raw


def checked_mount():
    if MOUNT.is_symlink() or not MOUNT.is_dir() or not os.path.ismount(MOUNT):
        raise RuntimeError('Required removable volume is not mounted at /Volumes/microSD; no destination created.')
    resolved = MOUNT.resolve()
    if resolved != MOUNT or not os.access(MOUNT, os.W_OK):
        raise RuntimeError('microSD mount is redirected or not writable; no destination created.')
    return shutil.disk_usage(MOUNT)


def write_json(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def private_source_category(relative):
    low = relative.casefold()
    if 'private' in low or 'drive' in low or low.endswith('.xml'):
        return 'private_or_source_material_local_retention_only'
    if low.endswith(('.zip', '.tar', '.tar.gz', '.tgz', '.npz', '.whl')):
        return 'scientific_source_or_transport_archive_local_retention'
    return 'bounded_research_folder_local_retention'


def verify_archive(root):
    manifest_path = root/'MANIFEST.json'; receipt_path = root/'RECEIPT.json'
    manifest = json.loads(manifest_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    errors = []
    if digest_file(manifest_path) != receipt.get('manifest_sha256'):
        errors.append(dict(kind='manifest_hash_mismatch'))
    checked = 0
    expected = set()
    for item in manifest['files']:
        q = PurePosixPath(item['archive_path'])
        if q.is_absolute() or '..' in q.parts or not q.parts or q.parts[0] != 'payload':
            errors.append(dict(kind='unsafe_manifest_path')); continue
        file = root.joinpath(*q.parts); expected.add(q.as_posix())
        if file.is_symlink() or not file.is_file():
            errors.append(dict(path=q.as_posix(), kind='missing_or_symlink')); continue
        if file.stat().st_size != item['bytes'] or digest_file(file) != item['sha256']:
            errors.append(dict(path=q.as_posix(), kind='payload_hash_or_size_mismatch'))
        else:
            checked += 1
    present = set()
    for base, dirs, names in os.walk(root/'payload', followlinks=False):
        base = Path(base)
        for name in dirs[:]:
            if (base/name).is_symlink():
                errors.append(dict(path=(base/name).relative_to(root).as_posix(), kind='unexpected_symlink_directory'))
                dirs.remove(name)
        for name in names:
            present.add((base/name).relative_to(root).as_posix())
    if present != expected:
        errors.append(dict(kind='unexpected_or_missing_payload_paths', unexpected=sorted(present-expected), missing=sorted(expected-present)))
    return dict(verified=not errors, files_verified=checked, expected_files=len(expected),
                manifest_sha256=digest_file(manifest_path), errors=errors)


def archive(source, files, excluded, raw_inventory):
    space = checked_mount()
    total = sum(s[2] for _, _, s in files)
    reserve = max(64*1024**2, math_ceil(total*.05))
    if space.free < total+reserve:
        raise RuntimeError('Insufficient free space for verified copy plus safety reserve.')
    destination = MOUNT/RELATIVE_DESTINATION
    if destination.exists() or destination.is_symlink():
        raise RuntimeError('Archive destination already exists; refusing to overwrite it.')
    parent = destination.parent
    # Do not traverse a pre-existing redirect under the removable mount.
    cursor = MOUNT
    for part in RELATIVE_DESTINATION.parts[:-1]:
        cursor = cursor/part
        if cursor.is_symlink():
            raise RuntimeError('Destination parent contains a symlink; refusing redirected copy.')
    parent.mkdir(parents=True, exist_ok=True)
    checked_mount()
    if parent.stat().st_dev != MOUNT.stat().st_dev:
        raise RuntimeError('Destination parent is not on the checked microSD filesystem.')
    staging = parent/('.'+destination.name+'.partial-'+uuid.uuid4().hex[:12])
    staging.mkdir(mode=0o700)
    (staging/'payload').mkdir()
    started = now(); records = []
    original_paths = {r for r, _, _ in raw_inventory}
    try:
        for relative, src, initial in files:
            checked_mount()
            if signature(src) != initial:
                raise RuntimeError('Source changed before copy: '+relative)
            dst = staging/'payload'/relative; dst.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256(); count = 0
            with src.open('rb') as inp, dst.open('xb') as out:
                if (os.fstat(inp.fileno()).st_dev, os.fstat(inp.fileno()).st_ino,
                    os.fstat(inp.fileno()).st_size, os.fstat(inp.fileno()).st_mtime_ns) != initial:
                    raise RuntimeError('Source identity changed at open: '+relative)
                for block in iter(lambda: inp.read(SCAN_CHUNK), b''):
                    out.write(block); h.update(block); count += len(block)
                out.flush(); os.fsync(out.fileno())
            if signature(src) != initial or count != initial[2]:
                raise RuntimeError('Source changed during copy: '+relative)
            digest = h.hexdigest()
            if dst.stat().st_size != count or digest_file(dst) != digest:
                raise RuntimeError('Destination verification failed: '+relative)
            records.append(dict(source_relative_path=relative, archive_path='payload/'+relative,
                                bytes=count, sha256=digest, source_mtime_ns=initial[3],
                                source_category=private_source_category(relative)))
        # Detect active writers/new files rather than silently archiving a mixed state.
        current, current_excluded = path_inventory(source)
        if {r for r, _, _ in current} != original_paths:
            raise RuntimeError('Source file inventory changed during archive; retry after writers finish.')
        for item, (_, src, initial) in zip(records, files):
            if signature(src) != initial or digest_file(src) != item['sha256']:
                raise RuntimeError('Final source recheck failed: '+item['source_relative_path'])
        manifest = dict(schema=1, archive_kind='private_bounded_research_folder_copy',
                        started_utc=started, finished_utc=now(), source_folder=source.name,
                        scope='Every eligible regular file currently inside this research folder; no external links followed.',
                        visibility='PRIVATE RESEARCH ARCHIVE — not the public source export; may contain private scientific sources.',
                        originals_retained=True, encryption_performed_by_script=False,
                        included_files=len(records), included_bytes=sum(x['bytes'] for x in records),
                        exclusions=excluded, files=records,
                        coverage=dict(failures_and_audits='Included when present inside the source.',
                                      raw_transport_and_private_scientific_archives='Included locally when inside the source and no secret marker is detected.',
                                      vendor_wheels='In-folder wheels/transport copies retained; outside-folder vendor binaries and all symlinks are not followed.',
                                      outside_folder_sources='Not included; no broad Drive or unrelated archive traversal.',
                                      secret_scan='Filename, high-confidence token/key markers and ZIP text/name inspection; not a comprehensive credential-safety certification.'))
        write_json(staging/'MANIFEST.json', manifest)
        receipt = dict(schema=1, completed_utc=now(), destination=str(destination),
                       source_folder=source.name, originals_retained=True,
                       included_files=len(records), included_bytes=manifest['included_bytes'],
                       excluded_entries=len(excluded), all_eligible_files_copied_and_sha256_verified=True,
                       complete_source_without_exclusions=not excluded,
                       manifest_sha256=digest_file(staging/'MANIFEST.json'),
                       free_bytes_at_start=space.free, required_bytes_with_reserve=total+reserve,
                       mount_checked_with_os_path_ismount=True,
                       note='Verified at copy time. The script does not eject the volume or encrypt the copy.')
        write_json(staging/'RECEIPT.json', receipt)
        result = verify_archive(staging)
        if not result['verified']:
            raise RuntimeError('Final manifest verification failed; partial archive retained.')
        checked_mount()
        if destination.exists():
            raise RuntimeError('Destination appeared during copy; partial archive retained.')
        staging.rename(destination)
        return dict(destination=str(destination), receipt=receipt, verification=result)
    except BaseException as exc:
        # Preserve partial evidence; never delete originals or a failed staging tree.
        failure = dict(failed_utc=now(), source_folder=source.name, copied_verified_files=len(records),
                       originals_retained=True, partial_archive=str(staging),
                       error_type=type(exc).__name__, error=str(exc), exclusions=excluded)
        try:
            write_json(staging/'FAILURE.json', failure)
        except OSError:
            pass
        raise


def math_ceil(value):
    return int(value) if value == int(value) else int(value)+1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--archive', action='store_true', help='Write the checked private copy to the fixed microSD destination.')
    mode.add_argument('--verify-only', type=Path, metavar='ARCHIVE', help='Read-only SHA256/manifest verification of an existing copy.')
    args = parser.parse_args()
    if args.verify_only:
        result = verify_archive(args.verify_only)
        print(json.dumps(result, indent=2)); return 0 if result['verified'] else 1
    checked_mount()
    files, excluded, raw = plan(SOURCE)
    total = sum(s[2] for _, _, s in files)
    if not args.archive:
        usage = checked_mount()
        print(json.dumps(dict(mode='read_only_plan_no_microSD_write', source=str(SOURCE),
                              destination=str(MOUNT/RELATIVE_DESTINATION), eligible_files=len(files),
                              eligible_bytes=total, microSD_free_bytes=usage.free,
                              exclusions=excluded, visibility='Private local archive, not public export',
                              next_action='Run with --archive only after final publication records and active writes are complete.'), indent=2))
        return 0
    print(json.dumps(archive(SOURCE, files, excluded, raw), indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(json.dumps(dict(completed=False, originals_retained=True,
                              error_type=type(exc).__name__, error=str(exc))), file=sys.stderr)
        sys.exit(1)
