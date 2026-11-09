# Martini LINCS diagnosis — bounded CPU test complete

The recovered full HLKNL system completed **800.0025 ps (145455 steps)** at the original **5.5 fs** timestep on the approved isolated local CPU runtime, beyond the original **586.591 ps** failure. No LINCS warnings or fatal errors were found. **The original instability's root cause remains unresolved.** Launcher defects have concrete repairs and regression evidence; a production dynamics fix has not been demonstrated.

## Full-system verification

The 243134-bead system used the recovered preconditioned coordinates and velocities, topology, loading, 303 K NPT settings, original thermostat seed −25559649, table extension 10, nstlist 100 and Verlet-buffer tolerance 0.0001. Logging and checkpoint frequencies increased. Native ARM64 CPU GROMACS 2022.5-Debian_2022.5_2 differs from the original x86 CUDA 2023.2-dev-20230712-a3d6917-dirty-unknown build. This was not a bitwise replay or a build/backend-controlled comparison.

Return code was 0. All 1456 time-resolved logged energy/constraint samples were finite. Temperature ranged 300.833–305.167 K; maximum logged constraint RMS was 2.17882e-05. Pressure ranged -1522.30–-1453.35 bar in this strongly tensile loaded setup. Finite pressure does not establish equilibrium, correct loading, or agreement with the published physical benchmark. The configured reaction-field dielectric is infinite by design; it is not a measured nonfinite energy.

Final coordinates contain all 243134 beads, with finite coordinates, velocities and box entries. Final and previous checkpoints, energy file, observable trajectory, logs and processed input are preserved. The log records a final checkpoint at step 145455; the binary checkpoint was not independently restarted or decoded in this closing audit. Dynamics ended 2026-10-31 22:37:34 UTC after 38 min 20 s, before the shared 23:04:04.930 UTC deadline. The study container was absent on Docker readback. No new cloud/GPU compute was started.

## Original failure and causal limits

The first violation was a VAL BB–SC1 constraint in col_9: global beads 21211–21212, local 462–463, target 0.292 nm. Later failures included ALA BB–SC1, local 883–884, target 0.270 nm. These are isolated constraints, not native crosslink constraints or large coupled LINCS graphs. The terminal PDB-write error followed existing divergence because the launcher used a read-only working directory. Fixing that directory repairs evidence capture, not the preceding instability.

No global temperature explosion appears in the original recorded samples. Local contacts, neighbor-list treatment, build/backend behavior or other numerical sensitivity remain candidates. Official GROMACS [2023.3 release notes](https://manual.gromacs.org/documentation/2023.5/release-notes/2023/2023.3.html) describe a coarse-grained Verlet-buffer correction (4885) and virtual-site velocity correction (4879). Neither is established as this run's cause. The CPU build also predates these fixes; its success does not prove a GPU defect.

Both reduced intact col_9 helix tests completed 700 ps without LINCS warnings, at 5.5 fs and 2 fs. They used new solvent packing and NVT. Runtime neighbor-list autotuning also differed (nstlist 50 versus 100). They are not a controlled timestep-only comparison. Artificial neighbor-stress tests did not reproduce LINCS in any of three modes.

## Reliability repairs and regression evidence

The deliberate invalid-velocity negative control wrote four diagnostic PDBs in writable output. Its default-warning-limit run returned exit code 0 despite three LINCS warnings; strict warning-limit mode failed immediately. This verifies that successful exit alone cannot classify a scientific run.

`runner-reliability.patch` and `candidate_runner.py` prepare unique attempt names, writable case directories, frequent checkpoints and failed/incomplete/completed states gated by warnings and final simulation time. Candidate syntax checking passed and its underlying warning/PDB behaviors were tested in isolation. The candidate runner has not been deployed or run on H100. Strict fail-fast mode can abort before diagnostic PDB writing; diagnostic mode must still classify warnings as failure.

## Decision

The full CPU replay establishes a diagnostic path beyond the failure time, and the launcher repairs address verified defects. It does not establish that reducing the timestep is necessary, that the GPU caused the failure, or that production dynamics are fixed. A single 0.8 ns trajectory cannot validate 45 ns stability, the archived 30 ns exclusion requirement, ensemble uncertainty or molecular-to-network calibration. PYD production and hydroxylation-matched control validation remain untested here. No calibrated adhesion-force or YAP/TAZ claim follows.

Before a paid retry, the next experiment should use a reviewed maintained engine, explicit effective neighbor-list settings and a short build/backend-controlled comparison with warning gates and preserved diagnostic output. That experiment has not been started. The public explorer's existing failed/untested calibration status remains appropriate.

Receipts: `final-validation.json`, `runner-regression-checks.json`, `reduced-validation.json`, `full-replay-v002/finished.json`. Runtime supply-chain limits remain documented in `SECURITY_REVIEW.md`. Original and negative-control failure evidence is preserved.
