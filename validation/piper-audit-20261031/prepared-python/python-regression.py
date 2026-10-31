"""Offline before/after regression tests. Run only after approval, inside the reviewed sandbox."""
import importlib.util,sys,unittest,dataclasses
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
old=load('baseline_cell',ROOT/'baseline_cell.py');new=load('patched_cell',ROOT/'patched_cell.py')
oldh=load('baseline_physio',ROOT/'baseline_physio.py');newh=load('patched_physio',ROOT/'patched_physio.py')
def curve(mod):
 return mod.MatrixCurve(np.array([0.,.5]),np.array([[1000.,2000.]]),np.array([.4]))
class Regression(unittest.TestCase):
 def test_original_shared_defaults_reproduced(self):
  a,b=old.CellModel(curve(old)),old.CellModel(curve(old))
  self.assertIs(a.clutch,b.clutch);self.assertIs(a.cp,b.cp)
 def test_patched_instance_isolation(self):
  a,b=new.CellModel(curve(new)),new.CellModel(curve(new))
  original=(b.clutch.n_m,b.cp.beta);a.clutch.n_m+=17;a.cp.beta+=3
  self.assertEqual((b.clutch.n_m,b.cp.beta),original)
 def test_default_values_preserved(self):
  self.assertEqual(dataclasses.asdict(old.ClutchParams()),dataclasses.asdict(new.ClutchParams()))
  self.assertEqual(dataclasses.asdict(old.CellParams()),dataclasses.asdict(new.CellParams()))
  self.assertEqual(dataclasses.asdict(oldh.LVParams()),dataclasses.asdict(newh.LVParams()))
 def test_explicit_objects_preserved(self):
  clutch,cp=new.ClutchParams(T=.04),new.CellParams()
  model=new.CellModel(curve(new),clutch=clutch,cp=cp)
  self.assertIs(model.clutch,clutch);self.assertIs(model.cp,cp)
 def test_heart_before_after(self):
  for ratio in [.5,1.,2.,4.]:
   for pwv in [1.,1.5,2.]:
    self.assertEqual(oldh.heart(ratio,10.,10.,pwv),newh.heart(ratio,10.,10.,pwv))
 def test_short_motor_clutch_before_after(self):
  for seed in [7,29]:
   a=old.motor_clutch(curve(old),np.array([400.]),old.ClutchParams(T=.04),seed=seed)
   b=new.motor_clutch(curve(new),np.array([400.]),new.ClutchParams(T=.04),seed=seed)
   self.assertEqual(set(a),set(b))
   for k in a:np.testing.assert_array_equal(a[k],b[k])
 def test_default_motor_clutch_before_after(self):
  a=old.motor_clutch(curve(old),np.array([400.]),seed=7)
  b=new.motor_clutch(curve(new),np.array([400.]),seed=7)
  for k in a:np.testing.assert_array_equal(a[k],b[k])
if __name__=='__main__':unittest.main(verbosity=2)

