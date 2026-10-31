# Fracture Atlas — executed results

2026-10-31. **450 local simulations completed**, comprising 280 topology/protocol runs and 170 controls/sensitivities. Seven families, five main seeds and eight loading protocols. All 350 quasistatic runs met the specified force residual at every recorded step. Inertial runs are time integrations, not equilibria. The benchmark took 37.13 s in the recorded Node v26.12.1 execution; browser custom runs are additional interactive calculations and are not included in the benchmark.

**The tested model does not select a universal toughest collagen topology.** In X tension, diagonal reinforcement has the largest sample mean work to the operational criterion, while aligned bundles have the largest mean peak force. The two are on the mean work/strength Pareto frontier. The ranking changes in shear and under a constrained inertial pulse. Compression often reaches the cap without the criterion; it cannot provide a complete failure-toughness ranking. None of these observations is experimental collagen validation.

## Main comparison

All work values below are energy density ×10⁻³ E₀, mean ± sample SD over five seeds. SD is not a confidence interval. Quasistatic work includes recoverable energy; pulse work is stored energy plus irreversible and damping loss, excluding kinetic energy. These definitions make separate sense for their protocols but do not make them one common material constant.

| Architecture | X tension | Shear | Constrained pulse |
|---|---:|---:|---:|
| Aligned bundles | 0.486 ± 0.039 | 0.001 ± 0.001 †5/5 | 0.872 ± 0.027 |
| Disordered | 0.443 ± 0.210 | 0.301 ± 0.063 | 1.391 ± 0.446 |
| Hierarchical | 0.324 ± 0.102 | 0.157 ± 0.050 | 1.346 ± 0.400 |
| Modular | 0.066 ± 0.034 | 0.092 ± 0.025 | 1.651 ± 0.650 †1/5 |
| Diagonal reinforcement | 0.609 ± 0.152 | 0.186 ± 0.035 | 1.311 ± 0.514 |
| Bottlenecked | 0.049 ± 0.012 | 0.315 ± 0.028 | 1.462 ± 0.695 †2/5 |
| Degree heterogeneous | 0.172 ± 0.074 | 0.145 ± 0.031 | 1.604 ± 0.107 |

† gives the number of capped runs: a mixture of criterion-limited and window-limited work is not a complete toughness estimate. The complete table for all eight protocols is in data/results.json.

In X tension, aligned bundles reach mean peak reaction 4.865×10⁻³, versus 2.492×10⁻³ for diagonal reinforcement. The latter deforms farther before meeting the criterion: 58.4% versus 20.7% strain. The greater work of diagonal reinforcement is therefore not evidence of greater strength. Its work distribution overlaps the disordered family and depends on the assumed rupture/regularization laws.

A single cut across X makes the bottlenecked network weak in X tension, yet it has the largest sampled mean shear work (0.315×10⁻³), close to the disordered network (0.301×10⁻³). Shear uses top/bottom grips, so that X cut does not have the same role. The selected graph motifs and their orientation are confounded; this does not show that bottlenecks are intrinsically tough.

Among pulse families with all five failures observed, degree-heterogeneous networks have the highest mean internalized work (1.604×10⁻³). Modular networks have a higher mixed endpoint mean but one capped run, so they cannot be declared the pulse toughness winner. Damping, density, pulse duration and supports are essential parts of this comparison. The animation continues after first criterion crossing; the score uses the first crossing.

## Pressure and acceleration: what is actually resolved

- compression: 27/35 runs reached the strain cap without the criterion; 0/35 had permanent collagen rupture.
- confined: 35/35 runs reached the strain cap without the criterion; 0/35 had permanent collagen rupture.
- biaxial: 33/35 runs reached the strain cap without the criterion; 0/35 had permanent collagen rupture.

At 30% imposed compression, resistance can differ between architectures without any complete failure measurement. The “pressure” animation is laterally confined skeleton compression, not imposed hydraulic pressure, pore pressure or a validated hydrostatic shock. No physical extreme-load limit can be inferred.

Uniform free acceleration generated maximum fiber strain 1.26e-13 and internalized work 4.61e-30 across the 35 baseline free runs, with zero rupture. External work largely became rigid-body kinetic energy. Clamping one edge under the same acceleration produced deformation and damage. The relevant specification is body force with mass, geometry, supports and time history, not acceleration alone.

## Which statistics predicted work?

Spearman correlations below use converged, uncensored topology samples; they are descriptive and family-confounded. Mean degree (4.556), coordination excess (0.556) and cycle rank (47) are constant in the fixed-budget sample, so they cannot explain its variation.

| Predictor | X tension (n=35) | Shear (n=30) |
|---|---:|---:|
| lambda2 | 0.312 | 0.120 |
| weightedLambda2 | 0.208 | 0.124 |
| normalizedLambda2 | 0.374 | 0.071 |
| maxBetweenness | -0.429 | 0.031 |
| degreeVariance | -0.029 | -0.299 |
| anisotropy | 0.204 | -0.082 |
| alignmentX | 0.378 | -0.529 |
| hessianMin | 0.166 | 0.576 |
| softIPR | -0.438 | -0.176 |

The unweighted λ₂ association is modest in X tension and weak in shear. Degree variance has essentially no X-tension association. Betweenness and soft-mode localization have stronger negative X-tension associations in this sample, but none is a sufficient scalar explanation. Reference Hessian modes include geometry and bending; their smallest eigenvalue relates more strongly to shear work here, without establishing a general predictor.

An exact counterexample to a direction-blind graph score is the same aligned seed-17 graph under X versus Y tension: every graph eigenvalue is identical. X reaches its criterion; Y remains very soft and capped. We do not form a ratio of two “toughnesses” when one did not fail, and the tiny Y/shear work is sensitive to solver tolerance.

### Held-out prediction of log work, X tension

Ridge penalty 1, training-only standardization; hold-out seeds 71 and 101. “Mechanical” includes the initial secant stiffness measured during loading, so it is not a zero-test topology predictor.

| Features | Seed hold-out R² | Leave-one-family-out R² |
|---|---:|---:|
| mean | -0.000 | -0.329 |
| spectral | 0.242 | -3.464 |
| geometry | 0.187 | -1.745 |
| mechanical | 0.469 | -0.040 |
| combined | 0.802 | -0.570 |

The combined predictor works on new seeds of known families, but all tested feature sets have negative family-held-out R². Purely spectral prediction fails particularly badly when transferred to a new architecture. No predictor demonstrated reliable cross-family generalization. Y-tension and shear validation results, including additional negative R² values, are retained in full.

## Composition, cycles, density and uncertainty

The independent composition sweep uses three disordered-network seeds. Doubling collagen volume approximately doubles work in this law, as expected from its linear energy prefactor; this is a constitutive scaling check, not new evidence of biological toughening. Diameter, bending, crimp, segment preference, material allocation and rupture disorder have conditional effects. The elastin-like parallel background increases total material and survives collagen rupture; its higher work must not be credited to collagen topology alone.

The six subfailure cyclic runs show additional loss when hypothetical sacrificial links are present. Mean cycle work is 5.828e-8 without those links and 1.123e-5 with them. The difference tests the implemented mechanism, not a native crosslink identity. Individual irreversible-loss terms and curves are in the dataset.

The edge-count sweep includes mean degrees below and above the bulk 2D Maxwell counting value. Its rows vary connectivity at fixed collagen volume and are not pooled into the topology predictor analysis. The finite-size checks change the realization; they do not establish continuum convergence.

## What the checks support — and what they do not

- Nine physical/numerical checks pass; seven baseline tensile re-runs reproduce stored work within 4.69e-11 rounding error.
- Maximum free-DOF residual among all quasistatic records: 2.000e-7. All production runs passed their specified residual test.
- Halving the load increment changes uncensored seed-17 tension/shear work by at most 11.6%. Thus event resolution is useful but not fully converged.
- Tightening force tolerance reduces the tiny aligned shear work by about 96%; that near-floppy number is numerically unresolved and is not used as an uncensored target.
- Halving the pulse time step in three families changes internalized work by at most 0.13%. Baseline constrained-pulse energy-balance error is at most 0.062% of external work.
- Changing the artificial collapse coefficient from 20 to 10 or 40 changes seed-17 tension/shear work by at most 1.6%. This narrow sensitivity does not make the regularizer physical.

These are implementation and sensitivity checks, not experimental validation. Local minima, event-triggered failure, small seed counts, artificial graph generators, 2D geometry and omitted contact/fluid mechanics remain material limitations. No molecular proxy calibration or absolute extreme-load prediction was performed.

## Deliverables and provenance

The interactive gallery, comparison animation, CSV/JSON results, representative trajectories, source, logs, checks, five GIFs and PNG/SVG figures are local files in this package. Every visual uses executed simulation output. See METHODS.md for equations and precise definitions, EVIDENCE.md for primary literature, and SECURITY-REVIEW.md for the bounded source inspection. Model SHA-256: f0a5034f44aa7065c779f6e20209cd95ee13c7a3ffe6f3e40ae08172a7a489c1.
