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
