# ScienceClaw swarm runs (summary; raw logs stay local in swarm/work/)

Setup: ScienceClaw `894598c` in a throwaway Docker container, Gemini 3.6 Flash backend, `--dry-run`, Infinite
pointed at a dead port (each agent's start-up call to Infinite was blocked there; nothing was posted). Skills
installed five extra packages at runtime inside the container (e.g. `chembl-webresource-client`).

## Round 1 — checking the model's predictions (5 collectives, 3–4 agents each, all exit 0)

| Topic | Takeaway |
|---|---|
| Crosslinks vs brittleness (Col I) | Supports the mechanism: crosslinks shift load from inter-molecular sliding to triple-helix backbone tension, consistent with the model's falling failure strain. |
| Collagen VII anchoring fibrils | Pentosidine raises fibril stiffness and lowers strain-to-failure; Col VII NC1/NC2 domains are Lys/Arg rich (susceptible). |
| AGE stiffening and YAP/TAZ | Proposes a YAP→LOX/LOXL2 feed-forward loop (not in the model; see H6). YAP saturation on stiff matrix attributed to motor-clutch limits, as in the model. |
| Growth-factor transport | Matrix-bound VEGF/HSPG binding and RAGE signalling matter more than steric hindrance; flags Ogston as too simple. |
| Heart / alagebrium | Alagebrium also acts on titin glycation, so the model's collagen share of passive myocardial stiffness is oversimplified. |

Unreliable specifics (fabricated-looking residue numbers, an off-topic semiconductor analogy) were discarded.

## Round 2 — Ewald-style hypotheses

See the table at the end of `../HYPOTHESES_EWALD.md`.

## Codex Gemini source critique 2026 10 31

Eight API-only Gemini reviewers completed source critiques on the existing GCP cpu32 VM. This pass used original standard-library workers with no generated-command execution, package installs or ScienceClaw execution. The 12 API calls include four targeted reruns after truncation. Two completed reports required only unambiguous filename expansion. Raw responses, errors and token usage were retained locally.

Curated findings: [CODEX_CRITIQUE_20261031.md](CODEX_CRITIQUE_20261031.md). Raw records: `work/codex_gemini_20261031/` (gitignored). Source packets include oxidative-tensegrity and the separate collagen-scaffold-lab; they are a bounded snapshot, not a claim to cover every private collagen document.

Source checks uphold the need for brittleness-off and pinning-off ablations, per-realization uncertainty propagation, controlled H8 structure/conformer sampling and H5 residual/timescale tests. In the 62 saved cell rows, maximum evaluated beta*dY/dM is 0.233710 versus a zero-determinant condition of one; no row is flagged bistable. The recovery-rate scenarios do not establish an aging clock or a near-bifurcation regime.

Reviewer overclaims were qualified: electrostatic double counting is not established by the supplied wrapper usage, orientation count does not uniquely explain CPU/GPU differences, and the saved entropy values are not strictly monotonic with stiffness. External literature suggestions remain leads. No scientific model parameters or source were changed.
