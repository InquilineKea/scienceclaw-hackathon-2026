# Crosslink density, placement and damage onset

The saved sweep varies added connector count at fixed collagen geometry and material. It uses the unchanged `model.js`, `directional.js` and `aging.js`; `density.js` only summarizes existing curves. See [crosslink methods](AGING_METHODS.md) for the constitutive law and boundary conditions.

## Design

Seven network families, three seeds (17, 29, 43), 12 angles (0–165° every 15°), and counts 0, 2, …, 24. Nonzero counts have distributed and centrally clustered placement. Zero-added configurations are shared controls rather than duplicated: 7 × 3 × 12 × (1 + 12 × 2) = 6,300 configurations. Each is solved at both 480 and 960 load steps, giving 12,600 solves. All connectors use stiffness multiplier 0.20 and rupture extension 0.30. Each placement uses nested candidate prefixes, preserving previously selected sites as count increases.

Density is connector count divided by the 36 nodes. Eligible-site occupancy is also exported. Neither is a measured molecular crosslink density, tissue AGE concentration or chronological age. The reference contains the same original junctions and collagen skeleton, with zero *added* connector springs. Collagen volume stays fixed; connector elastic energy is additional. Placement also changes lengths and orientations, so its effect is not clustering alone.

Loading prescribes u = ε n[n·(X−center)] on the same 20 perimeter nodes. Both coordinates are prescribed, with zero transverse perimeter strain. The remaining 16 nodes relax. Stiffness is the initial secant at ε=0.002. Failure criterion is 20% collagen-volume rupture or reaction below 50% of its running peak after ε>0.08, as specified in the crosslink methods. The strain cap is ε=0.85.

## Work before structural change

“First bond damage” is the first sample with any collagen or connector rupture. “First collagen damage” ignores earlier connector rupture. Before-event work and stored elastic energy are taken at the last intact sample; the JSON also records the onset bracket (last intact strain, first damaged strain). If no event occurs, before-event work is null. This is a sampled estimate, not a mathematically certified bound. Work integrates conjugate reaction against strain and includes recoverable elastic energy; it is not dissipation alone.

Damage onset, peak reaction and failure are mechanical events. No free energy, temperature, equilibrium phase coexistence or thermodynamic phase transition is modeled. Work to a chosen criterion is a dimensionless toughness proxy, not crack fracture energy or measured tissue toughness. Reduced failure strain and reduced work are reported separately from higher stiffness; no universal brittleness threshold is imposed.

## Numerical checks and display

The page displays the 960-step result. For each metric, relative step change is |fine−coarse| / max(|fine|, |coarse|, 10⁻¹²). A ≥5% difference or invalid solve flags the metric. Stiffness additionally requires a valid undamaged stiffness probe. Failure work and strain additionally require uncapped traces and agreement of the stopping criterion. Before-damage metrics can remain usable when a later trace is capped, provided the event occurred and the step check passed. This two-resolution check is not proof of asymptotic convergence.

Solid points require all selected seeds to pass the metric-specific check. Hollow points show unresolved finite estimates and have no connecting segment. Missing values are omitted. Whiskers show minimum and maximum across three seeds, not confidence intervals. Relative plots calculate each seed's paired ratio before averaging; both numerator and zero-added denominator must be resolved. Ratios greater than one can be interpreted only for the selected metric and loading direction. Every network has its own vertical scale; the horizontal density scale is shared.

## Reproducibility

The full records, both-resolution raw curves, runtime receipt, source snapshots and SHA-256 manifest are retained in the repository's [density run directory](https://github.com/InquilineKea/scienceclaw-hackathon-2026/tree/main/collagen-network-atlas/density-runs/20261031-density-v1). Large raw files may use the repository's documented lossless GitHub Releases route. The page exposes [CSV](data/density.csv) and [JSON](data/density.json). `benchmark-density.js` reproduces the sweep in a new output directory; no package installation is required. `check-density.js` tests event bracketing and metric quality flags. See `density-cloud/SECURITY_REVIEW.md` for the bounded remote runtime review.

No parameter here has yet been fitted to beaver collagen, human collagen, a specific AGE molecule or molecular dynamics. The separate CDSM pilot prepares matched species backbones; geometry generation alone does not provide mechanical parameters.
