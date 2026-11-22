"""Geometry helpers: dihedrals, proline-ring pseudorotation, chirality."""
import numpy as np

RING_CHI = {  # torsion name -> atom names (PDB nomenclature, heavy atoms)
    "chi0": ("CD", "N", "CA", "CB"),
    "chi1": ("N", "CA", "CB", "CG"),
    "chi2": ("CA", "CB", "CG", "CD"),
    "chi3": ("CB", "CG", "CD", "N"),
    "chi4": ("CG", "CD", "N", "CA"),
}


def dihedral(p0, p1, p2, p3):
    """Signed dihedral in degrees; works on (...,3) arrays."""
    b0 = p0 - p1
    b1 = p2 - p1
    b2 = p3 - p2
    b1n = b1 / np.linalg.norm(b1, axis=-1, keepdims=True)
    v = b0 - np.sum(b0 * b1n, axis=-1, keepdims=True) * b1n
    w = b2 - np.sum(b2 * b1n, axis=-1, keepdims=True) * b1n
    x = np.sum(v * w, axis=-1)
    y = np.sum(np.cross(b1n, v) * w, axis=-1)
    return np.degrees(np.arctan2(y, x))


def pseudorotation(chis):
    """Altona-Sundaralingam style pseudorotation for a 5-ring.

    chis: array (...,5) = chi0..chi4 in degrees with chi_j = A*cos(P + 4*pi*(j-2)/5).
    Returns (P in degrees in (-180,180], amplitude in degrees).
    With this convention chi2 = A*cos(P): P ~ 0 -> chi2>0 (Cgamma-exo, 'UP'),
    P ~ 180 -> chi2<0 (Cgamma-endo, 'DOWN').
    """
    chis = np.asarray(chis, float)
    j = np.arange(5)
    ang = 4 * np.pi * (j - 2) / 5
    a = 0.4 * np.sum(chis * np.cos(ang), axis=-1)
    b = -0.4 * np.sum(chis * np.sin(ang), axis=-1)
    return np.degrees(np.arctan2(b, a)), np.hypot(a, b)


def pucker_label(chi2):
    """exo if chi2 > 0 else endo (Ho et al. 2005 UP/DOWN convention)."""
    return np.where(np.asarray(chi2) > 0, "exo", "endo")


def chiral_volume(center, a, b, c):
    """Signed volume (a-center) . ((b-center) x (c-center))."""
    return float(np.dot(a - center, np.cross(b - center, c - center)))


def wrap(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0


def circ_mean(deg):
    r = np.radians(deg)
    return float(np.degrees(np.arctan2(np.sin(r).mean(), np.cos(r).mean())))


def circ_std(deg):
    r = np.radians(deg)
    R = np.hypot(np.sin(r).mean(), np.cos(r).mean())
    return float(np.degrees(np.sqrt(max(-2 * np.log(max(R, 1e-12)), 0.0))))
