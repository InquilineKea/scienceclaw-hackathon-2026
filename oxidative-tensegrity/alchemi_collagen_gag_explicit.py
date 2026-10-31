#!/usr/bin/env python3
"""Explicit-solvent binding free energy for the collagen-GAG interface (follow-up to alchemi_collagen_gag.py).

The rigid-scan AIMNet2 version (alchemi_collagen_gag.py) returns *contact energies* to rank chemistries: it has
no explicit water, no counterions, no conformational relaxation, and no entropy, so its numbers are not binding
free energies. Its own docstring names the fix -- "OpenMM/GROMACS with a validated protein-glycan force field".
This script is that fix.

Method: potential of mean force (PMF) by umbrella sampling along the collagen-side <-> GAG-side centre-of-mass
separation, in TIP3P water with 0.15 M NaCl, GAFF-2.11 + AM1-BCC parameters (openmmforcefields/OpenFF).
Each window restrains the COM distance with a harmonic bias; MBAR (pymbar>=4) unbiases the overlapping windows
into a continuous PMF. The binding free energy is the depth of the PMF well relative to the dissociated plateau,
with the standard-state / shell-volume correction applied.

Reuses the SAME chemistry as the rigid scan (imported from alchemi_collagen_gag): capped Lys/Arg and their
glycated forms CML-Lys / MG-H1-Arg, versus a dermatan-sulfate disaccharide at 0/1/2 sulfations. So the biology
question -- does glycation (loss of the + charge) weaken collagen-GAG binding? -- is now answered with a free
energy, directly comparable to the contact-energy ranking.

What is MORE accurate here than the rigid scan, and why it matters:
  * explicit TIP3P water + 0.15 M NaCl         -> real dielectric screening & ion condensation, not a Debye constant
  * full relaxation inside every umbrella window -> no rigid-fragment artefact
  * conformational + solvent entropy via sampling -> free energy, not a single-point interaction energy
  * PMF well depth + standard-state correction   -> a binding dG in kcal/mol, not an arbitrary contact energy

Honest residual caveats (see also the JSON "caveats" field):
  * GAFF-2.11 is only approximate for sulfated carbohydrates; GLYCAM06 or CHARMM36-carb is the publication-grade
    choice. Swap via --sugar-ff when those templates are available. AM1-BCC charges are used throughout.
  * single COM separation coordinate: captures the dominant cation-anion approach, not every bound pose. For a
    rigorous absolute dG, follow with a double-decoupling / alchemical (FEP) calculation.
  * one disaccharide fragment, not a full GAG chain or triple-helix context.

Usage (GPU box, after the oxidative-tensegrity security review is approved):
  python3 alchemi_collagen_gag_explicit.py --device CUDA --out results/alchemi_gag/collagen_gag_pmf.json
  python3 alchemi_collagen_gag_explicit.py --quick --pairs Lys:DS-4S CML-Lys:DS-4S     # fast smoke test

Requires: openmm>=8, openmmforcefields, openff-toolkit, pymbar>=4, rdkit, numpy.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

# Reuse the exact SMILES / charge definitions from the rigid-scan script so the two are comparable.
from alchemi_collagen_gag import COLLAGEN_SIDE, GAG_SIDE

ROOT = Path(__file__).resolve().parent

# --- physical constants -------------------------------------------------------------------------------------
KB_KJ = 0.0083144626  # kJ/mol/K
KJ_PER_KCAL = 4.184
NA = 6.02214076e23

# --- umbrella-sampling schedule (nm) -----------------------------------------------------------------------
# windows span tight contact -> dissociated plateau; the plateau defines the unbound reference.
WINDOW_MIN_NM = 0.30
WINDOW_MAX_NM = 1.45
WINDOW_STEP_NM = 0.05
UMBRELLA_K = 4000.0           # kJ/mol/nm^2 harmonic force constant on the COM distance


def _clean_smiles_to_rdkit(smiles):
    """Drop the scan-axis atom-map numbers (:1/:2) used by the rigid version; we restrain COMs, not one atom."""
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit could not parse SMILES: {smiles}")
    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.AddHs(mol)


def _make_offmol(smiles, name):
    """Build an OpenFF Molecule with one 3D conformer, ready for AM1-BCC parametrisation."""
    from openff.toolkit import Molecule

    rd = _clean_smiles_to_rdkit(smiles)
    from rdkit.Chem import AllChem

    params = AllChem.ETKDGv3()
    params.randomSeed = 11
    if AllChem.EmbedMolecule(rd, params) != 0:
        raise RuntimeError(f"embedding failed for {name}: {smiles}")
    AllChem.MMFFOptimizeMolecule(rd, maxIters=2000)
    off = Molecule.from_rdkit(rd, allow_undefined_stereo=True)
    off.name = name
    return off


def build_complex(collagen_name, gag_name, sugar_ff, padding_nm=1.0, ionic_M=0.15):
    """Parametrise both fragments, place them apart, solvate, and return (system, topology, positions, groups).

    groups = (collagen_atom_indices, gag_atom_indices) into the solute block, which is the first chunk of atoms.
    """
    import openmm
    from openmm import app, unit
    from openmmforcefields.generators import SystemGenerator

    csmi = COLLAGEN_SIDE[collagen_name][0]
    gsmi = GAG_SIDE[gag_name][0]
    mol_c = _make_offmol(csmi, collagen_name)
    mol_g = _make_offmol(gsmi, gag_name)

    forcefield_kwargs = dict(constraints=app.HBonds, rigidWater=True,
                             removeCMMotion=False, hydrogenMass=1.5 * unit.amu)
    system_generator = SystemGenerator(
        forcefields=["amber/protein.ff14SB.xml", "amber/tip3p_standard.xml", "amber/tip3p_HFE_multivalent.xml"],
        small_molecule_forcefield=sugar_ff,
        molecules=[mol_c, mol_g],
        forcefield_kwargs=forcefield_kwargs,
        periodic_forcefield_kwargs={"nonbondedMethod": app.PME},
    )

    # Combined gas-phase topology: collagen fragment first, GAG second, separated along +x by the first window.
    from openff.toolkit import Topology

    off_top = Topology.from_molecules([mol_c, mol_g])
    omm_top = off_top.to_openmm()

    xc = mol_c.conformers[0].to("nanometers").magnitude
    xg = mol_g.conformers[0].to("nanometers").magnitude
    xc = xc - xc.mean(0)
    xg = xg - xg.mean(0) + np.array([WINDOW_MIN_NM, 0.0, 0.0])
    positions = np.vstack([xc, xg]) * unit.nanometer
    n_c, n_g = len(xc), len(xg)

    modeller = app.Modeller(omm_top, positions)
    modeller.addSolvent(system_generator.forcefield, model="tip3p",
                        padding=padding_nm * unit.nanometer,
                        ionicStrength=ionic_M * unit.molar, neutralize=True)

    system = system_generator.create_system(modeller.topology)
    groups = (list(range(n_c)), list(range(n_c, n_c + n_g)))
    return system, modeller.topology, modeller.positions, groups, system.getNumParticles()


def add_umbrella(system, groups):
    """Add a harmonic restraint on the COM distance between the two solute fragments. Returns the force."""
    import openmm

    force = openmm.CustomCentroidBondForce(2, "0.5*k*(distance(g1,g2)-r0)^2")
    force.addPerBondParameter("k")
    force.addPerBondParameter("r0")
    g1 = force.addGroup(groups[0])
    g2 = force.addGroup(groups[1])
    force.addBond([g1, g2], [UMBRELLA_K, WINDOW_MIN_NM])
    system.addForce(force)
    return force


def com_distance_nm(positions_nm, groups, masses):
    """Mass-weighted COM separation (nm) from a raw positions array."""
    a, b = groups
    ma, mb = masses[a], masses[b]
    ca = (positions_nm[a] * ma[:, None]).sum(0) / ma.sum()
    cb = (positions_nm[b] * mb[:, None]).sum(0) / mb.sum()
    return float(np.linalg.norm(ca - cb))


def run_pair(collagen_name, gag_name, device, sugar_ff, equil_ps, sample_ps, sample_every_ps, temperature):
    """Umbrella-sample every window for one (collagen, GAG) pair; return per-window CV traces + metadata."""
    import openmm
    from openmm import unit

    system, topology, positions, groups, n_particles = build_complex(collagen_name, gag_name, sugar_ff)
    masses = np.array([system.getParticleMass(i).value_in_unit(unit.amu) for i in range(n_particles)])
    umbrella = add_umbrella(system, groups)

    centers = np.arange(WINDOW_MIN_NM, WINDOW_MAX_NM + 1e-9, WINDOW_STEP_NM)
    dt = 0.002  # ps
    n_equil = int(equil_ps / dt)
    n_sample = int(sample_ps / dt)
    stride = max(1, int(sample_every_ps / dt))

    integrator = openmm.LangevinMiddleIntegrator(temperature * unit.kelvin, 1.0 / unit.picosecond, dt * unit.picoseconds)
    system.addForce(openmm.MonteCarloBarostat(1.0 * unit.bar, temperature * unit.kelvin, 25))
    platform = openmm.Platform.getPlatformByName(device)
    context = openmm.Context(system, integrator, platform)
    context.setPositions(positions)
    context.setVelocitiesToTemperature(temperature * unit.kelvin)
    openmm.LocalEnergyMinimizer.minimize(context, maxIterations=2000)

    window_traces = []
    for ci, r0 in enumerate(centers):
        umbrella.setBondParameters(0, [0, 1], [UMBRELLA_K, float(r0)])
        umbrella.updateParametersInContext(context)
        # pull/relax toward this window before sampling
        integrator.step(n_equil)
        d_series = []
        collected = 0
        while collected < n_sample // stride:
            integrator.step(stride)
            state = context.getState(getPositions=True, enforcePeriodicBox=False)
            pos_nm = np.asarray(state.getPositions().value_in_unit(unit.nanometer))
            d_series.append(com_distance_nm(pos_nm, groups, masses))
            collected += 1
        window_traces.append(dict(center_nm=float(r0), k=UMBRELLA_K, distances_nm=d_series))
    del context, integrator
    return centers, window_traces, temperature


def mbar_pmf(centers, window_traces, temperature, n_bins=60):
    """Unbias the umbrella windows into a PMF (kcal/mol) via MBAR; return (bin_centers_nm, pmf_kcal, dpmf_kcal)."""
    from pymbar import FES

    kT = KB_KJ * temperature  # kJ/mol
    K = len(window_traces)
    x_n = np.concatenate([np.asarray(w["distances_nm"]) for w in window_traces])
    N_k = np.array([len(w["distances_nm"]) for w in window_traces])
    N = x_n.size

    # reduced biased potential of every sample in every window
    u_kn = np.zeros((K, N))
    for i, w in enumerate(window_traces):
        u_kn[i] = 0.5 * w["k"] * (x_n - w["center_nm"]) ** 2 / kT
    u_n_unbiased = np.zeros(N)  # target ensemble = no bias

    edges = np.linspace(x_n.min(), x_n.max(), n_bins + 1)
    bin_centers = 0.5 * (edges[:-1] + edges[1:])

    fes = FES(u_kn, N_k, verbose=False)
    fes.generate_fes(u_n_unbiased, x_n, fes_type="histogram",
                     histogram_parameters={"bin_edges": edges})
    res = fes.get_fes(bin_centers, reference_point="from-lowest", uncertainty_method="analytical")
    f_kcal = res["f_i"] * kT / KJ_PER_KCAL
    df_kcal = res["df_i"] * kT / KJ_PER_KCAL
    return bin_centers, f_kcal, df_kcal


def binding_dG(bin_centers, pmf_kcal, temperature):
    """Well depth relative to the dissociated plateau + standard-state correction (spherical shell to 1 M)."""
    plateau = np.mean(pmf_kcal[-max(3, len(pmf_kcal) // 10):])  # last ~10% of the coordinate
    well_i = int(np.argmin(pmf_kcal))
    r_min_nm = float(bin_centers[well_i])
    dG_raw = float(pmf_kcal[well_i] - plateau)  # negative = favourable
    # standard-state correction: from the sampled restraint shell to the 1 M (1661 nm^3/molecule) reference.
    v_shell_nm3 = 4.0 / 3.0 * np.pi * (float(bin_centers.max()) ** 3 - float(bin_centers.min()) ** 3)
    v_std_nm3 = 1660.5392
    kT_kcal = KB_KJ * temperature / KJ_PER_KCAL
    dG_std = dG_raw - kT_kcal * np.log(v_std_nm3 / v_shell_nm3)
    return dict(dG_bind_kcal=round(dG_std, 3), dG_well_vs_plateau_kcal=round(dG_raw, 3),
                r_min_nm=round(r_min_nm, 3), plateau_kcal=round(float(plateau), 3),
                standard_state_corr_kcal=round(-kT_kcal * float(np.log(v_std_nm3 / v_shell_nm3)), 3))


def parse_pairs(pairs_arg):
    if not pairs_arg or pairs_arg == ["all"]:
        return [(c, g) for c in COLLAGEN_SIDE for g in GAG_SIDE]
    out = []
    for item in pairs_arg:
        c, g = item.split(":")
        if c not in COLLAGEN_SIDE or g not in GAG_SIDE:
            raise SystemExit(f"unknown pair {item}; collagen in {list(COLLAGEN_SIDE)}, gag in {list(GAG_SIDE)}")
        out.append((c, g))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default="CUDA", help="OpenMM platform: CUDA / OpenCL / CPU")
    ap.add_argument("--sugar-ff", default="gaff-2.11",
                    help="small-molecule FF (gaff-2.11; use GLYCAM/CHARMM36-carb templates for publication)")
    ap.add_argument("--pairs", nargs="*", default=["Lys:DS-4S", "CML-Lys:DS-4S", "Arg:DS-4S", "MG-H1-Arg:DS-4S"],
                    help="'collagen:gag' pairs, or 'all'. Default = the four glycation comparisons at DS-4S.")
    ap.add_argument("--temperature", type=float, default=310.0, help="K (310 = physiological)")
    ap.add_argument("--equil-ps", type=float, default=200.0, help="equilibration per window (ps)")
    ap.add_argument("--sample-ps", type=float, default=1000.0, help="production per window (ps)")
    ap.add_argument("--sample-every-ps", type=float, default=1.0, help="CV recording stride (ps)")
    ap.add_argument("--quick", action="store_true", help="smoke profile: 20 ps equil / 50 ps sample per window")
    ap.add_argument("--save-traces", action="store_true", help="also write the raw per-window CV traces (.npz)")
    ap.add_argument("--out", default=str(ROOT / "results" / "alchemi_gag" / "collagen_gag_pmf.json"))
    a = ap.parse_args()

    if a.quick:
        a.equil_ps, a.sample_ps = 20.0, 50.0

    pairs = parse_pairs(a.pairs)
    t0 = time.time()
    table, traces_out = {}, {}
    for (cn, gn) in pairs:
        print(f"[{cn} | {gn}] umbrella sampling {len(np.arange(WINDOW_MIN_NM, WINDOW_MAX_NM + 1e-9, WINDOW_STEP_NM))} "
              f"windows ({a.equil_ps:.0f} ps equil + {a.sample_ps:.0f} ps sample each) on {a.device}...")
    for (cn, gn) in pairs:
        centers, window_traces, temp = run_pair(cn, gn, a.device, a.sugar_ff,
                                                a.equil_ps, a.sample_ps, a.sample_every_ps, a.temperature)
        bin_centers, pmf, dpmf = mbar_pmf(centers, window_traces, temp)
        dG = binding_dG(bin_centers, pmf, temp)
        table[f"{cn}|{gn}"] = dict(**dG,
                                   pmf_nm=[round(float(x), 3) for x in bin_centers],
                                   pmf_kcal=[round(float(x), 3) for x in pmf],
                                   pmf_err_kcal=[round(float(x), 3) for x in dpmf])
        traces_out[f"{cn}|{gn}"] = window_traces
        print(f"  dG_bind = {dG['dG_bind_kcal']:+.2f} kcal/mol  (well {dG['dG_well_vs_plateau_kcal']:+.2f} at "
              f"{dG['r_min_nm']} nm)")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(
        source=f"explicit-solvent-umbrella:{a.sugar_ff}/tip3p/am1bcc",
        method="COM-distance PMF, MBAR-unbiased, standard-state corrected",
        temperature_K=a.temperature, ionic_strength_M=0.15,
        windows=dict(min_nm=WINDOW_MIN_NM, max_nm=WINDOW_MAX_NM, step_nm=WINDOW_STEP_NM, k_kJ_mol_nm2=UMBRELLA_K),
        sampling=dict(equil_ps=a.equil_ps, sample_ps=a.sample_ps, stride_ps=a.sample_every_ps),
        seconds=round(time.time() - t0, 1),
        caveats=["GAFF-2.11 approximate for sulfated sugars; GLYCAM06/CHARMM36-carb preferred for publication",
                 "AM1-BCC charges",
                 "single COM separation coordinate (dominant pose); follow with alchemical FEP for absolute dG",
                 "one disaccharide fragment, not a full GAG chain or triple-helix context"],
        pairs=table), indent=2))
    print("wrote", out)

    if a.save_traces:
        npz = out.with_suffix(".traces.npz")
        flat = {f"{k}__w{j}": np.asarray(w["distances_nm"])
                for k, ws in traces_out.items() for j, w in enumerate(ws)}
        np.savez_compressed(npz, **flat)
        print("wrote", npz)


if __name__ == "__main__":
    main()
