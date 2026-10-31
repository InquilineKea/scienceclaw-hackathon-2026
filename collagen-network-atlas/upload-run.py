#!/usr/bin/env python3
"""Publish sealed scientific runs by adding a new Git tree; never replace a run."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath

_spec=importlib.util.spec_from_file_location('large_data',Path(__file__).with_name('large_data.py'))
large_data=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(large_data)

REPOSITORY='InquilineKea/scienceclaw-hackathon-2026'
PREFIXES={'atlas':'collagen-network-atlas/runs','molecular':'collagen-molecular-pilot/runs','archive':'datasets'}
LIMIT=95*1024*1024
SECRET=re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|(?i:authorization\s*:\s*bearer\s+)[A-Za-z0-9_.-]{20,}')
DENIED={'.env','.git','.aws','.ssh','credentials','credentials.json','auth.json','hosts.yml','cookies.sqlite','login data'}

def now():return datetime.datetime.now(datetime.UTC).isoformat()
def sha(data):return hashlib.sha256(data).hexdigest()
def gitsha(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def write_new(path,data):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')

def validated_files(run,kind):
    run=Path(run).absolute()
    if run.is_symlink() or not run.is_dir():raise ValueError('Run must be a real directory')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}',run.name):raise ValueError('Invalid run ID')
    for flag in ['FAILED.json','PREPARED.json']:
        if (run/flag).exists():raise ValueError('Failed or prepared-only runs are not published')
    finished=json.loads((run/'FINISHED.json').read_text())
    if finished.get('status')!='complete':raise ValueError('Run is not complete')
    manifest_bytes=(run/'MANIFEST.json').read_bytes()
    manifest=json.loads(manifest_bytes)
    if not isinstance(manifest,dict) or not manifest:raise ValueError('Missing file manifest')
    actual=set()
    for p in run.rglob('*'):
        if p.is_symlink():raise ValueError('Symlinks are never uploaded')
        if p.is_file():actual.add(str(p.relative_to(run)))
    if actual != set(manifest)|{'MANIFEST.json'}:raise ValueError('Unlisted, missing or extra run files')
    payload={}
    for name in sorted(actual):
        parts=PurePosixPath(name)
        if (parts.is_absolute() or '..' in parts.parts or '\\' in name or
            any(ord(c)<32 for c in name) or parts.parts[0]=='_release' or any(x.lower() in DENIED for x in parts.parts) or
            Path(name).suffix.lower() in {'.pem','.key','.p12','.pfx'}):
            raise ValueError('Sensitive or unsafe file path: '+name)
        p=run/name
        if p.stat().st_size>LIMIT:
            info=large_data.inspect_file(p,SECRET)
            m=manifest[name]
            if info['bytes']!=m['bytes'] or info['sha256']!=m['sha256']:raise ValueError('Changed file: '+name)
            payload[name]=info
            continue
        data=p.read_bytes()
        if SECRET.search(data):raise ValueError('Potential credential in '+name)
        if name!='MANIFEST.json':
            m=manifest[name]
            if len(data)!=m['bytes'] or sha(data)!=m['sha256']:raise ValueError('Changed file: '+name)
        payload[name]=data
    if kind=='atlas':
        d=json.loads((run/'data/results.json').read_text())
        if d['modelHash']!=large_data.inspect_file(run/'model.js')['sha256']:raise ValueError('Model/results mismatch')
        if not d['rows'] or not all(x.get('valid') for x in d['rows']):raise ValueError('Invalid atlas run')
    elif kind=='molecular':
        d=json.loads((run/'results.json').read_text())
        if not d.get('all_validated') or d.get('timed_out'):raise ValueError('Unvalidated molecular run')
    elif kind=='archive':
        if finished.get('kind')!='archive' or not finished.get('provenance'):
            raise ValueError('Archive requires explicit provenance; it is not a scientific run')
    else:raise ValueError('Unknown run kind')
    return payload,sha(manifest_bytes)

class Publisher:
    def __init__(self,remote=None,test=False):
        if remote is not None and not test:raise ValueError('Production destination is fixed')
        self.remote=remote or 'https://github.com/'+REPOSITORY+'.git'
        self.test=test
        self.temp=tempfile.TemporaryDirectory(prefix='scienceclaw-publish-')
        self.work=Path(self.temp.name)
        self.git=shutil.which('git')
        gh=shutil.which('gh')
        if not self.git or (not test and not gh):raise RuntimeError('Existing git and gh are required; nothing is installed')
        self.env={k:os.environ[k] for k in ['PATH','HOME','TMPDIR','LANG'] if k in os.environ}
        self.env.update({'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,
                         'GIT_TERMINAL_PROMPT':'0','GH_PROMPT_DISABLED':'1',
                         'GIT_AUTHOR_NAME':'ScienceClaw run archiver',
                         'GIT_AUTHOR_EMAIL':'721455+InquilineKea@users.noreply.github.com',
                         'GIT_COMMITTER_NAME':'ScienceClaw run archiver',
                         'GIT_COMMITTER_EMAIL':'721455+InquilineKea@users.noreply.github.com'})
        self.config=['-c','core.hooksPath='+os.devnull,'-c','commit.gpgsign=false',
                     '-c','http.version=HTTP/1.1','-c','http.postBuffer=268435456',
                     '-c','credential.helper=']
        if not test:
            import shlex
            self.config+=['-c','credential.helper=!'+shlex.quote(gh)+' auth git-credential']
        self.command(['init','--bare','--quiet'])
        self.command(['remote','add','origin',str(self.remote)])
        self.command(['config','remote.origin.promisor','true'])
        self.command(['config','remote.origin.partialclonefilter','blob:none'])
        self.env['GIT_INDEX_FILE']=str(self.work/'publish-index')

    def close(self):self.temp.cleanup()

    def command(self,args,data=None,check=True):
        r=subprocess.run([self.git,*self.config,*args],cwd=self.work,env=self.env,
                         input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if check and r.returncode:
            # Do not echo credential-helper stderr or user environment values.
            raise RuntimeError('Git '+args[0]+' failed (exit '+str(r.returncode)+'); check connection/authentication and retry')
        return r

    def fetch(self):
        self.command(['fetch','--quiet','--depth=1','--filter=blob:none','origin','refs/heads/main'])
        return self.command(['rev-parse','FETCH_HEAD']).stdout.decode().strip()

    def tree(self,head,prefix):
        rows=self.command(['ls-tree','-r','-z',head,'--',prefix]).stdout.split(b'\0')
        return {row.split(b'\t',1)[1].decode():row.split(b'\t',1)[0].decode().split()[2]
                for row in rows if row}

    def publish(self,payload,prefix):
        expected={prefix+'/'+name:gitsha(data) for name,data in payload.items()}
        for attempt in range(5):
            head=self.fetch();existing=self.tree(head,prefix)
            if existing:
                if existing==expected:return {'status':'already_uploaded','commit':head,'files':len(expected)}
                raise ValueError('Remote run ID exists with different files; nothing was overwritten')
            # Explicitly reject a file at an ancestor of the run directory.
            for ancestor in PurePosixPath(prefix).parents:
                if str(ancestor)=='.':continue
                row=self.command(['ls-tree',head,'--',str(ancestor)]).stdout
                if row and b' blob ' in row:raise ValueError('Remote destination has a file/dir conflict')
            self.command(['read-tree',head])
            for name,data in sorted(payload.items()):
                oid=self.command(['hash-object','-w','--stdin'],data).stdout.decode().strip()
                self.command(['update-index','--add','--cacheinfo','100644,'+oid+','+prefix+'/'+name])
            tree=self.command(['write-tree']).stdout.decode().strip()
            commit=self.command(['commit-tree',tree,'-p',head],('Archive completed run '+prefix+'\n').encode()).stdout.decode().strip()
            pushed=self.command(['push','--quiet','origin',commit+':refs/heads/main'],check=False)
            if pushed.returncode:
                # A concurrent push may have won. Rebase this addition onto the
                # latest tree; never force-push and never replace another run.
                time.sleep(min(attempt+1,3));continue
            remote=self.fetch()
            if self.tree(remote,prefix)!=expected:raise RuntimeError('Remote content verification failed')
            return {'status':'uploaded','commit':commit,'files':len(expected)}
        raise RuntimeError('Upload deferred after concurrent updates or a transport failure; local files are intact')

def receipt_dir(run):
    p=Path(run).parent.parent/'.upload-receipts';p.mkdir(exist_ok=True);return p

def upload(run,kind,test_remote=None):
    run=Path(run).absolute();payload,fingerprint=validated_files(run,kind)
    prefix=PREFIXES[kind]+'/'+run.name
    publisher=Publisher(test_remote,test=test_remote is not None)
    try:
        large={n:b for n,b in payload.items() if isinstance(b,dict)}
        if large:
            if test_remote is not None:raise ValueError('Use a fake Releases transport for offline large-data tests')
            small={n:b for n,b in payload.items() if isinstance(b,bytes)}
            payload,finish=large_data.prepare(publisher,small,large,kind,run.name,fingerprint,prefix)
        result=publisher.publish(payload,prefix)
        if large:result.update(finish(result['commit']))
    finally:publisher.close()
    result.update({'runId':run.name,'kind':kind,'repository':REPOSITORY,'path':prefix,
                   'manifestSHA256':fingerprint,'verifiedAt':now(),
                   'url':'https://github.com/'+REPOSITORY+'/tree/'+result['commit']+'/'+prefix})
    write_new(receipt_dir(run)/(run.name+'-'+uuid.uuid4().hex+'.json'),result)
    return result

def seal_molecular(run):
    run=Path(run)
    if (run/'MANIFEST.json').exists():return validated_files(run,'molecular')
    d=json.loads((run/'results.json').read_text())
    if not d.get('all_validated') or d.get('timed_out'):raise ValueError('Molecular result did not validate')
    write_new(run/'FINISHED.json',{'status':'complete','finishedAt':now(),'kind':'molecular'})
    manifest={str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':large_data.inspect_file(p)['sha256']}
              for p in sorted(run.rglob('*')) if p.is_file()}
    write_new(run/'MANIFEST.json',manifest)

def scan(root,kind):
    root=Path(root);results=[]
    for run in sorted((root/'runs').glob('*')):
        if not run.is_dir() or not (run/'FINISHED.json').exists() or not (run/'MANIFEST.json').exists():continue
        try:
            _,fp=validated_files(run,kind)
            receipts=root/'.upload-receipts'
            done=False
            for p in receipts.glob(run.name+'-*.json'):
                r=json.loads(p.read_text())
                if r.get('manifestSHA256')==fp and r.get('status') in {'uploaded','already_uploaded'}:done=True;break
            if not done:results.append(upload(run,kind))
        except Exception as exc:results.append({'runId':run.name,'status':'pending','error':str(exc)})
    return results

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run',nargs='?');ap.add_argument('--kind',choices=PREFIXES,default='atlas')
    ap.add_argument('--scan',metavar='ROOT');ap.add_argument('--seal-molecular',action='store_true')
    args=ap.parse_args()
    try:
        if args.scan:result=scan(args.scan,args.kind)
        elif args.run:
            if args.seal_molecular:seal_molecular(args.run)
            result=upload(args.run,args.kind)
        else:ap.error('Provide a completed run or --scan ROOT')
        print(json.dumps(result,indent=2))
        return 3 if isinstance(result,list) and any(x['status']=='pending' for x in result) else 0
    except Exception as exc:
        if args.run:
            write_new(receipt_dir(args.run)/(Path(args.run).name+'-'+uuid.uuid4().hex+'.json'),
                      {'status':'pending','checkedAt':now(),'error':str(exc)})
        print('Upload pending: '+str(exc),file=sys.stderr);return 3

if __name__=='__main__':sys.exit(main())
