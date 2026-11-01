"""3D fibre-network mechanics: diluted face-centred-cubic lattice (validation of the 2D topo-opt study).

Conventions follow oxt/network.py exactly, lifted from 2D to 3D:

  lattice      periodic W x W x W FCC conventional cells, nearest-neighbour distance 1
               (conventional cell a = sqrt(2), box L = sqrt(2) W per axis, V = 2 sqrt(2) W^3).
               The 12 FCC neighbours are covered by 6 outgoing bond axes (+v and -v per axis),
               so every undirected edge appears exactly once: bond id = 6 * node + axis,
               Nb = 6 N with N = 4 W^3 nodes.  Full-lattice coordination z = 12 (3D central-force
               isostatic point: 6).
  stretching   0.5 * mu_b * (|d_b| - 1)^2                     per bond
  bending     0.5 * kappa_p * theta_p^2                      per pair of collinear bonds through a node
               (theta = angle between the incoming and outgoing bond vector, 0 when straight)
  rigid xlink 0.5 * kx * (cos(phi) - cos(phi_0))^2           per pair of bonds meeting at a locked
               junction, rest angle phi_0 taken from the perfect FCC geometry (60/90/120/180 deg)
  GAG tether  0.5 * k_gag * |x_i - F X_i|^2                  embedding / osmotic background

Equilibrium under a prescribed deformation gradient F (3x3) is found by batched torch float64
L-BFGS with periodic images (Lees-Edwards style: bond image offsets are carried by F).  Stress is
the first Piola stress P = (1/V) dE/dF.  Rupture removes bonds whose strain exceeds eps_r and
re-equilibrates (quasi-static cascade).  These are the same assumptions as the 2D model, so any
difference between the 2D and 3D conclusions is a dimensionality effect, not a model change.

Analytic check: the *undiluted* FCC lattice with central-force bonds only (kappa = 0, no locks,
no tether) is a Bravais lattice, so non-affine relaxation vanishes and the small-strain moduli
equal the Born (affine) values exactly:
  G  = mu / sqrt(2)          (simple shear F[0,1] = gamma)
  Cx = Cy = Cz = sqrt(2) mu  (laterally constrained uniaxial stretch)
per unit bond stiffness mu (see tests/test_network3d.py and run_network3d.py --validate).
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field, replace

import numpy as np
import torch

SQ2 = math.sqrt(2.0)
_trap = getattr(np, "trapezoid", None) or np.trapz  # numpy 2.x renamed trapz

# 6 FCC bond axes in conventional-cell units (bond vector = sqrt(2) * axis, length 1).
# Axes 0-3 contain an x component (used by the "aligned" architecture); 4-5 are transverse.
AXES = np.array([[0.5, 0.5, 0.0], [0.5, -0.5, 0.0], [0.5, 0.0, 0.5],
                 [0.5, 0.0, -0.5], [0.0, 0.5, 0.5], [0.0, 0.5, -0.5]])
BASIS = np.array([[0.0, 0.0, 0.0], [0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]])  # cell units
_FRAC_CODE = {0: 0, 3: 1, 5: 2, 6: 3}  # (frac_x,frac_y,frac_z) half-bit code -> basis type


class Lattice3D:
    """Periodic W^3 FCC lattice. Bond id = 6 * node + axis (outgoing along +AXES[axis])."""

    def __init__(self, W: int):
        if W < 2:
            raise ValueError("W must be >= 2")
        self.W, self.N = W, 4 * W ** 3
        self.L = np.full(3, SQ2 * W)
        self.volume = float(self.L.prod())  # 2 * sqrt(2) * W^3

        # node id n = ((k*W + j)*W + i)*4 + t  (cells ordered k slowest, i fastest)
        kk, jj, ii = np.meshgrid(np.arange(W), np.arange(W), np.arange(W), indexing="ij")
        cells = np.stack([ii.reshape(-1), jj.reshape(-1), kk.reshape(-1)], 1)  # (N/4, 3)
        cells = np.repeat(cells, 4, axis=0)                                  # (N, 3), type cycles fastest
        types = np.tile(np.arange(4), cells.shape[0] // 4)
        self.X = SQ2 * (cells + BASIS[types])

        nxt = np.zeros((self.N, 6), dtype=np.int64)
        shift = np.zeros((6 * self.N, 3))
        for ax in range(6):
            nb, sh = self._neighbors(cells, types, AXES[ax], W)
            nxt[:, ax] = nb
            shift[ax::6] = sh
        self.nxt = nxt
        prv = np.zeros_like(nxt)
        for a in range(self.N):
            for ax in range(6):
                prv[nxt[a, ax], ax] = a
        # optional curved-reference rest geometry (set by curve_lattice; identity here)
        self.rest_len = np.ones(6 * self.N)
        self.bend_theta0 = np.zeros(self.N * 6)
        self.curve_amp = 0.0
        self.bi = np.repeat(np.arange(self.N), 6)
        self.bj = nxt.reshape(-1)
        self.bdir = np.tile(np.arange(6), self.N)
        self.shift = shift  # reference-coordinate image offset per bond
        self.Nb = 6 * self.N

        # bending pairs: incoming bond along axis k into node a, outgoing bond along k out of a
        a = np.repeat(np.arange(self.N), 6)
        ax = np.tile(np.arange(6), self.N)
        self.bend_in = 6 * prv[a, ax] + ax
        self.bend_out = 6 * a + ax
        self.bend_node = a

        # spokes around each node: 6 outgoing (+1) and 6 incoming (-1) bonds; all 66 pairs,
        # rest cosine from the perfect-lattice geometry (junction locks).
        out_ids = 6 * np.arange(self.N)[:, None] + np.arange(6)[None, :]          # (N, 6)
        in_ids = 6 * prv + np.arange(6)[None, :]                                  # (N, 6)
        spokes = np.concatenate([out_ids, in_ids], axis=1)                        # (N, 12)
        signs = np.concatenate([np.ones(6), -np.ones(6)])
        n_hat = np.concatenate([AXES, AXES]) * SQ2  # reference unit vector of each spoke's bond
        ref = signs[:, None] * n_hat  # spoke reference direction (away from the node)
        iu, ju = np.triu_indices(12, k=1)  # 66 pairs
        self.ang_u = (spokes[:, iu]).reshape(-1)          # (66*N,) node-major
        self.ang_v = (spokes[:, ju]).reshape(-1)
        self.ang_su = np.tile(signs[iu], self.N)
        self.ang_sv = np.tile(signs[ju], self.N)
        self.ang_cos0 = np.tile((ref[iu] * ref[ju]).sum(1), self.N)
        self.ang_node = np.repeat(np.arange(self.N), 66)

        # fibre lines (walk along each axis; one bond per line is cut so fibres stay finite)
        self.line = -np.ones(self.Nb, dtype=np.int64)
        lid = 0
        for ax in range(6):
            for start in range(self.N):
                if self.line[6 * start + ax] >= 0:
                    continue
                n = start
                while self.line[6 * n + ax] < 0:
                    self.line[6 * n + ax] = lid
                    n = nxt[n, ax]
                lid += 1
        self.n_lines = lid

    @staticmethod
    def _neighbors(cells, types, delta, W):
        """Neighbour node id and bond image shift for one axis (delta in cell units)."""
        cc = cells + BASIS[types] + delta[None, :]
        ijk = np.floor(cc).astype(np.int64)
        frac = cc - ijk
        code = (4 * (frac[:, 0] > 0.25) + 2 * (frac[:, 1] > 0.25) + (frac[:, 2] > 0.25)).astype(np.int64)
        btype = np.array([_FRAC_CODE[int(c)] for c in code])
        ncell = ijk % W
        nb = ((ncell[:, 2] * W + ncell[:, 1]) * W + ncell[:, 0]) * 4 + btype
        shift = SQ2 * W * np.floor_divide(ijk, W)
        return nb, shift

    def crack_plane(self, axis: int = 0):
        """Bonds crossing the internal crack plane (axis-normal at L/2, in reference coords).

        Returns (crossing, sign): crossing (Nb,) bool, sign (Nb,) = +1 if the bond's imaged
        end lies on the +axis side.  An opening jump J across the plane adds sign * J to the
        bond's image offset; the conjugate traction is dE/dJ / A_plane."""
        pa = np.array([a for a in range(3) if a != axis])
        Pa = self.X[self.bi]
        Pb = self.X[self.bj] + self.shift
        # BUGFIX 2026-10-31: the plane must NOT sit at L/2.  FCC nodes sit at
        # x = k*sqrt(2)/2 and L/2 = W*sqrt(2)/2 is exactly one of those layers, so every
        # bond touching the midplane has an endpoint ON it and (da*db) < 0 found ZERO
        # crossing bonds (traction-separation returned T == 0 identically).  Place the
        # plane strictly inside the gap between node layers W-1 and W.
        c = 0.5 * self.L[axis] - SQ2 / 4.0
        da, db = Pa[:, axis] - c, Pb[:, axis] - c
        crossing = (da * db) < 0
        # crossing bonds straddle the plane: db > 0 iff da < 0, so sign(db) says which
        # side the imaged end is on; adding sign*J to the image offset opens the bond.
        sign = np.where(db > 0.0, 1.0, -1.0)
        mid = 0.5 * (Pa + Pb)
        in_plane = mid[:, pa] - 0.5 * self.L[pa]   # in-plane coords relative to the plane centre
        return crossing, sign, in_plane

    def plane_area(self, axis: int = 0):
        return float(np.prod([self.L[a] for a in range(3) if a != axis]))


def curve_lattice(lat: "Lattice3D", amp: float, rng) -> "Lattice3D":
    """Geometric CURVATURE axis: wave the reference geometry along every fibre line.

    Each fibre line (periodic walk along one bond axis) is displaced transversally by
    amp * sin(2*pi*s/n + phase) with one full period per periodic wrap, so the reference
    stays exactly periodic.  Displacements from the (up to 6) lines through a node are
    accumulated, then the whole field is rescaled so the MEAN node deflection equals
    amp.  Rest lengths, bending rest angles and lock rest cosines are recomputed from
    the curved reference, so the curved network is exactly stress-free at rest.

    Mutates and returns lat.  Sets lat.rest_len (Nb,) and lat.bend_theta0 (6N,);
    lat.ang_cos0 is recomputed in place.  Use the SAME curved lattice for every
    realization of a condition (the waviness is an architecture property; realization
    variability comes from the bond dilution), so Batch3D's shared-X design is intact.
    """
    if amp <= 0.0:
        return lat
    disp = np.zeros_like(lat.X)
    for line in range(lat.n_lines):
        members = np.flatnonzero(lat.line == line)
        if members.size < 3:
            continue
        nodes = lat.bi[members]                      # walk order along the line
        ax = int(lat.bdir[members[0]])
        u = AXES[ax] * SQ2                           # line direction (unit)
        v = rng.standard_normal(3)
        v -= u * (v @ u)                             # transverse
        n = np.linalg.norm(v)
        if n < 1e-12:
            continue
        v = v / n
        s = np.arange(len(nodes), dtype=float)
        w = np.sin(2.0 * np.pi * s / len(nodes) + rng.uniform(0, 2 * np.pi))
        disp[nodes] += amp * w[:, None] * v[None, :]
    m = float(np.linalg.norm(disp, axis=1).mean())
    if m <= 0:
        return lat
    disp *= amp / m
    lat.X = lat.X + disp

    # rest geometry from the curved reference
    d = lat.X[lat.bj] - lat.X[lat.bi] + lat.shift
    lat.rest_len = np.linalg.norm(d, axis=1)
    u_hat = d / lat.rest_len[:, None]

    # bending rest angles: angle between the incoming and outgoing bond vector of each
    # collinear pair at the curved reference (0 for the straight lattice).
    din, dout = d[lat.bend_in], d[lat.bend_out]
    lat.bend_theta0 = np.arctan2(np.linalg.norm(np.cross(din, dout), axis=1),
                                 (din * dout).sum(1))

    # lock rest cosines: recompute spoke reference directions from curved unit vectors
    N = lat.N
    prv = np.zeros((N, 6), dtype=np.int64)
    a = np.repeat(np.arange(N), 6)
    ax = np.tile(np.arange(6), N)
    prv[lat.nxt[a, ax], ax] = a
    out_ids = 6 * np.arange(N)[:, None] + np.arange(6)[None, :]
    in_ids = 6 * prv + np.arange(6)[None, :]
    spokes = np.concatenate([out_ids, in_ids], axis=1)              # (N, 12)
    signs = np.concatenate([np.ones(6), -np.ones(6)])
    ref = signs[None, :, None] * u_hat[spokes]                      # unit, away from node
    iu, ju = np.triu_indices(12, k=1)
    lat.ang_cos0 = (ref[:, iu] * ref[:, ju]).sum(-1).reshape(-1)    # (66N,) node-major
    lat.curve_amp = float(amp)
    return lat


@dataclass
class SystemSpec3D:
    """Per-system bond-level parameters (numpy; lengths Nb / N as in oxt.network.SystemSpec)."""
    alive: np.ndarray
    mu: np.ndarray
    kappa_b: np.ndarray        # per-bond bending factor; pair kappa = kappa * sqrt(f_in f_out)
    eps_r: np.ndarray
    rigid_node: np.ndarray     # length N, junction-lock angular stiffness
    kappa: float
    mu_el: float
    k_gag: float
    prestrain: float = 0.0
    meta: dict = field(default_factory=dict)


@dataclass
class Design3D:
    """Architecture of one 3D network realisation (the topo-opt design space, translated).

    arch:
      uniform         constant retention probability (isotropic baseline, no locks)
      random          uncorrelated zero-mean random retention field (no directional bias)
      aligned         x-rich retention (axes 0-3 favoured); p_along / p_transverse = 2 at
                      amp = 0.5, matching the 2D winner's survival-probability ratio
                      (topo_opt #99: pattern=aligned, amp=0.5)
      aligned_nolock  the same aligned field without junction locks (ablation)
    lock: fraction of nodes locked at kx (2D winner: 0.08 at crossings/highest degree);
          lock_place "crossings" = clustered at high-degree nodes, "random" = spatially uniform.
    elastin: fraction of mu added on EVERY lattice bond as a permanent (never-rupturing)
          elastin background (oxt/network.py convention: mu_el term).
    age:   AGE-like damage dose 0..1 (oxt/materials.Damage conventions, simplified):
          rupture strain eps_r *= (1 - 0.45*age) and lock fraction += 0.25*age.
    notch: pre-crack ahead of the crack plane (fracture pipeline): notch_shape
          "none" | "circle" | "slab", notch_frac = crack size relative to the box (0..1),
          crack_axis = normal of the crack plane (0 = plane x = L/2).
    """
    z: float = 3.4
    arch: str = "uniform"
    amp: float = 0.5
    family: str = "diluted"        # diluted (finite fibres, one cut per line) | phantom
                                   # (phantomized: pure random bond removal, node positions
                                   #  preserved, fibres run through junctions, no line cuts)
    lock: float = 0.0
    lock_place: str = "crossings"   # crossings (clustered) | random (uniform)
    cut_lines: bool = True
    node_prune: float = 0.0        # optional extra node dilution before bond dilution
    mu: float = 1.0                 # Col I (oxt/materials.py)
    kappa: float = 3e-3
    eps_r: float = 0.10
    kx: float = 2e-3                # KX_LOX, as run_phase.py / topo_opt.py
    k_gag: float = 1e-6
    prestrain: float = 0.0
    elastin: float = 0.0
    age: float = 0.0
    notch_shape: str = "none"
    notch_frac: float = 0.0
    crack_axis: int = 0
    lock_fail_rad: float = 0.5     # irreversible crosslink failure: angle deviation (rad)


ARCHS = ["uniform", "random", "aligned", "aligned_nolock"]


def arch_field(arch: str, lat: Lattice3D, rng) -> np.ndarray:
    """Zero-mean retention field on bonds; keep probability p = clip(p0 * (1 + amp * f), 0, 1)."""
    if arch == "uniform":
        return np.zeros(lat.Nb)
    if arch in ("aligned", "aligned_nolock"):
        fa = np.where(np.arange(6) < 4, 0.4, -0.8)  # mean zero; ratio (1+.4a)/(1-.8a) = 2 at a=.5
        return fa[lat.bdir]
    if arch == "random":
        s = rng.standard_normal(lat.Nb)
        return (s - s.mean()) / (s.std() + 1e-12)
    raise ValueError(f"unknown arch {arch}")


def build_network3d(lat: Lattice3D, d: Design3D, rng) -> tuple[SystemSpec3D, dict]:
    """One realisation of a diluted FCC network with the requested architecture."""
    N, Nb = lat.N, lat.Nb
    active = np.ones(N, bool)
    if d.node_prune > 0:
        active = rng.random(N) >= d.node_prune
    m = active[lat.bi] & active[lat.bj]
    n_act = int(active.sum())

    f = arch_field(d.arch, lat, rng)
    if d.family == "phantom":
        warnings.warn("Legacy family='phantom' is an uncut FCC dilution ablation; use architecture3d.phantom_fcc for validated binary-junction phantomization",RuntimeWarning,stacklevel=2)
        # phantomized FCC: pure random bond removal with node positions preserved and NO
        # one-cut-per-fibre-line rule - fibres run through junctions (phantom crossings).
        f = np.zeros(Nb)
    cut_lines = d.cut_lines and d.family != "phantom"
    # expected alive bonds = 6 n_act p (1 - 1/(2W)) after the one-cut-per-fibre-line rule
    if cut_lines:
        p_bar = d.z / (12.0 * (1.0 - 1.0 / (2.0 * lat.W)))
    else:
        p_bar = d.z / 12.0   # no line cuts (phantom): every retained bond counts
    target = p_bar * m.sum()
    lo, hi = 0.0, 5.0
    p0 = 0.5 * (lo + hi)
    for _ in range(60):  # bisection on p0 so the expected alive-bond count hits the target z
        p0 = 0.5 * (lo + hi)
        if np.clip(p0 * (1 + d.amp * f), 0, 1)[m].sum() < target:
            lo = p0
        else:
            hi = p0
    p = np.clip(p0 * (1 + d.amp * f), 0, 1)
    alive = (rng.random(Nb) < p) & m
    if cut_lines:  # finite fibres: one cut per line (same rule as topo_opt.build_design)
        for line in range(lat.n_lines):
            members = np.flatnonzero(lat.line == line)
            if members.size:
                alive[rng.choice(members)] = False

    # pre-crack / notch ahead of the crack plane (fracture pipeline): remove alive bonds
    # crossing the plane inside the crack region (circle of radius notch_frac*L/2 in the
    # plane, or a slab band), so the remaining ligament transmits traction.
    n_notch = 0
    if d.notch_shape != "none" and d.notch_frac > 0:
        crossing, _sign, q = lat.crack_plane(d.crack_axis)
        if d.notch_shape == "circle":
            r = d.notch_frac * 0.5 * float(np.min(lat.L))
            inside = (q ** 2).sum(1) < r ** 2
        elif d.notch_shape == "slab":
            inside = np.abs(q[:, 0]) < d.notch_frac * 0.5 * float(np.min(lat.L))
        else:
            raise ValueError(f"unknown notch_shape {d.notch_shape}")
        cut = crossing & inside
        n_notch = int((alive & cut).sum())
        alive = alive & ~cut

    deg = np.bincount(lat.bi[alive], minlength=N) + np.bincount(lat.bj[alive], minlength=N)
    lock_eff = min(1.0, d.lock + 0.25 * d.age)  # AGE-like extra junction locks at dose d.age
    rigid = np.zeros(N)
    cand = np.flatnonzero(active & (deg >= 2))
    n_lock = min(int(round(lock_eff * n_act)), cand.size)
    if n_lock:
        tie = rng.random(cand.size)
        key = tie if d.lock_place == "random" else -deg[cand] + 0.5 * tie
        rigid[cand[np.argsort(key)[:n_lock]]] = d.kx

    eps_r_eff = d.eps_r * (1.0 - 0.45 * d.age)  # AGE-like embrittlement (materials.Damage.brittle)
    spec = SystemSpec3D(alive=alive, mu=np.full(Nb, d.mu), kappa_b=np.ones(Nb),
                        eps_r=np.full(Nb, eps_r_eff), rigid_node=rigid, kappa=d.kappa,
                        mu_el=d.elastin * d.mu, k_gag=d.k_gag, prestrain=d.prestrain,
                        meta=dict(arch=d.arch, z=d.z, amp=d.amp, lock=d.lock, lock_eff=lock_eff,
                                  elastin=d.elastin, age=d.age, eps_r=eps_r_eff,
                                  notch_shape=d.notch_shape, notch_frac=d.notch_frac,
                                  crack_axis=d.crack_axis, lock_fail_rad=d.lock_fail_rad))
    info = dict(z_realized=2.0 * alive.sum() / max(n_act, 1),
                z_active=2.0 * alive.sum() / max(int((deg > 0).sum()), 1),
                n_alive=int(alive.sum()), n_act=n_act, n_lock=int(n_lock), n_notch=n_notch,
                p0=p0, deg_active=float(deg[deg > 0].mean()) if (deg > 0).any() else 0.0)
    return spec, info


def scale_stiffness(spec: SystemSpec3D, s: float) -> SystemSpec3D:
    """Multiply every stiffness (mu, kappa, kx, k_gag) by s.  The energy is linear in all of
    them, so the equilibrium configuration is unchanged and the moduli scale exactly by s;
    eps_r is strain-based and therefore untouched.  Used by the matched-bulk-stiffness control."""
    if not np.isfinite(s) or s <= 0:
        raise ValueError("stiffness scale must be finite and positive")
    return replace(spec, mu=spec.mu * s, rigid_node=spec.rigid_node * s,
                   kappa=spec.kappa * s, mu_el=spec.mu_el * s, k_gag=spec.k_gag * s)


def matched_stiffness_scale(initial, target, relative_floor=1e-8, max_scale=1e4):
    """Public compatibility wrapper around the shared fail-closed E2 guard."""
    from .normalization import matched_stiffness_scale as checked_scale
    return checked_scale(initial, target, relative_floor, max_scale)


def squared_bend(din, dout, rest):
    """Unsigned harmonic bend with a differentiable straight-state Hessian.

    theta^2 = 2t + t^2/3 + 4t^3/45 + O(t^4), t=1-cos(theta).
    Compute t as half the squared unit-vector difference to avoid cancellation.
    Curved rest hinges retain their original unsigned harmonic law.
    """
    u = din / torch.linalg.vector_norm(din, dim=-1, keepdim=True).clamp_min(1e-12)
    v = dout / torch.linalg.vector_norm(dout, dim=-1, keepdim=True).clamp_min(1e-12)
    t = 0.5 * ((u-v)**2).sum(-1)
    # Clamp only the unused acos branch near the smooth straight limit.
    theta = torch.acos((1-t).clamp(-1+1e-12, 1-1e-7))
    sq = torch.where(t < 1e-5, 2*t+t*t/3+4*t*t*t/45, theta*theta)
    curved = (torch.sqrt(sq.clamp_min(1e-30))-rest)**2
    return torch.where(rest == 0, sq, curved)


def coordination3d(spec: SystemSpec3D, lat: Lattice3D) -> float:
    return 2.0 * spec.alive.sum() / lat.N


class Batch3D:
    """Stack of systems on one FCC lattice, evaluated together on one device.

    crack_axis: enable the internal crack plane (fracture pipeline) - bonds crossing the
      plane carry the applied opening jump J (traction-separation boundary condition), and
      the conjugate traction T = dE/dJ / A_plane is the cohesive traction.
    relax_kw: default L-BFGS budget (max_rounds / iters / ftol), overridable per call.
    """

    def __init__(self, lat: Lattice3D, specs: list[SystemSpec3D], device="cpu",
                 dtype=torch.float64, crack_axis: int | None = None, relax_kw: dict | None = None):
        self.lat, self.specs, self.B = lat, specs, len(specs)
        t = lambda a: torch.as_tensor(np.asarray(a), device=device, dtype=dtype)
        ti = lambda a: torch.as_tensor(np.asarray(a), device=device, dtype=torch.long)
        self.device, self.dtype = device, dtype
        self.relax_kw = dict(relax_kw or {})
        self.X = t(lat.X)
        self.shift = t(lat.shift)
        self.bi, self.bj = ti(lat.bi), ti(lat.bj)
        self.bend_in, self.bend_out = ti(lat.bend_in), ti(lat.bend_out)
        self.ang_u, self.ang_v = ti(lat.ang_u), ti(lat.ang_v)
        self.ang_su, self.ang_sv = t(lat.ang_su), t(lat.ang_sv)
        self.ang_cos0 = t(lat.ang_cos0)
        self.rest_len = t(lat.rest_len)
        self.bend_theta0 = t(lat.bend_theta0)
        self.ang_node = ti(lat.ang_node)
        self.alive = torch.as_tensor(np.stack([s.alive for s in specs]), device=device)
        self.mu = t(np.stack([s.mu for s in specs]))
        self.kb = t(np.stack([s.kappa_b for s in specs]))
        self.eps_r = t(np.stack([s.eps_r for s in specs]))
        self.kappa = t([s.kappa for s in specs])[:, None]
        self.kx = t(np.stack([s.rigid_node for s in specs]))
        self.mu_el = t([s.mu_el for s in specs])[:, None]
        self.k_gag = t([s.k_gag for s in specs])[:, None, None]
        self.pre = t([s.prestrain for s in specs])
        # irreversible crosslink (junction-lock pair) failure state: lock pairs only ever die
        self.lock_alive = ((self.kx[:, self.ang_node] > 0) & self.alive[:, self.ang_u] & self.alive[:, self.ang_v]).clone()
        self.lock_fail_rad = t([s.meta.get("lock_fail_rad", 0.5) for s in specs])[:, None]
        # crack plane (None = no internal crack / no applied opening)
        self.crack_axis = crack_axis
        if crack_axis is None:
            self.plane_w = None
            self.A_plane = None
        else:
            crossing, sign, _q = lat.crack_plane(crack_axis)
            self.plane_w = t(np.where(crossing, sign, 0.0))
            self.A_plane = lat.plane_area(crack_axis)
        eye = torch.eye(3, device=device, dtype=dtype)
        self.F0 = eye.expand(self.B, 3, 3) * (1 + self.pre)[:, None, None]
        self.x = (self.X[None] @ self.F0.transpose(1, 2)).clone()

    # ---- energy -----------------------------------------------------------------------
    def bond_vectors(self, x, F, jump=None):
        if jump is not None and self.plane_w is None:
            raise ValueError("jump given but Batch3D was built without crack_axis")
        img = torch.einsum("bij,nj->bni", F, self.shift)
        if jump is not None:
            img = img + self.plane_w[None, :, None] * jump[:, None, :]
        return x[:, self.bj] - x[:, self.bi] + img

    def energy(self, x, F, jump=None, per_system=False):
        d = self.bond_vectors(x, F, jump)
        ln = torch.linalg.norm(d, dim=-1)
        a = self.alive.to(self.dtype)
        if bool(((ln < 1e-10) & self.alive).any()):
            raise ValueError("collapsed active fibre segment")
        mu_eff = self.mu * a + self.mu_el
        e = 0.5 * (mu_eff * (ln - self.rest_len) ** 2).sum(1)

        din, dout = d[:, self.bend_in], d[:, self.bend_out]
        bend_sq = squared_bend(din, dout, self.bend_theta0)
        kp = self.kappa * torch.sqrt(self.kb[:, self.bend_in] * self.kb[:, self.bend_out]) \
            * a[:, self.bend_in] * a[:, self.bend_out]
        aligned_cos = (din*dout).sum(-1) / (torch.linalg.vector_norm(din,dim=-1)*torch.linalg.vector_norm(dout,dim=-1)).clamp_min(1e-24)
        if bool(((aligned_cos <= -1+1e-12)&(kp>0)).any()):
            raise ValueError("undefined antiparallel active bending hinge")
        e = e + 0.5 * (kp * bend_sq).sum(1)

        u = d[:, self.ang_u] * self.ang_su[None, :, None]
        v = d[:, self.ang_v] * self.ang_sv[None, :, None]
        cos = (u * v).sum(-1) / torch.clamp(ln[:, self.ang_u] * ln[:, self.ang_v], min=1e-9)
        kq = self.kx[:, self.ang_node] * a[:, self.ang_u] * a[:, self.ang_v] \
            * self.lock_alive.to(self.dtype)
        e = e + 0.5 * (kq * (cos - self.ang_cos0[None, :]) ** 2).sum(1)

        xa = self.X[None] @ F.transpose(1, 2)
        e = e + 0.5 * (self.k_gag * (x - xa) ** 2).sum((1, 2))
        return e if per_system else e.sum()

    # ---- equilibrium -------------------------------------------------------------------
    def relax(self, F, jump=None, ftol=1e-7, max_rounds=40, iters=300):
        # same schedule as oxt.network.Batch.relax: force criterion AND energy-settling
        # (sub-isostatic networks have tiny forces long before they are relaxed)
        ftol = self.relax_kw.get("ftol", ftol)
        max_rounds = self.relax_kw.get("max_rounds", max_rounds)
        iters = self.relax_kw.get("iters", iters)
        strict = self.relax_kw.get("strict", True)
        x = self.x.detach().clone().requires_grad_(True)
        opt = torch.optim.LBFGS([x], lr=1., max_iter=iters, history_size=50,
                                tolerance_grad=ftol * .1, tolerance_change=1e-18,
                                line_search_fn="strong_wolfe")
        def closure():
            opt.zero_grad()
            en = self.energy(x, F, jump)
            if not torch.isfinite(en):
                raise FloatingPointError("nonfinite network energy")
            en.backward()
            return en
        previous = self.energy(x, F, jump, per_system=True).detach()
        accepted = torch.zeros(self.B, dtype=torch.bool, device=self.device)
        for round_index in range(max_rounds):
            opt.step(closure)
            en = self.energy(x, F, jump, per_system=True)
            (grad,) = torch.autograd.grad(en.sum(), x)
            forces = grad.detach().abs().reshape(self.B, -1).max(1).values
            change = (en.detach()-previous).abs()
            accepted = (forces <= ftol) & (change <= 1e-10*en.detach().abs()+1e-16)
            if bool(accepted.all()):
                break
            previous = en.detach()
            if round_index >= 5 and self.B*self.lat.N <= 512:
                break  # use a local Newton polish rather than tiny L-BFGS steps
        polish_steps = 0
        if not bool(accepted.all()) and self.B*self.lat.N <= 512:
            # Optimizer preconditioning only: no change to the physical energy.
            for polish_steps in range(1, self.relax_kw.get("newton_steps",32)+1):
                e_before = self.energy(x,F,jump,per_system=True).detach()
                for specimen in range(self.B):
                    # Full batched Hessian includes independent specimen blocks.
                    flat = x.detach().reshape(-1)
                    def objective(z):
                        return self.energy(z.reshape_as(x),F,jump)
                    hess = torch.autograd.functional.hessian(objective,flat,vectorize=True)
                    grad = torch.autograd.functional.jacobian(objective,flat)
                    diagonal = max(float(hess.abs().max()),1e-30)
                    eye = torch.eye(flat.numel(),dtype=self.dtype,device=self.device)
                    direction = None
                    for exponent in range(8):
                        factor,info = torch.linalg.cholesky_ex(hess+diagonal*1e-10*10**exponent*eye)
                        if int(info)==0:
                            direction = -torch.cholesky_solve(grad[:,None],factor).reshape(-1)
                            break
                    if direction is None:
                        direction = -grad / diagonal
                    descent = float(grad@direction)
                    current = float(objective(flat))
                    for backtrack in range(20):
                        alpha = .5**backtrack
                        candidate = flat+alpha*direction
                        trial = float(objective(candidate))
                        if np.isfinite(trial) and trial <= current+1e-4*alpha*descent:
                            with torch.no_grad():x.copy_(candidate.reshape_as(x))
                            break
                    break  # one joint solve updates every independent specimen block
                en = self.energy(x,F,jump,per_system=True)
                (grad_x,) = torch.autograd.grad(en.sum(),x)
                forces = grad_x.detach().abs().reshape(self.B,-1).max(1).values
                change = (en.detach()-e_before).abs()
                accepted = (forces<=ftol)&(change<=1e-10*en.detach().abs()+1e-16)
                if bool(accepted.all()):break
        self.x = x.detach()
        self.last_relax = dict(accepted=accepted.cpu().tolist(),
                              force_max=forces.cpu().tolist(),
                              energy_change=change.cpu().tolist(), rounds=round_index+1, newton_polish_steps=polish_steps)
        if strict and not bool(accepted.all()):
            raise RuntimeError("equilibrium did not converge: " + repr(self.last_relax))
        return float(forces.max())

    def stress(self, F, jump=None):
        Fv = F.detach().clone().requires_grad_(True)
        e = self.energy(self.x, Fv, jump)
        (g,) = torch.autograd.grad(e, Fv)
        return g / self.lat.volume  # (B, 3, 3) first Piola stress

    def traction(self, F, jump):
        """Cohesive traction across the crack plane: T = (1/A_plane) dE/dJ at equilibrium."""
        jv = jump.detach().clone().requires_grad_(True)
        e = self.energy(self.x, F, jv)
        (g,) = torch.autograd.grad(e, jv)
        return g / self.A_plane  # (B, 3)

    def move_affine(self, F_old, F_new):
        M = F_new @ torch.linalg.inv(F_old)
        self.x = self.x @ M.transpose(1, 2)

    def bond_strain(self, F, jump=None):
        d = self.bond_vectors(self.x, F, jump)
        return torch.linalg.norm(d, dim=-1) / self.rest_len - 1.0

    def bond_tension(self, F, jump=None):
        d = self.bond_vectors(self.x, F, jump)
        return self.mu * (torch.linalg.norm(d, dim=-1) - self.rest_len) * self.alive.to(self.dtype)

    def rupture(self, F, jump=None):
        """Break every alive fibre bond above its rupture strain. IRREVERSIBLE: alive is
        never restored, so the crack history is preserved across the whole protocol."""
        s = self.bond_strain(F, jump)
        brk = self.alive & (s > self.eps_r)
        self.alive = self.alive & ~brk
        return brk.sum(1)

    def lock_deviation(self, F, jump=None):
        """Angle deviation (rad) of every junction-lock pair from its rest angle."""
        d = self.bond_vectors(self.x, F, jump)
        ln = torch.linalg.norm(d, dim=-1)
        u = d[:, self.ang_u] * self.ang_su[None, :, None]
        v = d[:, self.ang_v] * self.ang_sv[None, :, None]
        cos = (u * v).sum(-1) / torch.clamp(ln[:, self.ang_u] * ln[:, self.ang_v], min=1e-9)
        cos0 = torch.clamp(self.ang_cos0[None, :], -1.0, 1.0)
        return torch.acos(torch.clamp(cos, -1.0, 1.0)) - torch.acos(cos0)

    def rupture_locks(self, F, jump=None):
        """Break lock pairs whose angle deviation exceeds the threshold. IRREVERSIBLE."""
        dev = self.lock_deviation(F, jump)
        brk = self.lock_alive & self.alive[:, self.ang_u] & self.alive[:, self.ang_v] & (dev.abs() > self.lock_fail_rad)
        self.lock_alive = self.lock_alive & ~brk
        return brk.sum(1)

    # ---- protocols ---------------------------------------------------------------------
    def assert_damage_stable(self,F,jump=None,include_locks=False):
        pending = self.alive & (self.bond_strain(F,jump)>self.eps_r)
        if include_locks:
            locks = self.lock_alive & self.alive[:,self.ang_u] & self.alive[:,self.ang_v] & (self.lock_deviation(F,jump).abs()>self.lock_fail_rad)
            extra = bool(locks.any())
        else:extra=False
        if bool(pending.any()) or extra:
            raise RuntimeError("damage cascade limit exhausted with unstable elements")

    def F_shear(self, g):
        F = self.F0.clone()
        F[:, 0, 1] += g * (1 + self.pre)
        return F

    def F_stretch(self, e, axis):
        F = self.F0.clone()
        F[:, axis, axis] *= (1 + e)
        return F

    def shear_curve(self, gammas):
        Fp = self.F0.clone()
        out = []
        self.relax(Fp)
        for g in gammas:
            F = self.F_shear(g)
            self.move_affine(Fp, F)
            self.relax(F)
            out.append(self.stress(F)[:, 0, 1].cpu().numpy())
            Fp = F
        return np.stack(out, 1)  # (B, n_gamma)

    def small_strain_moduli(self, eps=2e-3):
        """Linear shear modulus G and constrained uniaxial moduli Cx, Cy, Cz."""
        x0 = self.x.clone()
        self.relax(self.F0)
        xr = self.x.clone()
        base = self.stress(self.F0)
        res = {}
        for name, F in [("G", self.F_shear(eps)), ("Cx", self.F_stretch(eps, 0)),
                        ("Cy", self.F_stretch(eps, 1)), ("Cz", self.F_stretch(eps, 2))]:
            self.x = xr.clone()
            self.move_affine(self.F0, F)
            self.relax(F)
            P = self.stress(F)
            if name == "G":
                res[name] = ((P[:, 0, 1] - base[:, 0, 1]) / (eps * (1 + self.pre))).cpu().numpy()
            else:
                ax = {"Cx": 0, "Cy": 1, "Cz": 2}[name]
                res[name] = ((P[:, ax, ax] - base[:, ax, ax]) / (eps * (1 + self.pre))).cpu().numpy()
        self.x = x0
        return res

    def failure_curve(self, strains, axis=0, max_cascade=8):
        """Quasi-static laterally-constrained uniaxial pull with bond rupture.

        Returns per-system: stress curve, broken-bond curve, first-rupture strain, index of
        peak stress and the per-bond tension field at the peak step (stress concentrations)."""
        Fp = self.F0.clone()
        self.relax(Fp)
        sig, broken, first = [], [], np.full(self.B, np.nan)
        t_peak = torch.zeros(self.B, self.lat.Nb, device=self.device, dtype=self.dtype)
        i_peak = np.zeros(self.B, dtype=np.int64)
        s_peak = np.full(self.B, -np.inf)
        for n, e in enumerate(strains):
            F = self.F_stretch(e, axis)
            self.move_affine(Fp, F)
            self.relax(F)
            nb = torch.zeros(self.B, dtype=torch.long, device=self.device)
            for _ in range(max_cascade):
                k = self.rupture(F)
                nb += k
                if int(k.sum()) == 0:
                    break
                self.relax(F)
            self.assert_damage_stable(F)
            s = self.stress(F)[:, axis, axis].cpu().numpy()
            broke_now = (nb > 0).cpu().numpy() & np.isnan(first)
            first[broke_now] = e
            better = s > s_peak
            i_peak = np.where(better, n, i_peak)
            s_peak = np.where(better, s, s_peak)
            with torch.no_grad():
                tp = self.bond_tension(F)
                t_peak = torch.where(torch.as_tensor(better, device=self.device)[:, None],
                                     tp, t_peak)
            sig.append(s)
            broken.append(nb.cpu().numpy())
            Fp = F
        return dict(sig=np.stack(sig, 1), broken=np.stack(broken, 1), first=first,
                    i_peak=i_peak, t_peak=t_peak.cpu().numpy())

    def cyclic(self, eps_max, n_cycles, steps, axis=0, max_cascade=8):
        """Repeated loading/unloading to eps_max with rupture: stress softening, hysteresis
        (energy dissipated per cycle), cumulative damage and residual stress (relaxation
        of the stress-free state under repeated loading, quasi-static)."""
        Fp = self.F0.clone()
        self.relax(Fp)
        eps = np.linspace(0.0, eps_max, steps + 1)[1:]
        out = {k: [] for k in ("peak", "w_load", "w_unload", "diss", "broken", "residual")}
        for _ in range(n_cycles):
            s_load = [self.stress(Fp)[:, axis, axis].cpu().numpy()]
            nb = np.zeros(self.B, dtype=np.int64)
            for e in eps:
                F = self.F_stretch(e, axis)
                self.move_affine(Fp, F)
                self.relax(F)
                for _ in range(max_cascade):
                    k = self.rupture(F)
                    nb += k.cpu().numpy()
                    if int(k.sum()) == 0:
                        break
                    self.relax(F)
                self.assert_damage_stable(F)
                s_load.append(self.stress(F)[:, axis, axis].cpu().numpy())
                Fp = F
            w_load = _trap(np.stack(s_load, 1), np.concatenate([[0.0], eps]), axis=1)
            out["peak"].append(np.max(np.stack(s_load,1),axis=1))
            out["w_load"].append(w_load)
            s_un = [s_load[-1]]
            for e in eps[-2::-1]:
                F = self.F_stretch(e, axis)
                self.move_affine(Fp, F)
                self.relax(F)
                for _ in range(max_cascade):
                    k = self.rupture(F)
                    nb += k.cpu().numpy()
                    if int(k.sum()) == 0:
                        break
                    self.relax(F)
                self.assert_damage_stable(F)
                s_un.append(self.stress(F)[:, axis, axis].cpu().numpy())
                Fp = F
            F = self.F_stretch(0.0, axis)
            self.move_affine(Fp, F)
            self.relax(F)
            for _ in range(max_cascade):
                k = self.rupture(F)
                nb += k.cpu().numpy()
                if int(k.sum()) == 0:
                    break
                self.relax(F)
            self.assert_damage_stable(F)
            s_un.append(self.stress(F)[:, axis, axis].cpu().numpy())
            Fp = F
            ee = np.concatenate([eps[::-1], [0.0]])
            w_unload = _trap(np.stack(s_un, 1), ee, axis=1)
            out["w_unload"].append(w_unload)
            out["diss"].append(w_load + w_unload)
            out["broken"].append(nb)
            out["residual"].append(s_un[-1])
        return {k: np.stack(v, 1) for k, v in out.items()}  # each (B, n_cycles)

    def cohesive_curve(self, deltas, mode="tension", mix=1.0, max_cascade=8):
        """Traction-separation across the crack plane (fracture pipeline).

        Applies a monotonically increasing opening jump J(delta) across the plane - tension
        (normal), shear (tangential) or mixed mode (normal delta plus mix*delta tangential) -
        relaxing to equilibrium at each step with IRREVERSIBLE fibre-bond and crosslink (lock
        rupture.  Returns per system: the traction vector T(delta) = dE/dJ / A_plane, the
        effective traction conjugate to delta, cumulative broken bonds / lock pairs, the
        first-rupture opening, peak traction and the per-bond tension field at peak traction.
        """
        if self.plane_w is None or self.crack_axis is None:
            raise ValueError("cohesive_curve needs Batch3D(..., crack_axis=...)")
        ax = self.crack_axis
        tan = (ax + 1) % 3  # first tangential direction in the plane
        dj = {"tension": (1.0, 0.0), "shear": (0.0, 1.0), "mixed": (1.0, mix)}[mode]
        F = self.F0.clone()
        jump0 = torch.zeros(self.B, 3, device=self.device, dtype=self.dtype)
        self.relax(F, jump=jump0)
        T, Teff, broken, locks, first = [], [], [], [], np.full(self.B, np.nan)
        t_peak = np.full(self.B, -np.inf)
        tp_snap = torch.zeros(self.B, self.lat.Nb, device=self.device, dtype=self.dtype)
        for dl in deltas:
            j = jump0.clone()
            j[:, ax] += dl * dj[0]
            j[:, tan] += dl * dj[1]
            self.relax(F, jump=j)
            nb = torch.zeros(self.B, dtype=torch.long, device=self.device)
            nl = torch.zeros(self.B, dtype=torch.long, device=self.device)
            for _ in range(max_cascade):
                k = self.rupture(F, jump=j)
                nb += k
                k2 = self.rupture_locks(F, jump=j)
                nl += k2
                if int(k.sum()) + int(k2.sum()) == 0:
                    break
                self.relax(F, jump=j)
            self.assert_damage_stable(F,jump=j,include_locks=True)
            tr = self.traction(F, j).cpu().numpy()          # (B, 3)
            teff = tr[:, ax] * dj[0] + tr[:, tan] * dj[1]    # dE/ddelta / A_plane
            broke_now = ((nb + nl) > 0).cpu().numpy() & np.isnan(first)
            first[broke_now] = dl
            T.append(tr)
            Teff.append(teff)
            broken.append(nb.cpu().numpy())
            locks.append(nl.cpu().numpy())
            better = teff > t_peak
            t_peak = np.where(better, teff, t_peak)
            with torch.no_grad():
                tp = self.bond_tension(F, jump=j)
                tp_snap = torch.where(torch.as_tensor(better, device=self.device)[:, None],
                                     tp, tp_snap)
        return dict(deltas=np.asarray(deltas, float), T=np.stack(T, 1), Teff=np.stack(Teff, 1),
                    broken=np.stack(broken, 1), locks_broken=np.stack(locks, 1),
                    first=first, t_peak=t_peak, t_peak_field=tp_snap.cpu().numpy())


def stress_concentration(t: np.ndarray) -> dict:
    """Spatial stress-concentration metrics from a per-bond tension field (participation/maxShare).

    max_share      max |t| / mean |t| over alive bonds (1 = perfectly shared)
    participation  (sum |t|)^2 / (n * sum t^2): 1 = uniform load sharing, -> 0 = concentrated
    p80            smallest fraction of alive bonds carrying 80% of the total |t|
    """
    a = np.abs(t[t != 0])
    if a.size == 0 or a.sum() == 0:
        return dict(max_share=np.nan, participation=np.nan, p80=np.nan)
    srt = np.sort(a)[::-1]
    cum = np.cumsum(srt) / a.sum()
    return dict(max_share=float(a.max() / a.mean()),
                participation=float(a.sum() ** 2 / (a.size * (a ** 2).sum())),
                p80=float((np.searchsorted(cum, 0.8) + 1) / a.size))


def hessian_moduli(lat, spec, device="cpu", dtype=torch.float64):
    """Relaxed first-Piola tangent by a joint displacement/F Hessian.

    All nine F components are included. The Schur complement eliminates
    nonaffine node motion. A scale-covariant numerical gauge floor is reported;
    its effect must be negligible relative to resolved moduli.
    """
    batch = Batch3D(lat, [spec], device=device, dtype=dtype)
    batch.relax(batch.F0)
    N = lat.N
    x0 = batch.x.detach()
    F0 = batch.F0.detach()
    z0 = torch.zeros(3*N+9, dtype=dtype, device=device)
    def energy_joint(z):
        deltaF = z[3*N:].reshape(1,3,3)
        x = x0 + z[:3*N].reshape(1,N,3) + batch.X[None] @ deltaF.transpose(1,2)
        return batch.energy(x, F0+deltaF)
    joint = torch.autograd.functional.hessian(energy_joint,z0,vectorize=True).detach().cpu().numpy()
    H = (joint[:3*N,:3*N]+joint[:3*N,:3*N].T)*.5
    mixed = joint[:3*N,3*N:]
    regularizer = 1e-12*max(float(np.max(np.abs(H))),1e-30)
    solve = np.linalg.solve(H+regularizer*np.eye(3*N),mixed)
    C = (joint[3*N:,3*N:] - mixed.T@solve)/lat.volume
    C = (C+C.T)*.5
    return dict(G=float(C[1,1]),Cx=float(C[0,0]),Cy=float(C[4,4]),Cz=float(C[8,8]),
                tangent9=C.tolist(),regularizer=regularizer,
                linear_solve_residual=float(np.max(np.abs((H+regularizer*np.eye(3*N))@solve-mixed))))


@dataclass
class Calibration3D:
    """Physical calibration of the dimensionless model (PLACEHOLDERS - see DESIGN.md).

    The model is dimensionless: bond length 1, fibre stiffness mu = 1, stress in mu / bond^2.
    To convert fracture output to SI:
      traction [Pa]  = T_model * force_scale / length_scale**2
      G_c [J/m^2]    = Gc_model * force_scale / length_scale
      stress [Pa]    = P_model * force_scale / length_scale**2
    thickness is 1 by construction in 3D (kept for the 2D consumer's plane-stress needs).

    Required calibration (not done here): length_scale = bond length l0 [m] of one collagen
    fibre segment between junctions (fit to fibril/network mesh size, e.g. SEM/pore data);
    force_scale = mu_SI * l0 [N] where mu_SI [N/m] is the fibre stretch stiffness per segment
    (from oxt/materials.py Col I parameters mapped to physical units via the repo's
    S_pa calibration); thickness = out-of-plane thickness of the tissue slice [m] for 2D
    consumers (1.0 for the 3D network itself).
    """
    length_scale: float = 1.0   # [m] per bond-length unit
    force_scale: float = 1.0    # [N] per model force unit (mu * length_scale)
    thickness: float = 1.0      # [m], informational for 2D consumers


def traction_si(T_model: float, cal: Calibration3D) -> float:
    return T_model * cal.force_scale / cal.length_scale ** 2


def gc_si(Gc_model: float, cal: Calibration3D) -> float:
    return Gc_model * cal.force_scale / cal.length_scale
