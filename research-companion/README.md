# ScienceClaw research companion: first working vertical slice

This original, buildless companion connects the published WordPress article to precomputed, inspectable evidence. It replays the completed 2D fiber-rigidity sweep; it does not simulate collagen proteins or submit cloud jobs.

## Contents

- `site/`: deployable static site, six mean response curves, 18 seed-specific onset summaries, 186 saved network states, CSV/report downloads and SHA-256 verification.
- `tools/export.py`: original Python-standard-library adapter reading only audited JSON/CSV/report data. It does not import or execute third-party simulation code.
- `tools/verify.py`: exact exported-data correspondence, SHA-256, byte counts and independent periodic-endpoint checks.
- `site/data/manifest.json`: versioned experiment record linking the article, pinned simulation revisions, design, validation, scientific limits, visualization coverage and artifact checksums.
- `EXPERIMENT-CONTRACT.md`: small interface future ScienceClaw experiments can target.

Run the exporter with the existing study output directory, then run the verifier. For example, from this folder:

```sh
python3 tools/export.py ../fiber-rigidity-sweep
python3 tools/verify.py ../fiber-rigidity-sweep
python3 -m http.server 8768 --bind 127.0.0.1 --directory site
```

In the GitHub repository layout, serve `../docs/research-companion/fiber-rigidity` instead of `site`; both tools detect this layout automatically.

Open http://127.0.0.1:8768. HTTP or HTTPS is required for data fetching; localhost or HTTPS is required for browser SHA-256. No package installation, external JavaScript, analytics, cookies or credentials are needed.

## Display coverage

All six mean curves retain all 121 strain samples. The seed table contains onset estimates, not full individual-seed curves. The network view shows seed 0 only and every fourth saved strain, for 31 states per parameter pair. These are independent affine-start minimized states, not a time trajectory. No interpolated physics or new calculations are implied. Edge energies are log-colored relative to each frame, so colors do not compare absolute energy across frames. Boundary edges use saved periodic edge vectors and are clipped to the actual sheared cell.

The 26.4 MB raw archive is retained locally and identified by hash but is not distributed in this compact site. The local public supplement remains a separate possible upload.

## Publication

Destination chosen by the user: `InquilineKea/scienceclaw-hackathon-2026`. Additive proposed site path: `docs/research-companion/fiber-rigidity/`; reusable adapter and contract: `research-companion/`. Existing atlas files and cloud infrastructure need no changes. The existing pinned GitHub Actions publication workflow packages `docs/` without executing the simulation or this adapter.

The older root `publish-pages.py` currently rejects several already-existing folders outside its allowlist, including later additions predating this companion. Do not run it to publish this addition. This companion has its own exporter and exact-byte verifier; the existing Pages workflow packages the added directory directly.

## Current boundary

This establishes one repeatable export-and-view pattern. It is not yet a registered ScienceClaw lifecycle hook, a multi-experiment library, a 3D molecular asset exporter, or a compute-backed service. Those require separate adapters and scientific validation. A Sketchfab model should be added only when an actual provenance-bearing 3D structure or network is selected; a 2D dataset should not be extruded and presented as molecular evidence.
