# CPU density-sweep execution review — 2026-10-31

Scope: one disposable Nebius CPU job, 4 vCPUs / 16 GiB, private endpoint, 100 GiB container disk, one-hour provider timeout, 20-minute child watchdog, 25-minute outer watchdog. Four-vCPU console estimate: $0.15/hour before discounts/tax; the eight-vCPU attempt was rejected before provisioning by the existing tenant quota; user approved CPU compute up to $2. No GPU is requested or used. Only this task's result bucket and resources may be cleaned up.

## Inspected source and runtime

The six original JavaScript files are model.js, directional.js, aging.js, density.js, benchmark-density.js and check-density.js. The first three remain byte-identical to the published crosslink experiment. The new analysis is postprocessing; the sweep uses worker_threads and fs/crypto/zlib standard APIs, with no package installer, network client, credential lookup, hooks, dynamic dependency download or external model. Local checks ran only original authored code on an existing runtime; no third-party image was executed on the Mac.

The remote runtime is official docker.io/library/node@sha256:94c973596a8581a87ba42746ceb0b0e0b5246d098de45b1ce04dcc967cfc5dfb, Linux amd64, Node 22.23.4, created 2026-10-28. Inspected registry index, platform manifest, image configuration/build history, Node Dockerfile, buildpack-deps parent recipes and entrypoint. The recipe uses Debian packages and signature/checksum-verified Node/Yarn downloads. The job bypasses the image entrypoint and never invokes npm, yarn, compilers or package installation. Image/runtime binaries, transitive Debian packages, signatures and reproducible-build correspondence have not been independently established; digest pinning identifies bytes, not safety.

## Findings and mitigation

- Moderate supply-chain risk: official but third-party Debian/Node runtime and a larger development base than strictly necessary. It supplies both Node and Python for an OS-level isolation wrapper without runtime package installation. Use a disposable credential-free job, pin the image digest, and run only bounded original code. No unexpected executable hooks were identified in the inspected entrypoint/recipes; binary safety is not proved.
- Moderate bootstrap privilege: Python starts as the container user to prepare files. Scientific children drop groups/GID/UID to 65534, use a cleared environment, no_new_privs and resource limits. No SSH key, registry credential, service secret, host directory or personal data is supplied.
- Network protection: a Linux x86_64 seccomp filter denies socket/connect/bind/listen/send/receive syscalls in each scientific child and its descendants. The wrapper tests an IPv4 socket and requires EPERM before execution. Image pulling and the provider-managed private output mount require platform networking outside that child filter. Unsupported architecture or failed filtering aborts the job.
- Moderate spending/retention risk: one-hour provider cap and shorter workload watchdog; results are compressed and capped below 1 GiB. Estimated compute at the one-hour cap is below $0.28 before tax, below the $2 authorization. Download and verify outputs before removing disposable resources.
- High scientific interpretation risk: dimensionless hypothetical connectors do not represent calibrated molecular crosslinks, chronological age or a thermodynamic phase transition. Report damage onset and mechanical failure separately, keep capped/invalid/resolution-sensitive results explicit, and retain both coarse and fine curves.

No new third-party execution on the Mac is authorized or performed. Remote execution follows the user's global remote-execution exception after this review. This inspection is not a guarantee of software or scientific correctness.
