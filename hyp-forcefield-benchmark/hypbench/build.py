"""Build capped peptides from the 1CAG crystal structure (Bella et al. 1994, 1.85 A).

All force fields start from the *same* coordinates.  AMBER-family topologies carry ACE/NME as
separate residues; CHARMM-family topologies carry the cap atoms inside the terminal residues
(CHARMM caps are patches), produced by merge_caps() with identical atom order.
"""
import os

import numpy as np
import openmm.app as app
import openmm.unit as u

from . import geom
from .ffreg import ROOT

PDB_1CAG = os.path.join(ROOT, "ff", "pdb_1cag_a", "1cag.pdb")

HEAVY_BONDS = {
    "PRO": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"), ("CG", "CD"), ("CD", "N")],
    "HYP": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"), ("CG", "CD"), ("CD", "N"), ("CG", "OD1")],
    "GLY": [("N", "CA"), ("CA", "C"), ("C", "O")],
    "ACE": [("CH3", "C"), ("C", "O")],
    "NME": [("N", "C")],
}

HYP_HYDROGENS = """<Residues>
 <Residue name="HYP">
  <H name="HA" parent="CA"/>
  <H name="HB2" parent="CB"/>
  <H name="HB3" parent="CB"/>
  <H name="HG" parent="CG"/>
  <H name="HD22" parent="CD"/>
  <H name="HD23" parent="CD"/>
  <H name="HD1" parent="OD1"/>
 </Residue>
</Residues>
"""


def read_pdb_atoms(path=PDB_1CAG):
    """{chain: {resnum: (resname, {atomname: xyz_A})}} for protein heavy atoms."""
    out = {}
    for line in open(path):
        if not line.startswith(("ATOM", "HETATM")):
            continue
        rn = line[17:20].strip()
        if rn not in ("PRO", "HYP", "GLY", "ALA"):
            continue
        ch, ri, an = line[21], int(line[22:26]), line[12:16].strip()
        xyz = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
        out.setdefault(ch, {}).setdefault(ri, (rn, {}))[1][an] = xyz
    return out


def _element(name):
    return app.element.Element.getBySymbol(name[0])


def build_capped(segments, pdb=PDB_1CAG):
    """segments: list of (chain_id, first_res, last_res).  Returns (Topology, positions[nm]) with H added."""
    data = read_pdb_atoms(pdb)
    top = app.Topology()
    pos = []
    for ch, first, last in segments:
        chain = top.addChain(ch)
        res = data[ch]
        prev_c = None
        # ACE from residue first-1
        rn, at = res[first - 1]
        r = top.addResidue("ACE", chain)
        amap = {}
        for new, old in (("CH3", "CA"), ("C", "C"), ("O", "O")):
            amap[new] = top.addAtom(new, _element(old), r)
            pos.append(at[old])
        for a, b in HEAVY_BONDS["ACE"]:
            top.addBond(amap[a], amap[b])
        prev_c = amap["C"]
        for ri in range(first, last + 1):
            rn, at = res[ri]
            if rn not in ("PRO", "HYP", "GLY"):
                raise ValueError(f"residue {ch}{ri} is {rn}; only PRO/HYP/GLY segments are supported")
            r = top.addResidue(rn, chain, id=str(ri))
            amap = {}
            for an in ("N", "CA", "C", "O", "CB", "CG", "CD", "OD1"):
                if an in at:
                    amap[an] = top.addAtom(an, _element(an), r)
                    pos.append(at[an])
            for a, b in HEAVY_BONDS[rn]:
                top.addBond(amap[a], amap[b])
            top.addBond(prev_c, amap["N"])
            prev_c = amap["C"]
        rn, at = res[last + 1]
        r = top.addResidue("NME", chain)
        amap = {}
        for new, old in (("N", "N"), ("C", "CA")):
            amap[new] = top.addAtom(new, _element(old), r)
            pos.append(at[old])
        top.addBond(amap["N"], amap["C"])
        top.addBond(prev_c, amap["N"])
    pos = np.array(pos) * 0.1
    hyd = os.path.join(ROOT, "ff", "derived", "hyp_hydrogens.xml")
    os.makedirs(os.path.dirname(hyd), exist_ok=True)
    with open(hyd, "w") as f:
        f.write(HYP_HYDROGENS)
    app.Modeller.loadHydrogenDefinitions(hyd)
    mod = app.Modeller(top, pos * u.nanometer)
    mod.addHydrogens(forcefield=None)
    return mod.topology, np.array(mod.positions.value_in_unit(u.nanometer))


def merge_caps(top):
    """Same atoms/order/bonds, but ACE atoms join the first residue and NME atoms the last (CHARMM patches)."""
    new = app.Topology()
    amap = {}
    for chain in top.chains():
        c = new.addChain(chain.id)
        residues = list(chain.residues())
        assert residues[0].name == "ACE" and residues[-1].name == "NME"
        body = residues[1:-1]
        cur = None
        for res in residues:
            if res.name == "ACE":
                cur = new.addResidue(body[0].name, c, id=body[0].id)
                prefix = "Y"  # CHARMM-like cap names: CAY, CY, OY, HY1..
            elif res.name == "NME":
                prefix = "T"
            else:
                if res is not body[0]:
                    cur = new.addResidue(res.name, c, id=res.id)
                prefix = None
            for a in res.atoms():
                name = a.name if prefix is None else f"{a.name}{prefix}"
                amap[a] = new.addAtom(name, a.element, cur)
    for b in top.bonds():
        new.addBond(amap[b[0]], amap[b[1]])
    new.setPeriodicBoxVectors(top.getPeriodicBoxVectors())
    return new


def topology_for(ff_family, top):
    return merge_caps(top) if ff_family == "charmm" else top


# ----------------------------------------------------------------------------- torsion bookkeeping
def residue_table(top):
    """List of dicts for PRO/HYP/GLY residues with atom indices needed for phi/psi/omega/chis.

    Works on the AMBER-style topology (caps as residues)."""
    rows = []
    for chain in top.chains():
        residues = list(chain.residues())
        for k, res in enumerate(residues):
            if res.name not in ("PRO", "HYP", "GLY"):
                continue
            a = {x.name: x.index for x in res.atoms()}
            prv = {x.name: x.index for x in residues[k - 1].atoms()}
            nxt = {x.name: x.index for x in residues[k + 1].atoms()}
            row = dict(chain=chain.id, resid=res.id, resname=res.name, atoms=a)
            row["phi"] = (prv["C"], a["N"], a["CA"], a["C"])
            row["psi"] = (a["N"], a["CA"], a["C"], nxt["N"])
            prev_ca = prv.get("CA", prv.get("CH3"))
            row["omega"] = (prev_ca, prv["C"], a["N"], a["CA"])
            if res.name in ("PRO", "HYP"):
                for name, quad in geom.RING_CHI.items():
                    row[name] = tuple(a[q] for q in quad)
            rows.append(row)
    return rows


def measure(rows, xyz):
    """xyz: (n_atoms,3) or (n_frames,n_atoms,3).  Returns {key: array} per residue row."""
    out = []
    for row in rows:
        d = {}
        for key in ("phi", "psi", "omega", "chi0", "chi1", "chi2", "chi3", "chi4"):
            if key in row:
                i, j, k, l = row[key]
                d[key] = geom.dihedral(xyz[..., i, :], xyz[..., j, :], xyz[..., k, :], xyz[..., l, :])
        if "chi2" in d:
            chis = np.stack([d[f"chi{n}"] for n in range(5)], axis=-1)
            d["P"], d["amp"] = geom.pseudorotation(chis)
        out.append(d)
    return out


def write_pdb(path, top, pos_nm):
    with open(path, "w") as f:
        app.PDBFile.writeFile(top, pos_nm * 10 * u.angstrom, f, keepIds=True)


def cip_labels(top, pos_nm):
    """CIP labels of stereocentres from 3D coordinates via RDKit: {(chain,resid,resname,atom): 'R'/'S'}."""
    from rdkit import Chem
    from rdkit.Chem import rdCIPLabeler
    from rdkit.Geometry import Point3D

    rw = Chem.RWMol()
    atoms = list(top.atoms())
    for a in atoms:
        rw.AddAtom(Chem.Atom(a.element.atomic_number))
    order = {}
    for b in top.bonds():
        order[(b[0].index, b[1].index)] = 1
    # carbonyls: C=O double bonds so valences are right
    for (i, j) in list(order):
        ai, aj = atoms[i], atoms[j]
        names = {ai.name, aj.name}
        if names in ({"C", "O"},) and ai.residue == aj.residue and {ai.element.symbol, aj.element.symbol} == {"C", "O"}:
            order[(i, j)] = 2
    for (i, j), o in order.items():
        rw.AddBond(i, j, Chem.BondType.DOUBLE if o == 2 else Chem.BondType.SINGLE)
    mol = rw.GetMol()
    conf = Chem.Conformer(len(atoms))
    for i, p in enumerate(pos_nm * 10):
        conf.SetAtomPosition(i, Point3D(*map(float, p)))
    mol.AddConformer(conf)
    Chem.SanitizeMol(mol)
    Chem.AssignStereochemistryFrom3D(mol)
    rdCIPLabeler.AssignCIPLabels(mol)
    out = {}
    for a in mol.GetAtoms():
        if a.HasProp("_CIPCode"):
            t = atoms[a.GetIdx()]
            out[(t.residue.chain.id, t.residue.id, t.residue.name, t.name)] = a.GetProp("_CIPCode")
    return out
