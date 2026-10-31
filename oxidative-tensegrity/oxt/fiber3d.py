"""Stochastic 3D fibre-network generator + solver (third architecture family).

The other two families (oxt/network3d.py) are FCC-based: `diluted` (random bond dilution +
one cut per fibre line -> finite fibres) and `phantom` (pure random bond removal, fibres
run through junctions).  This module grows networks the way collagen is actually laid
down: N_fib independent fibres, each a persistent random walk of unit segments with a
tunable initial orientation bias, cross-linked wherever two fibres pass within a search
radius.  No lattice is involved - the reference geometry is the as-grown node cloud in a
periodic box - so this family probes whether the FCC-based conclusions survive a fully
stochastic architecture.

Constitutive laws are IDENTICAL to oxt/network3d.py (same model, same units):
  stretching   0.5 * mu * (|d| - rest_len)^2          per fibre segment / crosslink
  bending      0.5 * kappa * (theta - theta_ref)^2    per pair of consecutive segments of
               one fibre (theta_ref = rest angle in the as-grown geometry, so a curved
               as-grown fibre is stress-free)
  rigid xlink  0.5 * kx * (cos(phi) - cos(phi_ref))^2  per pair of bonds meeting at a
               locked node (rest angle from the as-grown geometry)
  GAG tether  0.5 * k_gag * |x_i - F X_i|^2           embedding background

Matching to the FCC families (the architecture-atlas contract): same box volume
V = 2*sqrt(2)*W^3, same node count N = 4*W^3, same chemistry (mu, kappa, kx, eps_r,
k_gag from oxt/materials.py Col I), same target connectivity z.  Realized mismatches
(node count, bond density, fibre-length density, z) are REPORTED, not tuned away.

Solver: batched torch float64 L-BFGS (Batch3D-style) over a padded bond/pair index
stack - realizations of one condition are evaluated together on one device.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

MODE_MAP = {"tension": "I", "shear": "II", "mixed": "I+II-mixed"}


@dataclass
class FiberDesign:
    """One stochastic-fibre architecture condition."""
    n_fib: int = 32
    n_seg: int = 8                 # segments per (periodic ring) fibre
    p_align: float = 0.0           # orientation bias toward x: 0 isotropic ... 0.7 strong
    curve_sigma: float = 0.0       # geometric curvature: per-segment direction noise
    z: float = 3.4                 # target mean coordination (chain contributes 2)
    lock: float = 0.08             # fraction of nodes with junction locks
    lock_place: str = "crossings"  # crossings (crosslinked nodes first) | random
    xlink_dist: str = "random"     # random (uniform) | clustered (hotspot-rich-get-richer)
    mu: float = 1.0
    kappa: float = 3e-3
    kx: float = 2e-3
    eps_r: float = 0.10
    k_gag: float = 1e-6
    notch_shape: str = "none"       # none | circle (pre-crack ahead of the crack plane)
    notch_frac: float = 0.0
    crack_axis: int = 0
    lock_fail_rad: float = 0.5


def _unit(v):
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("zero direction")
    return v / n


def build_fiber_network(d: FiberDesign, rng, box_L: float, n_target: int) -> dict:
    """Grow one realization.  Returns a dict with geometry, bonds, pair lists and a
    matching report against the FCC reference (same V, same N, same z target).

    Fibres are OPEN persistent random walks of n_seg unit segments (n_seg+1 nodes,
    free ends - collagen networks have dangling fibre ends), so every chain bond has
    rest length exactly 1 and the reference state is stress-free by construction."""
    N = d.n_fib * (d.n_seg + 1)
    n_chain = d.n_fib * d.n_seg
    L = float(box_L)
    X = np.zeros((N, 3))
    fiber_of = np.repeat(np.arange(d.n_fib), d.n_seg + 1)
    seg_dir = np.zeros((d.n_fib, d.n_seg, 3))
    for f in range(d.n_fib):
        start = rng.uniform(0.0, L, 3)
        v = _unit(d.p_align * np.array([1.0, 0.0, 0.0]) + (1.0 - d.p_align) * rng.standard_normal(3))
        pos = start.copy()
        X[f * (d.n_seg + 1)] = np.mod(pos, L)
        for s in range(d.n_seg):
            seg_dir[f, s] = v
            pos = pos + v
            X[f * (d.n_seg + 1) + s + 1] = np.mod(pos, L)
            if d.curve_sigma > 0:
                v = _unit(v + d.curve_sigma * rng.standard_normal(3))
    # chain bonds: bond f*n_seg+s connects node f*(n_seg+1)+s -> +s+1 (rest length 1)
    bi = np.concatenate([np.arange(f * (d.n_seg + 1), f * (d.n_seg + 1) + d.n_seg)
                         for f in range(d.n_fib)])
    bj = bi + 1
    raw = X[bj] - X[bi]
    shift = -L * np.round(raw / L)           # minimal image: d = raw + shift == v (unit)
    chain = dict(bi=bi, bj=bj, shift=shift)

    # ---- crosslinks: pairs of nodes from different fibres within r_search ----------
    # z = 2*Nb/N with Nb = n_chain + n_x  ->  n_x = z*N/2 - n_chain
    n_x = int(round(d.z * N / 2.0 - n_chain))
    cell = max(L / 12.0, 1e-6)
    grid = {}
    for i in range(N):
        key = tuple((X[i] // cell).astype(int) % int(np.ceil(L / cell)))
        grid.setdefault(key, []).append(i)
    cand = []
    r_max = min(1.2, 0.45 * L)
    for i in range(N):
        gi = (X[i] // cell).astype(int)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    key = tuple((gi + np.array([dx, dy, dz])) % int(np.ceil(L / cell)))
                    for j in grid.get(key, ()):  # noqa: B007
                        if j <= i or fiber_of[j] == fiber_of[i]:
                            continue
                        raw = X[j] - X[i]
                        off = raw - L * np.round(raw / L)   # minimal-image bond vector
                        dist = float(np.linalg.norm(off))
                        if dist < 1e-6 or dist > r_max:
                            continue
                        cand.append((i, j, dist,
                                     -L * np.round(raw / L)))   # image shift for this pair
    if len(cand) < n_x:
        # matching failure: not enough close encounters at this box size / fibre count
        return dict(ok=False, reason=f"crosslink candidates {len(cand)} < needed {n_x}",
                    N=N, n_x_target=n_x)
    cand_i = np.array([c[0] for c in cand])
    cand_j = np.array([c[1] for c in cand])
    cand_d = np.array([c[2] for c in cand])
    cand_s = np.array([c[3] for c in cand])
    if d.xlink_dist == "clustered":
        # hotspots: repeatedly take the candidate whose endpoints already carry the most
        # crosslinks (rich get richer) - a spatially clustered crosslink distribution
        deg = np.zeros(N)
        keep = []
        idx = list(range(len(cand)))
        for _ in range(n_x):
            best, best_k = None, -1
            for k in idx:
                w = deg[cand_i[k]] + deg[cand_j[k]] + rng.random() * 0.1
                if w > best_k:
                    best, best_k = k, w
            keep.append(best)
            deg[cand_i[best]] += 1
            deg[cand_j[best]] += 1
            idx.remove(best)
        sel = np.array(keep)
    else:
        sel = rng.choice(len(cand), size=n_x, replace=False)
    xi, xj, xlen = cand_i[sel], cand_j[sel], cand_d[sel]
    xlink = dict(bi=xi, bj=xj, shift=cand_s[sel], rest=xlen)
    # crosslink rest length = as-grown distance (stress-free reference)

    # ---- bend pairs along fibres (interior nodes only; open chains have free ends) --
    b_in, b_out = [], []
    for f in range(d.n_fib):
        for s in range(1, d.n_seg):
            b_in.append(f * d.n_seg + (s - 1))    # segment INTO the node
            b_out.append(f * d.n_seg + s)          # segment OUT of the node
    b_in = np.array(b_in)
    b_out = np.array(b_out)
    d_in = X[bj][b_in] + chain["shift"][b_in] - X[bi][b_in]
    d_out = X[bj][b_out] + chain["shift"][b_out] - X[bi][b_out]
    th0 = np.arctan2(np.linalg.norm(np.cross(d_in, d_out), axis=1), (d_in * d_out).sum(1))

    # ---- locks ----------------------------------------------------------------
    deg = np.bincount(np.concatenate([bi, bj, xi, xj]), minlength=N)
    n_lock = int(round(d.lock * N))
    rigid = np.zeros(N)
    if n_lock:
        if d.lock_place == "crossings":
            key = -deg + 0.5 * rng.random(N)
        else:
            key = rng.random(N)
        rigid[np.argsort(key)[:n_lock]] = d.kx

    # ---- lock pairs (spokes at locked nodes) ---------------------------------
    inc = [[] for _ in range(N)]
    for b, (a_, c_) in enumerate(zip(np.concatenate([bi, xi]), np.concatenate([bj, xj]))):
        inc[a_].append(b)
        inc[c_].append(b)
    ang_u, ang_v, ang_su, ang_sv, ang_cos0, ang_node = [], [], [], [], [], []
    allbi = np.concatenate([bi, xi])
    allbj = np.concatenate([bj, xj])
    allsh = np.concatenate([chain["shift"], xlink["shift"]])
    allrest = np.concatenate([np.ones(n_chain), xlink["rest"]])
    for n in range(N):
        if rigid[n] <= 0:
            continue
        sp = inc[n]
        dirs = []
        for b in sp:
            a_, c_ = allbi[b], allbj[b]
            if a_ == n:
                v = X[c_] + allsh[b] - X[n]
                s = 1.0
            else:
                v = X[n] + allsh[b] - X[a_]
                s = -1.0
            dirs.append((v / np.linalg.norm(v), s))
        for p in range(len(dirs)):
            for q in range(p + 1, len(dirs)):
                ang_u.append(sp[p]); ang_v.append(sp[q])
                ang_su.append(dirs[p][1]); ang_sv.append(dirs[q][1])
                # rest cosine of the SIGNED spoke directions (matches energy's u = d*su)
                ang_cos0.append(float((dirs[p][1] * dirs[p][0]) @ (dirs[q][1] * dirs[q][0])))
                ang_node.append(n)

    Nb = n_chain + n_x
    tot_len = float(n_chain * 1.0 + xlen.sum())
    info = dict(
        ok=True, N=N, Nb=Nb, n_x=n_x, z_realized=2.0 * Nb / N, z_target=d.z,
        n_lock=n_lock, box_L=L, volume=L ** 3,
        fibre_length_density=tot_len / L ** 3,
        bond_density=Nb / L ** 3,
        orientation_S2=float(((seg_dir[:, :, 0] ** 2).mean() - 1.0 / 3.0) * 1.5),
        mean_xlink_len=float(xlen.mean()), p_align=d.p_align,
        curve_sigma=d.curve_sigma,
        n_nodes_target=n_target, node_match=abs(N - n_target) / max(n_target, 1))
    net = dict(info=info, X=X, fiber_of=fiber_of,
               allbi=allbi.astype(np.int64), allbj=allbj.astype(np.int64),
               allshift=allsh, rest_len=allrest,
               n_chain=n_chain,
               bend_in=b_in.astype(np.int64), bend_out=b_out.astype(np.int64),
               bend_theta0=th0, rigid=rigid,
               ang_u=np.array(ang_u, dtype=np.int64), ang_v=np.array(ang_v, dtype=np.int64),
               ang_su=np.array(ang_su), ang_sv=np.array(ang_sv),
               ang_cos0=np.array(ang_cos0), ang_node=np.array(ang_node, dtype=np.int64),
               eps_r=np.full(Nb, d.eps_r), mu=np.full(Nb, d.mu), kappa_b=np.ones(Nb),
               design=d)
    return net


class FiberBatch:
    """Batched solver over padded stochastic-fibre realizations (Batch3D-style API)."""

    def __init__(self, nets: list[dict], device="cpu", dtype=torch.float64,
                 relax_kw: dict | None = None):
        if not nets:
            raise ValueError("empty batch")
        self.nets, self.B = nets, len(nets)
        self.device, self.dtype = device, dtype
        self.relax_kw = dict(relax_kw or {})
        t = lambda a: torch.as_tensor(np.asarray(a), device=device, dtype=dtype)
        ti = lambda a: torch.as_tensor(np.asarray(a), device=device, dtype=torch.long)
        d0 = nets[0]
        self.N = d0["X"].shape[0]
        assert all(n["X"].shape[0] == self.N for n in nets), "node count must match"
        self.L = d0["info"]["box_L"]
        self.volume = d0["info"]["volume"]
        self.X = t(np.stack([n["X"] for n in nets]))
        self.Nb_max = max(n["allbi"].shape[0] for n in nets)
        self.Pb = self.Nb_max
        Nb, B = self.Nb_max, self.B
        bi = np.zeros((B, Nb), np.int64)
        bj = np.zeros((B, Nb), np.int64)
        sh = np.zeros((B, Nb, 3))
        rest = np.ones((B, Nb))
        alive = np.zeros((B, Nb), bool)
        eps_r = np.ones((B, Nb))
        mu = np.ones((B, Nb))
        for b, n in enumerate(nets):
            k = n["allbi"].shape[0]
            bi[b, :k] = n["allbi"]; bj[b, :k] = n["allbj"]
            sh[b, :k] = n["allshift"]; rest[b, :k] = n["rest_len"]
            alive[b, :k] = True
            eps_r[b, :k] = n["eps_r"]; mu[b, :k] = n["mu"]
        self.bi, self.bj = ti(bi), ti(bj)
        self.shift = t(sh)
        self.rest_len = t(rest)
        self.alive = torch.as_tensor(alive, device=device)
        self.eps_r = t(eps_r)
        self.mu = t(mu)
        # bend pairs
        self.Pbn = max(n["bend_in"].shape[0] for n in nets)
        bin_ = np.zeros((B, self.Pbn), np.int64)
        bout = np.zeros((B, self.Pbn), np.int64)
        bth = np.zeros((B, self.Pbn))
        for b, n in enumerate(nets):
            k = n["bend_in"].shape[0]
            bin_[b, :k] = n["bend_in"]; bout[b, :k] = n["bend_out"]; bth[b, :k] = n["bend_theta0"]
        self.bend_in, self.bend_out = ti(bin_), ti(bout)
        self.bend_theta0 = t(bth)
        # lock pairs
        self.Pa = max(n["ang_u"].shape[0] for n in nets) if any(n["ang_u"].size for n in nets) else 1
        au = np.zeros((B, self.Pa), np.int64)
        av = np.zeros((B, self.Pa), np.int64)
        asu = np.ones((B, self.Pa)); asv = np.ones((B, self.Pa))
        ac0 = np.ones((B, self.Pa)); an = np.zeros((B, self.Pa), np.int64)
        lock_alive = np.zeros((B, self.Pa), bool)
        for b, n in enumerate(nets):
            k = n["ang_u"].shape[0]
            au[b, :k] = n["ang_u"]; av[b, :k] = n["ang_v"]
            asu[b, :k] = n["ang_su"]; asv[b, :k] = n["ang_sv"]
            ac0[b, :k] = n["ang_cos0"]; an[b, :k] = n["ang_node"]
            lock_alive[b, :k] = n["rigid"][n["ang_node"]] > 0
        self.ang_u, self.ang_v = ti(au), ti(av)
        self.ang_su, self.ang_sv = t(asu), t(asv)
        self.ang_cos0 = t(ac0)
        self.ang_node = ti(an)
        self.kx = t(np.stack([np.where(n["rigid"] > 0, n["design"].kx, 0.0) for n in nets]))
        self.lock_alive = torch.as_tensor(lock_alive, device=device)
        self.lock_fail_rad = t([n["design"].lock_fail_rad for n in nets])[:, None]
        self.kappa = t([n["design"].kappa for n in nets])[:, None, None]
        self.k_gag = t([n["design"].k_gag for n in nets])[:, None, None]
        self.pre = t([0.0] * B)
        eye = torch.eye(3, device=device, dtype=dtype)
        self.F0 = eye.expand(B, 3, 3) * (1 + self.pre)[:, None, None]
        self.x = (self.X @ self.F0.transpose(1, 2)).clone()
        # BUGFIX 2026-10-31: bend rest angles must be bit-exact with the energy's own
        # evaluation of the as-grown geometry.  build_fiber_network computes th0 in
        # numpy with a different op order ((X[bj]+shift)-X[bi]) than energy()
        # ((x[bj]-x[bi])+F@shift), so for COLLINEAR pairs (straight fibres, curve_sigma=0)
        # th - th0 is pure float noise; the exact-Hessian route multiplies that noise by
        # d2(th)/dx2 ~ 1/|cross| ~ 1e16, giving O(kappa) curvature of random sign
        # (finite differences: autograd -0.120 vs FD +0.026 on a straight test network;
        # Cholesky failures in fiber_hessian_moduli).  First derivatives are unaffected,
        # so relax/stress stayed correct.  Recompute th0 with the same ops the energy
        # uses so th - th0 == 0 exactly at the stress-free reference.
        with torch.no_grad():
            d_ref = self.bond_vectors(self.x, self.F0)
            din = torch.gather(d_ref, 1, self.bend_in[..., None].expand(-1, -1, 3))
            dout = torch.gather(d_ref, 1, self.bend_out[..., None].expand(-1, -1, 3))
            cr0 = torch.linalg.norm(torch.cross(din, dout, dim=-1), dim=-1)
            self.bend_theta0 = torch.atan2(cr0, (din * dout).sum(-1))
        # crack plane (per-system crossing weights); axis 0 at L/2 by default
        self.crack_axis = d0["design"].crack_axis
        ax = self.crack_axis
        w = np.zeros((B, Nb))
        q_in = np.zeros((B, Nb, 2))
        c = 0.5 * self.L
        for b, n in enumerate(nets):
            Pa_ = n["X"][n["allbi"]]
            Pb_ = n["X"][n["allbj"]] + n["allshift"]
            da, db = Pa_[:, ax] - c, Pb_[:, ax] - c
            crossing = (da * db) < 0
            sign = np.where(db > 0.0, 1.0, -1.0)
            if n["design"].notch_shape == "circle" and n["design"].notch_frac > 0:
                pa2 = [a for a in range(3) if a != ax]
                mid = 0.5 * (Pa_ + Pb_)
                r = n["design"].notch_frac * 0.5 * self.L
                inside = ((mid[:, pa2] - 0.5 * self.L) ** 2).sum(1) < r ** 2
                crossing = crossing & ~inside
            w[b, :n["allbi"].shape[0]][crossing] = sign[crossing]
        self.plane_w = t(w)
        self.A_plane = self.L ** 2

    # ---- energy ---------------------------------------------------------------
    def bond_vectors(self, x, F, jump=None):
        sh = torch.einsum("bij,bnj->bni", F, self.shift)
        if jump is not None:
            sh = sh + self.plane_w[:, :, None] * jump[:, None, :]
        return torch.gather(x, 1, self.bj[..., None].expand(-1, -1, 3)) \
             - torch.gather(x, 1, self.bi[..., None].expand(-1, -1, 3)) + sh

    def energy(self, x, F, jump=None, per_system=False):
        d = self.bond_vectors(x, F, jump)
        ln = torch.linalg.norm(d, dim=-1)
        a = self.alive.to(self.dtype)
        e = 0.5 * ((self.mu * a) * (ln - self.rest_len) ** 2).sum(1)

        din = torch.gather(d, 1, self.bend_in[..., None].expand(-1, -1, 3))
        dout = torch.gather(d, 1, self.bend_out[..., None].expand(-1, -1, 3))
        cr = torch.linalg.norm(torch.cross(din, dout, dim=-1), dim=-1)
        dt = (din * dout).sum(-1)
        th = torch.atan2(cr, dt) - self.bend_theta0
        amin = torch.gather(a, 1, self.bend_in) * torch.gather(a, 1, self.bend_out)
        e = e + 0.5 * ((self.kappa[:, 0] * amin * th ** 2)).sum(1)

        u = torch.gather(d, 1, self.ang_u[..., None].expand(-1, -1, 3)) * self.ang_su[..., None]
        v = torch.gather(d, 1, self.ang_v[..., None].expand(-1, -1, 3)) * self.ang_sv[..., None]
        ln_u = torch.gather(ln, 1, self.ang_u).clamp(min=1e-9)
        ln_v = torch.gather(ln, 1, self.ang_v).clamp(min=1e-9)
        cos = (u * v).sum(-1) / (ln_u * ln_v)
        kq = torch.gather(self.kx, 1, self.ang_node) \
            * torch.gather(a, 1, self.ang_u) * torch.gather(a, 1, self.ang_v) \
            * self.lock_alive.to(self.dtype)
        e = e + 0.5 * (kq * (cos - self.ang_cos0) ** 2).sum(1)

        xa = self.X @ F.transpose(1, 2)
        e = e + 0.5 * (self.k_gag[:, 0] * ((x - xa) ** 2).sum(-1)).sum(1)
        return e if per_system else e.sum()

    def relax(self, F, jump=None, ftol=1e-7, max_rounds=40, iters=300):
        ftol = self.relax_kw.get("ftol", ftol)
        max_rounds = self.relax_kw.get("max_rounds", max_rounds)
        iters = self.relax_kw.get("iters", iters)
        x = self.x.detach().clone().requires_grad_(True)
        opt = torch.optim.LBFGS([x], lr=1.0, max_iter=iters, history_size=50,
                                tolerance_grad=ftol, tolerance_change=1e-16,
                                line_search_fn="strong_wolfe")

        def closure():
            opt.zero_grad()
            en = self.energy(x, F, jump)
            en.backward()
            return en

        fmax = float("inf")
        e_prev = float(self.energy(x.detach(), F, jump))
        for _ in range(max_rounds):
            opt.step(closure)
            with torch.no_grad():
                e_now = float(self.energy(x, F, jump))
            fmax = float(x.grad.abs().max())
            if fmax < ftol * 10 and abs(e_prev - e_now) <= 1e-10 * abs(e_now) + 1e-18:
                break
            e_prev = e_now
        self.x = x.detach()
        return fmax

    def stress(self, F, jump=None):
        Fv = F.detach().clone().requires_grad_(True)
        e = self.energy(self.x, Fv, jump)
        (g,) = torch.autograd.grad(e, Fv)
        return g / self.volume

    def traction(self, F, jump):
        jv = jump.detach().clone().requires_grad_(True)
        e = self.energy(self.x, F, jv)
        (g,) = torch.autograd.grad(e, jv)
        return g / self.A_plane

    def move_affine(self, F_old, F_new):
        M = F_new @ torch.linalg.inv(F_old)
        self.x = self.x @ M.transpose(1, 2)

    def bond_strain(self, F, jump=None):
        d = self.bond_vectors(self.x, F, jump)
        return torch.linalg.norm(d, dim=-1) - self.rest_len

    def bond_tension(self, F, jump=None):
        return self.mu * self.bond_strain(F, jump) * self.alive.to(self.dtype)

    def rupture(self, F, jump=None):
        s = self.bond_strain(F, jump)
        brk = self.alive & (s > self.eps_r)
        self.alive = self.alive & ~brk
        return brk.sum(1)

    def lock_deviation(self, F, jump=None):
        d = self.bond_vectors(self.x, F, jump)
        ln = torch.linalg.norm(d, dim=-1)
        u = torch.gather(d, 1, self.ang_u[..., None].expand(-1, -1, 3)) * self.ang_su[..., None]
        v = torch.gather(d, 1, self.ang_v[..., None].expand(-1, -1, 3)) * self.ang_sv[..., None]
        ln_u = torch.gather(ln, 1, self.ang_u).clamp(min=1e-9)
        ln_v = torch.gather(ln, 1, self.ang_v).clamp(min=1e-9)
        cos = (u * v).sum(-1) / (ln_u * ln_v)
        cos0 = torch.clamp(self.ang_cos0, -1.0, 1.0)
        return torch.acos(torch.clamp(cos, -1.0, 1.0)) - torch.acos(cos0)

    def rupture_locks(self, F, jump=None):
        dev = self.lock_deviation(F, jump)
        brk = self.lock_alive & (dev > self.lock_fail_rad)
        self.lock_alive = self.lock_alive & ~brk
        return brk.sum(1)

    # ---- protocols (Batch3D-compatible signatures) ----------------------------
    def F_shear(self, g):
        F = self.F0.clone()
        F[:, 0, 1] += g
        return F

    def F_stretch(self, e, axis):
        F = self.F0.clone()
        F[:, axis, axis] *= (1 + e)
        return F

    def small_strain_moduli(self, eps=2e-3, keys=("G", "Cx", "Cy", "Cz")):
        """Relax-based anisotropic small-strain moduli (documented difference to the
        exact-Hessian route used for the FCC families; fine for screening comparisons)."""
        x0 = self.x.clone()
        self.relax(self.F0)
        xr = self.x.clone()
        base = self.stress(self.F0)
        res = {}
        for name in keys:
            if name == "G":
                F = self.F_shear(eps)
                ax = (0, 1)
            else:
                axn = {"Cx": 0, "Cy": 1, "Cz": 2}[name]
                F = self.F_stretch(eps, axn)
                ax = (axn, axn)
            self.x = xr.clone()
            self.move_affine(self.F0, F)
            self.relax(F)
            P = self.stress(F)
            res[name] = ((P[:, ax[0], ax[1]] - base[:, ax[0], ax[1]]) / eps).cpu().numpy()
        self.x = x0
        return res

    def failure_curve(self, strains, axis=0, max_cascade=8):
        Fp = self.F0.clone()
        self.relax(Fp)
        sig, broken, first = [], [], np.full(self.B, np.nan)
        i_peak = np.zeros(self.B, dtype=np.int64)
        s_peak = np.full(self.B, -np.inf)
        t_peak = torch.zeros(self.B, self.Nb_max, device=self.device, dtype=self.dtype)
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
        from oxt.network3d import _trap
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
                s_load.append(self.stress(F)[:, axis, axis].cpu().numpy())
                Fp = F
            w_load = _trap(np.stack(s_load, 1), np.concatenate([[0.0], eps]), axis=1)
            out["peak"].append(s_load[-1])
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
            s_un.append(self.stress(F)[:, axis, axis].cpu().numpy())
            Fp = F
            ee = np.concatenate([eps[::-1], [0.0]])
            w_unload = _trap(np.stack(s_un, 1), ee, axis=1)
            out["w_unload"].append(w_unload)
            out["diss"].append(w_load - w_unload)
            out["broken"].append(nb)
            out["residual"].append(s_un[-1])
        return {k: np.stack(v, 1) for k, v in out.items()}

    def cohesive_curve(self, deltas, mode="tension", mix=1.0, max_cascade=8):
        ax = self.crack_axis
        tan = (ax + 1) % 3
        dj = {"tension": (1.0, 0.0), "shear": (0.0, 1.0), "mixed": (1.0, mix)}[mode]
        F = self.F0.clone()
        jump0 = torch.zeros(self.B, 3, device=self.device, dtype=self.dtype)
        self.relax(F, jump=jump0)
        T, Teff, broken, locks, first = [], [], [], [], np.full(self.B, np.nan)
        t_peak = np.full(self.B, -np.inf)
        tp_snap = torch.zeros(self.B, self.Nb_max, device=self.device, dtype=self.dtype)
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
            tr = self.traction(F, j).cpu().numpy()
            teff = tr[:, ax] * dj[0] + tr[:, tan] * dj[1]
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


def fiber_hessian_moduli(net: dict, device="cpu", dtype=torch.float64) -> dict:
    """Exact linear-response moduli at the stress-free state for ONE stochastic-fibre
    realization (same recipe as oxt.network3d.hessian_moduli, general graph version)."""
    b = FiberBatch([net], device=device, dtype=dtype)
    b.relax(b.F0)
    N = net["X"].shape[0]
    V = net["info"]["volume"]
    F0 = b.F0
    x0 = b.x.detach().reshape(-1).clone()

    def efun(v):
        return b.energy(v.view(1, N, 3), F0)

    H = torch.autograd.functional.hessian(efun, x0, vectorize=True).cpu().numpy()
    H = 0.5 * (H + H.T)
    cho = np.linalg.cholesky(H + 1e-10 * np.eye(H.shape[0]))
    solve = lambda r: np.linalg.solve(cho.T, np.linalg.solve(cho, r))
    I3 = torch.eye(3, dtype=dtype, device=device)

    def mixed(D, h=1e-5):
        D_t = torch.as_tensor(D, dtype=dtype, device=device)
        gs = []
        for s in (+h, -h):
            F = I3.clone()[None] + s * D_t[None]
            x = (b.X[0] @ F[0].T).reshape(-1).clone().requires_grad_(True)
            e = b.energy(x.view(1, N, 3), F)
            (g,) = torch.autograd.grad(e, x)
            gs.append(g.cpu().numpy())
        return (gs[0] - gs[1]) / (2 * h)

    def e_aff2(D):
        D_t = torch.as_tensor(D, dtype=dtype, device=device)
        eps = torch.zeros((), dtype=dtype, device=device, requires_grad=True)
        F = I3[None] + eps * D_t[None]
        e = b.energy((b.X[0] @ F[0].T)[None], F)
        (g1,) = torch.autograd.grad(e, eps, create_graph=True)
        (g2,) = torch.autograd.grad(g1, eps)
        return float(g2)

    dirs = {"G": [[0, 1, 0], [0, 0, 0], [0, 0, 0]],
            "Gyz": [[0, 0, 0], [0, 0, 1], [0, 0, 0]],
            "Gzx": [[0, 0, 0], [0, 0, 0], [1, 0, 0]],
            "Cx": [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
            "Cy": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
            "Cz": [[0, 0, 0], [0, 0, 0], [0, 0, 1]]}
    out = {}
    for name, D in dirs.items():
        bm = mixed(D)
        u = -solve(bm)
        out[name] = float((e_aff2(D) + bm @ u) / V)
    return out
