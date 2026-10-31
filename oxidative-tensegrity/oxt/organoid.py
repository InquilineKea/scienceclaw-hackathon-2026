"""Organoid embedded in a collagen gel: network mechanics -> tensegrity cell -> YAP/MRTF -> gene program.

An epithelial organoid (one cell layer, basal side on the gel) grows inside a fibre network.  Growth strains the
surrounding gel (hoop strain at the interface eps = R/R0 - 1, larger at buds), so the cells read the gel's
*nonlinear* stress-strain curve at that pre-strain, not its linear modulus.  Each cell runs the motor-clutch +
6-strut tensegrity model from oxt/cell.py; nuclear YAP and an MRTF proxy (transmitted prestress) drive a small
gene-regulatory network with matrix feedback (LOX crosslinks, MMP14 degradation) and Wnt delivery through the gel.

Everything in GENES / OrganoidParams is a model assumption chosen from the qualitative literature (YAP-TEAD
targets CTGF/CYR61/ANKRD1, AMOTL2 negative feedback, YAP-high fetal/regenerative state in intestinal organoids,
Gjorevski 2016 stiffness-dependent stem expansion), not a fit to data.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch

from .cell import KBT, ClutchParams, CellParams, MatrixCurve, TensegrityCell, hill, k_adhesion, yap_from


# --------------------------------------------------------------------------------------------------
# motor-clutch on torch (same equations as oxt.cell.motor_clutch, batched on GPU)
# --------------------------------------------------------------------------------------------------
def _interp_rows(strain_grid, E_sec, s):
    s = torch.clamp(s, strain_grid[0], strain_grid[-1])
    j = torch.clamp(torch.searchsorted(strain_grid, s.contiguous()) - 1, 0, len(strain_grid) - 2)
    s0, s1 = strain_grid[j], strain_grid[j + 1]
    w = (s - s0) / (s1 - s0)
    r = torch.arange(E_sec.shape[0], device=E_sec.device)
    return E_sec[r, j] * (1 - w) + E_sec[r, j + 1] * w


def motor_clutch_torch(curve: MatrixCurve, n_motor, p: ClutchParams = ClutchParams(), seed=0, device="cpu"):
    g = torch.Generator(device=device).manual_seed(seed)
    dt_ = torch.float32
    sg = torch.as_tensor(curve.strain, dtype=dt_, device=device)
    E = torch.as_tensor(curve.E_sec, dtype=dt_, device=device)
    nm = torch.as_tensor(np.asarray(n_motor, float), dtype=dt_, device=device)
    M, C = E.shape[0], p.n_c_max
    bound = torch.zeros((M, C), dtype=torch.bool, device=device)
    unfolded = torch.zeros_like(bound)
    xc = torch.zeros((M, C), dtype=dt_, device=device)
    rho = torch.ones(M, dtype=dt_, device=device)
    x_sub = torch.zeros(M, dtype=dt_, device=device)
    idx = torch.arange(C, device=device)[None, :]
    steps = int(p.T / p.dt)
    rec0 = steps // 2
    accF = torch.zeros(M, dtype=dt_, device=device)
    accv, accrho, accs, accP = (torch.zeros_like(accF) for _ in range(4))
    kadh = 4 * math.pi * p.a_m / 9 * 1e3
    p_on = 1 - math.exp(-p.k_on * p.dt)
    for t in range(steps):
        strain = x_sub / (p.a_m * 1e9)
        k = kadh * _interp_rows(sg, E, strain)
        F_sub = k * x_sub
        v = torch.clamp(p.v_u * (1 - F_sub / (nm * p.F_m)), min=0)
        xc = torch.where(bound, xc + v[:, None] * p.dt, xc)
        nb = bound.sum(1).to(dt_)
        x_sub = p.kappa_c * (xc * bound).sum(1) / (k + nb * p.kappa_c)
        Fi = torch.where(bound, p.kappa_c * (xc - x_sub[:, None]), torch.zeros_like(xc))
        newly = bound & ~unfolded & (Fi > p.F_talin)
        unfolded |= newly
        rho = torch.clamp(rho + p.d_rho * newly.sum(1) - (rho - 1) / p.tau_rho * p.dt, 1, p.n_c_max / p.n_c)
        koff = p.k_off0 * torch.exp(torch.clamp(Fi, 0, 60) / p.F_b) * torch.where(unfolded, p.koff_reinf, 1.0)
        unbind = bound & (torch.rand((M, C), generator=g, device=device) < 1 - torch.exp(-koff * p.dt))
        avail = idx < (p.n_c * rho)[:, None]
        bind = ~bound & avail & (torch.rand((M, C), generator=g, device=device) < p_on)
        bound = (bound & ~unbind) | bind
        unfolded &= bound
        xc = torch.where(bind, x_sub[:, None].expand_as(xc), xc)
        if t >= rec0:
            accF += F_sub
            accv += v
            accrho += rho
            accs += strain
            accP += F_sub * v
    n = steps - rec0
    out = dict(F=accF / n, v=accv / n, rho=accrho / n, strain=accs / n, P=accP / n)
    out = {k: v.double().cpu().numpy() for k, v in out.items()}
    out["entropy_prod_kB_per_s"] = (out["P"] + np.asarray(n_motor) * p.F_m * out["v"]) / KBT
    out["torn"] = out["strain"] * p.a_m / p.L_field_m > curve.fail_strain
    return out


# --------------------------------------------------------------------------------------------------
# tensegrity prestress table (the 6-strut solve is the slow scalar part; tabulate it once)
# --------------------------------------------------------------------------------------------------
class PrestressTable:
    def __init__(self, n_c=13, n_k=41):
        cell = TensegrityCell(k_cable=1.0)
        self.c = np.linspace(0.02, 0.14, n_c)  # c = c0 * M with M in [1, 1 + beta]
        self.lk = np.linspace(-4, 3, n_k)  # log10 anchor stiffness (cable units)
        tab = np.zeros((n_c, n_k))
        for i, c in enumerate(self.c):
            x0 = None
            for j, lk in enumerate(self.lk):
                r = cell.solve(float(c), 10 ** lk, x0=x0)
                tab[i, j], x0 = r["prestress"], r["x"]
        self.tab = tab
        self.rigid = np.array([cell.solve(float(c), 1e3)["prestress"] for c in self.c])

    def __call__(self, c, k_anchor):
        c = np.clip(c, self.c[0], self.c[-1])
        lk = np.clip(np.log10(np.maximum(k_anchor, 1e-12)), self.lk[0], self.lk[-1])
        fi = np.interp(c, self.c, np.arange(len(self.c)))
        fj = np.interp(lk, self.lk, np.arange(len(self.lk)))
        i0, j0 = np.minimum(fi.astype(int), len(self.c) - 2), np.minimum(fj.astype(int), len(self.lk) - 2)
        wi, wj = fi - i0, fj - j0
        T = self.tab
        ps = (T[i0, j0] * (1 - wi) * (1 - wj) + T[i0 + 1, j0] * wi * (1 - wj)
              + T[i0, j0 + 1] * (1 - wi) * wj + T[i0 + 1, j0 + 1] * wi * wj)
        rig = np.interp(c, self.c, self.rigid)
        return ps / np.maximum(rig, 1e-12)


def cell_steady_state(curve: MatrixCurve, table: PrestressTable, clutch: ClutchParams, cp: CellParams = CellParams(),
                      device="cpu", iters=5, damp=0.6, seed=0):
    """Fixed point M -> Y(M) -> 1 + beta Y, as CellModel.steady_state, with tabulated tensegrity."""
    M = np.ones(curve.E_sec.shape[0])

    def mech(M):
        mc = motor_clutch_torch(curve, clutch.n_m * M, clutch, seed=seed, device=device)
        k_anchor = k_adhesion(curve.E_at(mc["strain"]), 2e-6) * mc["rho"] / cp.k_cable_pN_nm
        ps = table(np.minimum(0.5, cp.c0 * M), k_anchor)
        return dict(Y=yap_from(mc["F"], ps, cp), prestress_ratio=ps, k_anchor=k_anchor,
                    **{f"mc_{k}": v for k, v in mc.items()})

    for _ in range(iters):
        M = damp * (1 + cp.beta * mech(M)["Y"]) + (1 - damp) * M
    out = mech(M)
    out["M"] = M
    return out


# --------------------------------------------------------------------------------------------------
# gel curve seen at a growth pre-strain, with stiffness remodelling factor
# --------------------------------------------------------------------------------------------------
def shifted_curves(strain, E_sec, fail_e, fail_sig, eps_pre, scale):
    """Rows = gels.  Returns E_sec'(s) = scale * D(eps_pre) * E_tangent-ish(s + eps_pre) on the same grid,
    where D is the post-peak retention of the gel's failure curve (1 before peak; <1 once the gel has torn)."""
    G = len(strain)
    Ep = np.empty_like(E_sec)
    s_eval = strain[None, :] + eps_pre[:, None]
    for g in range(G):
        Ep[:, g] = [np.interp(s_eval[r, g], strain, E_sec[r]) for r in range(E_sec.shape[0])]
    # damage retention from the uniaxial failure curve: stress at eps_pre / running max up to eps_pre
    D = np.ones(len(eps_pre))
    for r in range(len(eps_pre)):
        sig = np.interp(eps_pre[r], fail_e, fail_sig[r])
        run = np.max(np.where(fail_e <= eps_pre[r], fail_sig[r], -np.inf), initial=sig)
        D[r] = np.clip(sig / max(run, 1e-12), 0.05, 1.0)
    peak = fail_e[np.argmax(fail_sig, 1)]
    fail_left = np.maximum(peak - eps_pre, 0.01)
    return Ep * (scale * D)[:, None], fail_left, D


# --------------------------------------------------------------------------------------------------
# gene-regulatory network
# --------------------------------------------------------------------------------------------------
# name: (driver, K, n, tau_h)   driver in {Y, PS, W, ...}; see rates() for the combinations
GENES = {
    "CYR61":  ("Y", 0.35, 2, 1.0),    # CCN1, immediate-early YAP-TEAD target
    "CTGF":   ("Y", 0.40, 2, 2.0),    # CCN2
    "ANKRD1": ("Y", 0.60, 4, 4.0),    # switch-like YAP target
    "AMOTL2": ("Y", 0.50, 2, 3.0),    # YAP target that sequesters YAP (negative feedback)
    "ACTA2":  ("PS", 0.75, 4, 12.0),  # MRTF-SRF read-out of transmitted prestress
    "LOX":    ("Y+PS", 0.50, 2, 12.0),  # crosslinking enzyme -> stiffens gel
    "MMP14":  ("Y", 0.50, 2, 8.0),    # MT1-MMP -> degrades gel
    "LY6A":   ("Y", 0.55, 3, 24.0),   # fetal/regenerative (YAP-high) state marker (SCA1/ANXA1 class)
    "LGR5":   ("W-Y", 0.50, 2, 24.0),  # Wnt-dependent crypt stem state; suppressed by high YAP
    "KRT20":  ("diff", 0.40, 2, 24.0),  # differentiated enterocyte-like (low Wnt, low YAP)
    "MKI67":  ("prolif", 0.40, 2, 6.0),
}
GENE_NAMES = list(GENES)


def gene_targets(Y, PS, W):
    t = {}
    for name, (drv, K, n, _) in GENES.items():
        if drv == "Y":
            t[name] = hill(Y, K, n)
        elif drv == "PS":
            t[name] = hill(PS, K, n)
        elif drv == "Y+PS":
            t[name] = 0.5 * hill(Y, K, n) + 0.5 * hill(PS, 0.75, 4)
        elif drv == "W-Y":
            t[name] = hill(W, K, n) * (1 - hill(Y, 0.6, 3))
        elif drv == "diff":
            t[name] = (1 - hill(W, 0.5, 2)) * (1 - hill(Y, K, n))
        elif drv == "prolif":
            t[name] = 0.5 * hill(Y, K, n) + 0.5 * hill(W, K, n)
    return t


@dataclass
class OrganoidParams:
    R0_um: float = 50.0       # embedded radius
    days: float = 7.0
    dt_h: float = 0.1
    g0_per_day: float = 0.25  # max radial growth rate (MKI67 = 1, no confinement)
    tau_plastic_h: float = 24.0  # gel strain relaxes by plastic remodelling; crosslinks slow it:
    xl_plastic_gain: float = 2.0  # tau_p = tau_plastic_h (1 + gain * dose * k_rel)
    sigma_stall_pa: float = 600.0  # confining hoop stress that stalls growth (Alessandri 2013 order)
    bud_amp: float = 0.6      # bud/inter-bud strain contrast: eps_local = eps_hoop (1 + a cos theta)
    n_pos: int = 5            # positions from bud tip (theta=0) to inter-bud (theta=pi)
    k_amotl2: float = 0.8     # Y_eff = Y_mech / (1 + AMOTL2 / k)
    k_lox_per_day: float = 0.25   # stiffening per day at LOX = 1 (log-scale)
    k_mmp_per_day: float = 0.20   # softening per day at MMP14 = 1 (log-scale)
    scale_lo: float = 0.4
    scale_hi: float = 2.5


def wnt_delivery(mesh_rel, age_dose, thickness_um=500.0):
    """Delivered fraction of a Wnt/R-spondin-like ligand through the gel (Ogston sieving + binding), 0..1,
    normalised so a native gel delivers ~0.7."""
    from .physio import R_COLLAGEN_NM, ogston

    phi = np.clip(0.004 / np.maximum(mesh_rel, 0.2) ** 2, 1e-4, 0.2)  # fibre fraction ~ 1/mesh^2
    r, D0, bind, uptake = 2.5, 90.0, 8.0, 5e-5
    hind = np.array([ogston(r, p, R_COLLAGEN_NM) for p in phi])
    D = D0 * hind / (1 + bind * (1 + 2.0 * age_dose))
    lam = np.sqrt(D / uptake)
    x = thickness_um / lam
    return np.clip(1.25 * 2 * np.exp(-x) / (1 + np.exp(-2 * x)), 0, 1)


def simulate_organoids(Y_tab, PS_tab, eps_grid, scale_grid, sig_hoop, W, tau_p_h, xl_dose=None,
                       op: OrganoidParams = OrganoidParams()):
    """Integrate growth + genes + remodelling.

    Y_tab, PS_tab: (Ngel, n_eps, n_scale) steady YAP and prestress ratio from the cell model.
    sig_hoop: (Ngel, n_eps) gel hoop stress (Pa) at each pre-strain for scale 1.
    W: (Ngel,) Wnt delivery.  tau_p_h: (Ngel,) plastic relaxation time of the gel strain.
    xl_dose: (Ngel,) crosslink dose; crosslinked collagen resists MMP cleavage, k_mmp * exp(-2.5 dose)
    (same factor as physio.matrix_recovery_rate).
    The interface hoop strain obeys d eps/dt = (dR/dt)/R - eps/tau_p (viscoplastic gel).
    Returns dict of trajectories sampled daily.
    """
    Ng = Y_tab.shape[0]
    th = np.linspace(0, np.pi, op.n_pos)
    shape = (Ng, op.n_pos)
    R = np.full(Ng, op.R0_um)
    mmp_resist = np.exp(-2.5 * (np.zeros(Ng) if xl_dose is None else np.asarray(xl_dose)))[:, None]
    eps_h = np.zeros(Ng)
    logS = np.zeros(shape)  # per-position remodelling (log stiffness factor)
    genes = {g: np.zeros(shape) for g in GENE_NAMES}
    leps, lsc = np.asarray(eps_grid), np.log(np.asarray(scale_grid))

    def lookup(tab, eps, ls):
        fi = np.interp(eps, leps, np.arange(len(leps)))
        fj = np.interp(ls, lsc, np.arange(len(lsc)))
        i0 = np.minimum(fi.astype(int), len(leps) - 2)
        j0 = np.minimum(fj.astype(int), len(lsc) - 2)
        wi, wj = fi - i0, fj - j0
        gi = np.arange(Ng)[:, None].repeat(op.n_pos, 1)
        return (tab[gi, i0, j0] * (1 - wi) * (1 - wj) + tab[gi, i0 + 1, j0] * wi * (1 - wj)
                + tab[gi, i0, j0 + 1] * (1 - wi) * wj + tab[gi, i0 + 1, j0 + 1] * wi * wj)

    steps = int(op.days * 24 / op.dt_h)
    rec = {k: [] for k in ["R", "eps", "Y", "PS", "logS", *GENE_NAMES]}
    first = True
    for t in range(steps + 1):
        eps = np.clip(eps_h[:, None] * (1 + op.bud_amp * np.cos(th))[None, :], 0, leps[-1])
        ls = np.clip(logS, lsc[0], lsc[-1])
        Ymech = lookup(Y_tab, eps, ls)
        PS = lookup(PS_tab, eps, ls)
        if first:  # start from the self-consistent steady state at zero growth strain (AMOTL2 feedback included)
            for _ in range(60):
                tgt = gene_targets(Ymech / (1 + genes["AMOTL2"] / op.k_amotl2), PS, W[:, None])
                for g in GENE_NAMES:
                    genes[g] = 0.5 * genes[g] + 0.5 * tgt[g]
            first = False
        Yeff = Ymech / (1 + genes["AMOTL2"] / op.k_amotl2)
        tgt = gene_targets(Yeff, PS, W[:, None])
        if t % int(24 / op.dt_h) == 0:
            for k, v in (("R", R), ("eps", eps), ("Y", Yeff), ("PS", PS), ("logS", logS)):
                rec[k].append(v.copy())
            for g in GENE_NAMES:
                rec[g].append(genes[g].copy())
        if t == steps:
            break
        dt = op.dt_h
        for g, (_, _, _, tau) in GENES.items():
            genes[g] += dt / tau * (tgt[g] - genes[g])
        # confining stress: mean over the surface of hoop stress at local strain, times remodelling factor
        sh = np.array([np.interp(eps[i], leps, sig_hoop[i]) for i in range(Ng)]) * np.exp(logS)
        growth = op.g0_per_day / 24 * genes["MKI67"].mean(1) * np.clip(1 - sh.mean(1) / op.sigma_stall_pa, 0, None)
        R = R * (1 + growth * dt)
        eps_h = eps_h + growth * dt - eps_h * dt / tau_p_h
        logS = np.clip(logS + dt / 24 * (op.k_lox_per_day * genes["LOX"] - op.k_mmp_per_day * mmp_resist * genes["MMP14"]),
                       lsc[0], lsc[-1])
    return {k: np.stack(v, 0) for k, v in rec.items()}  # (days+1, Ngel[, n_pos])
