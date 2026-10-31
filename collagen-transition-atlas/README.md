# Collagen transition atlas

A separate, bounded mechanistic follow-up to the frozen Fracture Atlas. The code addresses a seven-part critique by distinguishing strain-driven rigidity, sliding, stiff-bond placement, damage, inclusion contact, plastic memory, statistical thermal sensitivity and hypothetical LOX feedback.

Read [METHODS.md](METHODS.md) for equations, controls and scientific boundaries and [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for the reviewed remote runtime. [Related studies](RELATED_STUDIES.md) distinguish this pilot from the larger matched-stiffness experiment.

## Files

- `core_network.py`: frozen user-owned baseline geometry and periodic-network primitives; provenance is in `BASE_PROVENANCE.json`.
- `transitions.py`: explicit mechanical, plastic, contact, feedback and transfer-matrix laws.
- `run_transitions.py`: numerical checks and append-only experiment profiles. Every sampled mechanical state stores residuals and convergence flags.
- `plot_results.py`: numerical figures and animations from recorded states.
- `sandbox_exec.py`: remote unprivileged execution with Internet sockets denied.
- `audit_results.py`: independent standard-library checksum and numerical readback.
- `independent_replay.py`: scalar-math energy and finite-difference spot checks on saved coordinates; imports no numerical packages.
- `prepare_transport.py`: reproducible v4 packaging from the frozen v2/v4 inputs for the provider request limit; execution still verifies both reconstructed hashes.
- `build_explorer.py`: standard-library export of eligible curves to a static browser explorer.

The exact dispatched bootstrap, source ZIP identity, job logs and results belong in a separate frozen dataset. Source added for subsequent auditing is not represented as code that ran in the H100 job.

## Remote execution

The scientific worker requires an already reviewed NumPy/PyTorch environment and a compatible GPU driver. The recorded job uses a digest-pinned official PyTorch container and checksum-pinned plotting wheels. Do not infer local execution approval from this README. The user requires a security review before third-party execution and separate approval for new local third-party execution.

Run directories must not already exist. A run allocates one directory, snapshots source, saves full JSON records, and writes `FINISHED.json` or `FAILED.json` plus a SHA-256 manifest. A process killed by a hard watchdog may leave only a partial directory; the outer job archive preserves it and labels the attempt failed.

After remote output retrieval, verify the job archive and every recorded file hash. Store each attempt separately. Use the existing `upload-run.py --kind archive` workflow for a sealed archival bundle with explicit provenance. A completed archival transfer is not a claim that every scientific sample converged. Keep failures inside the bundle and leave their status unchanged.

## Scope

All networks are finite and two-dimensional. The constitutive parameters, time units and loading strains are not fitted to tissues. Locking is not an AGE dose; finite disks are not biological cells; graph eigenvalues are not a universal toughness score. There is no validated pressure or acceleration limit.

The thermal component is an exact finite statistical model with assumed coefficients, not molecular dynamics. `THERMAL_MD_GATE.json` in the numerical output explains why actual melting MD was not run. A mathematical LOX feedback model must demonstrate multiple stable branches and hysteresis before being called bistable, and even that establishes only the behavior of its declared equations.

The explorer applies cumulative history eligibility for plastic sliding, rupture and adaptive damage: a later converged state does not validate a prior failed update. Archived numerical figures retain their original pointwise labels, and must be read with the audit and captions. Missing derived values remain null, never substituted with zero.

## Completed v4 results

[Read the published results](https://humanavianaisymbiosis.wordpress.com/2026/10/31/collagen-transition-atlas-h100-results-sliding-contact-feedback/) and inspect the [immutable 350-file collection](https://github.com/InquilineKea/scienceclaw-hackathon-2026/tree/b4c9e52d26c3cdb67d22ba71173cc035177cc310/datasets/20261031-collagen-transition-v4). The H100 run accepted 398/400 mechanical states; 34/36 recorded paths fully converged. Both failures are in the contact/compression sweep. Independent scalar calculations verified all 238 saved-frame energies and force spot checks for 22 cases. Residual-strain estimates remain provisional and non-monotonic.
