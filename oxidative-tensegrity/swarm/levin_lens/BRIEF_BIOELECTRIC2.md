# Brief: bioelectric ageing test, rerun after critique (2026-10-31)

This is the second run of the in-silico experiment described in the first brief, which is summarised here. Collagen
fibre networks give per-cell local stiffness maps. A motor-clutch/tensegrity cell turns each into traction and
prestress. These drive a bistable, gap-junction-coupled Vmem sheet. The sheet is compared with the senescent-
keratinocyte bioelectric signature (Sediqi & Levin 2025, iScience; cultures without ECM):
- depolarisation;
- within-dish SD −38%;
- between-dish SD ×15–22;
- global Moran's I 0.5 → 0.13–0.26.

## What the first run found, after source checks

- **Depolarisation:** built in through the stretch-activated current. It reverses on the stiffest networks because
  motor-clutch traction peaks and then falls.
- **Clustering:** Vmem Moran's I rose with crosslinking, the opposite direction to the data. With bootstrap
  intervals it was significantly up in 42 of 108 contrast × parameter sets and never significantly down. No set
  matched all four signs.
- **Spatial structure:** the actual stiffness map gave more Vmem clustering than the shuffled map (95% of
  comparisons). Correlated stiff patches nucleated switching near the single-cell saddle node, which sits at
  traction ≈ 1.19 × F50.
- **Pattern memory:** it existed only where prestress-gated junctions were nearly uncoupled on soft matrix. Net
  restoration after flips (restore minus the flipped baseline) was about zero in every field.
- **Weaknesses the reviewers raised:** prestress-gated junctions are the opposite of reported senescence uncoupling;
  seeds were paired across conditions; 8 seeds is low power; with no noise there are no information measures.

## What changed in this rerun (profile `gpu2`)

- Unique seeds for every network and 32 seeds per condition. Isotropic crosslinks only.
  **Bootstrap 95% intervals** over networks for every contrast, in `bootstrap_contrasts.csv`.
- A third junction mode, `stress_uncouple`: h = hill(PS; 0.5) × (1 − hill(F; F_unc = 400 pN, 4)). Prestress
  stabilises junctions; high traction closes them (a proxy for stress/Ca²⁺-driven connexin closure).
- Two flip fractions (0.10, 0.25), with net restoration reported (`net_heal_10`, `net_heal_25`).
- **Information measures:** a noisy stationary run (σ = 2 mV/√time, 200 time units, sampled every 0.25) gives
  Gaussian active information storage (AIS) and neighbour transfer entropy (TE), in nats. It also gives the
  across-cell Gaussian mutual information between local log stiffness and time-mean Vmem (MI_EV).
  Pio-Lopez, Hartl & Levin 2025 (Adv Sci) report AIS and TE rising with age in their model.

Unchanged: the 27-point sweep (G0 {0.25, 1, 4} × F50 {300, 400, 500} pN × three junction modes), the three field
controls (actual, shuffled, uniform), 64×64 networks and 16×16 cells.

You are AI reviewers. Those applying Levin's ideas must not speak for him or imply his endorsement. Check every
number you quote against the attached tables.
