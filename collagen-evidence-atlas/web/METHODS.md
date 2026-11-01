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


## Selection-responsive animations

Force/damage and uniform-drag microrheology can now calculate selected conditions in a browser worker. These are new single-realization synthetic calculations, separate from the unchanged saved ensemble plots. [Animation methods and coverage](METHODS.md#selection-responsive-force-damage-and-microrheology-animation) describe controls, cancellation, qualification and the remaining exact-match-only fluid fields.


# Selection-responsive force/damage and microrheology animation

This extension replaces fixed demonstration playback with new browser-local single-realization calculations using the existing original project laws. It does not change the saved ensemble tables, measured3D field data, fitted parameters or scientific evidence level. Local worker computation needs no account, cloud instance or paid API.

## Force and damage

Open the force replay inside the crosslink laboratory. Choose whether to animate its left or right selected network. It follows that network family, connector count, loading angle and seed. All seven families, counts0–24 (steps2), twelve directions0–165° and three study seeds are supported. If the curve shows all seeds, choose a representative seed; a trajectory is never an ensemble average.

The worker copies unmodified original model.js, directional.js and aging.js. It builds each placement independently on the same seeded collagen skeleton, with connector stiffness0.2 and rupture strain0.3, then calls the original simulate routine with960 steps. The original secant probe, perimeter affine directional strain, interior relaxation, irreversible damage avalanches, stopping criterion and failure flags are unchanged. Orange direction arrows locate the imposed loading orientation. The left/right animation panels always compare distributed and clustered placement for the chosen single architecture.

Playback selects the last computed frame at or below requested strain. Once one placement stops, its last available state is held and labeled. No interpolation, extrapolation or healing is introduced. Force magnitudes and geometry bounds share a fixed scale across both placements and the entire trajectory. Changing conditions can change that scale; numerical values retain their original units. This one-seed960-step calculation does not establish step convergence for a new comparison or replace saved metric-specific qualification flags.

## Uniform-drag microrheology

The animation follows the microrheology laboratory's family (disordered/modular), size (100/196nodes), frequency and single seed. When the curves show all five seeds, the animation seed selector chooses one realization. Its connector-density and drive-angle controls are explicit: connector count is round(density×nodeCount), with target density0–24/36; the actual count/density is displayed. The saved ensemble curves above remain at their original24/36 target density, with their original x/y drive aggregation. A changed animation density or oblique angle is a new single-specimen calculation, not a new ensemble curve.

The builder, gradient finite-difference tangent, complex-symmetric preconditioned iterative solve and response metrics reuse the pure numerical functions from the original microrheology/run.js. Node filesystem/batch entry points are removed. The full perimeter is clamped; the same four-node probe and three-fiber lesion are used. Added connectors stay intact during the prescribed lesion. At drive angleθ, each probe node receives(0.25cosθ,0.25sinθ), and the displacement readout uses the same energy-conjugate direction. “Follow x/y” uses0° for x and90° for y; if the curves display the x/y mean, it animates the explicitly labeled x realization, never a mean vector field.

We solve (K/k_ref+iΩI)u=b about the unprestressed reference, separately intact and damaged. Tangents are computed at h=1e−6 and h/2; the matrix is symmetrized after recording asymmetry. Each field requires finite phasors, positive local compliance, true relative residual<1e−7, tangent-step relative change<1e−5 and relative asymmetry<1e−5. Any failed intact/damaged pair is not drawn. In particular, the saved singular damaged196-node modular/distributed seed43 static case remains unavailable, not zero compliance. Ω=0 is rendered as a static response; phase/play are disabled.

Playback traverses phase at a fixed display speed, not a clock calibrated to physical time. ChangingΩ changes the solved amplitude and phase lag. For positiveΩ, displayed displacement is Re(u)cosφ−Im(u)sinφ. Total and damaged-minus-intact modes each derive one common scale from both placements; the scale is fixed during phase playback and shown numerically. Density/frequency/angle changes may rescale the view, so compare physical model amplitudes in the numerical readouts, not arrow length across different selections. Optional magnification applies equally to both placements. No new rupture develops during the harmonic cycle. Ω is normalized, not Hz; this is not calibrated tissue G′/G″ or damage propagation in time.

## Fluid-coupled coverage

No new FEniCSx pressure solver has been ported into the browser. The legacy saved fluid example is available only for196nodes,seed17, target density24/36,0° drive,Ω=0.1,κ=0.001, in each of the two available architectures. Changing any of those conditions clears the field and explicitly reports that no matching pressure solve exists. It never rotates, rescales or relabels old fluid fields as a new solution. Its original model assumptions and observable-specific pressure-mesh limitations remain as described in the integration methods. Uniform drag is the available on-demand response model.

## Cancellation, provenance and checks

Calculation runs in a dedicated worker, bounded to60 seconds and an eight-entry in-memory result cache. Controls debounce180ms. A new selection terminates the previous worker, clears old fields, disables playback while pending, and rejects stale completion messages. Closing the details cancels a running calculation. Pause, cancellation and retry are available; playback pauses when hidden or scrolled away. Completed results export as JSON with full selection parameters, geometry, fields/frames and numerical checks. This is local scientific data, not telemetry.

The isolated original Node/stdlib harness verifies force metrics against saved density rows, validates microrheology amplitudes and qualification against saved responses, preserves the singular static exclusion and irreversible damage, and independently checks that45° complex fields equal the normalized sum of0° and90° solutions. Native browser QA tests selection changes, phase play/pause, stale-result cancellation and exact saved-fluid coverage. See the responsive-animation source provenance and validation records. None of these checks is new biological/material validation.
