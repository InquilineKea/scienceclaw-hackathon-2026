#!/usr/bin/env python3
"""Finite-size comparison of the rigidity onset: G(z) and its seed-to-seed spread at several lattice sizes.

  python3 analyze_fss.py results/phase/cpu32.csv results/phase/fss_W16.csv
Writes results/phase/fss.png and fss_summary.md. Lattice size W comes from each CSV's _params.json.
Two sizes are enough to see where fluctuations stay large, not to fit critical exponents.
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

SERIES = [("LOX lock 0", 0.0, 0.0, "#2a6fdb"), ("LOX lock 1", 1.0, 0.0, "#7a4fd0"), ("AGE dose 1", 0.0, 1.0, "#c8402e")]
STYLE = {12: dict(ls="--", marker="s"), 16: dict(ls="-", marker="o"), 24: dict(ls="-", marker="D"), 32: dict(ls="-", marker="^")}


def main(paths):
    frames = []
    for p in map(Path, paths):
        d = pd.read_csv(p)
        d["W"] = json.loads(p.with_name(p.stem + "_params.json").read_text())["W"]
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    lines = ["| series | W | seeds | z of largest G spread (CV) | max CV | G at z≈3.5 | G at z≈4.2 |", "|---|---|---|---|---|---|---|"]
    for name, lk, ds, col in SERIES:
        for W, s in df[(df["lock"] == lk) & (df["dose"] == ds)].groupby("W"):
            g = s.groupby("z_target").agg(z=("z", "mean"), G=("G", "mean"), cv=("G", lambda x: x.std() / x.mean()),
                                          n=("G", "size"))
            g = g[(g["z"] > 2.7) & (g["z"] < 4.9)].sort_values("z")
            st = STYLE.get(W, {})
            ax[0].plot(g["z"], g["G"], color=col, ms=4, lw=1.6, label=f"{name}, W={W}", **st)
            ax[1].plot(g["z"], g["cv"], color=col, ms=4, lw=1.6, **st)
            k = int(np.argmax(g["cv"].to_numpy()))
            near = lambda z0: g.iloc[int(np.argmin(np.abs(g["z"].to_numpy() - z0)))]["G"]
            lines.append(f"| {name} | {W} | {int(g['n'].max())} | {g['z'].iloc[k]:.2f} | {g['cv'].iloc[k]:.2f} | "
                         f"{near(3.5):.1e} | {near(4.2):.1e} |")
    ax[0].set_yscale("log")
    ax[0].set_title("shear modulus G vs connectivity, two lattice sizes", loc="left", fontsize=11)
    ax[1].set_title("seed-to-seed spread of G (coefficient of variation)", loc="left", fontsize=11)
    for a in ax:
        a.axvline(4.0, color="0.55", lw=1, ls="--")
        a.set_xlabel("realised mean connectivity z")
        a.grid(alpha=0.25, lw=0.6)
    ax[0].legend(fontsize=8, frameon=False, ncol=2)
    out = Path(paths[0]).with_name("fss.png")
    fig.savefig(out, dpi=150)
    Path(out).with_name("fss_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
