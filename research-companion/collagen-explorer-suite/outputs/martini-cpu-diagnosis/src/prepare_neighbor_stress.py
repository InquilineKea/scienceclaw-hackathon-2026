from pathlib import Path
import shutil,json
root=Path('outputs/martini-cpu-diagnosis');out=root/'neighbor-stress-input';out.mkdir(exist_ok=False);shutil.copyfile(root/'input/martini_v3.0.0.itp',out/'martini_v3.0.0.itp')
lines=['Controlled fast-collision neighbor-list stress fixture, not collagen','64'];i=0
for group in range(2):
 for j in range(4):
  for k in range(4):
   for bead in range(2):
    i+=1;pos=[2+group*1.6,1+j*1.4+bead*.292+group*.05,1+k*1.4];vel=[1.2 if group==0 else -1.2,0,0];lines.append(f'{(i-1)//2+1:5d}{"VAL":<5}{("BB" if bead==0 else "SC1"):>5}{i:5d}'+''.join(f'{v:8.3f}'for v in pos)+''.join(f'{v:8.4f}'for v in vel))
lines.append('8.0 8.0 8.0');(out/'start.gro').write_text('\n'.join(lines)+'\n')
(out/'system.top').write_text('''#include "martini_v3.0.0.itp"
[ moleculetype ]
DIMER 1
[ atoms ]
1 SP2 1 VAL BB 1 0
2 SC3 1 VAL SC1 2 0
[ constraints ]
1 2 1 0.292
[ system ]
Controlled fast collisions: numerical stress, not physiological sampling
[ molecules ]
DIMER 32
''')
(out/'complete.ndx').write_text('[ System ]\n'+' '.join(map(str,range(1,65)))+'\n')
print('Prepared64-atom controlled neighbor-list stress fixture; not executed.')
