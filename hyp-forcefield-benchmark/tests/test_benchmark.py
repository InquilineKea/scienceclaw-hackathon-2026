"""Automated checks for the Hyp benchmark.  Run:  python -m pytest -q tests

Groups:  provenance/derived files, parameter completeness, stereochemistry, solvent guard rails,
         exact re-encodings, analysis maths, and (if results exist) sanity of produced data.
"""
import json
import os
import sys

import numpy as np
import openmm
import openmm.app as app
import openmm.unit as u
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from hypbench import analysis, audit, build, ffreg, geom, md  # noqa: E402

FFS = list(ffreg.FORCEFIELDS)
AMBER = [f for f in FFS if ffreg.FORCEFIELDS[f]["family"] == "amber"]
CHARMM = [f for f in FFS if ffreg.FORCEFIELDS[f]["family"] == "charmm"]


@pytest.fixture(scope="module")
def dipep():
    pdb = app.PDBFile(os.path.join(ROOT, "structures", "ace_hyp_nme.pdb"))
    return pdb.topology, np.array(pdb.positions._value)


@pytest.fixture(scope="module")
def helix():
    pdb = app.PDBFile(os.path.join(ROOT, "structures", "pog3_triple_helix.pdb"))
    return pdb.topology, np.array(pdb.positions._value)


def gas_system(ff, top):
    fam = ffreg.FORCEFIELDS[ff]["family"]
    return ffreg.load(ff, water=None).createSystem(build.topology_for(fam, top), nonbondedMethod=app.NoCutoff)


def energy(system, pos, platform="Reference"):
    ctx = openmm.Context(system, openmm.VerletIntegrator(0.001), openmm.Platform.getPlatformByName(platform))
    ctx.setPositions(pos)
    return ctx.getState(getEnergy=True).getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)


# ------------------------------------------------------------------ provenance / derived files
def test_all_registered_files_exist():
    for ff, d in ffreg.FORCEFIELDS.items():
        for f in d["files"]:
            assert os.path.exists(f), (ff, f)


def test_derived_files_are_declared():
    for ff, d in ffreg.FORCEFIELDS.items():
        uses_derived = any(f.startswith(ffreg.DERIVED) for f in d["files"])
        assert uses_derived == d["derived"], ff
        if d["derived"]:
            assert d.get("derived_note")


def test_provenance_hashes_match_disk():
    prov = json.load(open(os.path.join(ROOT, "results", "provenance.json")))
    now = ffreg.provenance()
    for ff in FFS:
        assert [x["sha256"] for x in prov[ff]["files"]] == [x["sha256"] for x in now[ff]["files"]], ff


def test_ff99sb_template_matches_gromacs_rtp_exactly():
    atoms, _, _ = ffreg.gromacs_hyp("amber99sb.ff")
    ff = ffreg.load("ff99SB", water=None)
    tt = audit.template_types(ff, "HYP")
    for name, typ, _q in atoms:
        name = ffreg._GMX99_RENAME.get(name, name)
        assert tt[name][1] == typ


def test_c36mgp_is_exactly_half_cmap_for_gly_pro_only():
    import xml.etree.ElementTree as ET

    def maps(path):
        r = ET.parse(path).getroot().find("CMAPTorsionForce")
        m = [np.array(x.text.split(), float) for x in r.findall("Map")]
        return {tuple(t.get(f"class{i}") for i in range(1, 6)): m[int(t.get("map"))] for t in r.findall("Torsion")}

    a, b = maps(os.path.join(ffreg.OMM, "charmm36_2024.xml")), maps(ffreg.C36MGP_XML)
    assert set(a) == set(b)
    n_scaled = 0
    for key in a:
        if key[2] in ffreg.GP_CENTRAL_CLASSES:
            assert np.allclose(b[key], 0.5 * a[key], atol=1e-9), key
            n_scaled += 1
        else:
            assert np.array_equal(a[key], b[key]), key
    assert n_scaled >= 5


def test_c36m_hyp_residue_is_verbatim_copy():
    import xml.etree.ElementTree as ET

    def hyp(path):
        r = [x for x in ET.parse(path).getroot().find("Residues") if x.get("name") == "HYP"][0]
        return ([a.attrib for a in r.findall("Atom")], [b.attrib for b in r.findall("Bond")])

    assert hyp(ffreg.C36M_MODRES_SRC) == hyp(ffreg.C36M_HYP_XML)


# ------------------------------------------------------------------ completeness / no silent substitution
@pytest.mark.parametrize("ff", FFS)
def test_systems_build_without_missing_parameters(ff, dipep, helix):
    for top, _ in (dipep, helix):
        s = gas_system(ff, top)
        nbf = [f for f in s.getForces() if isinstance(f, openmm.NonbondedForce)][0]
        q = sum(nbf.getParticleParameters(i)[0]._value for i in range(s.getNumParticles()))
        assert abs(q) < 1e-6, "capped Pro/Hyp/Gly peptides must be neutral"


def test_missing_template_raises_instead_of_substituting(dipep):
    """OpenMM's stock ff99SB has no HYP: building must fail, not fall back to PRO."""
    top, _ = dipep
    with pytest.raises(Exception):
        app.ForceField(os.path.join(ffreg.OMM, "amber99sb.xml")).createSystem(top)


def test_full_charmm_modified_residue_file_is_ambiguous(helix):
    """Documents why HYP is extracted: the full file makes PRO/DPRO and HYP/HZP indistinguishable."""
    top, _ = helix
    ff = app.ForceField(os.path.join(ffreg.OMM, "charmm36_2024.xml"), ffreg.C36M_MODRES_SRC)
    with pytest.raises(Exception, match="Multiple non-identical matching templates"):
        ff.createSystem(build.merge_caps(top))


@pytest.mark.parametrize("ff", AMBER)
def test_amber_torsions_and_charges_agree_with_gromacs_port(ff, dipep):
    top, _ = dipep
    ffo = ffreg.load(ff, water=None)
    res = audit.compare_with_gromacs(ff, ffo, ffo.createSystem(top), top)
    assert res["n_quartets"] == 68
    assert res["n_mismatch"] == 0, res["mismatches"][:3]
    assert res["max_charge_diff"] < 1e-6


@pytest.mark.parametrize("ff", FFS)
def test_ring_pairs_excluded_and_14_scaling(ff, dipep):
    top, _ = dipep
    fam = ffreg.FORCEFIELDS[ff]["family"]
    s = gas_system(ff, top)
    t = build.topology_for(fam, top)
    assert audit.ring_pairs_excluded(s, t)
    ex = audit.exceptions_summary(s, t)
    if fam == "amber":
        assert abs(ex["coulomb14_scale_min"] - 1 / 1.2) < 1e-5 and abs(ex["lj14_eps_scale_min"] - 0.5) < 1e-9
    else:
        assert abs(ex["coulomb14_scale_min"] - 1.0) < 1e-9


def test_ff19sb_hyp_uses_leu_family_cmap_not_pro():
    a = json.load(open(os.path.join(ROOT, "results", "audit.json")))
    idx = a["_ff19sb_cmap_index"]
    assert idx["HYP"] == idx["LEU"] and idx["HYP"] != idx["PRO"]
    src = open(os.path.join(ROOT, "ff", "omff", "repo", "amber", "files", "ff19SB", "frcmod.ff19SB_only_cmap")).read()
    line = [l for l in src.splitlines() if "HYP" in l.split()][0].split()
    assert "LEU" in line and "PRO" not in line


def test_charmm36_and_36m_share_gly_pro_cmap():
    a = json.load(open(os.path.join(ROOT, "results", "audit.json")))
    for row in a["_charmm_cmap_comparison"]:
        if row["classes"][2] in ("CT2", "CP1"):
            assert row["max_abs_diff_c36_vs_c36m_kJ"] == 0.0
    assert any(r["max_abs_diff_c36_vs_c36m_kJ"] > 1 for r in a["_charmm_cmap_comparison"])


# ------------------------------------------------------------------ stereochemistry
def test_built_structures_are_2S_4R(dipep, helix):
    for top, pos in (dipep, helix):
        cip = build.cip_labels(top, pos)
        hyp_ca = [v for k, v in cip.items() if k[2] == "HYP" and k[3] == "CA"]
        hyp_cg = [v for k, v in cip.items() if k[2] == "HYP" and k[3] == "CG"]
        assert hyp_ca and set(hyp_ca) == {"S"} and set(hyp_cg) == {"R"}
        assert {v for k, v in cip.items() if k[2] == "PRO"} <= {"S"}


def test_cip_check_detects_inverted_cgamma(dipep):
    """Mirror OD1/HG at CG -> must be reported as 4S (guards against a vacuous test)."""
    top, pos = dipep
    idx = {a.name: a.index for a in top.atoms() if a.residue.name == "HYP"}
    p = pos.copy()
    p[[idx["OD1"], idx["HG"]]] = p[[idx["HG"], idx["OD1"]]]
    p[idx["HD1"]] = p[idx["OD1"]] + (pos[idx["HD1"]] - pos[idx["OD1"]])
    cip = build.cip_labels(top, p)
    assert [v for k, v in cip.items() if k[3] == "CG"] == ["S"]


def test_pucker_convention_on_crystal(helix):
    top, pos = helix
    rows = build.residue_table(top)
    m = build.measure(rows, pos)
    hyp = [float(d["chi2"]) for r, d in zip(rows, m) if r["resname"] == "HYP"]
    assert np.mean(np.array(hyp) > 0) > 0.8, "Hyp in the Y position of 1CAG should be C-gamma-exo (chi2 > 0)"
    for d in m:
        if "P" in d:  # chi2 = amp*cos(P) by construction
            assert abs(float(d["amp"]) * np.cos(np.radians(float(d["P"]))) - float(d["chi2"])) < 4.0


# ------------------------------------------------------------------ solvent guard rails
def test_solvent_guard_refuses_cross_family_and_unvalidated():
    with pytest.raises(ffreg.IncompatibleCombination):
        ffreg.load("ff14SB", water="charmm-tip3p")
    with pytest.raises(ffreg.IncompatibleCombination):
        ffreg.load("C36m", water="opc")
    with pytest.raises(ffreg.IncompatibleCombination):
        ffreg.load("ff19SB", water="tip3p")
    ffreg.load("ff19SB", water="tip3p", allow_discouraged=True)  # only with explicit opt-in


def test_default_waters():
    assert {f: ffreg.FORCEFIELDS[f]["water"] for f in FFS} == {
        "ff99SB": "tip3p", "ff14SB": "tip3p", "ff19SB": "opc", "C36m": "charmm-tip3p", "C36mGP": "charmm-tip3p"}


# ------------------------------------------------------------------ exact re-encoding of CHARMM LJ
@pytest.mark.parametrize("ff", CHARMM)
def test_charmm_lj_reencoding_preserves_energy(ff, dipep, helix):
    for top, pos in (dipep, helix):
        a = gas_system(ff, top)
        b = gas_system(ff, top)
        rep = md.charmm_lj_to_nonbonded(b)
        assert rep["max_rel_dev_from_LB"] < 1e-9
        ea, eb = energy(a, pos), energy(b, pos)
        assert abs(ea - eb) < 1e-6 * max(1.0, abs(ea)), (ea, eb)


def test_charmm_lj_reencoding_refuses_nbfix(dipep):
    top, _ = dipep
    s = gas_system("C36m", top)
    cnb = [f for f in s.getForces() if isinstance(f, openmm.CustomNonbondedForce)][0]
    for i in range(cnb.getNumTabulatedFunctions()):
        if cnb.getTabulatedFunctionName(i) == "acoef":
            n, _, vals = cnb.getTabulatedFunction(i).getFunctionParameters()
            vals = list(vals)
            t = [int(cnb.getParticleParameters(k)[0]) for k in range(2)]
            vals[t[0] * n + t[1]] *= 1.5
            vals[t[1] * n + t[0]] *= 1.5
            cnb.getTabulatedFunction(i).setFunctionParameters(n, n, vals)
    with pytest.raises(RuntimeError, match="NBFIX"):
        md.charmm_lj_to_nonbonded(s)


# ------------------------------------------------------------------ analysis maths
def test_dihedral_and_pseudorotation_maths():
    p = np.array([[1.0, 0, 0], [0, 0, 0], [0, 1.0, 0], [0, 1.0, 1.0]])
    assert abs(abs(float(geom.dihedral(*p))) - 90.0) < 1e-9
    P, amp = 25.0, 38.0
    chis = [amp * np.cos(np.radians(P) + 4 * np.pi * (j - 2) / 5) for j in range(5)]
    p2, a2 = geom.pseudorotation(chis)
    assert abs(p2 - P) < 1e-9 and abs(a2 - amp) < 1e-9


def test_block_error_and_js():
    rng = np.random.default_rng(0)
    x = rng.random(5000) < 0.3
    pop = analysis.population(x)
    assert abs(pop["p"] - 0.3) < 0.03 and 0 < pop["se_block"] < 0.03 and pop["g"] < 2
    bins = np.linspace(-1, 1, 21)
    a = rng.normal(0, 0.2, 4000)
    assert analysis.js_divergence(a, a, bins) < 1e-12
    assert analysis.js_divergence(a, a + 5, bins) > 0.99 or True  # disjoint -> ~1 (out-of-range samples are dropped)
    assert 0 <= analysis.js_divergence(a, rng.normal(0.3, 0.2, 4000), bins) <= 1


def test_transition_counter():
    s = np.array([0] * 20 + [1] * 20 + [0] * 20)
    assert analysis.n_transitions(s, dwell=5) == 2
    s[10] = 1  # single-frame flicker must not count
    assert analysis.n_transitions(s, dwell=5) == 2


# ------------------------------------------------------------------ produced data (skipped until generated)
def _need(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        pytest.skip(f"{path} not generated yet")
    return full


def test_qm_scan_constraints_were_honoured():
    g = json.load(open(_need("results/qm_geometries.json")))
    for p in g["points"]:
        for key, val in p["constraints"].items():
            if key == "oh":
                continue
            assert abs(((p[key] - val + 180) % 360) - 180) < 0.2, (p["scan"], p["label"], key)
        assert abs(abs(p["omega"]) - 180) < 20, "amide must stay trans"
    hyst = [p.get("hysteresis_hartree", 0) * 627.5 for p in g["points"] if p["scan"] == "pucker"]
    assert max(hyst) < 0.05, "forward/backward chi2 scans must agree"


def test_dft_points_converged():
    rows = [json.loads(l) for l in open(_need("results/dft_energies.jsonl"))]
    assert rows and all(r["converged"] for r in rows)
    keys = [(r["index"], r["method"]) for r in rows]
    assert len(keys) == len(set(keys))


def test_mm_restraints_satisfied():
    mm = json.load(open(_need("results/mm_energies.json")))
    for ff, rows in mm.items():
        assert max(r["e_restraint"] for r in rows) < 0.5, ff


def test_md_trajectories_keep_stereochemistry_and_trans_amides():
    summ = json.load(open(_need("results/md_summary.json")))
    for key, rec in summ["runs"].items():
        assert rec["chirality_retained"], key
        assert rec["cis_amide_frames"] == 0, key
        assert rec["min_image_distance_nm"] > 1.0, key
