# Corrected WordPress archives and media provenance

These are the exact corrected publication packages for **Fracture Atlas**, model SHA-256 `f0a5034f44aa7065c779f6e20209cd95ee13c7a3ffe6f3e40ae08172a7a489c1`. They supplement the frozen scientific run and the non-overwriting runner; they do not replace either.

| Package | Bytes | SHA-256 |
|---|---:|---|
| [Complete archive, including rendered media](../../../archives/2026-10-31/fracture-atlas-complete-final-f0a5034f44aa.zip) | 12,487,518 | `9127370ca5ca9b1e07a6518809886815234a7e890e3b8098a7caf0f2e820966e` |
| [Source/data archive embedded in the WordPress supplement](../../../archives/2026-10-31/fracture-atlas-data-source-final-f0a5034f44aa.zip) | 5,861,750 | `94ca5e64137eae88856ede6fdc2917c4df2214784fd1ae71e14f0daad801e6eb` |

The original working directory retained an intermediate media input with earlier total support-reaction records. The final numerical results and replays were already correct. The corrected archives now explicitly include `data/media-input.json`, `data/media-provenance.json`, and `MEDIA-PROVENANCE.md`. Both packages were checked: all 51 complete-package member hashes and all 40 source/data member hashes passed, and the media input exactly equals the final results and replay objects.

Regeneration from the final inputs produced byte-identical figures to the original full archive. Fresh public downloads showed all five WordPress GIFs were byte-identical to those final renders. All six hosted PNGs had identical decoded pixels despite different encoding. Every frame was compared; the GIFs each contain 65 frames at 1100 × 720 pixels. The visuals display coordinates, fiber forces, damage and work that were unchanged by the support-reaction correction. Existing media URLs were retained. See the [detailed provenance note](MEDIA-PROVENANCE.md).

## Evidence files

- [Media provenance and public-file hashes](media-provenance.json)
- [All-frame pixel comparison](pixel-audit.json) and its [original native comparison source](compare-final-media.swift)
- [Archive validation](archive-validation.json) and [archive sizes/hashes](archive-metadata.json)
- [Recovery verification from public WordPress HTML](public-archive-verification.json)
- [WordPress post states at correction time](wordpress-posts.json)
- [Checksums of this publication addition](MANIFEST.json)

## Related material

- [Published findings](https://humanavianaisymbiosis.wordpress.com/2026/10/31/fracture-atlas-collagen-network-toughness-pressure-acceleration/)
- [WordPress reproducibility supplement](https://humanavianaisymbiosis.wordpress.com/2026/10/31/fracture-atlas-full-data-source-methods/)
- [Frozen 450-run baseline](../../runs/20261031-finished-f0a5034f44aa/)
- [Safe future-run storage](../../RUN_STORAGE.md)

The WordPress supplement links to a Git commit containing this directory, so its snapshot reference does not move with `main`. Historical packages remain available. These packages preserve hypothetical model results and do not establish experimentally validated tissue toughness, extreme-pressure safety, or molecular calibration.
