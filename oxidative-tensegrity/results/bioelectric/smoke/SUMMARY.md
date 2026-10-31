# Bioelectric ageing test (16x16 networks, 4x4 cells, 2 seeds)

Keratinocyte senescence (Sediqi & Levin 2025, day 10 -> 40/50 in culture, no ECM): depolarised; within-dish variability -38% (ratio ~0.62); between-dish SD x15-22; Moran's I 0.5 -> 0.13-0.26.

S_pa = 14416.3 Pa per lattice unit (young skin dermis E = 2 kPa). Timings (s): {"network": 324, "cell": 13, "vmem": 1}

Default parameters (G0=1, F50=400 pN, prestress-gated junctions), all three field controls:

| contrast | field | E_ratio | dV_mean_mV | sd_within_ratio | sd_between_ratio | moranV_young | moranV_old | q_hold_young | q_hold_old | q_restore_young | q_restore_old |
|---|---|---|---|---|---|---|---|---|---|---|---|
| skin 20.0->80.0 y | actual | 1.3 | 0.634 | 1.84 | 17.3 | 0.0358 | 0.184 | 0 | 0 | 0 | 0 |
| skin 20.0->80.0 y | shuffled | 1.3 | 0.634 | 1.71 | 16.1 | 0.104 | 0.174 | 0 | 0 | 0 | 0 |
| skin 20.0->80.0 y | uniform | 1.3 | 0.676 | nan | 2.13 | nan | nan | 0 | 0 | 0 | 0 |
| Col I z=3.2 dose 0.0->1.0 iso | actual | 8.28 | 1.33 | 91 | 141 | 0.163 | 0.24 | 0 | 0 | 0 | 0 |
| Col I z=3.2 dose 0.0->1.0 iso | shuffled | 8.28 | 1.33 | 89.3 | 140 | 0.15 | 0.223 | 0 | 0 | 0 | 0 |
| Col I z=3.2 dose 0.0->1.0 iso | uniform | 8.28 | 2.09 | nan | 4.25e+03 | nan | nan | 0 | 0 | 0 | 0 |

Sign agreement with the keratinocyte signature across the whole parameter sweep (actual field):

- Col I z=3.2 dose 0.0->1.0 iso: depolarised 100%, within-SD down 0%, between-SD up 100%, Moran's I down 0% of 1 parameter sets
- skin 20.0->80.0 y: depolarised 100%, within-SD down 0%, between-SD up 100%, Moran's I down 0% of 1 parameter sets
