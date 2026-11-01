#!/usr/bin/env bash
# B3: LAMMPS oscillatory shear -> G', G'' for healthy vs oxidised Col I / VII networks.
# Run on a Brev box inside a pinned container (never on the Mac). From ~/oxt:
#   docker run --rm -v "$PWD":/work -w /work -v oxt-lammps-conda:/opt/lammps-env \
#     -v oxt-mamba:/opt/mamba python:3.12.7-bookworm bash remote/brev_lammps.sh
# LAMMPS from conda-forge (pinned 2024.08.29) via pinned micromamba 1.5.10; bookworm base
# because the conda-forge lammps build needs GLIBC >= 2.34. pytorch-cpu only so oxt
# (deterministic deck generation + fit_viscoelastic) imports.
# Outputs: remote/lammps/<name>_stress.txt and remote/lammps/G_Gpp_summary.json
set -euo pipefail
cd "$(dirname "$0")/.."
ENV=/opt/lammps-env
MAMBA=/opt/mamba/bin/micromamba
if [ ! -x "$ENV/bin/lmp" ]; then
  if [ ! -x "$MAMBA" ]; then
    mkdir -p /opt/mamba/bin
    curl -Ls https://github.com/mamba-org/micromamba-releases/releases/download/1.5.10/micromamba-linux-64.tar.bz2 \
      | tar -xj -C /opt/mamba/bin --strip-components=1
  fi
  "$MAMBA" create -y -p "$ENV" -c conda-forge "lammps=2024.08.29" numpy "pytorch-cpu=2.5.1" \
    || "$MAMBA" create -y -p "$ENV" -c conda-forge "lammps=2024.08.29" numpy "pytorch=2.5.1=cpu*"
fi
echo "=== lmp sanity check"
"$ENV/bin/lmp" -h > /tmp/lmp_h.txt 2>&1 || true
head -2 /tmp/lmp_h.txt
grep -q "Large-scale Atomic" /tmp/lmp_h.txt
"$ENV/bin/python" -c "import numpy, torch; print('numpy', numpy.__version__, 'torch', torch.__version__)"
echo "=== regenerate decks (W=32, seed 42; deterministic)"
md5sum remote/lammps/*.in remote/lammps/*.data > /tmp/decks_before.md5
"$ENV/bin/python" remote/make_lammps_inputs.py 32
md5sum remote/lammps/*.in remote/lammps/*.data > /tmp/decks_after.md5
diff /tmp/decks_before.md5 /tmp/decks_after.md5 && echo "decks reproducible (byte-identical)" \
  || echo "WARNING: regenerated decks differ from pushed ones"
echo "=== run the 6 decks"
cd remote/lammps
for f in *.in; do
  n="${f%.in}"
  if [ -s "${n}_stress.txt" ]; then echo "skip $n (stress file present)"; continue; fi
  echo "--- lmp -in $f"
  "$ENV/bin/lmp" -in "$f" > "/tmp/${n}.log" 2>&1 || { tail -5 "/tmp/${n}.log"; exit 1; }
  tail -2 "/tmp/${n}.log"
done
cd ../..
echo "=== fit G', G''"
"$ENV/bin/python" - <<'EOF'
import json
from pathlib import Path
from oxt.lammps_export import fit_viscoelastic
out = {}
for p in sorted(Path("remote/lammps").glob("*_stress.txt")):
    out[p.name] = fit_viscoelastic(p, 200.0)
Path("remote/lammps/G_Gpp_summary.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
EOF
echo "B3 DONE"
