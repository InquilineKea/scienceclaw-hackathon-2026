# Controlled 2D, FCC 3D and geometrically disordered network comparisons

Executed 1 November 2026. Primary run: `event-controls-20261101T081852Z`. CPU-only; no cloud instance, package installation or cloud charge.

**Main finding:** matching intact axial stiffness does not make the response architecture-independent in this central-force brittle surrogate. FCC and geometrically disordered FCC networks absorb more normalized axial work than the triangular family in these specimens. The intervals for the two 3D intact families overlap, and this is not evidence of a uniquely toughest collagen network. Shear was held out from matching; many shear/damaged cases remain censored at strain 0.24. Work for censored cases is work to the strain limit, not known work-to-failure.

## Design and model boundary

Ten seeded realizations per family, paired intact/clustered/distributed removal, common imposed axial/shear strain histories, unit-height specimens, equal initial fiber material measure plus a separate uniform modulus scaling to match intact axial stiffness K=1. Same thresholds and geometry pair damage patterns within a seed. Matched results are exact rescalings of the same trajectories, not independent replicate runs. Damaged cases retain the intact scaling and are not rematched.

The 2D family has triangular topology with 49 nodes; FCC 3D and disordered 3D have 63 nodes. Disordered means larger positional disorder on the FCC graph, not an independently random connectivity ensemble. Realized degree/orientation, removed volume and grip distance are archived. Equal removed-edge count does not exactly match removed material or grip distance. Orientation, coordination, size and dimension are not independently matched causal factors.

This is an original small-strain linearized central-force truss with irreversible threshold failure, not the nonlinear atlas, a full fibrous collagen constitutive model, FEniCSx, transient acceleration/pressure, viscoelastic relaxation or biochemical reaction dynamics. The geometry is not updated in the stiffness operator; large plotted deformation does not validate large-strain kinematics. Compression rupture uses the same absolute strain threshold as tension and is an imposed surrogate. Raw dimensional 2D/3D stress/energy are not pooled. See SECURITY_AND_METHOD_REVIEW.md for exact equations and remaining protocol gates.

## Primary event-resolved results

Means and bootstrap 95% seed intervals use ten realizations per row. Units are work / (intact axial K × height²); matched K=height=1. Intervals represent seed variability, not biological or numerical-model uncertainty. Censored work is a lower bound on work to the chosen failure event and is not imputed as failure.

| Family | Loading | Damage | Mean endpoint work | 95% seed interval | Censored /10 |
|---|---|---|---:|---|---:|
| triangular2d | tension | intact | 0.00270548 | 0.00254406–0.00284747 | 0 |
| triangular2d | tension | clustered | 0.00194123 | 0.00178072–0.00212773 | 0 |
| triangular2d | tension | distributed | 0.00203285 | 0.00175520–0.00232923 | 0 |
| triangular2d | shear | intact | 0.00235930 | 0.00222326–0.00249941 | 7 |
| triangular2d | shear | clustered | 0.00204999 | 0.00193714–0.00216100 | 10 |
| triangular2d | shear | distributed | 0.00189532 | 0.00175933–0.00203188 | 9 |
| fcc3d | tension | intact | 0.01007491 | 0.00965061–0.01052935 | 0 |
| fcc3d | tension | clustered | 0.00823166 | 0.00788743–0.00863281 | 0 |
| fcc3d | tension | distributed | 0.00776270 | 0.00726602–0.00820151 | 0 |
| fcc3d | shear | intact | 0.00609203 | 0.00544035–0.00688103 | 2 |
| fcc3d | shear | clustered | 0.00578857 | 0.00543973–0.00615654 | 3 |
| fcc3d | shear | distributed | 0.00577795 | 0.00529694–0.00630696 | 5 |
| disordered3d | tension | intact | 0.01057650 | 0.01017165–0.01103482 | 0 |
| disordered3d | tension | clustered | 0.00883671 | 0.00811852–0.00954351 | 5 |
| disordered3d | tension | distributed | 0.00850479 | 0.00791268–0.00904111 | 3 |
| disordered3d | shear | intact | 0.00642161 | 0.00599430–0.00694128 | 2 |
| disordered3d | shear | clustered | 0.00610742 | 0.00571163–0.00654257 | 9 |
| disordered3d | shear | distributed | 0.00638153 | 0.00597943–0.00677375 | 9 |

Failure means remaining secant stiffness <10% of that damage pattern’s initial stiffness. Censoring at 0.24 is reported separately. No direct biological, clinical, age or species inference follows.

## Equal-material-budget contrast

The initial material measure sum(A L)=1 within each dimension with modulus E=1. The following equal-budget values are dimension-specific normalized model quantities, not pooled physical tissue energies.

| Family | Mean intact axial K | Mean intact axial endpoint work at equal budget | Mean modulus multiplier for matched K |
|---|---:|---:|---:|
| triangular2d | 0.43391161 | 0.00117371 | 2.3047 |
| fcc3d | 0.12733761 | 0.00128300 | 7.8532 |
| disordered3d | 0.12091540 | 0.00127808 | 8.2753 |

## Numerical checks and preserved negative result

Initial finite-increment diagnostic: 360 raw cases / 720 normalization rows, increments 0.01 and 0.005. 51/180 pairs changed work by >5%, maximum 30.91%; 13 changed censoring status. Those results are not used as the primary failure-work estimate.

Primary event-resolved follow-up: 180 cases / 360 normalization rows, plus 18 stricter-tolerance controls. No failed solves; largest explicit equilibrium residual 9.997e-11. Maximum intact stiffness-match error 1.11e-16. Maximum equal-budget external-work minus stored-plus-released energy error 5.421e-19. Tightening force tolerance 1e-10→1e-12 for seed 101 across all 18 family/damage/loading combinations changes work by at most 2.603e-10 relatively, with zero changed censoring flags. This is a tolerance check, not independent full-model validation.

The separate CG/dense, analytic series-spring and energy-gradient checks passed. First preflight attempt failed because its gradient check selected a clamped node; the failed attempt source/log remains intact. Correcting that test preceded all scientific cases.

## Animations and FEniCSx table

Six event-resolved GIFs compare the same seed 101 under intact, clustered and distributed damage for tension and held-out shear. Left to right: triangular 2D (green), FCC 3D (amber), geometrically disordered FCC 3D (purple). Dim red edges are removed; minus-number is total removed/broken edge count. All panels follow the same prescribed strain; a panel freezes at operational failure. Each panel displays its actual strain. Displacements are not exaggerated. GIF pace is illustrative and is not physical time. The earlier six finite-step GIFs remain diagnostic assets only.

FEniCSx figures reanalyze previously saved output: 4,158/4,160 algebraic systems resolved (99.95%), while 1,341/1,600 observable mesh comparisons pass both tests (83.81%). Isotropic clustered: 368/400; isotropic distributed: 307/400; modular clustered: 374/400; modular distributed: 292/400. Acceptance requires mesh-relative response change ≤0.05 and damage-ratio difference ≤0.5 percentage points, plus original validity flags. Effect scatter excludes rejected rows; the interactive table keeps all rows. No new FEniCSx solve was performed.

## Raw-data recovery

`runs/` contains the failed preflight, finite-increment diagnostic and event-resolved follow-up in separate immutable IDs. Each run stores config, every raw trajectory and solve residual/iteration records, full input geometry/edge thresholds, summaries and numerical controls. `source/` contains complete original simulation, launcher, analysis and raster/GIF code; `visualizations/` contains every diagram, GIF, source table and a filterable HTML table. `logs/` contains execution stdout/stderr, sandbox probes and browser-check notes. The top-level MANIFEST.json seals every scientific payload file other than itself; publication receipts remain outside the frozen dataset. No file is omitted due to extension or size. Files above 95 MiB would use Releases; none in this run exceeds the threshold.

Remaining scientific work includes nonlinear/bending/recruitment sensitivity, random connectivity ensembles, size effects, exact removed-volume/grip-distance controls, transient pressure/acceleration/relaxation and independent experimental calibration. This bounded study does not close the full earlier falsification protocol.
