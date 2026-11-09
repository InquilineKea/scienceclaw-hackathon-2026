"""Own metadata QA; raw scientific table values remain unchanged."""
import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
p=B/'ready/wet-transfer-gates.json';d=json.loads(p.read_text());d['defaultView']={'tableId':'derivative-curves','x':'step','y':'error','color':'switch','filters':{'case':'DITY_CONTROL','replica':0,'direction':'grip_rotation','tight':False},'plotKind':'scatter','xUnits':'radian','yUnits':'kJ/mol/radian','note':'One saved control pose, replica 0, grip-rotation direction and original PME tolerance only; compare switched and hard-cutoff LJ at actual stored angular perturbations. Absolute derivative error is kJ/mol/radian, not stiffness. Other directions require their own coordinate units.'};d['units']['derivative_error']='Direction-dependent: grip_rotation kJ/mol/radian; grip_strain kJ/mol per unit strain; normalized Cartesian directions kJ/mol/nm. Do not pool directions.';p.write_text(json.dumps(d,separators=(',',':')))
p=B/'ready/martini-pulling-virial.json';d=json.loads(p.read_text());d['defaultView']={'tableId':'force-and-pressure-diagnostic','x':'metric','y':'value','color':'metric','filters':{'unit':'bar'},'plotKind':'scatter','xUnits':'category','yUnits':'bar','note':'Categorical metric axis: only three pressure shifts in bar are plotted. Force (kJ/mol/nm), length (nm), virial and energy (kJ/mol) remain separate rows and must not share this y axis.'};p.write_text(json.dumps(d,separators=(',',':')))
p=B/'ready/hne-candidate-precision.json';d=json.loads(p.read_text());d['defaultView']['note']='Categorical runtime axis is intentional: matched-version mixed versus double numerical comparison in kJ/mol, with state as color. This is not a continuous time or performance axis; fresh sampling is separate.';d['defaultView']['xUnits']='category';d['defaultView']['yUnits']='kJ/mol';p.write_text(json.dumps(d,separators=(',',':')))
checks=[]
for p in sorted((B/'ready').glob('*.json')):
 d=json.loads(p.read_text());v=d.get('defaultView')
 if not v:checks.append({'id':d['id'],'status':'no default chart; geometry only'});continue
 t=next(t for t in d.get('tables',[]) if t['id']==v['tableId']);c=t['columns'];assert all(v.get(k) in c for k in ['x','y','color']),(d['id'],v,c)
 filters=v.get('filters',{});assert all(k in c for k in filters)
 rows=[r for r in t['rows'] if all(r[c.index(k)]==value for k,value in filters.items())];assert rows,d['id']
 if v.get('plotKind')!='matrix':assert any(isinstance(r[c.index(v['y'])],(int,float)) and not isinstance(r[c.index(v['y'])],bool) for r in rows),d['id']
 checks.append({'id':d['id'],'status':'pass','table':t['id'],'selectedRows':len(rows),'axisColumnsExist':True,'filterColumnsExist':True,'plotKind':v.get('plotKind'),'filters':filters})
(B/'default-view-qa.json').write_text(json.dumps(checks,indent=2))
# Refresh the original inventory's metadata/hash without touching tables.
p=B/'inventory.json';inv=json.loads(p.read_text())
for row in inv:
 f=B/'ready'/(row['id']+'.json');d=json.loads(f.read_text());raw=f.read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),defaultView=d.get('defaultView'))
p.write_text(json.dumps(inv,indent=2))
p=B/'argon-data-schema.json';a=json.loads(p.read_text())
def refresh(v):
 if isinstance(v,dict):
  if v.get('id') in {r['id'] for r in inv} and 'defaultView' in v:v['defaultView']=next(r['defaultView'] for r in inv if r['id']==v['id'])
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(a);p.write_text(json.dumps(a,indent=2))
print(json.dumps(checks,indent=2))
