# Completed GCP 3D collagen–decorin–fibronectin mechanism study

The study completed all 1,088 planned production attempts. **1,082 cases passed and six were rejected**: four equilibrium-convergence failures and two 300-second timeouts. No planned case is missing. Failed cases and earlier commissioning attempts are preserved. The production sweep ran for 5,454.9 seconds (90.9 minutes), finishing October 31, 2026 at 8:51 pm Eastern, well before the workload cutoff. No new cloud VM was created.

The useful conclusion is that organization and the assumed protein connection law have separable, interacting effects in this reduced model. Changing architecture creates large baseline differences; changing the law on the same network gives smaller, condition-dependent finite-strain differences. This is a mechanism sensitivity result, not validation of tissue mechanics or a biological ranking of the proteins.

## What was simulated

There are 64 disordered 3D collagen-segment scaffolds: 512/1,024 collagen nodes × eight graph seeds × uniform/clustered positions × isotropic/axially biased connections. Each scaffold has 4N collagen segments, mean degree eight, minimum degree five, and a matched collagen-volume budget. These are central-force strut networks, not resolved continuous fibrils. The two sizes compare finite volumes at fixed number density, not numerical mesh resolution.

Each scaffold has an adapter-free control and 16 adapter conditions: two mechanical architectures × two laws × two initial arm stiffnesses (k=1,4) × two arm energy budgets (D=0.1,0.4). Decorin-like adapters have two arms; fibronectin-like adapters represent a four-arm assembly. Arm counts and total adapter mass are matched, but valency and placement are hypothetical. Neither architecture specifies a real protein molecule's stoichiometry.

Binding uses a finite-depth Morse well with designated partners. Locking uses an irreversibly breakable harmonic contact. At fixed k and D the laws share initial curvature and per-arm well/rupture energy, but their finite-extension force curves differ. No partner exchange or stochastic reaction kinetics are simulated. A locked decorin-like adapter is a counterfactual control, not a claim of native covalent decorin crosslinks.

## Organization produces a large adapter-free baseline effect

The table reports means of eight graph seeds per row. Stress is in reduced units at 20% engineering strain; recoil is the recovered fraction of a 15% preload extension after 20 reduced time units. All 64 adapter-free cases passed.

| Nodes | Spatial organization | Connection orientation | Stress at 20% strain | Timed recovery |
|---|---|---|---:|---:|
| 512 | Uniform | Isotropic | 0.08587 | 27.47% |
| 512 | Uniform | Axial | 0.31883 | 64.06% |
| 512 | Clustered | Isotropic | 0.07546 | 27.12% |
| 512 | Clustered | Axial | 0.33784 | 67.15% |
| 1,024 | Uniform | Isotropic | 0.08969 | 20.75% |
| 1,024 | Uniform | Axial | 0.36274 | 54.91% |
| 1,024 | Clustered | Isotropic | 0.07230 | 19.69% |
| 1,024 | Clustered | Axial | 0.33922 | 57.05% |

Preferentially axial connections increase the mean adapter-free stress at 20% strain roughly 3.7–4.7-fold across these size/clustering combinations. This intervention changes the connection pattern while matching segment count and collagen volume; it is not a pure change of one tissue descriptor. Clustering does not have one universal effect: its effect depends on orientation, size and strain. Initial clustered/isotropic stiffness also changes appreciably with size, so a stable bulk-size limit has not been demonstrated.

The independent geometry audit verified all 64 connected 3D graphs, edge and volume budgets, and adapter placement/counts. Realized axial orientation P₂ is near zero in isotropic networks and about 0.41–0.43 in biased networks. Density occupancy CV is about 0.71 for clustered positions versus 0.24–0.35 for uniform positions on the specified 4×4×4 binning. These descriptors quantify the generator; they do not measure fibril crimp, bundling or biological disorder.

## The interaction law matters beyond its initial stiffness

All 1,088 exact initial-response controls passed. At fixed scaffold, adapter architecture and k, changing law or D leaves zero-strain modulus invariant to a maximum relative error of 8.03×10⁻¹¹, as expected from the matching contact curvature. Thus the nonlinear law comparison starts without an initial-curvature mismatch.

The table below illustrates one fully paired sensitivity condition: **four-arm fibronectin-like assembly, k=4 and D=0.1**, locking versus binding on identical graph/site geometry. All eight seeds are available in each row. These parameter values are uncalibrated, and this is not an optimized or physiological condition. The full 64-condition table, including other k/D settings and decorin-like adapters, is supplied in CONTRASTS.csv and ANALYSIS.json.

| Nodes | Spatial organization | Orientation | Mean stress change, locking vs binding | Seed range | Mean timed-recovery change |
|---|---|---|---:|---:|---:|
| 512 | Uniform | Isotropic | 13.16% | 7.08 to 23.63% | 1.064 pp |
| 512 | Uniform | Axial | 2.20% | 0.94 to 3.74% | 0.111 pp |
| 512 | Clustered | Isotropic | 10.15% | 1.83 to 16.41% | 0.813 pp |
| 512 | Clustered | Axial | 1.79% | -0.42 to 3.22% | 0.140 pp |
| 1,024 | Uniform | Isotropic | 13.75% | 9.53 to 19.68% | 1.382 pp |
| 1,024 | Uniform | Axial | 2.39% | 0.05 to 4.99% | 0.492 pp |
| 1,024 | Clustered | Isotropic | 13.50% | 4.08 to 27.05% | 0.434 pp |
| 1,024 | Clustered | Axial | 3.66% | 0.84 to 6.22% | 0.111 pp |

The relative stress effect is about 10–14% in isotropic networks and 2–4% in aligned networks in this example. Leave-one-seed-out means remain positive for all eight rows. Individual outcomes are not uniformly positive: one clustered, aligned 512-node seed gives a small negative effect. Lower relative effects in aligned networks partly reflect their higher baseline stress. The absolute-stress difference-in-differences is variable and is not consistently negative across size/clustering; the full paired values are retained rather than inferring a universal suppressive effect of alignment.

For the two-arm decorin-like proxy at k=4,D=0.1, mean relative stress changes span approximately 1.1–10.1% across organization/size rows. One row has seven complete pairs because of a rejected binding case. This architecture comparison cannot establish which real protein stiffens collagen more: site geometry and valency are model assumptions, and native binding energies and densities were not measured.

Most law differences occur without locked-contact rupture. Only 15 of the 511 accepted locked cases show locked-contact damage in the tensile window. Matching initial stiffness and energy does not match the full force curve; these results therefore do not isolate irreversibility or reaction kinetics alone. Native chemistry would require additional calibration and controls.

## Recovery, damage and censoring

All 1,082 accepted cases reached the prescribed 20% strain endpoint. Collagen damage occurred in 371 accepted cases, with onset unobserved/censored in the remaining 711. No accepted case reached the major load-loss criterion (force below 20% of its running maximum after 10% strain); that endpoint is censored in every accepted case. Maximum stress in this finite window is not ultimate tensile strength, and there is no defensible strength ranking or biological Pareto optimum here.

Recoil is a transient measurement at fixed model time with damping and matched total mass. After preloading, survivor topology is frozen during release. The lower timed recovery of larger networks cannot be identified as permanent deformation; longer relaxation and volume sensitivity would be needed. The finite-time recoil differences in the illustrated chemistry condition are approximately 0.11–1.38 percentage points. Model time is not calibrated to seconds.

## Numerical and provenance audit

The accepted solver passed 16 pilots and 16 finer repeats at the production sizes. Maximum peak-stress refinement disagreement was 0.5563%, fitted 0–2% modulus disagreement zero, and recoil-fraction disagreement 0.000350. Analytical forces/Hessians passed finite-difference, rigid-motion and pair-balance checks. Earlier 60%-strain/time-budget attempts and controlled-strain convergence failures are retained with their source versions; the 20%-strain scope and trust-region fallback were introduced before production, with acceptance gates unchanged.

The independent final audit found no coverage, finite-value, geometry-hash, contact-budget, raw force-tolerance or recoil-energy violations among accepted cases. Maximum accepted tensile force residual was 9.9923×10⁻⁷, below the 10⁻⁶ gate; maximum relative recoil energy-ledger error was 2.5411×10⁻⁵, below the 0.01 gate. Numerical stationarity does not prove a global minimum or nonlinear stability. Of 64 organization/adapter/k/D law-comparison strata, 58 have eight complete seed pairs and six have seven; failures are not imputed.

The complete raw archive contains 9,250 files / 877,294,257 uncompressed bytes; its compressed size is 861,436,037 bytes. Archive SHA-256: `a378501ae3d1321ac27aa675309bfd5006ca4683dde6b8be214c756d4584b8e5`. Every file was verified after download. Frozen production source hashes matched. Credentials and private keys are excluded. After verification, the three study containers were removed and confirmed absent; the shared VM and original source/results were retained.

## Biological interpretation and next experiment

The most useful biological implication is to compare a protein present during assembly with the same protein added after assembly, while measuring both architecture and mechanics. Decorin's effects during collagen fibrillogenesis and fibronectin-supported collagen deposition motivate that distinction. A separately controlled Factor-XIIIa condition can test a real covalent collagen–fibronectin mechanism. None of those reactions or assembly pathways has been validated by this simulation. BIOLOGY.md links the primary studies and explains the evidence boundaries.

A stronger next model needs explicit fibril bending/continuity, measured orientation/bundling and pore distributions, protein occupancy and valency constraints, and experimentally supported force/energy/kinetic parameters. The present high-connectivity network omits solvent, excluded volume, cells, integrins, secretion, turnover and actual assembly kinetics. Its prescribed organization changes are counterfactual endpoints, not simulated fibrillogenesis. Eight graph seeds characterize generator variation, not biological confidence intervals.

## Files and archive status

- RESULTS.md: this report; BIOLOGY.md: biological evidence and experimental controls; PROTOCOL.txt: design and amendments.
- CASE-SUMMARIES.csv and FULL-CASE-SUMMARIES.json: all attempted cases, including failures.
- CONTRASTS.csv and ANALYSIS.json: complete paired condition/seed analysis and organization–law interactions; no hypothesis significance or biological uncertainty claims.
- AUDIT.json and GEOMETRY-AUDIT.json: independent raw-result and topology checks.
- linear-response.json: all exact initial controls; study/: commissioning/refinement gates.
- results.tar.gz, RESULTS-MANIFEST.json, RESULTS-RECEIPT.json and DOWNLOAD-VERIFICATION.json: complete verified raw archive and provenance.
- CLEANUP-RECEIPT.json: exact task-container cleanup; source/: executable source and original analysis/audit/retrieval helpers.

The completed local payload is ready for a separate, SHA-256-verified microSD archive copy. No new-study microSD copy has been performed under the completion-monitor approval.
