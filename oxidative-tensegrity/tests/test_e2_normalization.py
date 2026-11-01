import ast,copy,json,math,unittest
from pathlib import Path
from oxt.normalization import matched_stiffness_scale,assess_e2,derive_e2_rows,select_e2_target,derive_e2_curve
P=Path(__file__).resolve().parent.parent
class E2Tests(unittest.TestCase):
 def test_valid_ratio_and_boundaries(self):
  for a,b,s in [(2.,6.,3.),(1.,1e4,1e4),(1e4,1.,1e-4),(3.,3.,1.)]:self.assertEqual(matched_stiffness_scale(a,b),s)
 def test_reject_invalid_modulus(self):
  for a in [-1.,0.,1e-15,1e-12,float('nan'),float('inf'),-float('inf'),True,None]:
   with self.subTest(a=a),self.assertRaises(ValueError):matched_stiffness_scale(a,1.)
 def test_reject_bad_target(self):
  for b in [-1.,0.,float('nan'),float('inf'),True]:
   with self.subTest(b=b),self.assertRaises(ValueError):matched_stiffness_scale(1.,b)
 def test_reject_bad_settings(self):
  for kw in [{'relative_floor':-1.},{'relative_floor':float('nan')},{'max_scale':.5},{'max_scale':float('inf')},{'max_scale':True}]:
   with self.subTest(kw=kw),self.assertRaises(ValueError):matched_stiffness_scale(1.,1.,**kw)
 def test_relative_floor_and_scale_limits(self):
  for a,b in [(1e-7,10.),(1e-6,1.),(1e6,1.)]:
   with self.subTest(a=a),self.assertRaises(ValueError):matched_stiffness_scale(a,b)
 def test_no_fallback_or_failed_baseline_selection(self):
  for mods,base in [([],True),([{'G':1}],False),([{'G':1},{'G':-1}],True),([{'G':float('nan')}],True)]:
   with self.assertRaises(ValueError):select_e2_target(mods,base)
  self.assertEqual(select_e2_target([{'G':1},{'G':3},{'G':2}],True),2)
 def test_actual_atlas_wrapper_and_rejected_rows(self):
  tree=ast.parse((P/'run_atlas3d.py').read_text());assign=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SCALED' for t in x.targets));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='e2_rows');ns={'derive_e2_rows':derive_e2_rows};exec(compile(ast.Module(body=[assign,fn],type_ignores=[]),'<exact atlas E2 AST>','exec'),ns)
  rows=[{'G':2.,'peak_stress':4.,'ok':True,'failure_strain':.3},{'G':0.,'peak_stress':2.,'ok':True},{'G':-1.,'ok':True},{'G':1.,'ok':False},{'G':float('nan'),'ok':True}];before=copy.deepcopy(rows);out=ns['e2_rows'](rows,6.)
  self.assertEqual(out[0]['G'],6.);self.assertEqual(out[0]['peak_stress'],12.);self.assertEqual(out[0]['failure_strain'],.3);self.assertEqual(out[0]['scale'],3.);self.assertEqual(out[0]['e2_method'],'posthoc_uniform_stiffness_scaling_not_rerun')
  for r in out[1:]:self.assertFalse(r['ok']);self.assertIsNone(r['scale']);self.assertIsNone(r['G']);self.assertEqual(r['e2_status'],'rejected')
  self.assertEqual(rows[:4],before[:4]);json.dumps(out,allow_nan=False)
 def test_nonfinite_observable_does_not_leak(self):
  for value in [float('nan'),float('inf'),1e308]:
   r=derive_e2_rows([{'G':1.,'ok':True,'peak_stress':value}],100.,['G','peak_stress'])[0];self.assertFalse(r['ok']);self.assertIsNone(r['peak_stress']);json.dumps(r,allow_nan=False)
 def test_public_solver_wrapper_uses_same_guard(self):
  t=ast.parse((P/'oxt/network3d.py').read_text());f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='matched_stiffness_scale');self.assertTrue(any(isinstance(x,ast.ImportFrom) and x.module=='normalization' and x.level==1 for x in ast.walk(f)))
 def test_no_denominator_floor_remaining(self):
  text=(P/'run_atlas3d.py').read_text();self.assertNotIn('g_target / max(',text);self.assertIn('E2_BASELINE_FAILURE.json',text)
 def test_fracture_curve_gate(self):
  r=derive_e2_curve([1.,2.],2.,4.,2.,6.,True);self.assertEqual(r['traction'],[3.,6.]);self.assertEqual(r['T_peak'],6.);self.assertEqual(r['Gc'],12.);self.assertEqual(r['status'],'accepted')
  for traction,peak,gc,initial,target,ok in [([1.],2.,4.,2.,6.,False),([float('nan')],2.,4.,2.,6.,True),([1.],float('inf'),4.,2.,6.,True),([1.],2.,float('nan'),2.,6.,True),([1e308],2.,4.,1.,100.,True),([1.],2.,4.,0.,6.,True),([],2.,4.,2.,6.,True)]:
   r=derive_e2_curve(traction,peak,gc,initial,target,ok);self.assertEqual(r['status'],'rejected');self.assertFalse(any(k in r for k in ['scale','traction','T_peak','Gc']));json.dumps(r,allow_nan=False)
 def test_actual_fracture_export_wiring(self):
  tree=ast.parse((P/'run_atlas3d.py').read_text());calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='derive_e2_curve'];self.assertEqual(len(calls),1);kw={x.arg:ast.unparse(x.value) for x in calls[0].keywords};self.assertEqual(kw['e1_ok'],"row['ok']");self.assertEqual(kw['initial'],"it['moduli']['G']");self.assertEqual(kw['target'],"it.get('e2_target')")
if __name__=='__main__':unittest.main(verbosity=2)
