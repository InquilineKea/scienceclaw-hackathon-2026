# Paired network law sensitivity

This is an original, dependency-free CPU screening model, not a validated collagen simulation. It extends the earlier cell-cavity network idea. The earlier public H100 matched-stiffness study measured bulk-network strain and relaxation, not explicit adhesion-site forces; this study introduces a separate cell-cavity geometry and force readout. It does not retroactively validate that earlier study.

The frozen design is in design.json. Every pair shares the same diluted triangular lattice, edge count, bending terms, adhesion nodes and loading history. A random 35% of edges carry the selected material properties in the uniform architecture. The same number of edges nearest a cell-adjacent center carry those properties in the clustered architecture. The cluster angle varies with seed. Initial shear stiffness is matched by scaling each architecture's entire mechanical energy to the same graph's unmodified reference. Viscous and yield forces receive the same scaling, retaining the specified relaxation-time ratios. This matches one initial shear observable, not the full elasticity tensor, local compliance, or relaxed stiffness.

For an edge with unit reference direction n, extension is e = n·(u_j-u_i). The energy is U = (k_inf/2)e² + (k_s/2)(e-s)². For the three sliding laws, k_inf = 0.2 k and k_s = 0.8 k. The selected edge's instantaneous stiffness is 0.25, 1 or 4 times the background. Time unit is the background sliding time; selected-to-background time ratios are 0.1, 1 and 10. No physical seconds or pN mapping is assigned.

Internal sliding is updated by backward Euler. Let r = e - s_new and z = e - s_old. Solve r + (dt/tau) phi(r) = z, with:

- Linear viscous sliding: phi(r) = r.
- Yield-threshold viscoplastic sliding: phi(r) = sign(r) max(|r|-0.01, 0).
- Eyring rate-strengthening sliding: phi(r) = 0.01 sinh(r/0.01).
- Locked elastic baseline: s = 0 and total edge force k e.

The threshold and Eyring scales are illustrative dimensionless strain scales, not fitted chemical constants. The Eyring function represents activated rate strengthening phenomenologically; no activation barrier is estimated. These three sliding laws have nonnegative dissipation and positive algorithmic tangents. They do not include rate weakening, bond rupture, rebinding, adhesion turnover, fiber buckling, geometric nonlinearities or poroelasticity.

A separate quadratic bending energy penalizes transverse second differences on opposite collinear segments, with coefficients 0.003 or 0.03. At each time step, free-node force balance is solved by a Newton method with positive-definite Cholesky factorization and residual-decreasing line search. There is no hidden regularization of singular systems. Mechanically unstable graph blocks are excluded and reported with their seed/density/bending, not repaired by adding arbitrary springs.

The outer boundary is fixed during cell loading. Actin target displacement points inward with magnitude ramping from 0 to 0.04 lattice units over t=0..1, held through t=5, unloaded through t=6, and recovered through t=10. Adhesions either follow the target exactly or couple to it through springs of stiffness 0.2. These springs are a compliance test, not an integrin clutch model. The readout is the mean magnitude of network reaction or adhesion spring force, with secondary maximum and heterogeneity metrics. Radial loading directions are prescribed; there is no active cell feedback.

Primary response is force integrated over the hold. Paired contrast is C = 2(F_clustered-F_uniform)/(F_clustered+F_uniform). C=0.1 means a 10% difference relative to the pair's average, not exactly a 10% ratio increase. Numerical zeros are handled explicitly. Uncertainty is the pointwise 95% percentile bootstrap of paired geometry-seed contrasts (4,000 resamples; deterministic scenario-specific seeds derived from base81271). Counts of positive/negative/unresolved parameter scenarios describe the chosen design coverage, not probabilities of mechanisms or biological outcomes. Intervals are not multiplicity corrected. A +/-0.05 mean contrast band is an explicitly chosen screening tolerance, not a biological threshold.

The main sweep uses twelve seeded graph attempts for each scenario. Refinements repeat selected scenarios at dt=0.025 instead of0.05 and with a9x9 instead of7x7 lattice. Increasing the lattice at fixed spacing increases the domain and boundary distance; it is a boundary/domain sensitivity test, not mesh convergence or paired identical geometry. Its random graph draws differ even at matching seed labels. Report these limitations when comparing domain means.

Checks include finite-difference energy gradients, rigid-translation invariance, force balance, initial shear matching, equilibrium residual, nonnegative sliding dissipation, analytic backward-Euler single-element relaxation, exact selected-label null when all selected coefficients equal background, and the two refinements. Sources and binaries are retained with hashes. There are no third-party scientific dependencies or remote/GPU computations in this study.

The law families are motivated by questions about hydrated collagen shearing and rate-dependent adhesion, not derived from these publications' parameter values:

- Gautieri et al., hydration/distance-dependent collagen shearing, https://pubmed.ncbi.nlm.nih.gov/22762892/
- Andreu et al., force-loading rate and mechanosensing, https://www.nature.com/articles/s41467-021-24383-3
- Brosz et al., collagen-specific Martini3 benchmark, https://pubmed.ncbi.nlm.nih.gov/41074457/

The next molecular experiments should distinguish the parameter combinations that change the network contrast most, while recognizing that missing 3D, nonlinear, fluid and cell feedback mechanisms are outside this screen. A sensitivity ranking is not a formal value-of-information calculation: it lacks a validated parameter prior, experimental noise model and utility function.
