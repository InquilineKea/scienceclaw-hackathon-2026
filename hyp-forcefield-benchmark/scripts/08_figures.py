"""Step 7: figures from results/*.json -> figs/*.png  (only from data that exists; nothing is interpolated)."""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import analysis as an  # noqa: E402
from hypbench.ffreg import FORCEFIELDS, ROOT  # noqa: E402

R, F = os.path.join(ROOT, "results"), os.path.join(ROOT, "figs")
os.makedirs(F, exist_ok=True)
FFS = list(FORCEFIELDS)
# categorical slots in fixed order (validated palette, light surface); second encoding = marker / dash
COL = dict(zip(FFS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
MRK = dict(zip(FFS, ["o", "s", "^", "D", "v"]))
DASH = dict(zip(FFS, ["-", "-", "-", "-", (0, (4, 2))]))
LAB = dict(zip(FFS, ["ff99SB", "ff14SB", "ff19SB", "CHARMM36m", "CHARMM36mGP"]))
INK, INK2, MUTED, SURF, GRID = "#0b0b0b", "#52514e", "#8a8983", "#fcfcfb", "#e6e5e0"
SEQ = LinearSegmentedColormap.from_list("seq", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
DIV = LinearSegmentedColormap.from_list("div", ["#1c5cab", "#86b6ef", "#ecebe7", "#f0a184", "#c2461a"])
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlecolor": INK, "legend.frameon": False,
                     "savefig.facecolor": SURF, "font.family": "DejaVu Sans"})


def save(fig, name):
    fig.savefig(os.path.join(F, name), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


Q = json.load(open(os.path.join(R, "qm_vs_mm.json")))
M = json.load(open(os.path.join(R, "md_summary.json")))
D = np.load(os.path.join(R, "md_distributions.npz"))
REF = M["reference"]

# ------------------------------------------------------------------ Fig 1: pucker scan + conformers
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.6), gridspec_kw=dict(width_ratios=[1.25, 1]))
p = Q["scans"]["pucker"]
a = ax[0]
a.plot(p["x"], p["dft"], color=INK, lw=2, marker="o", ms=5, label="DFT (B3LYP-D3BJ/def2-SVP)", zorder=5)
a.plot(p["x"], p["xtb"], color=MUTED, lw=1, ls=":", label="GFN2-xTB (geometry level)")
for ff in FFS:
    a.plot(p["x"], p["mm"][ff], color=COL[ff], lw=2, ls=DASH[ff], marker=MRK[ff], ms=4, label=LAB[ff])
a.axvline(0, color=GRID, lw=1)
a.set_ylim(-0.6, 5.6)
a.text(-44, -0.45, "← Cγ-endo", color=INK2, va="bottom")
a.text(44, -0.45, "Cγ-exo →", color=INK2, va="bottom", ha="right")
a.set_xlabel("χ2 = Cα–Cβ–Cγ–Cδ (deg), constrained")
a.set_ylabel("Energy relative to exo minimum (kcal/mol)")
a.set_title("Ring-pucker scan, gas phase (ψ = 150°, OH anti)")
a.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=4)
a = ax[1]
if "conformers" in Q:
    c = Q["conformers"]
    x = np.arange(len(c["labels"]))
    off = np.linspace(-0.3, 0.3, len(FFS) + 1)
    a.scatter(x + off[0], c["dft"], color=INK, marker="_", s=260, lw=3, label="DFT", zorder=5)
    for k, ff in enumerate(FFS):
        ok = np.array([(ch > 0) == lab.startswith("exo") for ch, lab in zip(c["mm_chi2"][ff], c["labels"])])
        y = np.array(c["mm"][ff])
        a.scatter(x[ok] + off[k + 1], y[ok], color=COL[ff], marker=MRK[ff], s=34, edgecolor=SURF, lw=0.6, zorder=4)
        a.scatter([], [], color=COL[ff], marker=MRK[ff], s=34, label=LAB[ff])
        a.scatter(x[~ok] + off[k + 1], y[~ok], facecolor="none", edgecolor=COL[ff], marker=MRK[ff], s=34, zorder=4)
    a.set_xticks(x)
    a.set_xticklabels([l.replace(" / ", "\n") for l in c["labels"]], fontsize=7.5)
    a.set_ylabel("Energy relative to exo / OH 180 (kcal/mol)")
    a.set_title("Six conformers: 2 puckers × 3 hydroxyl rotamers")
    a.set_ylim(-2.0, 4.8)
    a.legend(fontsize=7.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    a.text(0.01, 0.98, "hollow marker: MM structure left its pucker basin", transform=a.transAxes, ha="left", va="top", fontsize=7, color=MUTED)
save(fig, "fig1_dft_vs_mm_pucker.png")

# ------------------------------------------------------------------ Fig 2: psi scan
if "psi_exo" in Q["scans"]:
    p = Q["scans"]["psi_exo"]
    fig, a = plt.subplots(figsize=(6.4, 3.8))
    x = np.array(p["x"])
    a.plot(x, p["dft"], color=INK, lw=2, marker="o", ms=5, label="DFT", zorder=5)
    for ff in FFS:
        a.plot(x, p["mm"][ff], color=COL[ff], lw=2, ls=DASH[ff], marker=MRK[ff], ms=4, label=LAB[ff])
    a.set_xlabel("ψ = N–Cα–C–N (deg), constrained; ring held Cγ-exo")
    a.set_ylabel("Energy relative to ψ = 150° (kcal/mol)")
    a.set_title(f"Backbone ψ scan, gas phase ({len(x)} DFT points)")
    a.set_xticks(np.arange(-180, 181, 60))
    a.legend(fontsize=7.5, ncol=2)
    save(fig, "fig2_psi_scan.png")

# ------------------------------------------------------------------ Fig 3: dipeptide pucker free-energy surfaces
have = [ff for ff in FFS if f"dipeptide_{ff}|HYP|chi2" in D]
if have:
    fig, axs = plt.subplots(2, 3, figsize=(11.5, 7.4), layout="constrained")
    axs = axs.ravel()
    bins = np.linspace(-55, 55, 45)
    for k, ff in enumerate(have):
        P, amp = np.radians(D[f"dipeptide_{ff}|HYP|P"]), D[f"dipeptide_{ff}|HYP|amp"]
        xe, ye, fe, h = an.free_energy_2d(amp * np.cos(P), amp * np.sin(P), [bins, bins])
        fe = np.where(h >= 2, fe, np.nan)  # bins with <2 counts are not drawn
        a = axs[k]
        im = a.pcolormesh(xe, ye, fe, cmap=SEQ.reversed(), vmin=0, vmax=3.5, shading="flat")
        a.set_title(f"{LAB[ff]} in {M['runs'][f'dipeptide_{ff}']['water']}, {M['runs'][f'dipeptide_{ff}']['ps']:.0f} ps", fontsize=9)
        a.set_aspect("equal")
        a.axvline(0, color=MUTED, lw=0.6)
        a.text(-53, 47, "endo", color=INK2, fontsize=8)
        a.text(53, 47, "exo", color=INK2, fontsize=8, ha="right")
        a.set_xlabel("q·cos P  (≈ χ2, deg)")
        a.set_ylabel("q·sin P (deg)")
        e = M["runs"][f"dipeptide_{ff}"]["residues"]["HYP"]
        a.text(0, -50, f"endo {100*e['endo']:.0f} ± {100*e['endo_se']:.0f} %", ha="center", fontsize=8, color=INK)
    for k in range(len(have), 5):
        axs[k].axis("off")
        axs[k].text(0.5, 0.5, "not run", ha="center", color=MUTED, transform=axs[k].transAxes)
    cb = fig.colorbar(im, ax=axs[:3].tolist(), shrink=0.8, pad=0.02)
    cb.set_label("Free energy (kcal/mol), 300 K")
    a = axs[5]
    b1 = np.linspace(-55, 55, 34)
    for ff in have:
        x, f, h = an.free_energy_1d(D[f"dipeptide_{ff}|HYP|chi2"], b1)
        f = np.where(h >= 2, f, np.nan)
        a.plot(x, f, color=COL[ff], lw=2, ls=DASH[ff], label=LAB[ff])
    a.set_xlabel("χ2 (deg)")
    a.set_ylabel("Free energy (kcal/mol)")
    a.set_title("1D profile along χ2")
    a.set_ylim(0, 4.5)
    a.legend(fontsize=7.5)
    fig.suptitle("Ace-Hyp-NMe in explicit water: ring-pucker free-energy surfaces (pseudorotation plane)", color=INK, fontsize=11, fontweight="bold")
    save(fig, "fig4_pucker_fes_dipeptide.png")

# ------------------------------------------------------------------ Fig 4: endo populations vs experiment
groups = [("Hyp, Ace-Hyp-NMe", "dipeptide", "HYP", REF["hyp_endo_exp"]), ("Hyp (Y), triple helix", "helix", "HYP", REF["hyp_endo_exp"]),
          ("Pro (X), triple helix", "helix", "PRO", REF["pro_endo_exp"])]
fig, axs = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for a, (title, system, rn, exp) in zip(axs, groups):
    for k, ff in enumerate(FFS):
        key = f"{system}_{ff}"
        if key in M["runs"]:
            e = M["runs"][key]["residues"][rn]
            a.bar(k, 100 * e["endo"], width=0.62, color=COL[ff], yerr=100 * (e["endo_se"] if np.isfinite(e["endo_se"]) else 0),
                  error_kw=dict(ecolor=INK2, lw=1, capsize=2))
            a.text(k, 100 * e["endo"] + 100 * (e["endo_se"] if np.isfinite(e["endo_se"]) else 0) + 2, f"{100*e['endo']:.0f}", ha="center", fontsize=8, color=INK)
        else:
            a.text(k, 3, "not\nrun", ha="center", fontsize=7, color=MUTED)
        lit = REF["lit_md_endo"].get(ff)
        if lit and system == "helix":
            a.scatter(k, 100 * lit[rn], marker="D", s=30, facecolor=SURF, edgecolor=INK, zorder=6, label="published long MD" if k == 0 else None)
    a.axhline(100 * exp, color=INK, lw=1.2, ls=(0, (5, 3)))
    a.text(4.45, 100 * exp + 1.5, f"NMR reference {100*exp:.0f}% (triple helix)", ha="right", fontsize=7.5, color=INK)
    a.set_xticks(range(5))
    a.set_xticklabels([LAB[f].replace("CHARMM", "C") for f in FFS], fontsize=7.5, rotation=20)
    a.set_title(title)
    a.set_ylim(0, 100)
    a.grid(axis="x", visible=False)
axs[0].set_ylabel("Cγ-endo population (%)")
axs[1].legend(fontsize=7.5, loc="upper left")
save(fig, "fig3_pucker_populations.png")

# ------------------------------------------------------------------ Fig 5: residue interaction maps (helix)
hk = [ff for ff in FFS if f"helix_{ff}" in M["runs"]]
if hk and "helix_crystal" in M:
    c0 = np.array(M["helix_crystal"]["contact_matrix"])
    labels = M["helix_crystal"]["labels"]
    fig, axs = plt.subplots(2, 3, figsize=(11.5, 7.6), layout="constrained")
    axs = axs.ravel()
    im0 = axs[0].imshow(c0, cmap=SEQ, vmin=0, vmax=1)
    axs[0].set_title("Crystal segment: contact (dark) / none", fontsize=9)
    for k, ff in enumerate(FFS):
        a = axs[k + 1]
        if ff in hk:
            cm = np.array(M["runs"][f"helix_{ff}"]["contact_matrix"])
            im1 = a.imshow(cm - c0, cmap=DIV, vmin=-1, vmax=1)
            a.set_title(f"{LAB[ff]} − crystal, {M['runs'][f'helix_{ff}']['ps']:.0f} ps", fontsize=9)
        else:
            a.text(0.5, 0.5, "not run", ha="center", color=MUTED, transform=a.transAxes)
            a.set_title(LAB[ff])
    for a in axs:
        a.grid(False)
        a.set_xticks([4, 13, 22])
        a.set_xticklabels(["chain A", "chain B", "chain C"])
        a.set_yticks([4, 13, 22])
        a.set_yticklabels(["A", "B", "C"])
        for b in (8.5, 17.5):
            a.axhline(b, color=MUTED, lw=0.5)
            a.axvline(b, color=MUTED, lw=0.5)
    if hk:
        fig.colorbar(im1, ax=axs.tolist(), shrink=0.6, label="Δ contact frequency (simulation − crystal)")
    fig.suptitle("(Pro-Hyp-Gly)3 triple helix: residue–residue heavy-atom contacts within 4 Å", color=INK, fontsize=11, fontweight="bold")
    save(fig, "fig7_helix_residue_interactions.png")

# ------------------------------------------------------------------ Fig 6: where the force fields diverge
keys = [k for k in ("dipeptide:HYP:chi2", "helix:HYP:chi2", "helix:PRO:chi2", "helix:HYP:phi", "helix:HYP:psi", "helix:GLY:psi") if k in M["js_divergence"]]
if keys:
    fig, axs = plt.subplots(1, len(keys), figsize=(2.6 * len(keys) + 1.2, 3.4), layout="constrained")
    axs = np.atleast_1d(axs)
    for a, k in zip(axs, keys):
        d = M["js_divergence"][k]
        m = np.array(d["matrix"])
        im = a.imshow(m, cmap=SEQ, vmin=0, vmax=0.6)
        n = len(d["ffs"])
        a.set_xticks(range(n))
        a.set_yticks(range(n))
        short = [LAB[f].replace("CHARMM", "C") for f in d["ffs"]]
        a.set_xticklabels(short, rotation=60, fontsize=7)
        a.set_yticklabels(short if a is axs[0] else [""] * n, fontsize=7)
        for i in range(n):
            for j in range(n):
                a.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=6.5, color=SURF if m[i, j] > 0.35 else INK)
        s, rn, var = k.split(":")
        a.set_title(f"{rn.capitalize()} {var}, {s}", fontsize=9)
        a.grid(False)
    fig.colorbar(im, ax=axs.tolist(), shrink=0.8, label="Jensen–Shannon divergence (bits)")
    save(fig, "fig6_forcefield_divergence.png")

# ------------------------------------------------------------------ Fig 7: convergence of the dipeptide populations
if have:
    fig, a = plt.subplots(figsize=(6.4, 3.6))
    for ff in have:
        chi2 = D[f"dipeptide_{ff}|HYP|chi2"]
        t = np.arange(1, len(chi2) + 1) * 0.2
        run = np.cumsum(chi2 < 0) / np.arange(1, len(chi2) + 1)
        a.plot(t, 100 * run, color=COL[ff], lw=2, ls=DASH[ff], label=LAB[ff])
    a.axhline(100 * REF["hyp_endo_exp"], color=INK, lw=1, ls=(0, (5, 3)))
    a.set_xlabel("Simulation time (ps)")
    a.set_ylabel("Running Cγ-endo population of Hyp (%)")
    a.set_title("Convergence check: Ace-Hyp-NMe")
    a.text(4, 100 * REF["hyp_endo_exp"] + 1.5, "NMR reference 6% (triple helix)", fontsize=7.5, color=INK)
    a.legend(fontsize=7.5, ncol=2, loc="upper right")
    a.set_ylim(-2, 100)
    save(fig, "fig5_convergence.png")
