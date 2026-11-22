"""Parameter audit helpers (operate on created OpenMM Systems, i.e. on what would actually be simulated)."""
import os
import re
from collections import defaultdict

import numpy as np
import openmm
import openmm.unit as u

from . import ffreg

KJ = 4.184


def bonded_graph(top):
    nb = defaultdict(set)
    for b in top.bonds():
        nb[b[0].index].add(b[1].index)
        nb[b[1].index].add(b[0].index)
    return nb


def atom_table(ff_obj, system, top):
    """Per-atom (name, residue, type, class, charge, sigma, epsilon) for the system."""
    nbf = [f for f in system.getForces() if isinstance(f, openmm.NonbondedForce)][0]
    rows = []
    for a in top.atoms():
        q, sig, eps = nbf.getParticleParameters(a.index)
        rows.append(dict(index=a.index, name=a.name, res=a.residue.name, charge=round(q._value, 5),
                         sigma_nm=round(sig._value, 6), eps_kj=round(eps._value, 6)))
    return rows


def template_types(ff_obj, resname="HYP"):
    t = ff_obj._templates[resname]
    return {a.name: (a.type, ff_obj._atomTypes[a.type].atomClass) for a in t.atoms}


def proper_torsions(system, top):
    """{(i,j,k,l) canonical: [(n, phase_deg, k_kcal)]} for proper torsions (i-j-k-l bonded chain)."""
    nb = bonded_graph(top)
    out = defaultdict(list)
    imp = defaultdict(list)
    for f in system.getForces():
        if isinstance(f, openmm.PeriodicTorsionForce):
            for t in range(f.getNumTorsions()):
                i, j, k, l, n, ph, kk = f.getTorsionParameters(t)
                kk = kk.value_in_unit(u.kilojoule_per_mole) / KJ
                ph = ph.value_in_unit(u.degree)
                if abs(kk) < 1e-9:
                    continue
                if j in nb[i] and k in nb[j] and l in nb[k]:
                    key = (i, j, k, l) if (j, i) < (k, l) else (l, k, j, i)
                    out[key].append((int(n), round(ph, 2), round(kk, 5)))
                else:
                    imp[tuple(sorted((i, j, k, l)))].append((int(n), round(ph, 2), round(kk, 5)))
    return {k: sorted(v) for k, v in out.items()}, {k: sorted(v) for k, v in imp.items()}


def exceptions_summary(system, top):
    """1-4 scale factors actually present, plus a check that ring atoms never interact via nonbonded terms."""
    nbf = [f for f in system.getForces() if isinstance(f, openmm.NonbondedForce)][0]
    q = np.array([nbf.getParticleParameters(i)[0]._value for i in range(system.getNumParticles())])
    eps = np.array([nbf.getParticleParameters(i)[2]._value for i in range(system.getNumParticles())])
    nb = bonded_graph(top)
    scales, ljs = [], []
    n14 = n_excl = 0
    for e in range(nbf.getNumExceptions()):
        i, j, qq, sig, ee = nbf.getExceptionParameters(e)
        qq, ee = qq._value, ee._value
        if qq == 0 and ee == 0:
            n_excl += 1
            continue
        n14 += 1
        if abs(q[i] * q[j]) > 1e-6:
            scales.append(qq / (q[i] * q[j]))
        if eps[i] * eps[j] > 0:
            ljs.append(ee / np.sqrt(eps[i] * eps[j]))
    return dict(n_excluded_pairs=n_excl, n_14_pairs=n14,
                coulomb14_scale_min=float(np.min(scales)) if scales else None,
                coulomb14_scale_max=float(np.max(scales)) if scales else None,
                lj14_eps_scale_min=float(np.min(ljs)) if ljs else None,
                lj14_eps_scale_max=float(np.max(ljs)) if ljs else None)


def ring_pairs_excluded(system, top, ring_names=("N", "CA", "CB", "CG", "CD"), resname="HYP"):
    """All ring-ring atom pairs must be fully excluded (1-2/1-3 around a 5-ring)."""
    nbf = [f for f in system.getForces() if isinstance(f, openmm.NonbondedForce)][0]
    res = [r for r in top.residues() if r.name == resname][0]
    idx = {a.index for a in res.atoms() if a.name in ring_names}
    found = {}
    for e in range(nbf.getNumExceptions()):
        i, j, qq, sig, ee = nbf.getExceptionParameters(e)
        if i in idx and j in idx:
            found[(min(i, j), max(i, j))] = (qq._value == 0 and ee._value == 0)
    want = {(a, b) for a in idx for b in idx if a < b}
    return want == set(found) and all(found.values())


# ----------------------------------------------------------------------------- GROMACS cross-check
def parse_gmx_dihedraltypes(ffdir):
    """[(types4, func, phase, k_kJ, n)] in file order."""
    out = []
    sect = None
    for line in open(os.path.join(ffreg.GMX, ffdir, "ffbonded.itp")):
        line = line.split(";")[0].strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"\[\s*(\w+)\s*\]", line)
        if m:
            sect = m.group(1)
            continue
        if sect == "dihedraltypes":
            p = line.split()
            out.append((tuple(p[:4]), int(p[4]), float(p[5]), float(p[6]), int(p[7])))
    return out


def gmx_lookup(dihtypes, types4):
    """GROMACS-style proper dihedral lookup (func 9): exact match (either direction) beats wildcard X-j-k-X.

    Returns (terms [(n, phase, k_kcal)], 'specific'|'wildcard'|'missing')."""
    exact, wild = [], []
    for t, func, ph, k, n in dihtypes:
        if func != 9:
            continue
        for cand in (types4, types4[::-1]):
            if t == cand:
                exact.append((n, round(ph, 2), round(k / KJ, 5)))
                break
            if t[0] == "X" and t[3] == "X" and t[1:3] == cand[1:3]:
                wild.append((n, round(ph, 2), round(k / KJ, 5)))
                break
    if exact:
        return sorted(set(x for x in exact if abs(x[2]) > 1e-9)), "specific"
    if wild:
        return sorted(set(x for x in wild if abs(x[2]) > 1e-9)), "wildcard"
    return [], "missing"


ACE_NME_AMBER_TYPES = {("ACE", "CH3"): "CT", ("ACE", "C"): "C", ("ACE", "O"): "O", ("ACE", "H1"): "HC",
                       ("ACE", "H2"): "HC", ("ACE", "H3"): "HC", ("NME", "N"): "N", ("NME", "H"): "H",
                       ("NME", "C"): "CT", ("NME", "H1"): "H1", ("NME", "H2"): "H1", ("NME", "H3"): "H1"}


def amber_types_for_dipeptide(ff, top):
    """AMBER atom type per atom of Ace-Hyp-NMe taken from the GROMACS port's HYP entry."""
    ffdir = {"ff99SB": "amber99sb.ff", "ff14SB": "amber14sb.ff", "ff19SB": "amber19sb.ff"}[ff]
    atoms, _, _ = ffreg.gromacs_hyp(ffdir)
    ren = ffreg._GMX99_RENAME if ff == "ff99SB" else {}
    hyp = {ren.get(n, n): (t, q) for n, t, q in atoms}
    types, charges = {}, {}
    for a in top.atoms():
        if a.residue.name == "HYP":
            types[a.index], charges[a.index] = hyp[a.name]
        else:
            types[a.index] = ACE_NME_AMBER_TYPES[(a.residue.name, a.name)]
    return types, charges, ffdir


def compare_with_gromacs(ff, ff_obj, system, top):
    """Compare every proper torsion of the OpenMM system with the GROMACS port's ffbonded.itp."""
    types, charges, ffdir = amber_types_for_dipeptide(ff, top)
    dts = parse_gmx_dihedraltypes(ffdir)
    props, _ = proper_torsions(system, top)
    nb = bonded_graph(top)
    names = {a.index: f"{a.residue.name}:{a.name}" for a in top.atoms()}
    # enumerate all bonded quartets
    quartets = set()
    for j in nb:
        for k in nb[j]:
            if j < k:
                for i in nb[j] - {k}:
                    for l in nb[k] - {j}:
                        if i != l:
                            quartets.add((i, j, k, l) if (j, i) < (k, l) else (l, k, j, i))
    rows, mismatches = [], []
    for qd in sorted(quartets):
        t4 = tuple(types[x] for x in qd)
        g, how = gmx_lookup(dts, t4)
        o = sorted(set(props.get(qd, [])))
        ok = len(g) == len(o) and all(a[0] == b[0] and abs(a[1] - b[1]) < 0.05 and abs(a[2] - b[2]) < 2e-4 for a, b in zip(g, o))
        rows.append(dict(atoms=[names[x] for x in qd], types=t4, gromacs=g, openmm=o, match=how, agree=ok))
        if not ok:
            mismatches.append(rows[-1])
    nbf = [f for f in system.getForces() if isinstance(f, openmm.NonbondedForce)][0]
    dq = max(abs(nbf.getParticleParameters(i)[0]._value - q) for i, q in charges.items())
    return dict(n_quartets=len(rows), n_mismatch=len(mismatches), mismatches=mismatches, max_charge_diff=dq, rows=rows)
