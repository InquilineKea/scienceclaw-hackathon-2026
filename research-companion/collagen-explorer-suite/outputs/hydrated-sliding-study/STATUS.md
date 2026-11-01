# Hydrated collagen sliding — executed and published

Public explorer: https://scienceclaw-collagen-viscoelasticity.stochasticcockatoo.chatgpt.site/#hydrated-sliding

WordPress research page: https://humanavianaisymbiosis.wordpress.com/collagen-jamming-aging-crosslinks-mechanotransduction-scienceclaw/

All 36 planned explicit-water cycles completed on the initially idle existing H100, within the original one-hour wall ceiling. No new VM was created or started. The task-specific direct-host SSH port corrected the generated gateway-port mismatch; no global SSH configuration was changed. Both owned simulation containers exited normally and were removed. The pre-existing VM and unrelated workloads were retained.

Six molecular systems × three conditional velocity seeds × two ramp rates = 36 cycles. Total integrated time is 7.56 ns summed across separate 170/250 ps cycles; this is not a continuous 7.56 ns trajectory. Each model shares one prepared conformation and solvent build across its velocity replicas.

**Scientific outcome: 0/36 apparent stiffness estimates passed the declared molecular-to-network transfer gate.** All 216 graph × pair × rate × replica comparisons were excluded. No calibrated adhesion-force, cell-scale relaxation, tissue, YAP/TAZ or biological prediction was produced. This rejects transfer from this protocol; it does not establish that crosslinks lack mechanical effects.

## Endpoint observations

Baseline-corrected endpoint = last five forward samples minus last ten baseline samples, averaged within each replica. Intervals are exact independent-group percentile bootstrap over three velocity replicas per group, conditional on one starting system, not biological uncertainty.

| Linked coupon | Ramp (ps) | Linked minus control (pN) | Conditional 95% interval (pN) |
|---|---:|---:|---|
| GLU_LINKED | 40 | 116.15 | -87.24 to 357.50 |
| GLU_LINKED | 80 | 94.73 | -192.66 to 366.97 |
| PYD | 40 | -6.20 | -131.17 to 137.49 |
| PYD | 80 | 109.97 | -164.63 to 406.21 |
| DPD | 40 | -534.86 | -687.92 to -371.03 |
| DPD | 80 | -432.78 | -749.77 to -155.52 |

The large negative DPD endpoint shifts are retained. They are protocol- and starting-system-dependent observations, not evidence of a chemistry-only softening effect: ordinary-LYS controls change hydroxylation and charge, and the apparent stiffness gate fails. Native and glucosepane coupons also differ in context and valence.

## Controls, failures and provenance

The original four prepared molecular systems were retained. Native unlinked controls reconstruct complete ordinary LYS residues, hydrogens, charges, bonded terms and exclusions. The inherited source set lacks free HYL parameters; hydroxylation-matched native precursors remain unavailable. Do not interpret these controls as changing only crosslink connectivity.

Attempt 001 accepted no trajectories (six preparation failures). Attempt 002 accepted 23 trajectories and retained three failures. Attempt 003 repaired native-control sidechain clashes and isolated the bias energy in the force finite-difference check, preserving the same mechanics and tolerance; it supplied exactly the 13 missing trajectories. No accepted trajectory was rerun or duplicated. All three attempts are retained in the raw archive.

Native-case raw solvation metadata has a legacy CHARMM label. Static execution-path inspection and numerical input audits confirm Amber99/ColBuilder solute terms and amber14/tip3p.xml solvent/ion parameters for all cases. `forcefield-metadata-erratum.json` records the correction; raw files are unchanged.

## Network and physical-realism boundary

The authored network includes explicit linear bending and condensed series fiber/junction slip elements, a cell-shaped cavity, matched junction counts under uniform versus one-pole clustering, and fixed-law versus bulk-stiffness-matched comparisons. Independent rigid-translation, global-force-balance, energy derivative, Hessian symmetry and series-element checks passed. Because the molecular gate fails, the public maps show assumed geometry only, without invented force vectors. The earlier original and matched-stiffness models remain available unchanged.

The published Martini 3 collagen model is the next physical calibration gate. SI and Figure3 archives were downloaded, catalogue MD5/SHA256/ZIP CRC verified and inventoried; no author scripts executed. No fresh Martini trajectory or full fibril benchmark reproduction was completed. Published coverage includes HLKNL/PYD; glucosepane and a chemistry-matched native precursor require further parameter work.

## Validation and publication

All 394 raw files verified by SHA256 after path-safe archive extraction. The 41 release-input files match the verified full archive. All 36 planned case/replica/rate keys are present. Raw archive SHA256: `6f4bb1078bf0a2ebc0475448fcce071622158ce95b17e109e0d3fedc76ec973e`.

All six molecular selector combinations passed browser checks with expected sample counts and intervals, finite SVG coordinates and no duplicate IDs. The live DPD80 readout matched the saved analysis; console errors/warnings were absent. Narrow mobile layout had no horizontal overflow. Original density and earlier H100 network-size controls continued to update their results.

The published original HTML source and all earlier H100 assets are unchanged. Twenty-two public files were read back without authentication: numerical data, scripts, CSS, CSV, SVG and source ZIP exactly match the pushed release. Cloudflare adds its browser-detection script to the served HTML; removing that hosting insertion yields the exact source HTML.

WordPress received one visible paragraph linking directly to `#hydrated-sliding`. All 65 pre-existing block hashes are unchanged.

Version 3; commit `08fe597a97a2c94e6f4bc50122cce5419a109614`; deployment `appgdep_6ae63d2b727881919ded7a1cdbc5fec0` succeeded. The scoped credential handoff was explicitly approved and used only through the reviewed helper hidden stdin. A Git HTTP400 upload was resolved with a repository-local buffered transport setting, without changing TLS or authentication protections.

Public downloads contain displayed curves/summaries, network exclusions, provenance, benchmark readiness, numerical validation and authored analysis/source listings. The 253 MB complete raw archive is retained locally, not publicly uploaded. External forcefield distributions, prepared inputs and approval/account material are not included in the public source ZIP; it is not a turnkey reproducibility bundle.

Evidence: `publication.json`, `publication-readback.json`, `retrieval-verification.json`, `browser-selector-qa.json`, `PROTOCOL.md`, and screenshots.
