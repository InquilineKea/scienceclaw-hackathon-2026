"""Offline tests with disposable local Git repositories; no account credentials."""
from pathlib import Path
import importlib.util,sys,tempfile,subprocess,json,unittest
spec=importlib.util.spec_from_file_location('uploader',Path(__file__).with_name('upload-run.py'))
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

class UploadTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.remote=self.root/'remote.git';self.seed=self.root/'seed';self.seed.mkdir()
        def git(*args,cwd=self.seed):
            return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=cwd,stderr=subprocess.DEVNULL)
        git('init','--bare',str(self.remote));git('init','-b','main')
        (self.seed/'README.md').write_text('existing remote content\n')
        git('add','.');git('-c','user.name=Offline test','-c','user.email=test@example.invalid','-c','commit.gpgsign=false','commit','-m','base')
        git('remote','add','origin',str(self.remote));git('push','origin','main')
        self.pub=u.Publisher(self.remote,test=True)
    def tearDown(self):self.pub.close();self.tmp.cleanup()
    def run_fixture(self):
        p=self.root/'runs/example';(p/'data').mkdir(parents=True)
        (p/'model.js').write_text('fixture only; not a simulation')
        u.write_new(p/'FINISHED.json',{'status':'complete'})
        u.write_new(p/'data/results.json',{'modelHash':u.sha((p/'model.js').read_bytes()),'rows':[{'valid':True}]})
        self.manifest(p);return p
    def manifest(self,p):
        d={str(x.relative_to(p)):{'bytes':x.stat().st_size,'sha256':u.sha(x.read_bytes())}
           for x in p.rglob('*') if x.is_file() and x.name!='MANIFEST.json'}
        (p/'MANIFEST.json').write_text(json.dumps(d))
    def test_add_idempotent_and_collision(self):
        data={'MANIFEST.json':b'{}','data.csv':b'1,2\n'};prefix='collagen-network-atlas/runs/example'
        first=self.pub.publish(data,prefix);self.assertEqual(first['status'],'uploaded')
        second=self.pub.publish(data,prefix);self.assertEqual(second['status'],'already_uploaded')
        self.assertEqual(first['commit'],second['commit'])
        with self.assertRaises(ValueError):self.pub.publish({'data.csv':b'changed'},prefix)
        self.assertEqual(self.pub.tree(self.pub.fetch(),prefix),{prefix+'/'+n:u.gitsha(b) for n,b in data.items()})
        self.assertEqual(self.pub.command(['show','FETCH_HEAD:README.md']).stdout,b'existing remote content\n')
    def test_concurrent_commit_is_preserved(self):
        other=u.Publisher(self.remote,test=True);original=self.pub.command;triggered=[]
        def race(args,*a,**kw):
            if args[0]=='push' and not triggered:
                triggered.append(True);other.publish({'other.txt':b'concurrent data'},'runs/other')
            return original(args,*a,**kw)
        self.pub.command=race
        try:self.pub.publish({'ours.txt':b'our data'},'runs/ours')
        finally:other.close()
        head=self.pub.fetch();self.assertTrue(self.pub.tree(head,'runs/other'));self.assertTrue(self.pub.tree(head,'runs/ours'))
    def test_manifest_completion_and_extra_file_checks(self):
        p=self.run_fixture();u.validated_files(p,'atlas')
        (p/'extra.txt').write_text('unlisted')
        with self.assertRaises(ValueError):u.validated_files(p,'atlas')
        (p/'extra.txt').unlink();(p/'model.js').write_text('modified')
        with self.assertRaises(ValueError):u.validated_files(p,'atlas')
        (p/'FAILED.json').write_text('{}')
        with self.assertRaises(ValueError):u.validated_files(p,'atlas')
    def test_secret_path_and_symlink_checks(self):
        p=self.run_fixture();(p/'.env').write_text('not for publication');self.manifest(p)
        with self.assertRaises(ValueError):u.validated_files(p,'atlas')
        (p/'.env').unlink();(p/'leak.txt').write_text('ghp_'+'a'*36);self.manifest(p)
        with self.assertRaises(ValueError):u.validated_files(p,'atlas')
        (p/'leak.txt').unlink();(p/'link').symlink_to(self.seed/'README.md');self.manifest(p)
        with self.assertRaises(ValueError):u.validated_files(p,'atlas')

if __name__=='__main__':unittest.main()
