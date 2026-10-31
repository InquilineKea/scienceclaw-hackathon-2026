# Collagen molecular pilot: completed data and reproducibility

The completed record is in [runs/20261031-completed-molecular-pilot](runs/20261031-completed-molecular-pilot/). It includes the eight H100 fragment geometry relaxations, prepared and relaxed SDF structures, coordinates/energies/forces, convergence logs, successful and failed attempt records, model/software provenance, costs, L4 MACE-OFF/MACE-MP scans, comparison calculations, figure source and diagrams. Original job identifiers are retained.

The [prior GROMACS archive](prior-gromacs/20261031-ppg9-seed104729/) is earlier work, not a new run by this task. It includes its saved trajectories, topology/force-field files, inputs, energies, run logs and integrity records. Its original downloaded ZIP is preserved under the repository's archives/2026-10-31/. A 20 ps PPG9 baseline cannot establish collagen mechanics or crosslink chemistry.

The H100 work used NVIDIA ALCHEMI Toolkit/MACE-OFF, not the separate BGR NIM service. Legacy names for glucosepane, PYD and other crosslinks refer to simplified proxies. These calculations do not simulate validated native crosslink reactions, tissue fracture or extreme pressure/acceleration resistance. See the completed report and comparison caveats inside the frozen run.

## Future execution and storage

The live `run_pilot.sh` allocates a unique directory with exclusive creation. `pilot.py` refuses to reuse a folder containing prior scientific output or a previous start marker. A retry must be a new run. Historical scripts inside the completed archive are preserved verbatim as provenance; use the live entry point for future work.

No cloud job was launched by this archival update. All existing GPU-use, security-review and explicit execution-approval gates remain. No packages or model weights are bundled or installed by the archival work. Review external dependencies before execution.

The archive preserves all available files; it cannot supply molecular trajectories or solver iterations that were never recorded. Local files must still be deliberately committed/pushed or archived to GitHub after future runs. No unattended upload process was installed.
