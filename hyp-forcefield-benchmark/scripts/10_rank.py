"""Step 9: per-criterion scores and an equal-weight mean rank -> results/ranking.json

Lower is better for every criterion.  The psi-scan error is reported but not ranked on: all five force fields sit
within 0.45 kcal/mol of each other there, which is inside the DFT method noise.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench.ffreg import FORCEFIELDS, ROOT  # noqa: E402

R = os.path.join(ROOT, "results")
q = json.load(open(os.path.join(R, "qm_vs_mm.json")))
m = json.load(open(os.path.join(R, "md_summary.json")))
FFS = list(FORCEFIELDS)
ref = m["reference"]
crit = {}
crit["dft_pucker_scan_rmse_kcal"] = {ff: q["scans"]["pucker"]["rmse"][ff] for ff in FFS}
crit["dft_six_conformer_rmse_kcal"] = {ff: q["conformers"]["rmse_centered"][ff] for ff in FFS}
crit["hyp_endo_abs_err_dipeptide"] = {ff: abs(m["runs"][f"dipeptide_{ff}"]["residues"]["HYP"]["endo"] - ref["hyp_endo_exp"]) for ff in FFS}
crit["hyp_endo_abs_err_helix"] = {ff: abs(m["runs"][f"helix_{ff}"]["residues"]["HYP"]["endo"] - ref["hyp_endo_exp"]) for ff in FFS}
crit["pro_endo_abs_err_helix"] = {ff: abs(m["runs"][f"helix_{ff}"]["residues"]["PRO"]["endo"] - ref["pro_endo_exp"]) for ff in FFS}


def bb_dev(ff):
    d = []
    for rn, (phi, psi) in ref["crystal_phi_psi"].items():
        r = m["runs"][f"helix_{ff}"]["residues"][rn]
        d += [abs((r["phi_mean"] - phi + 180) % 360 - 180), abs((r["psi_mean"] - psi + 180) % 360 - 180)]
    return float(np.mean(d))


crit["backbone_phi_psi_mad_deg_helix"] = {ff: bb_dev(ff) for ff in FFS}
unranked = {"dft_psi_scan_rmse_kcal": {ff: q["scans"]["psi_exo"]["rmse"][ff] for ff in FFS}}


def ranks(vals, tol):
    """Average ranks; values closer than `tol` are treated as tied."""
    order = sorted(FFS, key=lambda f: vals[f])
    groups, cur = [], [order[0]]
    for f in order[1:]:
        if vals[f] - vals[cur[0]] <= tol:
            cur.append(f)
        else:
            groups.append(cur)
            cur = [f]
    groups.append(cur)
    out, pos = {}, 1
    for g in groups:
        r = pos + (len(g) - 1) / 2
        for f in g:
            out[f] = r
        pos += len(g)
    return out


TOL = dict(dft_pucker_scan_rmse_kcal=0.1, dft_six_conformer_rmse_kcal=0.1, hyp_endo_abs_err_dipeptide=0.02,
           hyp_endo_abs_err_helix=0.02, pro_endo_abs_err_helix=0.02, backbone_phi_psi_mad_deg_helix=0.5)
rk = {c: ranks(v, TOL[c]) for c, v in crit.items()}
mean_rank = {ff: float(np.mean([rk[c][ff] for c in crit])) for ff in FFS}
dft_rank = {ff: float(np.mean([rk[c][ff] for c in crit if c.startswith("dft")])) for ff in FFS}
exp_rank = {ff: float(np.mean([rk[c][ff] for c in crit if not c.startswith("dft")])) for ff in FFS}
out = dict(criteria=crit, unranked=unranked, ranks=rk, mean_rank=mean_rank, mean_rank_dft_only=dft_rank,
           mean_rank_experiment_only=exp_rank, order=sorted(FFS, key=lambda f: mean_rank[f]), tie_tolerances=TOL)
json.dump(out, open(os.path.join(R, "ranking.json"), "w"), indent=1)
for c, v in {**crit, **unranked}.items():
    print(f"{c:34s}", "  ".join(f"{ff} {v[ff]:.2f}" for ff in FFS))
print("mean rank (all)       ", {k: round(v, 2) for k, v in mean_rank.items()})
print("mean rank (DFT only)  ", {k: round(v, 2) for k, v in dft_rank.items()})
print("mean rank (experiment)", {k: round(v, 2) for k, v in exp_rank.items()})
print("order:", out["order"])
