"""Step 2: parameter audit of HYP in every registered force field -> results/audit.json"""
import json
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import openmm
import openmm.app as app

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import audit, build, ffreg, geom  # noqa: E402

R = os.path.join(ffreg.ROOT, "results")
pdb = app.PDBFile(os.path.join(ffreg.ROOT, "structures", "ace_hyp_nme.pdb"))
top_amber = pdb.topology
pos = np.array(pdb.positions._value)
out = {}

RING_BONDS = [("N", "CA"), ("CA", "CB"), ("CB", "CG"), ("CG", "CD"), ("CD", "N")]

for name, d in ffreg.FORCEFIELDS.items():
    fam = d["family"]
    ff = ffreg.load(name, water=None)
    top = build.topology_for(fam, top_amber)
    system = ff.createSystem(top)  # raises if any parameter is missing
    rec = dict(family=fam)
    # atom table (system-level; atom order identical across families)
    at = audit.atom_table(ff, system, top)
    tt = audit.template_types(ff, "HYP")
    # map template names -> our atom order by charge-agnostic graph position: use element+neighbour signature
    hyp_atoms = [a for a in top_amber.atoms() if a.residue.name == "HYP"]
    rec["hyp_atoms"] = [dict(name=a.name, charge=at[a.index]["charge"], sigma_nm=at[a.index]["sigma_nm"],
                             eps_kj=at[a.index]["eps_kj"]) for a in hyp_atoms]
    rec["hyp_template"] = {k: dict(type=v[0], cls=v[1]) for k, v in tt.items()}
    rec["net_charge_dipeptide"] = round(sum(r["charge"] for r in at), 6)
    rec["net_charge_hyp_residue"] = round(sum(at[a.index]["charge"] for a in hyp_atoms), 6)
    # torsions
    props, imps = audit.proper_torsions(system, top)
    nm = {a.index: f"{a.residue.name}:{a.name}" for a in top_amber.atoms()}
    bare = {a.index: a.name for a in top_amber.atoms()}
    hyp_idx = {a.index for a in hyp_atoms}
    ring, backbone = {}, {}
    for (i, j, k, l), terms in props.items():
        central = {bare[j], bare[k]}
        label = "-".join(nm[x].replace("HYP:", "") for x in (i, j, k, l))
        if j in hyp_idx and k in hyp_idx and any(central == set(b) for b in RING_BONDS):
            ring[label] = terms
        if j in hyp_idx and k in hyp_idx and central == {"CA", "C"}:
            backbone[label] = terms
    rec["ring_torsion_terms"] = ring
    rec["psi_bond_torsion_terms"] = backbone
    rec["n_ring_torsion_terms"] = sum(len(v) for v in ring.values())
    rec["n_improper_centres"] = len(imps)
    rec["forces"] = sorted({f.__class__.__name__ for f in system.getForces()})
    # CMAP
    cm = [f for f in system.getForces() if isinstance(f, openmm.CMAPTorsionForce)]
    if cm:
        f = cm[0]
        rec["cmap_torsions"] = []
        for t in range(f.getNumTorsions()):
            mp, a1, a2, a3, a4, b1, b2, b3, b4 = f.getTorsionParameters(t)
            size, en = f.getMapParameters(mp)
            en = np.array(en.value_in_unit(openmm.unit.kilocalorie_per_mole))
            rec["cmap_torsions"].append(dict(centre=nm[a3], map=mp, grid=size, min=float(en.min()), max=float(en.max()),
                                             rms=float(np.sqrt((en ** 2).mean()))))
    # exclusions
    rec["exceptions"] = audit.exceptions_summary(system, top)
    rec["ring_pairs_fully_excluded"] = bool(audit.ring_pairs_excluded(system, top))
    # cross-check with the independent GROMACS port (AMBER family only)
    if fam == "amber":
        cmp_ = audit.compare_with_gromacs(name, ff, system, top)
        rec["gromacs_crosscheck"] = dict(n_quartets=cmp_["n_quartets"], n_mismatch=cmp_["n_mismatch"],
                                         max_charge_diff=cmp_["max_charge_diff"], mismatches=cmp_["mismatches"][:20])
        rec["torsion_match_kind"] = {"-".join(r["atoms"]).replace("HYP:", ""): r["match"] for r in cmp_["rows"]
                                     if all(x.startswith("HYP:") for x in r["atoms"][1:3])}
    out[name] = rec
    print(f"{name:7s} netQ={rec['net_charge_dipeptide']:+.4f} ring terms={rec['n_ring_torsion_terms']:3d} "
          f"14scale=({rec['exceptions']['coulomb14_scale_min']:.4f},{rec['exceptions']['lj14_eps_scale_min'] if rec['exceptions']['lj14_eps_scale_min'] is None else round(rec['exceptions']['lj14_eps_scale_min'],3)}) "
          f"ring-excl={rec['ring_pairs_fully_excluded']} cmap={len(rec.get('cmap_torsions', []))} "
          + (f"gmx-mismatch={rec['gromacs_crosscheck']['n_mismatch']}/{rec['gromacs_crosscheck']['n_quartets']} dq={rec['gromacs_crosscheck']['max_charge_diff']:.1e}" if fam == "amber" else ""))

# ---- CHARMM36 (aug15) vs CHARMM36m (jul24): are Gly/Pro CMAPs and HYP charges the same?
def cmaps(path):
    r = ET.parse(path).getroot().find("CMAPTorsionForce")
    maps = [np.array(m.text.split(), float) for m in r.findall("Map")]
    res = {}
    for t in r.findall("Torsion"):
        key = tuple(t.get(f"class{i}") or t.get(f"type{i}") for i in range(1, 6))
        res[key] = maps[int(t.get("map"))]
    return res


c36 = cmaps(os.path.join(ffreg.OMM, "charmm36.xml"))
c36m = cmaps(os.path.join(ffreg.OMM, "charmm36_2024.xml"))
gp = cmaps(ffreg.C36MGP_XML)
cmp_rows = []
for key in sorted(set(c36) & set(c36m)):
    d = float(np.abs(c36[key] - c36m[key]).max())
    ratio = float(np.abs(gp[key]).max() / max(np.abs(c36m[key]).max(), 1e-12))
    cmp_rows.append(dict(classes=key, max_abs_diff_c36_vs_c36m_kJ=d, c36mGP_over_c36m=ratio))
    print("CMAP", key, f"max|C36-C36m|={d:.4f} kJ/mol  GP/C36m={ratio:.2f}")
out["_charmm_cmap_comparison"] = cmp_rows


def hyp_charges(path):
    for r in ET.parse(path).getroot().find("Residues"):
        if r.get("name") == "HYP":
            return {a.get("name"): float(a.get("charge")) for a in r.findall("Atom")}


out["_charmm_hyp_charges_aug15_equals_jul24"] = hyp_charges(os.path.join(ffreg.OMM, "charmm36.xml")) == hyp_charges(ffreg.C36M_HYP_XML)

# ---- ff19SB: does HYP have its own CMAP or share another residue's?
r19 = ET.parse(os.path.join(ffreg.OMM, "amber19", "protein.ff19SB.xml")).getroot().find("CMAPTorsionForce")
maps19 = [np.array(m.text.split(), float) for m in r19.findall("Map")]
res_map = {}
for t in r19.findall("Torsion"):
    m = [t.get(f"type{i}") for i in range(1, 6) if t.get(f"type{i}")]
    resn = [x.split("-")[1] for x in m if x.startswith("cmap-")]
    if resn:
        res_map[resn[0]] = int(t.get("map"))
out["_ff19sb_cmap_index"] = res_map
same = [r for r, i in res_map.items() if r != "HYP" and i == res_map.get("HYP")]
ident = [r for r, i in res_map.items() if r != "HYP" and np.allclose(maps19[i], maps19[res_map["HYP"]])]
out["_ff19sb_hyp_cmap_shared_with"] = sorted(set(same) | set(ident))
print("ff19SB HYP CMAP map index", res_map.get("HYP"), "shared/identical with:", out["_ff19sb_hyp_cmap_shared_with"])

# ---- water / ion models
water = {}
for (fam, w), path in ffreg.WATER_FILES.items():
    root = ET.parse(path).getroot()
    resn = [x.get("name") for x in root.find("Residues")]
    hoh = [x for x in root.find("Residues") if x.get("name") in ("HOH", "TIP3")][0]
    types = {t.get("name"): t for t in root.find("AtomTypes")}
    nbf = root.find("NonbondedForce")
    par = {a.get("type") or a.get("class"): a.attrib for a in nbf.findall("Atom")}
    lj = root.find("LennardJonesForce")
    sites = []
    for a in hoh.findall("Atom"):
        t = a.get("type")
        p = par.get(t, par.get(types[t].get("class"), {}))
        sites.append(dict(name=a.get("name"), charge=a.get("charge") or p.get("charge"), sigma=p.get("sigma"), epsilon=p.get("epsilon")))
    info = root.find("Info")
    water[f"{fam}:{w}"] = dict(file=os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path), n_sites=len(sites), sites=sites,
                               ions=sorted(x for x in resn if x not in ("HOH", "TIP3")),
                               source=[s.text for s in info.findall("Source")] if info is not None else [],
                               has_separate_LJ_force=lj is not None)
    print("water", fam, w, "sites", len(sites), "ions", len(resn) - 1)
out["_water_models"] = water
out["_solvent_policy"] = ffreg.SOLVENT_POLICY

# ---- stereochemistry of the built structures
for label, fn in (("ace_hyp_nme", "ace_hyp_nme.pdb"), ("pog3_triple_helix", "pog3_triple_helix.pdb")):
    p = app.PDBFile(os.path.join(ffreg.ROOT, "structures", fn))
    cip = build.cip_labels(p.topology, np.array(p.positions._value))
    summary = {}
    for (ch, rid, rn, an), v in cip.items():
        summary.setdefault(f"{rn}:{an}", {}).setdefault(v, 0)
        summary[f"{rn}:{an}"][v] += 1
    out.setdefault("_stereo", {})[label] = summary
    print("CIP", label, summary)

json.dump(out, open(os.path.join(R, "audit.json"), "w"), indent=1, default=str)
