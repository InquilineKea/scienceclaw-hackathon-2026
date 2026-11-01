# Argon design and review: implementation decisions

Gemini4Argon completed one design specification and one static source review on the existing GCP VM. Requested/returned model IDs and token usage are preserved in argon/*. The worker saved final non-thought output and usage only, executed no generated code and made no automatic retries. The original HTML/CSS/JS implementation is authored for this task. No new VM, package installation or visitor-facing LLM API was introduced.

Adopted: archival/metrology surfaces and typography; synchronized3D observed/predicted/residual views; full-width prediction/difference modes; default60µmZslab; fixed-scale signed pairwise error lens; source-point inspector; separate frozen equal-octant and filtered pooled metrics; linked score chart/octant filters/histogram; evidence-tagged research map; numeric CSV export; orthographic presets without continuous autoplay.

Not adopted: new fiber mesh or reference-cell hull; radial-distance-to-surface controls without validated distance data; all-node/stencil selectors unsupported by the bounded export; unverified claims of palette perceptual uniformity, precise contrast certification, sub50ms performance or universal model stability. Model critique is advice, not a measured validation result.

Findings and resolutions:

- Medium, selection contrast/fallback highlight: changed selected marker to dark copper-red,9px and added it to Canvas fallback.
- Medium, mobile breakpoint mismatch: renderer uses the same760px viewport media query as CSS; mobile layout buttons synchronized/hidden in favor of panel tabs. Browser tested at390px inner width, no horizontal overflow.
- Low, node ID input sync: inspector updates numeric source ID for pointer/keyboard lookup and clears stale hidden selections.
- Low, tiny metadata typography: legends/status/labels raised to10.5px and secondary text darkened. No formal WCAG conformance certification is claimed.
- Low, obsolete timer/default HTML: removed continuous-autoplay cleanup; defaults match the60µmZslab. Camera preset changes remain view transformations only.

Additional browser fixes: fit full-width orthographic projection to the smaller viewport dimension; clip Canvas fallback per pane; show explicit manual delta-range selection and sign; include numeric signed error change in point inspector; add exact coordinate axis labels; source-node/all-model residual readout; meaningful empty-state handling. Public data validation independently recomputes global RMSE from exported vectors and preserves exact source membership/global metrics. Rounding-induced RMSE changes are below1.3e-7µm.

Browser checks cover WebGL startup, model/filter changes, common global score invariance, reference/difference lens, empty slab, source-node inspection, selected-octantCSV737rows,390px responsive single-pane mode and Canvas fallback. Raw Argon review status labels are static opinions, not claims that the model executed these browser checks.
