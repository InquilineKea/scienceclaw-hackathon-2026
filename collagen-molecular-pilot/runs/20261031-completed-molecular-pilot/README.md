# ScienceClaw collagen fragment pilot — public results and code

This archive contains all new H100 fragment numerical results, coordinates, forces,
SDF structures, convergence records, successful and failed job logs, launch/code,
model and software provenance, plus the recovered pre-existing L4 GAG and MACE-OFF
proxy scans. It also includes the integrity/summary record for the earlier GROMACS
baseline; its separate public blog supplement provides the older detailed inputs
and sampled energy rows. Prior work is labeled explicitly.

The new run used NVIDIA ALCHEMI Toolkit FIRE2/MACE-OFF23, not BGR NIM. All eight
new conformers passed numerical checks. No actual glucosepane/PYD/4-HNE reaction
or tissue mechanics was validated. The old crosslink names are source labels for
simplified proxies, not certified biological structures. No stiffness overrides
from those proxies were imported into the explorer.

Exploratory legacy code is provided as inspected source, not an execution
recommendation or proof of the exact old job source version. Model weights,
software dependency binaries, private connection details, and unrelated account
security records are excluded. Use public/original SHA-256 entries to distinguish
privacy-edited text from exact source bytes. No dependency installation was added
by the H100 pilot. Review external dependencies before reproducing it.

The explorer panel is source-only integration: copy explorer_evidence_panel.py to
its project root; place pilot_run result/provenance/SDF files under
outputs/brev_fragment_pilot; call render_molecular_evidence(st, project_root) from
the existing Streamlit app. It displays evidence without changing stiffness or
rupture parameters. Integration syntax was checked; the app was not run here.
