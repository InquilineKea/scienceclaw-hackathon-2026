"""Probe 4: fiber3d protocols after the fixes (rest sanity + short curves)."""
import time
import numpy as np
import torch

torch.set_num_threads(4)
from oxt.fiber3d import FiberDesign, build_fiber_network, FiberBatch, fiber_hessian_moduli

W = 4
box_L = (2 * 2 ** 0.5 * W ** 3) ** (1 / 3)
fd = FiberDesign(n_fib=32, n_seg=7, p_align=0.35, curve_sigma=0.3, z=3.4,
                 lock=0.08, lock_place="crossings", xlink_dist="clustered")
nets = [build_fiber_network(fd, np.random.default_rng(s), box_L, 4 * W ** 3) for s in range(2)]
fb = FiberBatch(nets, device="cpu", relax_kw=dict(max_rounds=25, iters=200))
t0 = time.time()
fm = fb.relax(fb.F0)
P = fb.stress(fb.F0)
print(f"rest: fmax={fm:.2e} stress={P.abs().max().item():.2e} ({time.time()-t0:.1f}s)")

t0 = time.time()
res = fb.failure_curve(np.round(np.arange(0.02, 0.31, 0.04), 3), axis=0)
print(f"failure ({time.time()-t0:.0f}s): peak", res["sig"].max(1).round(4),
      "first", res["first"], "broken_tot", res["broken"].sum(1))

t0 = time.time()
res2 = fb.cohesive_curve(np.round(np.arange(0.02, 0.35, 0.04), 3), mode="tension")
print(f"cohesive ({time.time()-t0:.0f}s): T_peak", res2["Teff"].max(1).round(5),
      "first", res2["first"], "broken", res2["broken"][:, -1])

t0 = time.time()
hm = [fiber_hessian_moduli(n, device="cpu") for n in nets]
print(f"hessian ({time.time()-t0:.0f}s):", [{k: round(v, 5) for k, v in h.items()} for h in hm])
