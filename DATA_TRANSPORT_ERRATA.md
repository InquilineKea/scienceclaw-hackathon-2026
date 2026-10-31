# Preserved transport correction — 2026-10-31

The first automatic large-file trial published 120,412,160 bytes of real frozen scientific data. GitHub verified the asset SHA-256, but the first dataset index captured a temporary `untagged-*` URL while its release was a draft. That URL changes upon publication. The first index, receipt, release assets and source data remain preserved rather than being overwritten.

Use the [corrected v2 dataset index and recovery instructions](datasets/20261031-frozen-collagen-raw-bundle-v2/_release/README.md). The original archive SHA-256 is unchanged: `c224b81867f51a1014c0d526ce6833e798afb3a42ec122c9e85914cf50f46298`. No scientific result changed and no simulation was repeated. The v2 release is a new archival transport revision, not a new experiment.

The uploader now finds drafts through the authenticated release list, constructs permanent tag URLs before committing an index, and checks final public asset URLs and checksums before writing a success receipt. Regression tests cover draft discovery, draft URL changes, interruption/retry, collision protection and exact reconstruction.

A separate download check encountered the existing macOS Python installation's missing default CA bundle. Verification uses the existing system CA file (`SSL_CERT_FILE=/etc/ssl/cert.pem`) without disabling TLS verification or installing a package. On a normally configured Python installation, the documented restore command needs no environment override.
