#!/usr/bin/env python3
"""Write LAMMPS decks (oscillatory shear -> G', G'') for healthy vs oxidised networks.
Run remotely in the reviewed single-rank CPU environment:
  python -m oxt.lammps_export remote/lammps/<name>.in
Bare lmp lacks the mandatory exact angular callback. This is not GPU-ready.
then: python3 -c "from oxt.lammps_export import fit_viscoelastic; print(fit_viscoelastic('remote/lammps/<name>_stress.txt', 200))"
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oxt.lammps_export import export
from oxt.materials import COLLAGENS, Damage, build_spec
from oxt.network import Lattice

out = Path(__file__).resolve().parent / "lammps"
lat = Lattice(int(sys.argv[1]) if len(sys.argv) > 1 else 32)
for col in ("I", "VII"):
    for mode, dose in (("none", 0.0), ("iso", 1.0), ("aniso", 1.0)):
        spec = build_spec(lat, COLLAGENS[col], Damage(mode, dose), np.random.default_rng(42), mu_el=0.01, k_gag=1e-4)
        p = export(spec, lat, out, name=f"col{col}_{mode}")
        print(p)
