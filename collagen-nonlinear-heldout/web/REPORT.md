# Nonlinear collagen surrogate versus harmonic interpolation

The selected combined surrogate passes the frozen practical and numerical criteria on the adaptively reused conditional benchmark.

Pos008 was inspected in the preceding study and is an adaptively reused benchmark. Pos007 selects parameters; Pos004 supplies numerical commissioning. All results are conditional on measured inner/outer boundary motion. This is not an independent biological validation or known-force experiment.

## Final field comparison

| Model | Equal-octant vector MSE (µm²) | Equal-octant RMSE (µm) | Raw P1 strain NRMSE | Guarded local-strain NRMSE |
|---|---:|---:|---:|---:|
| Harmonic | 1.12814 | 1.06214 | 0.742073 | 0.604762 |
| control | 1.60179 | 1.26562 | 0.789113 | 0.6916 |
| buckling | 0.772985 | 0.879195 | 0.701325 | 0.530915 |
| sliding | 1.71175 | 1.30834 | 0.805266 | 0.708565 |
| combined | 0.805691 | 0.897603 | 0.703336 | 0.533428 |

Combined-model vector MSE improvement relative to harmonic: 28.5822%.

Displacement errors weight the eight spatial octants equally. Raw P1 strain uses volume-weighted infinitesimal tensor Frobenius error; guarded 5×5×5 strain uses equal eligible local affine-fit centers. These are different correlated outcomes, not independent replications. Secondary NRMSE is observed-field normalized after supplied-boundary-only translation removal. Lead with physical displacement errors.

## Qualification

| Required gate | Pass |
|---|---|
| vector_mse_5percent | yes |
| raw_strain_no_worse | yes |
| guarded_strain_no_worse | yes |
| common_coverage | yes |
| equilibrium | yes |
| finite_energy_history | yes |
| nonnegative_dissipation | yes |
| work_balance | yes |
| kkt | yes |
| positive_jacobian | yes |
| step_refinement | yes |
| angular_refinement | yes |
| no_detected_negative_curvature | yes |
| hvp_fd | yes |

Practical success requires at least 5% lower vector MSE than unchanged harmonic and neither raw nor guarded strain error worse, with complete common coverage. Numerical qualification additionally requires every listed boolean gate explicitly true; missing gates fail closed. Step and angular refinements must be assessed separately against the 110-direction/10-step primary case. A nonnegative finite Lanczos subspace screen does not prove stability, uniqueness or absence of every negative mode.

Thresholds, detailed controls and retained failures: [numerical-controls.json](numerical-controls.json). Full frozen selection and candidate outcomes: [SELECTION.json](SELECTION.json). Descriptive final results: [results.json](results.json).

## Interpretation limits

Selected parameters are predictive candidates, not measured buckling or sliding properties. The twelve-arm directional continuum varies compression softening and irreversible plastic lengthening with fixed tensile priors. Its slip state is an internal surrogate, not observed junction sliding or molecular damage. Proportional loading from a drug-relaxed reference is assumed, not an observed time history or established virgin state. No actual collagen graph connectivity is reconstructed. Missing boundary measurements receive modeled natural conditions. Uniform absolute stiffness is not identified by these homogeneous displacement-controlled fields. No aging, cell-force, fracture, toughness or species claim follows.

The same few positions and thousands of correlated vectors/tetrahedra are not independent biological replicates. Unknown specimen/batch independence and uncalibrated DVC, reference-registration and segmentation uncertainty prevent an experimental adequacy claim from numerical residuals alone. Better benchmark error would require confirmation on genuinely uninspected public fields with a new frozen contract.

## Source and provenance

- [Frozen protocol](PROTOCOL-FROZEN.md) and [design audit](FINAL-DESIGN-AUDIT.md).
- [Prior measured-field source snapshot](../collagen-measured-3d-validation/) retains mask/provenance records and baseline methodology.
- [Saenopy primary study](https://doi.org/10.1038/s41567-024-02632-8) and [public example release](https://github.com/rgerum/saenopy/releases/tag/v0.7.4).
- Lebedev angular tables are referenced in the frozen protocol; raw tables are excluded from this bounded export.

The public package retains original source and bounded audit/result records. Raw images, input fields, binary executables/states, probes and downloaded third-party tables are excluded. This report does not claim those exclusions are a complete reproducibility archive; original local research archives retain them.
