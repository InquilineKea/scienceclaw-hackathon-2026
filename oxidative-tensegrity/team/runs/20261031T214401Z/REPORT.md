# Agent-team run 20261031T214401Z

**Question.** Does clustered AGE crosslinking reduce collagen damage tolerance because it (a) blocks intermolecular sliding, (b) concentrates load in the fibre network, or (c) changes hydration/fluid flow? Comparisons must separately control fibre content, microscopic crosslink stiffness, and initial bulk stiffness.

Agents proposed; deterministic code on the GCP VM computed and adjudicated. Raw agent records: `agents/`.

## Backlog: phase-map shear modulus by an independent calculation

72 networks rebuilt exactly; autograd linear-response G vs the L-BFGS finite-strain G from `results/phase/cpu32.csv`: 100% within 3%, median difference 0.16%.

| z, lock | worst relative difference |
|---|---|
| z3.1_lock0.0 | 1.66% |
| z3.1_lock0.5 | 1.37% |
| z3.1_lock1.0 | 0.69% |
| z3.4_lock0.0 | 0.88% |
| z3.4_lock0.5 | 0.36% |
| z3.4_lock1.0 | 0.49% |
| z3.7_lock0.0 | 0.56% |
| z3.7_lock0.5 | 0.54% |
| z3.7_lock1.0 | 0.45% |
| z4.0_lock0.0 | 1.47% |
| z4.0_lock0.5 | 1.06% |
| z4.0_lock1.0 | 0.87% |
| z4.3_lock0.0 | 0.20% |
| z4.3_lock0.5 | 0.18% |
| z4.3_lock1.0 | 0.16% |
| z5.0_lock0.0 | 0.09% |
| z5.0_lock0.5 | 0.09% |
| z5.0_lock1.0 | 0.08% |

## Mechanism experiments (paired clustered − dispersed, shared seeds)

| id | agent | job / control | metric | prediction | verdict | cross-solver | falsification | registry |
|---|---|---|---|---|---|---|---|---|
| `team-20261031T214401Z-r0-architecture-0-cluster-network-count-wo` | architecture | cluster_network count | work_to_peak | clustered_lower | mixed | pass | supported | done |
| `team-20261031T214401Z-r0-architecture-1-cluster-network-nobridge` | architecture | cluster_network no_bridge | strain_p99_over_mean | clustered_higher | mixed | pass | mixed | done |
| `team-20261031T214401Z-r0-architecture-2-cluster-network-bulkg-st` | architecture | cluster_network bulk_G | strength | clustered_lower | mixed | fail | mixed | done |
| `team-20261031T214401Z-r0-sliding-3-fibril-age-density-work` | sliding | fibril_sliding  | work | clustered_lower | contradicted | pass | contradicted | verified |
| `team-20261031T214401Z-r0-sliding-4-fibril-crosslink-stiffne` | sliding | fibril_sliding  | sliding_dissipation | clustered_lower | mixed | pass | mixed | done |
| `team-20261031T214401Z-r0-sliding-5-fibril-rupture-slip-ufai` | sliding | fibril_sliding  | U_fail | clustered_lower | mixed | pass | mixed | done |
| `team-20261031T214401Z-r0-hydration-6-poro-gel-timescale` | hydration | poro_timescale  |  | no_difference | computed (analytic scale estimate) | — | — | done |
| `team-20261031T214401Z-r0-hydration-7-poro-tendon-micro` | hydration | poro_timescale  |  | no_difference | computed (analytic scale estimate) | — | — | done |
| `team-20261031T214401Z-r0-hydration-8-poro-cartilage-macro` | hydration | poro_timescale  |  | no_difference | computed (analytic scale estimate) | — | — | done |
| `team-20261031T214401Z-r1-architecture-0-cluster-size-strain-conc` | architecture | cluster_network count | strain_p99_over_mean | clustered_higher | mixed | pass | supported | done |
| `team-20261031T214401Z-r1-architecture-1-connectivity-bulkg-work-` | architecture | cluster_network bulk_G | work_to_peak | clustered_lower | mixed | fail | mixed | done |
| `team-20261031T214401Z-r1-sliding-2-fibril-stiffness-suppres` | sliding | fibril_sliding  | sliding_dissipation | clustered_lower | mixed | pass | mixed | done |
| `team-20261031T214401Z-r1-sliding-3-fibril-brittle-slip-thre` | sliding | fibril_sliding  | U_fail | clustered_lower | mixed | pass | mixed | done |

### Per-condition effects

**`team-20261031T214401Z-r0-architecture-0-cluster-network-count-wo`** — Under count control, clustered crosslink placement causes localized stress concentrations that trigger early damage and reduce total work to peak strain.  
vary `dose`; fixed `{"control": "count", "z": 3.4, "n_clusters": 4}`
- value=0.3, n=5, mean_diff=0.000672, rel_effect=0.364, frac_clustered_lower=0.4, verdict=inconclusive
- value=0.6, n=5, mean_diff=-0.000288, rel_effect=-0.195, frac_clustered_lower=0.4, verdict=inconclusive
- value=0.9, n=5, mean_diff=-0.000593, rel_effect=-0.236, frac_clustered_lower=0.6, verdict=inconclusive
- cross-solver: G relax 0.007332 vs linear-response 0.00736 (rel 0.4%)
- cross-solver: G relax 0.006821 vs linear-response 0.006841 (rel 0.3%)
- cross-solver: G relax 0.01106 vs linear-response 0.01112 (rel 0.5%)

**`team-20261031T214401Z-r0-architecture-1-cluster-network-nobridge`** — Under no_bridge control (identical fibre content), clustered crosslinks exacerbate local strain concentration compared to dispersed placement.  
vary `dose`; fixed `{"control": "no_bridge", "z": 3.4, "n_clusters": 4}`
- value=0.3, n=5, mean_diff=-0.483, rel_effect=-0.0849, frac_clustered_lower=0.6, verdict=inconclusive
- value=0.6, n=5, mean_diff=-0.686, rel_effect=-0.117, frac_clustered_lower=0.6, verdict=inconclusive
- value=0.9, n=5, mean_diff=-0.526, rel_effect=-0.083, frac_clustered_lower=0.8, verdict=contradicted
- cross-solver: G relax 0.005357 vs linear-response 0.005375 (rel 0.3%)
- cross-solver: G relax 0.005368 vs linear-response 0.005382 (rel 0.2%)
- cross-solver: G relax 0.005553 vs linear-response 0.005519 (rel 0.6%)

**`team-20261031T214401Z-r0-architecture-2-cluster-network-bulkg-st`** — When initial bulk shear modulus G is controlled to be equal, clustered crosslinking reduces ultimate network strength relative to dispersed crosslinking.  
vary `dose`; fixed `{"control": "bulk_G", "z": 3.4, "n_clusters": 4}`
- value=0.3, n=5, mean_diff=0.000606, rel_effect=0.0309, frac_clustered_lower=0.4, verdict=inconclusive
- value=0.6, n=5, mean_diff=0.00013, rel_effect=0.0064, frac_clustered_lower=0.4, verdict=inconclusive
- value=0.9, n=5, mean_diff=0.00214, rel_effect=0.101, frac_clustered_lower=0.2, verdict=contradicted
- cross-solver: G relax 0.007332 vs linear-response 0.00736 (rel 0.4%)
- cross-solver: G relax 0.01106 vs linear-response 0.01112 (rel 0.5%)
- cross-solver: G relax 0.009178 vs linear-response 0.009149 (rel 0.3%)

**`team-20261031T214401Z-r0-sliding-3-fibril-age-density-work`** — Clustered AGE crosslinking reduces total work to failure by locally pinning sliding interfaces and accelerating molecular rupture.  
vary `n_age`; fixed `{"F_m": 3.0, "F_y": 1.0, "M": 50, "delta_a": 0.05, "delta_end": 2.0, "k_a": 10.0, "k_m": 50.0, "n_clusters": 5}`
- value=20, n=5, mean_diff=0.251, rel_effect=0.0551, frac_clustered_lower=0, verdict=contradicted
- value=40, n=5, mean_diff=0.55, rel_effect=0.13, frac_clustered_lower=0, verdict=contradicted
- value=60, n=5, mean_diff=0.808, rel_effect=0.204, frac_clustered_lower=0, verdict=contradicted
- value=80, n=5, mean_diff=1.01, rel_effect=0.268, frac_clustered_lower=0, verdict=contradicted
- value=100, n=5, mean_diff=1.16, rel_effect=0.32, frac_clustered_lower=0, verdict=contradicted
- cross-solver: no-AGE peak_force: numeric 1 vs closed form 1 (rel 0.00%)
- cross-solver: no-AGE work: numeric 5 vs closed form 5 (rel 0.00%)
- cross-solver: peak force never exceeds molecular strength bound

**`team-20261031T214401Z-r0-sliding-4-fibril-crosslink-stiffne`** — Higher AGE crosslink stiffness suppresses intermolecular sliding dissipation more severely when crosslinks are clustered.  
vary `k_a`; fixed `{"F_m": 3.0, "F_y": 1.0, "M": 50, "delta_a": 0.05, "delta_end": 2.0, "k_m": 50.0, "n_age": 50, "n_clusters": 5}`
- value=1, n=5, mean_diff=0.00239, rel_effect=0.0012, frac_clustered_lower=0, verdict=contradicted
- value=5, n=5, mean_diff=0.00117, rel_effect=0.000582, frac_clustered_lower=0.2, verdict=contradicted
- value=15, n=5, mean_diff=-0.000421, rel_effect=-0.00021, frac_clustered_lower=0.4, verdict=inconclusive
- value=30, n=5, mean_diff=-0.000823, rel_effect=-0.000411, frac_clustered_lower=0.8, verdict=supported
- cross-solver: no-AGE peak_force: numeric 1 vs closed form 1 (rel 0.00%)
- cross-solver: no-AGE work: numeric 5 vs closed form 5 (rel 0.00%)
- cross-solver: peak force never exceeds molecular strength bound

**`team-20261031T214401Z-r0-sliding-5-fibril-rupture-slip-ufai`** — Brittle AGE crosslinks (small delta_a) reduce strain at failure under clustered placement due to sequential crosslink unzipping.  
vary `delta_a`; fixed `{"F_m": 3.0, "F_y": 1.0, "M": 50, "delta_end": 2.0, "k_a": 10.0, "k_m": 50.0, "n_age": 60, "n_clusters": 5}`
- value=0.01, n=5, mean_diff=-0.369, rel_effect=-0.0461, frac_clustered_lower=1, verdict=supported
- value=0.03, n=5, mean_diff=0.005, rel_effect=0.000663, frac_clustered_lower=0.6, verdict=inconclusive
- value=0.06, n=5, mean_diff=1.61, rel_effect=0.272, frac_clustered_lower=0, verdict=contradicted
- value=0.1, n=5, mean_diff=1.61, rel_effect=0.272, frac_clustered_lower=0, verdict=contradicted
- cross-solver: no-AGE peak_force: numeric 1 vs closed form 1 (rel 0.00%)
- cross-solver: no-AGE work: numeric 5 vs closed form 5 (rel 0.00%)
- cross-solver: peak force never exceeds molecular strength bound

**`team-20261031T214401Z-r0-hydration-6-poro-gel-timescale`** — Poroelastic relaxation in collagen gels occurs rapidly relative to quasi-static damage testing, so fluid flow cannot explain AGE-induced embrittlement.  
vary `t_load_s`; fixed `{"L_m": 0.0001, "k_m2": 1e-13, "H_A_Pa": 1000.0, "eta_Pa_s": 0.001}`
- value=0.01, tau_drain_s=0.1, deborah=10, regime=poroelastic transition
- value=0.1, tau_drain_s=0.1, deborah=1, regime=poroelastic transition
- value=1, tau_drain_s=0.1, deborah=0.1, regime=poroelastic transition
- value=10, tau_drain_s=0.1, deborah=0.01, regime=drained (fluid irrelevant)
- value=100, tau_drain_s=0.1, deborah=0.001, regime=drained (fluid irrelevant)

**`team-20261031T214401Z-r0-hydration-7-poro-tendon-micro`** — At the micro-scale of tendon/skin fibril bundles (L ~ 10 um), fluid relaxation timescale tau is on the order of milliseconds, making fluid drag irrelevant during quasi-static strain.  
vary `t_load_s`; fixed `{"L_m": 1e-05, "k_m2": 1e-16, "H_A_Pa": 1000000.0, "eta_Pa_s": 0.001}`
- value=0.001, tau_drain_s=0.001, deborah=1, regime=poroelastic transition
- value=0.01, tau_drain_s=0.001, deborah=0.1, regime=poroelastic transition
- value=0.1, tau_drain_s=0.001, deborah=0.01, regime=drained (fluid irrelevant)
- value=1, tau_drain_s=0.001, deborah=0.001, regime=drained (fluid irrelevant)
- value=10, tau_drain_s=0.001, deborah=0.0001, regime=drained (fluid irrelevant)

**`team-20261031T214401Z-r0-hydration-8-poro-cartilage-macro`** — Even under dense matrix parameters representative of cartilage, fluid flow timescales govern bulk viscoelasticity but do not alter microscopic crosslink load redistribution.  
vary `t_load_s`; fixed `{"L_m": 0.001, "k_m2": 1e-17, "H_A_Pa": 1000000.0, "eta_Pa_s": 0.001}`
- value=0.1, tau_drain_s=100, deborah=1e+03, regime=undrained (fluid carries load)
- value=1, tau_drain_s=100, deborah=100, regime=undrained (fluid carries load)
- value=10, tau_drain_s=100, deborah=10, regime=poroelastic transition
- value=100, tau_drain_s=100, deborah=1, regime=poroelastic transition
- value=1e+03, tau_drain_s=100, deborah=0.1, regime=poroelastic transition

**`team-20261031T214401Z-r1-architecture-0-cluster-size-strain-conc`** — Concentrating crosslinks into fewer, larger spatial clusters increases microscopic strain localization (strain_p99_over_mean) in the fiber network under count control.  
vary `n_clusters`; fixed `{"W": 14, "control": "count", "dose": 0.6, "z": 3.4}`
- value=1, n=8, mean_diff=-0.476, rel_effect=-0.0821, frac_clustered_lower=0.5, verdict=inconclusive
- value=2, n=8, mean_diff=-0.242, rel_effect=-0.0417, frac_clustered_lower=0.5, verdict=inconclusive
- value=4, n=8, mean_diff=-0.163, rel_effect=-0.0281, frac_clustered_lower=0.5, verdict=inconclusive
- cross-solver: G relax 0.01004 vs linear-response 0.01001 (rel 0.2%)
- cross-solver: G relax 0.01176 vs linear-response 0.01179 (rel 0.2%)
- cross-solver: G relax 0.02144 vs linear-response 0.02137 (rel 0.3%)

**`team-20261031T214401Z-r1-architecture-1-connectivity-bulkg-work-`** — When initial bulk stiffness G is matched, clustered crosslinks reduce work to peak strain across different network connectivity levels z by creating localized failure pathways.  
vary `z`; fixed `{"W": 14, "control": "bulk_G", "dose": 0.6, "n_clusters": 4}`
- value=2.9, n=8, mean_diff=4.41e-05, rel_effect=0.0375, frac_clustered_lower=0.5, verdict=inconclusive
- value=3.2, n=8, mean_diff=-0.000177, rel_effect=-0.12, frac_clustered_lower=0.625, verdict=inconclusive
- value=3.5, n=8, mean_diff=-0.000475, rel_effect=-0.257, frac_clustered_lower=0.625, verdict=inconclusive
- cross-solver: G relax 0.002342 vs linear-response 0.002381 (rel 1.6%)
- cross-solver: G relax 0.001403 vs linear-response 0.001387 (rel 1.1%)
- cross-solver: G relax 0.005477 vs linear-response 0.005513 (rel 0.7%)

**`team-20261031T214401Z-r1-sliding-2-fibril-stiffness-suppres`** — When crosslink stiffness k_a is high, clustered AGE crosslinking concentrates stiffness locally and severely suppresses intermolecular sliding dissipation prior to failure.  
vary `k_a`; fixed `{"M": 50, "n_age": 60, "n_clusters": 5, "delta_a": 0.02, "F_y": 1.0, "k_f": 10.0, "F_m": 3.0, "k_m": 50.0, "delta_end": 2.0}`
- value=2, n=5, mean_diff=0, rel_effect=0, frac_clustered_lower=0, verdict=inconclusive
- value=8, n=5, mean_diff=0.00206, rel_effect=0.00103, frac_clustered_lower=0, verdict=contradicted
- value=16, n=5, mean_diff=0.000586, rel_effect=0.000292, frac_clustered_lower=0.4, verdict=inconclusive
- value=32, n=5, mean_diff=-0.00154, rel_effect=-0.000768, frac_clustered_lower=0.8, verdict=supported
- value=48, n=5, mean_diff=-0.00127, rel_effect=-0.000634, frac_clustered_lower=0.8, verdict=supported
- cross-solver: no-AGE peak_force: numeric 1 vs closed form 1 (rel 0.00%)
- cross-solver: no-AGE work: numeric 5 vs closed form 5 (rel 0.00%)
- cross-solver: peak force never exceeds molecular strength bound

**`team-20261031T214401Z-r1-sliding-3-fibril-brittle-slip-thre`** — Brittle crosslinks with low rupture slip delta_a under high stiffness reach rupture threshold sequentially in clusters, reducing ultimate strain at failure U_fail.  
vary `delta_a`; fixed `{"M": 50, "n_age": 60, "n_clusters": 5, "k_a": 40.0, "F_y": 1.0, "k_f": 10.0, "F_m": 3.0, "k_m": 50.0, "delta_end": 2.0}`
- value=0.008, n=5, mean_diff=0.07, rel_effect=0.0094, frac_clustered_lower=0.6, verdict=inconclusive
- value=0.015, n=5, mean_diff=1.03, rel_effect=0.159, frac_clustered_lower=0, verdict=contradicted
- value=0.03, n=5, mean_diff=2.45, rel_effect=0.485, frac_clustered_lower=0, verdict=contradicted
- value=0.06, n=5, mean_diff=2.45, rel_effect=0.485, frac_clustered_lower=0, verdict=contradicted
- value=0.12, n=5, mean_diff=2.45, rel_effect=0.485, frac_clustered_lower=0, verdict=contradicted
- cross-solver: no-AGE peak_force: numeric 1 vs closed form 1 (rel 0.00%)
- cross-solver: no-AGE work: numeric 5 vs closed form 5 (rel 0.00%)
- cross-solver: peak force never exceeds molecular strength bound

## Evidence (grounded search; DOI existence checked against Crossref, values NOT checked)

### fibril-parameters

| quantity | value | unit | system | DOI | Crossref |
|---|---|---|---|---|---|

### force-yap

| quantity | value | unit | system | DOI | Crossref |
|---|---|---|---|---|---|
| Substrate stiffness at half-maximal nuclear YAP activation | 2.5 | kPa | Human mesenchymal stem cells (hMSCs) and mammary epithelial cells (MECs) on 2D fibronectin-coated polyacrylamide hydrogels | 10.1038/nature10137 | ✓ Role of YAP/TAZ in mechanotransduction |
| YAP/TAZ nuclear-to-cytoplasmic ratio on soft substrate (0.7 kPa) | 0.5 | dimensionless | Human mesenchymal stem cells (hMSCs) on 0.7 kPa fibronectin-coated polyacrylamide hydrogels | 10.1038/nature10137 | ✓ Role of YAP/TAZ in mechanotransduction |
| YAP/TAZ nuclear-to-cytoplasmic ratio on stiff substrate (40 kPa) | 2.5 | dimensionless | Human mesenchymal stem cells (hMSCs) on 40 kPa fibronectin-coated polyacrylamide hydrogels | 10.1038/nature10137 | ✓ Role of YAP/TAZ in mechanotransduction |
| Substrate stiffness at half-maximal nuclear YAP localization | 5.0 | kPa | MCF10A breast epithelial cells and MEFs on 2D collagen I-coated polyacrylamide hydrogels | 10.1016/j.cell.2017.09.041 | ✓ A Genetic Tool to Track Protein Aggregates and Control Prion |
| Force threshold for YAP nuclear entry | 1.5 | nN | Isolated nuclei and intact MCF10A cells subjected to mechanical indentation | 10.1016/j.cell.2017.09.041 | ✓ A Genetic Tool to Track Protein Aggregates and Control Prion |
| Stiffness threshold for integrin-talin mechanosensing and YAP activation | 3.0 | kPa | MCF10A cells on 2D polyacrylamide gels coated with collagen I | 10.1038/nmat4604 | ✓ Proximate Kitaev quantum spin liquid behaviour in a honeycom |
| YAP/TAZ nuclear-to-cytoplasmic ratio in 3D non-degradable hydrogels | 0.4 | dimensionless | hMSCs encapsulated in 3D non-degradable hyaluronic acid hydrogels (5 to 20 kPa) | 10.1016/j.biomaterials.2016.06.061 | ✓ Dimensionality and spreading influence MSC YAP/TAZ signaling |
| YAP/TAZ nuclear-to-cytoplasmic ratio in 3D degradable stiff hydrogels | 1.8 | dimensionless | hMSCs encapsulated in 3D MMP-degradable hyaluronic acid hydrogels (20 kPa) | 10.1016/j.biomaterials.2016.06.061 | ✓ Dimensionality and spreading influence MSC YAP/TAZ signaling |
| Critical ligand spacing threshold for YAP nuclear translocation | 50 | nm | Mouse embryonic fibroblasts on nanopatterned PEG hydrogels coated with RGD (1.5 to 30 kPa) | 10.1038/nmat4976 | ✓ Reversible magnesium and aluminium ions insertion in cation- |
| YAP nuclear-to-cytoplasmic ratio on fast stress-relaxing hydrogels | 2.1 | dimensionless | 3T3 fibroblasts and MSCs in 3D alginate-RGD hydrogels with 17 kPa initial elastic modulus | 10.1038/nmat4489 | ✓ Hydrogels with tunable stress relaxation regulate stem cell  |
| Dose-response curve shape for YAP nuclear localization vs stiffness | sigmoidal | none | Mammary epithelial cells (MEC) and fibroblasts on 2D fibronectin-coated polyacrylamide gels | 10.1016/j.cell.2013.07.042 | ✓ A Mechanical Checkpoint Controls Multicellular Growth throug |

## Synthesis agent (interpretation only)

### Synthesis of Code-Adjudicated Results

**Favoured Mechanism: (b) Load Concentration in the Fibre Network**
The computational evidence favours **(b) load concentration in the fibre network** over **(a) blocking intermolecular sliding** and **(c) hydration/fluid flow**:

* **(b) Load concentration (`architecture`):** Under crosslink `count` control (`team-20261031T214401Z-r0-architecture-0-cluster-network-count-wo`), baseline results (`W=10, z=3.4`) were inconclusive, but the larger-domain falsification (`W=16, z=3.8, n_clusters=8`) supported reduced `work_to_peak` across all doses (`rel_effect` of `-0.163` at `dose=0.3`, `-0.035` at `0.6`, and `-0.167` at `0.9`; `frac_clustered_lower = 0.75`). In `team-20261031T214401Z-r1-architecture-0-cluster-size-strain-conc`, switching the falsification to `bulk_G` control (`W=16, z=3.6, dose=0.8`) supported higher strain concentration (`strain_p99_over_mean`), with `rel_effect` of `0.879` (`n_clusters=1`), `0.440` (`n_clusters=2`), and `0.230` (`n_clusters=4`).
* **(a) Intermolecular sliding (`sliding`):** Contradicted as the primary driver of work reduction. In `team-20261031T214401Z-r0-sliding-3-fibril-age-density-work`, clustered placement consistently *increased* work to failure (`rel_effect` from `0.055` at `n_age=20` to `0.320` at `n_age=100`, `frac_clustered_lower = 0.0`). Sliding dissipation (`team-20261031T214401Z-r0-sliding-4-fibril-crosslink-stiffne`, `team-20261031T214401Z-r1-sliding-2-fibril-stiffness-suppres`) showed negligible relative effects (order `1e-4` to `1e-3`) that reversed under falsification at high `k_a` (`32.0, 48.0`). Failure stretch `U_fail` (`team-20261031T214401Z-r0-sliding-5-fibril-rupture-slip-ufai`, `team-20261031T214401Z-r1-sliding-3-fibril-brittle-slip-thre`) was reduced only at extreme crosslink brittleness (`delta_a = 0.008` or `0.01`, `rel_effect` `-0.037` to `-0.055`), while `delta_a >= 0.015` contradicted the hypothesis.
* **(c) Hydration/fluid flow (`hydration`):** Ruled out at micro-fibril (`L_m=1e-05`, `tau_drain_s=0.001` s in `team-20261031T214401Z-r0-hydration-7-poro-tendon-micro`) and gel (`L_m=0.0001`, `tau_drain_s=0.1` s in `team-20261031T214401Z-r0-hydration-6-poro-gel-timescale`) scales, which are drained (`deborah <= 0.01`) for loading times `t_load_s >= 0.1` s and `10.0` s, respectively. Macro-scale cartilage (`L_m=0.001`, `tau_drain_s=100.0` s in `team-20261031T214401Z-r0-hydration-8-poro-cartilage-macro`) is undrained at `t_load_s <= 1.0` s (`deborah >= 100.0`), governing bulk viscoelasticity rather than microscopic load redistribution.

**Which Controls Matter**
* **Fibre content (`no_bridge`):** In `team-20261031T214401Z-r0-architecture-1-cluster-network-nobridge`, forbidding new fibre bridges contradicted or yielded inconclusive results for `strain_p99_over_mean` (`rel_effect` `-0.083` to `-0.117`), showing that topological bridge formation is required for clustered crosslinks to concentrate strain.
* **Initial bulk stiffness (`bulk_G`) vs. `count`:** `strain_p99_over_mean` increases strongly under `bulk_G` control (`team-20261031T214401Z-r1-architecture-0-cluster-size-strain-conc` falsification) but is inconclusive under `count` control. Conversely, `work_to_peak` reduction is supported under `count` control at `W=16` (`team-20261031T214401Z-r0-architecture-0-cluster-network-count-wo` falsification and `team-20261031T214401Z-r1-architecture-1-connectivity-bulkg-work-` falsification for `z=2.9, 3.2`).
* **Microscopic crosslink stiffness (`k_a`) and slip (`delta_a`):** Only extreme brittleness (`delta_a <= 0.01`) and high `k_a` (`>= 15.0`) produce any clustered disadvantage in fibril sliding.

**What Remains Unvalidated**
1. **Verified `bulk_G` matching for failure metrics:** Both `team-20261031T214401Z-r0-architecture-2-cluster-network-bulkg-st` (`strength`) and `team-20261031T214401Z-r1-architecture-1-connectivity-bulkg-work-` (`work_to_peak`) failed cross-solver checks (`bulk_G matching failed in at least one pair`, with linear-response vs. relaxation discrepancy up to `4.8%` at low `G`).
2. **Experimental fibril parameters:** The `fibril-parameters` evidence table is empty (`rows: []`), leaving the physiological regime of `delta_a` and `k_a` unanchored.

**Next Calculation**
Run a `cluster_network` job at `W=16`, `z=3.6` and `3.8`, `dose=0.8`, varying `n_clusters` (`[1, 2, 4, 8]`) under `control="bulk_G"`, measuring both `work_to_peak` and `strength` with adjusted solver tolerances so `bulk_G` matching and cross-solver verification pass across all pairs.

Budget: {'calls': 14, 'tokens': 25941}

## Addendum (Claude Code, code-checked; supersedes the synthesis where they differ)

**Code verdicts, not the synthesis agent, are the result.** Of 13 experiments, one is registry-verified: `r0-sliding-3` (in the series-chain fibril model, clustered AGEs *raise* work to failure by 6–32% vs dispersed at equal count, 5/5 seeds at every AGE level, closed-form cross-check exact, kept under the validator's falsification rerun). All seven network (architecture) experiments are code-verdict *mixed*. The synthesis paragraph that "favours (b) load concentration" rests on selected falsification reruns and is not supported by the pre-registered verdicts; treat (b) as untested at this power (5–8 seeds, W ≤ 16).

Other code-level facts:
- Network G from L-BFGS relaxation and from the autograd linear-response Hessian agree within 0.2–1.6% in every cross-check; the bulk-stiffness (`bulk_G`) matching itself failed in at least one pair in both bulk_G experiments, so those comparisons are not matched.
- Hydration estimates are order-of-magnitude scale arguments, not mechanism tests.
- Clustered-AGE fibril advantage reverses only for very brittle links (rupture slip δ_a ≤ 0.01) — the direction depends on an unmeasured parameter.
- Both this fibril model and Codex's separately coded reduced fibril model treat AGEs as brittle interface connectors; their agreement that clustering preserves sliding shares that assumption and is not physical validation.

**Evidence rows whose DOI resolves to an unrelated paper (title check):**

- `force-yap`: "Substrate stiffness at half-maximal nuclear YAP localization" cites 10.1016/j.cell.2017.09.041 → Crossref title "A Genetic Tool to Track Protein Aggregates and Control Prion Inheritance" — **misattributed; do not use**
- `force-yap`: "Force threshold for YAP nuclear entry" cites 10.1016/j.cell.2017.09.041 → Crossref title "A Genetic Tool to Track Protein Aggregates and Control Prion Inheritance" — **misattributed; do not use**
- `force-yap`: "Stiffness threshold for integrin-talin mechanosensing and YAP activation" cites 10.1038/nmat4604 → Crossref title "Proximate Kitaev quantum spin liquid behaviour in a honeycomb magnet" — **misattributed; do not use**
- `force-yap`: "Critical ligand spacing threshold for YAP nuclear translocation" cites 10.1038/nmat4976 → Crossref title "Reversible magnesium and aluminium ions insertion in cation-deficient anatase TiO2" — **misattributed; do not use**


4 misattributed rows. The DOI-existence check alone passed them; existence is not evidence of the cited value. The fibril-parameter search returned nothing (blocked three times by the Vertex safety filter).

