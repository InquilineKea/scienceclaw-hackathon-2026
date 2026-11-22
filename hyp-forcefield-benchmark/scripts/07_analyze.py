"""Step 6: statistics for everything that exists on disk -> results/*.json (figures: 08_figures.py)."""
import json
import os
import sys

import numpy as np
import openmm.app as app

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import analysis as an  # noqa: E402
from hypbench import build, ffreg, geom, md  # noqa: E402

R = os.path.join(ffreg.ROOT, "results")
FFS = list(ffreg.FORCEFIELDS)
H = 627.509474
SVP = "B3LYP-D3BJ/def2-SVP"

# ============================================================== QM vs MM
G = json.load(open(os.path.join(R, "qm_geometries.json")))["points"]
MM = json.load(open(os.path.join(R, "mm_energies.json")))
DFT = {}
for line in open(os.path.join(R, "dft_energies.jsonl")):
    r = json.loads(line)
    DFT[(r["index"], r["method"])] = r["e_tot"]
planned = json.load(open(os.path.join(R, "dft_planned_jobs.json")))
done = [j for j in planned if (j["index"], j["method"]) in DFT]
todo = [j for j in planned if (j["index"], j["method"]) not in DFT]
idx = {(p["scan"], p["label"]): i for i, p in enumerate(G)}
i_exo, i_endo, i_ts = idx[("minimum", "exo")], idx[("minimum", "endo")], idx[("pucker", "+0.0")]
qm = dict(n_planned=len(planned), n_done=len(done), not_done=todo, scans={}, sensitivity={})


def rel(method, i, ref=i_exo):
    return (DFT[(i, method)] - DFT[(ref, method)]) * H if (i, method) in DFT and (ref, method) in DFT else None


for scan in ("pucker", "psi_exo", "psi_endo", "phi_exo", "phi_endo"):
    pts = [i for i, p in enumerate(G) if p["scan"] == scan and (i, SVP) in DFT]
    if scan != "pucker" and i_exo in [i for i in range(len(G))]:
        pass
    if len(pts) < 3:
        continue
    xkey = {"pucker": "chi2", "psi_exo": "psi", "psi_endo": "psi", "phi_exo": "phi", "phi_endo": "phi"}[scan]
    x = [G[i]["constraints"][xkey] for i in pts]
    order = np.argsort(x)
    pts = [pts[o] for o in order]
    e_q = np.array([rel(SVP, i) for i in pts])
    rec = dict(x=[G[i]["constraints"][xkey] for i in pts], xkey=xkey, dft=e_q.tolist(),
               xtb=[(G[i]["e_xtb"] - G[i_exo]["e_xtb"]) * H for i in pts], mm={}, rmse={}, rmse_centered={}, max_abs={})
    for ff in FFS:
        e_m = np.array([MM[ff][i]["e_mm"] - MM[ff][i_exo]["e_mm"] for i in pts])
        rec["mm"][ff] = e_m.tolist()
        d = e_m - e_q
        rec["rmse"][ff] = float(np.sqrt((d ** 2).mean()))          # zero fixed at the exo minimum
        rec["rmse_centered"][ff] = float(np.sqrt(((d - d.mean()) ** 2).mean()))  # shape only
        rec["max_abs"][ff] = float(np.abs(d).max())
    qm["scans"][scan] = rec

# six conformers: 2 puckers x 3 hydroxyl rotamers
conf = [("exo", "180", i_exo), ("endo", "180", i_endo)] + [
    (pk, lab, idx[(f"ohrot_{pk}", lab)]) for pk in ("exo", "endo") for lab in ("+60", "-60")]
have = [c for c in conf if (c[2], SVP) in DFT]
if len(have) == 6:
    e_q = np.array([rel(SVP, c[2]) for c in have])
    rec = dict(labels=[f"{c[0]} / OH {c[1]}" for c in have], dft=e_q.tolist(),
               xtb=[(G[c[2]]["e_xtb"] - G[i_exo]["e_xtb"]) * H for c in have], mm={}, rmse_centered={}, mm_chi2={},
               best_endo_minus_best_exo={})
    ex = [k for k, c in enumerate(have) if c[0] == "exo"]
    en = [k for k, c in enumerate(have) if c[0] == "endo"]
    rec["best_endo_minus_best_exo"]["DFT"] = float(e_q[en].min() - e_q[ex].min())
    for ff in FFS:
        e_m = np.array([MM[ff][c[2]]["e_mm"] - MM[ff][i_exo]["e_mm"] for c in have])
        chi2 = [MM[ff][c[2]]["chi2"] for c in have]
        rec["mm"][ff] = e_m.tolist()
        rec["mm_chi2"][ff] = chi2
        d = e_m - e_q
        rec["rmse_centered"][ff] = float(np.sqrt(((d - d.mean()) ** 2).mean()))
        # only conformers that stayed in their basin count as that pucker
        ex_ok = [k for k in ex if chi2[k] > 0]
        en_ok = [k for k in en if chi2[k] < 0]
        rec["best_endo_minus_best_exo"][ff] = float(e_m[en_ok].min() - e_m[ex_ok].min()) if ex_ok and en_ok else None
    qm["conformers"] = rec
for method in ("B3LYP-D3BJ/def2-TZVP", "PBE0-D3BJ/def2-SVP", "M06-2X/def2-SVP", SVP):
    v = dict(endo_minus_exo=rel(method, i_endo), barrier_chi2_0=rel(method, i_ts))
    if v["endo_minus_exo"] is not None or v["barrier_chi2_0"] is not None:
        qm["sensitivity"][method] = v
qm["mm_minima"] = {ff: dict(endo_minus_exo=MM[ff][i_endo]["e_mm"] - MM[ff][i_exo]["e_mm"], chi2_exo=MM[ff][i_exo]["chi2"],
                            chi2_endo=MM[ff][i_endo]["chi2"], endo_basin_exists=MM[ff][i_endo]["chi2"] < 0) for ff in FFS}
json.dump(qm, open(os.path.join(R, "qm_vs_mm.json"), "w"), indent=1)
print("DFT jobs done", len(done), "/", len(planned))

# ============================================================== MD
summary = dict(runs={}, not_run=[], reference=dict(
    hyp_endo_exp=0.06, pro_endo_exp=0.58,
    note="NMR-derived ring-pucker propensities for (POG)n triple helices as used by Pantelopulos & Best 2025 (310 K)",
    crystal_phi_psi=dict(PRO=(-72.24, 161.14), HYP=(-60.01, 150.54), GLY=(-69.97, 176.79)),
    lit_md_endo=dict(ff99SB=dict(PRO=0.55, HYP=0.33), ff14SB=dict(PRO=0.50, HYP=0.03), ff19SB=dict(PRO=0.47, HYP=0.03),
                     C36m=dict(PRO=0.29, HYP=0.77))))
dist = {}
for system in ("dipeptide", "dipeptide_endo", "helix"):
    fn = md.SYSTEMS[system][0]
    pdb = app.PDBFile(os.path.join(ffreg.ROOT, "structures", fn))
    top = pdb.topology
    x0 = np.array(pdb.positions._value)
    rows = build.residue_table(top)
    heavy = [[a.index for a in r.atoms() if a.element.symbol != "H"] for r in top.residues() if r.name in ("PRO", "HYP", "GLY")]
    res_labels = [f"{r.chain.id}{r.id}{r.name[0] if r.name != 'HYP' else 'O'}" for r in top.residues() if r.name in ("PRO", "HYP", "GLY")]
    res_chain = [r.chain.id for r in top.residues() if r.name in ("PRO", "HYP", "GLY")]

    def chir(xyz, row):
        a = row["atoms"]
        out = {}
        for centre, nb in (("CA", ("N", "C", "CB")), ("CG", ("CB", "CD", "OD1"))):
            if centre in a and all(n in a for n in nb):
                v = np.einsum("fi,fi->f", xyz[:, a[nb[0]]] - xyz[:, a[centre]],
                              np.cross(xyz[:, a[nb[1]]] - xyz[:, a[centre]], xyz[:, a[nb[2]]] - xyz[:, a[centre]]))
                out[centre] = v
        return out

    if system == "helix":
        cm0 = an.residue_contact_matrix(x0[None], heavy)
        donors, acceptors = [], []
        for r in top.residues():
            at = {a.name: a.index for a in r.atoms()}
            if r.name == "GLY":
                donors.append((at["N"], at["H"], r.chain.id))
            if r.name in ("PRO", "HYP", "GLY"):
                acceptors.append((at["O"], r.chain.id, r.name))
        summary["helix_crystal"] = dict(contact_matrix=cm0.tolist(), labels=res_labels, chains=res_chain)
        m0 = build.measure(rows, x0)
        summary["helix_crystal"]["hyp_endo"] = float(np.mean([float(d["chi2"]) < 0 for r, d in zip(rows, m0) if r["resname"] == "HYP"]))
        summary["helix_crystal"]["pro_endo"] = float(np.mean([float(d["chi2"]) < 0 for r, d in zip(rows, m0) if r["resname"] == "PRO"]))
        hb0 = an.hbond_occupancy(x0[None], [(d[0], d[1]) for d in donors], [a[0] for a in acceptors])
        inter = np.array([[d[2] != a[1] for a in acceptors] for d in donors])
        summary["helix_crystal"]["n_interchain_gly_hbonds"] = float((hb0 * inter).sum())

    for ff in FFS:
        key = f"{system}_{ff}"
        t = md.load(os.path.join(ffreg.ROOT, "md", key))
        if t is None:
            if system != "dipeptide_endo":  # bracketing runs are optional
                summary["not_run"].append(key)
            continue
        xyz = t["xyz"].astype(np.float64)
        meta = t["meta"]
        m = build.measure(rows, xyz)
        rec = dict(ff=ff, system=system, water=meta["water"], n_atoms=meta["n_atoms"], ps=len(xyz) * meta["save_ps"],
                   n_frames=len(xyz), temperature=meta["temperature"], box_nm=meta["box_nm"], residues={})
        dist[key] = {}
        for rn in ("HYP", "PRO", "GLY"):
            sel = [k for k, r in enumerate(rows) if r["resname"] == rn]
            if not sel:
                continue
            phi = np.stack([m[k]["phi"] for k in sel], 1)
            psi = np.stack([m[k]["psi"] for k in sel], 1)
            d = dict(n_res=len(sel), phi_mean=geom.circ_mean(phi), phi_sd=geom.circ_std(phi),
                     psi_mean=geom.circ_mean(psi), psi_sd=geom.circ_std(psi))
            dist[key][rn] = dict(phi=phi.ravel(), psi=psi.ravel())
            if rn != "GLY":
                chi2 = np.stack([m[k]["chi2"] for k in sel], 1)
                chi1 = np.stack([m[k]["chi1"] for k in sel], 1)
                P = np.stack([m[k]["P"] for k in sel], 1)
                amp = np.stack([m[k]["amp"] for k in sel], 1)
                endo = chi2 < 0
                pop = an.population(endo.mean(1))  # per-frame fraction over residues -> time series
                d.update(endo=pop["p"], endo_se=pop["se_block"], endo_first_half=pop["first_half"],
                         endo_second_half=pop["second_half"], stat_inefficiency_frames=pop["g"],
                         n_transitions=int(sum(an.n_transitions(endo[:, c]) for c in range(endo.shape[1]))),
                         per_residue_endo=endo.mean(0).tolist(), amp_mean=float(amp.mean()))
                dist[key][rn].update(chi1=chi1.ravel(), chi2=chi2.ravel(), P=P.ravel(), amp=amp.ravel())
            rec["residues"][rn] = d
        om = np.stack([d["omega"] for d in m], 1)
        rec["cis_amide_frames"] = int((np.abs(om) < 90).any(1).sum())
        ok = True
        for row in rows:
            for centre, v in chir(xyz, row).items():
                ok &= bool(np.all(np.sign(v) == np.sign(v[0])))
        ref = [chir(x0[None], row) for row in rows]
        for row, r0 in zip(rows, ref):
            for centre, v in chir(xyz[:1], row).items():
                ok &= bool(np.sign(v[0]) == np.sign(r0[centre][0]))
        rec["chirality_retained"] = ok
        stride = max(1, len(xyz) // 40)
        rec["min_image_distance_nm"] = float(an.min_image_self_distance(xyz[::stride], t["box"][::stride]).min())
        rec["epot_drift_kj_per_ns"] = float(np.polyfit(np.arange(len(t["epot"])) * meta["save_ps"] / 1000, t["epot"], 1)[0])
        rec["density_proxy_volume_nm3"] = float(t["vol"].mean())
        if system == "helix":
            s2 = max(1, len(xyz) // 100)
            cm = an.residue_contact_matrix(xyz, heavy, stride=s2)
            rec["contact_matrix"] = cm.tolist()
            hb = an.hbond_occupancy(xyz[::s2], [(d[0], d[1]) for d in donors], [a[0] for a in acceptors])
            rec["interchain_gly_hbonds_mean"] = float((hb * inter).sum())
            rec["hbond_matrix"] = hb.tolist()
            bb = [a.index for a in top.atoms() if a.name in ("N", "CA", "C") and a.residue.name in ("PRO", "HYP", "GLY")]
            ref_xyz = x0[bb] - x0[bb].mean(0)
            rm = []
            for f in xyz[::s2]:
                y = f[bb] - f[bb].mean(0)
                u_, s_, vt = np.linalg.svd(y.T @ ref_xyz)
                dsign = np.sign(np.linalg.det(u_ @ vt))
                rot = u_ @ np.diag([1, 1, dsign]) @ vt
                rm.append(np.sqrt((((y @ rot) - ref_xyz) ** 2).sum(1).mean()))
            rec["backbone_rmsd_nm_mean"] = float(np.mean(rm))
            rec["backbone_rmsd_nm_last"] = float(np.mean(rm[-10:]))
        summary["runs"][key] = rec
        hy = rec["residues"].get("HYP", {})
        print(f"{key:20s} {rec['ps']:6.0f} ps  Hyp endo {hy.get('endo', float('nan')):.2f}±{hy.get('endo_se', float('nan')):.2f} "
              f"(halves {hy.get('endo_first_half', 0):.2f}/{hy.get('endo_second_half', 0):.2f}, {hy.get('n_transitions')} transitions) "
              f"phi {hy.get('phi_mean', 0):.0f} psi {hy.get('psi_mean', 0):.0f} cis {rec['cis_amide_frames']} chir {ok} "
              f"minimg {rec['min_image_distance_nm']:.2f}", flush=True)

# pairwise Jensen-Shannon divergence between force fields
bins = dict(phi=np.linspace(-180, 180, 73), psi=np.linspace(-180, 180, 73), chi2=np.linspace(-60, 60, 49))
div = {}
for system in ("dipeptide", "helix"):
    have = [ff for ff in FFS if f"{system}_{ff}" in dist]
    for rn in ("HYP", "PRO", "GLY"):
        for var in ("phi", "psi", "chi2"):
            if not have or rn not in dist[f"{system}_{have[0]}"] or var not in dist[f"{system}_{have[0]}"][rn]:
                continue
            mat = [[an.js_divergence(dist[f"{system}_{a}"][rn][var], dist[f"{system}_{b}"][rn][var], bins[var]) for b in have] for a in have]
            div[f"{system}:{rn}:{var}"] = dict(ffs=have, matrix=mat)
summary["js_divergence"] = div
json.dump(summary, open(os.path.join(R, "md_summary.json"), "w"), indent=1)
np.savez_compressed(os.path.join(R, "md_distributions.npz"), **{f"{k}|{rn}|{v}": arr for k, d in dist.items() for rn, dd in d.items() for v, arr in dd.items()})
print("not run:", summary["not_run"])
