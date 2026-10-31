# Run storage policy

A run is a new directory, never a filename reused for a different calculation. The default identifier combines a UTC timestamp with random suffix. Directory creation is exclusive; concurrent jobs and explicit-name collisions cannot replace prior files. Completed, prepared and failed runs are all retained. Retrying means starting a new run.

Each run contains a source snapshot, RUN_CONTEXT.json with source fingerprints, data/, figures/, logs/, and FINISHED.json or FAILED.json. MANIFEST.json records exact file sizes and SHA-256 hashes. A prepared-only run contains PREPARED.json. Source and completed output are saved together. This is append-only workflow protection, not a filesystem mechanism that can prevent a person from deliberately editing/deleting files.

The live source is separate from frozen runs. `node benchmark.js [--render]` is the supported entry point. The numeric/media helpers reject execution outside a fresh run. The molecular pilot's live shell launcher also uses an exclusively allocated unique folder; archived launch scripts remain historical evidence. Existing cloud-execution approval and security gates remain in place.

Completed runs automatically upload to InquilineKea/scienceclaw-hackathon-2026 after their manifest is sealed. Authentication stays in the trusted host uploader, outside computation. A matching remote run is an idempotent success; a differing existing run is refused. Connection/authentication/size failures remain pending locally and can be retried without recomputation. Upload receipts live in .upload-receipts/, outside the frozen run. A periodic Codex check retries pending completed runs. No new GPU jobs are started by publication. An explicit --no-upload keeps one run local. Files above 95 MiB are retained locally for a separate large-file publication decision; they are never silently omitted.

## Retained information

All 450 per-run records and all sampled curves are saved. Representative replay states cover 56 topology/loading cases at seed 17. Outputs retain the original seven-significant-figure JSON export convention; curve CSVs are written from the sampled numeric records. No claim is made that every internal solver step or every per-edge state was recorded. Previous files cannot supply states that were never saved.

## Validation

Original standard-library storage tests cover exclusive collision handling, concurrent allocation, source snapshots, exclusion of credentials/prior data, traversal/symlink rejection and failed-log preservation. A complete 450-case run with rendering is recorded separately as 20261031-storage-verification. The mathematical model is unchanged by the storage update.

## Retry an upload

```sh
python3 -I upload-run.py --scan . --kind atlas
```

The remote folder is `collagen-network-atlas/runs/<run-id>/`. An upload adds a commit on main using the current remote tree and verifies every uploaded file by its Git content hash. The publisher never force-pushes or replaces existing run data. Only runs with FINISHED.json, exact MANIFEST.json coverage and validated numerical results are eligible.
