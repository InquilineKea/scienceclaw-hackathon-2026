# Fracture Atlas — methods and limits

Version 1, 31 October 2026. Original, dependency-free, dimensionless **2D** fiber-bundle model. This is a small hypothesis-generating computational comparison, not a calibrated collagen constitutive model or a design certification for extreme environments. The executed model SHA-256 is in `data/results.json`.

## What the coordinates and units mean

The reference specimen is a unit square with nominal unit out-of-plane thickness. Coordinates use L₀, material elastic scale uses E₀, and density uses ρ₀. Energy is normalized by E₀L₀³; energy density by E₀; force by E₀L₀². Time t₀ = L₀√(ρ₀/E₀), acceleration L₀/t₀². No dimensional L₀, E₀ or ρ₀ is fitted or supplied. Therefore the results do not specify MPa, joules, g-loads or tissue-safe accelerations.

The scalar quasistatic reaction Q = ∂U/∂q is conjugate to prescribed strain q. With reference volume one, its numerical value is also a generalized nominal stress. For biaxial compression Q = −(Pxx + Pyy); it is not a hydrostatic pressure measurement. The physical 3D mean stress would require a third normal component.

## Generator and fair comparisons

Baseline: 6×6 points, 36 nodes, 82 edges, seeds 17/29/43/71/101. Interior grid points have independent positional jitter (±0.15 grid spacings); boundary coordinates remain on the grips. Every family starts with the same points for a given seed. Candidate edges receive distance and seeded random scores. A minimum-score spanning tree ensures connectedness; further edges are added in score order until the fixed edge budget is met. Edge crossings are **not** junctions. There are no non-bonded contact forces.

Family-specific scores favor horizontal bundles, short disordered links, a central trunk with spatial branches, four spatial communities, diagonal reinforcement, a single link across the X midline, or two high-degree hubs. These are idealized graph motifs, not reconstructions of imaged collagen. “Isotropic” is the code label for a jittered short-range network; finite specimens are not perfectly isotropic. “Loops” means diagonal placement of redundant paths, not a larger cycle count: all baseline connected graphs have cycle rank E−N+1 = 47.

Every baseline has ΣAₑLₑ = φ = 0.06. Areas are normalized after edge selection, so longer total fiber length implies thinner effective bundles. This controls collagen volume and edge count simultaneously; it does not control every geometric statistic. The edge-count sweep (55/68/82/100) is separate and retains φ. It varies coarse-grained connectivity, not a measured molecular crosslink concentration. The size sensitivity (5×5 and 7×7) approximately matches mean degree and φ; it is not a mesh-refinement proof for a fixed material realization.

`distribution` assigns log-uniform relative bundle areas, renormalized to φ. `lengthBias` changes edge selection and therefore geometry/topology. Fibril diameter d changes effective bending per bundle at constant total collagen volume: the implied count of constituent fibrils changes. It is not an independent increase in solid fraction. Adding the elastin-like parallel component adds a separate material budget; those rows are not pure-topology comparisons.

## Constitutive law: all constants hypothetical

For an edge with reference length L, area A, current axial strain e=l/L−1, energy is A L w(e), axial force A w′(e). E₀=1. Crimp is modeled with a compliant toe slope t=0.08, recruitment strain c=0.04 and a cubic tensile force above recruitment:

```
0 ≤ e ≤ c:   w = t e²/2
e > c:       z=e−c; w = t c²/2 + t c z + z²/2 + z⁴
```

Compression has slope r=0.08 up to shortening b=0.025, then slope 0.08r. This is a phenomenological post-buckling force law, not a resolved Euler beam instability. For u=−e>b:

```
w = r[b²/2 + b(u−b) + 0.08(u−b)²/2]
    + C max(0,u−0.6)⁴/4,       C=20
```

The final term is an **artificial segment-collapse regularizer**. Without it, some edges collapse to zero length and the angular force becomes singular. It does not model steric fibril contact or physical densification. `collapseUsed` flags runs where an intact edge shortened by more than 60%. C=10 and C=40 sensitivity runs quantify this assumption; they do not validate it. Default tensile and shear results often activate the regularizer locally even though the specimen expands globally.

At each node, the two most nearly antiparallel edges form one continuation hinge if their initial angle exceeds 0.6π. Hinge energy is K(θ−θ₀)²/2 with the angle difference wrapped to (−π,π]. K = bend·√(A₁A₂)d²/(16Lmean), default `bend=20`, `d=0.025`. This mimics an EI/L scaling with a deliberately adjustable coupling multiplier; it is not a fitted fibril modulus. Hinge energy vanishes if either adjacent collagen edge ruptures. All other junction angles are freely rotating.

Rupture is irreversible when tensile strain exceeds 0.24[1+0.18(2r−1)] for a seeded uniform r. This imposed law is common across families. It demonstrates the consequences of geometry and redistribution **conditional on the rupture rule**, not a derived collagen rupture threshold. Compression never directly deletes an edge.

Optional sacrificial links add a parallel tensile spring of stiffness 0.3A/L on a specified random fraction of collagen edges. They release at e>0.075; their stored energy is recorded as dissipated. In cyclic runs they can reform only at e≤0, where the extra spring has zero stored energy. This is a reversible toy mechanism with no chemical identity, binding kinetics or hidden-length calibration. Optional background elasticity contributes AL·elastin·e²/2 even after collagen rupture. Collagen connectivity metrics deliberately ignore that surviving background.

Hydration, collagen types I/II/III/etc., glucosepane, pyridinoline, LOX identity, proteoglycan osmotic pressure and glycation do **not** set parameters. The damping slider is a generic rate parameter, not water content. Proteoglycan/fluid transport needs additional degrees of freedom, permeability and independent measurements, so no misleading composition-to-hydration mapping is provided.

## Loading and supports

| Protocol | Constraint / input | Observation |
|---|---|---|
| X tension | X=0/1 faces prescribed normal displacement; Y free except one pin | 60 increments to q=0.85 or criterion |
| Y tension | Same graph loaded between Y=0/1 faces; X free except one pin | 60 increments to q=0.85 or criterion |
| Shear | Bottom fixed X/Y; top shifted X with its Y fixed; sides free | 60 increments to q=0.90 or criterion |
| Unconfined compression | X faces approach; lateral motion free except one pin | 60 increments to q=0.30 or criterion |
| Confined compression | X faces approach; Y boundary displacement fixed | 60 increments to q=0.30 or criterion |
| Biaxial compression | All four faces prescribed equal inward normal strain | 60 increments to q=0.30 or criterion |
| Constrained pulse | Left edge clamped; each node gets body force m a(t) along X | a=0.018 sin(πt/8), t≤8; then zero, observe to t=16 |
| Free pulse | Same force per mass; all nodes free | Rigid translation is the expected control |

Quasistatic loading has no assigned finite strain rate: internal relaxation is completed at each step. The pulse has lumped mass ρ/N at each node (default total density 1), damping rate 0.12/t₀ and dt=0.0125t₀. Integration uses symplectic Euler and an exponential linear damping substep. Damping is relative to the constrained frame for clamped runs and to mean translation for the free control. Pulse duration and density sweeps keep acceleration amplitude fixed; they intentionally change impulse and total force, rather than imposing equal impulse across those sweeps.

Confined displacement, uniform hydrostatic traction, differential hydraulic pressure and interstitial pore pressure are different boundary-value problems. Only the first is solved. Biaxial compression is a solid-skeleton analogy. There is no fluid mass balance, drainage, permeability, cavitation, contact, shock wave, thermodynamics, inertia-calibrated material law or out-of-plane buckling. Extrapolating these results to extreme hydrated pressure or acceleration would be unsupported.

## Solver, failure, energy and retained connectivity

The quasistatic solver is original L-BFGS with memory 9, backtracking Armijo line search and a 0.04 maximum trial nodal displacement. Default residual tolerance: max absolute free-DOF energy gradient <2×10⁻⁷. Maximum iterations 1,400, with a fresh-history retry up to 2,800. After convergence, overstretched collagen/sacrificial links are removed and equilibrium is resolved until no further link changes. All completed production runs meet this stated residual test. This guarantees neither a global energy minimum nor physical validity.

The quasistatic stopping criterion is the first sampled state with **any** of: ≥20% of initial collagen volume ruptured; no intact collagen path connecting the loaded faces; reaction below 50% of its running maximum (only after q>0.08 and peak>10⁻⁵). The force-drop criterion can identify a buckling/softening loss of load capacity without rupture. It is an operational failure definition. `failureStrain` records this first sampled crossing, not an interpolated exact event.

Quasistatic work is the trapezoidal integral ∫Qdq to that state. It includes stored recoverable energy as well as losses. Strength is the largest sampled reaction to the stop; initial stiffness is the first secant slope (not an infinitesimal modulus). Hysteresis is the full loading–unloading work, reported separately in six subfailure cyclic comparisons with rupture threshold raised to two. Released spring and hinge energy are separately recorded. Event jumps and finite step widths limit work integration accuracy.

For pulses, reaction oscillations are not a failure rule. The first 20%-volume loss or spanning-path loss defines the criterion. Transient trajectories continue to twice the pulse duration, so end-damage may exceed damage at the first criterion. Pulse **internalized work** at the criterion is U + irreversible rupture/sacrificial losses + damping loss. Kinetic energy is excluded. External work, final kinetic energy and the energy-balance residual are also saved. Clamp reaction includes the direct body force carried by constrained nodal masses; constrained nodes do no external work because their displacement is zero. This damping-dependent quantity is not automatically interchangeable with quasistatic toughness.

If a strain/time cap arrives first, `censored=true`: the file reports observed protocol work, not a complete work-to-failure measurement. In monotonic nonnegative-work tests it can be interpreted as a protocol-specific lower bound; no survival model is fitted. Free acceleration has essentially zero material work, even though external work and kinetic energy are nonzero.

Retained connectivity is the fraction of opposite-grip nodes reachable from any starting-grip node along intact collagen edges. It is a topological diagnostic, not a stiffness fraction. Force localization is Σ|f|²/(Σ|f|)², an edge-force IPR. All energies are per reference volume; no crack surface is identified, so no J/m² fracture energy, stress-intensity factor or fracture-toughness claim is made.

## Graph and mechanical predictors

We compute mean degree, population degree variance, z−4, cycle rank, maximum k-core index, exact global unit-capacity edge connectivity (minimum 0-to-v max flow over all v), normalized maximum edge betweenness, mean local clustering and modularity of the **prescribed four spatial quadrants**. Modularity is not optimized over community partitions. Geometric anisotropy is the eigenvalue difference of the volume-weighted 2D orientation tensor; `alignmentX` is its xx component. Mean segment length is also recorded.

Three Laplacians are distinct: L=D−A (unweighted combinatorial); Lw with weights (Aₑ/Lₑ)/mean(A/L); and D⁻¹ᐟ²LD⁻¹ᐟ² (normalized unweighted). λ₂ is algebraic connectivity (the gap above the connected zero mode). λ₃−λ₂ is separately recorded and must not be confused with that gap. No chemistry, bending, orientation or loading direction enters the unweighted graph spectrum.

The bulk Maxwell central-force counting value is z≈2d=4 in 2D (6 in 3D), not a universal rigidity threshold for these finite supported, bending-stabilized, geometrically special networks. Even a free generic 2D count has the finite-size correction z≥4−6/N, and counting is not sufficient for rigidity. We therefore also finite-difference the mechanical Hessian at rest with **X-tension supports**, diagonalize it with an original Jacobi solver, record its smallest eigenvalue, the count below 10⁻⁵, and the lowest-mode DOF IPR Σvᵢ⁴ for ||v||₂=1. The threshold is a diagnostic convention; mode localization uses DOFs rather than node amplitudes. These supported small-strain modes are reference descriptors, not current loaded modes or a validated vibrational spectrum. The same X-supported descriptor is used in Y/shear regressions, an additional transfer limitation.

## Statistical analysis and verification

450 runs: 280 topology (7 families × 5 seeds × 8 protocols), 24 independent edge-count, 42 composition, 6 cycles, 59 numerical/regularizer sensitivities, 27 pulse duration/density and 12 finite-size sensitivities. The same five seeds support paired descriptive comparisons. Means and sample SDs are not confidence intervals or evidence of universal rank order.

Spearman correlations use converged, uncensored topology runs only (35 X tension, 30 Y tension, 30 shear, 32 pulse). Constant predictors return null, not zero evidence. Ridge regression predicts log(work+10⁻¹²), with training-only standardization, fixed penalty 1 on slopes and no penalty on the intercept. Compare training seeds 17/29/43 with held-out 71/101, and separately leave out each whole family. The mean-only baseline is included. “Mechanical” includes the first loading secant stiffness, so it assumes an early mechanical test; it is not a graph-only prediction. No hyperparameter search or statistical significance claims are made.

Nine original checks verify equal budgets/connectedness, seeded reproducibility, analytic gradients, rigid-motion invariance, analytic path eigenvalues/min-cut, energy minimization, reaction/energy consistency, free-translation invariance and irreversible rupture. Sensitivities halve strain/time increments, tighten residual tolerance tenfold, vary the collapse regularizer twofold and change specimen size. The weakest near-floppy responses can be numerically unresolved despite satisfying the absolute force tolerance. See `REPORT.md` for the observed differences.

The principal limitations are 2D geometry, small samples, hand-selected graph generators, imposed common rupture laws, no contact/fluid physics, local rather than global minimization, family confounding, operational failure thresholds and imperfect event resolution. These results answer which descriptors worked **inside this tested model**, not which native collagen tissue is toughest in an extreme environment.
