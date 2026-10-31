#!/usr/bin/env bash
# Four argon atoms: infrastructure check only, no biological content.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT/runs"
mkdir "$ROOT/runs/argon"
cd "$ROOT/runs/argon"
cat > argon.gro <<'EOF'
Four-argon infrastructure smoke
    4
    1ARG     AR    1   0.000   0.000   0.000
    2ARG     AR    2   0.500   0.000   0.000
    3ARG     AR    3   0.000   0.500   0.000
    4ARG     AR    4   0.000   0.000   0.500
   2.00000   2.00000   2.00000
EOF
cat > argon.top <<'EOF'
[ defaults ]
1 2 no 1.0 1.0
[ atomtypes ]
Ar 18 39.948 0.0 A 0.3405 0.996
[ moleculetype ]
ARG 1
[ atoms ]
1 Ar 1 ARG AR 1 0.0 39.948
[ system ]
Four-argon infrastructure smoke
[ molecules ]
ARG 4
EOF
# Combination rule 2 interprets 0.3405 nm and 0.996 kJ/mol as sigma/epsilon.
cat > argon.mdp <<'EOF'
integrator = md
nsteps = 1000
dt = 0.001
cutoff-scheme = Verlet
nstlist = 10
rcoulomb = 0.8
rvdw = 0.8
coulombtype = Cut-off
vdwtype = Cut-off
pbc = xyz
constraints = none
tcoupl = no
pcoupl = no
gen_vel = yes
gen_temp = 120
gen_seed = 17
nstxout = 0
nstvout = 0
nstxout-compressed = 100
nstenergy = 100
nstlog = 100
EOF
gmx grompp -f argon.mdp -c argon.gro -p argon.top -o argon.tpr -pp processed.top -po actual.mdp -maxwarn 0 > grompp.log 2>&1
timeout --signal=TERM --kill-after=10s 60s gmx mdrun -deffnm argon -ntmpi 1 -ntomp 1 -nb gpu -pme cpu -bonded cpu -update cpu > console.log 2>&1
gmx check -f argon.xtc > trajectory-check.txt 2>&1
printf 'Total-Energy\n0\n' | gmx energy -f argon.edr -o energy.xvg > energy-summary.txt 2>&1
python3 - <<'PY'
import json, math, re
from pathlib import Path
s=Path('argon.log').read_text()
assert 'Finished mdrun' in s
assert re.search(r'[Ss]hort[- ]range.*GPU|[Gg]PU.*short[- ]range',s)
assert not re.search(r'Fatal error|LINCS WARNING',s)
rows=[[float(x) for x in l.split()] for l in Path('energy.xvg').read_text().splitlines() if l.strip() and not l.startswith(('#','@'))]
assert all(math.isfinite(x) for row in rows for x in row)
assert len(rows)>=11 and rows[-1][0]>=1.0
Path('verification.json').write_text(json.dumps({'status':'INFRASTRUCTURE_SMOKE_COMPLETE','time_ps':rows[-1][0],'energy_frames':len(rows),'biological_model':False},indent=2)+'\n')
print(Path('verification.json').read_text())
PY
