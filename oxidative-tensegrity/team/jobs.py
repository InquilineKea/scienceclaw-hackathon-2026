#!/usr/bin/env python3
"""Deterministic solver jobs for the agent team. Agents choose jobs and parameters; only this code computes.

Every job takes a dict of parameters (clamped to SCHEMA ranges) and returns a dict of numbers. Jobs never
read agent text, never touch the network, and never execute anything but numpy/scipy/torch on local data.

  python3 team/jobs.py run tasks.json out.jsonl --workers 30      # batch runner (used on the GCP VM)
  python3 team/jobs.py smoke                                      # quick local check of every job

Mechanism jobs
  cluster_network   2D periodic Col I network at native z ~ 3.4. AGE crosslinks (bridging bonds, stiffened
                    brittle segments, locked junctions) placed dispersed vs clustered, under a matching control:
                      count     same base network, same number of each crosslink type; only placement differs
                      no_bridge as count, but no added bonds, so fibre content is identical
                      bulk_G    clustered crosslink stiffness rescaled (bisection) until initial G matches dispersed
                    -> G, strength, strain at peak, work to peak, largest avalanche, bond-strain concentration
  fibril_sliding    series chain of tropocollagen segments joined by sliding interfaces (elastic-plastic
                    friction plateau = intermolecular sliding) with AGE crosslinks as brittle parallel springs that
                    block sliding; segments rupture at F_m. Placement dispersed vs clustered.
                    -> peak force, strain at failure, work, sliding dissipation, failure mode
  poro_timescale    Biot drainage time tau = L^2 eta / (k H_A) and Deborah number vs loading time

Validator jobs (different calculations from the originals)
  network_linear_G  shear modulus from the autograd Hessian (G = [E_gg - Xi^T H^-1 Xi]/A), no L-BFGS relaxation
  fibril_analytic   closed-form limits of the chain: elastic compliance, friction plateau, molecular rupture
"""
from __future__ import annotations

import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCHEMA = {
    "cluster_network": dict(W=(8, 16, 12), z=(2.8, 4.6, 3.4), dose=(0.0, 1.0, 0.6), placement=["dispersed", "clustered"],
                            n_clusters=(1, 16, 4), control=["count", "no_bridge", "bulk_G"], seed=(0, 10**6, 9000),
                            max_strain=(0.1, 0.6, 0.4), n_strain=(6, 24, 14)),
    "fibril_sliding": dict(M=(10, 200, 40), n_age=(0, 400, 40), placement=["dispersed", "clustered"],
                           n_clusters=(1, 50, 4), k_a=(0.1, 50.0, 5.0), delta_a=(0.005, 0.5, 0.05),
                           F_y=(0.2, 5.0, 1.0), k_f=(1.0, 100.0, 10.0), F_m=(1.0, 20.0, 3.0), k_m=(1.0, 400.0, 40.0),
                           delta_end=(0.2, 10.0, 2.0), seed=(0, 10**6, 9000), dU=(1e-3, 0.05, 0.005)),
    "poro_timescale": dict(L_m=(1e-7, 1e-2, 1e-4), k_m2=(1e-20, 1e-10, 1e-14), H_A_Pa=(10.0, 1e7, 1e3),
                           eta_Pa_s=(5e-4, 1e-2, 1e-3), t_load_s=(1e-4, 1e6, 1.0)),
    "network_linear_G": dict(W=(8, 20, 12), z=(2.8, 6.0, 3.4), dose=(0.0, 1.0, 0.0), lock=(0.0, 1.0, 0.0),
                             seed=(0, 10**6, 5000), placement=["none", "dispersed", "clustered"], n_clusters=(1, 16, 4),
                             control=["count", "no_bridge"]),
    "fibril_analytic": dict(M=(10, 200, 40), F_y=(0.2, 5.0, 1.0), k_f=(1.0, 100.0, 10.0), F_m=(1.0, 20.0, 3.0),
                            k_m=(1.0, 400.0, 40.0), delta_end=(0.2, 10.0, 2.0), n_age=(0, 400, 0), k_a=(0.1, 50.0, 5.0),
                            delta_a=(0.005, 0.5, 0.05)),
}


def clamp(job: str, params: dict) -> dict:
    """Fill defaults and clamp every parameter into its allowed range; unknown keys are dropped."""
    if job not in SCHEMA:
        raise ValueError(f"unknown job {job!r}")
    out = {}
    for k, spec in SCHEMA[job].items():
        v = params.get(k)
        if isinstance(spec, list):
            out[k] = v if v in spec else spec[0]
        else:
            lo, hi, default = spec
            try:
                v = float(default if v is None else v)
            except (TypeError, ValueError):
                v = float(default)
            v = min(max(v, lo), hi)
            out[k] = int(round(v)) if isinstance(default, int) else v
    if job in ("cluster_network", "network_linear_G") and out["W"] % 2:
        out["W"] += 1
    return out


# ---------------------------------------------------------------- network jobs

def _min_image(d, L):
    return d - L * np.round(d / L)


def _place(pts, n, rng, placement, centers, L):
    """Choose n of the candidate points: uniformly at random, or those nearest the cluster centres."""
    n = min(n, len(pts))
    if n <= 0:
        return np.array([], dtype=int)
    if placement == "dispersed":
        return rng.choice(len(pts), n, replace=False)
    dist = np.min([np.linalg.norm(_min_image(pts - c, L), axis=1) for c in centers], axis=0)
    return np.argsort(dist + 1e-6 * rng.random(len(pts)))[:n]


def _network_spec(p, stiff_scale=1.0):
    """Base native network plus AGE crosslinks; placement only changes WHERE the same crosslinks go."""
    from oxt.materials import COLLAGENS, CROSSLINKS, Damage, build_spec
    from oxt.network import Lattice

    lat = Lattice(p["W"])
    col = COLLAGENS["I"]
    rng = np.random.default_rng(p["seed"])
    s = build_spec(lat, col, Damage(), rng, z=p["z"])
    if p.get("lock", 0) > 0:  # same generator and order as run_phase.py, so phase-map networks are rebuilt exactly
        idx = rng.choice(lat.N, int(round(p["lock"] * lat.N)), replace=False)
        s.rigid_node[idx] = np.maximum(s.rigid_node[idx], 2e-3)
    dmg = Damage("iso", p["dose"])
    if p.get("placement", "none") == "none" or p["dose"] <= 0:
        return lat, s
    k_rel = float(np.mean([CROSSLINKS[c]["k_rel"] for c in col.oxidative_xl]))
    crng = np.random.default_rng(p["seed"] + 7)  # same centres and draws for both placements
    centers = crng.random((p["n_clusters"], 2)) * lat.L
    mid = lat.X[lat.bi] + 0.5 * (lat.X[lat.bj] - lat.X[lat.bi] + lat.shift @ np.diag(lat.L))
    mid = np.mod(mid, lat.L)
    prng = np.random.default_rng(p["seed"] + 11)
    if p["control"] != "no_bridge":
        missing = np.flatnonzero(~s.alive)
        new = missing[_place(mid[missing], int(round(p["dose"] * dmg.bridge_frac * lat.Nb)), prng, p["placement"], centers, lat.L)]
        s.alive[new] = True
        s.mu[new] = col.mu * k_rel
        s.eps_r[new] = col.eps_r * dmg.brittle
    present = np.flatnonzero(s.alive)
    ch = present[_place(mid[present], int(round(p["dose"] * dmg.stiff_frac * present.size)), prng, p["placement"], centers, lat.L)]
    s.mu[ch] *= 1 + stiff_scale * dmg.stiff_gain * k_rel * p["dose"]
    s.kappa_b[ch] *= 1 + stiff_scale * 2 * k_rel * p["dose"]
    s.eps_r[ch] *= dmg.brittle
    nodes = _place(lat.X, int(round(p["dose"] * dmg.rigid_frac * lat.N)), prng, p["placement"], centers, lat.L)
    s.rigid_node[nodes] = np.maximum(s.rigid_node[nodes], stiff_scale * dmg.kx0 * k_rel)
    return lat, s


def _moduli(lat, s):
    from oxt.network import Batch
    return float(Batch(lat, [s]).small_strain_moduli()["G"][0])


def job_cluster_network(p):
    import torch
    torch.set_num_threads(1)
    from oxt.network import Batch, coordination

    scale = 1.0
    if p["control"] == "bulk_G" and p["placement"] == "clustered":
        target = _moduli(*_network_spec(dict(p, placement="dispersed")))
        lo, hi = 0.0, 8.0
        for _ in range(9):  # G is monotone in crosslink stiffness
            mid = 0.5 * (lo + hi)
            if _moduli(*_network_spec(p, mid)) < target:
                lo = mid
            else:
                hi = mid
        scale = 0.5 * (lo + hi)
    lat, s = _network_spec(p, scale)
    b = Batch(lat, [s])
    G = float(b.small_strain_moduli()["G"][0])
    eps = np.linspace(p["max_strain"] / p["n_strain"], p["max_strain"], p["n_strain"])
    # bond-strain concentration at a small stretch, before any rupture
    b2 = Batch(lat, [s])
    F = b2.F_stretch(0.02, 0)
    b2.move_affine(b2.F0, F)
    b2.relax(F)
    bs = b2.bond_strain(F)[0].detach().numpy()[s.alive]
    pos = np.abs(bs)
    sig, brk = Batch(lat, [s]).failure_curve(list(eps), axis=0)
    sig, brk = sig[0], brk[0]
    k = int(np.argmax(sig))
    nb = max(int(s.alive.sum()), 1)
    work = float(np.trapz(np.r_[0, np.clip(sig[:k + 1], 0, None)], np.r_[0, eps[:k + 1]]))
    return dict(G=G, strength=float(sig[k]), strain_at_peak=float(eps[k]), work_to_peak=work,
                max_avalanche=float(brk.max() / nb), broken_total=float(brk.sum() / nb),
                strain_p99_over_mean=float(np.percentile(pos, 99) / max(pos.mean(), 1e-12)),
                strain_cv=float(pos.std() / max(pos.mean(), 1e-12)), z=float(coordination(s, lat)),
                n_bonds=nb, stiff_scale=scale, curve=[float(v) for v in sig])


def job_network_linear_G(p):
    """Independent shear modulus: exact linear response from the autograd Hessian at the relaxed reference."""
    import torch
    torch.set_num_threads(1)
    from oxt.network import Batch

    lat, s = _network_spec(dict(p, control=p.get("control", "count")))
    b = Batch(lat, [s])
    b.relax(b.F0, ftol=1e-10, max_rounds=80)
    x0 = b.x[0].detach().clone()
    n = x0.numel()

    def E(xflat, g):
        F = b.F0.clone()
        F = F + torch.zeros_like(F).index_put_((torch.tensor([0]), torch.tensor([0]), torch.tensor([1])), g.reshape(1))
        return b.energy(xflat.reshape(1, -1, 2), F)

    xf = x0.reshape(-1).clone().requires_grad_(True)
    g0 = torch.zeros(1, dtype=x0.dtype, requires_grad=True)
    H = torch.autograd.functional.hessian(lambda a, c: E(a, c), (xf, g0))
    Hxx = H[0][0].detach().numpy().reshape(n, n)
    Hxg = H[0][1].detach().numpy().reshape(n)
    Hgg = float(H[1][1].detach().numpy().reshape(()))
    sol = np.linalg.lstsq(Hxx, Hxg, rcond=1e-12)[0]
    G = (Hgg - Hxg @ sol) / lat.area
    return dict(G=float(G), G_affine=float(Hgg / lat.area), hessian_dofs=int(n))


# ---------------------------------------------------------------- fibril jobs

def _age_counts(p, rng):
    counts = np.zeros(p["M"], dtype=int)
    if p["n_age"] <= 0:
        return counts
    if p["placement"] == "dispersed":
        for i in rng.integers(0, p["M"], p["n_age"]):
            counts[i] += 1
    else:
        sites = rng.choice(p["M"], min(p["n_clusters"], p["M"]), replace=False)
        for i in rng.choice(sites, p["n_age"]):
            counts[i] += 1
    return counts


def _slip(F, p_old, kf, Fy, Ka):
    """Interface slip delta at force F: friction element k_f(delta-p) capped at +-F_y, in parallel with K_a delta."""
    d_el = (F + kf * p_old) / (kf + Ka)  # friction still elastic
    if abs(kf * (d_el - p_old)) <= Fy:
        return d_el, p_old
    if Ka <= 0:
        return math.inf, p_old
    d = (F - Fy) / Ka
    return d, d - Fy / kf


def job_fibril_sliding(p):
    rng = np.random.default_rng(p["seed"])
    M, kf, Fy, km, Fm = p["M"], p["k_f"], p["F_y"], p["k_m"], p["F_m"]
    n = _age_counts(p, rng)
    plastic = np.zeros(M)
    U, F, work, slide_diss, age_breaks = 0.0, 0.0, 0.0, 0.0, 0
    Fs, Us, mode = [0.0], [0.0], "running"
    for _ in range(200000):
        U += p["dU"]
        for _cascade in range(M + 1):
            Ka = n * p["k_a"]
            free = Ka <= 0
            cap = Fy if free.any() else math.inf

            def total(Fv):
                d = [_slip(Fv, plastic[i], kf, Fy, Ka[i])[0] for i in range(M)]
                return sum(d) + M * Fv / km

            if cap < math.inf and total(cap * (1 - 1e-12)) < U:
                Fn = cap
                # localisation: extra displacement slides the first free interface at the plateau
                d = np.array([_slip(Fn * (1 - 1e-12), plastic[i], kf, Fy, Ka[i])[0] for i in range(M)])
                j = int(np.flatnonzero(free)[0])
                extra = U - (d.sum() + M * Fn / km)
                d[j] += extra
                slide_diss += Fy * max(d[j] - Fy / kf - plastic[j], 0.0)
                plastic[j] = max(plastic[j], d[j] - Fy / kf)
            else:
                lo, hi = 0.0, max(F, 1.0)
                while total(hi) < U:
                    hi *= 2
                    if hi > 1e9:
                        break
                for _ in range(80):
                    mid = 0.5 * (lo + hi)
                    if total(mid) < U:
                        lo = mid
                    else:
                        hi = mid
                Fn = 0.5 * (lo + hi)
                res = [_slip(Fn, plastic[i], kf, Fy, Ka[i]) for i in range(M)]
                d = np.array([r[0] for r in res])
                newp = np.array([r[1] for r in res])
                slide_diss += float(np.sum(Fy * np.clip(newp - plastic, 0, None)))
                plastic = np.maximum(plastic, newp)
            broke = (n > 0) & (d > p["delta_a"])
            if broke.any():
                age_breaks += int(n[broke].sum())
                n[broke] = 0
                continue
            break
        work += 0.5 * (F + Fn) * p["dU"]
        F = Fn
        Fs.append(F)
        Us.append(U)
        if F > Fm:
            mode = "molecular_rupture"
            break
        if np.any(d - plastic > p["delta_end"]) or np.any(plastic > p["delta_end"]):
            mode = "pullout"
            break
    Fs = np.array(Fs)
    k = int(np.argmax(Fs))
    return dict(peak_force=float(Fs[k]), U_at_peak=float(Us[k]), U_fail=float(Us[-1]), work=float(work),
                sliding_dissipation=float(slide_diss), age_breaks=age_breaks, failure_mode=mode,
                n_age_interfaces=int((_age_counts(p, np.random.default_rng(p["seed"])) > 0).sum()),
                elastic_slope=float(Fs[1] / Us[1]) if len(Fs) > 1 and Us[1] > 0 else None)


def job_fibril_analytic(p):
    M, kf, Fy, km, Fm = p["M"], p["k_f"], p["F_y"], p["k_m"], p["F_m"]
    slope = 1.0 / (M / km + M / kf)
    out = dict(elastic_slope_noAGE=slope)
    if p["n_age"] == 0:
        if Fy < Fm:
            out.update(failure_mode="pullout", peak_force=Fy,
                       # one interface slides delta_end beyond yield at F_y; the rest stay elastic
                       work=Fy * Fy / (2 * slope) + Fy * p["delta_end"], U_fail=Fy / slope + p["delta_end"])
        else:
            out.update(failure_mode="molecular_rupture", peak_force=Fm, work=Fm * Fm / (2 * slope))
    return out


def job_poro_timescale(p):
    D = p["k_m2"] * p["H_A_Pa"] / p["eta_Pa_s"]  # consolidation coefficient, m^2/s
    tau = p["L_m"] ** 2 / D
    return dict(consolidation_coeff_m2_s=D, tau_drain_s=tau, deborah=tau / p["t_load_s"],
                regime=("drained (fluid irrelevant)" if tau / p["t_load_s"] < 0.1 else
                        "undrained (fluid carries load)" if tau / p["t_load_s"] > 10 else "poroelastic transition"))


JOBS = dict(cluster_network=job_cluster_network, fibril_sliding=job_fibril_sliding, poro_timescale=job_poro_timescale,
            network_linear_G=job_network_linear_G, fibril_analytic=job_fibril_analytic)


def run_task(task):
    t0 = time.time()
    p = clamp(task["job"], task.get("params", {}))
    try:
        res = JOBS[task["job"]](p)
        ok = True
    except Exception as e:  # recorded, never hidden
        res, ok = dict(error=f"{type(e).__name__}: {e}"), False
    return dict(task_id=task["task_id"], job=task["job"], params=p, ok=ok, seconds=round(time.time() - t0, 2), result=res)


def main():
    if sys.argv[1] == "smoke":
        tasks = [dict(task_id="s1", job="fibril_sliding", params=dict(M=10, n_age=0)),
                 dict(task_id="s2", job="fibril_analytic", params=dict(M=10)),
                 dict(task_id="s3", job="fibril_sliding", params=dict(M=10, n_age=30, placement="dispersed")),
                 dict(task_id="s4", job="poro_timescale", params={}),
                 dict(task_id="s5", job="cluster_network", params=dict(W=8, n_strain=4, placement="clustered", control="count")),
                 dict(task_id="s6", job="network_linear_G", params=dict(W=8, z=4.4, seed=1)),
                 dict(task_id="s7", job="cluster_network", params=dict(W=8, z=4.4, seed=1, dose=0.0, n_strain=4))]
        for t in tasks:
            r = run_task(t)
            r["result"].pop("curve", None)
            print(json.dumps(r)[:400])
        return
    _, _, src, dst, *rest = sys.argv
    workers = int(rest[rest.index("--workers") + 1]) if "--workers" in rest else 8
    tasks = json.loads(Path(src).read_text())
    done = set()
    if Path(dst).exists():
        done = {json.loads(l)["task_id"] for l in Path(dst).read_text().splitlines() if l.strip()}
    todo = [t for t in tasks if t["task_id"] not in done]
    print(f"{len(todo)} tasks ({len(done)} already done), {workers} workers", flush=True)
    with ProcessPoolExecutor(workers) as ex, open(dst, "a") as fh:
        for f in as_completed([ex.submit(run_task, t) for t in todo]):
            fh.write(json.dumps(f.result()) + "\n")
            fh.flush()
    print("done", flush=True)


if __name__ == "__main__":
    main()
