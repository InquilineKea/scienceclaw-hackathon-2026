OPENMM CUDA EXPERIMENT LOG — 31 OCTOBER 2026

Captured test: 2026-10-31T09:02:56.750241+00:00 to 2026-10-31T09:02:59.306395+00:00.
Status: PASS. Actual compute platform: CUDA. Device: NVIDIA L4.
OpenMM: 8.6.1. Precision: mixed. Driver: 580.178.04.

The test creates two particles (12 Da each), a harmonic bond (equilibrium
length 0.1 nm, force constant 1000 kJ/mol/nm^2), and an initial separation
of 0.12 nm with zero starting velocities. It compares CUDA and Reference
initial energies and forces, then takes 1000 Verlet NVE steps of 1 fs on
CUDA, for 1 ps of simulated time.

Observed initial potential energies:
  Reference: 0.19999999999999979 kJ/mol
  CUDA:      0.19999991357326508 kJ/mol
Analytic energy: 0.2 kJ/mol; absolute tolerance: 1e-4 kJ/mol.
Maximum absolute force difference: 5.722045887779359e-06 kJ/mol/nm.
Force tolerance: 1e-3 kJ/mol/nm.
Relative final energy drift: 3.6648566137967979e-05.
Energy-drift limit: 1e-3 (0.1%).

SCOPE
This is an infrastructure and numerical smoke test. It does not validate
collagen chemistry, crosslinks, binding, aging mechanisms, solvent, PME,
nonbonded interactions, long simulations, or biological predictions.
The result records missing optional OpenCL libraries; CUDA loaded and ran.
No CPU fallback was allowed for the integration stage.

ACCESS DIAGNOSIS
The earlier restricted execution context reported CUDA_ERROR_NO_DEVICE
and could not resolve PyPI. After the session restrictions were removed,
the same hostname exposed the NVIDIA L4, cuInit returned 0, device count
was 1, and PyPI HTTPS returned 200. Both diagnostic records are included.
The pre-install smoke-test failure (OpenMM absent) is also retained.

FILES AND INTEGRITY
The results/, evidence/ and scripts/ files preserve the original bytes.
requirements-lock.txt copies the installed package versions captured by
pip freeze. publication_metadata.json was recorded at publication time.
manifest.json lists SHA-256 checksums and sizes. SHA256SUMS additionally
covers manifest.json. The ZIP checksum is provided outside the ZIP.
No trajectories or energy time series were saved by this test.

REPRODUCE WITH THE CAPTURED PACKAGE VERSIONS
On a Linux machine with an NVIDIA GPU, a suitable NVIDIA driver, Python
3.10 and the Python venv module, extract this ZIP and run from its root:

  python3 -m venv --without-pip .venv
  curl --fail --location https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  .venv/bin/python get-pip.py
  .venv/bin/python -m pip install --only-binary=:all: -r requirements-lock.txt
  .venv/bin/python scripts/openmm_cuda_smoke.py --output results/reproduced.json

The included original run_openmm_cuda_smoke.sh records hardware, probes
CUDA and PyPI, bootstraps pip if needed, installs openmm[cuda12], and runs
the test. Its install command resolves available versions at rerun time;
use the pinned instructions above to match this captured environment.
Equivalent reruns can differ within the stated numerical tolerances.

OpenMM installation documentation:
https://docs.openmm.org/latest/userguide/application/01_getting_started.html
Public report: https://openmm-cuda-experiment-log.stochasticcockatoo.chatgpt.site
WordPress research hub: https://humanavianaisymbiosis.wordpress.com/scienceclaw-comparative-collagen-aging-research-hub/
