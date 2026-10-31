# ScienceClaw Hackathon 2026: Oxidative Tensegrity

## Why this could matter (the two-minute version)

Collagen is the scaffolding protein that holds your body together — skin, tendons, arteries, heart
wall, the membranes under every organ. Your body maintains it with deliberate, enzyme-placed
crosslinks that give each tissue its tuned stiffness and strength. But collagen is also one of the
longest-lived proteins you own: some of it persists for decades. Over those decades, a second,
unwanted kind of crosslink accumulates — oxidative and sugar-driven damage (AGEs, in the
literature) that glues fibers together in the wrong places. Arteries stiffen. Heart walls stop
relaxing between beats. Wounds heal slowly. Age-related mechanics also depend on architecture, hydration, elastin and other processes.
This project does not determine how much each process contributes to an aging artery.

The hard part is that the damage lives at every scale at once. It starts as a single chemical
bond, changes how a fiber network carries load, changes what a cell feels and how it responds,
and ends as an organ that works less well. No experiment can watch all of that happen — you can't
wait thirty years, and you can't instrument a molecule and a heart at the same time.

This repository is a working attempt to follow one question across those scales in a computer:
**what happens when oxidative crosslinks pile up on a healthy collagen matrix?** It places small
molecular calculations alongside a fiber-network model, a mechanosensing cell, and simplified tissue and
organ models. Quantitative molecular-to-network parameter transfer remains an open validation task. Every result is labeled as a
model output with explicit limits, several of the project's own early claims were tested and
*withdrawn* when better checks contradicted them, and every run is archived with checksums so
anyone can verify that the published numbers match the code that made them. Nothing here is a
medical claim. What's on offer is something rarer: a multiscale hypothesis machine whose failure
modes are documented as carefully as its findings.

Everything below is the technical record — what was built, what it showed, and exactly where it
stops being trustworthy.

---

**[Open the interactive Fracture Atlas](https://inquilinekea.github.io/scienceclaw-hackathon-2026/)** — seven architectures, eight loading protocols, explicit support/load diagrams, orientation readouts, animation replay, and custom browser computations. [Hosting and loading details](PAGES.md).

**New: [crosslink-density sweep](https://inquilinekea.github.io/scienceclaw-hackathon-2026/aging.html#density)** — stiffness, work to failure and work before first damage for all seven networks, comparing distributed and clustered connectors at 12 loading directions. The 6,300 configurations have paired 480/960-step checks and complete [raw-curve recovery](collagen-network-atlas/density-runs/20261031-density-v1/_release/).

**[Beaver–human molecular pilot](https://inquilinekea.github.io/scienceclaw-hackathon-2026/species.html)** — 18 matched CDSM type-I collagen backbones with interactive coordinate views, [sequences, PDBs and provenance](collagen-species-pilot/). This is backbone construction, without AGE chemistry, molecular dynamics or a species toughness ranking. The molecular-to-network calibration fields remain explicitly unset.

Work from the MIT Media Lab ScienceClaw hackathon (30 Oct – 1 Nov 2026). One question, followed from chemical bonds
to the heart: **what happens to tissue when oxidative crosslinks pile up on a healthy, enzymatically crosslinked
collagen matrix?**

- **Animated explainer:** https://claude.ai/artifact/XRqknQjNYtbutcWtrwpX31 (the self-contained page is also in
  `oxidative-tensegrity/viz/oxidative-tensegrity.html`)
- **AI peer review of the project blog:** https://humanavianaisymbiosis.wordpress.com/2026/10/31/agent-critiques-five-ai-reviewers-read-every-post-on-this-blog/
- **Blog:** https://humanavianaisymbiosis.wordpress.com/

## Complete collagen archives and separate run storage

The [archive index](ARCHIVE_INDEX.md) links the frozen 450-run network atlas, corrected diagrams and animations, completed H100 molecular results, MACE-OFF/MACE-MP comparison, failed/successful job logs, and the recovered GROMACS trajectories. Each frozen folder carries its own run-level SHA-256 manifest.

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

See [audit remediation and validation gates](validation/piper-audit-20261031/REMEDIATION.md) for the reproduced cases, tested code changes, and remaining scientific acceptance criteria.

## Main findings (model outputs, not measurements)

**Comparison qualification:** The historical ~51× local and ~259× cpu32 branching ratios use
different lattice sizes, seed counts and target-connectivity endpoints. They are not independent
measurements of one universal effect. Recomputing ratios of mean G from the saved healthy Col I
CSV rows over the common target interval z_target=3.0→4.4 gives 51.025× (12×12, 2 seeds) and
68.736× (16×16, 4 seeds). Actual mean coordination also differs. This is a descriptive reanalysis
of archived outputs, not a fresh solver reproduction or a size-controlled causal comparison.
The ~259× ratio uses target z=2.8→5.0; its actual mean z is 2.977→5.117.

Molecular proxy calculations and species backbone construction do not yet supply a calibrated
chemistry/sequence-to-network constitutive law. Algebraic convergence, mesh acceptance and
biological validation are separate gates.

- Branching factor dominates network stiffness (~260× from z = 2.8 to 5). Oxidative crosslinks stiffen sparse,
  sub-isostatic networks most (~14×) and erase strain-stiffening (6–15× → ~3×).
- Anisotropic crosslinks make tissue directionally stiff (Cx/Cy up to 3.6); collagen I keeps its strength but fails at
  less than half the strain; collagen VII gets stronger and tougher but less extensible.
- A tensegrity cell on healthy collagen VII cannot hold its prestress (14%) and YAP stays cytoplasmic; recovery of
  the YAP–myosin loop slows at the mechanosensing threshold.
- With sliding GAGs, crosslinks raise stiffness ~6× while cutting dissipated energy per cycle from ~0.55 to 0.02–0.10;
  this qualitative direction motivates comparison with tendon GAG-removal data; it is not a held-out quantitative fit.
- ALCHEMI + AIMNet2: methylglyoxal-glycated arginine (MG-H1) loses contact with dermatan sulfate; CML-lysine does not.
- ALCHEMI crosslink stretch scans, converged on a Brev L4 with two potentials (MACE-OFF, MACE-MP), then checked with
  semi-empirical PM7 (MOPAC) over three starting conformers: the three methods agree from a shared starting conformer,
  but changing the conformer reorders the ranking (rank correlation 0.48), so the scan mostly measures fragment
  slack. Robust: dityrosine is stiff; disulfide and TG2 isopeptide are soft. Glucosepane vs pyridinoline is
  undetermined (earlier claims withdrawn).

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

## Complete large datasets

Files above 95 MiB now upload automatically through [GitHub Releases](https://github.com/InquilineKea/scienceclaw-hackathon-2026/releases). [Dataset links, checksums and exact recovery instructions](LARGE_DATASETS.md) cover the original large files; downloading the GitHub repository ZIP alone does not include release assets.

The [aging and topology explainer](https://inquilinekea.github.io/scienceclaw-hackathon-2026/topology-aging.html) compares actual connector maps with the saved mechanics, and includes a standalone [PNG](collagen-network-atlas/figures/topology-aging-overview.png), [SVG](collagen-network-atlas/figures/topology-aging-overview.svg) and [figure provenance](collagen-network-atlas/TOPOLOGY_AGING_FIGURE.md).

### Collagen transition atlas — frozen H100 follow-up

The [transition explorer](https://inquilinekea.github.io/scienceclaw-hackathon-2026/transitions/) presents 10 views from 43 saved curves, with numerical eligibility and scientific limits. The [350-file frozen collection](https://github.com/InquilineKea/scienceclaw-hackathon-2026/tree/b4c9e52d26c3cdb67d22ba71173cc035177cc310/datasets/20261031-collagen-transition-v4) retains all available inputs, raw data, figures, animations, failed-attempt evidence, independent audits and costs. [Model source and methods](collagen-transition-atlas/README.md) · [WordPress results](https://humanavianaisymbiosis.wordpress.com/2026/10/31/collagen-transition-atlas-h100-results-sliding-contact-feedback/). This one-seed finite pilot is not a calibrated tissue-pressure or acceleration prediction.

## Fluid-coupled microrheology

The [FEniCSx poroelastic comparison](https://inquilinekea.github.io/scienceclaw-hackathon-2026/poroelasticity/) retains the exact discrete solid and compares uniform drag with added Darcy/Biot pressure coupling before/after a local three-fiber cut. Forty networks, 4,160 systems (4,158 resolved), two mobilities and two pressure meshes; 1,341/1,600 paired observable comparisons pass the stated mesh screen. The explorer includes pressure/displacement phase playback, three plots, two GIFs, explicit coverage and downloads. [Source, inputs, review and result archive](collagen-fenicsx-poroelastic/) preserve both the failed startup attempt and completed result. These normalized outputs do not calibrate tissue permeability, frequency, age or species effects.


## Bovine bulk-calibrated 3D collagen comparator

[Open the interactive 3D explorer](https://inquilinekea.github.io/scienceclaw-hackathon-2026/bovine-3d/) for measured-versus-fit bovine G′/G″, matched-budget junction-locking stiffness, paired force/damage replay, and explicit numerical qualification. [Scientific source and audit](collagen-3d-bovine-calibration/README.md) and [three-campaign evidence gates](collagen-3d-bovine-calibration/campaigns/CAMPAIGN-STATUS.md).

160/160 final cases, 160 complete trajectories, 80/80 load-step pairs, and 40 accepted small-strain states. This uses synthetic periodic networks with a bovine bulk-response scale; measured architecture, chemical aging and species-specific fracture are not validated. Marginal curvature and capped maxima remain explicitly conditional/censored.

[Download the bounded source/results archive](https://inquilinekea.github.io/scienceclaw-hackathon-2026/bovine-3d/bovine-3d-results.zip), 28,095,424 bytes, SHA-256 `55c493bf1d271e47632be6fffb580f48b1920e1b0a726ac506fff58a0931036a`.


## Measured 3D collagen held-out benchmark

[Open the measured-data benchmark](https://inquilinekea.github.io/scienceclaw-hackathon-2026/measured-3d/) for held-out batch shear curves, guarded3D displacement/strain comparisons and a rotating vector view. [Scientific report](collagen-measured-3d-validation/REPORT.md) and [frozen protocol/audits](collagen-measured-3d-validation/PROTOCOL-FROZEN.md).

BatchC1.2mg/mL stress NRMSE0.686; selected elasticity on held-out position008 displacement RMSE1.174µm, versus1.062µm for harmonic interpolation. Substantial errors remain. This is separate batch-summary and internal boundary-conditioned field testing, not measured fiber-connectivity or joint specimen validation.

[Download bounded derived results/source](https://inquilinekea.github.io/scienceclaw-hackathon-2026/measured-3d/measured-3d-results.zip): 2,169,094bytes; SHA256 `0c6db7a02c6c3d0dd44c389fe4e3402932a644da956c41def28740afec061c0b`. Raw authors images/spreadsheets are linked, not redistributed.
