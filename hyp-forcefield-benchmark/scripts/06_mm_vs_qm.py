"""Step 4: gas-phase MM energies on the QM scan grid for every force field -> results/mm_energies.json

For each QM point the MM geometry is re-optimised from the QM geometry with the *same* torsions restrained
(harmonic, 2000 kJ/mol/rad^2); the restraint energy is excluded (separate force group).
"""
import json
import os
import sys

import numpy as np
import openmm
import openmm.app as app
import openmm.unit as u

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import build, ffreg, md  # noqa: E402

R = os.path.join(ffreg.ROOT, "results")
G = json.load(open(os.path.join(R, "qm_geometries.json")))
pdb = app.PDBFile(os.path.join(ffreg.ROOT, "structures", "ace_hyp_nme.pdb"))
top0 = pdb.topology
row = [r for r in build.residue_table(top0) if r["resname"] == "HYP"][0]
T = G["torsion_atoms"]
KEYS = ("phi", "psi", "chi2", "oh")
out = {}
for name, d in ffreg.FORCEFIELDS.items():
    ff = ffreg.load(name, water=None)
    top = build.topology_for(d["family"], top0)
    system = ff.createSystem(top, nonbondedMethod=app.NoCutoff, constraints=None)
    if d["family"] == "charmm":
        md.charmm_lj_to_nonbonded(system)  # exact re-encoding (see tests), avoids the slow table lookup
    rest = openmm.CustomTorsionForce("0.5*k*min(dt, 2*pi-dt)^2; dt=abs(theta-theta0); pi=3.141592653589793")
    rest.addPerTorsionParameter("k")
    rest.addPerTorsionParameter("theta0")
    for key in KEYS:
        rest.addTorsion(*T[key], [0.0, 0.0])
    rest.setForceGroup(7)
    system.addForce(rest)
    ctx = openmm.Context(system, openmm.VerletIntegrator(0.001), openmm.Platform.getPlatformByName("Reference"))
    res = []
    for p in G["points"]:
        for n, key in enumerate(KEYS):
            on = key in p["constraints"]
            rest.setTorsionParameters(n, *T[key], [2000.0 if on else 0.0, float(np.radians(p["constraints"][key])) if on else 0.0])
        rest.updateParametersInContext(ctx)
        ctx.setPositions(np.array(p["xyz"]) * 0.1)
        e_sp = ctx.getState(getEnergy=True, groups={0}).getPotentialEnergy().value_in_unit(u.kilocalorie_per_mole)
        openmm.LocalEnergyMinimizer.minimize(ctx, 1e-3, 3000)
        st = ctx.getState(getEnergy=True, getPositions=True, groups={0})
        e = st.getPotentialEnergy().value_in_unit(u.kilocalorie_per_mole)
        er = ctx.getState(getEnergy=True, groups={7}).getPotentialEnergy().value_in_unit(u.kilocalorie_per_mole)
        x = st.getPositions(asNumpy=True).value_in_unit(u.nanometer)
        m = {k: float(v) for k, v in build.measure([row], x)[0].items()}
        res.append(dict(scan=p["scan"], label=p["label"], e_mm=e, e_mm_qmgeom=e_sp, e_restraint=er,
                        rmsd_to_qm_A=float(np.sqrt(((x * 10 - np.array(p["xyz"])) ** 2).sum(1).mean())), **m))
    del ctx
    out[name] = res
    ex = [r for r in res if r["scan"] == "minimum"]
    print(f"{name:7s} E(endo)-E(exo) = {ex[1]['e_mm']-ex[0]['e_mm']:+.2f} kcal/mol   chi2 exo {ex[0]['chi2']:.1f} endo {ex[1]['chi2']:.1f}  "
          f"max restraint E {max(r['e_restraint'] for r in res):.3f}", flush=True)
json.dump(out, open(os.path.join(R, "mm_energies.json"), "w"))
