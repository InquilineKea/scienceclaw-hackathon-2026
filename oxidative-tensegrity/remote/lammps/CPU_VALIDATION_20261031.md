# LAMMPS CPU repair: completed commissioning

31 October 2026. The repaired reduced-network model passed **41 CPU checks** on the existing GCP host. The exact tested exporter was applied to the shared project, and all six prepared material inputs were regenerated. Previous source/decks, failed attempts, exact execution source and numerical outputs are retained. **No paid GPU run was launched and no cloud instance was created, started, stopped or modified.**

## Repairs applied

- Rheology output contains explicit time. A phase-aware sinusoidal fit uses that time and reports the retained cycles, offsets and residuals. Clock-free legacy two-column files require an explicit sample interval. This removes the approximately10x loss-modulus scaling error for the old0.1 output interval.
- Stretch coefficients are preserved without rounding; collagen and elastin contributions are combined without duplicate bonds. Each continuation hinge retains kappa*sqrt(kappa_b[in]*kappa_b[out]); junctions retain their individual stiffness.
- GAG embedding targets follow the affine reference, including initial prestrain. Current unwrapped coordinates come from a property/atom compute. Forces and potential energy are included consistently. Configurational stress includes the derived affine-tether contribution; thermostat and kinetic stresses are excluded explicitly.
- Exact angular energy, forces and virial are supplied through a single-rank CPU library callback. Native angular coefficients are deliberately zero. Runtime orientation guards reject leaving the commissioned junction sector. Bare lmp execution cannot replace this driver.
- Driven output refreshes force/virial at the same time as sampled strain. Continuous start/stop bounds preserve the imposed oscillation across output blocks. A partial final output block ends exactly at the requested run time.
- Generator/run instructions and the shared status/queue were updated.24 deck/data/base/sidecar files were regenerated for the six supplied width32 presets. Contact, sliding chemistry, rupture and biological calibration were not invented as part of a numerical repair.

## Validation evidence

The CPU engine reports LAMMPS22Jul2025 Update2, from pinned Linux wheel2025.7.22.2.0 with MPICH4.3.2 and one OpenMP thread. Numerical libraries ran only remotely in isolated workers with no network/home/credential access and read-only dependency/runtime mounts. No NumPy/LAMMPS simulation dependency was executed on the Mac.

| Check | Observed result |
| --- | --- |
| Final core suite |26/26 passed |
| Energy and supplied-preset extension |15/15 passed |
| Matched-state native/reference energy maximum error |6.63e-16 model energy units |
| Matched-state native/reference force maximum error |8.17e-14 model force units |
| Native/reference stress maximum error, including equilibrium comparisons |1.78e-10 model stress units |
| Driven storage-modulus relative change,dt.01 to.005 |9.02e-9 |
| Driven loss-modulus change scaled by storage modulus |6.27e-9 |
| Undriven NVE maximum relative energy drift |2.52e-7 |
| Undriven damped system plus bath maximum relative energy drift |3.95e-7 |
| Supplied material presets |Six presets each checked at widths8 and32:64 and1024nodes respectively |
| Retrieved remote files |327 hashes verified; all match |

The supplied-preset row refers to matched-state native energy/force checks, **not a completed full six-material dynamic rheology sweep**. Independent equilibrium checks compare LAMMPS FIRE with an independent analytic reference plus SciPy L-BFGS at four small shear values. Each of the two uniform driven trajectories has601 saved frames, all checked for geometry/branch validity. Analytic response checks vary frequency, phase, sampling interval and irregular times. Tests also cover legacy-clock rejection and exact final time with a non-divisible cadence.

The driven uniform reference has G_storage0.4936339356 versus0.4936339311 at the two steps. Its G_loss is about5.19e-8 versus4.88e-8: effectively a near-elastic numerical commissioning case, not a measured collagen loss modulus. The absolute loss-error criterion is scaled to storage to avoid an ill-conditioned relative comparison near zero. It does not establish accuracy for every dissipative network or loading frequency.

## Why commissioning required changes beyond the initial audit

The first attempt exposed an unsupported direct unwrapped-coordinate variable, repaired through the documented property/atom compute. The second attempt had matching energy but failed force agreement near straight hinges. Upstream harmonic-angle source uses a sin(theta) floor of0.001; that regularized force differs from the derivative of the source atan2 bending energy. The exact CPU callback fixes this discrepancy instead of weakening force tolerances. The original unsigned-angle limitation also motivates explicit orientation checks.

The third attempt passed conservative mechanics but had time-step-dependent negative apparent loss. End-of-step box updates were paired with an older force virial. Synchronized resampling removes that artifact. The initial relative-loss convergence criterion was replaced during commissioning by an explicit storage-scaled absolute loss criterion, while preserving the failed attempt. This was adaptive numerical development, not a preregistered scientific comparison. A passing fourth attempt was retained; the final run repeats the full suite after adding runtime orientation enforcement and partial-block stopping.

The independent analytical-force implementation was itself checked against finite differences. Passing numerical correspondence validates the defined reduced model, not collagen force-field accuracy, measured relaxation kinetics, nonlinear fracture behavior, fluid mechanics or biological aging.

## Remaining scope and GPU decision

This is a **single-MPI-rank CPU reference**. The exact angular Python callback has not been commissioned for GPU production; a separately reviewed native implementation or an explicitly justified alternate constitutive law must pass equivalent CPU/GPU checks first. The supplied full six-system dynamic sweep was not launched. Do not bypass this with bare lmp or an acceleration suffix.

The model remains2D, reduced-unit, elastic/embedded with phenomenological damping. The default zero-temperature reference is not a310K molecular simulation. No excluded-volume contact, calibrated fibril sliding, bond rupture, GAG binding or reaction kinetics is supplied. Undriven energy accounting is checked; full driven-flow thermostat/work accounting remains a separate validation question. The original lattice builder and its topology assumptions are unchanged.

## Reproducibility and local application

VALIDATION_SUMMARY.json gives the numerical summary. source/ contains final tested exporter and harnesses; retrieved/ contains remote sources, manifests, output/decks and all numerical failed attempts. SOURCE_CHANGES.diff describes the exporter/generator changes. APPLIED_CHANGES.json records applied files; before/ retains earlier prepared inputs and source. The runtime wheel hashes/provenance and upstream regularization source are documented separately. Registry/RECORD hashes are not independent vendor attestation.

The approved Nebius CLI installation and read-only login/query are recorded in the separate nebius-connection-review output. It returned two instances without changing them. The profile's IAM capabilities are not inherently restricted to read-only; this task used only authorized read operations. No auth tokens or raw account response are included in this numerical packet.
