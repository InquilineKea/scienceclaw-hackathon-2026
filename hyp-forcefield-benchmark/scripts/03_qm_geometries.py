"""Step 3a: GFN2-xTB constrained geometries for Ace-Hyp-NMe (minima + scans).

Constraints common to every point (QM and, later, MM):
  psi fixed (150 deg unless psi is the scanned coordinate)  -> keeps the PPII/collagen region, prevents
                                                               collapse to the gas-phase C7 hydrogen-bonded form
  hydroxyl torsion HG-CG-OD1-HD1 fixed at 180 deg            -> one OH rotamer everywhere (sensitivity run separately)
Output: results/qm_geometries.json
"""
import json
import os
import sys

import numpy as np
import openmm.app as app

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import build, geom, qm  # noqa: E402
from hypbench.ffreg import ROOT  # noqa: E402

pdb = app.PDBFile(os.path.join(ROOT, "structures", "ace_hyp_nme.pdb"))
top = pdb.topology
sym = [a.element.symbol for a in top.atoms()]
x0 = np.array(pdb.positions._value) * 10
row = [r for r in build.residue_table(top) if r["resname"] == "HYP"][0]
a = row["atoms"]
names = {(at.residue.name, at.name): at.index for at in top.atoms()}
T = dict(phi=row["phi"], psi=row["psi"], chi2=row["chi2"], oh=(a["HG"], a["CG"], a["OD1"], a["HD1"]))
PSI0, OH0 = 150.0, 180.0


def meas(x):
    m = build.measure([row], x / 10)[0]
    return {k: float(v) for k, v in m.items()}


def opt(x, **cons):
    c = [(T[k], v) for k, v in cons.items()]
    xyz, e = qm.xtb_opt(sym, x, c)
    return xyz, e


points = []


def add(scan, label, x, e, cons):
    points.append(dict(scan=scan, label=label, xyz=np.round(x, 6).tolist(), e_xtb=e, constraints=cons, **meas(x)))
    m = points[-1]
    print(f"{scan:10s} {label:>8s} E={e:.6f} phi={m['phi']:7.1f} psi={m['psi']:7.1f} chi1={m['chi1']:6.1f} chi2={m['chi2']:6.1f} "
          f"P={m['P']:7.1f} amp={m['amp']:5.1f} w={m['omega']:7.1f}", flush=True)


# --- minima (psi, OH constrained; ring free)
x_exo, e_exo = opt(x0, psi=PSI0, oh=OH0)
add("minimum", "exo", x_exo, e_exo, dict(psi=PSI0, oh=OH0))
x_tmp, _ = opt(x_exo, psi=PSI0, oh=OH0, chi2=-35.0)
x_endo, e_endo = opt(x_tmp, psi=PSI0, oh=OH0)
add("minimum", "endo", x_endo, e_endo, dict(psi=PSI0, oh=OH0))
chi2_min = dict(exo=meas(x_exo)["chi2"], endo=meas(x_endo)["chi2"])
assert chi2_min["exo"] > 10 and chi2_min["endo"] < -10, f"minima did not stay in distinct puckers: {chi2_min}"

# --- pucker scan in chi2, both directions (hysteresis check); keep the lower energy per grid point
grid = np.arange(-45.0, 45.01, 7.5)
best = {}
for start, order in ((x_exo, grid[::-1]), (x_endo, grid)):
    x = start
    for c2 in order:
        x, e = opt(x, psi=PSI0, oh=OH0, chi2=float(c2))
        if c2 not in best or e < best[c2][1]:
            best[c2] = (x, e, 0 if c2 not in best else abs(e - best[c2][1]))
        else:
            best[c2] = (best[c2][0], best[c2][1], abs(e - best[c2][1]))
for c2 in grid:
    x, e, hyst = best[c2]
    add("pucker", f"{c2:+.1f}", x, e, dict(psi=PSI0, oh=OH0, chi2=float(c2)))
    points[-1]["hysteresis_hartree"] = hyst

# --- backbone psi scan for each pucker (chi2 held at that pucker's minimum value)
for pk, xs in (("exo", x_exo), ("endo", x_endo)):
    for direction in (+1, -1):
        x = xs
        vals = [150, 180, -150, -120, -90, -60, -30] if direction > 0 else [120, 90, 60, 30, 0]
        for psi in vals:
            x, e = opt(x, psi=float(psi), oh=OH0, chi2=chi2_min[pk])
            add(f"psi_{pk}", f"{psi:+d}", x, e, dict(psi=float(psi), oh=OH0, chi2=chi2_min[pk]))

# --- phi scan (limited by the ring) for each pucker
for pk, xs in (("exo", x_exo), ("endo", x_endo)):
    phi0 = meas(xs)["phi"]
    for vals in ([v for v in (-70, -60, -50, -40) if v >= phi0 - 5], [v for v in (-80, -90, -100, -110) if v < phi0 + 5]):
        x = xs
        for phi in vals:
            x, e = opt(x, psi=PSI0, oh=OH0, chi2=chi2_min[pk], phi=float(phi))
            add(f"phi_{pk}", f"{phi:+d}", x, e, dict(psi=PSI0, oh=OH0, chi2=chi2_min[pk], phi=float(phi)))

# --- hydroxyl rotamer sensitivity at the two minima
for pk, xs in (("exo", x_exo), ("endo", x_endo)):
    for oh in (60.0, -60.0):
        x, e = opt(xs, psi=PSI0, oh=oh)
        add(f"ohrot_{pk}", f"{oh:+.0f}", x, e, dict(psi=PSI0, oh=oh))

json.dump(dict(symbols=sym, torsion_atoms={k: list(map(int, v)) for k, v in T.items()}, points=points),
          open(os.path.join(ROOT, "results", "qm_geometries.json"), "w"))
print("n points", len(points))
