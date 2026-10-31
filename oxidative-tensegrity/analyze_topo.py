#!/usr/bin/env python3
"""Pareto front, design rules and figure for a topo_opt.py run.

  python3 analyze_topo.py --tag ga_W12 [--reeval reeval_W16]
writes results/topo/<tag>_pareto.png and <tag>_summary.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "topo"

# reference data-viz palette (light): neutrals, sequential blue, categorical slot 2 for the front
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
C_INFEAS, C_FEAS, C_FRONT, C_ONSET = "#c3c2b7", "#86b6ef", "#eb6834", "#184f95"
MARKERS = dict(uniform="o", graded="^", layered="s", clustered="D", aligned="P")
ONSET = (3.2, 3.5)  # bending-stabilised rigidity onset in this model (results/cpu32 seed variance peak)
Z_ISO = 4.0         # central-force isostatic point


def spearman(a, b):
    ra, rb = pd.Series(a).rank(), pd.Series(b).rank()
    return float(np.corrcoef(ra, rb)[0, 1]) if len(ra) > 2 and ra.std() > 0 and rb.std() > 0 else float("nan")


def partial_spearman(a, b, c):
    """Spearman correlation of a and b after removing the linear effect of c from all three ranks."""
    R = np.stack([pd.Series(v).rank().to_numpy(float) for v in (a, b, c)], 1)
    if len(R) < 5 or np.any(R.std(0) == 0):
        return float("nan")
    C = np.c_[np.ones(len(R)), R[:, 2]]
    res = R[:, :2] - C @ np.linalg.lstsq(C, R[:, :2], rcond=None)[0]
    return float(np.corrcoef(res[:, 0], res[:, 1])[0, 1])


def md_table(df, floatfmt=3):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append(f"{v:.{floatfmt}g}" if isinstance(v, (float, np.floating)) else str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, lw=0.5)
    ax.set_axisbelow(True)


def scatter_sets(ax, d, x, y, front):
    inf = d[d.viol > 0]
    fea = d[(d.viol == 0) & ~d.index.isin(front.index)]
    ax.scatter(inf[x], inf[y], s=10, c=C_INFEAS, lw=0, label="outside stiffness band")
    ax.scatter(fea[x], fea[y], s=14, c=C_FEAS, lw=0, label="in band, dominated")
    for pat, m in MARKERS.items():
        f = front[front.pattern == pat]
        if len(f):
            ax.scatter(f[x], f[y], s=42, c=C_FRONT, marker=m, edgecolor="#fcfcfb", lw=1.0,
                       label=f"Pareto front: {pat}")


def figure(d, front, band, path, title):
    fig, axs = plt.subplots(2, 2, figsize=(10, 8.4), facecolor="#fcfcfb")
    axs = axs.ravel()
    panels = [("toughness", "max_drop", "toughness (worst of x/y pull)", "brittleness: largest stress drop / peak"),
              ("D_radial", "sensing", "transport: radial D/D0, exosome probe", "sensing: sqrt(T_ring x reach)"),
              ("z_matrix", "G", "matrix connectivity z", "shear modulus G (model units)"),
              ("toughness", "sensing", "toughness (worst of x/y pull)", "sensing: sqrt(T_ring x reach)")]
    for ax, (x, y, xl, yl) in zip(axs, panels):
        ax.set_facecolor("#fcfcfb")
        style(ax)
        if x == "z_matrix":
            ax.axvspan(*ONSET, color=C_ONSET, alpha=0.08, lw=0)
            ax.axvline(Z_ISO, color=C_ONSET, lw=1, ls="--")
            ax.axhspan(band["G_lo"], band["G_hi"], color=C_FRONT, alpha=0.08, lw=0)
            ax.set_yscale("log")
            ax.text(np.mean(ONSET), ax.get_ylim()[0] if False else d["G"].clip(lower=1e-6).min(),
                    "bending\nonset", color=C_ONSET, fontsize=7, ha="center", va="bottom")
            ax.text(Z_ISO + 0.04, d["G"].clip(lower=1e-6).min(), "isostatic\nz = 4", color=C_ONSET,
                    fontsize=7, va="bottom")
            ax.text(d["z_matrix"].max(), band["G_lo"] * 1.05,
                    f"YAP-responsive band\n{band['E_lo_Pa']:.0f}-{band['E_hi_Pa']:.0f} Pa", color=INK2,
                    fontsize=7, ha="right", va="bottom")
        scatter_sets(ax, d, x, y, front)
        ax.set_xlabel(xl, color=INK2, fontsize=9)
        ax.set_ylabel(yl, color=INK2, fontsize=9)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=8, labelcolor=INK2)
    fig.suptitle(title, color=INK, fontsize=11, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def rules(feas):
    """Design-rule tables among in-band designs."""
    out = []
    objs = [("toughness", "toughness"), ("max_drop", "brittleness"), ("strain_at_peak", "strain at peak"),
            ("sensing", "sensing"), ("T_ring", "T_ring"), ("decay_norm", "reach"), ("D_radial", "transport")]
    feats = [("z_matrix", "z (matrix)"), ("lock", "lock fraction"), ("pore", "pore radius"), ("amp", "amplitude")]
    rows = []
    for fc, fn in feats:
        rows.append(dict(feature=fn, **{on: spearman(feas[fc], feas[oc]) for oc, on in objs if oc in feas}))
    out.append("Spearman correlation, in-band designs (all patterns pooled):\n\n" + md_table(pd.DataFrame(rows), 2))
    prow = [dict(feature=fn, **{on: partial_spearman(feas[fc], feas[oc], feas["z_matrix"]) for oc, on in objs if oc in feas})
            for fc, fn in feats[1:]]
    out.append("Partial Spearman correlation controlling for z (inside the band, locks and pores trade off against "
               "connectivity, so the raw correlations above mix both):\n\n" + md_table(pd.DataFrame(prow), 2))
    keep = [c for c, _ in objs if c in feas] + ["z_matrix", "G"]
    for key, name in (("pattern", "pattern"), ("place", "lock placement (designs with lock >= 0.2)")):
        sub = feas if key == "pattern" else feas[feas["lock"] >= 0.2]
        if not len(sub):
            continue
        t = sub.groupby(key)[keep].median().reset_index()
        t.insert(1, "n", sub.groupby(key).size().to_numpy())
        out.append(f"Median by {name}:\n\n" + md_table(t, 3))
    g = feas[feas.pattern == "graded"]
    if len(g) >= 4:
        t = g.assign(sign=np.where(g.amp > 0, "denser near pore", "sparser near pore")).groupby("sign")[keep].median()
        t.insert(0, "n", g.assign(sign=np.where(g.amp > 0, 1, 0)).groupby(np.where(g.amp > 0, "denser near pore",
                                                                                      "sparser near pore")).size())
        out.append("Graded designs by gradient sign (median):\n\n" + md_table(t.reset_index(), 3))
    return "\n\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--reeval", nargs="*", default=[], help="tags of --reeval runs of this front")
    a = ap.parse_args()
    band = json.loads((OUT / "yap_band.json").read_text())
    d = pd.read_csv(OUT / f"{a.tag}_designs.csv")
    ev = pd.read_csv(OUT / f"{a.tag}_evals.csv")
    feas = d[d.viol == 0]
    front = d[(d["rank"] == 0) & (d.viol == 0)]
    figure(d, front, band, OUT / f"{a.tag}_pareto.png",
           f"Topology search {a.tag}: {len(d)} designs, {len(feas)} in the stiffness band, "
           f"{len(front)} on the Pareto front")

    md = [f"# Topology optimisation summary: `{a.tag}`", "",
          "Generated by `analyze_topo.py`. Model outputs (oxt/network.py, Col I parameters), not measurements.", "",
          f"- designs evaluated: {len(d)} ({len(ev)} realisations, W = {int(d.W.iloc[0])}), "
          f"generations: {int(d.gen.max()) + 1}",
          f"- stiffness band (model assumption, from oxt/cell.py YAP 25-75%): E = {band['E_lo_Pa']:.0f}-"
          f"{band['E_hi_Pa']:.0f} Pa, G = {band['G_lo']:.4f}-{band['G_hi']:.4f} model units",
          f"- in band: {len(feas)}; feasible Pareto front: {len(front)}",
          f"- rupture pull skipped (G more than 3x outside the band) for {int(ev.get('fail_skipped', pd.Series(dtype=bool)).sum())} "
          "realisations", ""]
    if len(feas):
        zq = feas["z_matrix"].quantile([0.1, 0.5, 0.9]).to_numpy()
        zf = front["z_matrix"].quantile([0.1, 0.5, 0.9]).to_numpy() if len(front) else [np.nan] * 3
        md += [f"- z_matrix of in-band designs: 10/50/90% = {zq[0]:.2f} / {zq[1]:.2f} / {zq[2]:.2f}",
               f"- z_matrix of the front: 10/50/90% = {zf[0]:.2f} / {zf[1]:.2f} / {zf[2]:.2f} "
               f"(bending onset {ONSET[0]}-{ONSET[1]}, isostatic {Z_ISO})", ""]
    cols = ["design", "gen", "pattern", "amp", "scale", "lock", "place", "pore", "z_matrix", "G", "E_Pa",
            "toughness", "max_drop", "strain_at_peak", "max_avalanche", "T_ring", "decay_norm", "sensing",
            "D_radial"]
    if len(front):
        md += ["## Pareto front (in band, rank 0), by toughness", "",
               md_table(front.sort_values("toughness", ascending=False)[[c for c in cols if c in front]], 3), ""]
    if len(feas) >= 6:
        md += ["## Design rules (associations among in-band designs)", "", rules(feas), ""]
    conv = d.groupby("gen").agg(n=("design", "size"), in_band=("viol", lambda v: int((v == 0).sum())),
                                best_toughness=("toughness", "max"), best_sensing=("sensing", "max"),
                                min_violation=("viol", "min")).reset_index()
    md += ["## Convergence by generation (offspring only)", "", md_table(conv, 3), ""]
    for rtag in a.reeval:
        r = pd.read_csv(OUT / f"{rtag}_designs.csv")
        m = r.merge(d, left_on="src_design", right_on="design", suffixes=("_re", ""))
        comp = pd.DataFrame(dict(
            quantity=["G", "toughness", "max_drop", "sensing", "D_radial"],
            spearman=[spearman(m[f"{q}_re"], m[q]) for q in ["G", "toughness", "max_drop", "sensing", "D_radial"]],
            median_ratio=[float(np.median(m[f"{q}_re"] / m[q].replace(0, np.nan)))
                          for q in ["G", "toughness", "max_drop", "sensing", "D_radial"]]))
        fr = r[r.src_design >= 0]
        md += [f"## Re-evaluation of the front: `{rtag}` (W = {int(r.W.iloc[0])}, "
               f"{int(r.n_reps.iloc[0])} realisations each)", "",
               f"{int((fr.viol == 0).sum())} of {len(fr)} front designs stay in the stiffness band. "
               "Rank correlation and median ratio (re-evaluated / original) per quantity:", "",
               md_table(comp, 3), "",
               "All re-evaluated designs, with plain uniform unlocked baselines (src_design = -1) at the median "
               "front pore size; rank is recomputed within this set:", "",
               md_table(r.sort_values(["viol", "rank"])[["src_design"] + [c for c in cols[2:] if c in r]
                                                        + ["viol", "rank"]], 3), ""]
        figure(r, r[(r['rank'] == 0) & (r.viol == 0)], band, OUT / f"{rtag}_pareto.png",
               f"Front of {a.tag} re-evaluated at W = {int(r.W.iloc[0])}")
    (OUT / f"{a.tag}_summary.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
