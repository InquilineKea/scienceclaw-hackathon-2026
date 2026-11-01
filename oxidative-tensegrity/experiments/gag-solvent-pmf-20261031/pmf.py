#!/usr/bin/env python3
"""Explicit-water binding free energy of Arg / Lys / charge-lost analogs to a sulfate ester (GAG sulfate model).

Tests the sign of the B5 vacuum result (MG-H1-Arg loses dermatan-sulfate contact, Arg > Lys) once water and salt
screen the ion pair. Parameters are only those shipped in the approved OpenMM 8.6.1 wheel (CHARMM36 model
compounds, TIP3P, 0.15 M NaCl):

  MGUA  methylguanidinium   (+1)  Arg side chain
  MAMM  methylammonium      (+1)  Lys side chain
  DMAM  dimethylamine       ( 0)  charge-lost amine (crude stand-in for MG-H1 / CML charge loss)
  MSO4  methyl sulfate      (-1)  sulfated GalNAc ester of dermatan/chondroitin sulfate

Two independent calculations per cation:
  umbrella  19 harmonic windows on the cation-centre to S distance (0.30-1.20 nm), WHAM afterwards (analyze.py)
  unbiased  free MD in a small box; the bound fraction gives K directly (validator, different estimator)

  python3 pmf.py --out /results [--quick]       (inside the no-network container; entry.py calls this)
Each window/replica writes its own .npy and a .json receipt as soon as it finishes, so partial runs are usable.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

BONDS = {
    "MGUA": [("C", "N2"), ("C", "N3"), ("C", "N1"), ("N1", "H11"), ("N1", "H12"), ("N2", "H21"), ("N2", "H22"),
             ("N3", "H31"), ("N3", "C2"), ("C2", "HC1"), ("C2", "HC2"), ("C2", "HC3")],
    "MAMM": [("CE", "HE1"), ("CE", "HE2"), ("CE", "HE3"), ("CE", "NZ"), ("NZ", "HZ1"), ("NZ", "HZ2"), ("NZ", "HZ3")],
    "DMAM": [("N1", "HN1"), ("N1", "C1"), ("N1", "C2"), ("C1", "H11"), ("C1", "H12"), ("C1", "H13"), ("C2", "H21"),
             ("C2", "H22"), ("C2", "H23")],
    "MSO4": [("S", "OS1"), ("S", "OS2"), ("S", "OS3"), ("S", "OS4"), ("OS1", "C1"), ("C1", "H11"), ("C1", "H12"),
             ("C1", "H13")],
}
ROOT_ATOM = {"MGUA": "C", "MAMM": "NZ", "DMAM": "N1", "MSO4": "S"}  # restraint / distance atoms
CATIONS = ["MGUA", "MAMM", "DMAM"]
WINDOWS = np.round(np.arange(0.30, 1.2001, 0.05), 3)
K_UMB = 1000.0  # kJ/mol/nm^2


def _element(name):
    return {"C": "C", "N": "N", "O": "O", "S": "S", "H": "H"}[name[0]]


def build_coords(res, rng):
    """Rough 3D coordinates from connectivity: bonded atoms placed on tetrahedral directions, then minimised."""
    adj = {}
    for a, b in BONDS[res]:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    names = list(dict.fromkeys([x for ab in BONDS[res] for x in ab]))
    pos = {ROOT_ATOM[res]: np.zeros(3)}
    tet = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]], float) / math.sqrt(3)
    R = np.linalg.qr(rng.normal(size=(3, 3)))[0]
    queue, parent = [ROOT_ATOM[res]], {ROOT_ATOM[res]: None}
    while queue:
        a = queue.pop(0)
        kids = [b for b in adj[a] if b not in pos]
        if parent[a] is None:
            dirs = tet @ R.T
        else:
            u = pos[parent[a]] - pos[a]
            u /= np.linalg.norm(u)
            e1 = np.cross(u, rng.normal(size=3))
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(u, e1)
            c, s = math.cos(math.radians(109.5)), math.sin(math.radians(109.5))
            dirs = [c * u + s * (math.cos(p) * e1 + math.sin(p) * e2) for p in (0, 2.094, 4.189)]
        for b, d in zip(kids, dirs):
            pos[b] = pos[a] + d * (1.09 if b.startswith("H") else 1.45)
            parent[b] = a
            queue.append(b)
    return names, np.array([pos[n] for n in names]) / 10.0  # nm


def make_system(cation, r0, box_nm, seed, restrain=True):
    import openmm as mm
    from openmm import app, unit

    rng = np.random.default_rng(seed)
    top = app.Topology()
    chain = top.addChain()
    xyz = []
    centre_idx = {}
    for res, shift in ((cation, np.zeros(3)), ("MSO4", None)):
        names, X = build_coords(res, rng)
        if shift is None:  # sulfate S built >= 0.75 nm from the cation centre (no overlaps); the restraint pulls to r0
            v = rng.normal(size=3)
            shift = v / np.linalg.norm(v) * max(r0, 0.75)
        r = top.addResidue(res, chain)
        atoms = {}
        for n, x in zip(names, X):
            atoms[n] = top.addAtom(n, app.Element.getBySymbol(_element(n)), r)
            xyz.append(x + shift)
        for a, b in BONDS[res]:
            top.addBond(atoms[a], atoms[b])
        centre_idx[res] = atoms[ROOT_ATOM[res]].index
    xyz = np.array(xyz) + box_nm / 2
    ff = app.ForceField("charmm36.xml", "charmm36/water.xml")
    mod = app.Modeller(top, [mm.Vec3(*p) for p in xyz] * unit.nanometer)
    mod.addSolvent(ff, model="tip3p", boxSize=mm.Vec3(box_nm, box_nm, box_nm) * unit.nanometer,
                   ionicStrength=0.15 * unit.molar, neutralize=True)
    system = ff.createSystem(mod.topology, nonbondedMethod=app.PME, nonbondedCutoff=1.0 * unit.nanometer,
                             constraints=app.HBonds)
    system.addForce(mm.MonteCarloBarostat(1 * unit.bar, 300 * unit.kelvin))
    i, j = centre_idx[cation], centre_idx["MSO4"]
    if restrain:
        f = mm.CustomBondForce("0.5*k*(r-r0)^2")
        f.addGlobalParameter("k", K_UMB)
        f.addGlobalParameter("r0", r0)
        f.addBond(i, j, [])
        f.setUsesPeriodicBoundaryConditions(True)
        system.addForce(f)
    return mod, system, (i, j)


def _dist(state, i, j, box):
    p = state.getPositions(asNumpy=True).value_in_unit_system(__import__("openmm").unit.md_unit_system)
    d = p[j] - p[i]
    d -= box * np.round(d / box)
    return float(np.linalg.norm(d))


def run_one(task):
    # per-process kernel caches: 14 processes sharing one cache raced and produced "kernel not found" errors
    cache = f"/tmp/omm-{os.getpid()}"
    os.makedirs(cache, exist_ok=True)
    os.environ["CUDA_CACHE_PATH"] = cache + "/cuda"
    os.environ["OPENMM_CACHE_DIR"] = cache
    time.sleep((os.getpid() % 14) * 1.5)  # stagger the first context creations
    import openmm as mm
    from openmm import app, unit

    t0 = time.time()
    out = Path(task["out"])
    cat, kind, r0, seed = task["cation"], task["kind"], task["r0"], task["seed"]
    mod, system, (i, j) = make_system(cat, r0, task["box"], seed, restrain=(kind == "umbrella"))
    integ = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 0.002 * unit.picoseconds)
    integ.setRandomNumberSeed(seed)
    plat = mm.Platform.getPlatformByName(task.get("platform", "CUDA"))
    props = {"Precision": "mixed", "TempDirectory": f"/tmp/omm-{os.getpid()}"} if plat.getName() == "CUDA" else {}
    sim = app.Simulation(mod.topology, system, integ, plat, props)
    sim.context.setPositions(mod.positions)
    sim.minimizeEnergy(maxIterations=2000)
    sim.context.setVelocitiesToTemperature(300 * unit.kelvin, seed)
    sim.step(int(task["equil_ps"] / 0.002))
    every = int(task["sample_ps"] / 0.002)
    n = int(task["prod_ps"] / task["sample_ps"])
    r = np.empty(n)
    for k in range(n):
        sim.step(every)
        st = sim.context.getState(getPositions=True)
        box = np.array([v[q] for q, v in enumerate(st.getPeriodicBoxVectors(asNumpy=True).value_in_unit(unit.nanometer))])
        r[k] = _dist(st, i, j, box)
    st = sim.context.getState(getEnergy=True)
    vol = float(st.getPeriodicBoxVolume().value_in_unit(unit.nanometer ** 3))
    tag = f"{kind}_{cat}_{r0:.3f}_s{seed}" if kind == "umbrella" else f"{kind}_{cat}_s{seed}"
    np.save(out / f"{tag}.npy", r)
    rec = dict(tag=tag, n_atoms=system.getNumParticles(), box_volume_nm3=vol, seconds=round(time.time() - t0, 1),
               platform=plat.getName(), finite=bool(np.isfinite(r).all()),
               potential_kJ=float(st.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)), **task)
    (out / f"{tag}.json").write_text(json.dumps(rec, indent=1))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--deadline", type=float, default=float(os.environ.get("PMF_DEADLINE_UNIX", "0")) or None)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.quick:
        um = dict(equil_ps=10, prod_ps=20, sample_ps=0.5, box=3.0)
        ub = dict(equil_ps=10, prod_ps=20, sample_ps=0.5, box=2.8)
        win, reps = WINDOWS[::6], 1
    else:
        um = dict(equil_ps=100, prod_ps=750, sample_ps=0.5, box=3.4)  # first 14 MGUA windows ran 1500 ps
        ub = dict(equil_ps=200, prod_ps=3000, sample_ps=0.5, box=2.8)
        win, reps = WINDOWS, 6
    umb = {c: [dict(kind="umbrella", cation=c, r0=float(r0), seed=1000 + 10 * k + ci, out=str(out), **um)
               for k, r0 in enumerate(win)] for ci, c in enumerate(CATIONS)}
    unb = [dict(kind="unbiased", cation=c, r0=0.45, seed=5000 + 100 * ci + s, out=str(out), **ub)
           for ci, c in enumerate(["MGUA", "MAMM"]) for s in range(reps)]
    if a.quick:
        tasks = umb["MGUA"] + umb["MAMM"] + umb["DMAM"] + unb
    else:
        # throughput on one H100 is ~27 ns/h for 14 tiny systems: Arg/Lys profiles and their independent
        # validator first, the charge-lost control on every other window last
        tasks = umb["MGUA"] + umb["MAMM"] + unb + umb["DMAM"][::2]
    done = {p.stem for p in out.glob("*.json")}
    todo = [t for t in tasks if (f"umbrella_{t['cation']}_{t['r0']:.3f}_s{t['seed']}" if t["kind"] == "umbrella"
                                 else f"unbiased_{t['cation']}_s{t['seed']}") not in done]
    print(f"{len(todo)}/{len(tasks)} tasks to run, {a.workers} GPU processes", flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(run_one, t) for t in todo]
        for f in as_completed(futs):
            try:
                r = f.result()
                print(f"done {r['tag']} {r['seconds']}s", flush=True)
            except Exception as e:  # keep going; failures are recorded
                print(f"FAILED {type(e).__name__}: {e}", flush=True)
            if a.deadline and time.time() > a.deadline:
                print("deadline reached; cancelling remaining", flush=True)
                for g in futs:
                    g.cancel()
                break
    print("finished", flush=True)


if __name__ == "__main__":
    main()
