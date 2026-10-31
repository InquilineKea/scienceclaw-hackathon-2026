"""Tests for the 3D architecture-atlas extensions (oxt/network3d.py fixes + oxt/fiber3d.py).

Fast CPU only (W=3-4, single-digit seconds per test); the GPU profiles are exercised
on the H100, never on the Mac host.
"""
import numpy as np
import torch

from oxt.network3d import (Lattice3D, Design3D, build_network3d, Batch3D, curve_lattice,
                           hessian_moduli)
from oxt.fiber3d import (FiberDesign, build_fiber_network, FiberBatch, fiber_hessian_moduli)

torch.set_num_threads(2)


def test_crack_plane_finds_crossing_bonds():
    """Regression: the plane used to sit exactly on an FCC node layer (x = L/2 is a
    lattice site plane), finding ZERO crossing bonds and T(delta) == 0 identically."""
    lat = Lattice3D(3)
    crossing, sign, _q = lat.crack_plane(0)
    assert crossing.sum() > 50
    # every FCC lattice bond is outgoing along +AXES (bond x-displacement >= 0), so a
    # bond straddling the plane always starts below it and its imaged end lies above:
    # sign is uniformly +1 (both-sign sets occur only in oxt/fiber3d, whose chain bonds
    # run in arbitrary directions).
    assert np.all(sign[crossing] == 1.0)
    spec, info = build_network3d(lat, Design3D(z=3.4, arch="aligned", lock=0.08),
                                np.random.default_rng(7))
    assert (spec.alive & crossing).sum() > 5
    b = Batch3D(lat, [spec], device="cpu", crack_axis=0, relax_kw=dict(max_rounds=10, iters=100))
    F = b.F0.clone()
    j = torch.zeros(1, 3, dtype=torch.float64)
    b.relax(F, jump=j)
    j[:, 0] = 0.10
    b.relax(F, jump=j)
    T = b.traction(F, j).numpy()
    assert np.abs(T[0, 0]) > 1e-6, "cohesive traction must be nonzero after the fix"


def test_energy_gradient_matches_finite_differences():
    """Regression: the validate check used to divide by max|FD| over sampled points but
    take max|g-FD| over ALL coordinates (unsampled FD entries are 0) -> false failure."""
    lat = Lattice3D(3)
    spec, _ = build_network3d(lat, Design3D(z=3.4, arch="aligned", lock=0.08),
                              np.random.default_rng(7))
    b = Batch3D(lat, [spec], device="cpu")
    F = torch.eye(3, dtype=torch.float64)[None] * 1.03
    F[0, 0, 1] = 0.02
    x = (b.X[None] @ F.transpose(1, 2)).clone() + 0.05 * torch.randn(1, lat.N, 3,
                                                                     dtype=torch.float64)
    x = x.requires_grad_(True)
    b.energy(x, F).backward()
    g = x.grad.numpy().ravel()
    ps = np.random.default_rng(0).choice(g.size, 25, replace=False)
    gn = {}
    h = 1e-6
    for p in ps:
        xp = x.detach().clone(); xp.reshape(-1)[p] += h
        xm = x.detach().clone(); xm.reshape(-1)[p] -= h
        gn[p] = (float(b.energy(xp, F)) - float(b.energy(xm, F))) / (2 * h)
    err = max(abs(g[p] - gn[p]) for p in ps) / max(abs(gn[p]) for p in ps)
    assert err < 1e-6


def test_phantom_family_matches_z_and_keeps_fibres():
    lat = Lattice3D(4)
    spec, info = build_network3d(lat, Design3D(z=3.4, arch="uniform", family="phantom",
                                              lock=0.08), np.random.default_rng(3))
    assert abs(info["z_realized"] - 3.4) < 0.15
    # The phantom family's defining property is the ABSENCE of the one-cut-per-fibre-line
    # rule, not "some line survives intact": at z=3.4 a retention probability of ~0.28
    # leaves an 8-bond FCC line fully alive with probability ~4e-5, so "full lines" is
    # statistically empty even without any forced cut.  Probe the rule deterministically
    # at z=12 (p=1, no random removal): phantom keeps every line whole; diluted cuts
    # every line exactly once.
    spec_ph, info_ph = build_network3d(lat, Design3D(z=12.0, arch="uniform", family="phantom"),
                                        np.random.default_rng(3))
    assert info_ph["z_realized"] == 12.0
    for line in range(lat.n_lines):
        members = np.flatnonzero(lat.line == line)
        if members.size > 1:
            assert spec_ph.alive[members].all(), "phantom: no line is ever force-cut"
    spec_di, info_di = build_network3d(lat, Design3D(z=12.0, arch="uniform", family="diluted"),
                                       np.random.default_rng(3))
    assert info_di["z_realized"] < 12.0
    for line in range(lat.n_lines):
        members = np.flatnonzero(lat.line == line)
        if members.size > 1:
            assert (~spec_di.alive[members]).sum() == 1, \
                "diluted: exactly the one forced cut per line at p=1"


def test_curved_lattice_is_stress_free_and_softens():
    lat = curve_lattice(Lattice3D(4), 0.15, np.random.default_rng(42))
    assert 1.0 < lat.rest_len.mean() < 1.05          # waviness slightly lengthens bonds
    assert np.abs(lat.bend_theta0).max() > 0.05       # reference has finite rest angles
    spec, info = build_network3d(lat, Design3D(z=3.4, arch="aligned", lock=0.08),
                                 np.random.default_rng(7))
    b = Batch3D(lat, [spec], device="cpu", relax_kw=dict(max_rounds=20, iters=150))
    fmax = b.relax(b.F0)
    P = b.stress(b.F0)
    assert float(P.abs().max()) < 1e-9, "curved reference must be stress-free"
    m = hessian_moduli(lat, spec, device="cpu")
    assert m["G"] > 0 and m["Cx"] > 0


def test_fiber3d_matching_and_rest_state():
    W = 4
    box_L = (2 * 2 ** 0.5 * W ** 3) ** (1 / 3)
    fd = FiberDesign(n_fib=32, n_seg=7, p_align=0.35, curve_sigma=0.3, z=3.4,
                     lock=0.08, lock_place="crossings", xlink_dist="clustered")
    net = build_fiber_network(fd, np.random.default_rng(0), box_L, 4 * W ** 3)
    info = net["info"]
    assert abs(info["z_realized"] - info["z_target"]) < 0.15
    assert info["node_match"] < 0.05
    fb = FiberBatch([net], device="cpu")
    x = fb.X.clone().requires_grad_(True)
    e = fb.energy(x, fb.F0)
    e.backward()
    assert float(e.detach()) < 1e-20 and float(x.grad.abs().max()) < 1e-12


def test_fiber3d_moduli_and_failure():
    W = 4
    box_L = (2 * 2 ** 0.5 * W ** 3) ** (1 / 3)
    fd = FiberDesign(n_fib=16, n_seg=7, p_align=0.35, curve_sigma=0.0, z=3.4, lock=0.08)
    net = build_fiber_network(fd, np.random.default_rng(1), box_L, 4 * W ** 3)
    m = fiber_hessian_moduli(net, device="cpu")
    assert all(m[k] > 0 for k in ("G", "Cx", "Cy", "Cz", "Gyz", "Gzx"))
    fb = FiberBatch([net], device="cpu", relax_kw=dict(max_rounds=15, iters=120))
    res = fb.failure_curve([0.05, 0.15, 0.30], axis=0)
    assert res["sig"].shape == (1, 3)
    assert np.isfinite(res["sig"]).all()
    coh = fb.cohesive_curve([0.05, 0.15, 0.30], mode="tension")
    assert np.isfinite(coh["Teff"]).all()


if __name__ == "__main__":
    for name, fn in sorted({k: v for k, v in globals().items()
                            if k.startswith("test_")}.items()):
        fn()
        print(f"PASS {name}", flush=True)
    print("all atlas3d tests passed")
