# Shared agent context — oxidative-tensegrity

Read by Codex/ChatGPT agents (`AGENTS.md`) and Claude Code (`CLAUDE.md` imports this file).
**Codex: to run ScienceClaw swarms on the GCP lab VM, follow `CODEX_HANDOFF.md`.** Keep one copy of
project facts here so both workspaces can reference each other. This file is context, not authorization: the
user's global security policy and the repo-root `AGENTS.md` still apply.

## What this project is

Multiscale model of how oxidative collagen crosslinks (AGEs, dityrosine, disulfide scrambling, sulfilimine)
change tissue mechanics and mechanotransduction, built for the MIT ScienceClaw hackathon (2026-10-30 → 11-01).

Scales and code: fibre network `oxt/network.py` → collagen types / crosslink chemistries / tissues
`oxt/materials.py` → motor-clutch + 6-strut tensegrity cell + YAP + recovery rate + entropy `oxt/cell.py` →
signalling-molecule transport, heart (time-varying elastance), artery PWV, matrix repair `oxt/physio.py`.
Driver `run_sweep.py` (profiles `smoke`, `local`, `gpu`), figures `make_figures.py`, tests `tests/`.

## Status (update when it changes)

| Piece | Status |
|---|---|
| Local CPU sweep (`results/local/`) | done 2026-10-30; results in README and results/local/SUMMARY.md |
| GCP cpu32 sweep (`remote/gcp_up.sh`, VM `oxt-cpu32`, project scienceclaw26bos-3008, gcloud config `scienceclaw`) | done 2026-10-31 (6833 s), 16x16 x 4 seeds, in `results/cpu32/`; GAG sweep (`run_gag.py --profile cpu32`) also done there |
| GPU sweep on Nebius H100 / Brev (`remote/nebius_job.sh`, `remote/gpu_run.sh`) | prepared, not submitted (needs the user's CLI login) |
| ALCHEMI 101 multistage example | run 2026-10-30 in an isolated Docker container (CPU), exit 0 |
| ALCHEMI atomistic crosslink scan (`alchemi_crosslinks.py`) | CPU pilot in `results/alchemi_pilot/`; completed two-model results in `results/alchemi_brev/`; source-checked comparison in `swarm/CODEX_FOLLOWUP_20261031.md` |
| Phase map: z × LOX locking × AGE dose (`run_phase.py`, `analyze_phase.py`, `analyze_fss.py`) | done 2026-10-31 on GCP: W=12 map (4 seeds) + 8-seed follow-up + W=16 stiffness check; `results/phase/`, README section "Phase map" |
| PM7 tie-breaker + conformer check (`pm7_crosslinks.py`, `remote/brev_pm7.sh`, MOPAC 23.2.5) | done 2026-10-31 on Brev L4 (CPU, no-network container), 504 optimisations, 0 failed; `results/alchemi_brev/crosslink_pm7.json`, `crosslink_model_comparison.md` |
| LAMMPS viscoelastic stage (`remote/lammps/`) | CPU commissioning done2026-10-31 on existing GCP:41/41 checks, independent energy/force/stress/equilibrium and undriven energy accounting, two uniform driven trajectories; six material presets checked at W8/W32 and W32 inputs regenerated. Exact single-rank CPU angular callback and synchronized sampling required; bare lmp unsupported. Full six-system rheology sweep not run; GPU implementation not validated. See `remote/lammps/CPU_VALIDATION_20261031.md`. No new VM or paid GPU job. |
| Token Factory critic swarm (`agents/critic_swarm.py`) | prepared, not run (needs `NEBIUS_API_KEY` set by the user) |
| ScienceClaw literature swarm (`swarm/`, Gemini, dry-run, Docker `sclaw`) | two rounds done 2026-10-31 (commit 894598c, user-approved); summaries in `swarm/SUMMARY.md` and `HYPOTHESES_EWALD.md`, raw logs local only |
| Graph audit and largest-size controls (Codex, GCP) | done2026-10-31;336 exact graph reconstructions,384 new mechanical controls, all converged;96/96 fine-step case comparisons pass .01pp tolerance;3 specialist+1 adversarial Gemini4Argon critique, source checks include transient-rate differences. Same old graph seeds; dimensionless linear model only. Curated `swarm/CODEX_GRAPH_AUDIT_CONTROLS_20261031.md`. Published GitHub dd6ffe8bd38b05f7c1fd3d262d282c3f33e3adbb and WordPress post258 under Agent Critiques, Collagen & ECM Aging, ScienceClaw Hackathon. Remote107blob checks and exact saved/public WordPress readback passed. No new VM/package; shared GCP retained running. |
| Controlled topology CPU sweeps and Argon review (Codex, GCP) | done 2026-10-31; 1,344 production + 400 control/refinement cases, eight benchmark cases; six specialist + two adversarial Gemini 4 Argon reviews. Distinct dimensionless linearized model, not nonlinear H100 replication or collagen MD. Curated `swarm/CODEX_CONTROLLED_TOPOLOGY_20261031.md`. Published GitHub commit a02164fcf2e7a82363a334557b7be8c99394734b and WordPress post235 under Agent Critiques, Collagen & ECM Aging, ScienceClaw Hackathon; exact saved-content/public-page and remote blob checks passed. No new VM; shared GCP retained running. |
| Gemini source critique (Codex, original API-only workers on GCP) | done 2026-10-31; 8 reviewer reports, 12 API requests including 4 targeted reruns; covers this model and collagen-scaffold-lab. Curated findings in `swarm/CODEX_CRITIQUE_20261031.md`; raw records local only in `swarm/work/codex_gemini_20261031/`. ScienceClaw not executed for this pass. |
| Gemini focused H5/H8/B1 follow-up (Codex, GCP API-only) | done 2026-10-31; 6 reviewers, 6 API calls, 23 raw observations; source-checked synthesis `swarm/CODEX_FOLLOWUP_20261031.md`; published under Agent Critiques, Collagen & ECM Aging, ScienceClaw Hackathon. |
| Levin-lens + open-endedness critique (Claude Code, GCP API-only, `gemini-4-argon`) | done 2026-10-31; 4 reviewers + 1 adversarial, 5 API calls, 331k tokens; every citation web-checked. Curated `swarm/LEVIN_LENS_CRITIQUE_20261031.md`; personas/runner `swarm/levin_lens/`; raw records local only in `swarm/work/levin_lens_20261031/`. Found organoid issues: remodelling cannot change K/G0 (`shifted_curves`), no crosslink MMP resistance, uncoupled positions (an `exp(logS)` windup it found was fixed separately). No model code changed; not published. |
| Agent team on one benchmark (Claude Code; `team/team.py`, `team/jobs.py`) | running 2026-10-31 on GCP `oxt-cpu32` (user `oxt`, venv `~/v`, separate dir `~/team-20261031`; no installs) with Vertex `gemini-3.6-flash` via the `scienceclaw` gcloud login (no API key). Question: does clustered AGE crosslinking cut damage tolerance by blocking sliding, concentrating load, or hydration? Architecture / sliding / hydration / molecular-evidence / validator agents only choose whitelisted solver jobs; code adjudicates paired clustered-vs-dispersed seeds and registers `team-*` experiments here, verifying only when a different calculation (autograd linear-response G, closed-form fibril limits) agrees AND a validator falsification rerun keeps the verdict. Also re-checks the phase map G by linear response (first point: 0.9% agreement). Output `team/runs/<stamp>/REPORT.md`. |
| Bioelectric ageing test (Claude Code; new `oxt/bioelectric.py`, `run_bioelectric.py`, `tests/test_bioelectric.py`) | done 2026-10-31 on Nebius H100 `bioelectric-ageing-h100-20261031` via Brev (pinned PyTorch image, no network, no installs; 41 min; stopped, disk kept). Results `results/bioelectric/gpu/`. Depolarisation is built in; Vmem Moran's I rises with crosslinking (opposite to senescent keratinocytes); 0/108 sets match all four signs; spatially correlated stiffness nucleates switching; pattern memory depends on prestress-gated junctions and net restoration is ~0. Critique: 4 Gemini calls, source-checked, appended to `swarm/LEVIN_LENS_CRITIQUE_20261031.md`. Not published. |

## Brev job queue (Codex: pick these up on Brev)

Claude Code now drives Brev from this Mac (org NCA-f3c7-49497, L4 `collagen-md-20261031`, kept running at the user's request). Other sessions: claim a job by writing your name
and the Brev instance in **Claimed by**, run it on a fresh Brev GPU instance (not the user's Mac), copy the
outputs back into this folder at the listed path, then set **Status** and add one line under Findings.
Do not run on the instance anything not listed here without the user's say-so.

| ID | Job | Command (on the Brev box, from this folder) | Outputs to bring back | Claimed by | Status |
|---|---|---|---|---|---|
| B1 | Converged ALCHEMI crosslink scan, two independent MLIPs | `ALCHEMI_COMMIT=84fe8e8fb8fab54863eea8f138722c7ab434966a RUN_ALCHEMI=1 bash remote/gpu_run.sh` (does B1 then B2) | `results/alchemi_brev/crosslink_mace_off.json`, `crosslink_mace_mp.json` | Claude Code, Brev L4 | done |
| B2 | Large network/tissue/cell sweep (48x48, 8 seeds) | same command as B1 (runs after it), or `python run_sweep.py --profile gpu --device cuda` | `results/gpu/` | — | open |
| B3 | LAMMPS reduced-network oscillatory shear CPU reference | `python -m oxt.lammps_export remote/lammps/colI_none.in` in reviewed isolated CPU runtime; explicit material stem required, no wildcard/bare lmp | `remote/lammps/*_stress.txt` | Codex, existing GCP CPU commissioning | CPU validation41/41done; complete six-system rheology production remains open; GPU blocked pending native exact-angle validation and explicit bounded authorization |
| B4 | GAG models × crosslinks under cyclic load (bridge / sliding / polyelectrolyte), 40x40, 8 seeds | `python run_gag.py --profile gpu --device cuda` | `results/gpu/gag.csv`, `gag_summary.csv` | — | open (12x12 version done on GCP: `results/cpu32/gag*.csv`) |
| B5 | Collagen–GAG interface vs glycation (Lys/Arg vs CML/MG-H1 × DS 0/1/2 sulfates), AIMNet2 via ALCHEMI | in the ALCHEMI venv plus `aimnet==0.2.5`: `python alchemi_collagen_gag.py --device cuda --orient 24` | `results/alchemi_gag/collagen_gag_brev_L4.json` | Claude Code, Brev L4 | done |
| B7 | Collagen network → organoid gene expression (156 Col I/IV gels: z × crosslinker × dose × alignment → motor-clutch/tensegrity YAP → 7-day organoid growth + YAP/MRTF/Wnt gene network) | `bash remote/brev_organoid.sh gpu` (`run_organoid.py`, `oxt/organoid.py`) | `results/organoid/gpu/` | Claude Code, Brev A6000 `organoid-a6000-20261031` (SSH via direct IP port 22; Brev gateway ports timed out 2026-10-31) | running |
| B6 | Fibril scale: ColBuilder + Martini 3 Col I fibril, PYD/HLKNL vs added crosslinks, GROMACS tension (Gräter group tools) | **needs a security review and user approval first** (ColBuilder, GROMACS, Martini topologies not yet reviewed) | proposal only | — | blocked |

Context for B4–B6: a ChatGPT session proposed testing whether added crosslinking stiffens a network yet costs it
resilience by blocking GAG-mediated fibril sliding (tendon GAG removal changes stress relaxation more than modulus).
B4 is that test at network scale; B5 asks whether glycation of GAG-binding Lys/Arg weakens the interface itself.
CPU pilots of B4 (GCP, 12x12) and B5 (Docker CPU, 6 orientations) are in `results/cpu32/` and `results/alchemi_gag/`.

Notes for B1: `alchemi_crosslinks.py` works around two ALCHEMI 0.3.0-rc issues (local MACE checkpoints, float64
positions); see `SECURITY-REVIEW.md`. A CPU pilot is in `results/alchemi_pilot/` for comparison; it was not
converged. If the two MLIPs disagree by >30% on a chemistry's `k_rel`, report it rather than averaging.

Findings from Brev jobs:
- B1 (source correction, Codex follow-up): completed initial relaxations reach fmax ≈ 0.02 eV/Å. Normalized stiffness differs 5.60× for HLNL and 5.77× for sulfilimine. Dityrosine is above the reference in both models but is not stiffest in MACE-OFF (HLNL 16.29 vs dityrosine 4.31). Glucosepane is 1.04× reference in OFF versus 1.55× in MP. Boundary minima affect OFF sulfilimine and the MP pyridinoline reference; inspect scans before quantitative interpretation. Not fed into the network model.
- B1 PM7 check (Claude Code): PM7 matches both MACE models on peak force from the shared seed-7 conformer (Spearman 0.95–0.98), but PM7 from two other conformers gives 0.48 against seed 7, and k_rel disagrees everywhere (0.40–0.48). The scan measures conformer slack. Robust: dityrosine stiff; disulfide and TG2 soft. Glucosepane vs pyridinoline, HLNL, pentosidine, sulfilimine: undetermined. Next: ≥20-conformer ensembles or pre-extended fragments.
- Phase map (Claude Code, GCP, not a Brev job): healthy Col I is connected above z ≈ 2.4, rigid by bending from ≈ 3.0, stretching-dominated above ≈ 3.9 (G extrapolates to 0 at 3.8–3.9), and brittle (avalanche > 5% of bonds) above ≈ 5. Strength and extensibility trade off at roughly constant work to peak; the 4-seed "optimum at 3.5" did not survive 12 seeds. AGE dose 1 at matched z: G 2–3× higher, ε_peak 10–35% lower, useful window shifts from 3.5–3.8 to 3.2–3.55. LOX locking stiffens only below z ≈ 4.
- B5: MG-H1-Arg is the weakest dermatan-sulfate binder and loses contact (4.0–4.5 Å); Arg > Lys; CML-Lys stays bound. Magnitudes shift ~0.5 eV between CPU and L4 runs (RDKit conformers differ by architecture), so average over conformers next.

- Codex separate MD follow-up: completed 6×20-ps explicit-solvent PYD/DPD collagen-coupon stability tests on `collagen-crosslink-followup-20261031` L4. All runtime/platform/final geometry checks passed; 90 remote file hashes verified. New VM stopped after retrieval, disk retained; other jobs untouched. This is not an AGE/oxidative stiffness ranking, reaction simulation or B6 completion. Report: `swarm/CODEX_MD_PILOT_20261031.md`; full local package: `/Users/simfish/Documents/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs/collagen-md-followup-20261031`.

- Codex glucosepane/dityrosine follow-up: completed 12 accepted 50-ps linked/control trajectories (600 ps total; 30-ps free tail each) using published Amber99 glucosepane and CHARMM/CGenFF DITY data in distinct local collagen contexts. All dry/wet/runtime/final readback checks passed; 199 raw-file hashes verified. One complete double run retained, an interrupted 21-ps diagnostic preserved, remaining integrations mixed; original one-hour deadline retained (23.094 min total execution window). Task L4 stopped, disk retained. Report `swarm/CODEX_CANDIDATE_COMPARISON_20261031.md`; full local package `/Users/simfish/Documents/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs/collagen-glucosepane-dityrosine-20261031`. No cross-chemistry mechanical ranking, full-fibril/B6 completion or reaction calculation is claimed. The bounded scientific snapshot and report were subsequently published; see the publication record below.

- Codex publication verified 2026-10-31: both Gemini review packets, six-run PYD/DPD data and twelve-run glucosepane/dityrosine data are public on `claude/oxidative-tensegrity` at commit `81e160606351a48557e4a2b91bc9296115a0d9aa` (481 added files, all remote blob identities/sizes matched). WordPress posts 121, 140, 163 and 164 have all three requested categories. New MD posts passed exact saved-content/public-page readback. Publication links and scope: `swarm/CODEX_PUBLICATION_20261031.md`.

- Codex Argon follow-up verified 2026-10-31: eight Gemini 4 Argon high-reasoning specialists plus two adversarial reviews (10 requests, 447,460 tokens; estimated token cost $1.878712) critique the completed candidate MD and design topology/regime tests. Source-checked report `swarm/CODEX_ARGON_REVIEW_20261031.md`, proposed campaign `swarm/CODEX_NEXT_SIMULATIONS_20261031.md`. Published as WordPress post 173 in all three requested categories and Git commit `0ea00f4f98dd855684524f2ceca2befa8829b66a` (140 added review files plus index update, all remote hashes/sizes matched). Independent line-cycle enumeration finds 2W cycles and expected pre-bridge factor 1-2/(3W), differing from the builder correction; realized z is already recorded. No new MD/QM/network sweep or closed-loop controller ran; code and physical-model changes remain recommendations.

## Cross-workspace links

- Claude Code workspace: this folder, plus `../quotient-swarm/` (multi-agent swarm prototype for the same
  hackathon) and `../collagen-scaffold-lab/` (affine strut-lattice scaffold app, different model).
- ChatGPT / Codex workflow: runs on Brev (per the user, 2026-10-31); its location is not visible from this Mac.
  Codex: record your workspace path or repo here, and use the Brev job queue above.
- Cross-agent memory bridge: a pending proposal from `claude-code` describes this project; it becomes shared
  context only after the user approves it.

## Junction-angle organoid hypothesis (Codex, 2026-10-31)

User requested this new experiment and publication, then explicitly requested a new Nebius H100. Dedicated package: `experiments/junction-angle-20261031/`. Completed 36 CPU mechanics cases in an isolated offline container on existing `collagen-md-l40s-20261031`; all accepted, raw outputs retrieved and hashes matched. Broadening achieved junction-angle SD slightly reduces interface-force CV for weak/free angular constraints and increases it for stronger constraints. This is a high-connectivity 2D scaffold sensitivity result, not isolated angle causality or gene-expression validation. See BASELINE_REPORT.md.

Published hypothesis post 183 under newly created Hypotheses category 116122; exact block content/status/category readback passed. URL in package README. Provisioned separate Nebius H100 `junction-organoid-h100-20261031` (ad5wiru1z), advertised $5.40/h plus disk; hardware verified H100 80GB. Original CUDA 144-case size/seed sweep submitted under `~/junction-angle-h100-20261031`, container `junction-angle-cuda-20261031`; final execution status/results tracked in package H100-EXECUTION.md. No other instances stopped or modified; new instance retained for hackathon use.

H100 completion: 144/144 cases accepted; CUDA runtime 13.75 s, container exit 0. Five raw output hashes verified, independent CPU/GPU force CV agreement within 6.96e-9 on all 36 shared cases. Eight-seed/size extension shows mixed small-network signs and positive larger-network mean effects; the initial four-seed sign pattern is not robust across size/seeds. Read `experiments/junction-angle-20261031/H100-RESULTS.md` before citing results. H100 retained for hackathon use.

## Controlled geometry and spatial signaling

Controlled-geometry and spatial-signaling follow-up (Codex, user-authorized 2026-10-31): completed on the same retained Nebius H100. First generator 0/16 geometry pairs passed; subsequent pairwise geometry-only optimization achieved 16/16 with unchanged matching gates. 384 mechanics cases total across two campaigns, all numerically accepted; 192 in successful follow-up. Broad-minus-narrow mean force CV is negative in all six size/lock settings, reversing the prior larger unmatched pilot's direction. A one-way, uncalibrated YAP/Hill gene-activity surrogate connects each spatial field to CCN1/CCN2/ANKRD1; mean-force, homogenization, permutation and YAP-off controls plus dt-halving passed. Gene-effect signs vary across assumed response parameters. No measured RNA, fitted fold changes, full cell tensegrity or living-organoid model. Read `experiments/junction-angle-20261031/controlled/REPORT.md` and frozen/adaptive protocols before interpreting. All 21 initial and 22 follow-up output hashes verified. Published post 192 under Simulation Results, Collagen & ECM Aging, ScienceClaw Hackathon; exact saved-content and public-page readback passed. Article link in controlled/PUBLICATION.json. Instance retained; workloads exited.

## Experiment registry (all agents: use this before running anything)

`experiments/registry.db` (SQLite) is the single registry of experiments for this project; CLI is
`python experiments/registry.py` (stdlib only, from this folder):

```bash
python experiments/registry.py list                                   # check before you start
python experiments/registry.py add --id my-exp --hypothesis "..." \
    --calc "original solver/calculation" --params '{"seed": 7}' --seeds '[0,1]'
python experiments/registry.py claim my-exp --by "Agent, machine"     # avoid duplicated work
python experiments/registry.py claim my-exp --by "Agent, machine" --status running|done
python experiments/registry.py verify my-exp --verifier "PM7 (MOPAC 23.2.5)" \
    --method "what the separate calculation verified (and what it did not)" --by "Agent"
python experiments/registry.py refute my-exp --reason "negative result" --by "Agent"
python experiments/registry.py show my-exp
```

Rules: register and claim before running so no two sessions duplicate a calculation; record
negative results with `refute`. A finding only becomes reusable when a **different
calculation/solver** verifies it — `verify` refuses unless `params["calculation"]` names the
original solver and `--verifier` is distinct from it; several agents agreeing is not verification.
Pre-registry runs (cpu32 sweep, phase map, PM7 tie-breaker, B1, B5, junction-angle 2D/H100/3D,
controlled-geometry, setpoint_vs_scar, bioelectric, glucosepane/dityrosine MD, TOPO_OPT) were
backfilled 2026-10-31 by `experiments/backfill_registry.py` (13 entries: 9 unvalidated,
3 independently_verified, 1 refuted) with validation_status set honestly from the recorded
evidence — see `python experiments/registry.py list`.

## Rules for any agent working here

3D follow-up (Codex, 2026-10-31): completed on the retained Nebius H100. Package
`experiments/junction-angle-20261031/three-d/`. Primary periodic Voronoi shear
grid: 10 seeds, requested z3.0–4.0, 21 positive strains plus zero; refined run
2351/2420 states accepted, including 110 zero controls; 80/110 accepted at 50%
shear. Finite-bending operational onset is not a true critical strain or a
Sharma scaling reproduction. Independent CPU/GPU energy and finite-difference
stress checks passed; low-strain stress changed <=0.00275% on tighter tolerance.
Separate finite cavity/anchoring pilot: 8/8 angle pairs matched, 126/144 mechanics
accepted. All 18 failures are seed30/parent-z3.2; a gradual-ramp diagnostic did
not rescue convergence and was stopped. Complete-case mean force-CV differences
are negative in 11/12 settings but every setting has mixed seed signs. Gene
directions are conditional and can differ from the earlier 2D setup. Compliant
anchors are VII-inspired architecture assumptions, not calibrated collagen-VII
properties. 79 remote file hashes and archive hash verified. Article post215
published under Simulation Results, Collagen & ECM Aging, ScienceClaw Hackathon;
exact saved/public readback passed. Two standalone local explorers included.
Read REPORT.md, protocols and PUBLICATION.json before citing. GPU verified idle;
H100 instance retained running. No melting MD, clustering fracture or inclusion
compression campaign ran in this follow-up.

- ALCHEMI at commit 84fe8e8f is user-approved (2026-10-30) for isolated containers / disposable VMs only. Other
  third-party code (LAMMPS, Nebius/Brev CLIs) still needs approval; never run it on the host Mac.
- Never put API keys, tokens or credentials in this folder; the user sets `NEBIUS_API_KEY` in their shell.
- Parameters in `oxt/materials.py` are model assumptions, not measurements. Keep README claims to what the
  model shows; record negative or surprising results instead of tuning them away.
- When you change status or findings, update this file so the other workspace sees it.

## Dityrosine separated deformation and conditional transfer (Codex, 2026-10-31)

User-authorized campaign completed on retained `junction-organoid-h100-20261031`.
Package `experiments/dityrosine-transfer-20261031/`: 672/672 accepted isolated
N-telopeptide ALCHEMI/full-AIMNet2 deformation states, 48/48 references and 72/72
tighter checks. Same-family members 0/3, three prior trajectory replicas, four
correlated frames each. Separate stretch/rotation, finite prestress, no solvent
in current scans. 94/96 scalar fits pass; per-member/replica axial-rigidity
ratios .395–1.014 and angular ratios .745–1.283. No universal stiffening result.
Mixed deformation diagnostics limit the diagonal-law transfer; no full tensor,
thermal PMF, fibril law, collagen I/VII comparison or measured RNA claim.

All 36 conditional 3D transfer scenarios completed, 888 main contraction cases
and 888 small-contraction probes, 776 accepted in each. Baseline nonconvergence
retained plus one new main failure and one new probe failure. At parent-z3.8,
50% model-element exposure, mean-force matching, alpha=.5/F50=1, rotation-only
preserves negative broad-minus-narrow force CV in 6/6 molecular scenarios;
stretching-only and combined in 4/6 each. Mean YAP positive at this benchmark,
but mixed over the wider response grid; dimensionless gene scores are assumed
surrogate outputs. Adapter/gradient/batched/serial/time-step controls passed;
scientific registry remains unvalidated by an independent calculation.

Both evidence archive SHA256 checks and extraction path checks passed. Own
production containers exited 0; H100 retained, other agents' workloads untouched.
WordPress post271 published in Simulation Results, Collagen & ECM Aging,
ScienceClaw Hackathon; exact saved content and public substantive readback
passed, with newsletter email and social crosspost disabled. See REPORT.md,
PROTOCOL.md, SECURITY-REVIEW.md, PUBLICATION.json and FILES.sha256 before reuse.

## Active solvent/coupling extension (Codex, 2026-10-31)

Registry `dityrosine-solvent-coupled-3d-20261031` is running. User explicitly
requested coupled stretch/rotation, solvent, fully 3D network/YAP tests and
Avian publication, then asked how this changes older deformation results.
Package `experiments/dityrosine-solvent-coupled-3d-20261031/` contains the frozen
protocol and numerical amendments. Original H100 `junction-organoid-h100-20261031`
was resumed after inconsistent Brev states and is reserved for the active
ALCHEMI/network stages; it has completed 108/108 mixed molecular states and
696 coupled-transfer network cases (593 accepted). Dedicated solvent H100
`dity-solvent-coupled-h100-20261031` (`dowg8kpe1`, $5.42/h total advertised)
executes exact prior explicit-water CHARMM/CGenFF systems, with restored omitted
solute bond terms before releasing solute constraints. Initial wet references
failed the unchanged projected-force gate; failed/partial attempts are retained.
A constraint-projected FIRE refinement succeeded on test poses, and the complete
robust wet grid is running. No wet law or solvent-dependent YAP conclusion is
yet declared. The standalone explorer includes actual nonplanar 3D graph fields;
no fiber-director/torsional constitutive law or measured organoid RNA is claimed.

Latest verified status: the solvent instance now shows **Stopped** in Brev;
both task hosts timed out on SSH. No instance was restarted after this change.
The last observed wet checkpoint was 74/78 accepted deformation states; final
wet/thermal files have not been retrieved. Do not treat the supervisor or short
thermal diagnostic as completed. User was asked asynchronously whether the
stop was intentional; no answer at this checkpoint. Registry is not marked done.
The retrieved AIMNet/sensitivity archive was reanalyzed locally with original
stdlib code; common-seed full-coupled versus diagonal contrasts are saved in
`analysis-retrieved/common-seed-coupling-ablation.json`. Interim interpretation
post407 is published and verified, with no final hydrated-law claim. See
`PRIOR-RUN-INTERPRETATION.md` and `PUBLICATION.json`; subscriber email/social
crosspost disabled. The explorer explicitly labels its retrieved AIMNet subset.

### Completed recovery and rewrite (supersedes the checkpoint above)

The user subsequently authorized resuming both task H100s, rewriting the post,
and **stopping both after verification**. On recovery, all remaining work had
already completed before shutdown: wet 78/78 states, 6/6 references; short
thermal diagnostics 6/6, 60 ps total. No missing physics states were rerun.
All six wet mixed profiles failed transfer checks (energy/force disagreement
4.89–77.90 versus limit .25, all fit-window checks failed); 0/3 wet paired laws
are admissible. No wet network transfer or hydrated YAP survival is claimed.
Admissible vacuum AIMNet pairs 4/6; classical-dry 1/3. The combined completed
network phases have 1008 main states (865 accepted), 1008 probes (886 accepted).
These are repeated common-specimen conditions, not independent organoids.

Final network archive SHA256 233e6687ae5e45abae9d2dc9749292eb1b2f49ff0f6e83f489e506f223429f00;
solvent 2ef64128729937c984a6c695733399d57db13c02f34273f9f816b230dec4acd9.
Both retrieved/extracted with matching hashes and safe paths. Post407 was
rewritten at its existing permalink, preserving current research-context links
and categories; canonical raw-content and public substantive readback passed.
Final explorer has 24 nonplanar meshes, 648 field cases, and explicit failed-wet
transfer labeling. See REPORT.md, PUBLICATION.json, VIEWER-QA.json and README.md.
Registry status done, independent scientific validation still unvalidated.

Both `dity-solvent-coupled-h100-20261031` and
`junction-organoid-h100-20261031` were stopped after verification; `brev ls`
confirmed both STOPPED. Retained disks and unrelated workloads were untouched.

### Relevant WordPress posts reconciled (2026-10-31)

User authorized rewriting relevant posts and linking the completed results.
Updated 34 article-specific interpretations and results links, including six
stale outlook paragraphs in primary posts. Destination remains completed post407.
Native section edits used optimistic content/target hashes. All untargeted
block hashes match on all 34 posts; the classic body of post18 also matches.
Public readback confirms full updated-group prose and results links on 34/34.
Six replacement body blocks match their prepared raw SHA1 identities. Source,
numerical tables, media and unrelated article bodies were preserved.

Audit/backups and the full public/edit-link inventory are in
`experiments/wordpress-reconciliation-20261031/REPORT.md`. Read APPLIED-FINAL.json
rather than the intermediate APPLIED.json. The large fracture supplement146
returned an internal connector error after saving; fresh readback confirmed one
new group and all 96 original blocks unchanged, so no duplicate retry occurred.
No cloud instance was resumed for the editorial reconciliation.


## FCC3D numerical commissioning and atlas readiness (Codex, 2026-10-31)

`experiments/fcc3d-atlas-commissioning-20261031/REPORT.md` records 166 passing checks on the existing idle Nebius H100. Normalization now scales mu_el; fresh E2 modulus verification, smooth straight-hinge Hessian, full 9x9 tangent, strict convergence with bounded small-system Newton polish, relative-strain rupture, physical bidirectional lock failure, cascade rejection and signed cyclic work/peak fixes are applied. `oxt/architecture3d.py` implements actual binary-junction phantom FCC and stochastic finite fibres alongside diluted FCC. Structural checks use eight seeds/generator; mechanics two seeds/generator. Concurrent expected-bond-count fix retained. This is bounded numerical validation, not physical calibration.

The proposed 360-record atlas (720 E1/E2 branches) is NOT launched or matched-production-ready. Baseline matching passed 5/8 diluted cases, 0/8 phantom, 0/8 stochastic; raw diagnostics and an expected preflight rejection are saved. W2 finite phantom z<=3 and current FCC retention-only Sx<=.25 invalidate some proposed targets. US$15 cap and 9000s workload are a prepared proposal requiring feasible matching, current quote and future launch authorization. No new VM/volume, no GitHub push or WordPress publication in this commissioning task.


## LAMMPS rotational bonded-particle bundle pilot (Codex, 2026-10-31)

`experiments/lammps-bpm-pilot-20261031/REPORT.md`: seven 36-bead bundle trajectories plus analytic/contact probes on the existing Nebius worker; 40 checks pass; 102 remote file hashes verified. Native BPM rotational beams plus gran/hooke/history friction, weak/strong generic links, time-step/rate/output controls. Six of nine weak links break; strong nine and 33 backbone bonds remain intact. CPU only: reviewed 2025.7.22.2.0 engine has BPM/GRANULAR but no GPU/KOKKOS. No GPU speedup, calibrated chemistry, pure-dissipation/fracture-energy or tissue-mechanics claim. External loop work and total translational+rotational kinetic energy reported separately. No new capacity, no other workload modified, no external publication in this task. Full raw/interactive packet path in ARTIFACT_LOCATION.md.
