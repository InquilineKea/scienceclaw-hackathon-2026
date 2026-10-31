# Matched FEniCSx poroelastic microrheology

Public explorer: [fluid-coupled microrheology](https://inquilinekea.github.io/scienceclaw-hackathon-2026/poroelasticity/).

This directory preserves a controlled comparison between the original discrete collagen network with uniform nodal drag and the same solid coupled to a FEniCSx Darcy/Biot pressure field. It includes the exact sparse solid inputs, authored simulation/analysis code, immutable runtime metadata, numerical checks and publication assets. Results are normalized exploratory mechanics; they are not calibrated age, species or tissue measurements.

See [methods](web/METHODS.md) for equations, boundary conditions, matching, pressure-mesh checks and limitations, and [security review](review/SECURITY_REVIEW.md) for the remote runtime and residual supply-chain risks. A pinned image digest is not a full source-to-binary verification.

`job/solid-source/` is the unchanged original atlas mechanics. `network-original.js` preserves the prior microrheology geometry/tangent builder with import paths adjusted. `export-network.js` exported forty exact paired sparse Hessians. `networks.json.gz` is the input to the FEniCSx run; `baseline.json.gz` is the prior published result for replay validation. `coupled.py` assembles the operators and solves; `plot.py` generates comparisons, validation, figures and harmonic GIFs remotely. No package installation or third-party numerical execution was performed on the Mac.

The first runtime attempt failed before solving because the constructor argument order had changed. Its exact input and diagnostic archive remain under `attempt-1/` and `job/poro-inputs.zip`. The corrected input is `job/poro-inputs-v2.zip`. Review the attempt records before interpreting a successful launcher or image pull as a scientific result.

## Completed result

DOLFINx 0.10.0.post2; 40 networks, 4160 systems and 4158 algebraically resolved. The two excluded static damaged modular drag systems retain their explicit flags. 1341/1600 paired observable comparisons pass the two pressure-mesh tests. Maximum resolved residual 1.85e-14; matched prior drag replay error 1.05e-09. The manufactured Darcy L2 refinement ratio is at most 0.2560. See `web/validation.json` and `web/comparisons.csv` for coverage rather than assuming every response is mesh-converged.

The successful numerical sweep took 11.4 seconds; with plots/animations the scientific child took 39.7 seconds. Provider UI showed a 40-second workload after startup. CPU-only, no GPU. The quoted resource estimate was $0.15/hour including ephemeral storage, billed per second including startup/shutdown; this is not a settled invoice. Both attempts completed/stopped within the approved $0.50 ceiling using about 6 minutes of combined provision-to-completion wall time. Temporary object storage is handled separately after verified download.

The preserved result ZIP SHA-256 is `6efceca6cbde6461a938cd7bbf8568325a90334e1d51eb55dbd406189eebca73` (25,570,444 bytes). `RUN_RECEIPT.json` records the exact input/runtime/output hashes.
