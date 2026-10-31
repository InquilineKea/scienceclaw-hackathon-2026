# Final 160-case audit plan

Prepared 2026-10-31 before the final download. This is a prospective check plan, not evidence that the final run is complete. No new simulation, package installation or cloud spending is required. The original standard-library [analyzer](../analyze-results.py) implements the numerical checks below and preserves unqualified descriptive curves.

## Freeze and identify the input

1. Receive the final download into a new directory, retaining interrupted/checkpoint archives, error records, logs, protocol, exact deployed solver and job receipt. Verify the downloaded archive against its remote SHA-256 before extracting. Never overlay checkpoint files onto the final directory or use filenames alone as proof of provenance.
2. Confirm that the final job receipt identifies the 25/50-step amended solver, four seeds 29–32, planes 1/2, rupture thresholds 0.1/0.2, common shear cap 0.5, unchanged force tolerance 1e-7, unchanged step tolerance 5% and energy tolerance 2%. Keep original 100/200-step controls separate. Check identical seed geometry and calibration across placement/resolution arms, degree-stratified selection, and common edge/angle material definitions from the deployed input/source provenance. These source-level identity checks are not proved by the result analyzer.
3. The expected grid has 160 final records: 4 seeds × 2 planes × 2 thresholds × 5 conditions × 2 resolutions. Conditions are baseline density 0, clustered/distributed density 0.15 and clustered/distributed density 0.30. There are 80 coarse/fine pairs. A failed or missing record is an outcome, not permission to replace it with a checkpoint or a different-resolution control.

## Execute only original standard-library analysis

Once the verified final input exists, use the original script with an explicit input and a fresh analysis directory. Replace the input path below with the actual verified download location; do not run against the checkpoint and label it final.

```sh
python3 collagen-3d-bovine-calibration/analyze-results.py --self-test
python3 collagen-3d-bovine-calibration/analyze-results.py --input collagen-3d-bovine-calibration/remote-final/results --out collagen-3d-bovine-calibration/analysis-final --coarse-steps 25 --fine-steps 50
```

The analyzer hashes every final/error input it reads, plus the final amplitude calibration and stiffness files. `*.partial.json` files are separately listed and excluded. Invalid JSON, explicit errors, duplicate keys, unexpected files and all missing case keys remain visible. Ambiguous duplicate endpoints are excluded rather than choosing a favorable record. Verify these categories manually against the download manifest and workload log before accepting the inventory.

For complete inventory, require loaded=160, missing=0, duplicate keys=0, unexpected production files=0 and complete resolution pairs=80. This inventory requirement is separate from numerical qualification: complete computation may still fail any scientific/numerical gate. Error files can coexist with later successful attempts; retain their history and inspect matching keys rather than deleting them to improve counts.

## Numerical and endpoint checks

For every record, inspect `runs.csv`; for every paired condition, inspect `resolution-pairs.csv` and `summary.json`:

- Exact completed trajectory/grid: converged status, accepted frames, steps+1 frames covering the prescribed uniform 0→0.5 grid. Do not infer completion from the largest saved strain alone.
- Accepted final per-seed amplitude calibration, both planes residual-qualified. Recompute conditional Pa and J/m³ using the same accepted final scale within each seed. These are bulk-matched scales, not independent measured fiber or fracture parameters.
- All accepted-frame force residuals ≤1e-7 model units.
- Terminal work balance, recomputed as work minus stored energy minus deletion loss minus relaxation loss, has relative error ≤2%, consistent with the serialized diagnostic. Losses must remain nonnegative and nondecreasing within the declared numerical floor. Inspect sign conventions and any anomalous per-step energy diagnostics; terminal closure alone cannot prove every avalanche is exact.
- Maximum observed stress and work through cap differ by ≤5% between 25 and 50 steps. Report failure counts and their conditions before aggregating effects. Do not loosen either tolerance to raise coverage.
- All three fine-grid checked states (initial, peak, terminal) must have adequate gradient convergence. Strict qualification requires positive resolved curvature at every checked state. Marginal/no-resolved-negative records have a separate conditional tier and are not proofs of stability. Confirmed negative curvature, unresolved finite-difference accuracy, unresolved negative modes, absent or unchecked records fail both tiers. Three selected checks do not establish stability along the entire path.
- Fracture-endpoint qualification additionally requires resolved, uncensored peaks at both resolutions and ≤5% work-to-peak difference. Keep maximum-at-cap right censoring, insufficient post-peak evidence and incomplete trajectories distinct. Never report work through cap as toughness or infer Gc without a physical crack area and appropriate test.
- Damage fraction precision is a separate disclosure: report coarse/fine broken-edge counts, absolute fraction and percentage-point differences. No damage precision tolerance was prespecified. A clustered-minus-distributed damage ranking must agree in direction at both resolutions, in addition to its numerical tier; agreement is a consistency check, not a precision proof. Zero/zero is no rank difference.

## Paired inference and claims

Use the common seed/plane/threshold/density pairs in `placement-pairs.csv`, baseline comparisons in `baseline-pairs.csv`, and degree-matched small-strain checks in `stiffness-pairs.csv`. Show descriptive, conditional and strict coverage separately. For damage use the additional damage-ranking tiers. Do not select the most favorable resolution, threshold, angle, seed or stability tier after viewing results.

Average the two prespecified angle contrasts within a seed first. Primary aggregate means require both angles qualified for that seed. Report number of contributing seeds, mean/range of seed-mean contrasts, sign counts and missing pairs. Four synthetic seeds are the independent network draws; the two angles, two resolutions and multiple thresholds are repeated conditions, not independent observations. Report exact coverage for every metric: a single universal accepted subset can hide endpoint-specific exclusions.

Audit conclusions against `report-data.json`: every headline curve must expose the same endpoint and qualification tier used for its numerical contrast. Keep failed/marginal curves accessible descriptively. A ranking with incomplete seed coverage or sensitivity to resolution/stability tier remains conditional. Even full numerical passage establishes a synthetic bulk-matched comparator, not measured 3D architecture validation, chemical aging calibration, specimen-level bovine fracture validation or a species difference.

## Completion record

Write a final audit receipt only after verification and analysis: input archive/hash, deployed source hash and amendments, raw and analyzed counts, gate coverage by condition, censoring, selected-state classifications, damage step differences, paired seed coverage, retained failures and output hashes. State separately whether computation finished, numerical gates passed, and experimental validation exists. Preserve the earlier checkpoint analysis under its original name. Archive the complete verified run and analysis to the mounted microSD under the user's standing archive policy if the actual volume is available; otherwise explicitly mark archival pending.
