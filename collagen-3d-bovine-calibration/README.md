# Bovine bulk-calibrated 3D collagen comparator

This is a conditional mechanical sensitivity study using synthetic periodic Voronoi-derived networks. It is not a measured bovine architecture, chemically calibrated aging model, species-strength model, or measured fracture-toughness law.

## Recorded coverage

- 160/160 final cases recovered; 160 complete trajectories, four synthetic seeds, two shear planes, baseline/two locking fractions/two placements, two assumed rupture strains and25/50load increments.
- 80/80 resolution pairs; 0 pass the strict numerical tier and 58 pass when marginal selected-state curvature is retained explicitly as conditional.
- 3 pairs additionally qualify resolved-peak endpoints. Maxima at the strain cap remain censored. Work through a cap is not toughness.
- Complete small-strain stiffness comparison:40/40accepted states. Four1%amplitude baseline checks accepted, including a preserved continuation rescue forseed30.

## Calibration

The existing Kelvin–Voigt fit uses ten bovine dermal type-I hydrogel frequency sweeps,0.8/1.5/2.3mg/mL,37°C,1%oscillatory shear,primary0.1–1Hz. At1.5mg/mL,G′=9.522Pa and G″=3.891f(Hz)Pa; homogeneous parallelη=0.6193Pa·s. Mean whole-file model-selection CV complexNRMSE0.498. This is model-selection within one source study, not untouched independent validation. The1–10Hz challenge is excluded from calibration.

Each seed receives one energy-density factor from its mean xy/xz1%amplitude response; that factor stays fixed for interventions. This is baseline matching, not prediction of specimen-to-specimen architecture effects. The homogeneous loss closure is not microscopic damping and is omitted from quasistatic fracture.

## What changes

Selected existing junctions have10× angular locking. Initial geometry, segment inventory and cell volume are fixed across paired placements; damage subsequently removes load-bearing edges. Clustered/distributed selections match selected-site degree counts, active-angle counts and summed angular coefficients. Local directions and segment lengths are not matched; see placement-geometry-diagnostics.json. No new graph edge is added. The10%/20%segment-extension rupture thresholds are independent assumptions, not measured aging chemistry. All angles incident to a broken segment are removed. No full3Danisotropy surface, RVE-size convergence, thermodynamic phase change or Gc is established.

## Numerical gates and provenance

Free-gradient tolerance1e−7, terminal work/energy discrepancy≤2%, and paired work/stress step change≤5%. Fine cases receive physical-gradient Hessian checks at initial/observed-peak/terminal checkpoints. These labels may coincide. Marginal checks are not proof of stability along the trajectory. Damage precision and coarse/fine contrast signs are reported separately from work/stress qualification. Four seeds are the replicate units; loading planes and frames are correlated.

Original JavaScript commissioning and a separate standard-library equation/Hessian audit support the equations. A preserved100/200-step baseline agrees with JavaScript across all100positive states (energy relative difference5.66e−8,stress1.76e−5); cap-work step change0.00668%. Those are numerical controls, not biological validation.

The first CPU optimizer attempt and finer-grid controls are preserved separately. The first bounded production job stopped at its agreed deadline with54completed cases; continuation preserved all54JSON files bit for bit and scheduled only missing cases. Source function identities are recorded. The final collection retains failures and censored endpoints. Stale periodic partial files are excluded from this bounded public export when final records exist, and remain in the hash-verified local/provider transport archive.

## Reproduction

The original solver uses Python3.10,NumPy2.1.3 andSciPy1.14.1 in a pinned official remote Python image; package and image hashes are recorded. No installers or third-party numerical packages were executed on the Mac. Numerical scripts are under source/, inputs under inputs/, raw final records under results/, and CSV audits under analysis/. Historical launchers are not needed to inspect the results. Review code and runtime before executing; deadline and transport settings are task-specific.

The analysis script accepts --input, --out, --coarse-steps and --fine-steps. For primary results use25/50; higher-resolution controls remain separate. Do not combine incomplete trajectories with resolved fracture peaks or infer chemical AGE concentration from locked-junction fraction.

## Three research campaigns

Exact measured-architecture validation needs specimen-level coordinates/fiber paths/full distributions and matched nonlinear data currently available on request. See campaigns/CAMPAIGN1.md and the unsent data-request draft. The existing solvent/coupled dityrosine campaign is audited in CAMPAIGN2.md; no duplicate molecular run was launched. Campaign3 reviews public sequence provenance and comparable measurements without exposing private Drive material or asserting beaver robustness.

## Data attribution

Bovine rheology: Ruiz-Mateos Brea and colleagues, Zenodo [10.5281/zenodo.17413651](https://zenodo.org/records/17413651),CCBY4.0, supporting [Acta Biomaterialia2024](https://doi.org/10.1016/j.actbio.2024.07.002). Measurements are reformatted toCSV/plots; source hashes and limitations are retained. Published3Darchitecture summaries: [2025virtual-testing study](https://doi.org/10.1016/j.mtbio.2025.101962), cited facts only; full article and figure archives are not redistributed here.

Interactive artifact: https://inquilinekea.github.io/scienceclaw-hackathon-2026/bovine-3d/
