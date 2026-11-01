from pathlib import Path
import json,hashlib,math,collections,statistics
R=Path(__file__).resolve().parent;D=R/'studies';public=R/'public-studies';public.mkdir(exist_ok=True);sources=[];inventory=[]
def sanitize(x):
 if isinstance(x,list):return [sanitize(y) for y in x]
 if isinstance(x,dict):
  d={k:sanitize(v) for k,v in x.items() if k!='local_original'}
  if 'local_original' in x:
   sources.append(x);p=x['local_original'];d['artifact']=p.split('/outputs/',1)[-1] if '/outputs/' in p else 'oxidative-tensegrity/'+p.split('/oxidative-tensegrity/',1)[-1] if '/oxidative-tensegrity/' in p else Path(p).name
  return d
 return x
for p in sorted(D.glob('*.json')):
 d=json.loads(p.read_text())
 for t in d['tables']:
  for row in t['rows']:
   if isinstance(row,dict):
    for k,v in row.items():
     if isinstance(v,str) and v.lower() in ['true','false']:row[k]=v.lower()=='true'
 p.write_text(json.dumps(d,allow_nan=False,separators=(',',':')))
 # Exact default paths and nonempty default filters.
 view=d['defaultView'];t=next(t for t in d['tables'] if t['id']==view['table']);assert all(k in t['columns'] for k in [''+view['x'],view['y'],view['color']]),p
 subset=[r for r in t['rows'] if all(r.get(k)==v for k,v in view['filters'].items())];assert subset,p
 for g in [d.get('geometry')]+d.get('spatialExamples',[]):
  if not g:continue
  n=len(g['nodes']);assert all(len(v)==3 and all(math.isfinite(a) for a in v) for v in g['nodes'])
  assert all(len(e)==2 and all(isinstance(a,int) and 0<=a<n for a in e) for e in g['edges'])
  if 'displacements' in g:assert len(g['displacements'])==n,p
  for f in g.get('frames',[]):assert len(f.get('nodes',f.get('xyz',[])))==n,p
 q=public/p.name;q.write_text(json.dumps(sanitize(d),allow_nan=False,separators=(',',':')))
 inventory.append({'id':d['id'],'title':d['title'],'file':p.name,'publicFile':str(q),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'tables':[{'id':t['id'],'rows':len(t['rows']),'columns':t['columns']} for t in d['tables']],'geometryNodes':len(d['geometry']['nodes']) if d.get('geometry') else 0,'geometryEdges':len(d['geometry']['edges']) if d.get('geometry') else 0,'spatialExamples':len(d.get('spatialExamples',[])),'defaultView':view,'defaultFilteredRows':len(subset),'gateSemantics':d['gateSemantics'],'sourceURLs':d['sourceURLs'],'limitations':d['limitations']})
(R/'source-provenance-private.json').write_text(json.dumps(sources,indent=2));(R/'inventory.json').write_text(json.dumps({'studyCount':len(inventory),'allDefaultColumnsExist':True,'allDefaultFiltersNonempty':True,'geometryIndicesValid':True,'displacementCountsMatch':True,'noImportedCodeExecuted':True,'noNewFittingOrSimulations':True,'studies':inventory},indent=2));print('Final inventory',len(inventory),'studies',sum(x['bytes'] for x in inventory),'public JSON bytes')
