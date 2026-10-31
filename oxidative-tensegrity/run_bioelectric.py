#!/usr/bin/env python3
"""Collagen stiffness distributions -> coupled membrane-potential sheets, young vs aged matrix.

Tests whether the local-stiffness distribution of oxidatively/AGE-crosslinked collagen networks, read by the
motor-clutch + tensegrity cell, pushes a gap-junction-coupled Vmem sheet toward the ageing signature reported for
senescing keratinocytes (Sediqi & Levin, iScience 2025): depolarisation, lower within-culture Vmem heterogeneity,
higher between-culture heterogeneity, lower spatial clustering (global Moran's I).  See oxt/bioelectric.py.

Stages: network (local shear maps) -> cell (per-patch mechanics) -> vmem (protocols x parameter sweep x field
controls) -> analysis.  Field controls: actual map, shuffled map (same cells, positions permuted), uniform map
(every cell gets the network-mean curve).

  python3 run_bioelectric.py --profile smoke
  python3 run_bioelectric.py --profile gpu --device cuda
Outputs in results/bioelectric/<profile>/.  Model outputs, not measurements.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent

PROFILES = {
    "tiny": dict(W=8, P=2, seeds=2, batch=8, z=[3.6], doses=[1.0], modes=["iso"], ages=[20, 80],
                 gammas=[0.002, 0.05], clutch_T=1.0, T=20.0,
                 sweep=dict(G0=[1.0], F50=[400.0], gj_mode=["prestress"])),
    "smoke": dict(W=16, P=4, seeds=2, batch=8, z=[3.2], doses=[1.0], modes=["iso"], ages=[20, 80],
                  gammas=[0.002, 0.05, 0.15], clutch_T=2.0, T=60.0,
                  sweep=dict(G0=[1.0], F50=[400.0], gj_mode=["prestress"])),
    "local": dict(W=32, P=8, seeds=2, batch=8, z=[2.8, 3.6], doses=[0.5, 1.0], modes=["iso"], ages=[20, 80],
                  gammas=[0.002, 0.05, 0.1, 0.2], clutch_T=4.0, T=120.0,
                  sweep=dict(G0=[0.25, 1.0], F50=[400.0], gj_mode=["const", "prestress"])),
    "gpu": dict(W=64, P=16, seeds=8, batch=32, z=[2.8, 3.2, 3.6, 4.0, 4.4], doses=[0.25, 0.5, 1.0],
                modes=["iso", "aniso"], ages=[20, 40, 60, 80], gammas=[0.002, 0.05, 0.1, 0.2, 0.3],
                clutch_T=10.0, T=200.0,
                sweep=dict(G0=[0.25, 1.0, 4.0], F50=[300.0, 400.0, 500.0], gj_mode=["const", "prestress"])),
    # rerun after the first critique: unique seeds, 32 per condition, iso only, stress-uncoupling junctions,
    # noisy information run (AIS / TE / stiffness-Vmem MI), two flip fractions, bootstrap intervals
    "gpu2": dict(W=64, P=16, seeds=32, batch=64, z=[2.8, 3.2, 3.6, 4.0, 4.4], doses=[0.25, 0.5, 1.0],
                 modes=["iso"], ages=[20, 40, 60, 80], gammas=[0.002, 0.05, 0.1, 0.2, 0.3],
                 clutch_T=10.0, T=200.0, unique_seeds=True,
                 sweep=dict(G0=[0.25, 1.0, 4.0], F50=[300.0, 400.0, 500.0],
                            gj_mode=["const", "prestress", "stress_uncouple"])),
    "smoke2": dict(W=16, P=4, seeds=3, batch=8, z=[3.2], doses=[1.0], modes=["iso"], ages=[20, 80],
                   gammas=[0.002, 0.05, 0.15], clutch_T=2.0, T=60.0, unique_seeds=True,
                   sweep=dict(G0=[1.0], F50=[400.0], gj_mode=["prestress", "stress_uncouple"])),
}


def items_for(P):
    """One item per network.  With unique_seeds every network gets its own seed (independent realisations across
    conditions); otherwise seeds repeat across conditions (paired realisations, as in the first gpu run)."""
    items = []
    for z in P["z"]:
        cfgs = [("none", 0.0)] + [(m, d) for m in P["modes"] for d in P["doses"]]
        for mode, d in cfgs:
            for s in range(P["seeds"]):
                items.append(dict(kind="colI", collagen="I", z=z, mode=mode, dose=d, seed=7000 + s))
    for age in P["ages"]:
        for s in range(P["seeds"]):
            items.append(dict(kind="skin", tissue="skin_dermis", age=age, seed=8000 + s))
    if P.get("unique_seeds"):
        for k, it in enumerate(items):
            it["seed"] = 100000 + k
    return items


def stage_network(P, device):
    import torch

    from oxt.bioelectric import local_shear_maps
    from oxt.materials import COLLAGENS, TISSUES, Damage, build_spec, load_crosslink_overrides, tissue_spec
    from oxt.network import Batch, Lattice, coordination

    load_crosslink_overrides()
    lat = Lattice(P["W"])
    items = items_for(P)
    rows, maps, glob = [], [], []
    for k in range(0, len(items), P["batch"]):
        t0 = time.time()
        chunk = items[k:k + P["batch"]]
        specs = []
        for it in chunk:
            rng = np.random.default_rng(it["seed"])
            if it["kind"] == "skin":
                s = tissue_spec(lat, TISSUES[it["tissue"]], it["age"], rng)
            else:
                s = build_spec(lat, COLLAGENS["I"], Damage(it["mode"], it["dose"]), rng, z=it["z"])
            specs.append(s)
        b = Batch(lat, specs, device=device)
        m, g = local_shear_maps(b, P["P"], P["gammas"])
        maps.append(m)
        glob.append(g)
        for it, s in zip(chunk, specs):
            rows.append(dict(it, z_real=coordination(s, lat), dose_real=s.meta.get("dose", it.get("dose", 0.0))))
        print(f"[network] {k + len(chunk)}/{len(items)} ({time.time() - t0:.0f}s)", flush=True)
        del b
        if device != "cpu":
            torch.cuda.empty_cache()
    return rows, np.concatenate(maps), np.concatenate(glob)


def load_table(path):
    """PrestressTable from a saved npz (lets the GPU box skip the scipy tensegrity solves)."""
    from oxt.organoid import PrestressTable

    d = np.load(path)
    t = PrestressTable.__new__(PrestressTable)
    t.c, t.lk, t.tab, t.rigid = d["c"], d["lk"], d["tab"], d["rigid"]
    return t


def stage_cell(G_loc, S_pa, P, device, table_path=None):
    """G_loc (Nnet, n_gamma, P*P) lattice units -> per-cell F, PS, Y for the actual and uniform fields."""
    from oxt.cell import ClutchParams, MatrixCurve
    from oxt.organoid import PrestressTable, cell_steady_state

    strain = np.array(P["gammas"])
    n, ng, nc = G_loc.shape
    E = np.clip(3 * G_loc * S_pa, 1e-3, None)               # energy-equivalent secant Young's modulus, Pa
    E_cells = E.transpose(0, 2, 1).reshape(n * nc, ng)
    E_unif = 3 * np.clip(G_loc.mean(2), 1e-12, None) * S_pa   # (n, ng): network-mean curve
    t0 = time.time()
    table = load_table(table_path) if table_path else PrestressTable()
    print(f"[cell] tensegrity table {time.time() - t0:.0f}s", flush=True)
    E_all = np.concatenate([E_cells, E_unif])
    curve = MatrixCurve(strain, E_all, np.full(len(E_all), 1.0))
    t0 = time.time()
    out = cell_steady_state(curve, table, ClutchParams(T=P["clutch_T"]), device=device)
    print(f"[cell] {len(E_all)} cells in {time.time() - t0:.0f}s", flush=True)
    res = {}
    for key, src in (("F", "mc_F"), ("PS", "prestress_ratio"), ("Y", "Y")):
        v = out[src]
        res[key] = v[:n * nc].reshape(n, nc)
        res[key + "_unif"] = np.repeat(v[n * nc:][:, None], nc, 1)
    res["E0"] = E[:, 0, :]
    return res


def stage_vmem(cell, P, device, seed=0):
    from oxt.bioelectric import VmemParams, run_protocols

    n, nc = cell["F"].shape
    Pg = P["P"]
    rng = np.random.default_rng(seed)
    perm = np.stack([rng.permutation(nc) for _ in range(n)])
    logE = np.log10(np.maximum(cell["E0"], 1e-3))
    fields = {
        "actual": (cell["F"], cell["PS"], logE),
        "shuffled": (np.take_along_axis(cell["F"], perm, 1), np.take_along_axis(cell["PS"], perm, 1),
                     np.take_along_axis(logE, perm, 1)),
        "uniform": (cell["F_unif"], cell["PS_unif"], None),
    }
    sw = P["sweep"]
    rows, rest_maps = [], {}
    for G0, F50, gj in itertools.product(sw["G0"], sw["F50"], sw["gj_mode"]):
        vp = replace(VmemParams(), G0=G0, F50=F50, gj_mode=gj, T=P["T"])
        for fname, (F, PS, lE) in fields.items():
            t0 = time.time()
            out, Vr = run_protocols(F.reshape(n, Pg, Pg), PS.reshape(n, Pg, Pg), vp,
                                    np.random.default_rng(seed + 1), device=device, logE=lE, seed=seed + 2)
            for i in range(n):
                rows.append(dict(net=i, G0=G0, F50=F50, gj_mode=gj, field=fname,
                                 **{k: float(v[i]) for k, v in out.items()}))
            if (G0, F50, gj) == (1.0, 400.0, "prestress"):
                rest_maps[fname] = Vr
            print(f"[vmem] G0={G0} F50={F50} gj={gj} {fname}: {time.time() - t0:.1f}s", flush=True)
    return rows, rest_maps


def stiffness_metrics(G_loc, E0, P):
    import pandas as pd

    from oxt.bioelectric import morans_I

    Pg = P["P"]
    stiff = G_loc[:, -1, :] / np.maximum(G_loc[:, 0, :], 1e-12)
    return pd.DataFrame(dict(
        net=np.arange(len(E0)), E_mean_Pa=E0.mean(1), E_median_Pa=np.median(E0, 1),
        E_cv=E0.std(1) / np.maximum(E0.mean(1), 1e-12),
        E_logsd=np.log10(np.maximum(E0, 1e-3)).std(1),
        moran_E=morans_I(np.log10(np.maximum(E0, 1e-3)).reshape(-1, Pg, Pg)),
        stiffening_median=np.median(stiff, 1)))


OPTIONAL = ["net_heal_10", "net_heal_25", "AIS", "TE", "r_EV", "MI_EV", "V_noise_sd"]


def analyse(net, stiff, vm, cell, P, out, n_boot=2000):
    """Condition tables, the keratinocyte comparison (skin dermis youngest -> oldest, Col I dose 0 -> 1), and
    bootstrap intervals over networks for each contrast."""
    import pandas as pd

    net, vm = pd.DataFrame(net), pd.DataFrame(vm)
    base = net.reset_index().rename(columns={"index": "net"})
    base = base.merge(stiff, on="net")
    base["Y_sd"] = cell["Y"].std(1)
    base["F_mean"] = cell["F"].mean(1)
    df = vm.merge(base, on="net")
    if "q_restore" in df and "net_heal_25" not in df:  # first gpu run: one flip fraction of 0.25
        df["net_heal_25"] = df["q_restore"] - df["q_flipped"]
    opt = [m for m in OPTIONAL if m in df]
    df.to_csv(out / "sheets.csv", index=False)
    key = ["kind", "z", "mode", "dose", "age"]
    for c in key:
        df[c] = df[c].fillna(-1 if c != "mode" else "-")
    params = ["G0", "F50", "gj_mode", "field"]
    agg = df.groupby(key + params, dropna=False).agg(
        n=("net", "size"), E_mean_Pa=("E_mean_Pa", "mean"), E_cv=("E_cv", "mean"), moran_E=("moran_E", "mean"),
        stiffening=("stiffening_median", "mean"), V_mean=("V_mean", "mean"),
        V_sd_within=("V_sd", "mean"), V_sd_between=("V_mean", "std"), frac_depol=("frac_depol", "mean"),
        moran_V=("moran_V", "mean"), q_hold=("q_hold", "mean"), **{m: (m, "mean") for m in opt}).reset_index()
    agg.to_csv(out / "conditions.csv", index=False)

    comp, boot = [], []
    rng = np.random.default_rng(0)
    for name, young, old in _contrast_groups(df):
        for (G0, F50, gj, field), gy in young.groupby(params):
            go = old[(old.G0 == G0) & (old.F50 == F50) & (old.gj_mode == gj) & (old.field == field)]
            row = dict(contrast=name, G0=G0, F50=F50, gj_mode=gj, field=field, **_contrast(gy, go, opt))
            comp.append(row)
            if field in ("actual", "shuffled"):
                boot.append(dict(contrast=name, G0=G0, F50=F50, gj_mode=gj, field=field,
                                 **_bootstrap(gy, go, opt, rng, n_boot)))
    comp, boot = pd.DataFrame(comp), pd.DataFrame(boot)
    comp.to_csv(out / "ageing_contrasts.csv", index=False)
    boot.to_csv(out / "bootstrap_contrasts.csv", index=False)
    return agg, comp, boot


def _contrast_groups(df):
    skin = df[df.kind == "skin"]
    if len(skin):
        ages = sorted(skin.age.unique())
        yield f"skin {ages[0]:g}->{ages[-1]:g} y", skin[skin.age == ages[0]], skin[skin.age == ages[-1]]
    col = df[(df.kind == "colI") & (df["mode"].isin(["none", "iso"]))]
    for z in sorted(col.z.unique()):
        c = col[col.z == z]
        d = sorted(c.dose.unique())
        yield f"Col I z={z:g} dose {d[0]:g}->{d[-1]:g} iso", c[c.dose == d[0]], c[c.dose == d[-1]]


def _stats(g, opt):
    """Per-group summary over networks (sheet level rows of one condition and parameter set)."""
    d = dict(E=g.E_mean_Pa.mean(), V=g.V_mean.mean(), sdw=g.V_sd.mean(), sdb=g.V_mean.std(),
             mor=g.moran_V.mean(), morE=g.moran_E.mean(), dep=g.frac_depol.mean(), qh=g.q_hold.mean())
    d.update({m: g[m].mean() for m in opt})
    return d


def _contrast(gy, go, opt):
    y, o = _stats(gy, opt), _stats(go, opt)
    r = lambda a, b: float(b / a) if abs(a) > 1e-12 else float("nan")
    out = dict(n_young=len(gy), n_old=len(go), E_ratio=r(y["E"], o["E"]),
               moranE_young=y["morE"], moranE_old=o["morE"], dV_mean_mV=o["V"] - y["V"],
               sd_within_ratio=r(y["sdw"], o["sdw"]), sd_between_ratio=r(y["sdb"], o["sdb"]),
               moranV_young=y["mor"], moranV_old=o["mor"], depol_young=y["dep"], depol_old=o["dep"],
               q_hold_young=y["qh"], q_hold_old=o["qh"])
    for m in opt:
        out[f"{m}_young"], out[f"{m}_old"] = y[m], o[m]
    return out


def _bootstrap(gy, go, opt, rng, B):
    """Resample networks with replacement within young and old groups (independent seeds in gpu2).
    Returns 95% percentile intervals for the keratinocyte-signature statistics and their deltas."""
    cols = ["V_mean", "V_sd", "moran_V"] + opt
    Y, O = gy[cols].to_numpy(float), go[cols].to_numpy(float)
    iy = rng.integers(0, len(Y), (B, len(Y)))
    io = rng.integers(0, len(O), (B, len(O)))
    by, bo = Y[iy], O[io]                                   # (B, n, k)
    k = {c: n for n, c in enumerate(cols)}
    with np.errstate(divide="ignore", invalid="ignore"):
        st = dict(
            dV=np.nanmean(bo[..., k["V_mean"]], 1) - np.nanmean(by[..., k["V_mean"]], 1),
            sdw_ratio=np.nanmean(bo[..., k["V_sd"]], 1) / np.nanmean(by[..., k["V_sd"]], 1),
            sdb_ratio=np.nanstd(bo[..., k["V_mean"]], 1, ddof=1) / np.nanstd(by[..., k["V_mean"]], 1, ddof=1),
            dmoran=np.nanmean(bo[..., k["moran_V"]], 1) - np.nanmean(by[..., k["moran_V"]], 1))
        for m in opt:
            st[f"d{m}"] = np.nanmean(bo[..., k[m]], 1) - np.nanmean(by[..., k[m]], 1)
    out = {}
    for name, v in st.items():
        v = v[np.isfinite(v)]
        lo, hi = (np.percentile(v, [2.5, 97.5]) if len(v) else (np.nan, np.nan))
        out[f"{name}_lo"], out[f"{name}_hi"] = float(lo), float(hi)
    # keratinocyte direction, all four intervals excluding the null: depolarised, within-SD down, between-SD up,
    # Moran's I down
    out["kerat_all4"] = bool(out["dV_lo"] > 0 and out["sdw_ratio_hi"] < 1 and out["sdb_ratio_lo"] > 1
                             and out["dmoran_hi"] < 0)
    out["moran_up_sig"] = bool(out["dmoran_lo"] > 0)
    out["moran_down_sig"] = bool(out["dmoran_hi"] < 0)
    return out


def md_table(df):
    fmt = lambda v: f"{v:.3g}" if isinstance(v, (float, np.floating)) else str(v)
    rows = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    rows += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return rows


def write_summary(comp, boot, P, out, S_pa, timings):
    target = ("Keratinocyte senescence (Sediqi & Levin 2025, day 10 -> 40/50 in culture, no ECM): depolarised; "
              "within-dish variability -38% (ratio ~0.62); between-dish SD x15-22; Moran's I 0.5 -> 0.13-0.26.")
    lines = [f"# Bioelectric ageing test ({P['W']}x{P['W']} networks, {P['P']}x{P['P']} cells, {P['seeds']} seeds"
             f"{', unique per condition' if P.get('unique_seeds') else ', paired across conditions'})", "",
             target, "", f"S_pa = {S_pa:.1f} Pa per lattice unit (young skin dermis E = 2 kPa). Timings (s): "
             f"{json.dumps(timings)}", ""]
    heal = "net_heal_25_young" if "net_heal_25_young" in comp else None
    extra = [c for c in ("AIS_young", "AIS_old", "TE_young", "TE_old", "MI_EV_young", "MI_EV_old") if c in comp]
    cols = ["contrast", "field", "E_ratio", "dV_mean_mV", "sd_within_ratio", "sd_between_ratio", "moranV_young",
            "moranV_old", "q_hold_young", "q_hold_old"] + ([heal, "net_heal_25_old"] if heal else []) + extra
    for gj in sorted(comp.gj_mode.unique()):
        d = comp[(comp.G0 == 1.0) & (comp.F50 == 400.0) & (comp.gj_mode == gj)]
        if len(d):
            lines += [f"G0=1, F50=400 pN, junctions = {gj}, all three field controls:", ""] + md_table(d[cols]) + [""]
    lines += ["Sign agreement with the keratinocyte signature across the parameter sweep (actual field), by junction mode:", ""]
    a = comp[comp.field == "actual"]
    for (c, gj), g in a.groupby(["contrast", "gj_mode"]):
        lines.append(f"- {c}, {gj}: depolarised {np.mean(g.dV_mean_mV > 0):.0%}, within-SD down "
                     f"{np.mean(g.sd_within_ratio < 1):.0%}, between-SD up {np.mean(g.sd_between_ratio > 1):.0%}, "
                     f"Moran's I down {np.mean(g.moranV_old < g.moranV_young):.0%} of {len(g)} parameter sets")
    ok = a.assign(ok=(a.dV_mean_mV > 0) & (a.sd_within_ratio < 1) & (a.sd_between_ratio > 1) & (a.moranV_old < a.moranV_young))
    lines += ["", f"All four keratinocyte signs at once (point estimates): {int(ok.ok.sum())} of {len(ok)} "
              "contrast x parameter sets (actual field)."]
    if len(boot):
        b = boot[boot.field == "actual"]
        lines += [f"All four with 95% bootstrap intervals excluding the null: {int(b.kerat_all4.sum())} of {len(b)}.",
                  f"Moran's I of Vmem significantly up with ageing: {int(b.moran_up_sig.sum())}; significantly down: "
                  f"{int(b.moran_down_sig.sum())} (of {len(b)}).", ""]
        for gj, g in b.groupby("gj_mode"):
            lines.append(f"- {gj}: Moran up {int(g.moran_up_sig.sum())}, down {int(g.moran_down_sig.sum())}, "
                         f"all four {int(g.kerat_all4.sum())} of {len(g)}")
    lines += ["", "net_heal_f = q_restore_f - q_flipped_f: restoration beyond the flipped-but-unhealed baseline (0 = none).",
              "AIS / TE: Gaussian active information storage and neighbour transfer entropy (nats) from a noisy "
              "stationary run; MI_EV: Gaussian mutual information between local log stiffness and time-mean Vmem."]
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def make_figure(net, cell, rest_maps, P, out):
    import pandas as pd

    net = pd.DataFrame(net)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    Pg = P["P"]
    skin = net[net.kind == "skin"]
    if skin.empty or "actual" not in rest_maps:
        return
    ages = sorted(skin.age.unique())
    pick = [int(skin[skin.age == a].index[0]) for a in (ages[0], ages[-1])]
    fig, ax = plt.subplots(2, 3, figsize=(11, 7))
    for r, i in enumerate(pick):
        im = ax[r, 0].imshow(np.log10(cell["E0"][i].reshape(Pg, Pg)), cmap="viridis")
        ax[r, 0].set_title(f"skin {int(net.age[i])} y: log10 local E (Pa)")
        plt.colorbar(im, ax=ax[r, 0])
        im = ax[r, 1].imshow(rest_maps["actual"][i], cmap="coolwarm", vmin=-75, vmax=0)
        ax[r, 1].set_title("Vmem at rest (mV), actual field")
        plt.colorbar(im, ax=ax[r, 1])
        im = ax[r, 2].imshow(rest_maps["shuffled"][i], cmap="coolwarm", vmin=-75, vmax=0)
        ax[r, 2].set_title("Vmem, shuffled field")
        plt.colorbar(im, ax=ax[r, 2])
    for a in ax.flat:
        a.set_xticks([]), a.set_yticks([])
    fig.tight_layout()
    fig.savefig(out / "bioelectric_maps.png", dpi=130)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="smoke", choices=PROFILES)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=None)
    ap.add_argument("--E-dermis-young-pa", type=float, default=2000.0)
    ap.add_argument("--table", default=None, help="precomputed tensegrity table npz (see --save-table)")
    ap.add_argument("--save-table", default=None, help="compute the tensegrity table, save it here, exit")
    ap.add_argument("--raw-only", action="store_true", help="simulate and save raw arrays; no pandas analysis")
    ap.add_argument("--analyse-only", action="store_true", help="analyse raw arrays already in --out")
    args = ap.parse_args()
    if args.save_table:
        from oxt.organoid import PrestressTable

        t = PrestressTable()
        np.savez(args.save_table, c=t.c, lk=t.lk, tab=t.tab, rigid=t.rigid)
        return
    P = PROFILES[args.profile]
    out = Path(args.out or ROOT / "results" / "bioelectric" / args.profile)
    out.mkdir(parents=True, exist_ok=True)

    if not args.analyse_only:
        timings = {}
        t0 = time.time()
        net, G_loc, G_glob = stage_network(P, args.device)
        timings["network"] = round(time.time() - t0)
        np.savez_compressed(out / "local_maps.npz", G_loc=G_loc, G_glob=G_glob, gammas=np.array(P["gammas"]))
        young = [i for i, r in enumerate(net) if r["kind"] == "skin" and r["age"] == min(P["ages"])]
        S_pa = args.E_dermis_young_pa / (3 * G_glob[young, 0].mean())
        t0 = time.time()
        cell = stage_cell(G_loc, S_pa, P, args.device, args.table)
        timings["cell"] = round(time.time() - t0)
        np.savez_compressed(out / "cells.npz", **cell)
        t0 = time.time()
        vm, rest_maps = stage_vmem(cell, P, args.device)
        timings["vmem"] = round(time.time() - t0)
        np.savez_compressed(out / "vmem_rest_maps.npz", **rest_maps)
        (out / "raw.json").write_text(json.dumps(dict(profile=args.profile, P=P, S_pa=float(S_pa), device=args.device,
                                                      timings=timings, networks=net, vmem=vm), default=float))
        if args.raw_only:
            print(f"raw outputs in {out}; timings {timings}")
            return

    raw = json.loads((out / "raw.json").read_text())
    loc = np.load(out / "local_maps.npz")
    cell = dict(np.load(out / "cells.npz"))
    rest_maps = dict(np.load(out / "vmem_rest_maps.npz"))
    stiff = stiffness_metrics(loc["G_loc"], cell["E0"], P)
    agg, comp, boot = analyse(raw["networks"], stiff, raw["vmem"], cell, P, out)
    write_summary(comp, boot, P, out, raw["S_pa"], raw["timings"])
    make_figure(raw["networks"], cell, rest_maps, P, out)
    print((out / "SUMMARY.md").read_text())


if __name__ == "__main__":
    main()
