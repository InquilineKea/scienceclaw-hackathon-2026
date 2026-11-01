# Uniform versus clustered adhesion: law sensitivity

**The topology effect is conditional on relative sliding time, local stiffness and cell coupling. It does not survive as a universal positive or negative prediction.** Changing the exact tested sliding-law family at fixed coefficients changed the magnitude but produced no direction-resolved sign reversals. Changing selected-to-background sliding time alone produced twelve matched-design sign-reversal comparisons across the screened conditions. These are pointwise exploratory intervals, not multiplicity-corrected discoveries or biological predictions.

The study ran on the laptop CPU with original C++ code and Python standard-library analysis, without new scientific dependencies, GPU use or additional cloud provisioning. It did not modify the H100 dynamics or spend additional cloud compute. The original public models are intact. This is a new cell-cavity screening model, not a reproduction of the earlier public H100 bulk-strain calculation, which did not directly measure adhesion-site forces.

## Concrete equal-stiffness example

At edge retention0.95, bending0.003 and clamped adhesions, selected and background edge stiffness are identical. Thus the uniform and clustered networks have exactly the same instantaneous stiffness; only the spatial assignment of sliding times differs. The response is mean adhesion-force magnitude integrated over the hold. Contrast is2(C-U)/(C+U), expressed as percent of the pair's average.

| Sliding law | Selected/background sliding time | Mean clustered-minus-uniform contrast | Pointwise95% paired-seed interval |
|---|---:|---:|---:|
| Linear viscous |0.1|−4.72%|−7.98% to−1.56%|
| Linear viscous |1|0.00%|0.00% to0.00%|
| Linear viscous |10|+9.77%|+2.60% to+17.44%|
| Yield threshold |0.1|−1.50%|−2.89% to−0.17%|
| Yield threshold |1|0.00%|0.00% to0.00%|
| Yield threshold |10|+3.70%|+0.30% to+7.08%|
| Eyring rate strengthening |0.1|−4.28%|−6.90% to−1.56%|
| Eyring rate strengthening |1|0.00%|0.00% to0.00%|
| Eyring rate strengthening |10|+9.58%|+2.74% to+16.89%|

All rows use twelve paired geometry seeds. The zero rows are an exact control: changing a selected-edge label without changing any material coefficient must have no mechanical effect. This result passed exactly. Faster/slower refer to internal sliding time relative to the background, not calibrated cellular seconds. This example was selected to illustrate the equal-stiffness result after the full sweep; it is not a separately preregistered confirmatory test.

## Coverage and uncertainty

The main frozen design contains240 material/loading scenarios and twelve graph attempts each, for5,760 possible histories. A mechanically unstable graph at seed4708,density0.8 failed the positive-definite constrained-Hessian check at both bending coefficients. Both architecture members and every material scenario for those graph blocks were excluded; no artificial springs were added. There are5,520 accepted histories,2,760 paired comparisons, and11–12 seed pairs per scenario.

For the primary hold-integral metric,91 parameter scenarios had intervals entirely below zero,14 entirely above zero, and135 included zero.140 scenario means were inside the declared±5% screening band. These counts describe coverage of the chosen factorial grid, not likelihoods of mechanisms. The grid includes exact null controls and intentionally broad parameter stress tests. Bootstrap intervals quantify paired geometry-seed variability conditional on each model; they omit parameter-prior, structural-model and biological uncertainty. They are pointwise, without multiplicity correction. Individual seed contrasts are retained in summary.json and the explorer.

## Which inputs matter within the screened ranges?

For each input, vary it while holding the other screened inputs fixed and calculate the range of scenario-mean topology contrasts. Average those ranges over matched design blocks:

| Varied input | Average range in topology contrast | Largest range |
|---|---:|---:|
| Local instantaneous stiffness ratio0.25,1,4|15.50 percentage points|30.22pp|
| Clamped versus compliant adhesion coupling|6.11pp|13.58pp|
| Selected/background sliding-time ratio0.1,1,10|5.03pp|14.49pp|
| Linear, yield-threshold or Eyring law|2.11pp|6.07pp|
| Edge retention0.80 versus0.95|1.34pp|4.57pp|
| Bending coefficient0.003 versus0.03|0.70pp|2.47pp|

The ranking depends on the chosen ranges. Comparing an infinite-stiffness clamp with one finite spring is not an empirically weighted distribution of cell behavior. This is a screening sensitivity analysis, not a formal expected-value-of-information calculation. Within its limits, it argues for constraining coefficients and coupling before investing in increasingly elaborate sliding equations.

## Numerical and geometry checks

Force-energy finite-difference error was1.28e-13 or less. Rigid translation produced force norm3.37e-17. Maximum force-balance error was1.60e-10; maximum equilibrium residual1.00e-10. Matched initial shear energies agreed to2.00e-15 relative error. Sliding dissipation was nonnegative. The single-element backward-Euler relaxation matched its analytic discrete solution to2.61e-18. These checks establish internal numerical consistency, not physical validity.

Halving dt from0.05 to0.025 in the selected subset changed individual hold-force integrals by at most0.341% and scenario-mean topology contrasts by at most0.0265 percentage points.308 histories were accepted in that check. This supports temporal numerical stability for those conditions only.

The originally planned9x9 larger-domain screen changed mean contrasts substantially. However, it changed cavity/lattice alignment, random graph realization, selected edge count and cluster footprint as well as boundary distance. It cannot isolate a boundary effect. Its308 accepted histories are retained, rather than presented as mesh convergence.

An additional, explicitly exploratory nested-core diagnostic preserved all original7x7 core-node positions, retained edges and selected-edge identities, added one surrounding ring of unmodified matrix, moved the boundary outward and re-matched initial shear stiffness.280 histories passed; seed4704 and4708 graph blocks failed the Hessian check. Comparisons use ten common accepted seeds. Across the fourteen checked scenarios, mean topology contrasts changed by−2.01 to+0.79 percentage points. All paired intervals for the change included zero and were sometimes broad. Thus the large change in the first domain screen was not reproduced when the local pattern was preserved. This does not establish domain independence; geometry/cluster footprint and boundary coupling must remain explicit in any later model.

## Molecular simulation decision

1. **Measure local stiffness and relative sliding/relaxation, not just whole-fibril high-force extension.** A matched hydrated bundle or junction study should extract force versus relative slip and hold/creep recovery for native crosslinks and unlinked hydroxylation-matched precursors. The current equal-stiffness sign reversal makes the direction of selected/background sliding-time contrast a particularly important unknown. Relative stiffness remains influential even after one bulk shear observable is matched.
2. **Use rate and load variation to distinguish friction mechanisms.** Compare small reversible loading, a hold, unloading and recovery, then multiple loading rates. Measure whether there is a slip threshold, how force depends on velocity, and whether residual displacement recovers. Those observables distinguish linear drag, yield-like resistance and activated rate dependence more directly than another axial force-extension endpoint.
3. **Control hydration and chemical state explicitly.** Use matched water content, lateral packing, ionic conditions, hydroxylation pattern and declared protonation/charge treatment. Glucosepane is not represented by the native Martini HLKNL/PYD parameters. Free-HYL parameter compatibility is still unresolved; geometry-only controls are not ready-to-run validated controls.
4. **Constrain the network/cell boundary independently.** Test a physically justified range of adhesion compliance and geometry before interpreting absolute force transmission. The present springs do not represent integrin/talin binding kinetics or cell feedback; adding detailed collagen chemistry will not determine those parameters.
5. **Retain the ongoing H100 run as a benchmark.** Its high-force axial protocol can validate a limited structural/mechanical implementation. It cannot supply the low-force sliding law or a physical cell-scale friction time by itself. No additional H100 dynamics or budget extension is authorized or initiated by this analysis. Molecular follow-ups above are a prioritized protocol, not executed results.

The next targeted simulation should therefore ask whether matched native crosslinks make hydrated relative sliding substantially slower or faster than the background, while measuring the corresponding small-strain force–slip response. Only if rate/load histories require a yield or activated law should a more elaborate law become the first calibration target. These decisions are conditional on the current small-strain screen;3D remodeling, buckling, fluid drainage, rupture and cell feedback remain separate potential causes of model failure.

Files: explorer.html is standalone and interactive; design.json is the original design; METHODS.md defines the equations; paired-contrasts.csv and summary.json retain all scenarios and seed contrasts; each raw-results CSV retains every accepted history and failure logs retain exclusions. Source, compiler invocation, validation receipts and SHA256 manifest are preserved locally.
