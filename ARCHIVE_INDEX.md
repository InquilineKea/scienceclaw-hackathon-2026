# Collagen scientific archive — 31 October 2026

This update adds the previously missing finished network atlas and molecular records. The existing oxidative-tensegrity results remain in their original paths.

| Dataset | Location |
|---|---|
| Frozen 450-run network atlas, corrected media and source | [collagen-network-atlas/runs/20261031-finished-f0a5034f44aa](collagen-network-atlas/runs/20261031-finished-f0a5034f44aa/) |
| Live explorer and non-overwriting run entry point | [collagen-network-atlas](collagen-network-atlas/) |
| Separate complete storage-workflow verification run | [collagen-network-atlas/runs/20261031-storage-verification](collagen-network-atlas/runs/20261031-storage-verification/) |
| H100 relaxations, L4 scans and comparison, source, logs, costs | [collagen-molecular-pilot/runs/20261031-completed-molecular-pilot](collagen-molecular-pilot/runs/20261031-completed-molecular-pilot/) |
| Previous 20 ps GROMACS PPG9 baseline, including saved trajectories | [collagen-molecular-pilot/prior-gromacs/20261031-ppg9-seed104729](collagen-molecular-pilot/prior-gromacs/20261031-ppg9-seed104729/) |
| Original archives and corrected frozen-atlas ZIP | [archives/2026-10-31](archives/2026-10-31/) |

## What is frozen

The network baseline has 450 run records, 24,414 sampled curve rows, 56 seed-17 replay cases and 3,246 saved frames. Five GIFs, their still images, the chart, methods, evidence ledger and numerical checks accompany the data. Parameters and source fingerprints are saved. These are hypothetical 2D network-model outputs, not experimentally validated collagen properties or a universal network toughness ranking.

The original rendering bundle contained earlier pulse/free rows. It is retained as historical input. Current diagrams and animations were regenerated from the final numerical records; final result/replay equality and image dimensions/frame counts were checked. The original ZIPs remain available as historical artifacts and are explicitly distinguished from the corrected frozen atlas.

The separate workflow-verification run reproduces the numerical records exactly, except run date and elapsed time. It verifies new-directory storage rather than adding independent scientific observations. Its nine numerical checks pass.

## Provenance and completeness

ARCHIVE_MANIFEST.json contains sizes and SHA-256 hashes of the files added by this update. Run-level manifests provide more focused verification. `python3 -I verify-archives.py` verifies the full added package without executing any scientific model or installing software.

The archive includes all available saved scientific raw data, code, logs and visuals in scope. It does not contain credentials, unrelated account records, GPU environment binaries or model weights. One local user-directory prefix in a scientific text record was replaced with `/Users/LOCAL_USER`; source and published hashes are retained in ARCHIVE_PROVENANCE.json. Original privacy-reviewed public packages and numerical records retain their bytes.

Replay states were originally sampled and retained only for selected cases. JSON exports use seven significant figures; curve CSVs retain their sampled-record numeric serialization. Unsaved internal states cannot be recovered from an archive. Prior GROMACS provenance and limited duration remain explicit. Molecular proxy curvatures are not inputs to this network model.

## Future runs

Run `node benchmark.js --render` from collagen-network-atlas on macOS, or omit --render for the numerical/analysis pipeline. It creates a timestamped unique folder, snapshots source, retains success/failure logs, verifies media inputs, and writes a checksum manifest. Existing run IDs are rejected, even after failure. The live molecular launcher likewise creates a distinct run folder. See RUN_STORAGE.md in the atlas.

Completed local runs require a deliberate GitHub upload. This change does not install a background uploader or start a paid GPU job.
