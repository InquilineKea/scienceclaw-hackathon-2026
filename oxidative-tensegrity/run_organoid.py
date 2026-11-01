#!/usr/bin/env python3
"""Collagen tensegrity network -> organoid gene expression map.

Question: if you embed an epithelial organoid in collagen gels whose fibre networks differ in connectivity,
crosslink chemistry, crosslink dose and alignment, which gene read-outs change, and can the gel's network
properties be read back from the organoid's expression?  In particular: is the gel's *linear* stiffness enough
to predict expression, or does the network's nonlinearity (strain stiffening, tearing) carry extra information
once the growing organoid pre-strains its own matrix?

Stages
  network   fibre networks (oxt.network, torch; GPU-batched): small-strain moduli, shear curve, failure curve
  cell      motor-clutch (torch) + tabulated 6-strut tensegrity -> YAP, prestress, on a grid of
            organoid-imposed pre-strain x remodelling factor, per gel
  organoid  7-day growth + gene network + LOX/MMP14 remodelling (oxt.organoid), bud tip -> inter-bud positions
  analysis  stiffness-only vs network-descriptor prediction, matched-stiffness pairs, inverse decoding

  python3 run_organoid.py --profile smoke
  python3 run_organoid.py --profile gpu --device cuda      # Brev / Nebius / GCP GPU box
Outputs in results/organoid/<profile>/.  Model outputs, not measurements.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

CHEMS = ["pyridinoline", "glucosepane", "dityrosine", "isopeptide_TG2"]
# in-vitro handles: LOX / lysyl-oxidase-like, ribose glycation, ruthenium/light dityrosine, transglutaminase
GLYCATION = {"glucosepane", "pentosidine"}

PROFILES = {
    "smoke": dict(W=10, seeds=1, batch=64, workers=1, threads=4, z=[3.0, 3.8], chems=["pyridinoline", "glucosepane"],
                  doses=[1.0], modes=["iso"], col4=False, clutch_T=3.0,
                  gammas=[0.02, 0.1, 0.2, 0.35, 0.5], fail=[0.05, 0.15, 0.3, 0.45, 0.6],
                  eps=[0.0, 0.05, 0.15, 0.3, 0.5], scale=[0.4, 1.0, 2.5], noise_reps=3),
    "cpu": dict(W=16, seeds=2, batch=8, workers=8, threads=1, z=[2.8, 3.2, 3.6, 4.0, 4.4], chems=CHEMS,
                doses=[0.5, 1.0], modes=["iso", "aniso"], col4=True, clutch_T=10.0,
                gammas=[0.005, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5],
                fail=list(np.round(np.linspace(0.02, 0.6, 20), 3)),
                eps=[0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5], scale=[0.4, 1.0, 2.5], noise_reps=5),
    "gpu": dict(W=32, seeds=4, batch=1024, workers=1, threads=8, z=[2.8, 3.1, 3.4, 3.7, 4.0, 4.4], chems=CHEMS,
                doses=[0.25, 0.5, 1.0], modes=["iso", "aniso"], col4=True, clutch_T=40.0,
                gammas=[0.005, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5],
                fail=list(np.round(np.linspace(0.03, 0.6, 20), 3)),
                eps=[0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5], scale=[0.4, 0.7, 1.0, 1.6, 2.5],
                noise_reps=8,
                # float64 LBFGS: the bond-rupture test is FP64-bound, so it runs on CPU cores at W=16 while the GPU
                # does shear/moduli at W=32.  Downstream uses only ratios from it (peak strain, post-peak retention).
                fail_W=16, fail_seeds=1, fail_workers=26, fail_batch=6),
}


def gel_items(P):
    gels = []
    for z in P["z"]:
        gels.append(dict(collagen="I", z=z, mode="none", dose=0.0, chem="none"))
        for chem in P["chems"]:
            for d in P["doses"]:
                for m in P["modes"]:
                    gels.append(dict(collagen="I", z=z, mode=m, dose=d, chem=chem))
        if P["col4"]:  # basement-membrane-like reference (Matrigel proxy)
            gels.append(dict(collagen="IV", z=z + 0.4, mode="none", dose=0.0, chem="none"))
    for i, g in enumerate(gels):
        g["gel"] = i
    return gels


def _items(gels, seeds):
    items = []
    for g in gels:
        for s in range(seeds):
            it = dict(g, seed=5000 + 97 * g["gel"] + s)
            if it["chem"] == "none":
                it.pop("chem")
            items.append(it)
    return items


def _tag(df, items):
    # build_spec meta does not carry gel id/chem; re-attach in submission order
    df["gel"] = [it["gel"] for it in items]
    df["chem"] = [it.get("chem", "none") for it in items]
    df["z_target"] = [it["z"] for it in items]
    return df


def stage_network(P, device, part="all"):
    """part: 'shear' (moduli + shear curve), 'fail' (rupture test), or 'all'.  Returns (net, fail, gels)."""
    from run_sweep import run_tasks

    gels = gel_items(P)
    net = fail = None
    if part in ("shear", "all"):
        items = _items(gels, P["seeds"])
        protos = ["moduli", "shear"] + (["failure"] if part == "all" and "fail_W" not in P else [])
        net = _tag(run_tasks(items, protos, P, device, "network"), items)
    if part == "fail" or (part == "all" and "fail_W" in P):
        Pf = dict(P, W=P.get("fail_W", P["W"]), batch=P.get("fail_batch", P["batch"]),
                  workers=P.get("fail_workers", P["workers"]), threads=1)
        items = _items(gels, P.get("fail_seeds", P["seeds"]))
        fail = _tag(run_tasks(items, ["failure"], Pf, "cpu" if "fail_W" in P else device, "failure"), items)
    if net is not None and fail is None and "strain_at_peak" in net:
        fail = net
    return net, fail, pd.DataFrame(gels)


def gel_table(net, fail, gels, P, E_native_pa):
    num = net.groupby("gel").mean(numeric_only=True)
    fnum = fail.groupby("gel").mean(numeric_only=True).loc[num.index]
    native = num[(gels.set_index("gel").loc[num.index, "collagen"] == "I")
                 & (gels.set_index("gel").loc[num.index, "chem"] == "none")]
    # calibrate: native Col I gel nearest z = 3.4 has E_lin = E_native_pa
    ref = native.iloc[np.argmin(np.abs(native["z_target"] - 3.4))]
    S_pa = E_native_pa / (3 * ref["G"])
    gam = P["gammas"]
    strain = np.array([0.0] + list(gam))
    E = np.stack([3 * num["G"].to_numpy()] + [3 * num[f"sig_g{g}"].to_numpy() / g for g in gam], 1)
    E = np.clip(E, 1e-9, None) * S_pa
    fe = np.array(P["fail"])
    # the failure test may run at a smaller W; downstream uses only its peak strain and post-peak retention ratio
    fsig = np.stack([fnum[f"fail_e{e}"].to_numpy() for e in fe], 1) * S_pa
    t = gels.set_index("gel").loc[num.index].reset_index()
    t["E_lin_Pa"] = E[:, 0]
    i20 = int(np.argmin(np.abs(strain - 0.2)))
    t["stiffening_E20_over_E0"] = E[:, i20] / E[:, 0]
    t["strain_at_peak"] = fnum["strain_at_peak"].to_numpy()
    t["strength_Pa"] = fnum["strength"].to_numpy() * S_pa
    t["toughness"] = fnum["toughness"].to_numpy()
    t["z_target"] = t["z"]
    t["z"] = num["z"].to_numpy()
    t["mesh"] = num["mesh"].to_numpy()
    t["anisotropy"] = (num["Cx"] / num["Cy"].clip(lower=1e-12)).to_numpy()
    nat_mesh = ref["mesh"]
    t["mesh_rel"] = t["mesh"] / nat_mesh
    return t, strain, E, fe, fsig, S_pa


def stage_cell(gt, strain, E, fe, fsig, P, device):
    from oxt.cell import ClutchParams, MatrixCurve
    from oxt.organoid import PrestressTable, cell_steady_state, shifted_curves

    t0 = time.time()
    table = PrestressTable()
    print(f"[cell] tensegrity table {time.time() - t0:.0f}s", flush=True)
    eps, sc = np.array(P["eps"]), np.array(P["scale"])
    Ng = len(gt)
    gi, ei, si = np.meshgrid(np.arange(Ng), np.arange(len(eps)), np.arange(len(sc)), indexing="ij")
    gi, ei, si = gi.ravel(), ei.ravel(), si.ravel()
    Ep, fail_left, D = shifted_curves(strain, E[gi], fe, fsig[gi], eps[ei], sc[si])
    curve = MatrixCurve(strain, Ep, fail_left)
    t0 = time.time()
    out = cell_steady_state(curve, table, ClutchParams(T=P["clutch_T"]), device=device)
    print(f"[cell] {len(gi)} cell conditions in {time.time() - t0:.0f}s", flush=True)
    rows = pd.DataFrame(dict(gel=gi, eps=eps[ei], scale=sc[si], damage_retention=D, E_seen_Pa=Ep[:, 0],
                             Y=out["Y"], prestress_ratio=out["prestress_ratio"], M=out["M"],
                             traction_pN=out["mc_F"], torn=out["mc_torn"]))
    shp = (Ng, len(eps), len(sc))
    Ytab = out["Y"].reshape(shp)
    PStab = out["prestress_ratio"].reshape(shp)
    # hoop stress at scale 1 from the secant curve (sigma = E_sec * eps), with tearing retention
    E1 = np.stack([np.interp(eps, strain, E[g]) for g in range(Ng)])
    Dg = D.reshape(shp)[:, :, int(np.argmin(np.abs(sc - 1.0)))]
    sig_hoop = E1 * eps[None, :] * Dg
    return rows, Ytab, PStab, sig_hoop


def stage_organoid(gt, Ytab, PStab, sig_hoop, P, **overrides):
    from oxt.organoid import GENE_NAMES, OrganoidParams, simulate_organoids, wnt_delivery

    age = np.where(gt["chem"].isin(GLYCATION), gt["dose"], 0.0)
    W = wnt_delivery(gt["mesh_rel"].to_numpy(), age)
    from oxt.materials import CROSSLINKS

    op = OrganoidParams(**overrides)
    k_rel = np.array([CROSSLINKS[c]["k_rel"] if c in CROSSLINKS else 0.0 for c in gt["chem"]])
    tau_p = op.tau_plastic_h * (1 + op.xl_plastic_gain * gt["dose"].to_numpy() * k_rel)
    tr = simulate_organoids(Ytab, PStab, P["eps"], P["scale"], sig_hoop, W, tau_p, gt["dose"].to_numpy(), op)
    rows = []
    for d in range(tr["R"].shape[0]):
        for g in range(len(gt)):
            r = dict(gel=g, day=d, R_um=tr["R"][d, g], Wnt=W[g], tau_plastic_h=tau_p[g])
            for k in ["eps", "Y", "PS", "logS", *GENE_NAMES]:
                v = tr[k][d, g]
                r[f"{k}_mean"] = v.mean()
                r[f"{k}_tip"] = v[0]
                r[f"{k}_inter"] = v[-1]
            rows.append(r)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------------------------------
def _ridge_cv(X, y, lam=1e-2, k=5, seed=0, groups=None):
    """Cross-validated R^2; folds split by group (gel) so replicate organoids never straddle train/test."""
    rng = np.random.default_rng(seed)
    n = len(y)
    groups = np.arange(n) if groups is None else np.asarray(groups)
    ug = np.unique(groups)
    fold = (rng.permutation(len(ug)) % k)[np.searchsorted(ug, groups)]
    pred = np.zeros(n)
    for f in range(k):
        tr, te = fold != f, fold == f
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-12
        Xt = (X[tr] - mu) / sd
        A = Xt.T @ Xt + lam * len(Xt) * np.eye(X.shape[1])
        w = np.linalg.solve(A, Xt.T @ (y[tr] - y[tr].mean()))
        pred[te] = ((X[te] - mu) / sd) @ w + y[tr].mean()
    ss = ((y - y.mean()) ** 2).sum()
    return 1 - ((y - pred) ** 2).sum() / max(ss, 1e-18)


def _poly(X):
    cols = [X] + [X[:, [i]] * X[:, [j]] for i in range(X.shape[1]) for j in range(i, X.shape[1])]
    return np.hstack(cols)


def analyse(gt, org, P, out):
    from oxt.organoid import GENE_NAMES

    rng = np.random.default_rng(1)
    readouts = ["R_um"] + [f"{g}_mean" for g in GENE_NAMES] + [f"{g}_tip" for g in GENE_NAMES] \
        + [f"{g}_inter" for g in GENE_NAMES]
    res = {}
    for day in (1, 3, int(org.day.max())):
        d = org[org.day == day].sort_values("gel").reset_index(drop=True)
        g = gt.sort_values("gel").reset_index(drop=True)
        logE = np.log10(g["E_lin_Pa"].to_numpy())[:, None]
        desc = np.column_stack([logE[:, 0], np.log10(g["stiffening_E20_over_E0"].clip(lower=1e-3)),
                                g["strain_at_peak"], np.log10(g["mesh_rel"]), np.log10(g["anisotropy"])])
        Xs = _poly(np.column_stack([logE, logE ** 2, logE ** 3]))[:, :3]
        Xd = _poly(desc)
        r = []
        for ro in readouts:
            y = d[ro].to_numpy()
            if y.std() < 1e-6:
                continue
            r.append(dict(readout=ro, spread=float(y.max() - y.min()), R2_stiffness_only=_ridge_cv(Xs, y),
                          R2_network_descriptors=_ridge_cv(Xd, y)))
        res[f"day{day}_prediction"] = pd.DataFrame(r)

        # matched linear stiffness pairs (within 10 %) that differ in chemistry, z or alignment
        pairs = []
        lE = logE[:, 0]
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if abs(lE[i] - lE[j]) < np.log10(1.1):
                    pairs.append((i, j))
        pr = []
        for ro in [f"{x}_mean" for x in ("CTGF", "ANKRD1", "LY6A", "LGR5", "ACTA2", "MKI67")] + ["R_um"]:
            y = d[ro].to_numpy()
            span = y.max() - y.min() + 1e-12
            dif = np.array([abs(y[i] - y[j]) for i, j in pairs]) / span if pairs else np.array([np.nan])
            pr.append(dict(readout=ro, n_pairs=len(pairs), median_rel_diff=float(np.nanmedian(dif)),
                           p90_rel_diff=float(np.nanpercentile(dif, 90)), max_rel_diff=float(np.nanmax(dif))))
        res[f"day{day}_matched"] = pd.DataFrame(pr)
        if pairs:
            k = int(np.argmax([abs(d["ANKRD1_mean"][i] - d["ANKRD1_mean"][j]) for i, j in pairs]))
            i, j = pairs[k]
            res[f"day{day}_best_pair"] = pd.concat([g.iloc[[i, j]].reset_index(drop=True),
                                                     d.iloc[[i, j]].reset_index(drop=True)
                                                     [["R_um", "CTGF_mean", "ANKRD1_mean", "LY6A_mean",
                                                       "LGR5_mean", "eps_mean", "Y_mean"]]], axis=1)

        # inverse problem: decode gel descriptors from a noisy gene panel (replicate organoids, 15 % CV)
        panel = [f"{x}_mean" for x in GENE_NAMES] + [f"{x}_tip" for x in GENE_NAMES] + ["R_um"]
        Y = d[panel].to_numpy()
        reps = P["noise_reps"]
        Yn = np.concatenate([Y * rng.lognormal(0, 0.15, Y.shape) for _ in range(reps)])
        Yn = np.log(np.clip(Yn, 1e-4, None))
        targets = dict(log10_E_lin=lE, stiffening=desc[:, 1], strain_at_peak=desc[:, 2], log10_mesh=desc[:, 3],
                       dose=g["dose"].to_numpy(), z=g["z"].to_numpy())
        dec = []
        for name, t in targets.items():
            tt = np.tile(t, reps)
            grp = np.tile(np.arange(len(t)), reps)
            full = _ridge_cv(Yn, tt, groups=grp)
            # greedy 4-gene panel
            chosen, best = [], -np.inf
            for _ in range(4):
                cand = [(c, _ridge_cv(Yn[:, chosen + [c]], tt, groups=grp)) for c in range(len(panel)) if c not in chosen]
                c, s = max(cand, key=lambda x: x[1])
                chosen.append(c)
                best = s
            dec.append(dict(target=name, R2_full_panel=full, R2_best4=best,
                            best4=", ".join(panel[c] for c in chosen)))
        res[f"day{day}_decoding"] = pd.DataFrame(dec)
    for k, v in res.items():
        v.to_csv(out / f"analysis_{k}.csv", index=False)
    return res


def write_summary(gt, org, res, P, out, timings):
    last = int(org.day.max())
    lines = [f"# Collagen network -> organoid gene expression ({out.name})", "",
             "Model outputs, not measurements. Gene-network parameters are assumptions (oxt/organoid.py).", "",
             f"Gels: {len(gt)}; network W={P['W']}, seeds={P['seeds']}; timings (s): {json.dumps(timings)}", ""]
    for day in (1, 3, last):
        pr = res[f"day{day}_prediction"]
        key = pr[pr.readout.str.endswith("_mean") | (pr.readout == "R_um")]
        lines += [f"## Day {day}: how much of each read-out does linear stiffness explain?", "",
                  key.round(3).to_markdown(index=False), "",
                  f"## Day {day}: matched linear stiffness (within 10 %), different network", "",
                  res[f"day{day}_matched"].round(3).to_markdown(index=False), ""]
        if f"day{day}_best_pair" in res:
            bp = res[f"day{day}_best_pair"]
            cols = ["collagen", "z", "chem", "mode", "dose", "E_lin_Pa", "stiffening_E20_over_E0",
                    "strain_at_peak", "R_um", "eps_mean", "Y_mean", "CTGF_mean", "ANKRD1_mean", "LY6A_mean",
                    "LGR5_mean"]
            lines += ["Largest ANKRD1 difference at matched stiffness:", "", bp[cols].round(3).to_markdown(index=False),
                      ""]
        lines += [f"## Day {day}: decode gel network from the organoid (15 % noise, {P['noise_reps']} replicates)", "",
                  res[f"day{day}_decoding"].round(3).to_markdown(index=False), ""]
    d = org[org.day == last].merge(gt, on="gel")
    top = d.groupby(["collagen", "chem", "mode"]).agg(
        E_lin_Pa=("E_lin_Pa", "median"), R_um=("R_um", "median"), Y=("Y_mean", "median"),
        CTGF=("CTGF_mean", "median"), ANKRD1=("ANKRD1_mean", "median"), LY6A=("LY6A_mean", "median"),
        LGR5=("LGR5_mean", "median"), KRT20=("KRT20_mean", "median"), ACTA2=("ACTA2_mean", "median"),
        tip_minus_inter_ANKRD1=("ANKRD1_tip", "median")).reset_index()
    top["tip_minus_inter_ANKRD1"] -= d.groupby(["collagen", "chem", "mode"])["ANKRD1_inter"].median().to_numpy()
    lines += [f"## Day {last}: medians by crosslinker and alignment (over z and dose)", "",
              top.round(3).to_markdown(index=False), ""]
    (out / "SUMMARY.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="smoke", choices=PROFILES)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=None)
    ap.add_argument("--reuse-network", action="store_true", help="start from existing network.csv/failure.csv")
    ap.add_argument("--network-part", default="all", choices=["all", "shear", "fail"],
                    help="run only part of the network stage, write its csv and stop (run the parts concurrently)")
    ap.add_argument("--E-native-pa", type=float, default=400.0,
                    help="calibration: linear Young's modulus of the native Col I gel at z=3.4 (~2 mg/mL gel)")
    args = ap.parse_args()
    P = PROFILES[args.profile]
    out = Path(args.out or ROOT / "results" / "organoid" / args.profile)
    out.mkdir(parents=True, exist_ok=True)
    (out / "no_amotl2_feedback").mkdir(exist_ok=True)
    import torch

    torch.set_num_threads(P["threads"])
    timings = {}
    t0 = time.time()
    if args.reuse_network and (out / "network.csv").exists():
        net, gels = pd.read_csv(out / "network.csv"), pd.DataFrame(gel_items(P))
        fail = pd.read_csv(out / "failure.csv") if (out / "failure.csv").exists() else net
    else:
        net, fail, gels = stage_network(P, args.device, args.network_part)
        if net is not None:
            net.to_csv(out / "network.csv", index=False)
        if fail is not None and fail is not net:
            fail.to_csv(out / "failure.csv", index=False)
        if args.network_part != "all":
            print(f"network part {args.network_part} done in {time.time() - t0:.0f}s")
            return
    timings["network"] = round(time.time() - t0)
    gt, strain, E, fe, fsig, S_pa = gel_table(net, fail, gels, P, args.E_native_pa)
    gt.to_csv(out / "gels.csv", index=False)
    t0 = time.time()
    cell, Ytab, PStab, sig_hoop = stage_cell(gt, strain, E, fe, fsig, P, args.device)
    cell.to_csv(out / "cell_table.csv", index=False)
    timings["cell"] = round(time.time() - t0)
    t0 = time.time()
    org = stage_organoid(gt, Ytab, PStab, sig_hoop, P)
    org.to_csv(out / "organoid.csv", index=False)
    # control: same gels without AMOTL2 -> YAP negative feedback (how much does adaptation hide the gel?)
    org_nofb = stage_organoid(gt, Ytab, PStab, sig_hoop, P, k_amotl2=1e9)
    org_nofb.to_csv(out / "organoid_no_amotl2_feedback.csv", index=False)
    timings["organoid"] = round(time.time() - t0)
    res = analyse(gt, org, P, out)
    write_summary(gt, org, res, P, out, timings)
    res_nofb = analyse(gt, org_nofb, P, out / "no_amotl2_feedback")
    write_summary(gt, org_nofb, res_nofb, P, out / "no_amotl2_feedback", timings)
    (out / "params.json").write_text(json.dumps(dict(profile=args.profile, P=P, S_pa=S_pa,
                                                     E_native_pa=args.E_native_pa, device=args.device), indent=1,
                                                default=float))
    print((out / "SUMMARY.md").read_text())


if __name__ == "__main__":
    main()
