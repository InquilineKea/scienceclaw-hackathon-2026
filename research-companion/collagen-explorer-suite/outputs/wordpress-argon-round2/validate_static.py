from pathlib import Path
import re,json,hashlib,subprocess,difflib
from html.parser import HTMLParser
R=Path(__file__).resolve().parent;A=R/'snapshot';B=R/'candidate'
changed=[p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file() and (not (A/p.relative_to(B)).exists() or p.read_bytes()!=(A/p.relative_to(B)).read_bytes())]
class H(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.refs=[];self.paras=[];self.p=None
 def handle_starttag(self,t,attrs):
  d=dict(attrs)
  if d.get('id'):self.ids.append(d['id'])
  if t=='script' and d.get('src'):self.refs.append(d['src'])
  if t=='link' and d.get('rel')=='stylesheet':self.refs.append(d['href'])
  if t=='p':self.p=[]
 def handle_data(self,x):
  if self.p is not None:self.p.append(x)
 def handle_endtag(self,t):
  if t=='p' and self.p is not None:self.paras.append(' '.join(''.join(self.p).split()));self.p=None
checks=[];syntax=[];patch=[]
for rel in changed:
 p=B/rel;old=(A/rel).read_text() if (A/rel).exists() else '';new=p.read_text()
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
 if p.suffix=='.js':
  x=subprocess.run(['/opt/homebrew/bin/node','--check',str(p)],capture_output=True,text=True);syntax.append({'path':rel,'returncode':x.returncode,'stderr':x.stderr});assert x.returncode==0
 if p.suffix=='.html':
  a=H();a.feed(old);b=H();b.feed(new)
  c={'path':rel,'original_ids_retained':set(a.ids)<=set(b.ids),'duplicate_ids':sorted({x for x in b.ids if b.ids.count(x)>1}),'missing_script_or_css':[x for x in b.refs if not x.startswith(('https:','http:','data:')) and not (p.parent/x.split('?')[0]).exists()],'removed_original_paragraphs':[x for x in a.paras if x not in b.paras]};checks.append(c)
  assert c['original_ids_retained'] and not any(c[x] for x in ['duplicate_ids','missing_script_or_css','removed_original_paragraphs']),c
scientific=[p for p in (A/'docs').rglob('*') if p.is_file() and (p.suffix=='.json' or p.parent.name=='data')]
assert all(p.read_bytes()==(B/p.relative_to(A)).read_bytes() for p in scientific)
a=(A/'docs/evidence-atlas/network-scenes.js').read_text();b=(B/'docs/evidence-atlas/network-scenes.js').read_text();worker=lambda s:re.search(r'const workerSource=(.*?);\n',s).group(1)
assert worker(a)==worker(b)
r={'changed_files':changed,'syntax_checks':syntax,'scientific_data_files':len(scientific),'scientific_data_unchanged':True,'bundled_worker_source_unchanged':True,'html_checks':checks,'generated_code_executed':(R/'browser-validation.json').exists()}
(R/'static-validation.json').write_text(json.dumps(r,indent=2));(R/'visualization.patch').write_text(''.join(patch));print('PASS',len(changed),'files;',len(syntax),'syntax checks;',len(scientific),'original data files unchanged')
