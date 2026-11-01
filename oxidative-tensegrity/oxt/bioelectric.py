"""Matrix stiffness *distributions* -> cell mechanics -> a gap-junction-coupled membrane-potential (Vmem) sheet.

Question: ageing keratinocytes depolarise, lose within-culture Vmem heterogeneity, gain between-culture
heterogeneity and lose spatial clustering (global Moran's I; Sediqi & Levin, iScience 2025).  If cells read the
matrix, does the *distribution* of local collagen stiffness that oxidative/AGE crosslinks produce push a coupled
Vmem sheet the same way, and does it change the sheet's ability to hold and restore a bioelectric pattern?

Pipeline (all parts are model assumptions, not fits):
  1. local stiffness map: under a global shear gamma, the network's elastic energy is split onto nodes and binned
     into P x P patches (one patch = one cell footprint).  G_loc(gamma) = 2 dE_patch / (gamma^2 A_patch) is an
     energy-equivalent secant modulus; its patch mean equals the global energy modulus exactly.
  2. per-cell mechanics: each patch's secant curve goes through the existing motor-clutch + tabulated tensegrity
     cell (oxt.organoid.cell_steady_state) -> traction F_i, prestress ratio PS_i, YAP Y_i.
  3. Vmem sheet on the P x P periodic grid:
       dV_i/dt = -gK(V_i) (V_i - E_K) - gL (V_i - E_L) - gM_i (V_i - E_cat) + sum_j G_ij (V_j - V_i)
     gK(V) is inward-rectifier-like (conducts when hyperpolarised), which makes single cells bistable, as in
     bistable Vmem models of non-excitable cells (e.g. Cervera, Meseguer & Mafe, Sci Rep 2016).
     gM_i = gM_max * hill(F_i, F50, 4): a stretch-activated cation current driven by adhesion traction (Piezo-like).
     G_ij = G0 (const) or G0 * sqrt(h(PS_i) h(PS_j)) (junction stabilisation needs cytoskeletal prestress).
  Depolarisation on stiffer matrix is therefore partly built in through gM.  What the model adds is how the
  *distribution and spatial structure* of stiffness shape heterogeneity, clustering and pattern memory, tested
  against shuffled-field and uniform-field controls that keep the mean (or the whole distribution) fixed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch

from .network import Batch, Lattice


# --------------------------------------------------------------------------------------------------
# 1. local stiffness maps from the fibre network
# --------------------------------------------------------------------------------------------------
def node_energy(b: Batch, x, F):
    """Elastic energy per node (B, N): bond terms split half to each end, bending and junction-angle terms
    assigned to their vertex node, GAG tether to its node.  Sums to Batch.energy(x, F, per_system=True)."""
    d = b.bond_vectors(x, F)
    ln = torch.linalg.norm(d, dim=-1)
    a = b.alive.to(b.dtype)
    eb = 0.5 * (b.mu * a + b.mu_el) * (ln - 1.0) ** 2
    N = b.X.shape[0]
    e = torch.zeros(b.B, N, dtype=b.dtype, device=b.device)
    e.index_add_(1, b.bi, 0.5 * eb)
    e.index_add_(1, b.bj, 0.5 * eb)

    din, dout = d[:, b.bend_in], d[:, b.bend_out]
    th = torch.atan2(din[..., 0] * dout[..., 1] - din[..., 1] * dout[..., 0], (din * dout).sum(-1))
    kp = b.kappa * torch.sqrt(b.kb[:, b.bend_in] * b.kb[:, b.bend_out]) * a[:, b.bend_in] * a[:, b.bend_out]
    bend_node = torch.as_tensor(b.lat.bend_node, device=b.device)
    e.index_add_(1, bend_node, 0.5 * kp * th ** 2)

    u = d[:, b.ang_u] * b.ang_su[None, :, None]
    v = d[:, b.ang_v] * b.ang_sv[None, :, None]
    phi = torch.atan2(u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0], (u * v).sum(-1))
    kq = b.kx[:, b.ang_node] * a[:, b.ang_u] * a[:, b.ang_v]
    e.index_add_(1, b.ang_node, 0.5 * kq * (phi - math.pi / 3) ** 2)

    xa = b.X[None] @ F.transpose(1, 2)
    e = e + 0.5 * (b.k_gag[:, :, 0] * ((x - xa) ** 2).sum(-1))
    return e


def patch_index(lat: Lattice, P: int):
    """Patch id (0..P*P-1) of every node, binning reference positions into a P x P grid."""
    fx = np.floor(lat.X[:, 0] / lat.L[0] * P).astype(int) % P
    fy = np.floor(lat.X[:, 1] / lat.L[1] * P).astype(int) % P
    return fy * P + fx


def local_shear_maps(b: Batch, P: int, gammas):
    """Shear the batch through `gammas` (increasing) and return G_loc (B, n_gamma, P*P) in lattice units,
    plus the global energy modulus (B, n_gamma).  Requires zero prestrain (energy is zero at rest)."""
    pid = torch.as_tensor(patch_index(b.lat, P), device=b.device)
    A = b.lat.area / (P * P)
    Fp = b.F0.clone()
    b.relax(Fp)
    with torch.no_grad():
        e0 = node_energy(b, b.x, Fp)
    out, glob = [], []
    for g in gammas:
        F = b.F_shear(g)
        b.move_affine(Fp, F)
        b.relax(F)
        with torch.no_grad():
            de = node_energy(b, b.x, F) - e0
            ep = torch.zeros(b.B, P * P, dtype=b.dtype, device=b.device).index_add_(1, pid, de)
        out.append((2 * ep / (g * g * A)).cpu().numpy())
        glob.append((2 * de.sum(1) / (g * g * b.lat.area)).cpu().numpy())
        Fp = F
    return np.stack(out, 1), np.stack(glob, 1)


def morans_I(f):
    """Global Moran's I on a periodic P x P grid with rook (4-neighbour) weights. f: (..., P, P)."""
    z = f - f.mean(axis=(-2, -1), keepdims=True)
    lag = sum(np.roll(z, s, axis=ax) for ax in (-2, -1) for s in (1, -1))
    num = (z * lag).sum(axis=(-2, -1)) / 4.0
    den = (z * z).sum(axis=(-2, -1))
    return np.where(den > 1e-12, num / np.maximum(den, 1e-30), np.nan)


# --------------------------------------------------------------------------------------------------
# 3. coupled Vmem sheet
# --------------------------------------------------------------------------------------------------
@dataclass
class VmemParams:
    E_K: float = -85.0       # mV
    E_L: float = 0.0         # mV, lumped Na/Cl leak
    E_cat: float = 0.0       # mV, stretch-activated cation channel
    gK_max: float = 1.0      # inward-rectifier-like K conductance (relative units)
    V_half: float = -40.0    # mV, gK = gK_max / 2
    V_slope: float = 5.0     # mV
    gL: float = 0.25
    gM_max: float = 0.6      # stretch-activated conductance at saturating traction
    F50: float = 400.0       # pN; mid-range of the clutch traction (~200-500 pN in results/cpu32/cell.csv); swept
    nF: float = 4.0
    ps50: float = 0.5        # prestress ratio for half-maximal junction stabilisation
    F_unc: float = 400.0     # pN traction at which stress halves junction conductance (stress_uncouple mode)
    G0: float = 1.0          # gap-junction conductance per neighbour pair
    gj_mode: str = "prestress"  # "const" | "prestress" | "stress_uncouple"
    dt: float = 0.05
    T: float = 200.0         # relaxation time (units of membrane time constant)
    V_depol: float = -35.0   # threshold used to call a cell depolarised
    sigma: float = 2.0       # mV / sqrt(time unit), membrane current noise for the information run
    T_info: float = 200.0    # length of the noisy stationary run
    sample: float = 0.25     # sampling interval for the information measures (time units, ~ membrane time)


def _hill(x, k, n=2.0):
    x = np.maximum(x, 0)
    return x ** n / (x ** n + k ** n)


def conductances(F, PS, vp: VmemParams):
    """F, PS: (S, P, P).  Returns gM (S,P,P) and edge conductances Gx, Gy to the +x / +y neighbour.
    Junction modes: const; prestress (stabilised by cytoskeletal prestress); stress_uncouple (stabilised by
    prestress but closed by high traction, a proxy for stress/Ca2+-driven connexin closure: biphasic in stiffness)."""
    gM = vp.gM_max * _hill(F, vp.F50, vp.nF)
    if vp.gj_mode == "const":
        h = np.ones_like(PS)
    elif vp.gj_mode == "prestress":
        h = _hill(PS, vp.ps50)
    elif vp.gj_mode == "stress_uncouple":
        h = _hill(PS, vp.ps50) * (1 - _hill(F, vp.F_unc, 4.0))
    else:
        raise ValueError(vp.gj_mode)
    Gx = vp.G0 * np.sqrt(h * np.roll(h, -1, axis=-1))
    Gy = vp.G0 * np.sqrt(h * np.roll(h, -1, axis=-2))
    return gM, Gx, Gy


def simulate_sheet(V0, gM, Gx, Gy, vp: VmemParams, T=None, clamp=None, device="cpu", noise=0.0, seed=0,
                   record_every=0):
    """Euler(-Maruyama) on all sheets at once. V0, gM, Gx, Gy: (S, P, P).  clamp: optional (mask, value) arrays
    held fixed during the run (used to write a pattern).  noise: sigma in mV/sqrt(time).  record_every > 0 also
    returns frames (n, S, P, P) as float32.  Returns final V (S, P, P) [, frames]."""
    t = lambda a: torch.as_tensor(np.asarray(a), dtype=torch.float64, device=device)
    V, gM, Gx, Gy = t(V0).clone(), t(gM), t(Gx), t(Gy)
    if clamp is not None:
        cm, cv = t(clamp[0]).bool(), t(clamp[1])
    gen = torch.Generator(device=device).manual_seed(seed) if noise > 0 else None
    amp = noise * math.sqrt(vp.dt)
    steps = int((T or vp.T) / vp.dt)
    frames = []
    for k in range(steps):
        gK = vp.gK_max / (1 + torch.exp((V - vp.V_half) / vp.V_slope))
        I = -gK * (V - vp.E_K) - vp.gL * (V - vp.E_L) - gM * (V - vp.E_cat)
        I = I + Gx * (torch.roll(V, -1, -1) - V) + torch.roll(Gx, 1, -1) * (torch.roll(V, 1, -1) - V)
        I = I + Gy * (torch.roll(V, -1, -2) - V) + torch.roll(Gy, 1, -2) * (torch.roll(V, 1, -2) - V)
        V = V + vp.dt * I
        if noise > 0:
            V = V + amp * torch.randn(V.shape, generator=gen, dtype=V.dtype, device=device)
        if clamp is not None:
            V = torch.where(cm, cv, V)
        if record_every and (k + 1) % record_every == 0:
            frames.append(V.float())
    if record_every:
        return V.cpu().numpy(), torch.stack(frames)
    return V.cpu().numpy()


def gaussian_info(frames):
    """Gaussian (linear) information measures from a stationary noisy run, history length 1, in nats.
    frames: torch (n, S, P, P).  Returns per-sheet means of
      AIS  active information storage  I(V_i,t ; V_i,t+1) = -0.5 ln(1 - rho_1^2)
      TE   transfer entropy from each of the 4 neighbours j -> i:
           0.5 ln( var(V_i,t+1 | V_i,t) / var(V_i,t+1 | V_i,t, V_j,t) )
    Gaussian estimators: exact for a linear-Gaussian process, a lower-bound proxy otherwise."""
    X = frames.double()
    X = X - X.mean(0, keepdim=True)
    a, b = X[:-1], X[1:]
    c = lambda u, v: (u * v).mean(0)
    vaa, vbb, vab = c(a, a), c(b, b), c(a, b)
    eps = 1e-12
    rho2 = (vab ** 2 / (vaa * vbb + eps)).clamp(max=1 - 1e-9)
    ais = -0.5 * torch.log(1 - rho2)
    res_b_a = vbb - vab ** 2 / (vaa + eps)                # var(X'|X)
    te = []
    for ax, sh in ((-1, 1), (-1, -1), (-2, 1), (-2, -1)):
        y = torch.roll(a, sh, ax)
        vyy, vay, vby = c(y, y), c(a, y), c(b, y)
        det = vaa * vyy - vay ** 2 + eps                   # var(X'|X,Y) by the 2x2 Schur complement
        res = vbb - (vab ** 2 * vyy - 2 * vab * vby * vay + vby ** 2 * vaa) / det
        te.append(0.5 * torch.log((res_b_a + eps) / (res.clamp(min=eps) + eps)))
    te = torch.stack(te).mean(0)
    vbar = frames.double().mean(0)
    return ais.mean((-2, -1)).cpu().numpy(), te.mean((-2, -1)).cpu().numpy(), vbar.cpu().numpy()


def pattern_target(P):
    """A two-domain prepattern: central disk depolarised (+1), surround hyperpolarised (-1)."""
    yy, xx = np.mgrid[0:P, 0:P]
    r = np.hypot(xx - (P - 1) / 2, yy - (P - 1) / 2)
    return np.where(r <= P / 4, 1.0, -1.0)


def sheet_metrics(V, vp: VmemParams):
    S = V.shape[0]
    flat = V.reshape(S, -1)
    return dict(V_mean=flat.mean(1), V_sd=flat.std(1), frac_depol=(flat > vp.V_depol).mean(1),
                moran_V=morans_I(V))


def _corr_rows(x, y):
    x = x - x.mean(1, keepdims=True)
    y = y - y.mean(1, keepdims=True)
    den = np.sqrt((x * x).sum(1) * (y * y).sum(1))
    return np.where(den > 1e-12, (x * y).sum(1) / np.maximum(den, 1e-30), np.nan)


def run_protocols(F, PS, vp: VmemParams, rng, device="cpu", flips=(0.1, 0.25), logE=None, seed=0):
    """F, PS: (S, P, P).  Protocols on every sheet:
      rest      start hyperpolarised (-70 mV +- 5) and relax (noise-free) -> distribution metrics
      memory    clamp the two-domain prepattern for T/4, release for T -> overlap q_hold with the target
      restore   flip a random fraction f of cells of the held pattern, relax for T -> q_restore_f, q_flipped_f and
                net_heal_f = q_restore_f - q_flipped_f (restoration beyond the un-healed flipped baseline)
      info      from the rest state, a noisy stationary run -> AIS, TE (Gaussian) and, if logE (S, P*P) is given,
                the across-cell correlation and Gaussian MI between local log stiffness and time-mean Vmem
    Overlap q = balanced accuracy - 1 against the target: 1 = perfect, 0 = pattern lost (uniform sheet)."""
    S, P, _ = F.shape
    gM, Gx, Gy = conductances(F, PS, vp)
    V0 = -70.0 + 5.0 * rng.standard_normal((S, P, P))
    Vr = simulate_sheet(V0, gM, Gx, Gy, vp, device=device)
    out = sheet_metrics(Vr, vp)

    tgt = pattern_target(P)
    Vt = np.where(tgt > 0, -5.0, -70.0)[None].repeat(S, 0)
    Vw = simulate_sheet(Vt, gM, Gx, Gy, vp, T=vp.T / 4, clamp=(np.ones_like(Vt), Vt), device=device)
    Vh = simulate_sheet(Vw, gM, Gx, Gy, vp, device=device)
    pos, neg = (tgt > 0).ravel(), (tgt < 0).ravel()

    def q(V):  # balanced: (hit rate in the disk + hit rate in the surround) - 1; a uniform sheet scores 0
        up = (V > vp.V_half).reshape(S, -1)
        return up[:, pos].mean(1) + (~up[:, neg]).mean(1) - 1.0
    out["q_hold"] = q(Vh)
    for f in flips:
        flip = rng.random((S, P, P)) < f
        Vf = np.where(flip, np.where(Vh > vp.V_half, -70.0, -5.0), Vh)
        tag = f"{int(round(f * 100))}"
        out[f"q_flipped_{tag}"] = q(Vf)
        out[f"q_restore_{tag}"] = q(simulate_sheet(Vf, gM, Gx, Gy, vp, device=device))
        out[f"net_heal_{tag}"] = out[f"q_restore_{tag}"] - out[f"q_flipped_{tag}"]

    if vp.sigma > 0:
        every = max(1, int(round(vp.sample / vp.dt)))
        _, frames = simulate_sheet(Vr, gM, Gx, Gy, vp, T=vp.T_info, device=device, noise=vp.sigma, seed=seed,
                                   record_every=every)
        ais, te, vbar = gaussian_info(frames)
        out["AIS"], out["TE"] = ais, te
        out["V_noise_sd"] = frames.double().std(0).mean((-2, -1)).cpu().numpy()
        if logE is not None:
            r = _corr_rows(logE.reshape(S, -1), vbar.reshape(S, -1))
            out["r_EV"] = r
            out["MI_EV"] = -0.5 * np.log(np.clip(1 - r ** 2, 1e-9, None))
        del frames
    return out, Vr
