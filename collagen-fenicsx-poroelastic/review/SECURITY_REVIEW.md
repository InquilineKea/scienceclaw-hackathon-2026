# FEniCSx remote pilot security review

Reviewed 2026-10-31 before execution. User approved a new CPU-only budget up to $0.50, 30-minute workload limit. No paid resource has been launched at the time of this review. The global remote-execution exception applies after reporting this review; local third-party execution has not been approved or performed.

## Reviewed runtime

Official `ghcr.io/fenics/dolfinx/dolfinx:v0.10.0-r1`, Linux amd64 manifest pinned to `sha256:f3e532f96eb91454f13e7aae5289990cd0348124302c003a2002b4cfadb26b1a`. Manifest/config SHA-256 verified. Image metadata records creation 2025-11-11 and 1,068,896,086 compressed layer bytes. No ENTRYPOINT; default command is bash. The immutable image will be used directly, without rebuilding or running installation scripts.

Inspected the official end-user and test-environment Docker recipes at DOLFINx v0.10.0.post5, and the pinned image configuration's build history. These recipes are contextual and do not prove an exact source-to-binary match. The image history records a slightly different ADIOS2 build version. The non-lab image is selected; Jupyter is not started and no service is exposed.

## Findings

- **Medium residual supply-chain risk:** historical apt/pip dependencies, tagged source downloads and several PETSc dependency downloads were not all hash-pinned during the vendor's build. Compiler, MPI, PETSc, SciPy and JIT components expand the execution surface. A pinned image prevents later tag drift, but does not authenticate every contained binary or establish safety. No signature verification or full binary/source audit was completed. No package installation is part of this job.
- **Medium initialization network window:** MPI/FEniCSx runtime initialization may require local communications. The unprivileged child imports the numerical runtime first, with a scrubbed environment and only public scientific inputs available, then installs and tests a seccomp socket-denial filter before mesh assembly or solving. It receives no user credentials, personal files, browser state or host mounts. A runtime import could perform network operations before the filter; this residual risk is disclosed rather than represented as full-lifetime network isolation.
- **Low source execution risk:** the newly authored scientific code reads the bounded input archive, assembles finite-element operators, solves linear systems and writes task results. Static inspection finds no external execution, credential search, persistence, privilege escalation, eval/exec or runtime downloads. DOLFINx JIT invokes a compiler in a task-owned cache; that is expected numerical-runtime behavior.
- **Low transport/archive risk:** input names and SHA-256 hashes are allowlisted before extraction; output is confined to the task directory. The parent alone reads/writes the private object-storage mount. The child runs UID/GID 65534 with core dumps disabled, bounded file size, and a process-group timeout. The bootstrap retains no cloud credential in the child environment.

The image and its dependencies are not executed on the Mac. Use a disposable remote CPU job, no GPU, no privileged container, no host Docker socket, no personal mounts, no shell installer and no open application ports. Download and verify SHA-256 receipts before cleanup. Static review cannot guarantee safety; the disclosed binary-provenance and initialization-window risks remain.

## Corrected attempt

The first launch reached mesh construction but stopped on an outdated Python argument order; no scientific outputs were produced. DOLFINx 0.10's versioned documentation confirms create_mesh(comm,cells,e,x). The constructor call was corrected. MPI automatic finalization is disabled for this disposable single-rank process because its shutdown attempted an OFI transmission after socket denial. The socket filter itself remains unchanged. Original inputs, failed-attempt diagnostics and corrected hashes are retained. No new dependency, permission, personal mount or network exception was introduced.
