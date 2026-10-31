# Large scientific datasets

Files above 95 MiB are automatically published as GitHub Release assets after a completed run passes its manifest and scientific validation. Smaller files and a complete inventory remain in Git. No raw file is silently excluded due to size.

- [All data releases](https://github.com/InquilineKea/scienceclaw-hackathon-2026/releases)
- [Frozen 2026-10-31 preservation bundle and member checksums](datasets/20261031-frozen-collagen-raw-bundle/)
- [Bundle download links and recovery instructions](datasets/20261031-frozen-collagen-raw-bundle/_release/README.md)
- [Atlas run folders](collagen-network-atlas/runs/)
- [Molecular run folders](collagen-molecular-pilot/runs/)

## Preservation and recovery

Each original file has a SHA-256 and byte count in its original MANIFEST.json. Large files are divided losslessly into parts of at most 1 GiB; every part has its own SHA-256. The first part starts at byte zero and parts are concatenated in the explicit order in `_release/LARGE_DATASETS.json`. Files up to 1 GiB require only one part. A release holds up to 900 data parts, with additional releases allocated automatically for larger datasets. This stays below GitHub's documented limits of 2 GiB per asset and 1000 assets per release.

The original MANIFEST.json, LARGE_DATASETS.json and recovery script are also attached to every release shard. Download the index and script, then use Python's standard library:

```sh
python3 -I restore-large-data.py LARGE_DATASETS.json /absolute/path/to/new-recovery-directory
```

The script reconstructs each file at its original relative path, verifies each downloaded part and the whole file, and refuses to overwrite differing files. A matching existing file is a verified no-op. Small files can be obtained from the commit-linked run folder; the original manifest covers both routes. The GitHub repository ZIP is **not** a complete substitute for release assets.

## Automatic completion and retries

The atlas and molecular completion hooks call the uploader. Uploads use the existing host GitHub CLI session; no credentials enter scientific workers. New releases are drafts until all parts and supporting metadata are verified. The Git run folder is then committed without force-pushing; releases are published and a success receipt is written outside the frozen run. A failure at any stage leaves local data intact and publication pending. Retrying reuses matching existing assets, including an upload that succeeded before its response was interrupted. Incomplete starter assets are retained; retry names are unique. Existing different assets or run IDs are refused, never deleted or replaced. The regular upload check retries publication without recomputing science.

The workflow never deletes or replaces release assets, tags, frozen files or manifests. This is append-only application behavior, not protection against a repository administrator deliberately editing or deleting data. Local originals remain as an independent copy. GitHub outages, account limits or failed authentication leave explicit pending records rather than a success claim or omitted data.

The preservation bundle combines already frozen records and repeat validation runs. It is not a new simulation or additional independent scientific evidence. See each original dataset's scientific caveats. No GPU or new paid storage service is provisioned by the upload process.

Sources: [GitHub release storage limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases), [release-asset API and digests](https://docs.github.com/en/rest/releases/assets).
