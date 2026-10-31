# Frozen completed atlas — 31 October 2026

This folder preserves the final 450-run dataset with its generating model and source. The numerical model fingerprint matches results.json. Do not execute the historical writer scripts in this folder. Use the live atlas root's `node benchmark.js --render` command to create a new run.

## Media correction

The first published archive used final numerical results with an older rendering-input bundle. Pulse/free rows and frames differed. We preserved the original archive under `archives/2026-10-31/` and retained that earlier bundle as `data/historical-media-input.json`. The current media input, SVG, PNGs and five GIFs were rebuilt from the final results/replays. Each GIF has 65 frames at 1100 × 720 pixels. The original renderer and preparation code were used; no image was generated from an artistic prompt.

`MANIFEST.original.json` describes the archive as received and is historical evidence. `MANIFEST.json` describes this corrected, frozen folder. See FREEZE.json and the media-rebuild logs for provenance.

All data are outputs of a hypothetical 2D network model, not measured collagen behavior. Only seed-17 representative replay states were retained in the original run. Unsaved internal steps cannot be reconstructed by archiving. See METHODS.md and EVIDENCE.md.
