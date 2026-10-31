#!/usr/bin/env python3
"""Figures for run_organoid.py outputs.   python3 make_organoid_figures.py results/organoid/gpu"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# categorical slots in fixed order (validated palette, light surface); shapes are the secondary encoding
SERIES = [("none", "#2a78d6", "o"), ("pyridinoline", "#eb6834", "s"), ("glucosepane", "#1baf7a", "^"),
          ("dityrosine", "#eda100", "D"), ("isopeptide_TG2", "#e87ba4", "v"), ("Col IV ref", "#008300", "P")]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e1e0d9"
GENES_SHOW = ["CYR61", "CTGF", "ANKRD1", "AMOTL2", "ACTA2", "LOX", "MMP14", "LY6A", "LGR5", "KRT20", "MKI67"]


def style(ax):
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors=INK2, labelsize=8)


def series_of(row):
    return "Col IV ref" if row.collagen == "IV" else row.chem


def main(out: Path):
    gels = pd.read_csv(out / "gels.csv")
    if "z_target" not in gels:
        zt = pd.read_csv(out / "network.csv").groupby("gel").z_target.first()
        gels["z_target"] = gels.gel.map(zt)
    org = pd.read_csv(out / "organoid.csv")
    last = int(org.day.max())
    d = org[org.day == last].merge(gels, on="gel")
    d["series"] = d.apply(series_of, axis=1)
    figs = out / "figures"
    figs.mkdir(exist_ok=True)

    # 1. read-outs vs linear stiffness: vertical scatter at one stiffness = information beyond stiffness
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.4), sharex=True)
    for ax, ro, lab in zip(axes.ravel(), ["Y_mean", "ANKRD1_mean", "LY6A_mean", "LGR5_mean", "ACTA2_mean", "R_um"],
                           ["nuclear YAP", "ANKRD1", "LY6A (fetal/regen.)", "LGR5 (crypt stem)", "ACTA2 (MRTF)",
                            "organoid radius (µm)"]):
        style(ax)
        for name, col, mk in SERIES:
            s = d[d.series == name]
            if len(s):
                ax.scatter(s.E_lin_Pa, s[ro], s=22, c=col, marker=mk, edgecolors="#fcfcfb", linewidths=0.6,
                           label=name, alpha=0.9)
        ax.set_xscale("log")
        ax.set_title(lab, fontsize=9, color=INK, loc="left")
    for ax in axes[1]:
        ax.set_xlabel("gel linear Young's modulus (Pa)", fontsize=8, color=INK2)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=6, frameon=False, fontsize=8, title="crosslinker",
               title_fontsize=8)
    fig.suptitle(f"Day {last}: organoid read-outs against gel stiffness", fontsize=10, color=INK, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(figs / "readouts_vs_stiffness.png", dpi=160)
    plt.close(fig)

    # 2. R^2 stiffness-only vs network descriptors
    pr = pd.read_csv(out / f"analysis_day{last}_prediction.csv")
    pr = pr[pr.readout.str.endswith("_mean") | (pr.readout == "R_um")].copy()
    pr["name"] = pr.readout.str.replace("_mean", "")
    pr = pr.sort_values("R2_stiffness_only")
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    style(ax)
    y = np.arange(len(pr))
    ax.barh(y - 0.19, pr.R2_stiffness_only.clip(lower=0), 0.36, color="#86b6ef", label="linear stiffness only")
    ax.barh(y + 0.19, pr.R2_network_descriptors.clip(lower=0), 0.36, color="#2a78d6",
            label="+ stiffening, failure strain, mesh, alignment")
    ax.set_yticks(y, pr.name, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_xlabel("cross-validated R² across gels", fontsize=8, color=INK2)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title(f"Day {last}: what predicts each read-out", fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(figs / "r2_stiffness_vs_network.png", dpi=160)
    plt.close(fig)

    # 3. gene heat map, gels sorted by stiffness (sequential single hue)
    g = d.sort_values("E_lin_Pa")
    M = np.stack([g[f"{x}_mean"] for x in GENES_SHOW])
    fig, ax = plt.subplots(figsize=(11, 3.6))
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("blue", ["#f0efec", "#9ec5f4", "#2a78d6", "#0d366b"])
    im = ax.imshow(M, aspect="auto", cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
    ax.set_yticks(range(len(GENES_SHOW)), GENES_SHOW, fontsize=8)
    ax.set_xticks([])
    ax.set_xlabel(f"{len(g)} gels, sorted by linear stiffness ({g.E_lin_Pa.min():.0f} → {g.E_lin_Pa.max():.0f} Pa)",
                  fontsize=8, color=INK2)
    ax.set_title(f"Day {last}: mean expression (0–1 model units)", fontsize=10, color=INK, loc="left")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    fig.tight_layout()
    fig.savefig(figs / "expression_heatmap.png", dpi=160)
    plt.close(fig)

    # 4. trajectories: native vs most-crosslinked of each chemistry at z = 3.4
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax in axes:
        style(ax)
    z0 = gels.z_target.iloc[(gels.z_target - 3.4).abs().argmin()]
    for name, col, mk in SERIES:
        sel = gels[(gels.apply(series_of, axis=1) == name)]
        if name != "Col IV ref":
            sel = sel[np.isclose(sel.z_target, z0)]
        if name not in ("none", "Col IV ref"):
            sel = sel[(sel.dose == sel.dose.max()) & (sel["mode"] == "iso")]
        if not len(sel):
            continue
        gi = int(sel.gel.iloc[0])
        tr = org[org.gel == gi].sort_values("day")
        for ax, ro in zip(axes, ["R_um", "eps_mean", "ANKRD1_mean"]):
            ax.plot(tr.day, tr[ro], color=col, lw=2, marker=mk, ms=5, label=name)
    for ax, lab in zip(axes, ["organoid radius (µm)", "gel hoop strain at interface", "ANKRD1"]):
        ax.set_title(lab, fontsize=9, color=INK, loc="left")
        ax.set_xlabel("day", fontsize=8, color=INK2)
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(figs / "trajectories.png", dpi=160)
    plt.close(fig)
    print("figures in", figs)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
