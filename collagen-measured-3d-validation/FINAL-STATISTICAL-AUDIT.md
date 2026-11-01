# Final statistical and interpretation audit

Read-only audit of completed JSON results and original analysis source, 2026-10-31. No model was rerun, rescored or retuned. No significance test was performed. This report is public-safe and contains no private account or Drive metadata.

## Main finding

The bulk semi-affine law improves the held-out batch-summary ramp score only slightly over its linear comparator and still transfers poorly. The spatial elastic law predicts some observed interior motion from supplied boundary motion, but the kinematic harmonic baseline predicts the final held-out position better. These outcomes do not establish a calibrated collagen material law or measured-network model.

## Bulk batch-summary test

The frozen split is batch A fit / B selection / C test, with 1.2 mg/ml primary. The input-domain guard stopped the original attempt before model selection or final-test response access: batch B at 2.4 mg/ml ends at strain 0.199995. The recorded pre-scoring amendment therefore uses 60 logarithmic targets from 0.005 to 0.19 for every batch/concentration, retaining candidates, fitting weights and selection rule. This is a support correction, not a favorable-error-window choice. The protocol preserves its earlier 0.30 domain as superseded history; final results carry fit_domain=[0.005,0.19].

Selection chose semi-affine λs=0.04, ds=0.05, fixed external d0=0.0025, with separate concentration scales fitted only on A. B mean-concentration NRMSE is 0.513062. All C biases are negative, indicating stress underprediction on the tested aggregate curves.

| Concentration (mg/ml) | Semi-affine C NRMSE | Linear C NRMSE | Semi-affine RMSE (Pa) | Mean bias (Pa) |
|---|---:|---:|---:|---:|
| 0.6 | 0.842898 | 0.848743 | 5.584824 | -3.855228 |
| 1.2 | 0.685506 | 0.697353 | 11.627686 | -8.878898 |
| 2.4 | 0.765015 | 0.770471 | 42.015986 | -34.639322 |

The primary NRMSE improvement is 0.011847, or 1.699% relative to the linear score. This is a descriptive improvement on one held-out batch-summary curve at the primary concentration, not a statistically established material improvement. NRMSE 0.685506 means error remains large relative to the observed stress RMS; it is not “68.6% inaccurate” at every strain. The 60 interpolated targets are correlated resamples of published means, not 60 independent experiments. Three concentrations and batches do not create nine independent test replicates. No raw replicate confidence interval, held-out G′/G″ result, viscosity law, failure threshold or specimen-matched field calibration is identified.

## Spatial final test: Pos008

Pos007 selected ν=0 among the three prespecified elastic candidates using equal-octant vector MSE. Harmonic interpolation was already a prespecified comparator and is not an elasticity law. Pos008 evaluates the selected elastic candidate, harmonic, affine and zero baselines. Position independence remains unknown; this is one final held-out position, not an independent biological cohort.

| Predictor | Equal-octant vector MSE (µm²), primary | Equal-octant vector RMSE (µm) | Secondary displacement NRMSE | Volume-weighted strain Frobenius NRMSE |
|---|---:|---:|---:|---:|
| zero | 8.941671 | 2.990263 | 1.000000 | 1.000000 |
| affine_boundary_fit | 2.866743 | 1.693146 | 0.566220 | 0.895356 |
| harmonic_interpolation | 1.128137 | 1.062138 | 0.355199 | 0.742073 |
| elastic_nu_0 | 1.377164 | 1.173526 | 0.392449 | 0.771420 |

Harmonic has lower displacement RMSE in 6/8 octants; elastic is better in the other 2. The primary MSE is 1.128137 for harmonic versus 1.377164 µm² for selected elasticity. This must not be presented as elastic outperforming the simpler interpolator or identifying ν=0 as the true collagen Poisson ratio. ν=0 is the best of three limited elastic candidates on the selection position, conditional on this geometry, incomplete boundaries and linear law.

The primary displacement score averages squared vector errors equally across octants. Secondary strain errors instead average the infinitesimal symmetric-strain tensor Frobenius squared error by tetrahedron volume and normalize by measured strain norm; shear components receive the factor two required for the tensor Frobenius norm. These are different outcome weightings and must be labeled separately. Strain is a derivative of the same measured displacement field, with amplified/correlated measurement error, not independent validation. The evaluated mesh is a sampling/discretization mesh, not a measured collagen junction graph.

Pos008 uses 3,385 valid supplied boundary nodes; 212 geometrically prescribed nodes lack valid measured vectors and remain unconstrained with natural zero traction. There are 240 missing measured vectors across the full field. All 4,355 reference-eligible score nodes are valid for this final position; 18,931 tetrahedra whose vertices are all score-eligible support the secondary strain calculation. Neither thousands of vectors nor thousands of tetrahedra are replicate counts. Frozen reference-only masks and exact axis-aligned DVC-support purging reduce direct overlap with supplied boundary measurements; they do not establish independence or calibrated measurement uncertainty.

## Normalization departure and invariant primary comparison

Static source review shows that rigid translation is correctly estimated from supplied boundary vectors only. However, secondary displacement NRMSE divides by RMS of the held-out observed displacement after this shift, rather than the boundary-derived amplitude requested by the optional normalization wording in PROTOCOL-FROZEN.md. Record this as a secondary-normalization departure. It does not change predicted fields, primary absolute MSE, or model selection; no reanalysis is needed to conceal or repair it. The zero predictor NRMSE is one by construction, not an external measurement-noise threshold. For transparent publication, lead with the primary µm²/µm errors and label NRMSE as observed-field normalized. Strain NRMSE is likewise outcome-norm normalized.

## What the evidence can and cannot support

All reported iterative field solves have recomputed free-node relative residual below 1e-8, which supports numerical equilibrium at that mesh. It does not establish mesh convergence or agreement within experimental uncertainty. The report cannot claim absolute predictive adequacy without independent registration/DVC/boundary uncertainty. Unknown boundary nodes, reference segmentation/registration assumptions, linearized strain and absent fiber-level connectivity remain material limitations.

Supplied near-cell and outer-face displacements drive all forward fields. This is conditional interior field prediction; it does not independently predict cell contraction, far-field propagation from known force, traction or force concentration. Uniform stiffness cancels from homogeneous linear displacement-boundary equilibrium, including homogeneous zero-traction unknown boundaries. Consequently the spatial results cannot validate k0, bulk rheology scale or cell forces. Bulk ramp and Classic spatial examples have no established specimen-matched calibration; publish their evidence separately.

No aging chemistry, fracture toughness, species robustness, 3D graph connectivity, G′/G″ holdout or molecular-to-network bridge is validated here. These completed tests are useful because they expose where a frozen baseline fails or where a simpler interpolator remains competitive. Further mechanistic models require a new prospective contract; retain the present negative/limited outcomes rather than retuning this final test.

## Files audited

`bulk-results.json`, `BULK-MODEL-FROZEN.json`, `Pos004-results.json`, `Pos007-results.json`, `Pos008-results.json`, `SPATIAL-MODEL-FROZEN.json`, `bulk-validation.mjs`, `spatial-validation.mjs`, `linear-fe.mjs`, `PROTOCOL-FROZEN.md` and the previously frozen reference-mask records. Outcome values were read only after completion.
