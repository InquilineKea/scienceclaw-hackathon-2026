#!/usr/bin/env python3
"""Locate transitions in run_phase.py sweeps and draw the phase figure.

  python3 analyze_phase.py results/phase/cpu32.csv [results/phase/tough.csv ...]
Writes phase_transitions.json, phase_summary.md and phase.png next to the first CSV. Several CSVs (each with
its own <stem>_params.json strain grid) are pooled; seeds are distinct across runs.

Markers, on the realised connectivity z (means over seeds):
  z_perc       largest cluster first holds >= 90% of nodes (connectivity percolation, the gel point)
  z_logslope   steepest rise of log10 G with z (onset of bending-stabilised rigidity)
  z_stretch0   a straight-line fit of G on the stretching branch (z > 4.3) extrapolates to G = 0
               (the central-force rigidity point; Maxwell counting gives 4 in 2D)
  z_brittle    largest rupture avalanche first exceeds 5% of bonds (onset of brittle, crack-like failure)
  useful window  G >= 1% of the stiffest network AND strain at peak >= 0.15
Brittleness is the largest single-step rupture avalanche (fraction of bonds); "work to peak" is the
area under the stress-strain curve up to peak stress (energy absorbed before the network starts to fail).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SERIES = [  # fixed order -> fixed colour
    ("LOX lock 0", dict(lock=0.0, dose=0.0), "#2a6fdb"),
    ("LOX lock 0.5", dict(lock=0.5, dose=0.0), "#16a3a3"),
    ("LOX lock 1", dict(lock=1.0, dose=0.0), "#7a4fd0"),
    ("AGE dose 0.5", dict(lock=0.0, dose=0.5), "#e08a1e"),
    ("AGE dose 1", dict(lock=0.0, dose=1.0), "#c8402e"),
]
G_FRAC, EPS_MIN = 0.01, 0.15


def load(paths):
    frames = []
    for p in map(Path, paths):
        d = pd.read_csv(p)
        eps = np.asarray(json.loads(p.with_name(p.stem + "_params.json").read_text())["fail"])
        if "curve" in d:
            w = []
            for c in d["curve"]:
                s = np.clip(np.asarray(json.loads(c)), 0, None)
                k = int(np.argmax(s))
                w.append(float(np.trapz(np.r_[0, s[:k + 1]], np.r_[0, eps[:k + 1]])))
            d["work_to_peak"] = w
        d["run"] = p.stem
        frames.append(d.drop(columns=["curve"], errors="ignore"))
    return pd.concat(frames, ignore_index=True)


def series(df, sel):
    s = df[(df["lock"] == sel["lock"]) & (df["dose"] == sel["dose"])].copy()
    s["logG"] = np.log10(s["G"].clip(lower=1e-7))
    # z_target above the lattice's maximum gives identical networks: bin on realised z instead
    s["zbin"] = (s.groupby("z_target")["z"].transform("mean")).round(2)
    g = s.groupby("zbin")
    m, sd = g.mean(numeric_only=True), g.std(numeric_only=True)
    m["n"] = g.size()
    return m.sort_index(), sd.sort_index()


def first_cross(x, y, thr):
    for i in range(1, len(x)):
        if y[i - 1] < thr <= y[i]:
            return float(x[i - 1] + (thr - y[i - 1]) * (x[i] - x[i - 1]) / (y[i] - y[i - 1]))
    return None


def transitions(m):
    z = m.index.to_numpy(dtype=float)
    lg = m["logG"].to_numpy()
    mid = 0.5 * (z[1:] + z[:-1])
    slope = np.diff(lg) / np.diff(z)
    k = int(np.argmax(slope))
    hi = z > 4.3
    z0 = None
    if hi.sum() >= 2:
        a, b = np.polyfit(z[hi], m["G"].to_numpy()[hi], 1)
        z0 = float(-b / a)
    useful = (m["G"] >= G_FRAC * m["G"].max()) & (m["strain_at_peak"] >= EPS_MIN)
    uz = z[useful.to_numpy()]
    out = dict(z_perc=first_cross(z, m["giant"].to_numpy(), 0.9),
               z_brittle=first_cross(z, m["max_avalanche"].to_numpy(), 0.05), z_logslope=float(mid[k]),
               dlogG_dz_max=float(slope[k]), z_stretch0=z0,
               useful_window=[float(uz.min()), float(uz.max())] if uz.size else None,
               G_range=[float(m["G"].min()), float(m["G"].max())])
    if "work_to_peak" in m:
        out["z_max_work_to_peak"] = float(z[int(np.nanargmax(m["work_to_peak"].to_numpy()))])
    return out


def main(paths):
    df = load(paths)
    first = Path(paths[0])
    out = {}
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.5), constrained_layout=True)
    panels = [("G", "shear modulus G (log)", True), ("strength", "tensile strength (peak stress)", False),
              ("strain_at_peak", "strain at peak stress (extensibility)", False),
              ("work_to_peak", "work to peak stress (energy absorbed before failure)", False),
              ("max_avalanche", "largest rupture avalanche (fraction of bonds)", False),
              ("giant", "largest-cluster fraction (connectivity percolation)", False)]
    for name, sel, col in SERIES:
        if not ((df["lock"] == sel["lock"]) & (df["dose"] == sel["dose"])).any():
            continue
        m, sd = series(df, sel)
        out[name] = transitions(m)
        out[name]["n_per_point"] = [int(v) for v in m["n"]]
        for a, (key, lab, logy) in zip(ax.flat, panels):
            if key not in m:
                continue
            a.errorbar(m.index, m[key], yerr=sd[key], color=col, lw=2, marker="o", ms=4, capsize=2, label=name)
            if logy:
                a.set_yscale("log")
            a.set_title(lab, fontsize=11, loc="left")
    base = out.get("LOX lock 0", {})
    for a in ax.flat:
        a.axvline(4.0, color="0.55", lw=1, ls="--")
        if base.get("useful_window"):
            a.axvspan(*base["useful_window"], color="#2a6fdb", alpha=0.07, lw=0)
        a.set_xlabel("realised mean connectivity z")
        a.grid(alpha=0.25, lw=0.6)
    ax[0, 2].axhline(EPS_MIN, color="0.55", lw=1, ls=":")
    ax[0, 0].legend(fontsize=8, frameon=False)
    seeds = df.groupby("run")["seed"].nunique().to_dict()
    fig.suptitle("Col I fibre network (2D, W=12) vs connectivity, LOX locking and AGE dose  |  dashed: isostatic "
                 f"z = 4; shaded: healthy useful window  |  seeds {sum(seeds.values())}", fontsize=11)
    fig.savefig(first.with_name("phase.png"), dpi=150)
    first.with_name("phase_transitions.json").write_text(json.dumps(out, indent=1))

    f = lambda v: "—" if v is None else f"{v:.2f}"
    lines = ["| series | gel point z_perc | steepest log G rise | stretching branch G→0 | brittle onset (avalanche > 5%) | useful window "
             f"(G ≥ {G_FRAC:.0%} max, ε_peak ≥ {EPS_MIN}) | max work to peak at z | G span |",
             "|---|---|---|---|---|---|---|---|"]
    for k, t in out.items():
        uw = "—" if not t["useful_window"] else f"{t['useful_window'][0]:.2f}–{t['useful_window'][1]:.2f}"
        lines.append(f"| {k} | {f(t['z_perc'])} | {f(t['z_logslope'])} | {f(t['z_stretch0'])} | {f(t['z_brittle'])} | {uw} | "
                     f"{f(t.get('z_max_work_to_peak'))} | {t['G_range'][0]:.1e} → {t['G_range'][1]:.1e} |")
    first.with_name("phase_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:] or ["results/phase/cpu32.csv"])
