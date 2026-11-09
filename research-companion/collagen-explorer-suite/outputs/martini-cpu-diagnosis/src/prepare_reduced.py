"""Original hydrated single-helix diagnostic, not a reproduction of the fibril."""
from pathlib import Path
import re,math,json,shutil,hashlib,itertools
root=Path('outputs/martini-cpu-diagnosis');src=root/'input';out=root/'reduced-input';out.mkdir(exist_ok=False)
for p in src.iterdir():
 if p.suffix in ['.itp','.top']:shutil.copyfile(p,out/p.name)
section='';atoms=[]
for l in (src/'col_9.itp').read_text().splitlines():
 s=l.split(';')[0].strip();m=re.match(r'\[\s*(.*?)\s*\]',s)
 if m:section=m.group(1);continue
 if section=='atoms' and s and not s.startswith('#'):atoms.append(s.split())
n=len(atoms);assert n==1940;offset=20749;lines=(src/'start.gro').read_text().splitlines()[2+offset:2+offset+n];xyz=[[float(l[k:k+8]) for k in [20,28,36]] for l in lines];mins=[min(p[d] for p in xyz) for d in range(3)];maxs=[max(p[d] for p in xyz) for d in range(3)];box=[maxs[d]-mins[d]+3.0 for d in range(3)];xyz=[[p[d]-mins[d]+1.5 for d in range(3)] for p in xyz]
# Explicitly new hydration fixture. Water-grid spacing0.5nm approximates Martini water number density.
# Exclude sites within0.48nm of any solute bead using a spatial cell index.
cells={};cellsize=.5
for p in xyz:cells.setdefault(tuple(int(x/cellsize) for x in p),[]).append(p)
water=[]
for i in range(int(box[0]/.5)):
 for j in range(int(box[1]/.5)):
  for k in range(int(box[2]/.5)):
   p=[(i+.5)*.5,(j+.5)*.5,(k+.5)*.5];key=tuple(int(x/.5) for x in p);neigh=itertools.product(*[range(q-1,q+2) for q in key]);near=False
   for c in neigh:
    if any(sum((a-b)**2 for a,b in zip(p,v))<.48**2 for v in cells.get(c,[])):near=True;break
   if not near:water.append(p)
charge=round(sum(float(a[6]) for a in atoms));ions=abs(charge);assert ions<30
iontype='CL' if charge>0 else 'NA';water,ionxyz=water[:-ions] if ions else water,water[-ions:] if ions else []
text=['Intact col_9 local numerical diagnostic; newly constructed hydration',str(n+len(water)+len(ionxyz))]
for i,(l,p) in enumerate(zip(lines,xyz),1):text.append(l[:15]+f'{i%100000:5d}'+''.join(f'{v:8.3f}' for v in p)+l[44:])
for j,p in enumerate(water,1):text.append(f'{(700+j)%100000:5d}{"W":<5}{"W":>5}{(n+j)%100000:5d}'+''.join(f'{v:8.3f}' for v in p))
for j,p in enumerate(ionxyz,1):text.append(f'{(900+j)%100000:5d}{iontype:<5}{iontype:>5}{(n+len(water)+j)%100000:5d}'+''.join(f'{v:8.3f}' for v in p))
text.append(' '.join(f'{v:.7f}' for v in box));(out/'start.gro').write_text('\n'.join(text)+'\n')
top='''#define GO_VIRT
#include "martini_v3.0.0.itp"
#include "go-sites.itp"
#include "col_9.itp"
#include "col_9_go-excl.itp"
#include "martini_v3.0.0_solvents_v1.itp"
#include "martini_v3.0.0_ions_v1.itp"
[ system ]
Intact failing triple helix in a new hydration fixture
[ molecules ]
col_9 1
W '''+str(len(water))+'\n'+(iontype+' '+str(ions)+'\n' if ions else '');(out/'system.top').write_text(top)
groups={'System':list(range(1,n+len(water)+ions+1)),'Protein':list(range(1,n+1)),'non-Protein':list(range(n+1,n+len(water)+ions+1)),'ACE':[int(a[0]) for a in atoms if a[3]=='ACE' and a[4]=='BB'],'NME':[int(a[0]) for a in atoms if a[3]=='NME' and a[4]=='BB']};assert len(groups['ACE'])==len(groups['NME'])==3
(out/'complete.ndx').write_text(''.join('[ '+name+' ]\n'+'\n'.join(' '.join(map(str,v[i:i+15])) for i in range(0,len(v),15))+'\n' for name,v in groups.items()))
# Reuse source microscopic potentials; only the system/environment and ensemble differ.
base=[]
for line in (src/'source-relative.mdp').read_text().splitlines():
 key=line.split('=',1)[0].strip().lower().replace('_','-')
 if key.startswith('pull-') or key=='pull':continue
 base.append(line)
base+=['pull = yes','pull-ngroups = 2','pull-ncoords = 1','pull-group1-name = ACE','pull-group2-name = NME','pull-coord1-type = constant-force','pull-coord1-geometry = direction','pull-coord1-groups = 1 2','pull-coord1-dim = N N Y','pull-coord1-vec = 0 0 1','pull-coord1-k = -1806','pull-coord1-start = yes'];(out/'source-relative.mdp').write_text('\n'.join(base)+'\n')
report={'fixture':'Intact col_9 plus newly constructed Martini water box; not the original fibril environment','solute_atoms':n,'water_beads':len(water),'counterion_type':iontype if ions else None,'counterions':ions,'net_solute_charge_e':charge,'box_nm':box,'original_global_atom_mapping':{'21211':462,'21212':463,'21632':883,'21633':884},'changes':['Other helices removed; no intermolecular covalent bonds exist in the source system.top.','New water grid and counterions; energy minimization required.','NVT replaces source NPT; same applied end force; cap coordinates translated only.','Original internal potential parameters and topology retained.'],'limits':'A stable reduced fixture does not establish full-fibril stability or identify the source failure uniquely.'};(root/'reduced-fixture.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
