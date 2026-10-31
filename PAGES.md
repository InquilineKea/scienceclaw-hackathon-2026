# Public Fracture Atlas

The interactive application is served at https://inquilinekea.github.io/scienceclaw-hackathon-2026/ from `main:/docs`. GitHub Pages serves the original static HTML, CSS, JavaScript, and frozen data directly; `.nojekyll` disables Jekyll processing. No external package, custom Action, login, backend, or remote computation is required.

Visitors can choose seven architectures and eight loading protocols, scrub or play recorded deformation, inspect force/damage and predictor plots, change hypothetical assumptions and calculate a new pair in browser workers, export that pair, and copy a link to a benchmark comparison. Custom values are not stored on a server. A shared benchmark link preserves protocol and architecture choices; export JSON to preserve a custom calculation.

## Loading is explicit

Green arrows indicate prescribed coordinate motion or the X-directed body-force protocol; cyan marks identify held coordinates. The markers are schematic direction cues, not force magnitudes. Fiber colors and widths retain their original internal-force meaning.

- X tension: left-edge x = 0; right-edge x = 1 + strain; y is free except for the bottom-left pin. This is uniform prescribed edge displacement, not equal nodal force or isotropic stress.
- Y tension: bottom-edge y = 0; top-edge y = 1 + strain; x is free except for the bottom-left pin.
- Shear: bottom fixed in both coordinates; top translated in +X at fixed height; side faces otherwise free.
- Unconfined compression: right edge moves left; left-edge x held; lateral y motion free except for one pin.
- Confined compression: the same X shortening, plus fixed top/bottom y coordinates. Lateral reactions may develop.
- Biaxial compression: all four sides approach the center at equal X/Y normal strain. This is kinematic isotropy in 2D; the stress need not be isotropic, and there is no fluid or 3D hydrostatic-pressure law.
- Clamped pulse: every node receives body force per mass along +X; the entire left edge is fixed in both coordinates. The default acceleration is 0.018 sin(πt/8) for 0 ≤ t ≤ 8, followed by zero, with observation to t = 16.
- Free pulse: the same uniform X-directed acceleration, with no supports. Rigid translation is the control.

The interface also reports the initial volume-weighted fabric tensor anisotropy A₀ = sqrt((Qxx − Qyy)² + 4Qxy²), with trace(Q) = 1 and Q = Σ(A L n⊗n)/Σ(A L). A₀ = 0 is an isotropic second moment; A₀ = 1 is parallel fibers. X alignment is Qxx. These quantities do not measure load anisotropy or mechanical isotropy and do not capture bottlenecks or other higher-order topology.

## Update and verify

Edit the live source in `collagen-network-atlas/`, then run the original bounded publisher `python3 -I publish-pages.py`. It copies only the explicit public asset list into `docs/` and writes `DEPLOYMENT.json` with model and asset hashes. Check loading markers with `node collagen-network-atlas/check-load-guide.js` and verify browser interactions before pushing. This does not run the scientific benchmark or modify frozen runs or ZIPs. The archived numerical model remains `f0a5034f44aa7065c779f6e20209cd95ee13c7a3ffe6f3e40ae08172a7a489c1`.

The 450-run baseline is a hypothetical, dimensionless 2D model, not experimentally calibrated tissue toughness. Numerical and pressure-model limitations remain visible in the explorer and methods. Historical publication packages remain pinned to their original snapshot.


## Directional mechanical anisotropy extension

The [load-angle view](https://inquilinekea.github.io/scienceclaw-hackathon-2026/?angle=0&network=aligned&directionSeed=mean#direction) adds an independent prescribed-perimeter tension experiment. A 0–180° slider solves a selected network at any integer angle in a browser worker. The seven stiffness and work-to-criterion curves cover twelve directions and three seeds (252 new runs); 180° repeats 0°. Mean curves and individual seeds, numerical checks, censoring markers, exact-angle JSON exports, and a CSV are available. See `collagen-network-atlas/DIRECTIONAL_METHODS.md` for the explicit boundary condition, metric definitions and limits. The 450 original runs and their model remain frozen.

The new files are original dependency-free code. `node collagen-network-atlas/check-directional.js` checks boundary derivatives, virtual work, rotational covariance, periodicity, analytical single-fiber stiffness and censoring. `node collagen-network-atlas/benchmark-directional.js /new/output/directory` creates a separate directional dataset and refuses to overwrite an existing directory. The published data are frozen under `collagen-network-atlas/directional-runs/20261031-perimeter-v1/`.


## Age-related crosslink hypothesis tab

`aging.html` is a separate public page linked from the original atlas navigation with a new-tab link. It compares the identical collagen skeleton with and without effective connector springs. Users can change connector number, placement, stiffness, rupture extension and loading angle; compare deformation, reaction, collagen/connector damage and directional stiffness/work; and export or share the complete controls. The default dataset contains 504 added-connector runs and 252 newly paired references, with 18 strain-step sensitivity checks. Age, chemical concentration and molecular identity are not calibrated. Methods and sources are in `collagen-network-atlas/AGING_METHODS.md`; the frozen dataset is under `collagen-network-atlas/aging-runs/20261031-connectors-v1/`.

The publisher checks the baseline, directional and aging data against their current model source hashes before copying the explicit static asset list. No package installation or external dependency build is needed.

## Matched FEniCSx fluid coupling

`/poroelasticity/` is a separate buildless public replay with pressure and displacement phase controls, size/mobility tables, figures, GIFs and raw results. The bounded publisher copies the explicit file list from `collagen-fenicsx-poroelastic/web/` and records it in `docs/DEPLOYMENT.json`. Scientific code and the immutable remote runtime/input receipts remain in the repository. Frequency plots show all algebraically resolved fine-mesh values; summary tables/ratio plots use only qualified seed pairs.


## Bovine bulk-calibrated 3D collagen comparator

[Open the interactive 3D explorer](https://inquilinekea.github.io/scienceclaw-hackathon-2026/bovine-3d/) for measured-versus-fit bovine G′/G″, matched-budget junction-locking stiffness, paired force/damage replay, and explicit numerical qualification. [Scientific source and audit](collagen-3d-bovine-calibration/README.md) and [three-campaign evidence gates](collagen-3d-bovine-calibration/campaigns/CAMPAIGN-STATUS.md).

160/160 final cases, 160 complete trajectories, 80/80 load-step pairs, and 40 accepted small-strain states. This uses synthetic periodic networks with a bovine bulk-response scale; measured architecture, chemical aging and species-specific fracture are not validated. Marginal curvature and capped maxima remain explicitly conditional/censored.

[Download the bounded source/results archive](https://inquilinekea.github.io/scienceclaw-hackathon-2026/bovine-3d/bovine-3d-results.zip), 28,095,424 bytes, SHA-256 `55c493bf1d271e47632be6fffb580f48b1920e1b0a726ac506fff58a0931036a`.
