# Audit remediation: demonstrated fixes and remaining evidence gates

The supplied Piper summary is an engineering handoff, not an independent numerical-validation report. This revision preserves all frozen runs, raw figures, release assets and run-level manifests.

## Completed

- Six atlas seed-17 cases reproduced against the saved model fingerprint: aligned/isotropic tension, isotropic shear, confined compression, constrained pulse and free translation. Full geometries, curves, replay frames, comparisons and logs are preserved under `runs/`. All four equilibrium cases met residual <2e-7. The constrained pulse energy error was 0.03324%. Free translation had negligible internal work and zero damage; its external/kinetic integration mismatch was 0.1924%, separately reported.
- Seven before/after Python regressions passed: original shared parameter identity demonstrated, patched instance mutation isolation, unchanged default values, retained explicit parameter objects, twelve heart cases, two short seeded clutch cases and one default-duration seeded clutch case. Exact array comparisons passed. See `python-runs/` for copied source, isolation checks and logs.
- Function-call/mutable defaults were replaced with per-call construction in cell/heart code and the network-capable image-inspection helper.
- Animation callback state was explicitly bound. Existing animation saving consumes the callback inside its loop; no historical animation corruption was demonstrated. The plotting script was not rerun by these regressions.
- The historical stiffness ratios were recomputed from saved CSVs: 51.025× (12×12, two seeds, target z=3.0→4.4), 259.285× (16×16, four seeds, target z=2.8→5.0), and 68.736× for the larger campaign over the shared target endpoints. Actual realized coordination also differs. Documentation no longer presents these as one controlled universal effect.
- Clinical attribution and molecular-to-network linkage claims were qualified. An unexecuted larger profile is no longer described as a result to trust.

## What the successful checks do not establish

Same-source reproduction is not an independent implementation. The pilot covers six cases, not all 450, and does not test shear relaxation or prove damage-placement effects. Numerical regression of defaults does not validate the biological equations. No new cloud job, physical experiment, full FEniCSx rerun or species-mechanics calibration was performed.

## Predeclared geometry falsification protocol — not executed

1. Treat geometry, orientation, actual coordination and damage placement as separate factors. Use at least ten fresh network realizations per family, paired intact/damaged samples, and common seed identities for reproducibility; cross-generator identical seeds do not imply identical geometry.
2. Compare a 2D triangular generator, 3D FCC generator and disordered fibrous generator. Preserve specimen aspect ratio, solid/fiber-volume budget, recruitment and damage laws, normalized loading history and boundary protocol. Record all material rescaling. Raw 2D and 3D energies/stresses have different dimensional conventions and must not be pooled.
3. Report both equal-material-budget and separately matched-initial-stiffness comparisons. Match the measured tangent response for the actual loading direction; do not match only a graph degree or a single unrelated stiffness component. Reserve loading directions/protocols for validation rather than fitting every response. Compare actual orientation tensors and supported mechanical soft modes; z≈4 and z≈6 are dimension-dependent counting references, not rigidity proofs.
4. Define two primary outputs before running: intact/damaged relaxation-time or phase-response change, and operational work-to-failure with explicit censoring. Report paired effect sizes and seed uncertainty; include equal-count clustered/distributed damage, distance to grips and removed fiber volume as controls. Imposed failure work is not measured fracture energy.
5. Halve load/time increments, tighten force tolerance tenfold, check energy balance for every transient control, and record failed solves and negative effects. Do not convert failed or censored cases into zero toughness or remove them silently. Test time-window sufficiency for relaxation separately from force convergence.
6. Use each solver's documented residual and energy gates; compare small-strain/gradient reference problems with an independent implementation before interpreting cross-generator contrasts. A sign reversal, poor numerical resolution, or held-out prediction failure falsifies transfer of the original claim even if one within-family trend remains.

## Calibration and reporting gates

| Quantity | Evidence required | Present boundary |
| --- | --- | --- |
| Bulk elastic/viscoelastic scale | Identified concentration, hydration, geometry, temperature and frequency/strain protocol; held-out specimens or studies | Existing bovine/rheology projects contain bulk comparisons. These do not validate measured 3D architecture or every chemistry. |
| Recruitment/anisotropy | Directional stress–strain data and measured orientation/recruitment distributions | Generator scores and orientation changes remain model assumptions unless separately measured and validated. |
| Rupture/toughness | Matched failure curves, strain-rate/size controls, crack or failure-area convention and censoring | Atlas work-to-failure depends on the imposed criterion; it is not calibrated tissue fracture toughness. |
| Crosslink remodeling | Chemical identities, occupancies, lifetimes and kinetic intervention controls | Generic reversible/sliding laws do not establish glucosepane/PYD/4-HNE reaction kinetics. |
| Relaxation/poroelasticity | Time/frequency response, permeability and boundary/drainage controls; accepted mesh comparisons | FEniCSx algebraic resolution (4,158/4,160) and observable mesh acceptance (1,341/1,600) have different denominators. Report both and withhold rejected comparisons. |
| Species/molecular transfer | Matched tissue chemistry and architecture plus independently constrained constitutive transfer | COL1A1 backbone construction or proxy-fragment rankings do not supply a calibrated species-strength law. |

New experimental measurements cannot be manufactured by a code patch. Remaining gates are scientific work items, not closed bugs. Keep failed hypotheses and earlier versions available, and publish later validation as new identified runs.
