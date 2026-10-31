# Completed CPU density sweep

6,300 unique configurations; 12,600 solves at 480 and 960 steps. Seven architectures, three paired seeds, twelve loading directions, thirteen connector counts and two placement patterns (one shared zero-added control). See `DENSITY_METHODS.md` in the application for the exact model and interpretation.

All equilibria were valid. The fine results include 124 capped configurations. Metric flags: stiffness 0; work to failure criterion 412; failure strain 377; work before first bond damage 2; work before first collagen damage 30. Flags include resolution sensitivity and, where applicable, censoring and stopping-criterion changes. They are not a measured error distribution or evidence of biological validation.

At 0° with 24 added connectors, mean paired ratios across three seeds illustrate the placement dependence:

| Network and placement | Stiffness | Work to criterion | Failure strain | Work before first damage |
|---|---:|---:|---:|---:|
| Disordered / distributed | 3.048 | 1.428 | 1.056 | 1.300 |
| Disordered / clustered | 1.615 | 0.897 | 0.809 | 0.957 |
| Modular / distributed | 4.132 | 1.716 | 1.000 | 0.848 |
| Modular / clustered | 2.612 | 2.316 | 1.073 | 2.115 |

All displayed metrics in this table passed the selected paired checks. Results vary by angle, seed and architecture; these examples are not universal rankings. Work includes recoverable elastic energy and is not thermodynamic phase-change enthalpy, tissue toughness or irreversible dissipation alone.

The scientific workload took 763.6 seconds in a disposable four-vCPU Nebius container, Node v22.23.4, with no GPU. Runtime receipt confirms UID 65534 and tested socket denial. The console estimate was $0.15/hour, implying roughly $0.032 for the scientific workload alone, before startup/shutdown, storage and tax; this is an estimate, not an invoice. The authorized ceiling was $2.

`MANIFEST.json` is the unmodified job-generated manifest. `FINISHED.json` records completion. `VALIDATION.json` adds independent collection checks over all 6,300 raw records. `download-receipt.json` records the verified original ZIP hash. Source snapshots and both-resolution summaries are preserved.

The 199,139,567-byte `raw-curves.ndjson.gz` is held in [GitHub Releases](https://github.com/InquilineKea/scienceclaw-hackathon-2026/releases/tag/data-density-20261031-v1-15e00af6c6c2), with the lossless recovery index in [_release/](./_release/). The repository ZIP alone does not contain this large raw file. All raw bytes were verified against the job manifest and GitHub's uploaded-asset SHA-256.
