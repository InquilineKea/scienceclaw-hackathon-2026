# LAMMPS reduced-network CPU reference

CPU commissioning completed31October2026:41/41 checks passed, including independent energies/forces/stress and equilibrium, driven time-step checks, undriven energy accounting and the six supplied materials at widths8/32. See CPU_VALIDATION_20261031.md. The six width32 deck/data sets are regenerated; this does not mean the complete six-system dynamic sweep was run.

## Required driver

Run in the reviewed, isolated remote CPU environment from the project root:

```bash
python -m oxt.lammps_export remote/lammps/colI_none.in
```

Use the explicit six stems colI_none,colI_iso,colI_aniso,colVII_none,colVII_iso,colVII_aniso when selecting a job. Do not glob all *.in: each material also has a base include file. Bare `lmp -in` is unsupported because it lacks the mandatory exact angular callback. The CPU driver is single MPI rank; it is not a commissioned GPU workflow. No paid GPU launch is authorized by this README.

Each material has .data,.base.in,.in and.meta.json files. Keep them together. The driver uses exact per-hinge and per-node angular energy/force/virial through the LAMMPS library, preserving the source law near straight hinges where stock harmonic-angle force regularization differs. It refreshes strain and stress at the same sample time. Runtime checks restrict junction orientation; all saved frames require geometry review before scientific interpretation.

The output columns are time,gamma,sigma_config,potential,tether_energy,thermostat_exchange. Fitting uses actual time:

```python
from oxt.lammps_export import fit_viscoelastic
result = fit_viscoelastic('remote/lammps/colI_none_stress.txt', period=200)
```

Legacy two-column gamma/stress data require explicit sample_interval; no sample-index derivative is assumed. Returned residuals and retained-cycle counts describe the fundamental fit, not biological validation. G_loss near zero should be assessed with an absolute observable tolerance, not a singular relative-error ratio.

## Scope

Reduced LJ units, nominal unit mass and uncalibrated damping; default athermal reference. This is not atomistic collagen MD or a fluid/GAG chemistry model. No contact, sliding kinetics, rupture or reactive potential is introduced. Configurational stress excludes kinetic/thermostat stresses and includes the affine-tether term. Old source and inputs are retained in the task's validation packet.

Validated Linux runtime: LAMMPS2025.7.22.2.0(22Jul2025 Update2), MPICH4.3.2, NumPy1.26.4/SciPy1.14.1. Review/install remotely under the global security policy; keep cloud credentials and personal directories out of workers. A GPU-native exact angular implementation or justified different law must pass a separate parity/performance review before any GPU production. No effect size, physical time or collagen constitutive parameter is calibrated by these checks.
