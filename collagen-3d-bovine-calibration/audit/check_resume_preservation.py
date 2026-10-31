"""Independent stdlib check: resumed outputs preserve every prior final JSON byte.

Run after the parent verifies and safely extracts the resumed result archive:
  python3 campaign1-audit/check_resume_preservation.py remote-final
No numerical solver or third-party dependency is imported.
"""
import argparse,ast,collections,hashlib,json,sys,zipfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
RESUME_SHA='f4c8573194af1a113f4054ac525dd3394478c45ceca4e50c6951219619614929'
PRIOR_SHA='1e5608e44409fa08cc3cedf183e27eca84167c827cf4f2e5efa5b877db7b7bf4'
def sha(b):return hashlib.sha256(b).hexdigest()
def function_records(path):
 text=path.read_text();tree=ast.parse(text);out={}
 for name in ('Model','simulate','checks'):
  node=next(n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name)
  out[name]={'source_sha256':sha(ast.get_source_segment(text,node).encode()),'ast_sha256':sha(ast.dump(node,include_attributes=False).encode())}
 return out

def main():
 parser=argparse.ArgumentParser();parser.add_argument('final_root',type=Path);parser.add_argument('--out',type=Path,default=P/'campaign1-audit/resume-preservation-readback.json');args=parser.parse_args();root=args.final_root
 if root.name=='results':root=root.parent
 if not root.is_absolute() and not root.exists():root=P/root
 reference=P/'bovine3d-resume-state.zip';assert sha(reference.read_bytes())==RESUME_SHA
 records=[];reference_status=collections.Counter();errors=[]
 with zipfile.ZipFile(reference) as z:
  provenance=json.loads(z.read('resume-provenance.json'));assert provenance['prior_archive_sha256']==PRIOR_SHA
  for name,expected in provenance['files'].items():
   original=z.read(name);assert sha(original)==expected
   final=root/name;exists=final.is_file();data=final.read_bytes() if exists else None
   is_result=name.startswith('results/')
   if is_result:reference_status[json.loads(original)['status']]+=1
   prior_local=P/'remote-completed'/name
   item={'file':name,'prior_sha256':expected,'prior_bytes':len(original),'final_exists':exists,'final_sha256':sha(data) if data is not None else None,'byte_identical':data==original,'prior_local_byte_identical':prior_local.is_file() and prior_local.read_bytes()==original,'kind':'final_result' if is_result else 'commission'};records.append(item)
   if not item['byte_identical']:errors.append({'file':name,'kind':'missing' if not exists else 'changed'})
   if not item['prior_local_byte_identical']:errors.append({'file':name,'kind':'prior_local_mismatch'})
 expected_results=sum(r['kind']=='final_result' for r in records)
 assert expected_results==54
 old_functions=function_records(P/'remote-completed/cpu-solver.py');new_source=root/'cpu-solver.py';identities={}
 if new_source.exists():
  new_functions=function_records(new_source)
  for name in old_functions:identities[name]={'prior':old_functions[name],'final':new_functions[name],'source_identical':old_functions[name]['source_sha256']==new_functions[name]['source_sha256'],'ast_identical':old_functions[name]['ast_sha256']==new_functions[name]['ast_sha256']}
  if not all(x['source_identical'] and x['ast_identical'] for x in identities.values()):errors.append({'kind':'mathematical_function_changed'})
 else:errors.append({'kind':'missing_returned_source'})
 all_final=[f for f in (root/'results').glob('*.json') if not f.name.endswith(('.partial.json','.error.json'))]
 statuses=collections.Counter();parse_errors=[]
 for f in all_final:
  try:statuses[json.loads(f.read_text()).get('status','missing_status')]+=1
  except (ValueError,OSError) as exc:parse_errors.append({'file':f.name,'error':str(exc)})
 output={'scope':'Bit-preservation and function identity; scientific qualification is a separate analysis','reference_resume_zip_sha256':RESUME_SHA,'prior_archive_sha256':PRIOR_SHA,'final_root':str(root),'preserved_result_records_expected':expected_results,'preserved_result_records_byte_identical':sum(r['kind']=='final_result' and r['byte_identical'] for r in records),'preserved_commission_records_expected':len(records)-expected_results,'preserved_commission_records_byte_identical':sum(r['kind']=='commission' and r['byte_identical'] for r in records),'prior_final_status_counts':dict(reference_status),'total_final_json_files':len(all_final),'new_final_files_beyond_prior':len(all_final)-expected_results,'final_status_counts':dict(statuses),'parse_errors':parse_errors,'mathematical_function_identity':identities,'errors':errors,'all_prior_bytes_and_functions_preserved':not errors,'files':records}
 args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(output,indent=2));print(json.dumps({k:v for k,v in output.items() if k not in ['files','mathematical_function_identity']},indent=2));return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
