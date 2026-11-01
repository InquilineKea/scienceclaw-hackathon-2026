# Bovine bulk-matched 3D comparator and campaign audit

This completed computational study calibrates a synthetic periodic-network baseline to bovine hydrogel bulk rheology. Physical validation against measured 3D collagen architecture, molecular aging chemistry and species-specific fracture has not been achieved.

## Complete inventory and numerical qualification

Recovered 160/160 planned final cases; 160 complete trajectories, 80/80 coarse/fine pairs. Force-qualified cases: 160; terminal energy-qualified cases: 160. Strict numerical pairs: 0; explicitly conditional pairs allowing marginal selected-state curvature: 58. Conditional resolved-peak endpoint pairs: 3.

The four seeds are the independent synthetic realization units. Two shear planes, rupture thresholds, placements and load grids are repeated conditions. Force/energy checks do not establish biological truth. Marginal curvature is not proof of stability along the trajectory. Capped stress maxima and cap work cannot be interpreted as toughness or thermodynamic phase change.

All 54 previously completed result records and two commissioning records are preserved byte for byte. Model/simulate/checks function source and AST identities match the prior execution. Failed optimizer attempts and finer-grid controls remain separate. No acceptance threshold was relaxed.

## Stiffness result

All 40 small-strain states accepted. Mean modified/baseline stiffness at 15% locks: clustered 1.445585, distributed 1.479934; at 30%: clustered 1.979444, distributed 2.270143. Mean paired seed-level C/D ratios 0.988148 and0.883184. At each fraction, distributed is stiffer in three seeds and clustered in one. The positive added angular penalties make stiffening expected by construction. Initial graph/geometry/reference inventory is held identical; selected-site degree/angle budgets match within roundoff. Local orientation and segment lengths are not matched. No graph edge is added.

## Paired damage comparisons

|Rupture|Locks|Metric|Tier|Eligible seeds /4|C/D mean|C−D signs +/−|
|---|---|---|---|---|---|---|
|0.1|0.15|maximum_observed_stress_Pa|descriptive|4|0.97838|1/3|
|0.1|0.15|work_through_cap_J_m3|descriptive|4|0.99242|2/2|
|0.1|0.3|maximum_observed_stress_Pa|descriptive|4|1.02920|2/2|
|0.1|0.3|work_through_cap_J_m3|descriptive|4|1.00098|2/2|
|0.2|0.15|maximum_observed_stress_Pa|descriptive|4|1.01252|2/2|
|0.2|0.15|work_through_cap_J_m3|descriptive|4|1.00265|1/3|
|0.2|0.3|maximum_observed_stress_Pa|descriptive|4|0.99479|2/2|
|0.2|0.3|work_through_cap_J_m3|descriptive|4|1.00119|2/2|
|0.1|0.15|maximum_observed_stress_Pa|qualified_conditional|0|unavailable|0/0|
|0.1|0.15|work_through_cap_J_m3|qualified_conditional|0|unavailable|0/0|
|0.1|0.3|maximum_observed_stress_Pa|qualified_conditional|0|unavailable|0/0|
|0.1|0.3|work_through_cap_J_m3|qualified_conditional|0|unavailable|0/0|
|0.2|0.15|maximum_observed_stress_Pa|qualified_conditional|2|0.99466|0/2|
|0.2|0.15|work_through_cap_J_m3|qualified_conditional|2|0.99174|0/2|
|0.2|0.3|maximum_observed_stress_Pa|qualified_conditional|4|0.99479|2/2|
|0.2|0.3|work_through_cap_J_m3|qualified_conditional|4|1.00119|2/2|

Subset estimates are explicitly subset estimates; no complete four-seed claim follows when fewer than four seeds qualify in both planes. Descriptive estimates retain failed refinement gates. Damage precision/ranking is separately reported in the CSV audits, not guaranteed by stress/work qualification. The sweep does not establish a general robust fracture ranking.

## Calibration and remaining campaigns

The reused source-specific Kelvin–Voigt fit has G′ = 9.522 Pa and G″ = 3.891 f(Hz) Pa at 1.5 mg/mL, 37°C, 1% amplitude; mean file model-selection CV complex NRMSE 0.498. Each synthetic seed receives one baseline scalar fixed across interventions. This is controlled bulk matching, not held-out architecture validation. Homogeneous baseline viscosity 0.6193 Pa·s is omitted from quasistatic fracture and does not identify microscopic/aging dissipation.

Campaign 1 raw 3D coordinates, adjacency, fiber polylines and full joint distributions are available on request and unrecovered. Campaign 2 existing hydrated dityrosine paired laws pass 0/3; no wet constitutive transfer. Campaign 3 BOV/RAT figure-summary calibration is conditionally possible after digitization/aggregation uncertainty checks; no beaver–human mechanical robustness ranking is identified. See campaigns/ for evidence, prospective validation contracts and the unsent architecture-data request.

## Sources

Bovine rheology: [Zenodo 17413651](https://zenodo.org/records/17413651),CC BY 4.0; [2024 atlas](https://doi.org/10.1016/j.actbio.2024.07.002). Measured architecture summaries: [2025 study](https://doi.org/10.1016/j.mtbio.2025.101962). Independent local strain route: [NIST DVC](https://data.nist.gov/od/id/mds2-4129).
