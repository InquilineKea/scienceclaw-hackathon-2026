# Collagen Evidence Atlas: methods and provenance

This is an interactive visualization of immutable saved results, not a new simulation, calibration or independent validation. The visualization was co-designed and reviewed with Gemini4Argon on the existing GCP lab VM; original dependency-free HTML/CSS/JavaScript implements it. No model runs when a visitor opens the page. No analytics, external fonts, CDN libraries, credentials or runtime API calls are used.

Scientific source snapshot: https://github.com/InquilineKea/scienceclaw-hackathon-2026/tree/11b57e1daf9724ac6d169c3fa1289f5e09ce18ab/collagen-nonlinear-heldout

## What is drawn

The scene contains4355 frozen score-eligible PIV sample locations and753 reference-cell segmentation samples. These are sampling locations and displacement vectors, not collagen fibers, junctions or forces. No lines connect neighboring sample nodes. The outline indicates the approximate353.82×353.82×356.63µm sampling box; X/Y/Z axes indicate physical coordinate directions. The cell cloud is a reference fluorescence mask, not a mechanical inclusion mesh or observed fiber shell.

Observed and predicted vector colors use a fixed0–8µm displacement-magnitude scale. Residual vectors are prediction minus observation, with fixed0–4µm magnitude coloring. The paired error lens renders scalar points, not residual vectors: Δerror = |u_model−u_observed| − |u_reference−u_observed|, inµm. Teal means lower error; copper means higher error, with a default−1 to+1µm scale and saturation outside that range. Users may explicitly choose±0.1,±0.5,±1 or±2µm; the selected scale stays fixed across filters and model changes. Paired pointwise norm differences do not equal differences in the global squared-error score. Color scales never automatically rescale when slicing or changing regions.

Arrow magnification changes displayed lengths only; it does not change data, applied loads or scores. Camera presets/orbit/pan/zoom change the view, not loading direction, experimental time or material state. The default60µmZslab reduces occlusion. Density selects every nth currently filtered point for drawing, while all filtered points remain in regional statistics and CSV export. Point picking chooses the nearest projected displayed eligible sample; the source-node ID and numerical inspector disambiguate dense views. Point inspection is also available by source-node ID and keyboard brackets.

## Scores and filtering

The frozen global primary vector RMSE is sqrt[(1/8) sum_o mean_{i in octant o} |u_pred_i−u_obs_i|²]. The interactive regional RMSE is sqrt[mean_{i in selected region} |u_pred_i−u_obs_i|²]. They use different weighting and need not agree even with all regions selected. Global scores and parameter selection remain unchanged by filters. Histograms count all filtered vectors; the final bin includes all residual magnitudes≥3.75µm. Empty selections return no score, not zero.

Octants match the original sign convention (positive coordinate>0). Slabs use |coordinate−center|≤thickness/2. Coordinates/vectors in the display export are rounded to0.00001µm; published global metrics retain their original precision. This rounding does not alter model selection or frozen outcomes.

The optional raw P1 mismatch coloring is a derived visualization descriptor: for each node, sqrt of the volume-weighted incident-eligible-tetrahedron mean squared Frobenius strain mismatch. It is dimensionless, uses a fixed0–0.15 scale, and is gray where no eligible incident tetrahedra contribute. It is not the normalized global strain score and not an independent strain assay. Raw P1 derivatives are finer than the35µmPIV window;303 complete guarded5³ local fits support the separately reported averaged-strain score.

## Scientific scope

Pos007 selected among12 prescribed parameter combinations. Pos008 was already examined and is an adaptively reused, boundary-conditioned benchmark. The4355 vectors, eight octants and strain stencils are correlated within one position. No independent-sample significance claim follows. The source model supplies measured outer-face and near-cell displacement; uniform absolute stiffness is unidentifiable. Compression softening is phenomenological; sliding is irreversible plastic lengthening, not directly observed crosslink motion. The assumed virgin proportional history from a drug-relaxed reference is unmeasured.

Only the primary combined candidate received the full20-step/302-direction refinements and bounded32-step final-state Hessian screens. No detected negative curvature is not proof of global stability or mesh convergence. Numerical work/dissipation are normalized surrogate quantities, not fracture toughness or a measured energy-absorption limit. The research map links separate studies with their own evidence levels and units; this benchmark does not validate their aging, species, fracture or chemistry claims.

## Design audit

Argon proposed synchronized3D views, residual lenses, tomographic slicing, a dual ledger for frozen/global versus conditional/local scores, pairwise model comparison, point inspection, an evidence map and restrained archival styling. We adopted those features. We did not implement suggestions requiring unavailable data (all-node eligibility/stencil membership/radial distance from the cell surface), infer fiber architecture, or adopt unverified claims that a custom palette is perceptually uniform or achieves a particular contrast ratio. The design model's output is advice, not scientific evidence.

See the GitHub source folder for the design brief, final design, review receipts, implementation decisions, data hashes and browser checks. Only final non-thought model text and usage metadata are retained. Existing VM costs are separate from estimated API token cost; estimates are not billing receipts.


## Integrated comparisons, November 1

The atlas now includes crosslink density/aging hypotheses, saved damage replays, and paired uniform-drag/fluid-coupled microrheology. See [integration methods](INTEGRATION-METHODS.md) and [comparison provenance](COMPARISON-PROVENANCE.json). These saved synthetic studies remain distinct from the measured-field benchmark above.
