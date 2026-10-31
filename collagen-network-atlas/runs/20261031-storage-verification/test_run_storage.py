"""Meaningful storage checks; no model execution, downloads or third-party imports."""
from pathlib import Path
import concurrent.futures
import importlib.util
import json
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('storage',Path(__file__).with_name('run-atlas.py'))
storage=importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage)


class StorageTests(unittest.TestCase):
    def test_collision_preserves_original(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'model.js').write_text('original source')
            run=storage.reserve(root,'same');(run/'data/raw.json').write_text('precious data')
            with self.assertRaises(FileExistsError):storage.reserve(root,'same')
            self.assertEqual((run/'data/raw.json').read_text(),'precious data')
            with self.assertRaises(FileExistsError):storage.write_new(run/'data/raw.json',{})

    def test_concurrent_unique_runs_and_frozen_source(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'model.js').write_text('version 1')
            (root/'.env').write_text('do not copy');(root/'data').mkdir()
            (root/'data/prior.json').write_text('old result')
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                runs=list(pool.map(lambda _:storage.reserve(root),range(12)))
            self.assertEqual(len(set(runs)),12)
            (root/'model.js').write_text('version 2')
            for r in runs:
                self.assertEqual((r/'model.js').read_text(),'version 1')
                self.assertFalse((r/'.env').exists());self.assertFalse((r/'data/prior.json').exists())
                metadata=json.loads((r/'RUN_CONTEXT.json').read_text())
                self.assertEqual(metadata['sourceFiles']['model.js']['sha256'],storage.digest(r/'model.js'))

    def test_reject_traversal_and_symlinks(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            with self.assertRaises(ValueError):storage.reserve(root,'../outside')
            (root/'runs').symlink_to(root,target_is_directory=True)
            with self.assertRaises(ValueError):storage.reserve(root,'new')

    def test_failed_stage_log_cannot_be_replaced(self):
        import sys
        with tempfile.TemporaryDirectory() as t:
            run=storage.reserve(Path(t),'failure')
            with self.assertRaises(RuntimeError):
                storage.execute_stage(run,[sys.executable,'-I','-c','print("failure evidence");raise SystemExit(3)'],'failed.log',{})
            before=(run/'logs/failed.log').read_bytes()
            with self.assertRaises(FileExistsError):
                storage.execute_stage(run,[sys.executable,'-I','-c','print("replacement")'],'failed.log',{})
            self.assertEqual(before,(run/'logs/failed.log').read_bytes())


if __name__=='__main__':unittest.main()
