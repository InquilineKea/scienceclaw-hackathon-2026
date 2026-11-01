# Independent nonlinear material and solver audit

Audit scope: original local C++17 and JavaScript source, original independent Python standard-library mathematical probes, and inert numeric quadrature tables. No imported numerical package, cloud action, publication, installation or new experimental error scoring was performed by this auditor. Source hashes are recorded separately in NONLINEAR-STATIC-SOURCE-HASHES.json. Files can continue to change after this snapshot.

## Mathematical design

The scalar law is continuously joined at zero compression and at tensile threshold 0.04. In compression the proposed energy is d0²[exp(e/d0)−1−e/d0], force d0[exp(e/d0)−1], tangent exp(e/d0); tension is quadratic through 0.04 followed by a continuously joined exponential branch with scale 0.05. No compression floor was introduced. For a reference direction n, stretch strain is |Fn|−1, so left rigid rotations preserve the energy exactly.

The slip update minimizes w(ef−s)+H s²/2+Y(s−s_old), constrained to s≥s_old, H=0.05. Inactive state s_old is admissible when w'(ef−s_old)≤Y+H s_old. Active elastic strain solves w'(elastic)+H elastic=H ef+Y. Its condensed tangent is w''H/(w''+H); inactive tangent is w''. This is irreversible tensile lengthening with hardening, rather than signed frictional slip or measured crosslink damage. Its endpoint depends on an assumed loading path, which the two experimental images do not identify.

The exact Piola derivative includes a geometric term: with a=Fn/|Fn|, T=w', c=condensed tangent, δL=a·δFn,

    δP = 15 Σ weight [c δL a + (T/|Fn|)(δFn−a δL)] ⊗ n.

The T/|Fn| term is negative in compression. Omitting it in a Hessian or stability check would conceal negative-curvature modes. Positive scalar w'' and positive detF do not imply a stable finite-strain equilibrium or rank-one convexity. With isotropic fourth moments, the reference small-strain limit has λ=μ and ν=0.25. It is not identical to the previously selected ν=0 model; retain an own-law no-buckling/no-slip control and the older baselines.

Independent local probes in INDEPENDENT-MATERIAL-REFERENCE.json passed scalar incremental-gradient, condensed-tangent, KKT, repeated-hold, finite-F gradient/HVP, left-objectivity and cyclic energy/dissipation checks. These are controlled constitutive tests, not proof of convergence of the experimental-field problem.

## C++ static readback

The audited solver computes the energy gradient as 15 V weight T (Fn/|Fn|) times the directional nodal shape gradient, consistent with the stated energy and envelope theorem. Fixed nodal components are excluded from optimizer dot products and every search update. Previous plastic state remains fixed through all objective/line-search evaluations; the returned state is committed only after the accepted global load increment. Initial reactions at the undeformed state are zero; trapezoidal work uses prescribed-boundary reactions at successive load fractions. Stored elastic plus hardening energy and incremental Y Δs dissipation are logged separately.

The initially reported inverted-trial defect has been corrected: every objective evaluation now rejects detF≤0.05, nonfinite directional length and nonfinite/overflowed local potential. The starting state must be finite. Final acceptance requires finite energy and the free-force residual, followed by the determinant gate. Active C++ return mapping has a bisection fallback and final KKT rejection. No new critical implementation blocker was found in this static snapshot.

Remaining qualification requirements:

* The existing original C++/JS check verifies four laws on a controlled field to roughly 1e−14 relative gradient agreement, including plastic laws starting from zero previous slip. It does not test a nonzero previously committed state, unloading/reloading, or near-yield branch transitions. Add that history coverage and retain source hashes. JavaScript currently lacks C++'s explicit final active KKT guard and uses a different Newton iteration count; do not assert literal source equivalence.
* The optimizer returns a stationary state, not a certificate of a local minimum. Check the exact constrained incremental Hessian at the selected load checkpoints, including the geometric term and condensed slip tangent. A bounded random-start Lanczos check can detect negative modes but cannot prove absence of all missed modes; disclose iterations, starts, residual and state coverage. Report any detF guard proximity, since a guard-limited minimum is a model constraint rather than physical damage.
* Trapezoidal reaction work is an approximate path integral. The logged work−stored−dissipation residual must meet the frozen gate; compare 10/20 ramps for selected cases. Plastic internal states must belong to their own paths. Neither work nor dissipated energy at the observed endpoint is fracture toughness.
* A failed kinematic warm start can abort before optimization although the previous free-node state with updated boundary values might remain valid. If a fallback is desired, specify it before scoring and use identically across candidates; preserve initial failures. Do not change the accepted force tolerance after seeing prediction scores.
* Candidate definitions, exact angular resolution, rescue limits and actual baseline controls must replace the superseded draft before Pos007 selection. At this audit, the old draft still described three buckling levels crossed with four slip states/H=0.10; actual source design is four levels including no buckling crossed with three slip states/H=0.05.

## Angular quadrature

Original independent controlled probes compare 36 deformation/law combinations (three finite F, four compression laws, three yield choices, zero previous slip) against 8192 positive sphere points. This concerns local material integration and right-material rotational isotropy; it is separate from left frame objectivity. All four-moment patch checks can pass while these nonlinear errors remain.

| Rule | Maximum energy relative difference | Maximum Piola relative difference | Maximum right-rotation energy difference |
|---|---:|---:|---:|
| 26 Lebedev | 13.896% | 36.430% | 21.037% |
| 50 Lebedev | 1.383% | 10.821% | 2.314% |
| 110 Lebedev, actual inert table | 0.570% | 3.320% | 0.366% |
| 302 Lebedev, actual inert table | 0.0815% | 2.296% | 0.122% |
| 512 product sphere | 0.0719% | 2.882% | 0.210% |
| 1152 product sphere | 0.0387% | 1.388% | 0.0173% |
| 2048 product sphere | 0.0243% | 0.807% | 0.0226% |

The 8192 rule's own controlled right-rotation energy difference is 0.00687%. These maxima are not estimates of full-field displacement error. Rule110 is a reasonable improvement for bounded screening, but selected full re-equilibration at302 or higher is required to assess whether conclusions survive angular discretization. Evaluation of a finer energy on the same equilibrium does not replace re-equilibration. A result near the proposed 5% predictive-success margin cannot ignore unresolved numerical sensitivity.

Full machine-readable probes and originals are ANGULAR-QUADRATURE-REFERENCE.json, ANGULAR-QUADRATURE-REFERENCE-EXTENDED.json and ANGULAR-QUADRATURE-REFERENCE-110-302.json with matching original scripts.

## Scientific inference limits

The tets interpolate a continuum over measured displacement nodes. They do not reconstruct measured collagen fibers, junctions, pores or their connectivity. The boundary conditions retain the earlier partial-Dirichlet box and near-cell nodal constraints, including material inside the cell region; there is no newly segmented physical cavity. The 35 µm PIV-support purge and frozen masks must remain identical across baselines and new laws.

Pos008 was previously observed and motivated this extension; any improvement is on a reused benchmark. Select only on Pos007, freeze before further Pos008 scoring, and preserve every failed candidate. No independent modulus, cell traction, aging mechanism, crosslink placement, G″ or species effect is identifiable from this conditional displacement-only comparison. The raw P1 strain descriptor remains exploratory and differs in support from the DVC measurement. Keep the same descriptor for a prespecified safeguard, but do not label it measurement-matched strain validation.
