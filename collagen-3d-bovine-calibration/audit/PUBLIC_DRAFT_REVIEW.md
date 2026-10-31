# Public explorer draft review

2026-10-31. Static review of index.html, page.js and build-artifact.py before final results were inserted. No publication or browser mutation performed by this reviewer.

## Fix before publication

**High — show pre-avalanche peaks in the plotted stress path.** The draft stress chart and static SVG use only `frame.stress` (post-avalanche), while numerical peak qualification uses `max(preStress,stress)` and the work integral uses the loading branch ending at `preStress`. Hiding the pre-avalanche value can erase the actual sampled rupture peak and vertical stress drop. Draw the prior post-event state to the next pre-event stress, then both pre/post values at the same imposed shear. Damage remains a post-event curve. Use the same representation in both the interactive and WordPress static figures. This is a representation correction; it does not alter source results.

**Medium — display actual resolution and the limits of the angle sampling.** The explorer should state the complete-factorial 25/50 loading increments and the separate three preserved 100/200 controls. A two-resolution loading-step test is not spatial mesh/RVE convergence. The xy and xz tests are two shear directions, not a complete 3D anisotropy surface or proof of isotropy. Three requested curvature checkpoints can coincide (e.g. a cap maximum and terminal state); report checkpoint coverage without implying three independent distinct states or whole-path stability.

**Medium — keep quantitative outcomes accessible, not just a generic paired-summary sentence.** `summary` already carries placement and baseline aggregates, but the draft `comparison_text` contains only general advice. Before publication, show the actual qualified pair/seed counts and effects for maximum sampled stress, cap-work density and any resolved-peak endpoints, including explicit unavailable cells when no endpoint passes. Distinguish strict-positive-curvature and conditional-marginal tiers. Do not use a generic 'qualified trajectory' label for a conditional one without explaining the tier.

**Medium — periodic locked-node markers should share the edge wrapping convention.** Edges are clipped to a convected periodic cell, while purple locked-site dots are drawn at raw displaced node coordinates. Nodes crossing a periodic face can therefore appear outside or detached from the displayed edge network. Wrap the displaced node in reference-cell coordinates before projecting its marker. The underlying crosslink calculation is unaffected.

**Medium — replace the generic source link with the verified scientific snapshot.** The current builder points to the repository homepage. Insert the bounded source/results commit URL after verified publication and ensure the linked downloadable archive is actually the final checked artifact. Do not publish placeholder result data or combine the earlier failed attempts with the final factorial counts.

## Robustness improvements

- Filter nonfinite stiffness points before computing `Math.max` for the y-axis; otherwise any unaccepted/missing point inserts NaN and breaks the scale.
- In the static plot, determine the stiffness y-limit from accepted values rather than fixing it permanently to 3. Current data fit (maximum individual ratio about 2.783), so no present clipping was found.
- Prefer 'simulated shear stress/response' to 'observed shear stress/response' on the mechanics panels. The actual measured observations are the separate bovine rheology data.
- Guard Play until visualization data are loaded. The draft callback can access DATA.geometry before DATA exists.
- Display data-load errors in the default visible panel, not only in the initially hidden damage tab.
- Use stage-specific qualification text for a spatial frame; a valid frame from a later-unresolved trajectory can be displayed descriptively but does not establish a qualified complete path.

## Claims that are appropriately bounded

The opening notice clearly distinguishes a bovine bulk-response scale from synthetic topology, angular locking and assumed rupture thresholds. The text does not claim molecular viscosity, AGE concentration, age in years, native tissue validation, measured architecture, calibrated Gc, phase change or complete separation. Per-seed amplitude matching is described as a scalar calibration with a fixed factor across interventions; it is not presented as architecture identification. The phenomenological parallel dashpot is explicitly absent from quasistatic damage curves. The cross-validation wording acknowledges selection on the same folds. The PDB1CAG caveat correctly separates molecular crystal structure from hydrogel network architecture.

Static review found the periodic edge transformation consistent with affine simple shear and stored nonaffine displacements. The spatial colors are an axial extension/force surrogate, not the full vector force field including angular forces. The page's explanatory text mostly makes this distinction; retain it in figure captions and WordPress prose.
