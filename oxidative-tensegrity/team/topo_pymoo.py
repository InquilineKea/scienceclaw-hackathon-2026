#!/usr/bin/env python3
"""Independent optimiser check of the topology front: pymoo's NSGA-II on the identical objective.

topo_opt.py evaluates designs and runs its own numpy NSGA-II. This script keeps topo_opt's design encoding,
objectives (toughness, max_drop, sensing, D_radial) and stiffness-band constraint, but lets pymoo 0.6.2 do
selection, crossover, mutation and survival, from a different seed. If the GA found a real front, both
optimisers should agree on where it is: which patterns / lock placements / connectivity it occupies, and its
normalised hypervolume. Agreement is judged by code in compare().

  python3 team/topo_pymoo.py run --gens 10 --pop 28 --workers 28 --seed 77    # writes results/topo/pymoo_*.csv
  python3 team/topo_pymoo.py compare                                         # -> results/topo/pymoo_compare.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import topo_opt as T  # noqa: E402


def run(a):
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import Problem
    from pymoo.optimize import minimize

    band = T.load_band()
    P = dict(T.PROFILES["cpu32"], W=a.W, workers=a.workers)
    P["G_skip"] = (band["G_lo"] / 3, band["G_hi"] * 3)
    ecsv, dcsv = T.OUT / f"pymoo_s{a.seed}_evals.csv", T.OUT / f"pymoo_s{a.seed}_designs.csv"
    ecsv.unlink(missing_ok=True)
    state = dict(gen=0, next_id=0, archive=[])
    t0 = time.time()
    ex = ProcessPoolExecutor(a.workers)

    class Topo(Problem):
        def __init__(self):
            super().__init__(n_var=7, n_obj=len(T.OBJ), n_ieq_constr=1, xl=0.0, xu=1.0)

        def _evaluate(self, X, out, *args, **kwargs):
            rows = T.evaluate(X, state["gen"], state["next_id"], P, ex, ecsv, t0, reps=2)
            agg = T.aggregate(rows, band).sort_values("design")
            out["F"] = T.objective_matrix(agg)
            out["G"] = agg["viol"].to_numpy(float)[:, None]
            agg["optimizer"] = "pymoo-NSGA2"
            state["archive"].append(agg)
            state["next_id"] += len(X)
            state["gen"] += 1
            pd.concat(state["archive"]).to_csv(dcsv, index=False)
            print(f"pymoo gen {state['gen']} evaluated ({time.time() - t0:.0f}s)", flush=True)

    minimize(Topo(), NSGA2(pop_size=a.pop), ("n_gen", a.gens), seed=a.seed, verbose=False)
    ex.shutdown()
    print("wrote", dcsv, flush=True)


def front(df):
    F, V = T.objective_matrix(df), df["viol"].to_numpy()
    r = T.nondominated_sort(F, V)
    return df[(r == 0) & (V == 0)]


def hv_mc(F, lo, hi, n=200000, seed=0):
    """Monte-Carlo hypervolume of minimisation points in the box [lo, hi] (same box for both optimisers)."""
    rng = np.random.default_rng(seed)
    U = lo + (hi - lo) * rng.random((n, F.shape[1]))
    dom = np.zeros(n, bool)
    for f in F:
        dom |= np.all(U >= f, 1)
    return float(dom.mean())


def compare(a):
    ga = pd.read_csv(T.OUT / "ga_W12_designs.csv")
    pm = pd.concat([pd.read_csv(p) for p in sorted(T.OUT.glob("pymoo_s*_designs.csv"))], ignore_index=True)
    fa, fb = front(ga), front(pm)
    Fa, Fb = T.objective_matrix(fa), T.objective_matrix(fb)
    allF = np.vstack([Fa, Fb])
    lo, hi = allF.min(0), allF.max(0) + 1e-12
    out = dict(n_evaluated=dict(ga=len(ga), pymoo=len(pm)), n_front=dict(ga=len(fa), pymoo=len(fb)),
               hv=dict(ga=hv_mc(Fa, lo, hi), pymoo=hv_mc(Fb, lo, hi), union=hv_mc(allF, lo, hi)))
    for col in ("pattern", "place"):
        out[col] = dict(ga=fa[col].value_counts(normalize=True).round(2).to_dict(),
                        pymoo=fb[col].value_counts(normalize=True).round(2).to_dict())
    out["z_front"] = dict(ga=[float(fa["z"].min()), float(fa["z"].max())], pymoo=[float(fb["z"].min()), float(fb["z"].max())])
    # cross-dominance: share of each front not dominated by any point of the other front
    def undominated(X, Y):
        return float(np.mean([not any(np.all(y <= x) and np.any(y < x) for y in Y) for x in X]))
    out["share_not_dominated_by_other"] = dict(ga=undominated(Fa, Fb), pymoo=undominated(Fb, Fa))
    za, zb = out["z_front"]["ga"], out["z_front"]["pymoo"]
    overlap = max(0.0, min(za[1], zb[1]) - max(za[0], zb[0])) / max(za[1] - za[0], zb[1] - zb[0], 1e-9)
    out["verdict"] = ("front reproduced" if overlap >= 0.5 and min(out["share_not_dominated_by_other"].values()) >= 0.3
                      else "front NOT reproduced")
    out["z_overlap_fraction"] = overlap
    (T.OUT / "pymoo_compare.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "compare"])
    ap.add_argument("--gens", type=int, default=10)
    ap.add_argument("--pop", type=int, default=28)
    ap.add_argument("--workers", type=int, default=28)
    ap.add_argument("--seed", type=int, default=77)
    ap.add_argument("--W", type=int, default=12)
    a = ap.parse_args()
    run(a) if a.cmd == "run" else compare(a)
