# Revised collagen transition simulations: actual scope

The implemented suite is separate from the frozen original atlas. The convergence-focused v4 job uses the small commissioning profile. Larger profiles exist in source, but this does not mean those larger grids were completed.

| Mechanism | Actual v4 controls | Saved observables | Boundary |
|---|---|---|---|
| Strain-driven rigidity | W=6; seed 17; z=3, 3.6, 4.2; bending 10^-4; 9 shear strains 0–0.8 | Stress, tangent modulus, incremental nonaffinity, realized graph statistics, residuals | Finite crossovers; no critical-exponent or ensemble estimate |
| Sliding versus locking | Three locking levels 0, 0.5, 1 on the same graph and initial spring constants | 25 load–hold–unload samples per level; dissipation; residual strain | Mobility law is hypothetical, not an AGE dose |
| Sliding and rupture | Three locking levels; common 20% elastic bond-strain threshold | 18 tensile samples per level; damage and avalanche checks | Prescribed rupture law; no chemical reaction |
| Stiff-bond placement | Seven fractions, random or clustered, twentyfold stiffness | Three small-shear states per case | Original graph unchanged; no demonstrated percolation threshold |
| Damage placement | Random and adaptive high-tension cuts | 14 states per path through 65% bond removal | Fixed lateral confinement and 0.12 tensile strain |
| Inclusion contacts | Disk area fractions 0, 0.4, 0.75 | Ten compression states per case, to 0.45 strain | 2D area fraction, initial contact/prestress possible |
| Plastic memory | Two amplitudes, two hold times, two locking levels | Eight 18-state histories; residual-strain interpolation | No junction rebinding or fibre merging |
| LOX feedback | 969 coupling/gain pairs and 202 dynamic states | Equilibria, stability, hysteresis | A new hypothetical three-stage ODE; not a fitted H5 extension |
| Helix–coil sensitivity | 18 combinations and 117 temperatures | Exact finite 81-site folded fraction | No atomistic MD, Celsius mapping or species prediction |

There are 36 mechanical cases with 400 recorded states. Internal optimizer iterates and intermediate plastic-hold substeps are not stored as trajectories. Per-state force and energy tests determine convergence; a process completing is not a substitute for those tests.

The first submitted job failed before its numerical data could be exported. The second recovered all seven mechanical suites but failed at feedback serialization and had only 82/400 converged states, with no fully converged recorded path. v4 adds a gauge-fixed damped-Newton refinement for small networks without loosening acceptance tolerances. The final audit and outcome files determine whether that repair succeeded.

A completed raw archive includes all recorded states, including invalid ones, and all available attempt logs. Missing first-attempt data are explicitly documented, never regenerated and presented as original.
