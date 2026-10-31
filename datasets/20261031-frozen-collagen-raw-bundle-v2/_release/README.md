# Release-backed raw data

All original files are covered by the adjacent MANIFEST.json. Small files are in Git; the large files below are stored losslessly in GitHub Releases. The GitHub source-code ZIP alone does not include release assets.

* `collagen-frozen-data-20261031.tar`: 120412160 bytes; SHA-256 `c224b81867f51a1014c0d526ce6833e798afb3a42ec122c9e85914cf50f46298`.
  * [Download part 1](https://github.com/InquilineKea/scienceclaw-hackathon-2026/releases/download/data-archive-20261031-frozen-collagen-raw-bundle-v2-f95f1bfa45dd29bf961f-s0001/ea36a186a387d8ec-part-000001-c224b81867f51a1014c0d526ce6833e798afb3a42ec122c9e85914cf50f46298.bin)

Download this directory’s `LARGE_DATASETS.json` and `restore-large-data.py`, then run:

```sh
python3 -I restore-large-data.py LARGE_DATASETS.json /path/to/recovery
```

Restoration verifies every part and whole-file checksum, and refuses to replace differing existing files. The uploader never deletes or replaces assets or tags; administrators can still alter repository content. Keep the local copy and manifest as an independent copy.
