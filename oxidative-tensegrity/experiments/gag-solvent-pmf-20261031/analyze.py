#!/usr/bin/env python3
"""WHAM free-energy profiles and standard binding free energies; independent check from unbiased MD.

  python3 analyze.py RESULTS_DIR      -> RESULTS_DIR/summary.json, summary.md, pmf.png

Umbrella route: WHAM on 1D distance histograms, Jacobian-corrected W(r) = F(r) + 2kT ln r, plateau at 1.0-1.2 nm set
to zero, contact cutoff r_c at the first maximum of W after its minimum; K = 4*pi*int_0^rc r^2 exp(-W/kT) dr;
dG0 = -kT ln(K * c0). Error from WHAM on two halves of every window (first/second half of the trajectory).
Unbiased route: bound fraction p = P(r < r_c) pooled over replicas in a box of volume V with one pair:
K = V * p / (1 - p) (pair-in-box mass action), same r_c. Agreement within 0.5 kcal/mol or 2 sigma = validated.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

kT = 2.494339  # kJ/mol at 300 K
KCAL = 4.184
C0 = 0.6022  # 1 M in molecules per nm^3
K_UMB = 1000.0
BINS = np.linspace(0.25, 1.25, 201)


def wham(samples, centres, iters=20000, tol=1e-9):
    mid = 0.5 * (BINS[1:] + BINS[:-1])
    H = np.array([np.histogram(s, BINS)[0] for s in samples], float)
    N = H.sum(1)
    bias = np.array([0.5 * K_UMB * (mid - c) ** 2 / kT for c in centres])  # (windows, bins), in kT
    f = np.zeros(len(centres))
    for _ in range(iters):
        denom = (N[:, None] * np.exp(f[:, None] - bias)).sum(0)
        P = H.sum(0) / np.where(denom > 0, denom, np.inf)
        fn = -np.log((P[None, :] * np.exp(-bias)).sum(1))
        fn -= fn[0]
        if np.max(np.abs(fn - f)) < tol:
            f = fn
            break
        f = fn
    with np.errstate(divide="ignore"):
        F = -np.log(P)
    W = F + 2 * np.log(mid)  # remove the r^2 Jacobian, in kT
    plateau = (mid >= 1.0) & (mid <= 1.2) & np.isfinite(W)
    W -= W[plateau].mean()
    return mid, W


def contact_cutoff(mid, W):
    ok = np.isfinite(W)
    i0 = int(np.nanargmin(np.where(ok & (mid < 0.7), W, np.nan)))
    j = i0 + int(np.nanargmax(np.where(ok[i0:] & (mid[i0:] < 0.8), W[i0:], np.nan)))
    return float(mid[j])


def binding(mid, W, rc):
    sel = (mid <= rc) & np.isfinite(W)
    dr = mid[1] - mid[0]
    K = float(4 * np.pi * np.sum(mid[sel] ** 2 * np.exp(-W[sel])) * dr)  # nm^3
    return K, -kT * np.log(K * C0) / KCAL  # kcal/mol


def load(d):
    um, ub = {}, {}
    for p in sorted(Path(d).glob("*.json")):
        rec = json.loads(p.read_text())
        if not rec.get("finite"):
            continue
        r = np.load(p.with_suffix(".npy"))
        if rec["kind"] == "umbrella":
            um.setdefault(rec["cation"], []).append((rec["r0"], r))
        else:
            ub.setdefault(rec["cation"], []).append((rec["box_volume_nm3"], r))
    return um, ub


def main(d):
    um, ub = load(d)
    out, curves = {}, {}
    for cat, wins in sorted(um.items()):
        wins.sort()
        centres = [c for c, _ in wins]
        mid, W = wham([r for _, r in wins], centres)
        rc = contact_cutoff(mid, W)
        K, dG = binding(mid, W, rc)
        halves = []
        for h in (0, 1):
            m2, W2 = wham([np.array_split(r, 2)[h] for _, r in wins], centres)
            halves.append(binding(m2, W2, rc)[1])
        out[cat] = dict(windows=len(wins), r_contact_nm=rc, W_min_kT=float(np.nanmin(W[mid < rc])),
                        K_nm3=K, dG0_kcal=dG, dG0_halves=halves, dG0_err=float(abs(halves[0] - halves[1]) / 2))
        curves[cat] = (mid, W)
        if cat in ub:
            rcs = [r for _, r in ub[cat]]
            V = float(np.mean([v for v, _ in ub[cat]]))
            allr = np.concatenate(rcs)
            p = float(np.mean(allr < rc))
            per = [float(np.mean(r < rc)) for r in rcs]
            Kb = V * p / max(1 - p, 1e-12)
            dGb = -kT * np.log(max(Kb, 1e-12) * C0) / KCAL
            se_p = float(np.std(per, ddof=1) / np.sqrt(len(per))) if len(per) > 1 else float("nan")
            se_dG = kT / KCAL * se_p / max(p * (1 - p), 1e-12)
            agree = abs(dGb - dG) <= max(0.5, 2 * np.hypot(se_dG, out[cat]["dG0_err"]))
            out[cat]["unbiased"] = dict(replicas=len(rcs), ns_total=len(allr) * 0.5e-3, box_nm3=V, p_bound=p,
                                        K_nm3=Kb, dG0_kcal=float(dGb), dG0_se=float(se_dG), agrees_with_umbrella=bool(agree))
    if "MGUA" in out and "MAMM" in out:
        out["ddG_Arg_minus_Lys_kcal"] = out["MGUA"]["dG0_kcal"] - out["MAMM"]["dG0_kcal"]
    if "DMAM" in out and "MAMM" in out:
        out["ddG_neutral_minus_Lys_kcal"] = out["DMAM"]["dG0_kcal"] - out["MAMM"]["dG0_kcal"]
    Path(d, "summary.json").write_text(json.dumps(out, indent=1))
    lines = ["| analog | windows | contact r_c (nm) | well depth (kT) | ΔG° umbrella (kcal/mol) | ΔG° unbiased | agree |",
             "|---|---|---|---|---|---|---|"]
    for cat in ("MGUA", "MAMM", "DMAM"):
        if cat in out:
            o, u = out[cat], out[cat].get("unbiased", {})
            lines.append(f"| {cat} | {o['windows']} | {o['r_contact_nm']:.2f} | {o['W_min_kT']:.2f} | {o['dG0_kcal']:.2f} ± {o['dG0_err']:.2f} | "
                         + (f"{u['dG0_kcal']:.2f} ± {u['dG0_se']:.2f} ({u['ns_total']:.0f} ns) | {'yes' if u['agrees_with_umbrella'] else 'NO'} |" if u else "— | — |"))
    Path(d, "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print({k: v for k, v in out.items() if k.startswith("ddG")})
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.4, 4), constrained_layout=True)
        col = {"MGUA": "#2a6fdb", "MAMM": "#16a3a3", "DMAM": "#c8402e"}
        lab = {"MGUA": "methylguanidinium (Arg)", "MAMM": "methylammonium (Lys)", "DMAM": "dimethylamine (charge lost)"}
        for cat, (m, W) in curves.items():
            ax.plot(m, W, color=col[cat], lw=2, label=lab[cat])
        ax.axhline(0, color="0.6", lw=1)
        ax.set_xlabel("cation centre – sulfate S distance (nm)")
        ax.set_ylabel("W(r) (kT)")
        ax.set_title("Binding to methyl sulfate in TIP3P water, 0.15 M NaCl", loc="left", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        fig.savefig(Path(d, "pmf.png"), dpi=150)
    except ImportError:
        pass


if __name__ == "__main__":
    main(sys.argv[1])
