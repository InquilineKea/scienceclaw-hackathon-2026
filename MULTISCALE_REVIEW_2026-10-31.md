# Multiscale-physics review of the Science/ runs — 2026-10-31

Claude Code, four parallel read-only reviewers plus spot-checks of the key code claims. Nothing was run or
modified. Question: did the runs neglect physics at other scales badly enough to sink their conclusions, and
would MD (GPU LAMMPS / OpenMM), FEniCSx or a coarse-grained fibril model fix it?

## Short answer

Missing molecular physics is rarely what sinks these results. Three recurring problems matter more:

1. **Wrong rigidity regime.** Most collagen networks here sit above the 2D isostatic point
   (atlas z ≈ 4.56, FEniCSx job z ≈ 4.6–5.9, junction-angle lattice z = 6). Native collagen is at z ≈ 3.4:
   bending-dominated, with the most seed-to-seed scatter (phase map: G CV 0.5–0.8 at W=16, z 3.0–3.9).
   In 3D that is 2.6 below isostatic, so 2D rankings near z ≈ 4 can reorder. Fix: re-run at z ≈ 3.4 with
   periodic boundaries and ≥ 500 nodes. **CPU only, no MD.**
2. **Assumed bridges presented as mechanisms.** The `k_rel` crosslink table (`oxidative-tensegrity/oxt/materials.py:21-30`)
   is placeholders, and `results/crosslink_params.json` was never produced. The force→YAP→gene signs come from
   the curvature of the assumed Hill curves. No simulation fixes that; it needs a measured force→YAP curve.
3. **Ageing modelled as extra springs.** AGEs act inside fibrils by suppressing molecular sliding. Adding
   node-to-node springs makes stiffening automatic and can flip the sign of toughness effects. **This is the one
   place GPU LAMMPS earns its keep**: a coarse-grained fibril pulled to failure vs crosslink density, which then
   replaces the brittle fibre law.

A single crosslink's stiffness (1–25 N/m) is about 1000× stiffer than a 300-nm molecule (~0.015 N/m). Because
the two act in series, crosslink chemistry barely changes network stiffness; crosslink density and sliding
resistance do. So **single-crosslink MD (MACE, PM7, the dityrosine campaign) cannot calibrate the network.**

## Verdicts

| Project / run | Verdict | Main reason |
|---|---|---|
| collagen-network-atlas: AGE "distributed connectors raise work ×1.4–1.7" | at risk (sign) | AGEs as extra springs; no fibril sliding |
| atlas: AGE stiffness rise | built in | springs at zero rest strain can only stiffen |
| atlas: fibre-direction toughness rank | at risk (rank) | brittle 0.24 rupture, N=36, clamped edge, ~1 SD apart |
| atlas: pulse / pressure / finite-frequency microrheology | not physically meaningful (already caveated) | drag stands in for fluid |
| atlas: "no universal toughest topology", controls | safe | |
| collagen-fenicsx-poroelastic (`job/coupled.py`) | formulation needs fixing before use | friction counted twice (`K+iωI` drag plus Darcy, line 107); storage S=0.1, nearly incompressible should be ~0; refinement runs the unstable direction; no scale separation |
| collagen-scaffold-lab | rank probably OK, magnitudes not | affine upper bound; BCC 3–10× too stiff; struts buckle at 3–5% |
| collagen-species-pilot | safe | makes no mechanical claim |
| junction-angle 2D (H100) | at risk for biology | z=6 lattice; sign already flipped once |
| junction-angle controlled → YAP/genes | mechanics OK (6–7/8 seeds); gene direction at risk | Hill-curve operating point near its inflection point |
| junction-angle 3D shear | safe qualitatively | ~210 nodes; onset values only a caveat |
| junction-angle 3D cavity | at risk | free shell between cavity (r<0.32) and clamp (<0.12 / >0.88) is thinner than one edge |
| dityrosine-transfer | not run; can't calibrate the network as designed | intramolecular i→i+2 link, vacuum, ±3% |
| ALCHEMI crosslink scans | caveat; never fed into network | MACE models disagree up to 5.6×; mostly conformer slack |
| ALCHEMI collagen–GAG | sign at risk | vacuum contact energies; solvent may unbind |
| topo (Pareto front) | at risk (rank) | 2D, W=12, 2 realisations, z 3.2–3.8 |
| bioelectric | at risk | depolarisation built in; 4×4 cell patches vs correlation length |
| setpoint_vs_scar | safe as a statement about the model | |
| synconetics `model.py` sensitivity grid | **bug** | `model.py:156` calls `simulate(p)` without `policy`, so "gated" rows equal "fixed"; RESULTS.md's matched-duration claim is false |
| synconetics rafts "order reduces delivery" | at risk (sign) | flips with assumed order penalty |
| synconetics biochemistry ranking | at risk (rank) | no lipid-peroxidation autocatalysis; MD won't help |
| quotient-swarm, flywheel | multiscale physics not relevant | evaluation-design risks only |

The phase map in `oxidative-tensegrity/README.md` shares one of these limits: its AGE series uses the same
assumed `materials.py` parameters, so the AGE shifts are model statements, not calibrated ones. Its
connectivity, LOX-locking and finite-size results don't depend on `k_rel`.

## What to run, in priority order

| # | Calculation | Tool | Cost | Decides |
|---|---|---|---|---|
| 1 | Re-run atlas / FEniCSx-job / topo designs at z ≈ 3.4, periodic, 500–5000 nodes, ≥ 6 seeds | existing `oxt` / JS code, CPU | 2–300 CPU-h | rigidity-regime ranks (most claims above) |
| 2 | Fix synconetics `simulate(p, policy=policy)`; re-run grid | CPU | minutes | the policy comparison |
| 3 | Coarse-grained fibril (Depalle/Kamml bead model), 5–6 crosslink densities × 3 replicas × 2 rates, to failure | LAMMPS-GPU (NGC) or LAMMPS CPU | 20–150 H100-h (or 20–40 h on 32 vCPU) | AGE toughness sign; replaces brittle fibre law |
| 4 | 3D cavity rerun: 500–2000 seed points, cavity ≥ 3 edges, clamp ≥ 4R, 5/15/40% contraction, buckling springs; sparse solver | GPU or CPU | 1–10 H100-h | cavity force-spread claim |
| 5 | Consistent Biot / Brinkman poroelastic block: one friction Γ = η/k, S≈0, Taylor–Hood P2–P1 | FEniCSx | <1 CPU-h 2D, 10–50 3D | pulse / microrheology frequency claims |
| 6 | Collagen–GAG explicit-solvent PMFs, 4 pairs × 20 windows × 10 ns | OpenMM | ~40 H100-h | GAG binding sign |
| 7 | Sliding PMF ± one glucosepane (only if #3 shows the sliding barrier is sensitive) | OpenMM all-atom | 150–500 H100-h | feeds #3 |

MD would **not** help: single-crosslink stiffness, force→YAP calibration, topology ranks, species ranking from
sequence, synconetics biochemistry. Poroelasticity is also unnecessary for organoid growth: drainage time is
~0.1 s for 100 µm, against hours of growth.

## Done well (don't redo)

Frozen protocols with predeclared gates; failed cases kept; paired seeds; CPU/GPU and finite-difference
cross-checks; dt-halving; SHA-256 manifests; null calibration contract in the species pilot; sign reversals
reported rather than tuned away; ALCHEMI values deliberately not fed into the network.
