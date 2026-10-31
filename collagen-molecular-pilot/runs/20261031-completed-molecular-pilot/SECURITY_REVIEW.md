# Review for the bounded collagen fragment pilot

Date: 2026-10-31. Inspection only; this chat has not yet executed molecular software.

## Concrete execution proposed

Run `pilot.py` through `run_pilot.sh` on the existing Brev instance
`collagen-md-20261031` (`enjgg7tq5`). Eight conformers cover four neutral molecules:
N-methylacetamide, capped glycine, N-ethylacetamide (truncated isopeptide amide
motif), and 2,2'-biphenol (truncated dityrosine biaryl motif). Use the installed
NVIDIA ALCHEMI Toolkit FIRE2 optimizer with the cached MACE-OFF23 medium model.
This is **Toolkit batched geometry relaxation, not a BGR NIM service run**.

No instance creation, installers, dependency upgrades, new model downloads at
runtime, account changes, or interruptions of existing jobs. The launcher refuses
to start while another GPU process is present. Eight-minute inner deadline and
ten-minute outer timeout. At the live catalog rate of $0.845421/hour, ten minutes
is $0.1409035 in compute-equivalent time; this is not a billing invoice or a cap
on the already-running VM's total charges. Storage is separately listed at
$0.14965/GB/month; actual allocated storage and account credits are unverified.

## Findings

| Severity | Finding and evidence | Mitigation / residual risk |
|---|---|---|
| High | MACE checkpoint requires pickle-capable `torch.load(weights_only=False)`. `nvalchemi/models/mace.py:1123` uses this; `mace/calculators/mace.py:18` also globally enables non-weights-only loading. Checkpoint pickle has expected MACE/e3nn/torch globals, including graph reconstruction, which can execute code. | Only load in an isolated non-root, offline container. Hash verification does not prove safety. No host home, Docker socket, keys, tokens, or browser directories mounted. |
| Medium | Existing environment has a large transitive dependency tree with no complete independently verified wheel hashes/signatures. Versions include torch 2.14.1+cu130, mace-torch 0.3.15, aimnet 0.2.5, RDKit 2024.9.6, ASE 3.24.0, and toolkit-ops 0.5.0. | Reuse read-only environment; no installation. Native libraries and compiled kernels were not comprehensively reverse engineered. Residual supply-chain risk remains. |
| Medium | Upstream `pyproject.toml:132` uses `unsafe-best-match`; many dependencies have lower bounds only. CI uses mutable action tags; pre-commit hooks use tags. Makefile can download a scanner. | Do not run installers, Makefile targets, CI, pre-commit, or upstream examples. Existing build provenance is incomplete. |
| Medium | Existing Brev-generated SSH configuration enables agent forwarding and disables host-key verification. | Inspection connections now use `ForwardAgent=no`, `AddKeysToAgent=no`, no multiplexed connection reuse, and a workspace-specific known-hosts file. The first host key was accepted using trust on first use; it was not independently fingerprint-verified. Global configuration is unchanged. |
| High scientific | `alchemi_crosslinks.py` uses an approximate glucosepane core and neutral pyridinone proxy under the name pyridinoline; it can derive automatic network stiffness overrides. | Do not use those values to calibrate tissue mechanics. New pilot names each truncated motif explicitly and exports no stiffness or rupture-force parameter. |
| High scientific | Installed `nvalchemi/models/aimnet2.py` explicitly disables Coulomb and D3 dispersion. Existing GAG code adds a screened electrostatic approximation to rigid-fragment energies. | Do not call the bare wrapper a full AIMNet2 molecular potential or claim binding free energies. Use neutral-organic MACE-OFF for the prepared pilot. |
| Medium scientific | Default BGR NIM MACE-MPA-0 is documented for periodic materials; MACE-OFF is not listed as a supported BGR NIM model. | Do not mislabel Toolkit execution as NIM. A literal NIM pilot needs a separately reviewed NIM image and compatible AIMNet2 v2 checkpoint, with nonperiodic mode. |
| Low licensing | MACE-OFF23 uses an Academic Software License (noncommercial academic use). | Prepared for the user's academic ScienceClaw experiment; retain license attribution. |

## What was inspected and verified

- Read local launcher, crosslink and GAG scripts, project instructions, and prior
  security review as contextual evidence, without treating historical approval
  claims as present authorization.
- Downloaded exact NVIDIA toolkit revision
  `84fe8e8fb8fab54863eea8f138722c7ab434966a` as inert source data. Compared all 316
  installed toolkit Python files with the matching source tree: **316 identical,
  zero different or missing**. Installed direct_url metadata names that commit.
- Inspected build metadata, lockfile presence, CI and pre-commit configuration,
  Makefile download paths, agent instruction files as untrusted data, and
  execution/deserialization/network-sensitive code patterns. No obvious secret
  theft or persistence mechanism was found in the inspected paths. This is not
  a guarantee that every source path and dependency is benign.
- Downloaded the public MACE-OFF23 medium checkpoint as inert bytes and compared
  against the Brev cache. Both SHA-256 values are
  `4842c52ad210d6e1f84d6cf1ffa70fae25a7e0d755ed55cf223f43913f587db7`.
  Inspected pickle opcode global references without unpickling. The public URL
  was a moving upstream `main` path; signatures and historical maintainership
  were not independently verified.
- Existing local Docker image ID is
  `sha256:78c6833ca878fd221957db5d580f7f2e9e31265b38656e97368caf23f12e24c8`
  for `python:3.12.7-bookworm`. This records local content identity, not a verified
  publisher signature. Launcher uses this ID and `--pull never`.
- New pilot syntax and shell syntax pass static parsing. Runtime validation is
  intentionally pending approval. No chemical library/model imports have been
  performed by this chat yet.

## Isolation and validation

New container runs as the remote user's numeric unprivileged UID, with no network,
read-only root filesystem, all capabilities dropped, no new privileges, 2 CPUs,
6 GB RAM, 256 processes, and a dedicated writable output directory. The existing
Python environment and model cache are mounted read-only. Temporary compiler
caches go to disposable `/tmp`. The script caps its PyTorch allocator to 25% of
GPU memory; this is not a hardware-enforced partition of the GPU. Only the new
container is removed on completion/timeout.

RDKit must sanitize every SMILES, verify connectedness/charge/radicals/formula,
confirm complete MMFF parameters, and converge the initial embedding. Model
atomic-number coverage is checked from the loaded checkpoint. Final forces and
energies are re-evaluated at final coordinates. Outputs require finite values,
force maximum <=0.02 eV/Angstrom, no gross bond distortion/atom overlap, and
non-increasing energy. These are numerical and geometry checks, not experimental
or quantum-chemical validation. Relative energies are computed only among
conformers of the same molecule.

## Approval required

The user's `/Users/LOCAL_USER/.codex/AGENTS.md`, section 5, says:

> Do not execute third-party code until I explicitly approve it after reviewing the findings.

Approval requested only for this bounded isolated pilot using the existing
environment and reviewed model, with the above residual risks. It does not
authorize deploying BGR NIM, installing GROMACS, broad ScienceClaw agent execution,
changing other jobs, or simulating unparameterized crosslink reactions.

Sources:
- https://docs.nvidia.com/nim/alchemi/alchemi-bgr/overview
- https://docs.nvidia.com/nim/alchemi/alchemi-bgr/custom-models
- https://github.com/NVIDIA/nvalchemi-toolkit/tree/84fe8e8fb8fab54863eea8f138722c7ab434966a
- https://github.com/ACEsuit/mace-off

## User-approved scope update during execution

The user explicitly approved the isolated pilot after reading this review.
They subsequently authorized a second, more powerful GPU because the hackathon
permits two GPUs and time is limited. The selected second configuration is one
Nebius H100 SXM 80 GB, 16 CPUs, 200 GB RAM, 100 GB disk, catalog $5.40/hour plus
storage ($0.12264/GB/month). It is stoppable. The existing L4 remains running.
This replaces waiting for or sharing the busy L4. No approval to modify or stop
that existing scan was inferred.

The approved installed Python environment is copied as files, along with the
same hash-verified MACE-OFF23 checkpoint. No package resolver or new installer is
needed. The same Python image is fetched by its recorded digest on the new VM.
The original isolation, runtime limits, and scientific validation apply. A
driver compatibility check is required before the new pilot runs.

## Runtime corrections within the approved isolation

Two failed attempts were preserved. The first revealed that legacy embedded
TorchScript buffers remained on CPU despite checkpoint `map_location`; an
explicit full-module `.to(device="cuda", dtype=torch.float64)` fixed placement.
The second reached force evaluation but Triton's generated helper library could
not load from Docker's default no-execute temporary mount. The disposable `/tmp`
mount now explicitly permits execution for these compiler artifacts, while
retaining `nosuid,nodev`; the rest of the filesystem remains read-only. Network
is still disabled, the user remains unprivileged, capabilities are dropped, and
no package or model changed. The third attempt completed successfully.
