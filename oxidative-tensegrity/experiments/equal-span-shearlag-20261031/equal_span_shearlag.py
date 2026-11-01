#!/usr/bin/env python3
"""Equal-span controls for Codex's three-owner shear-lag toy (colbuilder-study/pyd-ownership-surrogate).

Codex's clustered [12,13,14,16,17,18]/30 and dispersed [3,8,13,17,22,27]/30 junction sets differ in
clumpiness AND in occupied axial span (0.2 vs 0.8 of L), so "dispersing raised K by 15-30%" mixes the two.
This script separates them, in the same model and under the same loading.

Independent reimplementation, not a rerun of Codex's code: junction coordinates q are explicit DOFs
joined to their three sites by arm springs kappa (Codex condenses them into kappa/3 pair springs), and the
system is solved with numpy.linalg.solve on the full stiffness matrix. Same frozen choices otherwise:
3 owners x 31 nodes, L=1, EA=1, kappa=1, sites at c-1, c, c+1 nodes, cyclic owner rotation, staggered
grips (owner0 left end u=0, owner1 right end u=delta) or all-end grips.

Dimensionless linear model. Not MD, not PYD chemistry, no rupture/plasticity.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import pathlib

import numpy as np

N = 31
KARM = 1.0
CODEX = {  # Codex's remote values (ACTUAL-RESULTS.md), primary 6-junction staggered + all-ends
    ("2", "clustered", "staggered"): 0.7103597, ("2", "dispersed", "staggered"): 0.8184748,
    ("3", "clustered", "staggered"): 0.8096359, ("3", "dispersed", "staggered"): 1.0532746,
}
CLUSTERED = [12, 13, 14, 16, 17, 18]
DISPERSED = [3, 8, 13, 17, 22, 27]


def sites_for(centers, ownership, offset=1):
    """Same owner rule as the original: junction j, a=j%3, b=a+1 (2-owner) or (j+t)%3 (3-owner)."""
    out = []
    for j, c in enumerate(centers):
        a = j % 3
        b = (a + 1) % 3
        if ownership == 2:
            out.append([(a, c - offset), (a, c), (b, c + offset)])
        else:
            out.append([((j + t) % 3, c + (t - 1) * offset) for t in range(3)])
    return out


def stiffness(centers, ownership, grips="staggered", n=N, scale=1, delta=0.01):
    """Return reaction/delta. `scale` refines the mesh: node index i -> i*scale, same physical sites."""
    nodes = n if scale == 1 else (n - 1) * scale + 1
    kb = (nodes - 1) * 1.0  # EA/dz with EA=1, L=1
    jsites = sites_for([c * scale for c in centers], ownership, offset=scale)
    ndof = 3 * nodes + len(jsites)
    K = np.zeros((ndof, ndof))

    def spring(a, b, k):
        K[a, a] += k; K[b, b] += k; K[a, b] -= k; K[b, a] -= k

    idx = lambda o, i: o * nodes + i
    for o in range(3):
        for i in range(nodes - 1):
            spring(idx(o, i), idx(o, i + 1), kb)
    for jj, s in enumerate(jsites):
        q = 3 * nodes + jj
        for o, i in s:
            spring(idx(o, i), q, KARM)
    if grips == "staggered":
        fixed = {idx(0, 0): 0.0, idx(1, nodes - 1): delta}
        pulled = [idx(1, nodes - 1)]
    else:
        fixed = {**{idx(o, 0): 0.0 for o in range(3)}, **{idx(o, nodes - 1): delta for o in range(3)}}
        pulled = [idx(o, nodes - 1) for o in range(3)]
    free = [d for d in range(ndof) if d not in fixed]
    fd = list(fixed)
    uf = np.array([fixed[d] for d in fd])
    u = np.zeros(ndof)
    u[fd] = uf
    u[free] = np.linalg.solve(K[np.ix_(free, free)], -K[np.ix_(free, fd)] @ uf)
    f = K @ u
    resid = np.abs(f[free]).max()
    energy = 0.5 * u @ K @ u
    reaction = f[pulled].sum()
    if resid > 1e-9 or abs(2 * energy - reaction * delta) > 1e-12 or abs(f.sum()) > 1e-9:
        raise ArithmeticError("equilibrium / energy gate failed")
    return reaction / delta


def kde_C(centers, h=0.05, n=N):
    """Codex's analytic real-line Gaussian concentration C = L*int p^2, centers in units of L."""
    z = np.array(centers) / (n - 1)
    d = z[:, None] - z[None, :]
    return float(np.exp(-d ** 2 / (4 * h * h)).sum() / (2 * math.sqrt(math.pi) * h * len(z) ** 2))


def descriptors(centers, n=N):
    z = np.sort(np.array(centers) / (n - 1))
    gaps = np.diff(z)
    nn = np.minimum(np.r_[np.inf, gaps], np.r_[gaps, np.inf])
    return {"span": float(z[-1] - z[0]), "centroid": float(z.mean()), "mean_nn": float(nn.mean()),
            "gap_cv": float(gaps.std() / gaps.mean()), "C_h05": kde_C(centers)}


def designed_sets():
    """Named equal-span families. Span 24 nodes (0.8 L, same as dispersed) and span 6/10 nodes."""
    return {
        # span 0.8, from evenly spread to strongly clumped (endpoints pinned at 3 and 27)
        "s80_even(dispersed)": DISPERSED,
        "s80_two_end_clumps": [3, 4, 5, 25, 26, 27],
        "s80_center_clump": [3, 13, 14, 16, 17, 27],
        "s80_left_clump": [3, 4, 5, 6, 7, 27],
        "s80_right_clump": [3, 23, 24, 25, 26, 27],
        # span 0.2 (same as clustered), two arrangements
        "s20_clustered(original)": CLUSTERED,
        "s20_contiguous": [12, 13, 14, 15, 16, 18],
        # evenly spaced, fixed pattern, span varied
        "even_d1_s17": [12, 13, 14, 15, 16, 17],
        "even_d2_s33": [10, 12, 14, 16, 18, 20],
        "even_d3_s50": [7, 10, 13, 16, 19, 22],
        "even_d4_s67": [5, 9, 13, 17, 21, 25],
        "even_d5_s83": [2, 7, 12, 17, 22, 27],
        # clustered pattern translated toward a grip (position control)
        "s20_shift_left": [c - 9 for c in CLUSTERED],
        "s20_shift_right": [c + 9 for c in CLUSTERED],
    }


def ols(X, y):
    X1 = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    r2 = 1 - ((y - X1 @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return beta, float(r2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=20261031)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Independent reproduction of Codex's four staggered K values (+ all-ends limit)
    repro = {}
    for (own, pl, gr), ref in CODEX.items():
        k = stiffness(CLUSTERED if pl == "clustered" else DISPERSED, int(own), gr)
        repro[f"owners{own}-{pl}-{gr}"] = {"codex": ref, "this": k, "abs_diff": abs(k - ref)}
    for own in (2, 3):
        for pl, c in (("clustered", CLUSTERED), ("dispersed", DISPERSED)):
            repro[f"owners{own}-{pl}-all_ends"] = {"this": stiffness(c, own, "all_ends")}
    # mesh check: same physical sites on 2x and 4x refined backbones
    mesh = {f"scale{s}": stiffness(DISPERSED, 3, scale=s) for s in (1, 2, 4)}

    # 2. Designed equal-span families
    designed = []
    for name, c in designed_sets().items():
        row = {"name": name, "centers": c, **descriptors(c)}
        for own in (2, 3):
            row[f"K_own{own}"] = stiffness(c, own)
        designed.append(row)

    # 3. Random 6-subsets of admissible centers 1..29: joint decomposition of span vs clumpiness
    rng = np.random.default_rng(a.seed)
    seen, rand = set(), []
    while len(rand) < a.samples:
        c = tuple(sorted(rng.choice(np.arange(1, 30), 6, replace=False).tolist()))
        if c in seen:
            continue
        seen.add(c)
        row = {"centers": list(c), **descriptors(c)}
        for own in (2, 3):
            row[f"K_own{own}"] = stiffness(list(c), own)
        rand.append(row)

    analysis = {}
    for own in (2, 3):
        y = np.array([r[f"K_own{own}"] for r in rand])
        span = np.array([r["span"] for r in rand])
        C = np.array([r["C_h05"] for r in rand])
        nn = np.array([r["mean_nn"] for r in rand])
        cen = np.array([abs(r["centroid"] - 0.5) for r in rand])
        res = {}
        for label, X in {"span": span[:, None], "C": C[:, None], "mean_nn": nn[:, None],
                         "span+C": np.column_stack([span, C]),
                         "span+C+|centroid-0.5|": np.column_stack([span, C, cen])}.items():
            beta, r2 = ols(X, y)
            res[label] = {"R2": r2, "beta": beta.tolist()}
        # within-span-bin spread of K and of C (does clumpiness still matter at fixed span?)
        bins = []
        for lo in np.arange(0.2, 0.95, 0.1):
            m = (span >= lo) & (span < lo + 0.1)
            if m.sum() < 20:
                continue
            bc, r2c = ols(C[m][:, None], y[m])
            bins.append({"span_bin": [round(lo, 2), round(lo + 0.1, 2)], "n": int(m.sum()),
                         "K_min": float(y[m].min()), "K_max": float(y[m].max()),
                         "K_rel_range_pct": float(100 * (y[m].max() - y[m].min()) / y[m].mean()),
                         "C_range": [float(C[m].min()), float(C[m].max())],
                         "within_bin_R2_K_on_C": r2c, "slope_K_per_C": float(bc[1])})
        res["within_span_bins"] = bins
        res["K_range_all"] = [float(y.min()), float(y.max())]
        analysis[f"owners{own}"] = res

    summary = {"schema": "equal-span-shearlag-v1",
               "evidence_class": "independent reimplementation; dimensionless linear shear-lag toy; not MD or chemistry",
               "reproduction_of_codex": repro, "mesh_refinement_dispersed_owner3": mesh,
               "designed": designed, "random_subset_analysis": analysis,
               "random_samples": a.samples, "seed": a.seed}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with open(out / "random_subsets.csv", "w") as fh:
        keys = ["centers", "span", "centroid", "mean_nn", "gap_cv", "C_h05", "K_own2", "K_own3"]
        fh.write(",".join(keys) + "\n")
        for r in rand:
            fh.write(",".join(" ".join(map(str, r[k])) if k == "centers" else f"{r[k]:.8g}" for k in keys) + "\n")
    print(json.dumps({k: summary[k] for k in ("reproduction_of_codex", "mesh_refinement_dispersed_owner3")}, indent=1))
    for r in designed:
        print(f"{r['name']:26s} span={r['span']:.3f} C={r['C_h05']:.3f} nn={r['mean_nn']:.3f} "
              f"K2={r['K_own2']:.4f} K3={r['K_own3']:.4f}")
    for own, res in analysis.items():
        print(own, {k: round(v["R2"], 3) for k, v in res.items() if isinstance(v, dict) and "R2" in v})
        for b in res["within_span_bins"]:
            print("  ", b["span_bin"], "n", b["n"], "K range %.1f%%" % b["K_rel_range_pct"],
                  "R2(K~C) %.2f" % b["within_bin_R2_K_on_C"], "slope %.3f" % b["slope_K_per_C"])


if __name__ == "__main__":
    main()
