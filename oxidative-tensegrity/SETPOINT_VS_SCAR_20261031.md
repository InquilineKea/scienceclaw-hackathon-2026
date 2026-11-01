# Setpoint versus scar: local organoid-loop perturbation test (2026-10-31)

**Result:** The tested feedback loop does not exhibit a defended interior stiffness setpoint. AGE-like MMP resistance drives every tested initial condition toward the imposed upper stiffness bound. Native conditions split by initial stiffness: low starts drift slowly downward; high starts drift upward to the bound. Transient positive and negative stiffness pulses did not produce a robust switch or bidirectional restoration. These are **SIMULATED** results from a reduced, frozen-radius slice of the organoid model, not tissue data or a full organoid result.

## Coordination and scope

Before editing, I inspected the current `oxt/organoid.py` and the topology session's shared status note. The current code already includes dose-dependent MMP resistance and clamps `logS` on update. The topology job was using 26 VM workers. I did not change shared organoid code or the active VM checkout. I added `setpoint_vs_scar.py`, and ran it as one process in a separate VM directory with copies of `oxt/organoid.py`, `oxt/cell.py`, and the existing calibration CSV. The current module's `GENES`, `gene_targets`, and `OrganoidParams` are imported directly. The frozen-radius assay holds hoop strain at zero, uses the saved cell-model calibration to interpolate YAP and prestress versus stiffness, and integrates the same gene kinetics and LOX/MMP14 `logS` update as the organoid model. It therefore isolates the putative memory loop but does not test growth, shape, cell-to-cell coupling, or ECM topology.

## Design and clipping checks

Baseline effective Young modulus was 180 Pa, inside the saved YAP transition band. Conditions crossed dose 0 or 1, initial matrix factors 0.7, 1, and 1.4, a day-10-to-13 effective-stiffness pulse of factor 1/1.8, 1, or 1.8, and matrix-factor bounds 0.4–2.5 or widened 0.1–10. Each run lasted 90 model days at 0.2 h steps; the slow-relaxation check lasted 360 days at 0.4 h steps. The pulse changes the sensed modulus transiently and is removed, so any residual change must pass through the model's feedback. Daily `logS`, YAP, prestress, remodelling rate, bound contact and pulse state were saved.

| Dose | Bounds | Day-360 final `logS` range | At bound | Late remodelling rate (logS/day) | Reading |
|---|---:|---:|---:|---:|---|
| 0 | 0.4–2.5 | −0.848 to 0.916 | 3/9 | −0.0006 to +0.0206 | Low states are still slowly drifting; high states are clipped with positive drive |
| 0 | 0.1–10 | −0.848 to 2.303 | 3/9 | −0.0006 to +0.0447 | Widening the bound moves the high state upward; it is not an interior attractor |
| 1 | 0.4–2.5 | 0.916 | 9/9 | +0.1050 | All conditions hit the upper bound with strong positive drive |
| 1 | 0.1–10 | 2.303 | 9/9 | +0.1383 | The supposed scar follows the new bound, proving numerical clipping dominates its plateau |

For the native widened-bound low start, day-360 `logS` ≈ −0.848 with rate ≈ −0.0004/day; the mid start is ≈ −0.819 with rate ≈ −0.0006/day. They remain distinct and moving, so apparent persistence cannot be called stable memory. The high start reaches `logS = log(10)` with rate +0.0447/day. The three pulse values leave the low-start endpoint within 0.001 and the mid-start endpoint within 0.006. Thus the tested pulse does not switch the attractor; a stronger/different timed perturbation could still cross a separatrix, but that has not been demonstrated.

**Classification:** upper-bound states are clipping plus ongoing drift; lower native states show slow relaxation on this horizon. No tested state meets the proposed setpoint criterion of returning to an interior target after perturbations in both directions. AGE dose in this assay changes the drift toward the bound, not evidence of a tissue storing or defending a target morphology. A persistent *physical* matrix scar would require a distinct irreversible crosslink state; this assay only changes MMP resistance and a mutable stiffness scalar.

## Limitations and next test

The calibration is from the flat-modulus cell response, not a condition-specific nonlinear collagen curve. External pulses act on sensed stiffness rather than on a spatial strain field. The fixed radius and zero-strain approximation omit the organoid growth/confinement loop; this is a mechanism test, not a direct numerical run of `simulate_organoids`. The 90- and 360-day runs also use different time steps, so this is not a strict time-step convergence study. A future full-model assay should expose initial-state and pulse hooks in `simulate_organoids`, retain the clip diagnostic, compare longer horizons with equal time steps, and repeat across saved gel-specific cell tables. No such shared-code change was made during other sessions' active work.

Outputs: `results/setpoint_vs_scar/` and `results/setpoint_vs_scar_360/` contain the trajectories, summary and run metadata. Script: `setpoint_vs_scar.py`. GCP VM: `oxt-cpu32`, project `scienceclaw26bos-3008`, isolated directory `~/setpoint-scar-20261031`. No new package was installed.
