# Collagen network -> organoid gene expression (no_amotl2_feedback)

Model outputs, not measurements. Gene-network parameters are assumptions (oxt/organoid.py).

Gels: 156; network W=32, seeds=4; timings (s): {"network": 0, "cell": 137, "organoid": 3}

## Day 1: how much of each read-out does linear stiffness explain?

| readout     |   spread |   R2_stiffness_only |   R2_network_descriptors |
|:------------|---------:|--------------------:|-------------------------:|
| R_um        |    9.499 |               0.971 |                    0.966 |
| CYR61_mean  |    0.108 |               0.736 |                    0.662 |
| CTGF_mean   |    0.126 |               0.74  |                    0.672 |
| ANKRD1_mean |    0.298 |               0.729 |                    0.666 |
| AMOTL2_mean |    0.153 |               0.747 |                    0.684 |
| ACTA2_mean  |    0.479 |               0.875 |                    0.907 |
| LOX_mean    |    0.309 |               0.869 |                    0.892 |
| MMP14_mean  |    0.152 |               0.749 |                    0.698 |
| LY6A_mean   |    0.215 |               0.739 |                    0.708 |
| LGR5_mean   |    0.243 |               0.296 |                    0.293 |
| KRT20_mean  |    0.095 |               0.022 |                   -0.052 |
| MKI67_mean  |    0.195 |              -0.005 |                   -0.065 |

## Day 1: matched linear stiffness (within 10 %), different network

| readout     |   n_pairs |   median_rel_diff |   p90_rel_diff |   max_rel_diff |
|:------------|----------:|------------------:|---------------:|---------------:|
| CTGF_mean   |       389 |             0.005 |          0.036 |          0.247 |
| ANKRD1_mean |       389 |             0.004 |          0.031 |          0.207 |
| LY6A_mean   |       389 |             0.004 |          0.023 |          0.122 |
| LGR5_mean   |       389 |             0.018 |          0.35  |          0.53  |
| ACTA2_mean  |       389 |             0.003 |          0.038 |          0.162 |
| MKI67_mean  |       389 |             0.018 |          0.821 |          0.846 |
| R_um        |       389 |             0.035 |          0.109 |          0.242 |

Largest ANKRD1 difference at matched stiffness:

| collagen   |     z | chem           | mode   |   dose |   E_lin_Pa |   stiffening_E20_over_E0 |   strain_at_peak |   R_um |   eps_mean |   Y_mean |   CTGF_mean |   ANKRD1_mean |   LY6A_mean |   LGR5_mean |
|:-----------|------:|:---------------|:-------|-------:|-----------:|-------------------------:|-----------------:|-------:|-----------:|---------:|------------:|--------------:|------------:|------------:|
| I          | 2.922 | dityrosine     | aniso  |   0.25 |     57.764 |                    3.201 |             0.15 | 60.597 |      0.153 |    0.729 |       0.772 |         0.706 |       0.736 |       0.214 |
| I          | 2.927 | isopeptide_TG2 | iso    |   0.25 |     53.467 |                    3.07  |             0.27 | 60.639 |      0.142 |    0.806 |       0.803 |         0.767 |       0.76  |       0.196 |

## Day 1: decode gel network from the organoid (15 % noise, 8 replicates)

| target         |   R2_full_panel |   R2_best4 | best4                                    |
|:---------------|----------------:|-----------:|:-----------------------------------------|
| log10_E_lin    |           0.464 |      0.46  | ACTA2_tip, ACTA2_mean, R_um, LOX_tip     |
| stiffening     |           0.424 |      0.42  | ACTA2_tip, ACTA2_mean, R_um, LOX_mean    |
| strain_at_peak |           0.223 |      0.22  | ACTA2_tip, ACTA2_mean, R_um, LGR5_tip    |
| log10_mesh     |           0.27  |      0.285 | ACTA2_tip, R_um, ACTA2_mean, AMOTL2_mean |
| dose           |           0.128 |      0.146 | LGR5_tip, ACTA2_tip, LOX_tip, R_um       |
| z              |           0.249 |      0.259 | ACTA2_tip, R_um, ACTA2_mean, AMOTL2_mean |

## Day 3: how much of each read-out does linear stiffness explain?

| readout     |   spread |   R2_stiffness_only |   R2_network_descriptors |
|:------------|---------:|--------------------:|-------------------------:|
| R_um        |   36.45  |               0.937 |                    0.955 |
| CYR61_mean  |    0.365 |               0.218 |                    0.103 |
| CTGF_mean   |    0.357 |               0.26  |                    0.146 |
| ANKRD1_mean |    0.409 |               0.439 |                    0.331 |
| AMOTL2_mean |    0.337 |               0.332 |                    0.224 |
| ACTA2_mean  |    0.491 |               0.775 |                    0.76  |
| LOX_mean    |    0.37  |               0.668 |                    0.619 |
| MMP14_mean  |    0.324 |               0.347 |                    0.235 |
| LY6A_mean   |    0.299 |               0.475 |                    0.352 |
| LGR5_mean   |    0.285 |               0.349 |                    0.264 |
| KRT20_mean  |    0.117 |               0.049 |                   -0.019 |
| MKI67_mean  |    0.214 |               0.002 |                   -0.046 |

## Day 3: matched linear stiffness (within 10 %), different network

| readout     |   n_pairs |   median_rel_diff |   p90_rel_diff |   max_rel_diff |
|:------------|----------:|------------------:|---------------:|---------------:|
| CTGF_mean   |       389 |             0.005 |          0.052 |          0.911 |
| ANKRD1_mean |       389 |             0.01  |          0.101 |          0.84  |
| LY6A_mean   |       389 |             0.007 |          0.082 |          0.826 |
| LGR5_mean   |       389 |             0.059 |          0.297 |          0.558 |
| ACTA2_mean  |       389 |             0.005 |          0.162 |          0.645 |
| MKI67_mean  |       389 |             0.047 |          0.752 |          0.808 |
| R_um        |       389 |             0.044 |          0.155 |          0.359 |

Largest ANKRD1 difference at matched stiffness:

| collagen   |     z | chem           | mode   |   dose |   E_lin_Pa |   stiffening_E20_over_E0 |   strain_at_peak |   R_um |   eps_mean |   Y_mean |   CTGF_mean |   ANKRD1_mean |   LY6A_mean |   LGR5_mean |
|:-----------|------:|:---------------|:-------|-------:|-----------:|-------------------------:|-----------------:|-------:|-----------:|---------:|------------:|--------------:|------------:|------------:|
| I          | 3.215 | glucosepane    | aniso  |   0.25 |    249.071 |                    2.355 |             0.27 | 82.974 |      0.248 |    0.59  |       0.639 |         0.462 |       0.568 |       0.279 |
| I          | 3.22  | isopeptide_TG2 | aniso  |   0.25 |    236.805 |                    2.258 |             0.39 | 81.042 |      0.199 |    0.856 |       0.821 |         0.805 |       0.789 |       0.174 |

## Day 3: decode gel network from the organoid (15 % noise, 8 replicates)

| target         |   R2_full_panel |   R2_best4 | best4                                   |
|:---------------|----------------:|-----------:|:----------------------------------------|
| log10_E_lin    |           0.64  |      0.651 | R_um, ACTA2_mean, ACTA2_tip, ANKRD1_tip |
| stiffening     |           0.524 |      0.532 | R_um, ACTA2_mean, LOX_mean, LGR5_tip    |
| strain_at_peak |           0.289 |      0.326 | R_um, ACTA2_mean, CYR61_tip, LGR5_tip   |
| log10_mesh     |           0.532 |      0.544 | R_um, ACTA2_tip, ANKRD1_tip, ACTA2_mean |
| dose           |           0.103 |      0.139 | R_um, LGR5_tip, KRT20_tip, ACTA2_mean   |
| z              |           0.516 |      0.513 | R_um, ACTA2_tip, ANKRD1_tip, LY6A_mean  |

## Day 7: how much of each read-out does linear stiffness explain?

| readout     |   spread |   R2_stiffness_only |   R2_network_descriptors |
|:------------|---------:|--------------------:|-------------------------:|
| R_um        |  131.452 |               0.877 |                    0.918 |
| CYR61_mean  |    0.372 |               0.249 |                    0.121 |
| CTGF_mean   |    0.363 |               0.305 |                    0.183 |
| ANKRD1_mean |    0.405 |               0.533 |                    0.435 |
| AMOTL2_mean |    0.342 |               0.398 |                    0.288 |
| ACTA2_mean  |    0.516 |               0.702 |                    0.693 |
| LOX_mean    |    0.393 |               0.568 |                    0.509 |
| MMP14_mean  |    0.342 |               0.394 |                    0.286 |
| LY6A_mean   |    0.378 |               0.452 |                    0.348 |
| LGR5_mean   |    0.332 |               0.336 |                    0.251 |
| KRT20_mean  |    0.152 |               0.128 |                    0.057 |
| MKI67_mean  |    0.235 |               0.061 |                    0.008 |

## Day 7: matched linear stiffness (within 10 %), different network

| readout     |   n_pairs |   median_rel_diff |   p90_rel_diff |   max_rel_diff |
|:------------|----------:|------------------:|---------------:|---------------:|
| CTGF_mean   |       389 |             0.009 |          0.067 |          0.938 |
| ANKRD1_mean |       389 |             0.018 |          0.142 |          0.875 |
| LY6A_mean   |       389 |             0.016 |          0.116 |          0.888 |
| LGR5_mean   |       389 |             0.072 |          0.257 |          0.644 |
| ACTA2_mean  |       389 |             0.004 |          0.186 |          0.636 |
| MKI67_mean  |       389 |             0.054 |          0.68  |          0.76  |
| R_um        |       389 |             0.031 |          0.209 |          0.554 |

Largest ANKRD1 difference at matched stiffness:

| collagen   |     z | chem           | mode   |   dose |   E_lin_Pa |   stiffening_E20_over_E0 |   strain_at_peak |    R_um |   eps_mean |   Y_mean |   CTGF_mean |   ANKRD1_mean |   LY6A_mean |   LGR5_mean |
|:-----------|------:|:---------------|:-------|-------:|-----------:|-------------------------:|-----------------:|--------:|-----------:|---------:|------------:|--------------:|------------:|------------:|
| I          | 2.922 | dityrosine     | aniso  |   0.25 |     57.764 |                    3.201 |             0.15 | 153.725 |      0.305 |    0.449 |       0.46  |         0.405 |       0.416 |       0.416 |
| I          | 2.927 | isopeptide_TG2 | iso    |   0.25 |     53.467 |                    3.07  |             0.27 | 174.598 |      0.263 |    0.803 |       0.801 |         0.76  |       0.752 |       0.202 |

## Day 7: decode gel network from the organoid (15 % noise, 8 replicates)

| target         |   R2_full_panel |   R2_best4 | best4                                   |
|:---------------|----------------:|-----------:|:----------------------------------------|
| log10_E_lin    |           0.803 |      0.796 | R_um, ACTA2_mean, CTGF_mean, KRT20_mean |
| stiffening     |           0.678 |      0.678 | R_um, ACTA2_mean, KRT20_tip, LGR5_tip   |
| strain_at_peak |           0.406 |      0.436 | R_um, KRT20_mean, CTGF_mean, KRT20_tip  |
| log10_mesh     |           0.655 |      0.648 | R_um, ACTA2_tip, LGR5_mean, KRT20_mean  |
| dose           |           0.224 |      0.25  | R_um, KRT20_tip, ACTA2_mean, AMOTL2_tip |
| z              |           0.654 |      0.642 | R_um, LGR5_mean, ACTA2_tip, KRT20_mean  |

## Day 7: medians by crosslinker and alignment (over z and dose)

| collagen   | chem           | mode   |   E_lin_Pa |    R_um |     Y |   CTGF |   ANKRD1 |   LY6A |   LGR5 |   KRT20 |   ACTA2 |   tip_minus_inter_ANKRD1 |
|:-----------|:---------------|:-------|-----------:|--------:|------:|-------:|---------:|-------:|-------:|--------:|--------:|-------------------------:|
| I          | dityrosine     | aniso  |   2333.95  |  69.541 | 0.843 |  0.816 |    0.796 |  0.785 |  0.176 |   0.06  |   0.737 |                   -0.007 |
| I          | dityrosine     | iso    |   3080.68  |  66.336 | 0.8   |  0.8   |    0.759 |  0.758 |  0.196 |   0.066 |   0.741 |                   -0.047 |
| I          | glucosepane    | aniso  |   2453.21  |  74.846 | 0.832 |  0.812 |    0.787 |  0.777 |  0.139 |   0.101 |   0.737 |                   -0.015 |
| I          | glucosepane    | iso    |   2759.02  |  69.208 | 0.829 |  0.811 |    0.784 |  0.774 |  0.134 |   0.093 |   0.741 |                   -0.026 |
| I          | isopeptide_TG2 | aniso  |   2597.29  |  76.02  | 0.855 |  0.821 |    0.805 |  0.791 |  0.172 |   0.059 |   0.74  |                    0.001 |
| I          | isopeptide_TG2 | iso    |   2641.24  |  72.855 | 0.828 |  0.81  |    0.783 |  0.775 |  0.183 |   0.062 |   0.741 |                   -0.022 |
| I          | none           | none   |    911.648 | 136.83  | 0.852 |  0.82  |    0.803 |  0.789 |  0.173 |   0.059 |   0.716 |                   -0.002 |
| I          | pyridinoline   | aniso  |   2164.42  |  77.484 | 0.854 |  0.82  |    0.804 |  0.789 |  0.173 |   0.059 |   0.736 |                    0     |
| I          | pyridinoline   | iso    |   2529.28  |  75.975 | 0.848 |  0.818 |    0.799 |  0.782 |  0.178 |   0.06  |   0.739 |                   -0.013 |
| IV         | none           | none   |    228.915 | 169.437 | 0.794 |  0.797 |    0.753 |  0.749 |  0.203 |   0.067 |   0.58  |                   -0.053 |
