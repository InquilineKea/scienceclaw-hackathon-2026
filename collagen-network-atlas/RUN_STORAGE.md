# Run storage policy

A run is a new directory, never a filename reused for a different calculation. The default identifier combines a UTC timestamp with random suffix. Directory creation is exclusive; concurrent jobs and explicit-name collisions cannot replace prior files. Completed, prepared and failed runs are all retained. Retrying means starting a new run.

Each run contains a source snapshot, RUN_CONTEXT.json with source fingerprints, data/, figures/, logs/, and FINISHED.json or FAILED.json. MANIFEST.json records exact file sizes and SHA-256 hashes. A prepared-only run contains PREPARED.json. Source and completed output are saved together. This is append-only workflow protection, not a filesystem mechanism that can prevent a person from deliberately editing/deleting files.

The live source is separate from frozen runs. `node benchmark.js [--render]` is the supported entry point. The numeric/media helpers reject execution outside a fresh run. The molecular pilot's live shell launcher also uses an exclusively allocated unique folder; archived launch scripts remain historical evidence. Existing cloud-execution approval and security gates remain in place.

A completed local run is not automatically uploaded. Commit and push its new directory, or attach an archive in a deliberate GitHub upload. No background cloud job, recurring automation or credential-bearing auto-push process was installed.

## Retained information

All 450 per-run records and all sampled curves are saved. Representative replay states cover 56 topology/loading cases at seed 17. Outputs retain the original seven-significant-figure JSON export convention; curve CSVs are written from the sampled numeric records. No claim is made that every internal solver step or every per-edge state was recorded. Previous files cannot supply states that were never saved.

## Validation

Original standard-library storage tests cover exclusive collision handling, concurrent allocation, source snapshots, exclusion of credentials/prior data, traversal/symlink rejection and failed-log preservation. A complete 450-case run with rendering is recorded separately as 20261031-storage-verification. The mathematical model is unchanged by the storage update.
