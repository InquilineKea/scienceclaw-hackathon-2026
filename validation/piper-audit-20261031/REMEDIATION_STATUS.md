# Piper audit remediation — prepared, validation pending

Working branch: codex/audit-remediation-20261031, based on fetched origin/main b050dd6. Frozen runs and manifests were not edited. The uploaded audit is treated as a handoff, not independent numerical evidence.

## Prepared changes
- Fresh default parameter objects for motor_clutch, CellModel and heart; fresh default headers in the network-capable image-review helper.
- Explicit per-animation callback bindings.
- README qualifications distinguishing target from actual coordination and local from cpu32 campaign ranges. Prepared patches parse as Python; git diff --check passed. Dynamic equivalence is untested.
- Removed the unsupported instruction to trust an unexecuted 48×48 GPU profile.

## Reanalysis of saved data (no solver execution)
Healthy Col I, mode none, ratio of endpoint mean G:
| Campaign | Nodes/grid | Seeds | Target z interval | Ratio |
| --- | --- | --- | --- | ---: |
| local | 12×12 | 2 | 3.0→4.4 | 51.024987 |
| cpu32 | 16×16 | 4 | 2.8→5.0 | 259.284652 |
| cpu32, common target endpoints | 16×16 | 4 | 3.0→4.4 | 68.735670 |

Actual local mean z at endpoints is 3.19444→4.60417. Actual cpu32 mean z at common endpoints is 3.19141→4.52148. Matching target endpoints does not control realized geometry, seeds or finite-size effects. No statistical significance or new solver reproduction is claimed.

## Work still required
1. Execute the reviewed isolated atlas reproduction pilot after local approval; retain full curves and failure logs. This checks repeatability of existing code, not an independent implementation.
2. Numerically compare unchanged and patched Python defaults with fixed seeds, test instance isolation, and check plotting callback parity in a separately reviewed isolated environment.
3. Run predeclared matched-budget and matched-stiffness 2D/3D/disordered controls, treating geometry, orientation, connectivity and damage placement as separate interventions. New runs require their own new IDs and acceptance gates.
4. Reconcile FEniCSx algebraic solve counts with observable mesh-acceptance denominators; algebraic success is insufficient. Existing evidence is not replaced by this patch.
5. Build experimental calibration and held-out validation for recruitment, relaxation and anisotropy. Rupture, remodeling and molecular/sequence-to-network transfer remain uncalibrated until corresponding evidence is supplied or measured.

No new cloud resources were provisioned, paid computation launched, repository code executed, or results published. The user can review prepared-fixes.patch and SECURITY_REVIEW.md before local execution approval.

## Approved pilot update

The six-case atlas pilot completed successfully. See PILOT_RESULT.md and PILOT_RESULT.json. Python numerical regressions remain pending approval; code fixes are still uncommitted and unpublished.

## Python regression update

The approved isolated before/after Python suite completed with seven passing tests, including twelve heart conditions and seeded clutch comparisons. See PYTHON_RESULT.json and python-runs/. The preparation-stage pending notes above are historical. The plotting script and full multiscale sweeps were not executed. Scientific geometry and calibration gates remain open.
