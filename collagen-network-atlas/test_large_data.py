"""Offline regression tests: no network, credentials, packages, or scientific jobs."""
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def module(name, filename):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
u=module('u','upload-run.py');l=u.large_data;r=module('r','restore-large-data.py')
base=module('base','test_upload_run.py')

class FakeReleases:
    """Stateful external service double; rest of the publication is real local Git."""
    def __init__(self):self.releases={};self.blobs={};self.put_count=0;self.fail_publish=False
    def ensure(self,tag,identity,head,prefix):
        return self.releases.setdefault(tag,{'tag_name':tag,'draft':True})
    def put(self,release,name,file,size,checksum):
        return self.put_bytes(release,name,Path(file).read_bytes(),size,checksum)
    def put_bytes(self,release,name,data,size=None,checksum=None):
        key=(release['tag_name'],name)
        if size is not None:assert len(data)==size and hashlib.sha256(data).hexdigest()==checksum
        if key in self.blobs:assert self.blobs[key]==data
        else:
            assert release['draft'];self.blobs[key]=data;self.put_count+=1
        return {'name':name,'browser_download_url':'https://github.com/'+l.REPOSITORY+'/releases/download/untagged-temporary/'+name}
    def publish(self,release,commit):
        if self.fail_publish:raise RuntimeError('simulated publication interruption')
        release['draft']=False
        return 'https://github.com/'+l.REPOSITORY+'/releases/tag/'+release['tag_name']
    def open(self,req):
        tag,name=req.full_url.split('/')[-2:];return io.BytesIO(self.blobs[(tag,name)])

class LargeDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
    def tearDown(self):self.tmp.cleanup()
    def index(self):
        data=b'0123456789abcdefghijk';p=self.root/'raw.bin';p.write_bytes(data)
        info=l.inspect_file(p,part_bytes=7)
        parts=[];blobs={};offset=0
        for n,part in enumerate(info['parts']):
            url='https://github.com/'+l.REPOSITORY+'/releases/download/test/p'+str(n)
            parts.append({**part,'url':url});blobs[url]=data[offset:offset+part['bytes']];offset+=part['bytes']
        return {'schemaVersion':1,'repository':l.REPOSITORY,'files':{'nested/raw.bin':{'bytes':len(data),'sha256':info['sha256'],'parts':parts}}},blobs,data
    def test_stream_scan_across_boundaries(self):
        p=self.root/'raw';p.write_bytes(b'x'*11+b'ghp_'+b'a'*36)
        with self.assertRaises(ValueError):l.inspect_file(p,u.SECRET,part_bytes=13)
    def test_multi_part_exact_restore_and_idempotence(self):
        index,blobs,data=self.index();opener=lambda req:io.BytesIO(blobs[req.full_url])
        out=self.root/'recovered';self.assertEqual(r.restore(index,out,opener)[0]['status'],'restored')
        self.assertEqual((out/'nested/raw.bin').read_bytes(),data)
        self.assertEqual(r.restore(index,out,opener)[0]['status'],'already_verified')
    def test_corruption_and_whole_file_digest(self):
        index,blobs,data=self.index();opener=lambda req:io.BytesIO(blobs[req.full_url])
        key=next(iter(blobs));blobs[key]=b'bad'
        with self.assertRaises(ValueError):r.restore(index,self.root/'out',opener)
        self.assertFalse((self.root/'out/nested/raw.bin').exists())
        index,blobs,data=self.index();index['files']['nested/raw.bin']['sha256']='0'*64
        with self.assertRaises(ValueError):r.restore(index,self.root/'out',opener)
    def test_no_overwrite_and_path_escape(self):
        index,blobs,data=self.index();out=self.root/'out';(out/'nested').mkdir(parents=True)
        (out/'nested/raw.bin').write_bytes(b'existing')
        with self.assertRaises(ValueError):r.restore(index,out)
        self.assertEqual((out/'nested/raw.bin').read_bytes(),b'existing')
        item=index['files'].pop('nested/raw.bin');index['files']['../escape']=item
        with self.assertRaises(ValueError):r.restore(index,out)
        index['files']={'nested/raw.bin':item};out2=self.root/'symlink';out2.symlink_to(out,target_is_directory=True)
        with self.assertRaises(ValueError):r.restore(index,out2)
    def test_large_validation_has_exact_manifest_coverage(self):
        run=self.root/'run';run.mkdir();(run/'raw.bin').write_bytes(b'x'*4096)
        u.write_new(run/'FINISHED.json',{'status':'complete','kind':'archive','provenance':'test fixture only'})
        u.write_new(run/'MANIFEST.json',{p.name:{'bytes':p.stat().st_size,'sha256':l.inspect_file(p)['sha256']} for p in run.iterdir()})
        before=u.LIMIT;u.LIMIT=1024
        try:
            payload,fp=u.validated_files(run,'archive');self.assertIsInstance(payload['raw.bin'],dict)
            (run/'raw.bin').write_bytes(b'y'*4096)
            with self.assertRaises(ValueError):u.validated_files(run,'archive')
        finally:u.LIMIT=before

    def test_asset_retry_and_collision_do_not_delete_or_replace(self):
        api=l.Releases.__new__(l.Releases);api.work=self.root;api.cache={};api.base='fake/releases'
        release={'id':1,'draft':True};assets=[{'id':1,'name':'part.bin','state':'starter','size':0}];calls=[]
        def request(endpoint,method='GET',data=None,file=None,missing=False):
            calls.append(method)
            if method=='GET':return assets.copy()
            self.assertEqual(method,'POST');content=Path(file).read_bytes()
            a={'id':2,'name':endpoint.split('name=')[1],'state':'uploaded','size':len(content),
               'digest':'sha256:'+u.sha(content)};assets.append(a);return a
        api.api=request;raw=self.root/'part';raw.write_bytes(b'raw data')
        result=api.put(release,'part.bin',raw,8,u.sha(b'raw data'))
        self.assertTrue(result['name'].startswith('part.bin.retry-'));self.assertEqual(assets[0]['state'],'starter')
        api.put(release,'part.bin',raw,8,u.sha(b'raw data'));self.assertEqual(calls.count('POST'),1)
        with self.assertRaises(ValueError):api.put(release,'part.bin',raw,8,'0'*64)
        self.assertEqual(calls.count('POST'),1);self.assertNotIn('DELETE',calls);self.assertNotIn('PATCH',calls)

    def test_draft_recovery_without_public_tag(self):
        api=l.Releases.__new__(l.Releases);api.base='fake/releases'
        draft={'id':42,'tag_name':'frozen','draft':True}
        api.api=lambda endpoint,**kwargs:None if '/tags/' in endpoint else [draft]
        self.assertEqual(api.get('frozen'),draft)
        self.assertIsNone(api.get('missing'))

class TransactionTests(base.UploadTests):
    def setUp(self):
        super().setUp();self.root=self.root.resolve()
    def test_split_shards_and_resume_after_git_commit(self):
        raw=self.root/'raw.bin';raw.write_bytes(bytes(range(256))*10)
        info=l.inspect_file(raw,part_bytes=1024);small={'MANIFEST.json':b'{"fixture":true}\n','FINISHED.json':b'{}'}
        api=FakeReleases();before=l.PARTS_PER_RELEASE;l.PARTS_PER_RELEASE=2
        try:
            args=(self.pub,small,{'raw.bin':info},'archive','fixture','a'*64,'datasets/fixture')
            payload,finish=l.prepare(*args,releases=api)
            result=self.pub.publish(payload,'datasets/fixture');api.fail_publish=True
            with self.assertRaises(RuntimeError):finish(result['commit'])
            count=api.put_count;api.fail_publish=False
            again,finish=l.prepare(*args,releases=api)
            self.assertEqual(again,payload);self.assertEqual(count,api.put_count)
            result=self.pub.publish(again,'datasets/fixture');self.assertEqual(result['status'],'already_uploaded')
            receipt=finish(result['commit']);self.assertEqual(len(receipt['releases']),2)
            index=json.loads(payload['_release/LARGE_DATASETS.json'])
            r.restore(index,self.root/'restored',api.open)
            self.assertEqual((self.root/'restored/raw.bin').read_bytes(),raw.read_bytes())
            # A third retry of a published release adds nothing.
            l.prepare(*args,releases=api);self.assertEqual(api.put_count,count)
            with self.assertRaises(ValueError):
                l.prepare(self.pub,{**small,'extra':b'collision'},{'raw.bin':info},'archive','fixture','a'*64,'datasets/fixture',releases=api)
        finally:l.PARTS_PER_RELEASE=before

if __name__=='__main__':unittest.main()
