#!/usr/bin/env python3
"""3D architecture + fracture validation: does the 2D topo-opt conclusion survive in 3D?
(oxt/network3d.py)

Advisor feedback this experiment implements (verbatim):
  the 2D topo-opt results sit at z=3.2-3.8, just below the 2D isostatic point 4 and far below
  the 3D one of 6; behavior can change near the rigidity transition; bending
  resistance/prestress/boundary constraints can stabilize below Maxwell thresholds; published
  research shows certain 2D and 3D subisostatic fiber networks can behave similarly when
  connectivity is matched, so 2D conclusions need to survive that comparison.  The validation
  sequence: Step 1 - build a 3D network generator: diluted FCC network with stretching and
  bending, retaining the target connectivity range and optimized alignment patterns;
  Step 2 - repeat the actual comparison: winning aligned architecture vs random and uniform
  baselines, matched random seeds where possible, testing BOTH equal microscopic fiber
  properties AND matched initial bulk stiffness as SEPARATE experiments; Step 3 - measure
  actual resilience: stress-strain curves, failure strain, peak load, energy dissipation,
  spatial stress concentrations, relaxation and damage under repeated loading, not just
  initial stiffness.  Eight realizations is a small sample; seed-to-seed spread in G is
  0.5-0.8x, so use >=8 seeds and report spread.

Stage A (architecture matrix): architecture {aligned (2D winner translated: x-rich retention
p_along/p_transverse = 2 at amp 0.5, 8% junction locks at crossings), aligned_nolock,
uniform, random} x target z front x controls {E1_matched_fiber: identical microscopic fibre
properties; E2_matched_bulk: every stiffness rescaled so the initial shear modulus equals the
uniform baseline median at the same z (exact: the energy is linear in all stiffnesses)} x
matched seeds; report mean AND spread.

Stage B (fracture pipeline): notched specimens (pre-crack ahead of an internal crack plane)
under tension / shear / mixed-mode opening, irreversible fibre + crosslink failure, cohesive
traction-separation T(delta) extraction, per-condition fracture-law JSON (peak strength,
critical opening delta_f, G_c = integral T ddelta, uncertainty over >= 8 realizations) with
dimensionless->SI calibration hooks for the downstream MOOSE cohesive-zone FEM adapter.

  python3 run_network3d.py --profile smoke              # Mac CPU, minutes
  python3 run_network3d.py --profile local            # Mac CPU, hours
  python3 run_network3d.py --profile gpu --device cuda  # Nebius H100 (remote/nebius_3d.sh)
  python3 run_network3d.py --validate --profile smoke # generator validation only
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from oxt.network3d import ARCHS, _trap  # noqa: F401 (ARCHS documents the space)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "network3d"

ARCH_CODE = {a: i for i, a in enumerate(["uniform", "random", "aligned", "aligned_nolock"])}
ARCH_LOCK = {"aligned": 0.08, "aligned_nolock": 0.0, "uniform": 0.0, "random": 0.0}  # 2D winner: 8%

# Stage A profiles. relax: L-BFGS budget per relax call (sub-isostatic 3D networks crawl;
# G comes from the exact Hessian instead, curves carry the documented budget).
PROFILES = {
    "smoke": dict(W=3, z=[3.4], archs=["uniform", "aligned"], seeds=2, threads=2,
                  relax=dict(max_rounds=10, iters=150),
                  gammas=[0.005, 0.02, 0.05],
                  fail=list(np.round(np.arange(0.04, 0.25, 0.04), 3)),
                  cycles=2, cyc_steps=2, cyc_eps=0.10, axes=[0], controls=["E1", "E2"],
                  frac_modes=["tension", "shear"], frac_deltas=list(np.round(np.arange(0.01, 0.09, 0.01), 4)),
                  frac_conditions=[
                      dict(name="aligned_z3.4_notch25", arch="aligned", z=3.4,
                           lock_place="crossings", lock=0.08, elastin=0.0, age=0.0,
                           notch_shape="circle", notch_frac=0.25)]),
    "local": dict(W=4, z=[3.0, 3.4, 3.8], archs=["uniform", "random", "aligned", "aligned_nolock"],
                  seeds=8, threads=2, relax=dict(max_rounds=25, iters=250),
                  gammas=[0.002, 0.005, 0.01, 0.02, 0.05, 0.1],
                  fail=list(np.round(np.arange(0.02, 0.51, 0.04), 3)),
                  cycles=4, cyc_steps=3, cyc_eps=0.10, axes=[0], controls=["E1", "E2"],
                  frac_modes=["tension", "shear", "mixed"],
                  frac_deltas=list(np.round(np.arange(0.005, 0.16, 0.005), 4)),
                  frac_conditions=[dict(name="aligned_z3.4_notch25", arch="aligned", z=3.4,
                                        lock_place="crossings", lock=0.08, elastin=0.0, age=0.0,
                                        notch_shape="circle", notch_frac=0.25)]),
    "gpu": dict(W=6, z=[3.0, 3.2, 3.4, 3.6, 3.8],
                archs=["uniform", "random", "aligned", "aligned_nolock"],
                seeds=12, threads=8, relax=dict(max_rounds=40, iters=300),
                gammas=[0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3],
                fail=list(np.round(np.arange(0.02, 0.51, 0.02), 3)),
                cycles=5, cyc_steps=4, cyc_eps=0.10, axes=[0, 1], controls=["E1", "E2"],
                frac_modes=["tension", "shear", "mixed"],
                frac_deltas=list(np.round(np.arange(0.005, 0.21, 0.005), 4)),
                frac_conditions=[
                    dict(name="aligned_z3.4_notch25", arch="aligned", z=3.4,
                         lock_place="crossings", lock=0.08, elastin=0.0, age=0.0,
                         notch_shape="circle", notch_frac=0.25),
                    dict(name="uniform_z3.4_notch25", arch="uniform", z=3.4,
                         lock_place="crossings", lock=0.0, elastin=0.0, age=0.0,
                         notch_shape="circle", notch_frac=0.25),
                    dict(name="aligned_z3.4_unnotched", arch="aligned", z=3.4,
                         lock_place="crossings", lock=0.08, elastin=0.0, age=0.0,
                         notch_shape="none", notch_frac=0.0),
                    dict(name="aligned_z3.4_lockuniform", arch="aligned", z=3.4,
                         lock_place="random", lock=0.08, elastin=0.0, age=0.0,
                         notch_shape="circle", notch_frac=0.25),
                    dict(name="aligned_z3.4_age050", arch="aligned", z=3.4,
                         lock_place="crossings", lock=0.08, elastin=0.0, age=0.5,
                         notch_shape="circle", notch_frac=0.25),
                    dict(name="aligned_z3.4_elastin02", arch="aligned", z=3.4,
                         lock_place="crossings", lock=0.08, elastin=0.02, age=0.0,
                         notch_shape="circle", notch_frac=0.25),
                    dict(name="aligned_z2.8_notch25", arch="aligned", z=2.8,
                         lock_place="crossings", lock=0.08, elastin=0.0, age=0.0,
                         notch_shape="circle", notch_frac=0.25),
                    dict(name="aligned_z4.2_notch25", arch="aligned", z=4.2,
                         lock_place="crossings", lock=0.08, elastin=0.0, age=0.0,
                         notch_shape="circle", notch_frac=0.25)]),
}


def make_specs(lat, arch, z, seeds, **over):
    from oxt.network3d import Design3D, build_network3d

    specs, infos = [], []
    for s in seeds:
        rng = np.random.default_rng([int(s), ARCH_CODE[arch], int(round(z * 100))])
        d = dict(z=z, arch=arch, amp=0.5, lock=ARCH_LOCK[arch], lock_place="crossings")
        d.update(over)
        spec, info = build_network3d(lat, Design3D(**d), rng)
        specs.append(spec)
        infos.append(info)
    return specs, infos


def curve_metrics(strains, res):
    """Failure-curve resilience metrics per system (same definitions as topo_opt / run_phase)."""
    sig, broken = res["sig"], res["broken"]
    peak = sig.max(1)
    i_peak = sig.argmax(1)
    drops = np.maximum(0, np.diff(sig, axis=1)).max(1) if sig.shape[1] > 1 else np.zeros(len(sig))
    tough = _trap(sig, np.asarray(strains)[None, :], axis=1)
    return dict(peak_stress=peak, strain_at_peak=np.asarray(strains)[i_peak],
                failure_strain=res["first"], toughness=tough,
                max_drop=drops / np.maximum(peak, 1e-30),
                residual_stress=sig[:, -1], broken_total=broken.sum(1))


def linear_moduli(lat, specs, device, relax_kw):
    """G, Cx, Cy, Cz per system via the exact Hessian (fast near the rigidity onset)."""
    from oxt.network3d import hessian_moduli

    out = {k: np.zeros(len(specs)) for k in ("G", "Cx", "Cy", "Cz")}
    for i, sp in enumerate(specs):
        m = hessian_moduli(lat, sp, device=device)
        for k in out:
            out[k][i] = m[k]
    return out


# --------------------------------------------------------------------------------------------------
# Stage A: architecture matrix
# --------------------------------------------------------------------------------------------------
def evaluate_cell(lat, arch, z, seeds, P, device, control, g_target=None, e1_mod=None):
    """One (architecture, z) cell: B = len(seeds) systems evaluated together.

    control = 'E1': matched microscopic fibre properties (Col I parameters everywhere).
    control = 'E2': matched initial bulk stiffness - every stiffness rescaled by
    g_target / G_i (E1's exact Hessian G of the same realization) so each specimen's linear
    shear modulus equals g_target exactly.  The energy is linear in all stiffnesses, so the
    equilibrium and strains are unchanged and every modulus scales by exactly s (verified
    in --validate); no second Hessian pass is needed."""
    from oxt.network3d import Batch3D, scale_stiffness, stress_concentration, matched_stiffness_scale

    t0 = time.time()
    specs, infos = make_specs(lat, arch, z, seeds)
    scale = np.ones(len(seeds))
    if control == "E2":
        if e1_mod is None:
            raise ValueError("E2 needs e1_mod (the E1 Hessian moduli of the same seeds)")
        scale = np.asarray([matched_stiffness_scale(g, g_target) for g in e1_mod["G"]])
        specs = [scale_stiffness(sp, float(s)) for sp, s in zip(specs, scale)]
        mod = linear_moduli(lat, specs, device, P["relax"])
        if not np.allclose(mod["G"],g_target,rtol=2e-5,atol=0.):
            raise RuntimeError("fresh Hessian failed matched-stiffness verification")
    else:
        mod = linear_moduli(lat, specs, device, P["relax"])
    rows, cyc_rows, curves = [], [], {}
    for ax in P["axes"]:
        bf = Batch3D(lat, specs, device=device, relax_kw=P["relax"])
        res = bf.failure_curve(P["fail"], axis=ax)
        cm = curve_metrics(P["fail"], res)
        curves[f"sig_{arch}_z{z}_c{control}_ax{ax}"] = res["sig"]
        curves[f"broken_{arch}_z{z}_c{control}_ax{ax}"] = res["broken"]
        for i, s in enumerate(seeds):
            conc = stress_concentration(res["t_peak"][i])
            rows.append(dict(arch=arch, z_target=z, z_realized=infos[i]["z_realized"],
                             z_active=infos[i]["z_active"], control=control, axis=ax, seed=int(s),
                             scale=float(scale[i]), G=float(mod["G"][i]), Cx=float(mod["Cx"][i]),
                             Cy=float(mod["Cy"][i]), Cz=float(mod["Cz"][i]),
                             n_alive=infos[i]["n_alive"], n_lock=infos[i]["n_lock"],
                             **{k: float(v[i]) for k, v in cm.items()}, **conc))
        del bf
    bc = Batch3D(lat, specs, device=device, relax_kw=P["relax"])
    cyc = bc.cyclic(P["cyc_eps"], P["cycles"], P["cyc_steps"], axis=0)
    curves[f"cyclic_peak_{arch}_z{z}_c{control}"] = cyc["peak"]
    curves[f"cyclic_diss_{arch}_z{z}_c{control}"] = cyc["diss"]
    for i, s in enumerate(seeds):
        for c in range(P["cycles"]):
            cyc_rows.append(dict(arch=arch, z_target=z, control=control, seed=int(s), cycle=c,
                                 peak_stress=float(cyc["peak"][i, c]),
                                 work_load=float(cyc["w_load"][i, c]),
                                 work_unload=float(cyc["w_unload"][i, c]),
                                 dissipated=float(cyc["diss"][i, c]),
                                 broken_cum=int(cyc["broken"][i, c]),
                                 residual_stress=float(cyc["residual"][i, c])))
    del bc
    bs = Batch3D(lat, specs, device=device, relax_kw=P["relax"])
    curves[f"shear_{arch}_z{z}_c{control}"] = bs.shear_curve(P["gammas"])
    seconds = time.time() - t0
    for r in rows:
        r["seconds"] = seconds
    print(f"[{arch} z={z} {control}] G mean={np.mean(mod['G']):.3e} "
          f"spread [{np.min(mod['G']):.3e}, {np.max(mod['G']):.3e}] "
          f"({seconds:.0f}s, {len(rows)} rows)", flush=True)
    return rows, cyc_rows, curves


# --------------------------------------------------------------------------------------------------
# Stage B: fracture pipeline (cohesive-law extraction)
# --------------------------------------------------------------------------------------------------
def cohesive_metrics(res):
    """Per-system cohesive-law metrics from a traction-separation curve Teff(delta)."""
    d, T = res["deltas"], res["Teff"]
    peak = T.max(1)
    i_peak = T.argmax(1)
    Gc = _trap(T, d[None, :], axis=1)                 # work of separation to delta_max
    df = np.full_like(peak, d[-1])
    cens = np.zeros(len(peak), bool)
    for i in range(len(peak)):
        after = np.flatnonzero((d >= d[i_peak[i]]) & (T[i] <= 0.05 * peak[i]))
        if after.size:
            df[i] = d[after[0]]
        else:
            cens[i] = True
    Gc_f = np.array([_trap(T[i, :np.searchsorted(d, df[i]) + 1],
                           d[:np.searchsorted(d, df[i]) + 1]) for i in range(len(peak))])
    return dict(T_peak=peak, delta_f=df, Gc=Gc, Gc_to_f=Gc_f, delta_censored=cens,
                first_rupture=res["first"], broken_total=res["broken"][:, -1],
                locks_broken_total=res["locks_broken"][:, -1])


def _agg(vals):
    v = np.asarray(vals, float)
    return dict(mean=float(v.mean()), std=float(v.std()), min=float(v.min()),
                max=float(v.max()), n=int(v.size))


def evaluate_fracture_condition(lat, cond, P, device, out_dir):
    """Cohesive-law extraction for one condition x all modes x all seeds -> one JSON per mode.

    Output contract (downstream MOOSE cohesive-zone FEM adapter, built by another agent):
    per (condition, mode) JSON with the dimensionless T(delta) curve per realization, the
    extracted law (T_peak, delta_f, G_c) with uncertainty across >= 8 realizations, and the
    Calibration3D fields needed to convert to SI later."""
    from oxt.network3d import Batch3D, Calibration3D, stress_concentration

    cal = Calibration3D()  # placeholder (dimensionless); see DESIGN.md for required calibration
    seeds = list(range(P["seeds"]))
    arch = cond["arch"]
    specs, infos = make_specs(lat, arch, cond["z"], seeds,
                              lock=cond.get("lock", ARCH_LOCK[arch]),
                              lock_place=cond.get("lock_place", "crossings"),
                              elastin=cond.get("elastin", 0.0), age=cond.get("age", 0.0),
                              notch_shape=cond.get("notch_shape", "none"),
                              notch_frac=cond.get("notch_frac", 0.0))
    for mode in P["frac_modes"]:
        t0 = time.time()
        b = Batch3D(lat, specs, device=device, crack_axis=0, relax_kw=P["relax"])
        res = b.cohesive_curve(P["frac_deltas"], mode=mode, mix=cond.get("mix", 1.0))
        cm = cohesive_metrics(res)
        per_seed = []
        for i, s in enumerate(seeds):
            per_seed.append(dict(
                seed=int(s), deltas=res["deltas"].tolist(),
                traction_T=res["T"][i].tolist(), traction_eff=res["Teff"][i].tolist(),
                broken=res["broken"][i].tolist(), locks_broken=res["locks_broken"][i].tolist(),
                T_peak=float(cm["T_peak"][i]), delta_f=float(cm["delta_f"][i]),
                Gc=float(cm["Gc"][i]), Gc_to_f=float(cm["Gc_to_f"][i]),
                delta_censored=bool(cm["delta_censored"][i]),
                first_rupture=None if np.isnan(cm["first_rupture"][i]) else float(cm["first_rupture"][i]),
                z_realized=infos[i]["z_realized"], n_notch=infos[i]["n_notch"],
                stress_concentration=stress_concentration(res["t_peak_field"][i])))
        law = dict(condition=cond["name"], mode=mode, mix_ratio=cond.get("mix", 1.0),
                   crack_axis=0, notch_shape=cond.get("notch_shape", "none"),
                   notch_frac=cond.get("notch_frac", 0.0), arch=arch, z_target=cond["z"],
                   n_realizations=len(seeds),
                   model_units="dimensionless (bond length 1, fibre stiffness mu=1)",
                   calibration=dict(length_scale_m=cal.length_scale,
                                    force_scale_N=cal.force_scale,
                                    thickness_m=cal.thickness,
                                    traction_SI="T * force_scale / length_scale**2 [Pa]",
                                    Gc_SI="Gc * force_scale / length_scale [J/m^2]",
                                    status="PLACEHOLDER - calibration required, see DESIGN.md"),
                   aggregates={k: _agg(v) for k, v in
                               dict(T_peak=cm["T_peak"], delta_f=cm["delta_f"], Gc=cm["Gc"],
                                    Gc_to_f=cm["Gc_to_f"]).items()},
                   realizations=per_seed)
        fdir = out_dir / "fracture_laws"
        fdir.mkdir(parents=True, exist_ok=True)
        (fdir / f"{cond['name']}__{mode}.json").write_text(json.dumps(law, indent=2))
        print(f"[fracture {cond['name']} {mode}] T_peak={np.mean(cm['T_peak']):.3e} "
              f"delta_f={np.mean(cm['delta_f']):.3f} Gc={np.mean(cm['Gc']):.3e} "
              f"({time.time() - t0:.0f}s, {len(seeds)} seeds)", flush=True)
        del b


# --------------------------------------------------------------------------------------------------
# validation (generator sanity, Step 2 of the plan)
# --------------------------------------------------------------------------------------------------
def validate_generator(P, device, out_dir):
    from oxt.network3d import (Batch3D, Calibration3D, Design3D, Lattice3D, SystemSpec3D,
                               build_network3d, hessian_moduli, scale_stiffness)
    import torch

    torch.set_num_threads(P["threads"])
    rep = {}
    lat = Lattice3D(P["W"])
    d = lat.X[lat.bj] - lat.X[lat.bi] + lat.shift
    rep["bonds_unit_length"] = bool(np.allclose(np.linalg.norm(d, axis=1), 1.0, atol=1e-12))
    rep["volume"] = lat.volume

    # 1. undiluted FCC = Bravais lattice -> moduli equal the Born values exactly
    full = SystemSpec3D(alive=np.ones(lat.Nb, bool), mu=np.ones(lat.Nb), kappa_b=np.ones(lat.Nb),
                        eps_r=np.full(lat.Nb, 9.0), rigid_node=np.zeros(lat.N), kappa=0.0,
                        mu_el=0.0, k_gag=0.0)
    m = hessian_moduli(lat, full, device=device)
    rep["full_G"], rep["full_G_analytic"] = m["G"], 1 / math.sqrt(2)
    rep["full_Cx"], rep["full_C_analytic"] = m["Cx"], math.sqrt(2)
    rep["full_lattice_ok"] = bool(abs(m["G"] / (1 / math.sqrt(2)) - 1) < 1e-6
                                   and abs(m["Cx"] / math.sqrt(2) - 1) < 1e-6)

    # 2. isostatic onset: below z=6 central-force networks are floppy; bending stabilises them
    onset = {}
    for kap in (0.0, 3e-3):
        gs = []
        for s in range(4):
            rng = np.random.default_rng([s, 2, 340])
            spec, info = build_network3d(lat, Design3D(z=3.4, arch="uniform", kappa=kap), rng)
            gs.append(hessian_moduli(lat, spec, device=device)["G"])
        onset[f"G_kappa{kap:g}"] = float(np.mean(gs))
    onset["bending_stabilises"] = bool(onset["G_kappa0.003"] > 10 * max(onset["G_kappa0"], 1e-12))
    above = []
    for s in range(4):
        rng = np.random.default_rng([s, 2, 800])
        spec, info = build_network3d(lat, Design3D(z=8.0, arch="uniform", kappa=0.0), rng)
        above.append(hessian_moduli(lat, spec, device=device)["G"])
    onset["G_z8_kappa0"] = float(np.mean(above))
    onset["above_isostatic_stiff"] = bool(np.mean(above) > 10 * onset["G_kappa0.003"])
    rep["onset"] = onset

    # 3. z statistics vs requested, >= 8 seeds per architecture (W >= 4: at W=3 the
    #    one-cut-per-fibre-line rule biases z upward)
    zstats = {}
    zlat = Lattice3D(max(P["W"], 4))
    for arch in ARCH_CODE:
        zs, za = [], []
        for s in range(8):
            rng = np.random.default_rng([s, ARCH_CODE[arch], 340])
            spec, info = build_network3d(zlat, Design3D(z=3.4, arch=arch, amp=0.5,
                                                        lock=ARCH_LOCK[arch]), rng)
            zs.append(info["z_realized"])
            za.append(info["z_active"])
        zstats[arch] = dict(mean=float(np.mean(zs)), std=float(np.std(zs)),
                            min=float(np.min(zs)), max=float(np.max(zs)),
                            z_active_mean=float(np.mean(za)))
    rep["z_stats_target_3.4"] = zstats
    rep["z_stats_ok"] = bool(all(abs(v["mean"] - 3.4) < 0.15 and v["std"] < 0.2
                                 for v in zstats.values()))

    # 4. energy conservation: autograd gradient vs central finite differences
    rng = np.random.default_rng(7)
    spec, info = build_network3d(lat, Design3D(z=3.4, arch="aligned", lock=0.08), rng)
    b = Batch3D(lat, [spec], device=device)
    F = torch.eye(3, dtype=torch.float64)[None] * 1.03
    F[0, 0, 1] = 0.02
    x = (b.X[None] @ F.transpose(1, 2)).clone() + 0.05 * torch.randn(1, lat.N, 3, dtype=torch.float64)
    x = x.requires_grad_(True)
    b.energy(x, F).backward()
    g = x.grad.numpy().ravel()
    gn = np.zeros_like(g)
    h = 1e-6
    ps = np.random.default_rng(0).choice(g.size, 25, replace=False)
    for p in ps:
        xp = x.detach().clone(); xp.reshape(-1)[p] += h
        xm = x.detach().clone(); xm.reshape(-1)[p] -= h
        gn[p] = (float(b.energy(xp, F)) - float(b.energy(xm, F))) / (2 * h)
    # compare ONLY on the sampled coordinates: gn is zero elsewhere by construction
    # (pre-2026-10-31 the max ran over all coordinates, which falsely failed this check)
    err = float(np.max(np.abs(g[ps] - gn[ps])) / max(np.max(np.abs(gn[ps])), 1e-12))
    rep["energy_grad_max_rel_err"] = err
    rep["energy_conservation_ok"] = bool(err < 1e-6)

    # 5. matched-bulk-stiffness rescaling is exact (energy linear in all stiffnesses)
    spec2 = scale_stiffness(spec, 2.3)
    m1 = hessian_moduli(lat, spec, device=device)
    m2 = hessian_moduli(lat, spec2, device=device)
    rep["rescale_G_ratio"] = float(m2["G"] / m1["G"])
    rep["rescale_exact"] = bool(abs(m2["G"] / m1["G"] / 2.3 - 1) < 1e-8)

    # 6. irreversibility + crack history: bond and crosslink failure never heals, and the
    #    stress at a fixed strain cannot increase after unload/reload with damage in between
    ir = {}
    bc = Batch3D(lat, [spec], device=device, relax_kw=P["relax"])
    F1 = bc.F_stretch(0.08, 0)
    bc.move_affine(bc.F0, F1)
    bc.relax(F1)
    alive_hist, lock_hist = [int(bc.alive.sum())], [int(bc.lock_alive.sum())]
    for _ in range(6):
        k = bc.rupture(F1) + bc.rupture_locks(F1)
        alive_hist.append(int(bc.alive.sum()))
        lock_hist.append(int(bc.lock_alive.sum()))
        if int(k.sum()) == 0:
            break
        bc.relax(F1)
    ir["alive_monotone"] = bool(all(a2 <= a1 for a1, a2 in zip(alive_hist, alive_hist[1:])))
    ir["locks_monotone"] = bool(all(a2 <= a1 for a1, a2 in zip(lock_hist, lock_hist[1:])))
    ir["alive_hist"], ir["lock_hist"] = alive_hist, lock_hist
    # reload the same strain: with permanent damage the response must be softer or equal
    s_dmg = float(bc.stress(F1)[0, 0, 0])
    bc2 = Batch3D(lat, [spec], device=device, relax_kw=P["relax"])
    bc2.move_affine(bc2.F0, F1)
    bc2.relax(F1)
    ir["undamaged_stress"], ir["damaged_stress"] = float(bc2.stress(F1)[0, 0, 0]), s_dmg
    ir["damage_softens"] = bool(s_dmg <= float(bc2.stress(F1)[0, 0, 0]) + 1e-12)
    rep["irreversibility"] = ir

    # 7. cohesive sanity: unnotched full ligament under tension -> T rises, ruptures, decays
    rng2 = np.random.default_rng(1)
    fcond = P["frac_conditions"][0] if P.get("frac_conditions") else dict(
        name="sanity", arch="aligned", z=3.4, lock=0.08)
    fspec, finfo = make_specs(lat, fcond["arch"], fcond["z"], [0],
                              lock=fcond.get("lock", 0.08),
                              notch_shape=fcond.get("notch_shape", "none"),
                              notch_frac=fcond.get("notch_frac", 0.0))
    bf = Batch3D(lat, fspec, device=device, crack_axis=0, relax_kw=P["relax"])
    # widen the opening range so fibre rupture and traction decay are actually visible
    sanity_deltas = list(np.round(np.arange(0.02, 0.34, 0.04), 4))
    res = bf.cohesive_curve(sanity_deltas, mode="tension")
    te = res["Teff"][0]
    rep["cohesive_sanity"] = dict(T_curve=te.tolist(), deltas=res["deltas"].tolist(),
                                  peak=float(te.max()), broken=int(res["broken"][0].sum()),
                                  T_rises_then_falls=bool(te.argmax() < len(te) - 1
                                                          and te.min() < te.max()),
                                  positive_Gc=bool(te.max() > 0))

    (out_dir / "validation.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2), flush=True)
    return rep


# --------------------------------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------------------------------
def run(P, device, out_dir, profile=""):
    import torch
    from oxt.network3d import Lattice3D

    torch.set_num_threads(P["threads"])
    lat = Lattice3D(P["W"])
    print(f"lattice W={P['W']}: {lat.N} nodes, {lat.Nb} bonds, {lat.n_lines} fibre lines, "
          f"V={lat.volume:.1f}", flush=True)
    t0 = time.time()
    rows, cyc_rows, curves = [], [], {}
    e1_cache = {}
    for z in P["z"]:
        g_target = None
        for control in P["controls"]:
            for arch in P["archs"]:
                r, c, cu = evaluate_cell(lat, arch, z, list(range(P["seeds"])), P, device,
                                         control, g_target, e1_mod=e1_cache.get((z, arch)))
                rows += r
                cyc_rows += c
                curves.update(cu)
                if control == "E1":
                    # cache E1's exact moduli: E2 rescales them linearly (no second Hessian)
                    mod_e1 = {k: [r0[k] for r0 in r if r0["axis"] == P["axes"][0]]
                              for k in ("G", "Cx", "Cy", "Cz")}
                    e1_cache[(z, arch)] = mod_e1
                    g_row = [r["G"] for r in rows if r["z_target"] == z
                             and r["arch"] == "uniform" and r["control"] == "E1"]
                    g_target = float(np.median(g_row))
                    print(f"[z={z}] E2 bulk-stiffness target G = {g_target:.4e} "
                          f"(uniform median over {len(g_row)} seeds)", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "realizations.csv", index=False)
    pd.DataFrame(cyc_rows).to_csv(out_dir / "cyclic.csv", index=False)
    np.savez_compressed(out_dir / "curves.npz",
                        gammas=np.asarray(P["gammas"]), fail=np.asarray(P["fail"]),
                        **curves)
    agg = df.groupby(["arch", "z_target", "control", "axis"]).agg(["mean", "std", "min", "max"])
    agg.round(6).to_csv(out_dir / "aggregate.csv")
    print(df.groupby(["arch", "z_target", "control"])[
        ["G", "peak_stress", "toughness", "failure_strain", "max_share"]].agg(["mean", "std"])
        .round(6), flush=True)

    # Stage B: fracture pipeline
    for cond in P["frac_conditions"]:
        evaluate_fracture_condition(lat, cond, P, device, out_dir)

    (out_dir / "summary.json").write_text(json.dumps(
        dict(profile=profile, W=P["W"], seeds=P["seeds"], z=P["z"], archs=P["archs"],
             controls=P["controls"], axes=P["axes"], cycles=P["cycles"], cyc_eps=P["cyc_eps"],
             relax=P["relax"], frac_conditions=[c["name"] for c in P["frac_conditions"]],
             frac_modes=P["frac_modes"], device=device,
             seconds_total=round(time.time() - t0, 1)), indent=2))
    print(f"total {time.time() - t0:.0f}s, {len(df)} rows -> {out_dir}", flush=True)
    return df


def main():
    ap = argparse.ArgumentParser(description="3D FCC architecture + fracture validation")
    ap.add_argument("--profile", default="smoke", choices=list(PROFILES))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=None)
    ap.add_argument("--validate", action="store_true", help="generator validation only")
    ap.add_argument("--seeds", type=int, default=None, help="override seeds (>= 8 for real runs)")
    args = ap.parse_args()
    P = dict(PROFILES[args.profile])
    if args.seeds is not None:
        P["seeds"] = args.seeds
    out_dir = Path(args.out) if args.out else OUT / args.profile
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.validate:
        validate_generator(P, args.device, out_dir)
        return
    run(P, args.device, out_dir, profile=args.profile)


if __name__ == "__main__":
    main()
