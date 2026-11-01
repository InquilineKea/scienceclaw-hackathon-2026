#!/usr/bin/env python3
"""Phase map of the Col I fibre network: connectivity z x junction locking x AGE dose.

Axes
  z       mean connectivity (fibre branching + LOX bridging), 2.2 .. 6.0
  lock    fraction of junctions whose angles are locked by LOX-type (pyridinoline, k_rel = 1) crosslinks
  dose    oxidative/AGE dose (Damage(iso)): adds stiff, brittle intrafibrillar and bridging crosslinks

Per system: connectivity percolation (largest-cluster fraction), small-strain moduli G and Cx, and a
laterally constrained uniaxial pull with bond rupture -> strength, strain at peak, toughness, brittleness.

  python3 run_phase.py --profile cpu32        # GCP 32 vCPU
  python3 run_phase.py --profile smoke        # quick check
  python3 run_phase.py --profile fss --W 24 --tag W24   # finite-size scaling, moduli only
Rows are appended to results/phase/<tag>.csv as each task finishes, so a partial run is usable.
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

PROFILES = {
    "smoke": dict(W=8, seeds=1, batch=4, workers=4, z=[2.6, 4.0, 5.5], lock=[0.0, 1.0], dose=[1.0],
                  fail=[0.05, 0.15, 0.3, 0.5]),
    "cpu32": dict(W=12, seeds=4, batch=2, workers=30,
                  z=[2.2, 2.5, 2.8, 3.1, 3.4, 3.7, 4.0, 4.3, 4.6, 5.0, 5.5, 6.0],
                  lock=[0.0, 0.5, 1.0], dose=[0.5, 1.0],
                  fail=list(np.round(np.linspace(0.02, 0.6, 15), 3))),
    # finite-size scaling around the rigidity onset: small-strain moduli only (no failure pull)
    # more seeds and a finer strain grid where the useful window and the brittle crossover sit
    "tough": dict(W=12, seeds=8, batch=2, workers=16, z=[3.1, 3.4, 3.7, 4.0, 4.3, 4.6, 5.0],
                  lock=[0.0], dose=[1.0], fail=list(np.round(np.linspace(0.01, 0.5, 20), 3))),
    "fss": dict(W=16, seeds=6, batch=2, workers=120, z=list(np.round(np.arange(2.8, 4.66, 0.15), 2)),
                lock=[0.0, 1.0], dose=[1.0], fail=[]),
}
KX_LOX = 2e-3  # locked-junction angular stiffness for k_rel = 1 (same scale as materials.Damage.kx0)


def largest_cluster(alive, lat):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    i, j = lat.bi[alive], lat.bj[alive]
    A = coo_matrix((np.ones(i.size), (i, j)), shape=(lat.N, lat.N))
    _, lab = connected_components(A, directed=False)
    return np.bincount(lab).max() / lat.N


def _worker(task):
    import torch

    torch.set_num_threads(1)
    from oxt.materials import COLLAGENS, Damage, build_spec
    from oxt.network import Batch, Lattice, coordination

    lat = Lattice(task["W"])
    col = COLLAGENS["I"]
    specs = []
    for it in task["items"]:
        rng = np.random.default_rng(it["seed"])
        dmg = Damage("iso", it["dose"]) if it["dose"] > 0 else Damage()
        s = build_spec(lat, col, dmg, rng, z=it["z"])
        if it["lock"] > 0:  # LOX-locked junctions, on top of any AGE-locked ones
            n = int(round(it["lock"] * lat.N))
            idx = rng.choice(lat.N, n, replace=False)
            s.rigid_node[idx] = np.maximum(s.rigid_node[idx], KX_LOX)
        s.meta.update(seed=it["seed"], lock=it["lock"], dose=it["dose"], z_target=it["z"])
        specs.append(s)
    rows = [dict(**{k: v for k, v in s.meta.items() if k in ("seed", "lock", "dose", "z_target")},
                 z=coordination(s, lat), giant=largest_cluster(s.alive, lat)) for s in specs]
    t0 = time.time()
    m = Batch(lat, specs).small_strain_moduli()
    if not task["fail"]:
        for i, r in enumerate(rows):
            r.update(G=m["G"][i], Cx=m["Cx"][i], seconds=time.time() - t0, W=task["W"])
        return rows
    sig, brk = Batch(lat, specs).failure_curve(task["fail"], axis=0)
    eps = np.asarray(task["fail"])
    nb = np.array([s.alive.sum() for s in specs])
    for i, r in enumerate(rows):
        k = int(np.argmax(sig[i]))
        drops = np.diff(sig[i]) / max(sig[i, k], 1e-300)
        r.update(G=m["G"][i], Cx=m["Cx"][i], strength=float(sig[i, k]), strain_at_peak=float(eps[k]),
                 toughness=float(np.trapz(np.clip(sig[i], 0, None), eps)),
                 # brittleness: largest single-step stress drop relative to peak, and the largest
                 # rupture avalanche as a fraction of the bonds present
                 max_drop=float(-drops.min()) if drops.size else 0.0,
                 max_avalanche=float(brk[i].max() / max(nb[i], 1)),
                 broken_total=float(brk[i].sum() / max(nb[i], 1)),
                 curve=json.dumps([float(v) for v in sig[i]]), seconds=0.0)
    for r in rows:
        r.update(seconds=time.time() - t0, W=task["W"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="smoke", choices=PROFILES)
    ap.add_argument("--W", type=int)
    ap.add_argument("--seeds", type=int)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--tag")
    ap.add_argument("--seed0", type=int, default=5000)
    a = ap.parse_args()
    P = dict(PROFILES[a.profile])
    for k in ("W", "seeds", "workers"):
        if getattr(a, k):
            P[k] = getattr(a, k)
    tag = a.tag or a.profile
    items = []
    for s in range(P["seeds"]):
        for z in P["z"]:
            for lk in P["lock"]:
                items.append(dict(z=z, lock=lk, dose=0.0, seed=a.seed0 + s))
            for d in P["dose"]:
                items.append(dict(z=z, lock=0.0, dose=d, seed=a.seed0 + s))
    # slow (near-threshold, floppy) systems first so the pool stays busy at the end
    items.sort(key=lambda it: abs(it["z"] - 3.4))
    tasks = [dict(items=items[k:k + P["batch"]], W=P["W"], fail=P["fail"])
             for k in range(0, len(items), P["batch"])]
    print(f"{len(items)} systems, {len(tasks)} tasks, {P['workers']} workers", flush=True)
    out = ROOT / "results" / "phase"
    out.mkdir(parents=True, exist_ok=True)
    csv = out / f"{tag}.csv"
    csv.unlink(missing_ok=True)
    (out / f"{tag}_params.json").write_text(json.dumps(P, indent=1))
    t0 = time.time()
    with ProcessPoolExecutor(P["workers"]) as ex:
        futs = [ex.submit(_worker, t) for t in tasks]
        for n, f in enumerate(as_completed(futs)):
            rows = f.result()
            pd.DataFrame(rows).to_csv(csv, mode="a", header=not csv.exists(), index=False)
            print(f"task {n + 1}/{len(tasks)} ({rows[0]['seconds']:.0f}s, wall {time.time() - t0:.0f}s)", flush=True)
    print("wrote", csv, flush=True)


if __name__ == "__main__":
    main()
