#!/usr/bin/env python3
"""Topology optimisation of 2D Col I fibre networks for organoid scaffolds (NSGA-II, plain numpy).

A design is a 7-gene vector in [0, 1]^7 that sets *where* fibre segments (bonds) and LOX-locked junctions
go around an empty pore that stands in for the organoid:

  g0  z        mean matrix connectivity, 2.6 .. 5.0 (outside the pore)
  g1  pattern  uniform | graded (radial, around the pore) | layered (bands parallel to x) | clustered
               (smoothed random field) | aligned (by lattice direction; + = along x)
  g2  amp      pattern amplitude, -1 .. 1 (sign: graded + = denser near the pore; aligned + = x-rich)
  g3  scale    layered: 1-3 bands; clustered: correlation length 0.8-3 lattice units
  g4  lock     fraction of matrix junctions locked (kx = 2e-3, pyridinoline-type, as run_phase.py)
  g5  place    lock placement: random | near the pore | far from the pore | at fibre crossings (high degree)
  g6  pore     pore radius, 1 .. W/4 lattice units

Objectives, all from oxt/network.py (Col I parameters, no AGE damage); each design is evaluated on two
independent realisations, one pulled along x and one along y, so a design cannot win by aligning with
the load axis:
  resilience  toughness (worst of the two pulls, maximise) and brittleness = largest one-step stress drop
              relative to peak (worst of the two, minimise); strain at peak and largest rupture avalanche
              are recorded too
  sensing     sqrt(T * reach): T = bond strain in a 2-unit ring around the pore relative to the affine bond
              strain under a small uniaxial stretch (strain transmission to the cell); reach = share of the
              work of an isotropic contraction at the pore stored in fibres beyond the pore-to-box midpoint,
              relative to a fully bonded sheet with the same pore (linear response, exact Hessian solve)
  transport   effective radial diffusivity D/D0 of an exosome-sized particle (r = 50 nm) from the outer
              shell to the pore, through shells in series with Ogston hindrance per shell
              (oxt.physio.ogston, phi = 0.15 x local bond density relative to native Col I z = 3.4)
Constraint: linear shear modulus G inside a stiffness band derived from oxt/cell.py (see --calibrate-yap);
violation = |log10 distance| to the band.  Feasible designs dominate infeasible ones (Deb's rule).

  python3 topo_opt.py --calibrate-yap               # YAP(E) curve -> results/topo/yap_calibration.csv
  python3 topo_opt.py --profile smoke               # quick check
  python3 topo_opt.py --profile cpu32 --tag ga_W12  # GCP 32 vCPU
  python3 topo_opt.py --reeval results/topo/ga_W12_designs.csv --profile cpu32 --W 16 --reps 2 \
      --workers 28 --max-designs 10 --tag reeval_W16       # front subset + uniform baselines
Set OMP_NUM_THREADS=1 (and OPENBLAS/MKL) when running many workers.
Rows are appended to results/topo/<tag>_evals.csv (one per realisation) and <tag>_designs.csv (one per
design, with generation and rank) as they finish, so a partial run is usable.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "topo"

PROFILES = {
    "smoke": dict(W=8, pop=8, gens=2, workers=4, fail=list(np.round(np.arange(0.04, 0.41, 0.04), 3))),
    "local": dict(W=10, pop=12, gens=10, workers=6, fail=list(np.round(np.arange(0.04, 0.45, 0.04), 3))),
    "cpu32": dict(W=12, pop=28, gens=30, workers=28, fail=list(np.round(np.arange(0.04, 0.45, 0.04), 3))),
}
PATTERNS = ["uniform", "graded", "layered", "clustered", "aligned"]
PLACES = ["random", "near_pore", "far_pore", "crossings"]
KX_LOX = 2e-3          # same as run_phase.KX_LOX
Z_NATIVE = 3.4         # COLLAGENS["I"].z: bond density reference for transport
PHI0 = 0.15            # collagen volume fraction at native density, as run_sweep.stage_organ
R_PROBE_NM = 50.0      # exosome radius (oxt.physio.MOLECULES["exosome"])
S_PA = 12667.0         # Pa per stress unit: results/cpu32/summary.json S_pa_per_unit (young dermis E = 2 kPa)
N_GENES = 7
FAIL_KEYS = ["strength", "strain_at_peak", "toughness", "max_drop", "max_avalanche", "broken_total", "residual",
             "curve"]


# --------------------------------------------------------------------------------------------------
# design -> network
# --------------------------------------------------------------------------------------------------
def decode(g, W):
    g = np.clip(np.asarray(g, float), 0, 1 - 1e-12)
    return dict(z=2.6 + 2.4 * g[0], pattern=PATTERNS[int(g[1] * len(PATTERNS))], amp=-1 + 2 * g[2],
                scale=g[3], lock=g[4], place=PLACES[int(g[5] * len(PLACES))], pore=1.0 + g[6] * (W / 4 - 1))


def _min_image(P, c, L):
    d = P - c
    return d - L * np.round(d / L)


def geometry(lat, pore):
    c = lat.L / 2
    mid = lat.X[lat.bi] + 0.5 * np.array([[1.0, 0.0], [0.5, math.sqrt(3) / 2], [-0.5, math.sqrt(3) / 2]])[lat.bdir]
    dm = _min_image(mid, c, lat.L)
    dn = _min_image(lat.X, c, lat.L)
    rn = np.linalg.norm(dn, axis=1)
    in_pore = rn < pore
    return dict(c=c, dm=dm, rm=np.linalg.norm(dm, axis=1), dn=dn, rn=rn, in_pore=in_pore,
                pore_bond=in_pore[lat.bi] | in_pore[lat.bj], r_max=0.5 * min(lat.L))


def pattern_field(d, lat, geo, rng):
    """Zero-mean field on bonds; probability of a bond is p0 * (1 + amp * f)."""
    m = ~geo["pore_bond"]
    if d["pattern"] == "uniform":
        f = np.zeros(lat.Nb)
    elif d["pattern"] == "graded":
        r = np.clip((geo["rm"] - d["pore"]) / max(geo["r_max"] - d["pore"], 1e-9), 0, 1)
        f = 1 - 2 * r
    elif d["pattern"] == "layered":
        n = 1 + int(d["scale"] * 3 - 1e-9)
        y = geo["dm"][:, 1] + geo["c"][1]
        f = np.cos(2 * np.pi * n * y / lat.L[1])
    elif d["pattern"] == "clustered":
        ell = 0.8 + 2.2 * d["scale"]
        dn = lat.X[:, None] - lat.X[None]
        dn -= lat.L * np.round(dn / lat.L)
        K = np.exp(-(dn ** 2).sum(-1) / (2 * ell ** 2))
        s = K @ rng.standard_normal(lat.N)
        s = (s - s.mean()) / (s.std() + 1e-12)
        f = np.tanh(0.5 * (s[lat.bi] + s[lat.bj]))
    elif d["pattern"] == "aligned":
        f = np.where(lat.bdir == 0, 1.0, -0.5)
    f = f - f[m].mean() if m.any() else f
    return f


def build_design(d, lat, rng):
    from oxt.materials import COLLAGENS
    from oxt.network import SystemSpec

    col = COLLAGENS["I"]
    geo = geometry(lat, d["pore"])
    f = pattern_field(d, lat, geo, rng)
    m = ~geo["pore_bond"]
    n_m = int((~geo["in_pore"]).sum())
    target = d["z"] * n_m / 2 / (1 - 1.0 / lat.W)  # expected alive matrix bonds before the line cut
    lo, hi = 0.0, 5.0
    for _ in range(50):  # bisection on p0 so that the expected bond count hits the target z
        p0 = 0.5 * (lo + hi)
        if np.clip(p0 * (1 + d["amp"] * f[m]), 0, 1).sum() < target:
            lo = p0
        else:
            hi = p0
    p = np.clip(p0 * (1 + d["amp"] * f), 0, 1)
    alive = (rng.random(lat.Nb) < p) & m
    for line in range(lat.n_lines):  # finite fibres: one cut per line that the pore does not cut already
        members = np.flatnonzero(lat.line == line)
        if not geo["pore_bond"][members].any():
            alive[rng.choice(members)] = False

    deg = np.bincount(lat.bi[alive], minlength=lat.N) + np.bincount(lat.bj[alive], minlength=lat.N)
    rigid = np.zeros(lat.N)
    cand = np.flatnonzero(~geo["in_pore"] & (deg >= 2))
    n_lock = min(int(round(d["lock"] * n_m)), cand.size)
    if n_lock:
        tie = rng.random(cand.size)
        key = {"random": tie, "near_pore": geo["rn"][cand] + 1e-3 * tie,
               "far_pore": -geo["rn"][cand] + 1e-3 * tie, "crossings": -deg[cand] + 0.5 * tie}[d["place"]]
        rigid[cand[np.argsort(key)[:n_lock]]] = KX_LOX
    spec = SystemSpec(alive=alive, mu=np.full(lat.Nb, col.mu), kappa_b=np.ones(lat.Nb),
                      eps_r=np.full(lat.Nb, col.eps_r), rigid_node=rigid, kappa=col.kappa, mu_el=0.0,
                      k_gag=1e-6, prestrain=0.0, meta=dict(d))
    return spec, geo, n_m


# --------------------------------------------------------------------------------------------------
# linear response at the stress-free reference: exact Hessian solve (no L-BFGS)
# --------------------------------------------------------------------------------------------------
def linear_response(b, geo, pore):
    import torch

    lat = b.lat
    N = lat.N
    X = b.X
    I2 = torch.eye(2, dtype=b.dtype)[None]

    def efun(v):
        return b.energy(v.view(1, N, 2), I2)

    x0 = X.reshape(-1).clone()
    H = torch.autograd.functional.hessian(efun, x0, vectorize=True)
    Hn = H.numpy()

    def mixed(D, h=1e-5):  # d/d(eps) of dE/dx along the affine path F = I + eps D
        gs = []
        for s in (+h, -h):
            F = (torch.eye(2, dtype=b.dtype) + s * torch.as_tensor(D, dtype=b.dtype))[None]
            x = (X @ F[0].T).reshape(-1).clone().requires_grad_(True)
            e = b.energy(x.view(1, N, 2), F)
            (g,) = torch.autograd.grad(e, x)
            gs.append(g)
        return ((gs[0] - gs[1]) / (2 * h)).numpy()

    def e_aff2(D):
        eps = torch.zeros((), dtype=b.dtype, requires_grad=True)
        F = (torch.eye(2, dtype=b.dtype) + eps * torch.as_tensor(D, dtype=b.dtype))[None]
        e = b.energy((X @ F[0].T)[None], F)
        (g1,) = torch.autograd.grad(e, eps, create_graph=True)
        (g2,) = torch.autograd.grad(g1, eps)
        return float(g2)

    cho = np.linalg.cholesky(Hn)
    solve = lambda r: np.linalg.solve(cho.T, np.linalg.solve(cho, r))
    out = {}
    na = {}
    for name, D in [("G", [[0, 1], [0, 0]]), ("Cx", [[1, 0], [0, 0]]), ("Cy", [[0, 0], [0, 1]])]:
        bm = mixed(D)
        u = -solve(bm)
        out[name] = (e_aff2(D) + bm @ u) / lat.area
        na[name] = u.reshape(N, 2)

    alive = b.alive[0].numpy()
    nvec = np.array([[1.0, 0.0], [0.5, math.sqrt(3) / 2], [-0.5, math.sqrt(3) / 2]])[lat.bdir]
    ring = alive & (geo["rm"] >= pore) & (geo["rm"] < pore + 2.0)
    matrix_nodes = ~geo["in_pore"]
    for name, ax in [("Cx", 0), ("Cy", 1)]:
        u = na[name]
        s_aff = nvec[:, ax] ** 2
        s = s_aff + (nvec * (u[lat.bj] - u[lat.bi])).sum(1)
        out[f"T_ring_{name}"] = float(np.abs(s[ring]).sum() / max(np.abs(s_aff[ring]).sum(), 1e-12))
        out[f"T_bulk_{name}"] = float(np.abs(s[alive]).sum() / max(np.abs(s_aff[alive]).sum(), 1e-12))
        out[f"nonaffine_{name}"] = float((u[matrix_nodes] ** 2).sum(1).mean())

    out.update(contraction(solve, lat, geo, pore, b.specs[0], matrix_nodes, nvec))
    return out


def term_energies(spec, lat, u):
    """Per-term fibre energies (stretch per bond, bending per collinear pair, lock per spoke pair) at
    displacement u from the reference, with the location (distance from the pore centre) of each term.
    Same expressions as Batch.energy, evaluated in numpy so they can be split by position."""
    x = lat.X + u
    a = spec.alive.astype(float)
    d = x[lat.bj] - x[lat.bi] + lat.shift
    ln = np.linalg.norm(d, axis=1)
    e_s = 0.5 * (spec.mu * a + spec.mu_el) * (ln - 1) ** 2
    din, dout = d[lat.bend_in], d[lat.bend_out]
    th = np.arctan2(din[:, 0] * dout[:, 1] - din[:, 1] * dout[:, 0], (din * dout).sum(1))
    kp = spec.kappa * np.sqrt(spec.kappa_b[lat.bend_in] * spec.kappa_b[lat.bend_out]) * a[lat.bend_in] * a[lat.bend_out]
    e_b = 0.5 * kp * th ** 2
    uu = d[lat.ang_u] * lat.ang_su[:, None]
    vv = d[lat.ang_v] * lat.ang_sv[:, None]
    phi = np.arctan2(uu[:, 0] * vv[:, 1] - uu[:, 1] * vv[:, 0], (uu * vv).sum(1))
    e_l = 0.5 * spec.rigid_node[lat.ang_node] * a[lat.ang_u] * a[lat.ang_v] * (phi - math.pi / 3) ** 2
    return e_s, e_b, e_l


def contraction(solve, lat, geo, pore, spec, matrix_nodes, nvec):
    """Isotropic contraction at the pore: unit inward force on fibre crossings (degree >= 3) of the giant
    cluster within 1.5 of the edge (dangling ends would only be dragged against the tether), with the net
    force removed so the box does not translate on the tether.  Returns the far/near fibre-strain ratio."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    N = lat.N
    alive, k_gag = spec.alive, spec.k_gag
    out = {}
    deg = np.bincount(lat.bi[alive], minlength=N) + np.bincount(lat.bj[alive], minlength=N)
    _, lab = connected_components(coo_matrix((np.ones(alive.sum()), (lat.bi[alive], lat.bj[alive])),
                                             shape=(N, N)), directed=False)
    giant = lab == np.argmax(np.bincount(lab[matrix_nodes])) if matrix_nodes.any() else np.zeros(N, bool)
    out["giant"] = float(giant[matrix_nodes].mean()) if matrix_nodes.any() else 0.0
    rn, dn = geo["rn"], geo["dn"]
    src = matrix_nodes & giant & (rn < pore + 1.5) & (deg >= 3)
    if src.sum() < 2:
        out.update(decay_len=0.0, decay_ratio=0.0, u_ratio=0.0, decay_dist=1.0, w_fib=0.0, far_work=0.0,
                   n_src=int(src.sum()))
        return out
    f = np.zeros((N, 2))
    f[src] = -dn[src] / np.maximum(rn[src, None], 1e-9)
    f[src] -= f[src].mean(0)
    u = solve(f.reshape(-1)).reshape(N, 2)
    # what a distant cell feels is fibre strain, not displacement: a floppy network moves as a whole on
    # its weak tether (large, slowly decaying u) while carrying almost no fibre tension
    eb = np.abs((nvec * (u[lat.bj] - u[lat.bi])).sum(1))
    um = np.linalg.norm(u, axis=1)
    r_out = geo["r_max"] - 1.0
    near_b = alive & (geo["rm"] < pore + 1.0)
    far_b = alive & (np.abs(geo["rm"] - r_out) < 0.5)
    far_n = matrix_nodes & (np.abs(rn - r_out) < 0.5)
    R = eb[far_b].mean() / max(eb[near_b].mean(), 1e-300) if far_b.any() and near_b.any() else 0.0
    Ru = um[far_n].mean() / max(um[src].mean(), 1e-300) if far_n.any() else 0.0
    dist = max(r_out - (pore + 0.5), 1e-9)
    # fraction of the cell's work stored in fibres rather than in the weak background tether
    w_fib = 1.0 - k_gag * (u ** 2).sum() / max((f * u).sum(), 1e-300)
    Rc = min(max(R, 1e-6), 0.9)
    # reach: share of the fibre energy (stretch + bending + locks) stored beyond the midpoint between the
    # pore edge and the box edge; in a sub-isostatic network most of the work goes into bending, which a
    # strain ratio misses
    e_s, e_b, e_l = term_energies(spec, lat, u * (1e-4 / max(um.max(), 1e-300)))
    r_split = 0.5 * (pore + geo["r_max"])
    far = e_s[geo["rm"] >= r_split].sum() + e_b[geo["rn"][lat.bend_node] >= r_split].sum() \
        + e_l[geo["rn"][lat.ang_node] >= r_split].sum()
    tot = e_s.sum() + e_b.sum() + e_l.sum()
    out.update(decay_ratio=float(R), decay_len=float(dist / -math.log(Rc)), u_ratio=float(Ru),
               decay_dist=float(dist), w_fib=float(w_fib), far_work=float(far / max(tot, 1e-300)),
               n_src=int(src.sum()))
    return out


def reference_ratio(lat, geo, pore):
    """Far-field work share of a fully bonded (z = 6) sheet with the same pore and box: the geometric
    (box size, pore size, periodic image) part of the decay that any network would show."""
    import torch
    from oxt.materials import COLLAGENS
    from oxt.network import Batch, SystemSpec

    col = COLLAGENS["I"]
    alive = ~geo["pore_bond"]
    spec = SystemSpec(alive=alive, mu=np.full(lat.Nb, col.mu), kappa_b=np.ones(lat.Nb),
                      eps_r=np.full(lat.Nb, col.eps_r), rigid_node=np.zeros(lat.N), kappa=col.kappa,
                      mu_el=0.0, k_gag=1e-6)
    b = Batch(lat, [spec])
    N = lat.N
    I2 = torch.eye(2, dtype=b.dtype)[None]
    H = torch.autograd.functional.hessian(lambda v: b.energy(v.view(1, N, 2), I2), b.X.reshape(-1).clone(),
                                          vectorize=True).numpy()
    cho = np.linalg.cholesky(H)
    solve = lambda r: np.linalg.solve(cho.T, np.linalg.solve(cho, r))
    nvec = np.array([[1.0, 0.0], [0.5, math.sqrt(3) / 2], [-0.5, math.sqrt(3) / 2]])[lat.bdir]
    return contraction(solve, lat, geo, pore, spec, ~geo["in_pore"], nvec)["far_work"]
    u = solve(f.reshape(-1)).reshape(N, 2)
    # what a distant cell feels is fibre strain, not displacement: a floppy network moves as a whole on
    # its weak tether (large, slowly decaying u) while carrying almost no fibre tension
    eb = np.abs((nvec * (u[lat.bj] - u[lat.bi])).sum(1))
    um = np.linalg.norm(u, axis=1)
    r_out = geo["r_max"] - 1.0
    near_b = alive & (geo["rm"] < pore + 1.0)
    far_b = alive & (np.abs(geo["rm"] - r_out) < 0.5)
    far_n = matrix_nodes & (np.abs(rn - r_out) < 0.5)
    R = eb[far_b].mean() / max(eb[near_b].mean(), 1e-300) if far_b.any() and near_b.any() else 0.0
    Ru = um[far_n].mean() / max(um[src].mean(), 1e-300) if far_n.any() else 0.0
    dist = max(r_out - (pore + 0.5), 1e-9)
    # fraction of the cell's work stored in the fibre network rather than the weak background tether;
    # R > 1 happens only when the pore edge is barely attached, so R is clipped to 0.9
    w_fib = 1.0 - 1e-6 * (u ** 2).sum() / max((f * u).sum(), 1e-300)
    Rc = min(max(R, 1e-6), 0.9)
    # reach: share of the fibre energy (stretch + bending + locks) stored beyond the midpoint between the
    # pore edge and the box edge; in a sub-isostatic network most of the work goes into bending, which a
    # strain ratio misses
    e_s, e_b, e_l = term_energies(spec, lat, u * (1e-4 / max(um.max(), 1e-300)))
    r_split = 0.5 * (pore + geo["r_max"])
    far = e_s[geo["rm"] >= r_split].sum() + e_b[geo["rn"][lat.bend_node] >= r_split].sum() \
        + e_l[geo["rn"][lat.ang_node] >= r_split].sum()
    tot = e_s.sum() + e_b.sum() + e_l.sum()
    out.update(decay_ratio=float(R), decay_len=float(dist / -math.log(Rc)), u_ratio=float(Ru),
               decay_dist=float(dist), w_fib=float(w_fib), far_work=float(far / max(tot, 1e-300)),
               n_src=int(src.sum()))
    return out


# --------------------------------------------------------------------------------------------------
def transport_radial(alive, lat, geo, pore, n_m):
    """D_eff / D0 for a probe diffusing from the outer shell to the pore through shells in series."""
    from oxt.physio import ogston

    edges = np.arange(pore, geo["r_max"] + 1e-9, 1.0)
    if edges.size < 2:
        return 1.0, 1.0
    res = res0 = 0.0
    dens_native = Z_NATIVE / 2  # bonds per node at native connectivity
    for r0, r1 in zip(edges[:-1], edges[1:]):
        nodes = (~geo["in_pore"]) & (geo["rn"] >= r0) & (geo["rn"] < r1)
        bonds = alive & (geo["rm"] >= r0) & (geo["rm"] < r1)
        dens = bonds.sum() / max(nodes.sum(), 1) / dens_native
        D = ogston(R_PROBE_NM, PHI0 * dens, 40.0)
        rc = 0.5 * (r0 + r1)
        res += (r1 - r0) / (rc * D)
        res0 += (r1 - r0) / rc
    dens_all = alive.sum() / max(n_m, 1) / dens_native
    return res0 / res, ogston(R_PROBE_NM, PHI0 * dens_all, 40.0)


def failure(b, strains, axis, max_cascade=8):
    """Same protocol as Batch.failure_curve (quasi-static, laterally constrained stretch with rupture)."""
    import torch

    sig, broken = b.failure_curve(strains, axis=axis, max_cascade=max_cascade)
    s, k_all = sig[0], broken[0]
    eps = np.asarray(strains)
    nb = max(int(torch.as_tensor(b.specs[0].alive).sum()), 1)
    k = int(np.argmax(s))
    drops = np.diff(s) / max(s[k], 1e-300)
    return dict(strength=float(s[k]), strain_at_peak=float(eps[k]),
                toughness=float(np.trapz(np.clip(s, 0, None), eps)),
                max_drop=float(max(-drops.min(), 0.0)) if drops.size else 0.0,
                max_avalanche=float(k_all.max() / nb), broken_total=float(k_all.sum() / nb),
                residual=float(s[-1] / max(s[k], 1e-300)), curve=json.dumps([float(v) for v in s]))


def _worker(task):
    import torch

    torch.set_num_threads(1)
    from oxt.network import Batch, Lattice, coordination, mesh_size

    lat = Lattice(task["W"])
    d = decode(task["genes"], task["W"])
    rng = np.random.default_rng(task["seed"])
    spec, geo, n_m = build_design(d, lat, rng)
    t0 = time.time()
    row = dict(design=task["design"], gen=task["gen"], rep=task["rep"], seed=task["seed"], axis=task["axis"],
               W=task["W"], **{k: v for k, v in d.items()},
               genes=json.dumps([round(float(x), 5) for x in task["genes"]]),
               z_box=coordination(spec, lat), z_matrix=2.0 * spec.alive.sum() / n_m,
               n_locked=int((spec.rigid_node > 0).sum()), mesh=mesh_size(spec, lat))
    b = Batch(lat, [spec])
    row.update(linear_response(b, geo, d["pore"]))
    row["far_work_ref"] = reference_ratio(lat, geo, d["pore"])
    row["decay_rel"] = row["far_work"] / max(row["far_work_ref"], 1e-12)
    ax = "Cx" if task["axis"] == 0 else "Cy"  # transmission along this realisation's pull axis
    row["T_ring"], row["T_bulk"] = row[f"T_ring_{ax}"], row[f"T_bulk_{ax}"]
    row["D_radial"], row["D_bulk"] = transport_radial(spec.alive, lat, geo, d["pore"], n_m)
    t1 = time.time()
    # realisations far outside the stiffness band are infeasible whatever their toughness (constraint
    # domination ranks them by violation alone); the floppy ones are also the slowest to relax
    lo, hi = task.get("G_skip", (0.0, np.inf))
    row["fail_skipped"] = bool(task["fail"]) and not (lo <= row["G"] <= hi)
    row.update({k: np.nan for k in FAIL_KEYS})  # fixed column order for the appended CSV
    if task["fail"] and not row["fail_skipped"]:
        row.update(failure(Batch(lat, [spec]), task["fail"], task["axis"]))
    row.update(sec_linear=t1 - t0, seconds=time.time() - t0)
    return row


# --------------------------------------------------------------------------------------------------
# objectives, constraint, NSGA-II
# --------------------------------------------------------------------------------------------------
def load_band():
    p = OUT / "yap_band.json"
    if not p.exists():
        raise SystemExit("run --calibrate-yap first (writes results/topo/yap_band.json)")
    return json.loads(p.read_text())


def aggregate(rows, band):
    """Per-design objectives from its realisations (worst case for resilience, mean otherwise)."""
    df = pd.DataFrame(rows)
    g = df.groupby("design")
    first = g.first()
    agg = pd.DataFrame(dict(
        gen=first["gen"], genes=first["genes"], W=first["W"], z=first["z"], pattern=first["pattern"],
        amp=first["amp"], scale=first["scale"], lock=first["lock"], place=first["place"], pore=first["pore"],
        n_reps=g.size(), z_matrix=g["z_matrix"].mean(), z_box=g["z_box"].mean(), mesh=g["mesh"].mean(),
        G=g["G"].mean(), G_sd=g["G"].std(), Cx=g["Cx"].mean(), Cy=g["Cy"].mean(),
        T_ring=g["T_ring"].mean(), T_bulk=g["T_bulk"].mean(),
        nonaffine=g["nonaffine_Cx"].mean(), decay_len=g["decay_len"].mean(), decay_ratio=g["decay_ratio"].mean(),
        decay_dist=g["decay_dist"].mean(), u_ratio=g["u_ratio"].mean(), w_fib=g["w_fib"].mean(),
        decay_rel=g["decay_rel"].mean(), far_work=g["far_work"].mean(), far_work_ref=g["far_work_ref"].mean(),
        D_radial=g["D_radial"].mean(), D_bulk=g["D_bulk"].mean()))
    if "toughness" in df:
        agg["toughness"] = g["toughness"].min()
        agg["toughness_mean"] = g["toughness"].mean()
        agg["max_drop"] = g["max_drop"].max()
        agg["max_avalanche"] = g["max_avalanche"].max()
        agg["strain_at_peak"] = g["strain_at_peak"].min()
        agg["strength"] = g["strength"].min()
    agg["E_Pa"] = 3 * agg["G"] * S_PA
    # far-field share of the cell's work relative to a fully bonded sheet with the same pore and box
    # (removes box and pore geometry), capped at 1.5 and gated by the share stored in fibres at all
    agg["decay_norm"] = np.clip(agg["decay_rel"], 0, 1.5) * np.clip(agg["w_fib"], 0, 1)
    agg["sensing"] = np.sqrt(np.clip(agg["T_ring"], 0, None) * np.clip(agg["decay_norm"], 0, None))
    lo, hi = band["G_lo"], band["G_hi"]
    Gc = np.clip(agg["G"], 1e-12, None)
    agg["viol"] = np.where(Gc < lo, np.log10(lo / Gc), np.where(Gc > hi, np.log10(Gc / hi), 0.0))
    return agg.reset_index()


OBJ = [("toughness", -1), ("max_drop", +1), ("sensing", -1), ("D_radial", -1)]  # (column, sign): minimise sign*x


def objective_matrix(agg):
    F = np.stack([s * agg[c].to_numpy(float) if c in agg else np.full(len(agg), np.nan) for c, s in OBJ], 1)
    return np.where(np.isnan(F), 1e9, F)  # skipped rupture pulls rank last on that objective


def dominates(fa, fb, va, vb):
    if va > 0 or vb > 0:  # constraint domination (Deb 2000)
        return va < vb
    return bool(np.all(fa <= fb) and np.any(fa < fb))


def nondominated_sort(F, V):
    n = len(F)
    S = [[] for _ in range(n)]
    cnt = np.zeros(n, int)
    for i in range(n):
        for j in range(i + 1, n):
            if dominates(F[i], F[j], V[i], V[j]):
                S[i].append(j); cnt[j] += 1
            elif dominates(F[j], F[i], V[j], V[i]):
                S[j].append(i); cnt[i] += 1
    rank = np.full(n, -1)
    front = [i for i in range(n) if cnt[i] == 0]
    r = 0
    while front:
        nxt = []
        for i in front:
            rank[i] = r
            for j in S[i]:
                cnt[j] -= 1
                if cnt[j] == 0:
                    nxt.append(j)
        front, r = nxt, r + 1
    return rank


def crowding(F, rank):
    cd = np.zeros(len(F))
    for r in np.unique(rank):
        idx = np.flatnonzero(rank == r)
        if idx.size <= 2:
            cd[idx] = np.inf
            continue
        for m in range(F.shape[1]):
            o = idx[np.argsort(F[idx, m])]
            span = F[o[-1], m] - F[o[0], m]
            cd[o[0]] = cd[o[-1]] = np.inf
            if span > 0:
                cd[o[1:-1]] += (F[o[2:], m] - F[o[:-2], m]) / span
    return cd


def sbx_pm(p1, p2, rng, eta_c=15.0, eta_m=20.0, pc=0.9):
    c1, c2 = p1.copy(), p2.copy()
    if rng.random() < pc:
        for i in range(p1.size):
            if rng.random() < 0.5:
                u = rng.random()
                beta = (2 * u) ** (1 / (eta_c + 1)) if u <= 0.5 else (1 / (2 * (1 - u))) ** (1 / (eta_c + 1))
                c1[i] = 0.5 * ((1 + beta) * p1[i] + (1 - beta) * p2[i])
                c2[i] = 0.5 * ((1 - beta) * p1[i] + (1 + beta) * p2[i])
    for c in (c1, c2):
        for i in range(c.size):
            if rng.random() < 1.0 / c.size:
                u = rng.random()
                dl = (2 * u) ** (1 / (eta_m + 1)) - 1 if u < 0.5 else 1 - (2 * (1 - u)) ** (1 / (eta_m + 1))
                c[i] += dl
    return np.clip(c1, 0, 1), np.clip(c2, 0, 1)


def initial_population(n, rng):
    """Latin hypercube, plus one uniform/no-lock design per categorical pattern as anchors."""
    P = (rng.permuted(np.tile(np.arange(n), (N_GENES, 1)), axis=1).T + rng.random((n, N_GENES))) / n
    for k, pat in enumerate(PATTERNS[: min(n, len(PATTERNS))]):
        P[k, 1] = (k + 0.5) / len(PATTERNS)
    return P


# --------------------------------------------------------------------------------------------------
def evaluate(pop, gen, first_id, P, ex, csv, t0, reps=2):
    tasks = []
    for i, g in enumerate(pop):
        did = first_id + i
        for r in range(reps):
            tasks.append(dict(genes=list(map(float, g)), design=did, gen=gen, rep=r, seed=20000 + 16 * did + r,
                              axis=r % 2, W=P["W"], fail=P["fail"], G_skip=P.get("G_skip", (0.0, np.inf))))
    # slow (floppy, low-z) systems first so the pool stays busy at the end
    tasks.sort(key=lambda t: decode(t["genes"], P["W"])["z"])
    rows = []
    futs = [ex.submit(_worker, t) for t in tasks]
    for n, f in enumerate(as_completed(futs)):
        row = f.result()
        rows.append(row)
        pd.DataFrame([row]).to_csv(csv, mode="a", header=not csv.exists(), index=False)
        if (n + 1) % max(1, len(tasks) // 8) == 0 or n + 1 == len(tasks):
            print(f"  gen {gen}: {n + 1}/{len(tasks)} ({row['seconds']:.0f}s, wall {time.time() - t0:.0f}s)",
                  flush=True)
    return rows


def run_ga(P, tag, seed, reps):
    band = load_band()
    P = dict(P, G_skip=(band["G_lo"] / 3, band["G_hi"] * 3))
    rng = np.random.default_rng(seed)
    OUT.mkdir(parents=True, exist_ok=True)
    ecsv, dcsv = OUT / f"{tag}_evals.csv", OUT / f"{tag}_designs.csv"
    ecsv.unlink(missing_ok=True); dcsv.unlink(missing_ok=True)
    (OUT / f"{tag}_params.json").write_text(json.dumps(dict(P, reps=reps, seed=seed, band=band, obj=OBJ,
                                                            S_pa=S_PA), indent=1))
    t0 = time.time()
    deadline = t0 + P.get("budget_s", 1e12)
    with ProcessPoolExecutor(P["workers"]) as ex:
        pop = initial_population(P["pop"], rng)
        rows = evaluate(pop, 0, 0, P, ex, ecsv, t0, reps)
        archive = aggregate(rows, band)
        archive["rank"] = nondominated_sort(objective_matrix(archive), archive["viol"].to_numpy())
        archive.to_csv(dcsv, index=False)
        parents = archive
        next_id = len(archive)
        gen_times = [time.time() - t0]
        for gen in range(1, P["gens"]):
            if time.time() + 1.1 * max(gen_times) > deadline:
                print(f"stopping before gen {gen}: time budget", flush=True)
                break
            tg = time.time()
            F, V = objective_matrix(parents), parents["viol"].to_numpy()
            rank = nondominated_sort(F, V)
            cd = crowding(F, rank)
            genes = np.array([json.loads(s) for s in parents["genes"]])

            def tour():
                i, j = rng.integers(len(parents), size=2)
                return i if (rank[i], -cd[i]) < (rank[j], -cd[j]) else j

            kids = []
            while len(kids) < P["pop"]:
                c1, c2 = sbx_pm(genes[tour()], genes[tour()], rng)
                kids += [c1, c2]
            kids = np.array(kids[: P["pop"]])
            rows = evaluate(kids, gen, next_id, P, ex, ecsv, t0, reps)
            next_id += len(kids)
            off = aggregate(rows, band)
            union = pd.concat([parents.drop(columns=["rank"], errors="ignore"), off], ignore_index=True)
            F, V = objective_matrix(union), union["viol"].to_numpy()
            rank = nondominated_sort(F, V)
            cd = crowding(F, rank)
            order = np.lexsort((-cd, rank))[: P["pop"]]
            parents = union.iloc[order].reset_index(drop=True)
            parents["rank"] = rank[order]
            # rewrite designs file with every design ever evaluated and its rank in the full archive
            archive = pd.concat([archive.drop(columns=["rank"]), off], ignore_index=True)
            archive["rank"] = nondominated_sort(objective_matrix(archive), archive["viol"].to_numpy())
            archive.to_csv(dcsv, index=False)
            gen_times.append(time.time() - tg)
            nf = int(((archive["rank"] == 0) & (archive["viol"] == 0)).sum())
            print(f"gen {gen} done in {gen_times[-1]:.0f}s; archive {len(archive)} designs, "
                  f"{nf} feasible non-dominated", flush=True)
    print("wrote", dcsv, flush=True)


BASELINE_Z = [3.2, 3.4, 3.6, 3.8]


def run_reeval(src, P, tag, reps, only_front=True, baselines=True, max_designs=None):
    """Re-evaluate designs (default: the feasible non-dominated set) at another W / more realisations, plus
    plain uniform, unlocked baselines at the median front pore size (src_design = -1)."""
    band = load_band()
    P = dict(P, G_skip=(0.0, np.inf))
    d = pd.read_csv(src)
    if only_front:
        d = d[(d["rank"] == 0) & (d["viol"] == 0)].reset_index(drop=True)
    if max_designs and len(d) > max_designs:  # best on each objective, then the most spread-out (crowding)
        F = objective_matrix(d)
        keep = list(dict.fromkeys(int(np.argmin(F[:, m])) for m in range(F.shape[1])))
        cd = crowding(F, np.zeros(len(d), int))
        for i in np.argsort(-cd, kind="stable"):
            if len(keep) >= max_designs:
                break
            if int(i) not in keep:
                keep.append(int(i))
        d = d.iloc[sorted(keep)].reset_index(drop=True)
    if baselines and len(d):
        W0 = int(d["W"].iloc[0])
        g6 = float(np.median([(r - 1.0) / (W0 / 4 - 1) for r in d["pore"]]))
        base = [json.dumps([(z - 2.6) / 2.4, 0.1, 0.5, 0.5, 0.0, 0.1, g6]) for z in BASELINE_Z]
        d = pd.concat([d, pd.DataFrame(dict(genes=base, design=-1))], ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    ecsv, dcsv = OUT / f"{tag}_evals.csv", OUT / f"{tag}_designs.csv"
    ecsv.unlink(missing_ok=True)
    t0 = time.time()
    pop = np.array([json.loads(s) for s in d["genes"]])
    with ProcessPoolExecutor(P["workers"]) as ex:
        tasks_rows = evaluate(pop, -1, 0, P, ex, ecsv, t0, reps)
    agg = aggregate(tasks_rows, band)
    agg["src_design"] = d["design"].to_numpy()[agg["design"].to_numpy()]
    agg["rank"] = nondominated_sort(objective_matrix(agg), agg["viol"].to_numpy())
    agg.to_csv(dcsv, index=False)
    print("wrote", dcsv, flush=True)


# --------------------------------------------------------------------------------------------------
# stiffness band from the cell model
# --------------------------------------------------------------------------------------------------
def calibrate_yap(clutch_T=40.0):
    """Steady YAP vs a strain-independent matrix modulus E, using oxt/cell.py unchanged.

    The band is where YAP is most responsive: E between the points where Y crosses 25% and 75% of its
    range over the grid.  A cell on matrix inside the band can read stiffness changes; below it YAP is off
    whatever the matrix does, above it YAP is saturated.  This is a model assumption, not a measurement."""
    from oxt.cell import CellModel, ClutchParams, MatrixCurve, nuc_cyto_ratio

    E = np.logspace(0, 4.5, 28)
    strain = np.array([0.0, 0.05, 0.2, 0.5])
    curve = MatrixCurve(strain, np.repeat(E[:, None], strain.size, 1), np.full(E.size, 0.2))
    cm = CellModel(curve, ClutchParams(T=clutch_T), seed=0)
    ss = cm.steady_state(np.ones(E.size))
    Y = ss["Y"]
    df = pd.DataFrame(dict(E_Pa=E, G_model=E / (3 * S_PA), Y=Y, YAP_NC=nuc_cyto_ratio(Y),
                           prestress_ratio=ss["prestress_ratio"], mc_F=ss["mc_F"], M=ss["M"]))
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "yap_calibration.csv", index=False)
    ylo, yhi = Y.min(), Y.max()
    lE = np.log10(E)
    Ys = np.maximum.accumulate(Y)  # monotone envelope for interpolation
    q = lambda frac: float(10 ** np.interp(ylo + frac * (yhi - ylo), Ys, lE))
    E_lo, E_hi = q(0.25), q(0.75)
    band = dict(E_lo_Pa=E_lo, E_hi_Pa=E_hi, G_lo=E_lo / (3 * S_PA), G_hi=E_hi / (3 * S_PA), S_pa=S_PA,
                Y_min=float(ylo), Y_max=float(yhi), clutch_T=clutch_T,
                note="E where steady YAP crosses 25%..75% of its range in oxt/cell.py; model assumption")
    (OUT / "yap_band.json").write_text(json.dumps(band, indent=1))
    print(df.to_string(index=False))
    print(json.dumps(band, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="smoke", choices=PROFILES)
    ap.add_argument("--W", type=int)
    ap.add_argument("--pop", type=int)
    ap.add_argument("--gens", type=int)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--budget-min", type=float, default=40.0, help="stop starting new generations after this")
    ap.add_argument("--tag")
    ap.add_argument("--calibrate-yap", action="store_true")
    ap.add_argument("--reeval", help="designs CSV whose rank-0 designs are re-evaluated")
    ap.add_argument("--linear-only", action="store_true", help="skip the rupture pull (quick checks)")
    ap.add_argument("--max-designs", type=int, help="re-evaluate at most this many front designs")
    a = ap.parse_args()
    if a.calibrate_yap:
        return calibrate_yap()
    P = dict(PROFILES[a.profile])
    for k in ("W", "pop", "gens", "workers"):
        if getattr(a, k):
            P[k] = getattr(a, k)
    P["budget_s"] = a.budget_min * 60
    if a.linear_only:
        P["fail"] = []
    tag = a.tag or a.profile
    if a.reeval:
        return run_reeval(a.reeval, P, tag, a.reps, max_designs=a.max_designs)
    run_ga(P, tag, a.seed, a.reps)


if __name__ == "__main__":
    main()
