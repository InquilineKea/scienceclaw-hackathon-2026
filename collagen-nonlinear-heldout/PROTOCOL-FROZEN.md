# Frozen nonlinear comparison protocol
Frozen before Pos007 production scoring, 2026-10-31. Supersedes PROTOCOL-DRAFT.md.

Use original measured 3D benchmark geometry, boundary translation, missing-data handling, score masks and equal-octant vector MSE unchanged. Pos004 is numerical commissioning only; Pos007 selects parameters; Pos008 is an adaptively reused test benchmark, previously examined. No independent-sample significance claim.

Twelve factorial arms: compression buckling scale absent, 0.0025, 0.01, 0.04; irreversible sliding yield absent, 0.01, 0.04. Hardening H=0.05. Tensile stiffening onset 0.04 and scale 0.05 are fixed literature-informed priors, not fitted to test outcomes. All arms include finite geometry and tensile stiffening. The no-buckling/no-sliding arm is the matched control (small-strain Poisson ratio 0.25); previous elastic nu=0 and harmonic interpolation remain separate baselines.

Select lowest Pos007 equal-octant vector MSE separately within buckling-only, sliding-only and combined families among numerically converged runs. Combined family winner is primary. Save selection before reading Pos008 scores. Retain every failure and report coverage.

Primary quadrature: full Lebedev 110 / 55 antipodal directions. Ten equal proportional displacement steps from assumed virgin drug-relaxed reference; this loading history is a modeling assumption, not a measured time series. Re-equilibrate primary selected case using 20 steps and 302 directions. Gradient tolerance 1e-7 relative to common linear boundary force scale; maximum 3000 iterations/step; determinant >0.05 at every evaluation; local slip KKT tolerance 1e-9 scaled. No outcome-dependent rescue parameters. Per-case wall timeout 15 minutes.

Practical improvement requires at least 5% lower Pos008 vector MSE than harmonic interpolation, raw P1 strain NRMSE no worse than harmonic 0.7420726542, and guarded 5x5x5 averaged-strain NRMSE no worse than harmonic 0.6047619794. Terminal reaction-work balance error <=2%; 10/20-step and 110/302-direction changes in prediction vector RMSE and reaction work <=1%. Screen constrained exact incremental Hessian including geometric compression terms with 32-step seeded Lanczos; resolved negative curvature invalidates stable-equilibrium claims. A nonnegative finite subspace screen does not prove global stability. If gates fail, report unresolved numerical evidence, not a validated win.

No actual fiber connectivity is reconstructed. This isotropic directional continuum uses irreversible plastic lengthening as a sliding surrogate; it does not identify chemical crosslinks or actual fiber sliding. Absolute stiffness cancels in displacement-driven homogeneous models. No fracture, toughness, aging, independent rheology or biological causality is validated here.

All production code is original standard-library code. Numeric angular tables are inert data from https://people.sc.fsu.edu/~jburkardt/datasets/sphere_lebedev_rule/ (Lebedev 017 and029); preserve URLs and hashes; omit downloaded tables from public redistribution.
