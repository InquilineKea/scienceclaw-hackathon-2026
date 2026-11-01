# GCP reproduction of the 2D fiber-rigidity workflow

Completed November 1, 2026, well before the 12:30 pm Eastern compute deadline. This is an independently executed CPU reproduction and expanded numerical test of the supplied workflow. It is distinct from the earlier continuous-fiber collagen–decorin–fibronectin study.

## Outcome

All 72 supplied demonstration states, all 2,178 expanded states, and all 16 tighter-tolerance check states converged. The expanded sweep took 396.237 seconds; the 16-state tolerance check took 2.894 seconds. These are measured solver/export times, excluding source review, dependency transfer, test suites and audits. No completed expanded state hit the 50,000-step cap. Raw failures from configuration/runtime setup are preserved separately and described in ATTEMPTS.md.

The workflow and ScienceClaw integration work under the tested conditions. Its two operational transition estimates disagree substantially, and this run does not establish a universal critical exponent or biological collagen mechanism.

## What actually ran

Public fiber-rigidity-sweep pinned at 5dcdca9676f29d66e63a2b665dfdb85d7173f039; ScienceClaw pinned at 894598cd3a90891a077c254566276bd379038bad plus the supplied validated metadata.category patch. Exact wheels, source hashes and execution controls are in SECURITY-REVIEW.md, PROVENANCE.json and the original source bundle.

GCP reported zero global GPU quota for the available project. The existing shared e2-standard-32 host was reused; no VM or quota change was made. Each simulation container had an eight-CPU ceiling, low CPU shares and 16 GiB limit. This was JAX 64-bit floating point on CPU, not an H100 test. The supplied 100,000-precursor-node H100 configuration was not executed. A fixed-step CPU benchmark measured 4.313 million node-iterations/second; the actual expanded sweep averaged about 2.507 million, including its compilation, exports and topology handling.

The expanded design used a 16×16 precursor lattice, target coordination z=3.2,3.5,3.8; bending stiffness κ=0.001,0.01; three paired topology seeds 0,1,2; and 121 logarithmically spaced simple-shear strains γ=0.001–1. Retained networks contained 238–256 nodes after phantom contraction, dilution and cleanup. Organization begins from a triangular lattice; the disorder comes from random phantom bypass directions and bond dilution, rather than arbitrary 3D fiber placement. Mean actual coordination was 3.202715,3.498034,3.796875. For a given z/seed, the same topology was reused across both κ values. κ is a bending-stiffness parameter, not a protein-chemistry control.

Solver settings were unchanged physics, independent affine starts, force tolerance 1e-8, max 50,000 steps, dt0=.02, batches 64. A separately declared 16-state check used seed 0, z 3.2/3.8, both κ values, and γ=.001,.01,.1,1 with force tolerance 1e-10 and max 200,000 steps. Every check state converged. Maximum relative stress difference was 0.0524945%; the tighter check is numerical tolerance sensitivity, not finite-size or mesh convergence.

## What the denser grid says

The table uses estimates computed from the three-seed mean curves. γ is dimensionless simple shear. The modulus criterion identifies the first persistent doubling above its own initial three-point median. The nonaffinity criterion identifies a strict interior maximum of total nonaffinity. They are different operational measurements.

| Target z | Bending κ | Modulus onset γ | Nonaffinity onset γ | Onset ratio | Conditional f, modulus onset |
|---:|---:|---:|---:|---:|---:|
| 3.2 | 0.001 | 0.074989 | 0.022387 | 3.35× | 0.294 |
| 3.2 | 0.01 | 0.23714 | 0.037584 | 6.31× | 0.181 |
| 3.5 | 0.001 | 0.1 | 0.018836 | 5.31× | 0.158 |
| 3.5 | 0.01 | 0.33497 | 0.066834 | 5.01× | 0.109 |
| 3.8 | 0.001 | 0.33497 | 0.022387 | 14.96× | 0.073 |
| 3.8 | 0.01 | 0.79433 | 0.089125 | 8.91× | Not determined |

The two onset estimates differ by 3.35–14.96 times. The modulus criterion increases with coordination at each tested κ. The nonaffinity criterion is mixed at κ=.001 and increases at κ=.01. These are finite-grid directions for these definitions; they do not establish a true critical strain, an extrapolated limit at z=4, or agreement between physical transition diagnostics. A relative doubling criterion also depends on the baseline modulus, so its trend should not automatically be read as a thermodynamic transition trend.

Ten of 12 conditional power-law fits passed the code's numerical fit gates; two remained unresolved. The five resolved fits using the modulus onset gave f≈0.073–0.294. The five positive fits using the nonaffinity onset gave f≈0.017–0.088; two of these conditional 95% intervals include zero, and the weakest fit has R²≈0.169. A program label of “determined” therefore does not by itself establish a convincing physical power law. All resolved fits used seven points in the predeclared onset-relative window. The high-z/high-κ modulus-onset fit remained unresolved because only four points fit before γ=1; thez 3.2/κ.01 nonaffinity-onset fit had no finite positive stiffening exponent.

This run did not reproduce an effective fitted slope near the workflow's displayed literature reference 0.7. It also does not refute an asymptotic literature exponent: the code fits total K without bending-background subtraction, at finite bending stiffness, small size and an operationally chosen onset. Its confidence intervals condition on that onset and fitting window and omit onset, finite-size, seed and bending-crossover uncertainty. Do not equate these local fits with a universality-class measurement.

## Validation and integration

- Full fiber Python suite:118 passed.
- Metadata-category patch:9 tests plus 28 subtests passed.
- Mutation checks:all 19 physics/analysis mutants and all 7 integration mutants detected by expected assertion failures.
- Viewer:syntax passed and 8 DOM-level Node tests passed. No real browser/WebGL or H100 validation is claimed.
- Actual patched registry:335 skills discovered; the new tool was categorized asmaterials, ranking sixth for “materials” and second for “materials science: rigidity in fiber networks.” These are observed keyword ranks, not an LLM assessment.
- Actual ScienceClaw executor:72/72 states; strict result JSON and identical scientific array hash after resume. Default poster created a materials draft without live publication or credentials.
- Independent audit of all 72 demo,2,178 expanded and 16 tight states: topology counts/coordination, checkpoint coverage, convergence flags/tolerance, energy descent and independently calculated stretching/bending energies and nonaffinity; local-polynomial modulus compared with saved finite-difference modulus. Selected stress checks use an independent energy finite difference, with selected coordinate-force checks at converged states. Seed-specific onset definitions were independently recomputed and matched.
- Expanded audit maximum absolute discrepancies:energy 1.11e-16, nonaffinity 0, stress 2.98e-11 over 54 selected states, modulus 3.77e-15; largest selected coordinate energy derivative 7.44e-9. These are in model units and are numerical consistency checks, not physical calibration.

## Scientific scope

The model is an athermal periodic 2D phantom triangular fiber network with harmonic stretching and same-fiber angular bending. It has no 3D topology, explicit excluded volume, thermal fluctuations, protein binding/unbinding, covalent chemistry, decorin assembly effects, fibronectin conformational unfolding, or experimentally calibrated collagen material scales. Independent affine-start local minimizations are not a quasistatic loading path and do not prove global energy minima. Three seeds and one expanded size do not establish finite-size scaling or robust ensemble uncertainty. The 16 selected tighter states do not validate the full dense-grid derivative or exponent against tighter tolerance.

The useful result is a functioning, contained and reproducible computational harness, plus a concrete demonstration that onset definition matters strongly even when force convergence is good. It is not evidence for collagen–decorin versus collagen–fibronectin biology.

## Records and integrity

The full GCP archive is 26,448,567 bytes. Its SHA-256 is 4f3cda7b6f868da3052d329b7fa858531399f865d8b73e3f8d9ac2aa30ada065. All 905 payload files plus the manifest were retrieved with exact inventory and SHA-256 verification. All 24 fiber-repository Python source files match the statically reviewed checkout. The first-stage 63-file snapshot is separately verified. The original archives and extracted records are retained. See VERIFICATION.json, archive-record.json and raw/results/SHA256-MANIFEST.json.

Preserved records include all setup/runtime failures, non-run partial manifests, exact generated configs, solver checkpoints and positions, per-seed summaries, conditional fits, raw viewer data, actual mutation-test reports, dependency hashes, controller/launcher history and container exit states. Installed environments/caches/native Node binaries are excluded from the result archive; exact wheel hashes and Node runtime file hashes are retained. No credentials or private keys were copied. Cleanup is recorded separately after local verification; the shared VM and remote task data are retained.

All seven task containers were removed after verification, with their absence checked. The cleanup receipt has its own remotely generated SHA-256. The shared VM, remote task data and unrelated work remain intact.

Additional source integrity: all 546 Python files in the retained ScienceClaw snapshot match the pinned, patched local source data, including registry/executor and copied skill. This establishes snapshot identity; unrelated skills were not executed or comprehensively security-audited.
