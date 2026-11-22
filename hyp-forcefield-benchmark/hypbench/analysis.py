"""Statistics for the benchmark: populations with block errors, free energies, divergences, contacts."""
import numpy as np

KT300 = 0.0019872041 * 300.0  # kcal/mol


def block_se(x, n_blocks=5):
    """Standard error of the mean from contiguous blocks (time-ordered data)."""
    x = np.asarray(x, float)
    if len(x) < n_blocks * 2:
        return float("nan")
    b = np.array_split(x, n_blocks)
    m = np.array([y.mean() for y in b])
    return float(m.std(ddof=1) / np.sqrt(n_blocks))


def stat_inefficiency(x, max_lag=None):
    """Integrated autocorrelation estimate g = 1 + 2*sum(C(t)) truncated at first non-positive C(t)."""
    x = np.asarray(x, float)
    x = x - x.mean()
    v = x.var()
    if v == 0:
        return float("inf")
    n = len(x)
    g = 1.0
    for t in range(1, max_lag or n // 2):
        c = np.dot(x[:-t], x[t:]) / ((n - t) * v)
        if c <= 0:
            break
        g += 2 * c * (1 - t / n)
    return float(g)


def n_transitions(indicator, dwell=5):
    """Count state changes of a boolean series after a median-like debounce (state must persist `dwell` frames)."""
    s = np.asarray(indicator).astype(int)
    if len(s) == 0:
        return 0
    cur, run, n, cand = s[0], 0, 0, s[0]
    for v in s[1:]:
        if v != cur:
            if v == cand:
                run += 1
            else:
                cand, run = v, 1
            if run >= dwell:
                cur, run, n = v, 0, n + 1
        else:
            run, cand = 0, cur
    return n


def population(indicator, n_blocks=5):
    x = np.asarray(indicator, float)
    half = len(x) // 2
    return dict(p=float(x.mean()), se_block=block_se(x, n_blocks), first_half=float(x[:half].mean()),
                second_half=float(x[half:].mean()), g=stat_inefficiency(x), n_frames=int(len(x)),
                n_transitions=n_transitions(x > 0.5))


def free_energy_1d(x, bins, kT=KT300):
    h, e = np.histogram(x, bins=bins)
    p = h / h.sum()
    with np.errstate(divide="ignore"):
        f = -kT * np.log(p)
    f -= np.nanmin(f[np.isfinite(f)])
    return 0.5 * (e[1:] + e[:-1]), f, h


def free_energy_2d(x, y, bins, kT=KT300):
    h, xe, ye = np.histogram2d(x, y, bins=bins)
    p = h / h.sum()
    with np.errstate(divide="ignore"):
        f = -kT * np.log(p)
    f -= f[np.isfinite(f)].min()
    return xe, ye, f.T, h.T


def js_divergence(a, b, bins):
    """Jensen-Shannon divergence (bits, 0..1) between two samples on common bins."""
    p, _ = np.histogram(a, bins=bins)
    q, _ = np.histogram(b, bins=bins)
    p = p / max(p.sum(), 1)
    q = q / max(q.sum(), 1)
    m = 0.5 * (p + q)

    def kl(u, v):
        mask = u > 0
        return float(np.sum(u[mask] * np.log2(u[mask] / v[mask])))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def min_image_self_distance(xyz, box):
    """Minimum distance between solute atoms and any periodic image of the solute (orthorhombic), per frame."""
    out = np.empty(len(xyz))
    shifts = [np.array(s) for s in ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1),
                                     (1, -1, 0), (1, 0, -1), (0, 1, -1), (1, -1, -1), (1, 1, -1), (1, -1, 1))]
    for f in range(len(xyz)):
        x = xyz[f].astype(float)
        best = np.inf
        for s in shifts:
            d = x[:, None, :] - (x[None, :, :] + s * box[f])
            best = min(best, np.sqrt((d ** 2).sum(-1).min()))
        out[f] = best
    return out


def residue_contact_matrix(xyz, res_atoms, cutoff=0.4, stride=1):
    """Fraction of frames in which residues i,j have any heavy-atom pair within cutoff (nm)."""
    n = len(res_atoms)
    m = np.zeros((n, n))
    frames = xyz[::stride]
    for x in frames:
        for i in range(n):
            xi = x[res_atoms[i]]
            for j in range(i + 1, n):
                d = xi[:, None, :] - x[res_atoms[j]][None, :, :]
                if (d ** 2).sum(-1).min() < cutoff ** 2:
                    m[i, j] += 1
                    m[j, i] += 1
    return m / len(frames)


def hbond_occupancy(xyz, donors, acceptors, d_cut=0.35, angle_cut=140.0):
    """donors: [(N,H)], acceptors: [O]; returns occupancy matrix [donor, acceptor]."""
    occ = np.zeros((len(donors), len(acceptors)))
    for x in xyz:
        for a, (n, h) in enumerate(donors):
            for b, o in enumerate(acceptors):
                dno = np.linalg.norm(x[n] - x[o])
                if dno < d_cut:
                    v1, v2 = x[n] - x[h], x[o] - x[h]
                    cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                    if np.degrees(np.arccos(np.clip(cosang, -1, 1))) > angle_cut:
                        occ[a, b] += 1
    return occ / len(xyz)
