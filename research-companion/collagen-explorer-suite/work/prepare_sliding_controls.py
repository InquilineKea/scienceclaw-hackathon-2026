"""Original stdlib-only residue reconstruction from previously reviewed data adapters."""
import ast, collections, copy, hashlib, itertools, json, math
from pathlib import Path
BASE=Path('/path/to/Codex/2026-10-31/referenced-chatgpt-conversation-this-is-an-2/outputs/collagen-gag-pipeline')
CAND=Path('/path/to/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/work/prepare_glucosepane_model.py')
OUT=Path('outputs/hydrated-sliding-study')
ns=dict(collections=collections,copy=copy,itertools=itertools,json=json,math=math,Path=Path,pathlib=__import__('pathlib'),re=__import__('re'))
source=(BASE/'src/target_preparation.py').read_text();tree=ast.parse(source)
names={'add','sub','mul','dot','cross','norm','unit','perp','place','canonical','Molecule','write_pdb'}
nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'reviewed_original_builder_subset','exec'),ns)
tree=ast.parse(CAND.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in {'read_rtp','AmberParameters'}]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'reviewed_original_parameter_parser','exec'),ns)
p=ns['AmberParameters'](BASE/'inputs/parameters/colbuilder/amber99sb-star-ildnp.ff');Molecule=ns['Molecule']
summary=[]
for kind in ('PYD','DPD'):
 d=json.loads((OUT/'inputs'/kind/'prepared.json').read_text());m=Molecule(p,kind+'_LYS_CONTROL');modified=[]
 for ri,r in enumerate(d['residues']):
  coords={a['name']:a['xyz'] for a in d['atoms'] if a['resindex']==ri}
  name=r['name']
  if name in ('LYX','LY2','LY3','LXX','LX2','LX3'):
   modified.append({'resindex':ri,'source_residue':name,'restored_residue':'LYS','chain':r['chain'],'id':r['id']})
   name='LYS';coords={k:v for k,v in coords.items() if k in ('N','H','CA','HA','C','O','CB','HB1','HB2')}
   # Missing distal side-chain atoms are rebuilt with declared trans Z-matrix
   # geometry. These are starting coordinates, subsequently minimized remotely.
   history=['N','CA','CB','CG','CD','CE','NZ']
   other=[(a['xyz'],a['element']) for a in d['atoms'] if a['resindex']!=ri and (a['resname'] not in ('LYX','LY2','LY3','LXX','LX2','LX3') or a['name'] in ('N','H','CA','HA','C','O','CB','HB1','HB2'))]
   other += [(a['xyz'],a['element']) for a in m.atoms if a['xyz'] is not None and a['resname']=='LYS']
   best=None
   for torsions in itertools.product((-60.,60.,180.),repeat=4):
    trial=dict(coords)
    for j,torsion in zip(range(3,len(history)),torsions):
     a=history[j];length=1.47 if a=='NZ' else 1.53
     trial[a]=ns['place'](trial[history[j-1]],trial[history[j-2]],trial[history[j-3]],length,111.,torsion)
    coupon=Molecule(p,'rotamer');coupon.residue('LYS',trial,r['chain'],r['id']);coupon.hydrogens();adj=coupon.adjacency();skip=set()
    for ia in range(len(coupon.atoms)):
     seen={ia};front={ia}
     for _ in range(3):front=set().union(*(adj[k] for k in front))-seen;seen|=front
     skip|={(min(ia,j),max(ia,j)) for j in seen}
    def clash(a,b):
     threshold=1.2 if a['element']==b[1]=='H' else 1.8 if 'H' in (a['element'],b[1]) else 2.7
     return max(0.,threshold-math.dist(a['xyz'],b[0]))**2
    side=[a for a in coupon.atoms if a['name'] not in ('N','H','CA','HA','C','O','CB','HB1','HB2')]
    penalty=sum(clash(a,b) for a in side for b in other)
    penalty+=sum(clash(a,(b['xyz'],b['element'])) for i,a in enumerate(coupon.atoms) for j,b in enumerate(coupon.atoms) if j>i and (i,j) not in skip)
    if best is None or penalty<best[0]:best=(penalty,trial)
   coords=best[1]
  m.residue(name,coords,r['chain'],r['id'],r.get('source'))
 for chain in dict.fromkeys(r['chain'] for r in m.res):m.peptide([i for i,r in enumerate(m.res) if r['chain']==chain])
 m.hydrogens();folder=OUT/'inputs'/m.name;folder.mkdir(exist_ok=True);audit=m.save(folder)
 assert audit['coverage_pass'],audit['missing_terms']
 assert not audit['junctions']
 # Six individually capped molecules, with no interchain covalent bonds.
 assert all(m.atoms[i]['chain']==m.atoms[j]['chain'] for i,j in m.bonds)
 record={'model':m.name,'atoms':len(m.atoms),'charge_e':audit['net_charge_e'],'rebuilt_sites':modified,
 'source_sha256':hashlib.sha256((OUT/'inputs'/kind/'prepared.json').read_bytes()).hexdigest(),
 'control_scope':'unlinked ordinary-lysine reconstruction; hydroxylation and charge are changed as well as crosslink connectivity',
 'chemistry_matched_HYL_precursor_control':False,'dynamic_validation':False,
 'limitation':'Source force field has no free HYL template. Do not call this a hydroxylation-matched precursor or interpret a native linked-minus-control difference as connectivity alone.'}
 (folder/'CONTROL_PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n');summary.append(record)
(OUT/'control-preparation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
