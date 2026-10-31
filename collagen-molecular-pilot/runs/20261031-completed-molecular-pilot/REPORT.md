# ScienceClaw collagen fragment pilot: execution report

Date: 2026-10-31. Times in raw logs are UTC; New York is UTC−04:00 on this date.

**Actual execution:** NVIDIA ALCHEMI Toolkit FIRE2 with MACE-OFF23 medium on NVIDIA H100 80GB HBM3. This used the NVIDIA ALCHEMI Toolkit, not the separately deployed BGR NIM service. The user approved this substitution after the static security review.

**Brev instance:** `collagen-pilot-h100-20261031`, ID `g1c2xtpht`. The existing `collagen-md-20261031` L4 (ID `enjgg7tq5`) was busy with a prior scan; the user explicitly authorized one additional more powerful GPU. This chat created one instance. The inventory contained two GPUs immediately afterward. A separate L40S instance (`collagen-md-l40s-20261031`, ID `hck82wx4n`) appeared later; the 09:43 UTC inventory contained three running instances. Following explicit user authorization, this completed H100 was stopped and STOPPED status was verified through the authenticated CLI; the L4 and L40S remain running. See the final lifecycle record in `resource_state.json`.

**Run label:** `collagen-fragment-pilot-20261031T094052Z`. Docker execution record: `5b3d8e42702a11dd5b6dc31f0e7f9a13fcce83fdb3317e295e7cb687c7d3b57a 0 false 2026-10-31T09:40:52.434375929Z 2026-10-31T09:41:33.230407102Z`. This is a direct container run, so the container ID and run label identify the job; there is no fabricated NIM service job ID.

**Outcome:** 8/8 conformers passed all recorded numerical and geometry checks. Measured script runtime: 36.687 seconds. Timeout: False.

| Structure | Atoms | Initial energy (eV) | Final energy (eV) | Change (eV) | Maximum force (eV/Å) | Passed |
|---|---:|---:|---:|---:|---:|---|
| peptide_bond_control_seed17 | 12 | -6767.21799893 | -6767.26149250 | -0.04349356 | 0.014684 | True |
| peptide_bond_control_seed29 | 12 | -6767.21800009 | -6767.26149286 | -0.04349277 | 0.014687 | True |
| capped_glycine_seed17 | 19 | -12431.57853678 | -12431.66078620 | -0.08224943 | 0.012987 | True |
| capped_glycine_seed29 | 19 | -12431.60396536 | -12431.69403311 | -0.09006775 | 0.013054 | True |
| isopeptide_amide_motif_seed17 | 15 | -7837.77488485 | -7837.81609226 | -0.04120741 | 0.011260 | True |
| isopeptide_amide_motif_seed29 | 15 | -7837.77489129 | -7837.81609716 | -0.04120587 | 0.011261 | True |
| dityrosine_biaryl_core_seed17 | 24 | -16712.65280223 | -16712.76979602 | -0.11699379 | 0.015416 | True |
| dityrosine_biaryl_core_seed29 | 24 | -16712.65280760 | -16712.76979603 | -0.11698843 | 0.015420 | True |

Two independently seeded starting conformers were used for each of N-methylacetamide (peptide-bond control), N-acetylglycine methylamide (capped glycine), N-ethylacetamide (truncated isopeptide amide motif), and 2,2'-biphenol (truncated dityrosine biaryl motif). They are neutral singlets with explicit hydrogens, totaling 140 atoms across the batch. The seeds are not a claim of exhaustive or unique conformer sampling.

RDKit sanitization, connectedness, formula, charge, radical exclusion, complete MMFF initialization parameters, and MMFF convergence were checked. Model element coverage was checked from the loaded checkpoint. Final energies and forces were recomputed at the final coordinates. The numerical target was maximum force ≤0.02 eV/Å. Geometry checks reject gross bond-length distortion and atom overlap; these do not establish quantum accuracy or experimental validation.

**Interpretation:** Relaxation lowers local model energy. Absolute energies of molecules with different formulas cannot be used to rank crosslink strength. No glucosepane, pyridinoline, or 4-HNE reaction was simulated. There is no tensile failure measurement, reaction barrier, free-energy calculation, explicit solvent, or tissue calibration here. The dityrosine and isopeptide entries are explicitly truncated motifs.

Two initial attempts failed during model placement and JIT-cache loading. Explicit CUDA placement for all model buffers and executable permission for the disposable temporary compiler cache resolved them. Their logs and container records are retained under `h100_runs/`; no dependency or model was replaced.

## Costs and resource state

The live catalog rate is $5.40/hour for the H100. The measured script runtime corresponds to $0.055031 of compute time. This excludes provisioning, transfers, image preparation, waiting, and any subsequent idle time. The H100 is now confirmed stopped. Requested storage is retained; exact billing and storage charges remain unverified. The catalog disk rate is $0.12264/GB/month; 100 GB was requested ($12.264/month at that rate). Actual invoice amounts, credit balance, exact billable storage, rounding, and network charges were not available from the queried CLI metadata.

Across all three attempts, the recorded container runtime totals 99.364 seconds, corresponding to $0.149047 at the H100 catalog rate. This also excludes setup and idle time.

The pre-existing L4 catalog rate is $0.845421/hour plus storage. No changes were made to its simulation or lifecycle. See `resource_state.json` for the final observed instance state.

## Earlier computations recovered separately

The existing L4 had a prior container `a764482e2959` running the crosslink scan. Its earlier GAG result contains 12 rigid-fragment pair scans and reports 34.451 seconds. A final read-only check recovered its completed MACE-OFF crosslink scan: eight proxy fragments, 21 anchor distances each, 2592.354 seconds, 419 maximum optimization steps and reported final free-atom force maximum 0.0197359 eV/Å. Full curves and fitted values are retained in evidence/existing_crosslink_params.json; they were not independently geometry-validated. The subsequent MACE-MP result file was not present at the 09:53 UTC check. The installed AIMNet2 wrapper disables long-range Coulomb and D3; the GAG script adds a screened electrostatic approximation. These are not full binding free energies and are not new runs by this chat. The approximate glucosepane and neutral pyridinoline proxy in the old crosslink script must not calibrate tissue mechanics.

The downloaded GROMACS archive passed all 122 entries in its recorded SHA-256 manifest. Its log identifies an L40S, not the current L4 or new H100. It contains an earlier 20 ps unmodified PPG9 sample with mean sampled temperature 299.1984 K, density 1009.1992 kg/m³, and pressure 42.6658 bar. This is a short baseline, not a new MD comparison or a validation of collagen mechanics. No new GROMACS/ALCHEMI MD comparison was run: the current scope prioritized the reviewed relaxation pilot, and no validated target-crosslink force field was available.

## Deliverables and reproducibility

- `pilot.py`, `run_pilot.sh`, and `restore_reviewed_environment.sh`: executed source and bounded offline launch/restore workflow.
- `pilot_run/`: real energies, forces, coordinates, initial/relaxed SDF files, convergence trace, console log, job/container IDs, timestamps, GPU snapshots, and provenance.
- `prepared/`: the earlier CPU preparation performed on the existing Brev L4, including an unsubmitted NIM-compatible request.
- `evidence/`: static source/model checks, package versions, prices, prior job logs, and transfer/cleanup records.
- `prior_gromacs/`: audited earlier MD logs/data with explicit separate provenance.
- `collagen-mechanics-explorer-with-brev-evidence.zip`: source-only updated existing explorer with the actual result files and a read-only evidence panel. Original mechanics parameters are unchanged. Integration passed static syntax checks; the Streamlit application was not executed in this task.

The model SHA-256 is `4842c52ad210d6e1f84d6cf1ffa70fae25a7e0d755ed55cf223f43913f587db7`. Toolkit revision is `84fe8e8fb8fab54863eea8f138722c7ab434966a`; all 316 installed toolkit Python files matched that revision. A complete independent supply-chain proof is not claimed. See SECURITY_REVIEW.md for the reviewed risks, scope, explicit approval, and isolation controls.

The multi-gigabyte software archive is kept in task scratch space and on the Brev VM, not embedded in the deliverable ZIP. Model weights are not redistributed in this package. Reproducing the environment from scratch requires a separate dependency installation review.

Sources: [NVIDIA BGR model documentation](https://docs.nvidia.com/nim/alchemi/alchemi-bgr/overview), [NVIDIA BGR API](https://docs.nvidia.com/nim/alchemi/alchemi-bgr/api-reference), [MACE-OFF model repository](https://github.com/ACEsuit/mace-off), [MACE-OFF paper](https://arxiv.org/abs/2312.15211).
