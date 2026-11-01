# Small-strain stiffness interpretation and independent data audit

Original Python standard-library readback, 2026-10-31. This inspects saved JSON and solver source statically; no numerical solver was executed. The 40 states are 4 seeds × 2 planes × 5 conditions, comprising 8 baselines and 32 modified/baseline ratios. Calling these “40 stiffness ratios” would count the 8 trivial baseline ratios as additional effects.

All 40 states are marked accepted, with maximum residual 9.9637407e-09 model units (limit 1e-8 in stiffness.mjs). Stiffness is the shear stress at γ=0.001 divided by 0.001, a finite small-strain secant estimate, not an independently converged zero-strain derivative. Baseline normalization uses the same seed and plane, so the common bulk calibration scale cancels.

| Locked fraction | Pattern | Mean modified/baseline | Seed-mean range | All 8 direction ratios range |
|---|---|---:|---:|---:|
| 15% | clustered | 1.445585 | 1.305451–1.550362 | 1.269243–1.694548 |
| 15% | distributed | 1.479934 | 1.314136–1.641318 | 1.291905–1.720321 |
| 30% | clustered | 1.979444 | 1.771702–2.244080 | 1.684834–2.382881 |
| 30% | distributed | 2.270143 | 2.046995–2.627509 | 2.029484–2.783163 |

| Locked fraction | Mean paired C/D | Range of seed-mean C/D | Seed signs C−D (+ / −) | Direction signs (+ / −) |
|---|---:|---:|---:|---:|
| 15% | 0.988148 | 0.797481–1.179426 | 1 / 3 | 4 / 4 |
| 30% | 0.883184 | 0.760313–1.095780 | 1 / 3 | 2 / 6 |

These are mean paired ratios, not a ratio of pooled means. Four synthetic network seeds are the replicate units; planes are repeated directions. No biological confidence interval, organism difference or calibrated aging effect follows. Both placements stiffen every saved small-strain direction relative to its own unlocked baseline under the imposed 10× angular coefficient; the placement ranking is much less uniform at 15% than the overall locking effect. The table reports all signs rather than asserting a universal clustered/distributed order.

## What the matching controls establish

Direct comparison of all eight placement pairs and their unlocked baseline confirms bit-exact equality of initial positions, edge and angle inventories, active-edge masks, reference lengths, rest cosines, cell conventions, N and realized connectivity. No graph edge is added by the locking intervention. Existing-junction angular coefficients are multiplied; damage in a later experiment removes existing load-bearing edges and their incident angles. Thus “crosslink density” here means fraction of existing junctions selected for angular locking, not measured bond number or chemical concentration.

Selected-site counts and active-degree histograms match exactly for each placement pair. Total active-angle counts also match. The summed active angular coefficient agrees to floating-point roundoff: maximum absolute difference 1.2101431e-14. Therefore use “matched angular coefficient budget” or “equal within floating-point roundoff”, rather than literal bit equality of summed floating-point numbers. Equal coefficients do not mean equal deformation-dependent angular energy, force distribution or stiffness.

The two arms do not match local fiber directions, lengths, rest angles, node-to-boundary geometry, or overlap of selected regions with load-bearing pathways. These are consequences/confounders of the placement intervention and are documented in placement-geometry-diagnostics.json. No length/orientation-independent causal effect of clustering is identified. The fixed shared graph and cell control segment inventory/volume within a seed, but neither provides measured collagen concentration or validates a molecular crosslink-to-network map.

## Final-results integration

The stiffness table is complete independently of the still-incoming fracture grid. Do not transfer its convergence status to fracture trajectories. Use final accepted amplitude scales for Pa values, retain original G_dim and residuals, and separate finite-strain energy, step-refinement, censoring and selected-state stability gates. Broader fracture rankings require coverage at both planes for each reported seed, disclosure of how many of all four seeds qualify, and resolution-consistent damage contrasts when damage is the endpoint.
