"""Hardware-free checks for oxt/bioelectric.py: python3 -m pytest -q tests/test_bioelectric.py"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from oxt.bioelectric import VmemParams, conductances, local_shear_maps, morans_I, node_energy, simulate_sheet  # noqa: E402
from oxt.materials import COLLAGENS, Damage, build_spec  # noqa: E402
from oxt.network import Batch, Lattice  # noqa: E402


def _batch():
    lat = Lattice(12)
    specs = [build_spec(lat, COLLAGENS["I"], Damage(m, d), np.random.default_rng(3), z=4.4)
             for m, d in (("none", 0.0), ("iso", 1.0))]
    return Batch(lat, specs)


def test_node_energy_sums_to_total():
    b = _batch()
    F = b.F_shear(0.05)
    b.move_affine(b.F0, F)
    b.relax(F)
    tot = b.energy(b.x, F, per_system=True)
    assert np.allclose(node_energy(b, b.x, F).sum(1).numpy(), tot.detach().numpy(), rtol=1e-10)


def test_patch_moduli_average_to_global():
    b = _batch()
    loc, glob = local_shear_maps(b, 3, [0.002, 0.05])
    assert np.allclose(loc.mean(2), glob, rtol=1e-8)
    assert (loc >= -1e-12).all()


def test_morans_I_limits():
    P = 8
    cb = np.indices((P, P)).sum(0) % 2 * 2.0 - 1
    halves = np.where(np.arange(P)[None, :] < P // 2, 1.0, -1.0).repeat(P, 0)
    assert np.isclose(morans_I(cb), -1.0)
    assert morans_I(halves) > 0.6


def test_single_cell_bistable_and_traction_depolarises():
    vp = VmemParams(G0=0.0)
    F = np.array([[[0.0]], [[0.0]], [[800.0]]])
    gM, Gx, Gy = conductances(F, np.ones_like(F), vp)
    V = simulate_sheet(np.array([[[-70.0]], [[-5.0]], [[-70.0]]]), gM, Gx, Gy, vp)
    assert V[0, 0, 0] < -60 and V[1, 0, 0] > -20  # two stable states without traction
    assert V[2, 0, 0] > -35                         # high traction removes the polarised state


def test_gaussian_info_estimators():
    import torch

    from oxt.bioelectric import gaussian_info
    g = torch.Generator().manual_seed(0)
    n, P = 20000, 4
    white = torch.randn((n, 1, P, P), generator=g)
    ais, te, _ = gaussian_info(white)
    assert abs(ais[0]) < 2e-3 and abs(te[0]) < 2e-3
    rho = 0.8                                   # AR(1): AIS = -0.5 ln(1 - rho^2)
    x = torch.zeros((n, 1, P, P))
    for t in range(1, n):
        x[t] = rho * x[t - 1] + torch.randn((1, P, P), generator=g)
    ais, _, _ = gaussian_info(x)
    assert abs(ais[0] - (-0.5 * np.log(1 - rho ** 2))) < 0.03
    y = torch.zeros((n, 1, P, P))               # each cell driven by its left neighbour -> TE > 0
    for t in range(1, n):
        y[t] = 0.5 * torch.roll(y[t - 1], 1, -1) + torch.randn((1, P, P), generator=g)
    _, te, _ = gaussian_info(y)
    assert te[0] > 0.02


def test_stress_uncouple_closes_junctions_at_high_traction():
    vp = VmemParams(gj_mode="stress_uncouple", G0=1.0)
    F = np.array([[[100.0, 100.0]], [[800.0, 800.0]]])
    _, Gx, _ = conductances(F, np.full_like(F, 0.9), vp)
    assert Gx[0].mean() > 5 * Gx[1].mean()
