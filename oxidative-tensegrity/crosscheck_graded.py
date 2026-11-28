#!/usr/bin/env python3
"""Decide, by the rule in results/topo/graded_crosscheck_protocol.json, whether pymoo's graded front designs
survive 8 realisations at W=12 and W=16.

  python3 crosscheck_graded.py            # reads results/topo/graded_x8_W{12,16}_*.csv
writes results/topo/graded_crosscheck_summary.json and prints a table.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "results" / "topo"
# primary objectives on 8-realisation means: (column, +1 maximise / -1 minimise)
MEAN_OBJ = [("toughness_mean", +1), ("drop_mean", -1), ("sensing", +1), ("D_radial", +1)]
# secondary: topo_opt's own worst-case aggregate (min toughness, max drop over realisations)
WORST_OBJ = [("toughness", +1), ("max_drop", -1), ("sensing", +1), ("D_radial", +1)]


def load(W):
    d = pd.read_csv(OUT / f"graded_x8_W{W}_designs.csv")
    e = pd.read_csv(OUT / f"graded_x8_W{W}_evals.csv")
    g = e.groupby("design")
    d = d.merge(pd.DataFrame(dict(drop_mean=g["max_drop"].mean(), n_ok=g["toughness"].count(),
                                  T_ring_se=g["T_ring"].std() / np.sqrt(g.size()),
                                  tough_se=g["toughness"].std() / np.sqrt(g.size()),
                                  in_band_reps=g["G"].apply(lambda v: int(v.between(*BAND).sum())))),
                left_on="design", right_index=True)
    d["label"] = d["src_design"]
    d["group"] = d["label"].map(GROUP)
    return d.set_index("label")


def dominated_by(row, others, obj):
    """Labels of comparators that dominate `row` (at least as good on all, strictly better on one)."""
    a = np.array([s * row[c] for c, s in obj])
    hits = []
    for lab, o in others.iterrows():
        b = np.array([s * o[c] for c, s in obj])
        if np.all(b >= a) and np.any(b > a):
            hits.append(lab)
    return hits


band = json.loads((OUT / "yap_band.json").read_text())
BAND = (band["G_lo"], band["G_hi"])
proto = json.loads((OUT / "graded_crosscheck_protocol.json").read_text())
GROUP = {**{k: "graded" for k in proto["graded_real_gradient"]}, **{k: "sanity" for k in proto["sanity"]},
         **{k: "comparator" for k in proto["comparators"]}}

res = {W: load(W) for W in (12, 16)}
rows, verdict = [], {}
for lab in proto["graded_real_gradient"] + proto["sanity"]:
    rec = dict(design=lab, group=GROUP[lab])
    ok_all = True
    for W, d in res.items():
        if lab not in d.index:
            rec[f"W{W}"] = "not run"
            ok_all = False
            continue
        r = d.loc[lab]
        comp = d[(d.group == "comparator") & (d.viol == 0)]
        in_band = bool(r.viol == 0)
        dom_mean = dominated_by(r, comp, MEAN_OBJ) if in_band else []
        dom_worst = dominated_by(r, comp, WORST_OBJ) if in_band else []
        rec.update({f"W{W}_G": round(float(r.G), 5), f"W{W}_in_band": in_band,
                    f"W{W}_reps_in_band": int(r.in_band_reps), f"W{W}_dominated_by_mean": dom_mean,
                    f"W{W}_dominated_by_worst": dom_worst, f"W{W}_toughness_mean": round(float(r.toughness_mean), 5),
                    f"W{W}_drop_mean": round(float(r.drop_mean), 3), f"W{W}_sensing": round(float(r.sensing), 3),
                    f"W{W}_T_ring": round(float(r.T_ring), 4), f"W{W}_D_radial": round(float(r.D_radial), 3)})
        ok_all &= in_band and not dom_mean
    rec["survives_primary"] = ok_all
    rows.append(rec)
    verdict[lab] = ok_all

comp_tab = {W: d[d.group == "comparator"][["G", "viol", "in_band_reps", "toughness_mean", "drop_mean", "sensing",
                                            "T_ring", "D_radial"]].round(5).reset_index().to_dict("records")
            for W, d in res.items()}
summary = dict(protocol=proto, band=BAND, graded=rows, comparators=comp_tab,
               any_graded_survives=any(verdict[k] for k in proto["graded_real_gradient"]),
               any_graded_in_band_both_W=any(r.get("W12_in_band") and r.get("W16_in_band") for r in rows
                                             if r["group"] == "graded"))
(OUT / "graded_crosscheck_summary.json").write_text(json.dumps(summary, indent=1, default=str))

cols = ["design", "group", "W12_G", "W12_reps_in_band", "W12_in_band", "W16_G", "W16_reps_in_band", "W16_in_band",
        "W12_sensing", "W16_sensing", "W12_toughness_mean", "W16_toughness_mean", "survives_primary"]
print(pd.DataFrame(rows).reindex(columns=cols).to_string(index=False))
for W in (12, 16):
    print(f"\ncomparators W={W}")
    print(pd.DataFrame(comp_tab[W]).to_string(index=False))
    for r in rows:
        if r.get(f"W{W}_in_band"):
            print(f"  {r['design']} dominated by (means): {r[f'W{W}_dominated_by_mean']}  (worst-case): "
                  f"{r[f'W{W}_dominated_by_worst']}")
print("\nany graded design survives (primary rule):", summary["any_graded_survives"])
print("any graded design in band at both W:", summary["any_graded_in_band_both_W"])
