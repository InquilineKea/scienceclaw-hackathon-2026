"""Explicit-solvent MD with each force field's validated water model.  Resumable, chunked output."""
import glob
import json
import os
import time

import numpy as np
import openmm
import openmm.app as app
import openmm.unit as u

from . import build, ffreg

SYSTEMS = {
    # name: (structure file, box (nm) or None, description)
    "dipeptide": ("ace_hyp_nme.pdb", (2.8, 2.8, 2.8)),
    "dipeptide_endo": ("ace_hyp_nme_endo.pdb", (2.8, 2.8, 2.8)),  # same molecule started from the xTB C-gamma-endo minimum
    "helix": ("pog3_triple_helix.pdb", None),  # box derived from the solute after alignment
}
# Nonbonded settings follow each family's standard practice
NB = {
    "amber": dict(nonbondedCutoff=0.9 * u.nanometer),
    "charmm": dict(nonbondedCutoff=1.2 * u.nanometer, switchDistance=1.0 * u.nanometer),
}
WATER_MODELLER = {"tip3p": "tip3p", "charmm-tip3p": "tip3p", "opc": "tip4pew"}  # geometry template for placement only
TEMPERATURE = 300.0
DT_FS = 4.0
HMASS = 3.0
SAVE_STEPS = 50  # 0.2 ps


def charmm_lj_to_nonbonded(system, rtol=1e-6):
    """Exact re-encoding of the CHARMM LJ terms for speed on the CPU platform.

    OpenMM's CHARMM XML puts LJ in a CustomNonbondedForce with a type-pair table (to support NBFIX) and the
    special 1-4 LJ in a CustomBondForce.  If - and only if - every type pair present in *this* system obeys
    Lorentz-Berthelot (i.e. no NBFIX override is active), the same energy is produced by the standard
    NonbondedForce.  Otherwise this raises: nothing is approximated.  Equivalence is unit-tested.
    """
    forces = {f.__class__.__name__: (i, f) for i, f in enumerate(system.getForces())}
    nbf = forces["NonbondedForce"][1]
    ci, cnb = forces["CustomNonbondedForce"]
    bi, cb = forces["CustomBondForce"]
    assert cnb.getEnergyFunction().replace(" ", "") == "acoef(type1,type2)/r^12-bcoef(type1,type2)/r^6;"
    assert cb.getEnergyFunction().replace(" ", "") == "4*epsilon*((sigma/r)^12-(sigma/r)^6)"
    tabs = {cnb.getTabulatedFunctionName(i): cnb.getTabulatedFunction(i).getFunctionParameters() for i in range(2)}
    n = tabs["acoef"][0]
    A = np.array(tabs["acoef"][2]).reshape(n, n)
    B = np.array(tabs["bcoef"][2]).reshape(n, n)
    types = np.array([int(cnb.getParticleParameters(i)[0]) for i in range(cnb.getNumParticles())])
    present = sorted(set(types))
    sig, eps = np.ones(n), np.zeros(n)
    for t in present:
        if A[t, t] > 0 and B[t, t] > 0:
            sig[t] = (A[t, t] / B[t, t]) ** (1 / 6)
            eps[t] = B[t, t] ** 2 / (4 * A[t, t])
    worst = 0.0
    for a in present:
        for b in present:
            s, e = 0.5 * (sig[a] + sig[b]), np.sqrt(eps[a] * eps[b])
            for tab, ref in ((A, 4 * e * s ** 12), (B, 4 * e * s ** 6)):
                dev = abs(tab[a, b] - ref) / max(abs(ref), 1e-30) if ref > 0 else abs(tab[a, b])
                worst = max(worst, dev)
    if worst > rtol:
        raise RuntimeError(f"NBFIX-type pair override active in this system (max rel dev {worst:.2e}); fast path refused")
    for i in range(nbf.getNumParticles()):
        q, _, _ = nbf.getParticleParameters(i)
        nbf.setParticleParameters(i, q, sig[types[i]], eps[types[i]])
    exc = {}
    for e in range(nbf.getNumExceptions()):
        i, j, qq, s, ee = nbf.getExceptionParameters(e)
        exc[(min(i, j), max(i, j))] = e
    for b in range(cb.getNumBonds()):
        i, j, (s, e) = cb.getBondParameters(b)
        k = exc[(min(i, j), max(i, j))]
        _, _, qq, _, _ = nbf.getExceptionParameters(k)
        nbf.setExceptionParameters(k, i, j, qq, s, e)
    nbf.setUseSwitchingFunction(cnb.getUseSwitchingFunction())
    nbf.setSwitchingDistance(cnb.getSwitchingDistance())
    nbf.setUseDispersionCorrection(cnb.getUseLongRangeCorrection())
    for idx in sorted((ci, bi), reverse=True):
        system.removeForce(idx)
    return dict(n_lj_types_present=len(present), max_rel_dev_from_LB=worst, n_14_lj=cb.getNumBonds())


def align_to_x(pos):
    """Rotate so that the first principal axis lies along x; centre at origin."""
    c = pos - pos.mean(0)
    w, v = np.linalg.eigh(np.cov(c.T))
    axes = v[:, ::-1]
    if np.linalg.det(axes) < 0:
        axes[:, 2] *= -1
    return c @ axes


def prepare(ff, system, seed=1, fast_charmm=True, barostat=True):
    d = ffreg.FORCEFIELDS[ff]
    fam = d["family"]
    fn, box = SYSTEMS[system]
    pdb = app.PDBFile(os.path.join(ffreg.ROOT, "structures", fn))
    top0 = pdb.topology
    pos = np.array(pdb.positions._value)
    if box is None:
        pos = align_to_x(pos)
        ext = pos.max(0) - pos.min(0)
        lat = max(ext[1], ext[2]) + 2.0  # >= 2.0 nm of solvent between lateral images
        box = (float(ext[0] + 2.0), float(lat), float(lat))
    pos = pos - pos.mean(0) + np.array(box) / 2
    top = build.topology_for(fam, top0)
    ffo = ffreg.load(ff)  # validated water for this FF; raises on a non-validated pairing
    mod = app.Modeller(top, pos * u.nanometer)
    mod.addSolvent(ffo, model=WATER_MODELLER[d["water"]], boxSize=openmm.Vec3(*box) * u.nanometer, neutralize=False)
    sysm = ffo.createSystem(mod.topology, nonbondedMethod=app.PME, constraints=app.HBonds, rigidWater=True,
                            hydrogenMass=HMASS * u.amu, **NB[fam])
    lj_report = charmm_lj_to_nonbonded(sysm) if fam == "charmm" and fast_charmm else None
    if barostat:
        sysm.addForce(openmm.MonteCarloBarostat(1.0 * u.bar, TEMPERATURE * u.kelvin, 25))
    n_solute = top0.getNumAtoms()
    return dict(system=sysm, topology=mod.topology, positions=mod.positions, n_solute=n_solute, box=box,
                solute_top=top0, lj_report=lj_report)


def run(ff, system, ns, outdir, threads=1, equil_ps=10.0, chunk_ps=10.0, seed=1):
    os.makedirs(outdir, exist_ok=True)
    p = prepare(ff, system, seed)
    integ = openmm.LangevinMiddleIntegrator(TEMPERATURE * u.kelvin, 1.0 / u.picosecond, DT_FS * u.femtosecond)
    integ.setRandomNumberSeed(seed)
    plat = openmm.Platform.getPlatformByName("CPU")
    sim = app.Simulation(p["topology"], p["system"], integ, plat, {"Threads": str(threads)})
    state_file = os.path.join(outdir, "state.xml")
    meta_file = os.path.join(outdir, "meta.json")
    chunks = sorted(glob.glob(os.path.join(outdir, "chunk_*.npz")))
    if chunks and os.path.exists(state_file):
        sim.loadState(state_file)
    else:
        chunks = []
        sim.context.setPositions(p["positions"])
        e0 = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)
        sim.minimizeEnergy(maxIterations=1000)
        e1 = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)
        sim.context.setVelocitiesToTemperature(TEMPERATURE * u.kelvin, seed)
        sim.step(int(equil_ps * 1000 / DT_FS))
        json.dump(dict(ff=ff, system=system, water=ffreg.FORCEFIELDS[ff]["water"], n_atoms=p["system"].getNumParticles(),
                       n_solute=p["n_solute"], box_nm=p["box"], e_initial=e0, e_minimised=e1, dt_fs=DT_FS,
                       hydrogen_mass=HMASS, temperature=TEMPERATURE, charmm_lj_reencoding=p['lj_report'], save_ps=SAVE_STEPS * DT_FS / 1000,
                       equil_ps=equil_ps, nonbonded={k: str(v) for k, v in NB[ffreg.FORCEFIELDS[ff]["family"]].items()},
                       openmm=openmm.__version__, seed=seed), open(meta_file, "w"), indent=1)
        sim.saveState(state_file)
    n_chunks = int(round(ns * 1000 / chunk_ps))
    frames_per_chunk = int(chunk_ps * 1000 / DT_FS / SAVE_STEPS)
    ns_idx = p["n_solute"]
    t0 = time.time()
    for c in range(len(chunks), n_chunks):
        xyz = np.empty((frames_per_chunk, ns_idx, 3), np.float32)
        epot = np.empty(frames_per_chunk)
        vol = np.empty(frames_per_chunk)
        boxes = np.empty((frames_per_chunk, 3))
        for f in range(frames_per_chunk):
            sim.step(SAVE_STEPS)
            st = sim.context.getState(getPositions=True, getEnergy=True)
            xyz[f] = st.getPositions(asNumpy=True).value_in_unit(u.nanometer)[:ns_idx]
            epot[f] = st.getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)
            bv = st.getPeriodicBoxVectors(asNumpy=True).value_in_unit(u.nanometer)
            boxes[f] = np.diag(bv)
            vol[f] = np.prod(boxes[f])
        np.savez_compressed(os.path.join(outdir, f"chunk_{c:04d}.npz"), xyz=xyz, epot=epot, vol=vol, box=boxes)
        sim.saveState(state_file)
        el = time.time() - t0
        print(f"{ff} {system} chunk {c+1}/{n_chunks} {el:.0f}s  ({(c+1-len(chunks))*chunk_ps/1000/el*86400:.1f} ns/day)", flush=True)


def load(outdir):
    chunks = sorted(glob.glob(os.path.join(outdir, "chunk_*.npz")))
    if not chunks:
        return None
    d = [np.load(c) for c in chunks]
    return dict(xyz=np.concatenate([x["xyz"] for x in d]), epot=np.concatenate([x["epot"] for x in d]),
                vol=np.concatenate([x["vol"] for x in d]), box=np.concatenate([x["box"] for x in d]),
                meta=json.load(open(os.path.join(outdir, "meta.json"))))
