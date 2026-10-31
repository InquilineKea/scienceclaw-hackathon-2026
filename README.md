# ScienceClaw Hackathon 2026: Oxidative Tensegrity

Work from the MIT Media Lab ScienceClaw hackathon (30 Oct – 1 Nov 2026). One question, followed from chemical bonds
to the heart: **what happens to tissue when oxidative crosslinks pile up on a healthy, enzymatically crosslinked
collagen matrix?**

- **Animated explainer:** https://claude.ai/artifact/XRqknQjNYtbutcWtrwpX31 (the self-contained page is also in
  `oxidative-tensegrity/viz/oxidative-tensegrity.html`)
- **AI peer review of the project blog:** https://humanavianaisymbiosis.wordpress.com/2026/10/31/agent-critiques-five-ai-reviewers-read-every-post-on-this-blog/
- **Blog:** https://humanavianaisymbiosis.wordpress.com/

## Complete collagen archives and separate run storage

The [archive index](ARCHIVE_INDEX.md) links the frozen 450-run network atlas, corrected diagrams and animations, completed H100 molecular results, MACE-OFF/MACE-MP comparison, failed/successful job logs, and the recovered GROMACS trajectories. [File checksums](ARCHIVE_MANIFEST.json) cover the added deliverables.

Future atlas runs now create separate timestamped folders with source snapshots and logs. Existing run names are rejected. These results retain their scientific limits: hypothetical network mechanics and molecular proxy calculations do not establish validated tissue toughness or native crosslink reactions.

## What is here

| Path (under `oxidative-tensegrity/`) | What it is |
|---|---|
| `oxt/` | The model: fibre network with rupture (`network.py`), collagen I/IV/VII, crosslink chemistries and tissues (`materials.py`), motor-clutch + 6-strut tensegrity cell + YAP + recovery rate (`cell.py`), transport, heart, artery (`physio.py`), GAG sliding models (`gag.py`) |
| `run_sweep.py`, `run_gag.py`, `make_figures.py` | Sweeps (laptop, 32-vCPU, GPU profiles) and figures |
| `results/cpu32/` | Main results: 16×16 networks, 4 seeds, 8 branching values, 5 ages (GCP 32 vCPU), GAG cyclic loading, figures |
| `alchemi_crosslinks.py`, `alchemi_collagen_gag.py`, `results/alchemi_*` | NVIDIA ALCHEMI: crosslink stretch scans (MACE) and collagen–GAG contact energies (AIMNet2), CPU and Brev L4 |
| `HYPOTHESES_EWALD.md` | Eight testable hypotheses in the spirit of Colin Ewald's matrisome work, with ScienceClaw swarm verdicts |
| `swarm/` | ScienceClaw agent-swarm runner (Gemini, dry-run, isolated container), topics, round summaries |
| `agents/` | Critic swarms: `blog_critic.py` (five Gemini reviewers over a WordPress site), `critic_swarm.py` (results critics) |
| `remote/` | GCP, Brev and Nebius job scripts, LAMMPS decks |
| `viz/` | The explainer page, its template and the data export |
| `SECURITY-REVIEW.md` | Pre-execution reviews of ALCHEMI and ScienceClaw, and what was run where |
| `AGENTS.md`, `CODEX_HANDOFF.md` | Shared context and runbook for Codex / Claude Code agents |
| `tests/` | Hardware-free checks (analytic lattice moduli, tensegrity, transport, heart, LAMMPS export) |

## Main findings (model outputs, not measurements)

- Branching factor dominates network stiffness (~260× from z = 2.8 to 5). Oxidative crosslinks stiffen sparse,
  sub-isostatic networks most (~14×) and erase strain-stiffening (6–15× → ~3×).
- Anisotropic crosslinks make tissue directionally stiff (Cx/Cy up to 3.6); collagen I keeps its strength but fails at
  less than half the strain; collagen VII gets stronger and tougher but less extensible.
- A tensegrity cell on healthy collagen VII cannot hold its prestress (14%) and YAP stays cytoplasmic; recovery of
  the YAP–myosin loop slows at the mechanosensing threshold.
- With sliding GAGs, crosslinks raise stiffness ~6× while cutting dissipated energy per cycle from ~0.55 to 0.02–0.10;
  only the sliding model matches tendon GAG-removal data.
- ALCHEMI + AIMNet2: methylglyoxal-glycated arginine (MG-H1) loses contact with dermatan sulfate; CML-lysine does not.
- ALCHEMI crosslink stretch scans, converged on a Brev L4 with two independent potentials (MACE-OFF, MACE-MP): the
  models disagree up to ~6× (rank correlation 0.48); robust only where they agree: dityrosine is the stiffest
  linkage, glucosepane is no stiffer than the healthy enzymatic crosslink, TG2 isopeptide is soft.

Limits: 2D, small networks; parameters are literature-informed assumptions; atomistic numbers are rigid-fragment
contact energies; agent-swarm syntheses are leads, not evidence. Details in `oxidative-tensegrity/README.md`.

## Run it

```bash
cd oxidative-tensegrity
python3 -m pytest -q tests
python3 run_sweep.py --profile smoke
python3 make_figures.py --results results/smoke
```

Dependencies: numpy, scipy, pandas, matplotlib, torch (CPU is fine). GPU, ALCHEMI and ScienceClaw steps run only in
isolated containers or disposable VMs; see `SECURITY-REVIEW.md` before running any of them.

## Compute used

MacBook (Python/SciPy/PyTorch), Google Cloud 32-vCPU VM, NVIDIA Brev L4 with ALCHEMI, Docker sandboxes, Gemini via
Google AI Studio (ScienceClaw swarms and critic swarms). Built with Claude Code, coordinated with Codex.
