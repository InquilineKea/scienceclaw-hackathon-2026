# Final-model media provenance correction — 31 October 2026

The model SHA-256 is `f0a5034f44aa7065c779f6e20209cd95ee13c7a3ffe6f3e40ae08172a7a489c1`.

The original working directory retained an intermediate `data/media-input.json` with model hash `2caf29c69aa5e7bcc1e1f70d221d0a08df77c6c20ab4a057dd30f564124a6dbc`. Its total support-reaction fields were stale. The published numerical results and replay file already used the final model; those files are byte-identical in this correction. The earlier ZIP excluded the intermediate media input.

This package now includes the corrected `data/media-input.json`, whose `results` and `replays` objects exactly match the final numerical files, plus `data/media-provenance.json`. The latter records the final model hash, source and public-file digests, and all-frame native pixel comparisons.

Regenerating from final data produced byte-identical figures to those in the original full ZIP. All five publicly hosted GIFs are byte-identical to the regenerated GIFs. The six hosted PNGs are encoded differently by WordPress, but every decoded pixel is identical. Each GIF has 65 frames at 1100 × 720 pixels. The figures show coordinates, fiber forces, work and damage, not the stale total support reactions, so no visible figure replacement was needed. Numerical conclusions are unchanged.

Historical original ZIPs and the stale intermediate input remain outside this corrected package. This correction is versioned separately and does not modify benchmark entry points or the separately managed GitHub runner.
