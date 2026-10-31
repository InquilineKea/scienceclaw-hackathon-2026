# Nonlinear collagen field prediction benchmark

Public interactive report: https://inquilinekea.github.io/scienceclaw-hackathon-2026/nonlinear-3d/

Read REPORT.md, PROTOCOL-FROZEN.md and NUMERICAL-AMENDMENT.md before interpreting outcomes. Position008 is adaptively reused; this is not fresh biological validation. The final dataset is a measured PIV sampling mesh with internal displacement constraints, not measured fiber connectivity. The sliding law is irreversible scalar plastic lengthening, not a calibrated chemical crosslink model.

## Reproduction and inputs

Original code uses Node.js, Python standard libraries and a C++17 compiler, with no imported simulation package. Review source before execution under your own policy. Numeric angular tables are data, not executable code.

1. Recreate the sibling `collagen-measured-3d-validation` data folder using its original input extraction/mask scripts and frozen masks, linked in that study's report. Download the authors' ClassicSingleCellTFM and evaluated archives at https://github.com/rgerum/saenopy/releases/tag/v0.7.4 . Retain geometry.json, measured.json and frozen-mask.json under data/Pos004, data/Pos007 and data/Pos008. Do not optimize masks from displacement error. Baseline fields/results are from the preceding study and must be recomputed identically or recovered from its private complete archive.
2. Retrieve the two plain numeric quadrature files at URLs in audit/QUADRATURE-PROVENANCE.json into audit/. Verify their SHA-256 hashes. Raw tables are omitted from the public export; the source directory labels data/code LGPL. No downloaded code is required.
3. Run original checks.mjs, preflight.mjs, compile solver.cpp with an existing C++17 compiler (`-O3 -std=c++17`, no fast-math), and compare the JS/C++ constitutive calculations using crosscheck.mjs. Numerical reference audits are retained.
4. Prepare boundary-only binary inputs with `node prepare-input.mjs Pos007 110` and corresponding Pos008 110/302 commands. The preparation reads measured input but stores only prescribed boundary vectors; interior targets are excluded from the solver binary. Solver input dimensions/physical conventions are documented in the source.
5. Run run-sweep.mjs for the twelve fixed Pos007 arms. All twelve terminal outcomes are required before `node analyze.mjs selection`; the immutable SELECTION.json must exist before any Pos008 scoring. Historical selection is supplied; reproduce in a fresh output directory without overwriting it. Do not rerun parameter selection from Pos008 errors.
6. Run run-test.mjs and run-refinements.mjs using frozen selection; collect-test.mjs applies identical score masks. Compile hvp-audit.cpp and run numerical-controls.mjs for independent load-step/angular checks and the bounded final-state Hessian screens. The correct incoming slip state is `.previous-state.bin`, not the final committed `.state.bin`.
7. make-plots.py, make-animation.py and report-and-stage-public.py consume the saved results. The animation rotates a camera around final fields; it does not invent measured loading or damage dynamics.

Actual production source/input hashes, all candidate metrics, histories and diagnostics are retained. Public export excludes input binaries, executable binaries, raw author images, full internal state arrays and probes; complete private local/microSD records retain those present in the run folder. The public zip is a bounded results/source artifact, not a self-contained raw-data archive.

Independent 20-step and302-direction controls must each satisfy <=1% changes in prediction-field L2, error RMSE and normalized reaction work. A nonnegative32-step seeded Lanczos screen means no detected negative curvature in that subspace; it does not establish global stability or mesh convergence. Work is normalized surrogate-model work, never fracture toughness.
