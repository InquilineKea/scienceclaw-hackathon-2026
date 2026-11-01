# Bioelectric ageing test (64x64 networks, 16x16 cells, 8 seeds, paired across conditions)

Keratinocyte senescence (Sediqi & Levin 2025, day 10 -> 40/50 in culture, no ECM): depolarised; within-dish variability -38% (ratio ~0.62); between-dish SD x15-22; Moran's I 0.5 -> 0.13-0.26.

S_pa = 18100.7 Pa per lattice unit (young skin dermis E = 2 kPa). Timings (s): {"network": 2253, "cell": 60, "vmem": 155}

G0=1, F50=400 pN, junctions = const, all three field controls:

| contrast | field | E_ratio | dV_mean_mV | sd_within_ratio | sd_between_ratio | moranV_young | moranV_old | q_hold_young | q_hold_old | net_heal_25_young | net_heal_25_old |
|---|---|---|---|---|---|---|---|---|---|---|---|
| skin 20->80 y | actual | 1.31 | 3.01 | 1.13 | 1.05 | 0.518 | 0.543 | 0 | 0 | 0.00231 | -0.0292 |
| skin 20->80 y | shuffled | 1.31 | 3 | 1.12 | 1.05 | 0.476 | 0.502 | 0 | 0 | 0.00231 | -0.0232 |
| skin 20->80 y | uniform | 1.31 | 5.45 | nan | 1.23 | nan | nan | 0 | 0 | 0.00476 | 0.000896 |
| Col I z=2.8 dose 0->1 iso | actual | 38.8 | 2.62 | 41.9 | 30.1 | 0.535 | 0.582 | 0 | 0 | -0.0261 | 0.00599 |
| Col I z=2.8 dose 0->1 iso | shuffled | 38.8 | 2.62 | 38.7 | 30.4 | 0.484 | 0.481 | 0 | 0 | -0.0261 | 0.00599 |
| Col I z=2.8 dose 0->1 iso | uniform | 38.8 | 1.55 | nan | 2.02e+03 | nan | nan | 0 | 0 | -0.0261 | 0.00599 |
| Col I z=3.2 dose 0->1 iso | actual | 12.1 | 7.36 | 2.93 | 1.23 | 0.589 | 0.574 | 0 | 0 | 0.0231 | 0.00066 |
| Col I z=3.2 dose 0->1 iso | shuffled | 12.1 | 7.36 | 2.91 | 1.23 | 0.465 | 0.442 | 0 | 0 | 0.0231 | 0.00066 |
| Col I z=3.2 dose 0->1 iso | uniform | 12.1 | 8.69 | nan | 6.05 | nan | nan | 0 | 0 | 0.0231 | -0.00773 |
| Col I z=3.6 dose 0->1 iso | actual | 7.35 | 11.9 | 1.13 | 1.1 | 0.551 | 0.618 | 0 | 0 | -0.0162 | -0.000377 |
| Col I z=3.6 dose 0->1 iso | shuffled | 7.35 | 11.9 | 1.1 | 1.06 | 0.484 | 0.539 | 0 | 0 | -0.0162 | -0.000377 |
| Col I z=3.6 dose 0->1 iso | uniform | 7.35 | 24.6 | nan | 10.8 | nan | nan | 0 | 0 | -0.0162 | -0.000377 |
| Col I z=4 dose 0->1 iso | actual | 4.27 | 2.26 | 1.07 | 1.41 | 0.566 | 0.61 | 0 | 0 | 0.00556 | -0.0107 |
| Col I z=4 dose 0->1 iso | shuffled | 4.27 | 2.25 | 1.1 | 1.43 | 0.469 | 0.545 | 0 | 0 | 0.0191 | -0.0107 |
| Col I z=4 dose 0->1 iso | uniform | 4.27 | -4.14 | nan | 0.0972 | nan | nan | 0 | 0 | 0.0297 | -0.0107 |
| Col I z=4.4 dose 0->1 iso | actual | 2.88 | -12.2 | 1.84 | 2.79 | 0.602 | 0.59 | 0 | 0 | 0.0247 | 0.0188 |
| Col I z=4.4 dose 0->1 iso | shuffled | 2.88 | -12.2 | 1.69 | 2.76 | 0.57 | 0.476 | 0 | 0 | 0.0247 | 0.0188 |
| Col I z=4.4 dose 0->1 iso | uniform | 2.88 | -50.4 | nan | 0.0459 | nan | nan | 0 | 0 | 0.0247 | 0.0188 |

G0=1, F50=400 pN, junctions = prestress, all three field controls:

| contrast | field | E_ratio | dV_mean_mV | sd_within_ratio | sd_between_ratio | moranV_young | moranV_old | q_hold_young | q_hold_old | net_heal_25_young | net_heal_25_old |
|---|---|---|---|---|---|---|---|---|---|---|---|
| skin 20->80 y | actual | 1.31 | 3.01 | 1.12 | 1.05 | 0.473 | 0.501 | 0 | 0 | 0.00231 | 0.000896 |
| skin 20->80 y | shuffled | 1.31 | 3.01 | 1.11 | 1.05 | 0.423 | 0.451 | 0 | 0 | 0.00231 | 0.000896 |
| skin 20->80 y | uniform | 1.31 | 5.45 | nan | 1.23 | nan | nan | 0.25 | 0 | -0.125 | 0.000896 |
| Col I z=2.8 dose 0->1 iso | actual | 38.8 | 2.61 | 25.7 | 30.2 | 0.189 | 0.466 | 0.858 | 0.0024 | 0.0217 | 0.00599 |
| Col I z=2.8 dose 0->1 iso | shuffled | 38.8 | 2.61 | 22.6 | 30.4 | 0.115 | 0.34 | 0.938 | 0 | 0.0264 | 0.00599 |
| Col I z=2.8 dose 0->1 iso | uniform | 38.8 | 1.55 | nan | 2.02e+03 | nan | nan | 0.933 | 0 | -0.016 | 0.00599 |
| Col I z=3.2 dose 0->1 iso | actual | 12.1 | 7.35 | 2.24 | 1.24 | 0.409 | 0.511 | 0.00481 | 0 | 0.0195 | 0.00066 |
| Col I z=3.2 dose 0->1 iso | shuffled | 12.1 | 7.36 | 2.11 | 1.24 | 0.273 | 0.373 | 0.012 | 0 | 0.0225 | 0.00066 |
| Col I z=3.2 dose 0->1 iso | uniform | 12.1 | 8.69 | nan | 6.05 | nan | nan | 0 | 0 | 0.0231 | 0.00688 |
| Col I z=3.6 dose 0->1 iso | actual | 7.35 | 11.9 | 1.07 | 1.11 | 0.474 | 0.573 | 0 | 0 | -0.0162 | -0.000377 |
| Col I z=3.6 dose 0->1 iso | shuffled | 7.35 | 11.9 | 1.04 | 1.07 | 0.407 | 0.494 | 0.0024 | 0 | -0.0162 | -0.000377 |
| Col I z=3.6 dose 0->1 iso | uniform | 7.35 | 24.6 | nan | 10.8 | nan | nan | 0 | 0 | -0.0162 | -0.000377 |
| Col I z=4 dose 0->1 iso | actual | 4.27 | 2.26 | 1.05 | 1.41 | 0.518 | 0.568 | 0 | 0 | 0.0297 | -0.0107 |
| Col I z=4 dose 0->1 iso | shuffled | 4.27 | 2.26 | 1.07 | 1.43 | 0.418 | 0.5 | 0 | 0 | 0.0297 | -0.0107 |
| Col I z=4 dose 0->1 iso | uniform | 4.27 | -4.14 | nan | 0.0972 | nan | nan | 0 | 0 | 0.0297 | -0.0107 |
| Col I z=4.4 dose 0->1 iso | actual | 2.88 | -12.3 | 1.77 | 2.77 | 0.563 | 0.546 | 0 | 0 | 0.0247 | 0.0188 |
| Col I z=4.4 dose 0->1 iso | shuffled | 2.88 | -12.2 | 1.64 | 2.73 | 0.532 | 0.434 | 0 | 0 | 0.0247 | 0.0188 |
| Col I z=4.4 dose 0->1 iso | uniform | 2.88 | -50.4 | nan | 0.0459 | nan | nan | 0 | 0 | 0.0247 | 0.0188 |

Sign agreement with the keratinocyte signature across the parameter sweep (actual field), by junction mode:

- Col I z=2.8 dose 0->1 iso, const: depolarised 100%, within-SD down 0%, between-SD up 100%, Moran's I down 0% of 9 parameter sets
- Col I z=2.8 dose 0->1 iso, prestress: depolarised 100%, within-SD down 0%, between-SD up 100%, Moran's I down 0% of 9 parameter sets
- Col I z=3.2 dose 0->1 iso, const: depolarised 100%, within-SD down 11%, between-SD up 78%, Moran's I down 78% of 9 parameter sets
- Col I z=3.2 dose 0->1 iso, prestress: depolarised 100%, within-SD down 0%, between-SD up 78%, Moran's I down 0% of 9 parameter sets
- Col I z=3.6 dose 0->1 iso, const: depolarised 100%, within-SD down 44%, between-SD up 67%, Moran's I down 0% of 9 parameter sets
- Col I z=3.6 dose 0->1 iso, prestress: depolarised 100%, within-SD down 44%, between-SD up 67%, Moran's I down 0% of 9 parameter sets
- Col I z=4 dose 0->1 iso, const: depolarised 100%, within-SD down 11%, between-SD up 89%, Moran's I down 22% of 9 parameter sets
- Col I z=4 dose 0->1 iso, prestress: depolarised 100%, within-SD down 11%, between-SD up 89%, Moran's I down 11% of 9 parameter sets
- Col I z=4.4 dose 0->1 iso, const: depolarised 0%, within-SD down 0%, between-SD up 100%, Moran's I down 22% of 9 parameter sets
- Col I z=4.4 dose 0->1 iso, prestress: depolarised 0%, within-SD down 0%, between-SD up 100%, Moran's I down 22% of 9 parameter sets
- skin 20->80 y, const: depolarised 100%, within-SD down 33%, between-SD up 78%, Moran's I down 11% of 9 parameter sets
- skin 20->80 y, prestress: depolarised 100%, within-SD down 33%, between-SD up 78%, Moran's I down 11% of 9 parameter sets

All four keratinocyte signs at once (point estimates): 0 of 108 contrast x parameter sets (actual field).
All four with 95% bootstrap intervals excluding the null: 0 of 108.
Moran's I of Vmem significantly up with ageing: 42; significantly down: 0 (of 108).

- const: Moran up 12, down 0, all four 0 of 54
- prestress: Moran up 30, down 0, all four 0 of 54

net_heal_f = q_restore_f - q_flipped_f: restoration beyond the flipped-but-unhealed baseline (0 = none).
AIS / TE: Gaussian active information storage and neighbour transfer entropy (nats) from a noisy stationary run; MI_EV: Gaussian mutual information between local log stiffness and time-mean Vmem.
