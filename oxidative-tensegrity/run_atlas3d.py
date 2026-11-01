#!/usr/bin/env python3
"""3D collagen architecture-atlas screening: 45 conditions x 8 paired seeds (360 sims).

Families (connectivity-matched, same chemistry, same box volume V = 2*sqrt(2)*W^3,
same node count N = 4*W^3 for the FCC families; the stochastic family reports its
node-count match instead of tuning it away):
  diluted  oxt.network3d Design3D(family="diluted")  - random dilution + ONE CUT PER
           FIBRE LINE (finite fibres) on the FCC lattice
  phantom  oxt.network3d Design3D(family="phantom")  - pure random bond removal, no
           line cuts (uncut-dilution ablation; see DESIGN.md for the concurrent
           architecture3d.phantom_fcc binary-junction generator, not used here)
  fiber    oxt.fiber3d build_fiber_network           - N_fib independent persistent
           random walks, crosslinked at close encounters, as-grown stress-free reference

Matrix per family (12 architecture conditions at z = 3.4 + 3 z-probes):
  orientation      diluted/phantom: arch uniform | aligned amp 0.25 | aligned amp 0.5
                   fiber:           p_align 0.0 | 0.35 | 0.7
  curvature        diluted/phantom: curve_lattice amp 0 | 0.15 (same curved lattice for
                   every realization of a condition)
                   fiber:           curve_sigma 0 | 0.3
  crosslink dist.  diluted/phantom: lock_place crossings | random
                   fiber:           xlink_dist clustered | random
  z-probes         center architecture (weak orientation, no curvature, clustered
                   crosslinks) at z = 3.0 / 3.8 / 4.2
Chemistry everywhere: Col I mu = 1, kappa = 3e-3, kx = 2e-3, eps_r = 0.10, k_gag = 1e-6,
lock fraction 0.08, lock_fail_rad 0.5.  Seeds 0..7 are shared across ALL conditions
(paired-seed comparisons); the rng stream of a realization is default_rng([seed,
condition_index]) so a seed names the same nominal realization everywhere.

Controls:
  E1  fixed microscopic material - the Col I parameters above, in-sim.
  E2  matched initial bulk stiffness - EXACT post-hoc, no new sims: the energy is linear
      in every stiffness, so the equilibrium path and all strains are unchanged when all
      stiffnesses are rescaled by s = g_target / G_i and every stress/traction/energy
      scales by exactly s (verified in --validate for both families against in-sim
      rescaled Hessians).  g_target = median E1 G of the diluted baseline condition
      (iso orientation, no curvature, clustered locks, z = 3.4, W as the profile).

Protocols per realization (batched over the 8 seeds of a condition):
  exact-Hessian anisotropic moduli (E1), laterally-constrained uniaxial failure curve
  with irreversible bond + lock rupture (axis 0), cyclic loading (hysteresis, residual
  stress, recoil = w_unload/w_load), and cohesive traction-separation T(delta) for
  mode I (tension) and mode II (shear) on the internal crack plane (notch circle 0.25
  ahead of it for the FCC families; the fiber family notches in FiberBatch).  Every
  (condition, mode, seed) curve is written as a schema oxt-fracture-bridge/curve@1 JSON
  (fracture_bridge/README.md contract; extra keys are tolerated by the adapter).

Matching failures (|z_realized - z_target| > 0.15, fiber crosslink-candidate shortage,
node-count mismatch > 5%) are reported per condition in matching_report.json, excluded
from the simulation batch, and enter the Pareto analysis as violations (Deb constraint
domination, topo_opt.dominates).

Pareto: nondominated_sort over per-condition means of [strength = peak stress,
G_c (mode I), recoil], all maximized (negated for the minimization front), with seed
spread (sd) reported and a robust front on mean - sd.

Finite-size add-on: the diluted center condition re-run at W = 3 / 5 / 6 (8 seeds
each, 24 sims; W = 4 is the screening member).

  python3 run_atlas3d.py --profile smoke --device cuda     # plumbing check, minutes
  python3 run_atlas3d.py --validate --device cuda          # generator/E2/Pareto checks
  python3 run_atlas3d.py --profile full  --device cuda      # the 360-sim screening
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
import warnings
from pathlib import Path

import numpy as np
import torch

from oxt.normalization import assess_e2, derive_e2_rows, matched_stiffness_scale, select_e2_target, derive_e2_curve

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "atlas3d"
SQ2 = math.sqrt(2.0)

CHEM = dict(mu=1.0, kappa=3e-3, kx=2e-3, eps_r=0.10, k_gag=1e-6,
            lock=0.08, lock_fail_rad=0.5)
Z_MATCH = 3.4
Z_PROBES = [3.0, 3.8, 4.2]
Z_TOL = 0.15
NOTCH = dict(notch_shape="circle", notch_frac=0.25)

ORIENT_FCC = [("iso", "uniform", 0.0), ("weak", "aligned", 0.25), ("strong", "aligned", 0.5)]
ORIENT_FIB = [("iso", 0.0), ("weak", 0.35), ("strong", 0.7)]
CURVE_FCC = [("c0", 0.0), ("c015", 0.15)]
CURVE_FIB = [("c0", 0.0), ("c03", 0.3)]
XDIST_FCC = [("xclu", "crossings"), ("xrand", "random")]
XDIST_FIB = [("xclu", "clustered"), ("xrand", "random")]
FAMILIES = ["diluted", "phantom", "fiber"]
FIBER_DESIGN_BASE = dict(n_fib=32, n_seg=7)   # 32*(7+1) = 256 = 4*W^3 at W = 4
MODES = [("tension", "I"), ("shear", "II")]

PROFILES = {
    # plumbing smoke: 3 conditions (one per family incl. the g_target baseline),
    # 2 seeds, tiny protocol grids - minutes on the H100
    "smoke": dict(W=4, seeds=[0, 1], threads=8, relax=dict(max_rounds=8, iters=120, strict=False),
                  fail=[0.04, 0.12, 0.20], cycles=1, cyc_steps=2, cyc_eps=0.10,
                  frac_deltas=[0.02, 0.05, 0.10, 0.16], conditions=[0, 15, 30],
                  finite_W=[]),
    # the screening: 45 conditions x 8 paired seeds + finite-size add-on
    "full": dict(W=4, seeds=list(range(8)), threads=8, relax=dict(max_rounds=30, iters=250, strict=False),
                 fail=list(np.round(np.arange(0.02, 0.50, 0.04), 3)),
                 cycles=4, cyc_steps=3, cyc_eps=0.10,
                 frac_deltas=list(np.round(np.arange(0.01, 0.31, 0.01), 4)),
                 conditions=None, finite_W=[3, 5, 6]),
}


# --------------------------------------------------------------------------- #
# condition matrix (stable order -> condition_index seeds the rng streams)
# --------------------------------------------------------------------------- #
def _fcc_cond(idx, family, oname, arch, amp, cname, curve_amp, xname, lock_place, z):
    return dict(idx=idx, kind="fcc", family=family, orient=oname, curve=cname,
                xdist=xname, arch=arch, amp=amp, curve_amp=curve_amp,
                lock_place=lock_place, z=z,
                name=f"{family}-{oname}-{cname}-{xname}" + ("" if z == Z_MATCH
                                                            else f"-z{z:g}"))


def _fib_cond(idx, oname, p_align, cname, curve_sigma, xname, xlink_dist, z):
    return dict(idx=idx, kind="fiber", family="fiber", orient=oname, curve=cname,
                xdist=xname, p_align=p_align, curve_sigma=curve_sigma,
                xlink_dist=xlink_dist, z=z,
                name=f"fiber-{oname}-{cname}-{xname}" + ("" if z == Z_MATCH
                                                         else f"-z{z:g}"))


def build_conditions():
    conds = []
    idx = 0
    for family in ("diluted", "phantom"):
        for oname, arch, amp in ORIENT_FCC:
            for cname, curve_amp in CURVE_FCC:
                for xname, lock_place in XDIST_FCC:
                    conds.append(_fcc_cond(idx, family, oname, arch, amp, cname,
                                           curve_amp, xname, lock_place, Z_MATCH))
                    idx += 1
        # z-probes at the center architecture: weak orientation, no curvature, clustered
        for z in Z_PROBES:
            conds.append(_fcc_cond(idx, family, "weak", "aligned", 0.25, "c0", 0.0,
                                   "xclu", "crossings", z))
            idx += 1
    for oname, p_align in ORIENT_FIB:
        for cname, curve_sigma in CURVE_FIB:
            for xname, xlink_dist in XDIST_FIB:
                conds.append(_fib_cond(idx, oname, p_align, cname, curve_sigma,
                                       xname, xlink_dist, Z_MATCH))
                idx += 1
    for z in Z_PROBES:
        conds.append(_fib_cond(idx, "weak", 0.35, "c0", 0.0, "xclu", "clustered", z))
        idx += 1
    assert len(conds) == 45, len(conds)
    return conds


BASELINE_IDX = 0          # diluted-iso-c0-xclu at z=3.4: defines g_target
FINITE_COND_IDX = 4       # diluted center architecture (weak, c0, xclu) at z=3.4


# --------------------------------------------------------------------------- #
# generators
# --------------------------------------------------------------------------- #
_lat_cache = {}


def get_lattice(W, curve_amp):
    key = (W, curve_amp)
    if key not in _lat_cache:
        from oxt.network3d import Lattice3D, curve_lattice
        lat = Lattice3D(W)
        if curve_amp > 0:
            # the waviness is an architecture property: one fixed curved lattice per
            # (W, amplitude); realization variability comes from the dilution rng
            lat = curve_lattice(lat, curve_amp, np.random.default_rng([W, 77, int(curve_amp * 1000)]))
        _lat_cache[key] = lat
    return _lat_cache[key]


def fcc_design(cond):
    from oxt.network3d import Design3D
    return Design3D(z=cond["z"], arch=cond["arch"], amp=cond["amp"],
                    family=cond["family"], lock=CHEM["lock"],
                    lock_place=cond["lock_place"], mu=CHEM["mu"], kappa=CHEM["kappa"],
                    kx=CHEM["kx"], eps_r=CHEM["eps_r"], k_gag=CHEM["k_gag"],
                    lock_fail_rad=CHEM["lock_fail_rad"], crack_axis=0, **NOTCH)


def fiber_design(cond, over=None):
    from oxt.fiber3d import FiberDesign
    d = dict(FIBER_DESIGN_BASE, p_align=cond["p_align"], curve_sigma=cond["curve_sigma"],
             z=cond["z"], lock=CHEM["lock"], lock_place="crossings",
             xlink_dist=cond["xlink_dist"], mu=CHEM["mu"], kappa=CHEM["kappa"],
             kx=CHEM["kx"], eps_r=CHEM["eps_r"], k_gag=CHEM["k_gag"],
             lock_fail_rad=CHEM["lock_fail_rad"], crack_axis=0, **NOTCH)
    d.update(over or {})
    return FiberDesign(**d)


def build_realizations(cond, seeds, W, n_target):
    """Build one realization per seed; return (items, failures).

    items: dicts with everything the battery needs; failures: dicts with the matching
    failure reason per seed."""
    items, failures = [], []
    with warnings.catch_warnings():
        # family="phantom" is the documented uncut-dilution ablation (a concurrent
        # commissioning note points at architecture3d.phantom_fcc; not used here)
        warnings.filterwarnings("ignore", message="Legacy family='phantom'")
        for s in seeds:
            rng = np.random.default_rng([int(s), cond["idx"], 101])
            if cond["kind"] == "fcc":
                lat = get_lattice(W, cond["curve_amp"])
                from oxt.network3d import build_network3d
                spec, info = build_network3d(lat, fcc_design(cond), rng)
                z_pre = info["z_realized"] + 2.0 * info["n_notch"] / max(lat.N, 1)
                item = dict(seed=int(s), spec=spec, info=info, z_prenotch=float(z_pre),
                            z_realized=float(info["z_realized"]),
                            n_notch=int(info["n_notch"]), n_lock=int(info["n_lock"]),
                            n_alive=int(info["n_alive"]), node_match=None)
            else:
                from oxt.fiber3d import build_fiber_network
                box_L = (2 * SQ2 * W ** 3) ** (1 / 3)
                net = build_fiber_network(fiber_design(cond), rng, box_L, n_target)
                if not net.get("ok", False):
                    failures.append(dict(seed=int(s), reason=net.get("reason", "build failed"),
                                          z_target=cond["z"]))
                    continue
                info = net["info"]
                item = dict(seed=int(s), net=net, z_prenotch=float(info["z_realized"]),
                            z_realized=float(info["z_realized"]), n_notch=None,
                            n_lock=int(info["n_lock"]), n_alive=int(info["Nb"]),
                            node_match=float(info["node_match"]))
            if abs(item["z_prenotch"] - cond["z"]) > Z_TOL:
                failures.append(dict(seed=int(s),
                                     reason=f"z_realized {item['z_prenotch']:.3f} vs target "
                                            f"{cond['z']} (tol {Z_TOL})",
                                     z_target=cond["z"]))
                continue
            if item["node_match"] is not None and item["node_match"] >= 0.05:
                failures.append(dict(seed=int(s),
                                     reason=f"node_match {item['node_match']:.3f} >= 0.05",
                                     z_target=cond["z"]))
                continue
            items.append(item)
    return items, failures


# --------------------------------------------------------------------------- #
# per-realization metrics
# --------------------------------------------------------------------------- #
def e1_moduli(cond, items, device):
    from oxt.network3d import hessian_moduli
    from oxt.fiber3d import fiber_hessian_moduli
    out = []
    if cond["kind"] == "fcc":
        lat = get_lattice(cond["_W"], cond["curve_amp"])
        for it in items:
            m = hessian_moduli(lat, it["spec"], device=device)
            out.append({k: float(m[k]) for k in ("G", "Cx", "Cy", "Cz")})
    else:
        for it in items:
            m = fiber_hessian_moduli(it["net"], device=device)
            out.append({k: float(m[k]) for k in ("G", "Gyz", "Gzx", "Cx", "Cy", "Cz")})
    return out


def run_battery(cond, items, P, device, out_dir):
    """Failure + cyclic + cohesive protocols for the batch of ok realizations.

    Returns (rows, cyc_rows, seconds).  rows are E1 dicts; the caller
    derives the E2 rows by stress rescaling (exact, energy linear in stiffnesses)."""
    from oxt.network3d import Batch3D, stress_concentration
    from oxt.fiber3d import FiberBatch
    from run_network3d import curve_metrics, cohesive_metrics

    t0 = time.time()
    seeds = [it["seed"] for it in items]
    relax = P["relax"]

    def new_batch(crack=False):
        if cond["kind"] == "fcc":
            lat = get_lattice(cond["_W"], cond["curve_amp"])
            kw = dict(crack_axis=0) if crack else {}
            return Batch3D(lat, [it["spec"] for it in items], device=device,
                           relax_kw=relax, **kw)
        return FiberBatch([it["net"] for it in items], device=device, relax_kw=relax)

    # ---- failure curve (axis 0) ------------------------------------------------
    b = new_batch()
    res = b.failure_curve(P["fail"], axis=0)
    cm = curve_metrics(P["fail"], res)
    fail_metrics = []
    for i, s in enumerate(seeds):
        conc = stress_concentration(res["t_peak"][i])
        fail_metrics.append(dict(peak_stress=float(cm["peak_stress"][i]),
                                 strain_at_peak=float(cm["strain_at_peak"][i]),
                                 failure_strain=None if np.isnan(cm["failure_strain"][i])
                                 else float(cm["failure_strain"][i]),
                                 toughness=float(cm["toughness"][i]),
                                 max_drop=float(cm["max_drop"][i]),
                                 residual_stress=float(cm["residual_stress"][i]),
                                 broken_total=int(cm["broken_total"][i]), **conc))
    del b

    # ---- cyclic -----------------------------------------------------------------
    b = new_batch()
    cyc = b.cyclic(P["cyc_eps"], P["cycles"], P["cyc_steps"], axis=0)
    cyc_rows, cyc_sum = [], []
    for i, s in enumerate(seeds):
        recoil = []
        for c in range(P["cycles"]):
            wu, wl = float(cyc["w_unload"][i, c]), float(cyc["w_load"][i, c])
            rec = wu / wl if abs(wl) > 1e-30 else float("nan")
            recoil.append(rec)
            cyc_rows.append(dict(cond=cond["name"], cond_idx=cond["idx"],
                                 family=cond["family"], kind=cond.get("kind2", "screen"),
                                 W=cond["_W"], z_target=cond["z"], seed=int(s), cycle=c,
                                 peak_stress=float(cyc["peak"][i, c]),
                                 work_load=float(cyc["w_load"][i, c]),
                                 work_unload=wu, dissipated=float(cyc["diss"][i, c]),
                                 broken_cum=int(cyc["broken"][i, c]),
                                 residual_stress=float(cyc["residual"][i, c]),
                                 recoil=rec))
        cyc_sum.append(dict(cyc_peak_mean=float(np.mean(cyc["peak"][i])),
                            cyc_diss_mean=float(np.mean(cyc["diss"][i])),
                            cyc_residual_mean=float(np.mean(cyc["residual"][i])),
                            cyc_recoil_mean=float(np.mean(recoil))))
    del b

    # ---- cohesive T(delta), modes I and II --------------------------------------
    coh = {m: dict() for m in MODES}
    b = new_batch(crack=True)
    for mode, mode_roman in MODES:
        res = b.cohesive_curve(P["frac_deltas"], mode=mode)
        coh[mode] = dict(res=res, metrics=cohesive_metrics(res), roman=mode_roman)
    del b

    seconds = time.time() - t0

    # ---- per-realization rows + fracture-bridge JSONs ---------------------------
    rows, curve_jsons = [], []
    for i, it in enumerate(items):
        row = dict(cond=cond["name"], cond_idx=cond["idx"], family=cond["family"],
                   orient=cond["orient"], curve=cond["curve"], xdist=cond["xdist"],
                   kind=cond.get("kind2", "screen"), W=cond["_W"], z_target=cond["z"],
                   seed=it["seed"], ok=True,
                   z_realized=it["z_realized"], z_prenotch=it["z_prenotch"],
                   node_match=it["node_match"], n_alive=it["n_alive"],
                   n_lock=it["n_lock"], n_notch=it["n_notch"])
        row.update({k: it["moduli"][k] for k in it["moduli"]})
        row.update(fail_metrics[i])
        row.update(cyc_sum[i])
        for mode, mode_roman in MODES:
            m = coh[mode]["metrics"]
            for k in ("T_peak", "delta_f", "Gc", "Gc_to_f", "delta_censored"):
                row[f"{k}_{mode_roman}"] = float(m[k][i])
            row[f"first_rupture_{mode_roman}"] = (None if np.isnan(m["first_rupture"][i])
                                                 else float(m["first_rupture"][i]))
            row[f"broken_{mode_roman}"] = int(m["broken_total"][i])
        row["seconds"] = seconds
        rows.append(row)

        # schema oxt-fracture-bridge/curve@1 JSON per (condition, mode, seed)
        for mode, mode_roman in MODES:
            res, m = coh[mode]["res"], coh[mode]["metrics"]
            dl = res["deltas"]
            te = res["Teff"][i]
            payload = dict(
                schema="oxt-fracture-bridge/curve@1",
                condition=cond["name"], mode=mode_roman, realization=it["seed"],
                units={"delta": "model (bond length = 1, dimensionless)",
                       "traction": "model (dimensionless, force/area with mu = 1)"},
                delta=[float(x) for x in dl], traction=[float(x) for x in te],
                # extras (tolerated by fracture_bridge.extract_cohesive):
                seed=it["seed"], family=cond["family"], z_target=cond["z"],
                z_realized=it["z_realized"],
                traction_vector=res["T"][i].tolist(),
                broken=res["broken"][i].tolist(), locks_broken=res["locks_broken"][i].tolist(),
                T_peak=float(m["T_peak"][i]), delta_f=float(m["delta_f"][i]),
                Gc=float(m["Gc"][i]), Gc_to_f=float(m["Gc_to_f"][i]),
                delta_censored=bool(m["delta_censored"][i]),
                first_rupture=(None if np.isnan(m["first_rupture"][i])
                               else float(m["first_rupture"][i])),
                stress_concentration=stress_concentration(res["t_peak_field"][i]),
                calibration=dict(
                    status="PLACEHOLDER - dimensionless model; see "
                           "experiments/network3d-atlas-20261031/DESIGN.md",
                    traction_SI="T * force_scale / length_scale**2 [Pa]",
                    Gc_SI="Gc * force_scale / length_scale [J/m^2]"),
            )
            payload["E2_matched_bulk"] = derive_e2_curve(
                te.tolist(), float(m["T_peak"][i]), float(m["Gc"][i]),
                initial=it["moduli"]["G"], target=it.get("e2_target"), e1_ok=row["ok"])
            fdir = out_dir / "fracture_laws" / cond["name"] / f"mode_{mode_roman}"
            fdir.mkdir(parents=True, exist_ok=True)
            fp = fdir / f"seed{it['seed']}.json"
            fp.write_text(json.dumps(payload, indent=1))
            curve_jsons.append(str(fp.relative_to(out_dir)))
    return rows, cyc_rows, seconds


# quantities that rescale EXACTLY under a uniform stiffness rescaling s
SCALED = ["G", "Cx", "Cy", "Cz", "Gyz", "Gzx", "peak_stress", "toughness",
          "residual_stress", "cyc_peak_mean", "cyc_diss_mean", "cyc_residual_mean",
          "T_peak_I", "Gc_I", "Gc_to_f_I", "T_peak_II", "Gc_II", "Gc_to_f_II"]


def e2_rows(rows, g_target):
    return derive_e2_rows(rows, g_target, SCALED)


# --------------------------------------------------------------------------- #
# Pareto (topo_opt machinery: minimization + Deb constraint domination)
# --------------------------------------------------------------------------- #
def pareto_analysis(agg, conds_by_name):
    from topo_opt import nondominated_sort  # noqa: F401 (dominates used inside it)
    F, V, names = [], [], []
    for name, a in agg.items():
        if name not in conds_by_name or conds_by_name[name].get("kind2") == "finite":
            continue
        vals = [-a["strength_mean"], -a["Gc_I_mean"], -a["recoil_mean"]]
        F.append([1e9 if not np.isfinite(v) else v for v in vals])
        V.append(int(a["n_fail"]))
        names.append(name)
    F = np.asarray(F, float)
    V = np.asarray(V, int)
    rank = nondominated_sort(F, V)
    fronts = {}
    for r in np.unique(rank):
        fronts[int(r)] = [names[i] for i in np.flatnonzero(rank == r)]
    per_family = {}
    for fam in ("diluted", "phantom", "fiber"):
        sel = [i for i, n in enumerate(names) if conds_by_name[n]["family"] == fam]
        if sel:
            rk = nondominated_sort(F[sel], V[sel])
            per_family[fam] = [names[sel[i]] for i in np.flatnonzero(rk == 0)]
    # robust front: maximize worst-case (mean - sd)
    Fr = []
    for name, a in agg.items():
        if name not in conds_by_name or conds_by_name[name].get("kind2") == "finite":
            continue
        Fr.append([-(a["strength_mean"] - a["strength_sd"]),
                   -(a["Gc_I_mean"] - a["Gc_I_sd"]),
                   -(a["recoil_mean"] - a["recoil_sd"])])
    Fr = np.asarray([[1e9 if not np.isfinite(v) else v for v in row] for row in Fr], float)
    rank_r = nondominated_sort(Fr, V)
    robust_front = [names[i] for i in np.flatnonzero(rank_r == 0)]
    return dict(fronts=fronts, front0=fronts.get(0, []),
                per_family_front0=per_family, robust_front0=robust_front,
                n_conditions=len(names))


# --------------------------------------------------------------------------- #
# CSV plumbing
# --------------------------------------------------------------------------- #
def write_csv_header(path, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()


def append_csv(path, fields, rows):
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        for r in rows:
            w.writerow(r)


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def run(P, device, out_dir, profile):
    import pandas as pd  # needed for the final aggregation (and by topo_opt)

    torch.set_num_threads(P["threads"])
    conds = build_conditions()
    if P["conditions"] is not None:
        conds = [conds[i] for i in P["conditions"]]
    by_name = {c["name"]: c for c in conds}
    for c in conds:
        c["_W"] = P["W"]
    extra_conds = []
    if P.get("finite_W"):
        base = build_conditions()[FINITE_COND_IDX]
        for W in P["finite_W"]:
            c = dict(base)
            c = {k: v for k, v in c.items() if k != "_W"}
            c["idx"] = base["idx"] * 100 + W          # distinct rng stream per size
            c["_W"] = W
            c["kind2"] = "finite"
            c["name"] = f"finiteW{W}-{base['name']}"
            extra_conds.append(c)
    all_conds = conds + extra_conds

    rpath = out_dir / "realizations.csv"
    cpath = out_dir / "cyclic.csv"
    rfields = ["cond", "cond_idx", "family", "orient", "curve", "xdist", "kind", "W",
               "z_target", "seed", "control", "scale", "ok", "e2_status", "e2_reason", "e2_method", "z_realized", "z_prenotch",
               "node_match", "n_alive", "n_lock", "n_notch", "G", "Cx", "Cy", "Cz",
               "Gyz", "Gzx", "peak_stress", "strain_at_peak", "failure_strain",
               "toughness", "max_drop", "residual_stress", "broken_total", "max_share",
               "participation", "p80", "cyc_peak_mean", "cyc_diss_mean",
               "cyc_residual_mean", "cyc_recoil_mean", "T_peak_I", "delta_f_I", "Gc_I",
               "Gc_to_f_I", "delta_censored_I", "first_rupture_I", "broken_I",
               "T_peak_II", "delta_f_II", "Gc_II", "Gc_to_f_II", "delta_censored_II",
               "first_rupture_II", "broken_II", "seconds"]
    cfields = ["cond", "cond_idx", "family", "kind", "W", "z_target", "seed", "cycle",
               "peak_stress", "work_load", "work_unload", "dissipated", "broken_cum",
               "residual_stress", "recoil"]
    write_csv_header(rpath, rfields)
    write_csv_header(cpath, cfields)

    g_target = None
    match = {}
    t_start = time.time()
    done = 0
    for cond in all_conds:
        n_target = 4 * cond["_W"] ** 3
        items, fails = build_realizations(cond, P["seeds"], cond["_W"], n_target)
        match[cond["name"]] = dict(
            z_target=cond["z"], W=cond["_W"], kind=cond.get("kind2", "screen"),
            n_seeds=len(P["seeds"]), n_ok=len(items), n_fail=len(fails),
            z_prenotch=[round(it["z_prenotch"], 4) for it in items],
            fails=fails,
            fail=(len(fails) > 0))
        if not items:
            print(f"[{cond['name']}] ALL {len(P['seeds'])} seeds failed matching: "
                  f"{fails[0]['reason'] if fails else '?'}", flush=True)
            (out_dir / "matching_report.json").write_text(json.dumps(match, indent=1))
            done += 1
            continue
        mods = e1_moduli(cond, items, device)
        for it, m in zip(items, mods):
            it["moduli"] = m
        if g_target is None:
            # Never silently change the target population to the next condition.
            try:
                g_target = select_e2_target(
                    mods, cond["idx"] == BASELINE_IDX and cond.get("kind2") != "finite")
            except ValueError as exc:
                (out_dir / "E2_BASELINE_FAILURE.json").write_text(json.dumps(
                    dict(condition=cond["name"], reason=str(exc), moduli=mods), indent=2))
                raise
            print(f"[g_target] validated baseline G median = {g_target:.4e}", flush=True)
        for it in items:
            gate = assess_e2(it["moduli"]["G"], g_target)
            it["e2_scale"] = gate["scale"]
            it["e2_gate"] = gate
            it["e2_target"] = g_target
        rows, cyc_rows, secs = run_battery(cond, items, P, device, out_dir)
        for r, it in zip(rows, items):
            r["control"] = "E1"
            r["scale"] = 1.0
        rows += e2_rows(rows, g_target)
        append_csv(rpath, rfields, rows)
        append_csv(cpath, cfields, cyc_rows)
        done += 1
        elapsed = time.time() - t_start
        eta = elapsed / done * (len(all_conds) - done)
        Gs = np.array([it["moduli"]["G"] for it in items])
        print(f"[{done}/{len(all_conds)}] {cond['name']}: G mean={Gs.mean():.3e} "
              f"spread[{Gs.min():.2e},{Gs.max():.2e}] "
              f"peak={np.mean([r['peak_stress'] for r in rows if r['control'] == 'E1']):.3e} "
              f"Gc_I={np.mean([r['Gc_I'] for r in rows if r['control'] == 'E1']):.3e} "
              f"({secs:.0f}s, eta {eta / 60:.0f}m, fail {len(fails)}/{len(P['seeds'])})",
              flush=True)
        (out_dir / "matching_report.json").write_text(json.dumps(match, indent=1))
        if device.startswith("cuda"):
            torch.cuda.empty_cache()

    # ---- aggregate + Pareto ----------------------------------------------------
    import pandas as pd
    df = pd.read_csv(rpath)
    e1 = df[(df["control"] == "E1") & (df["ok"])]
    agg = {}
    for name, g in e1.groupby("cond"):
        agg[name] = dict(
            strength_mean=float(g["peak_stress"].mean()),
            strength_sd=float(g["peak_stress"].std(ddof=1)) if len(g) > 1 else 0.0,
            Gc_I_mean=float(g["Gc_I"].mean()), Gc_I_sd=float(g["Gc_I"].std(ddof=1)) if len(g) > 1 else 0.0,
            recoil_mean=float(g["cyc_recoil_mean"].mean()),
            recoil_sd=float(g["cyc_recoil_mean"].std(ddof=1)) if len(g) > 1 else 0.0,
            n_seeds=int(len(g)), n_fail=int(match.get(name, {}).get("n_fail", 0)),
            G_mean=float(g["G"].mean()), G_sd=float(g["G"].std(ddof=1)) if len(g) > 1 else 0.0)
    by_name_full = {c["name"]: c for c in all_conds}
    pareto = pareto_analysis(agg, by_name_full)
    (out_dir / "pareto.json").write_text(json.dumps(dict(
        objectives=["strength (peak stress, axis 0, E1 mean over ok seeds)",
                    "G_c (cohesive mode I, E1 mean)",
                    "recoil (cyclic w_unload/w_load mean)"],
        direction="all maximized; fronts computed on negated values (minimization)",
        violations="matching failures per condition (Deb constraint domination)",
        aggregate=agg, **pareto), indent=1))
    (out_dir / "summary.json").write_text(json.dumps(dict(
        profile=profile, W=P["W"], seeds=P["seeds"], chemistry=CHEM,
        relax=P["relax"], fail_grid=P["fail"], frac_deltas=P["frac_deltas"],
        cycles=P["cycles"], cyc_steps=P["cyc_steps"], cyc_eps=P["cyc_eps"],
        g_target=g_target, conditions=[c["name"] for c in all_conds],
        n_conditions=len(all_conds), device=device,
        matching=match, seconds_total=round(time.time() - t_start, 1)), indent=1))
    print(f"total {time.time() - t_start:.0f}s -> {out_dir}", flush=True)
    print(f"Pareto front (overall): {pareto['front0']}", flush=True)


# --------------------------------------------------------------------------- #
# --validate: generator / E2 / Pareto checks (run on the target machine)
# --------------------------------------------------------------------------- #
def validate(device, P, out_dir):
    import pandas as pd  # noqa: F401  (topo_opt needs it; fail early here)
    from oxt.network3d import (Batch3D, Design3D, Lattice3D, build_network3d,
                               hessian_moduli, scale_stiffness)
    from oxt.fiber3d import (FiberBatch, FiberDesign, build_fiber_network,
                             fiber_hessian_moduli)
    from topo_opt import nondominated_sort
    from run_network3d import cohesive_metrics, curve_metrics

    torch.set_num_threads(P["threads"])
    rep = {}
    W = P["W"]
    lat = Lattice3D(W)

    # 1. z matching per family (8 seeds, pre-notch z)
    for fam in ("diluted", "phantom"):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Legacy family='phantom'")
            zs, za = [], []
            for s in range(8):
                rng = np.random.default_rng([s, 0 if fam == "diluted" else 15, 101])
                spec, info = build_network3d(
                    lat, Design3D(z=3.4, arch="uniform", family=fam, lock=CHEM["lock"],
                                 lock_place="crossings", mu=CHEM["mu"],
                                 kappa=CHEM["kappa"], kx=CHEM["kx"],
                                 eps_r=CHEM["eps_r"], k_gag=CHEM["k_gag"]), rng)
                zs.append(info["z_realized"] + 2.0 * info["n_notch"] / lat.N)
                za.append(info["z_realized"])
        rep[f"z_{fam}"] = dict(mean=float(np.mean(zs)), min=float(np.min(zs)),
                               max=float(np.max(zs)),
                               ok=bool(np.all(np.abs(np.asarray(zs) - 3.4) < Z_TOL)))

    # 2. fiber family: matching (z, node count, stress-free as-grown reference)
    box_L = (2 * SQ2 * W ** 3) ** (1 / 3)
    fib_center = build_conditions()[30]
    zs, okm, n_ok = [], True, 0
    for s in range(8):
        net_s = build_fiber_network(fiber_design(fib_center),
                                    np.random.default_rng([s, 30, 101]), box_L, 4 * W ** 3)
        if not net_s.get("ok", False):
            okm = False
            continue
        inf = net_s["info"]
        okm = okm and abs(inf["z_realized"] - 3.4) < Z_TOL and inf["node_match"] < 0.05
        zs.append(inf["z_realized"])
        n_ok += 1
    rep["fiber_matching"] = dict(ok=bool(okm), n_ok=n_ok,
                                 z_mean=float(np.mean(zs)) if zs else None,
                                 z_max_dev=float(np.max(np.abs(np.asarray(zs) - 3.4))) if zs else None)
    net = build_fiber_network(fiber_design(fib_center),
                              np.random.default_rng([0, 30, 101]), box_L, 4 * W ** 3)
    fb = FiberBatch([net], device=device)
    x = fb.X.clone().requires_grad_(True)
    e = fb.energy(x, fb.F0)
    e.backward()
    rep["fiber_stress_free"] = dict(energy=float(e.detach()), grad=float(x.grad.abs().max()),
                                    ok=bool(float(e.detach()) < 1e-20
                                            and float(x.grad.abs().max()) < 1e-12))

    # 3. E2 exactness, FCC: in-sim rescaled Hessian vs post-hoc ratio
    rng = np.random.default_rng([0, 0, 101])
    spec, _ = build_network3d(lat, Design3D(z=3.4, arch="uniform", family="diluted",
                                            lock=CHEM["lock"], lock_place="crossings",
                                            mu=CHEM["mu"], kappa=CHEM["kappa"],
                                            kx=CHEM["kx"], eps_r=CHEM["eps_r"],
                                            k_gag=CHEM["k_gag"]), rng)
    m1 = hessian_moduli(lat, spec, device=device)
    m2 = hessian_moduli(lat, scale_stiffness(spec, 2.3), device=device)
    rep["E2_fcc_exact"] = dict(ratio=float(m2["G"] / m1["G"]),
                               ok=bool(abs(m2["G"] / m1["G"] / 2.3 - 1) < 1e-8))

    # 4. E2 exactness, fiber: in-design rescaled moduli vs post-hoc ratio
    over = dict(mu=CHEM["mu"] * 2.3, kappa=CHEM["kappa"] * 2.3, kx=CHEM["kx"] * 2.3,
                k_gag=CHEM["k_gag"] * 2.3)
    net2 = build_fiber_network(fiber_design(build_conditions()[30], over=over),
                               np.random.default_rng([0, 30, 101]), box_L, 4 * W ** 3)
    f1 = fiber_hessian_moduli(net, device=device)
    f2 = fiber_hessian_moduli(net2, device=device)
    ratios = {k: f2[k] / f1[k] for k in f1}
    rep["E2_fiber_exact"] = dict(ratios=ratios,
                                 ok=bool(all(abs(r / 2.3 - 1) < 1e-6 for r in ratios.values())))

    # 5. cohesive plumbing per family: T rises then falls, positive Gc
    for fam, mk in (("diluted", lambda: Batch3D(lat, [spec], device=device, crack_axis=0,
                                                relax_kw=P["relax"])),
                    ("fiber", lambda: FiberBatch([net], device=device, relax_kw=P["relax"]))):
        b = mk()
        res = b.cohesive_curve([0.02, 0.06, 0.12, 0.20, 0.30], mode="tension")
        cm = cohesive_metrics(res)
        te = res["Teff"][0]
        rep[f"cohesive_{fam}"] = dict(
            T_peak=float(te.max()), Gc=float(cm["Gc"][0]), broken=int(res["broken"][0].sum()),
            rises_then_falls=bool(te.argmax() < len(te) - 1 and te.min() < te.max()),
            ok=bool(te.max() > 0 and cm["Gc"][0] > 0))

    # 6. Pareto plumbing: known 3-point front + constraint domination
    F = np.array([[0.0, 0.0], [1.0, 1.0], [0.5, 0.5]])
    V = np.array([0, 0, 1])
    rank = nondominated_sort(F, V)
    rep["pareto_plumbing"] = dict(rank=rank.tolist(),
                                  ok=bool(rank[0] == 0 and rank[1] == 1 and rank[2] == 1))

    rep["all_ok"] = bool(all(v.get("ok", True) for v in rep.values() if isinstance(v, dict)))
    (out_dir / "atlas_validation.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=2), flush=True)
    return rep


def main():
    ap = argparse.ArgumentParser(description="3D collagen architecture-atlas screening")
    ap.add_argument("--profile", default="smoke", choices=list(PROFILES))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=None)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--seeds", type=int, nargs="*", default=None)
    args = ap.parse_args()
    P = dict(PROFILES[args.profile])
    if args.seeds:
        P["seeds"] = list(args.seeds)
    out_dir = Path(args.out) if args.out else OUT / args.profile
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.validate:
        validate(args.device, P, out_dir)
        return
    run(P, args.device, out_dir, profile=args.profile)


if __name__ == "__main__":
    main()
