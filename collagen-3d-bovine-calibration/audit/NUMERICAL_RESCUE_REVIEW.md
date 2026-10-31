# Near-equilibrium numerical rescue review

The parent reports that the first twelve vectorized production curves stopped before damage with physical max gradients approximately 1.01e-7–2.9e-7, while the same baseline is solvable with the original JavaScript implementation. A SciPy energy/line-search stopping floor is a plausible explanation, not established solely by the small residual. Preserve `OptimizeResult.message`, iteration/evaluation counts, physical and scaled gradients, and the coordinates of failures before assigning a cause.

## First, retain the tolerance and improve termination

Use `ftol=0`, adequate `maxls` (e.g. 100), and a bounded larger `maxiter`. Choose the scaled-gradient tolerance no greater than `min(1e-12,0.01*physical_tol*min(pre))`. A callback may stop when the independently evaluated **unscaled free gradient** passes the unchanged physical tolerance; SciPy's success flag alone is neither necessary nor sufficient. Independently re-evaluate the returned coordinates after every optimizer exit. Restart L-BFGS-B three to five times from its latest coordinates, logging every exit, and keep the best physically qualified state. `ftol=0` can still stop when function changes round to zero or the line search fails, so it is not a universal fix.

Near equilibrium, a very stiff short segment can leave a measurable gradient while its correct coordinate change and energy decrease are at floating-point scale. The physical energy is approximately 1e-3 in some nonlinear states; an energy change around 1e-18 can be comparable to evaluation roundoff. Accepting arbitrary energy growth is invalid, but a separately bounded, logged roundoff allowance can permit a residual-reducing polish without changing the constitutive energy or force tolerance.

## Analytic Hessian backup

`exact_hessian.py` is original remote-only audit code, not yet executed with NumPy/SciPy locally. It adds the exact residual-weighted geometric terms to the existing `J.T@J` matrix. For an axial segment it adds `(length-rest)/(rest*length) * (I-nnᵀ)` with the two-endpoint incidence signs. For an angle it adds `aw*(sg*cos-c0)*sg` times the Hessian of the unsigned normalized dot product, mapped from two segment vectors to their four endpoints. Duplicate shared-node entries are summed in sparse assembly. The physical matrix has no artificial diagonal spring.

The unsigned cosine Hessian blocks are

- Haa = [−na nbᵀ − nb naᵀ − cos I + 3 cos na naᵀ] / A²;
- Hbb = [−na nbᵀ − nb naᵀ − cos I + 3 cos nb nbᵀ] / B²;
- Hab = [I − na naᵀ − nb nbᵀ + cos na nbᵀ] / (AB), with Hba=Habᵀ.

The independently authored standard-library `check-hessian-blocks.py` checks these block expressions against finite differences on 32 deformed angle samples from all four frozen geometries. All passed, with maximum relative Hessian-vector error 1.75e-9 (`hessian-block-checks.json`). This validates the calculus, not the NumPy sparse implementation. Run `check_hvp` remotely on all four full models at perturbed and loaded states, including a deleted-edge mask, before enabling the polish.

`gradient_polish` is limited to a near-equilibrium residual <=1e-4 and twelve iterations. It scales coordinates, diagonalizes the true Hessian, and clips eigenvalues **only for the search direction** to produce a descent-preconditioned step. Every accepted trial must lower the actual max free gradient and must satisfy Etrial <= Ecurrent + 64*machine_epsilon*max(|Ecurrent|,1e-12). Every allowance, energy change, residual reduction, step fraction and raw minimum eigenvalue is logged. The objective, physical Hessian, force tolerance and downstream curvature classification are unchanged. A polished stationary state can still be unstable and must undergo the independent curvature screen. No negative eigenvalue is hidden by the search-direction clipping.

If this bounded rescue still fails, preserve the state as unresolved; do not reinterpret nonconvergence as fracture or continue the damage curve from an invalid equilibrium. A revised remote run must retain its exact source/amendment hashes and the failed first attempt as a separate diagnostic series.
