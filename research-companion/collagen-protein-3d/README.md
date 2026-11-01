# 3D collagen–decorin–fibronectin research companion

Original dependency-free static companion for the completed central-force scaffold study. Destination: `docs/research-companion/collagen-protein-3d/` in `InquilineKea/scienceclaw-hackathon-2026`. This is separate from the later continuous-fiber refinement pilot, whose no-go is included prominently.

## Four comparisons

1. Organization-only: adapter-free endpoint means and individual graph seeds.
2. Interaction law: binding versus breakable locking on identical scaffold/adapter geometry, matched initial arm curvature and energy.
3. Adapter architecture: two-arm decorin-like versus four-arm fibronectin-like, both binding; matched total arms/mass but different valency/site geometry.
4. Organization × law: paired absolute difference-in-differences requiring all four cases per seed. This distinguishes a relative effect's denominator from a change in the absolute law effect.

Stress contrasts use the 20% strain endpoint; timed recovery uses T=20 reduced units after 15% preload. Rejected cases never enter the means, even when their tensile phase completed. Dots show synthetic seed variation, not biological uncertainty. The individual response plot displays every saved accepted loading sample, including repeated-strain events; the connecting segments are visual guides.

## Geometry and provenance

All64 original initial graphs are included, with exact coordinates, collagen edges, adapter groups, geometry hashes and measured generator descriptors. The view rotates a projection of those3D coordinates; it does not show molecular structures or deformed states. Organization changes regenerate graph edges; paired seeds are generator interventions. Law comparisons reuse identical scaffold and adapter hashes. Adapter architecture comparisons reuse the scaffold but intentionally change sites/valency.

`site/data/manifest.json` records source digests, complete design, coverage, limits and SHA-256/byte lengths for28 artifacts. All1,088 summaries and1,082 accepted tensile curves are included. Source text is downloadable for inspection and is never imported/executed by the browser or exporter. Six production failures and earlier commissioning outcomes are visible and downloadable. Full raw checkpoints/tracebacks remain in the separately verified861MB local archive; sensitive orchestration/account records are not published.

## Rebuild and verify

Both tools use Python standard library only and read data without importing simulation source:

```sh
python3 tools/export.py --study /path/to/collagen-protein-3d --raw /path/to/3d-results
python3 tools/verify.py --study /path/to/collagen-protein-3d --raw /path/to/3d-results
```

They default to this chat's local output layout; explicit paths make the adapter portable. Local layout uses `site/`; repository layout uses `../../docs/research-companion/collagen-protein-3d` relative to this README's directory. Serve that site folder over HTTP(S). No packages, analytics, external scripts, API keys or cloud jobs are required.

## Scientific boundary

This is an uncalibrated central-force strut sensitivity study. It cannot rank biological proteins, infer native covalent decorin, model assembly chemistry, establish ultimate strength or identify permanent deformation from short-time recoil. The later beam model passed elementary bending/buckling tests but failed network refinement; its160-case production was not launched. That failure does not validate or erase the earlier study's numerical results; it bounds what can be claimed about a more physically detailed replacement.
