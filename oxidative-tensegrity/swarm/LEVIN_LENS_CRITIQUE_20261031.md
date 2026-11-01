# Levin-lens and open-endedness critique of the collagen network model (2026-10-31)

Five Gemini reviewers on the GCP lab project read the model's code, results and earlier critiques and proposed
testable bridges between collagen/ECM, vimentin and gap-junction networks on one side and (a) Michael Levin's
published research programme and (b) open-endedness research on the other. Three reviewers are **AI reviewers
applying ideas from Levin's published work**. They are not Levin, do not speak for him, and nothing here implies he
has seen or endorses this work. One reviewer applies open-endedness ideas (novelty search, quality-diversity,
evolvability of development). The fifth is an adversarial reviewer that read the first four reviews and attacked them.

The first-pass literature audit by Claude Code is preserved below, with a Codex claim-scope audit appended.
Verification applies to the stated scope of each source, not every extrapolation made by a reviewer. Code claims were checked
against the reviewed source snapshot; current code can differ. This is an AI-assisted critique, not experimental validation. Nothing in the model was changed.

## Short answer

The model cannot yet say anything about *collective* competency, because it has no collective: every reviewer
found that cells never talk to each other. The organoid's 5 surface positions share only a radius and a mean hoop
stress, with no gap junctions, no bioelectric state, no vimentin and no cell-cell forces. Within that limit the
model does carry three ideas that fit the Levin programme well, and each is testable:

1. **ECM as a writable memory.** LOX writes stiffness, MMP14 erases it, and AGE crosslinks write in a way that
   resists erasure. The open question is whether the tissue *defends* a stiffness (a setpoint) or merely *records*
   one (a scar). The model's organoid loop can test this in silico after a small fix.
2. **Strain stiffening as the signal-carrying range of the matrix.** The model's reported result is that
   crosslinks erase strain stiffening (K/G₀ 8.8–14.7 → 3–4.6) before they raise stiffness much. Published fibre
   mechanics links strain stiffening and fibre alignment to long-range force transmission between cells. That motivates
   the testable hypothesis that crosslinking changes the range over which cells can sense each other. Its direction
   is not established by a bulk stiffness or strain-stiffening ratio.
3. **Ageing as a shrinking set of reachable states.** This only becomes testable in the model once positions are
   coupled. Until then, "lost competency" cannot be told apart from "stiffer material".

## Verified code findings that matter for any bridge

These came out of the reviews and were confirmed in the source. They are model issues independent of the Levin framing.

| # | Finding | Where | Consequence |
|---|---|---|---|
| C1 | Organoid remodelling multiplies the whole secant curve by `scale`, so LOX/MMP14 "writing" can change stiffness but never the strain-stiffening ratio K(γ)/G₀ | `oxt/organoid.py:157` (`shifted_curves`) | The model's headline mechanism (crosslinks flatten nonlinearity) never enters the organoid's own feedback loop |
| C2 | MMP14 softening rate is constant; crosslink-driven protease resistance (`exp(-2.5·dose)`, used at tissue scale in `oxt/physio.py:100`) is absent in the organoid | `oxt/organoid.py:209, 282` | The organoid cannot show turnover escape (H1), so it cannot show a crosslink-locked state |
| C3 | In the reviewed snapshot, hoop stress used unclipped `exp(logS)` while the YAP/prestress lookup used clipped `logS` | was `oxt/organoid.py:259` vs `:279` | Integrator windup, a numerical "memory". **Fixed since by another session**: `logS` is now clamped to the table range (`:288`). Hysteresis tests should still check that trajectories do not just sit on the clamp walls (0.4× / 2.5×) |
| C4 | The 5 angular positions are uncoupled; their strain is an imposed cosine (`bud_amp`) | `oxt/organoid.py` `simulate_organoids` | No symmetry breaking, error correction or stress sharing can emerge |
| C5 | Each adhesion sees a seed-averaged, homogenised secant curve; tearing uses a fixed a/L ratio | `oxt/cell.py:68, 131` | Non-affine force chains near the rigidity onset, the very thing that would carry long-range signals, are averaged away |
| C6 | Sliding GAGs next to locked junctions get an infinite slip threshold (already flagged in `CODEX_CRITIQUE_20261031.md`) | `oxt/gag.py:36–38` | Any "stress-sharing" bridge built on GAG dissipation partly measures this imposed rule |

**Partly verified:** R1 noted that at steady gene levels the organoid's remodelling rate reduces to
d(logS)/dt = 0.125·h(PS; 0.75, 4) − 0.075·h(Y; 0.5, 2). The algebra is correct (`GENES` and line 282). R1 and R5
read this as a positive-feedback latch with an unstable interior zero, so the organoid would be bistable even
though single cells are not. Whether the zero is unstable depends on how Y and PS change with logS in the tabulated
cell model; **this was not checked numerically**. It is the first in-silico test below.

## Bridges ranked by testability

Ranking is Claude Code's, after the adversarial review (R5) merged 16 first-round bridges into 5 and the source
checks. T = testability (5 = weeks with existing tools), N = novelty, both as scored by the reviewers and adjusted
where noted. "Hook" is the part of the model the bridge attaches to.

| Rank | Bridge | Hook | Prediction | Falsifier | T / N |
|---|---|---|---|---|---|
| 1 | **In-silico setpoint vs latch vs scar** (R1 B1–B2, R3 B3, R5 M1) | organoid LOX/MMP14 loop | With C3 fixed and C2 added, a transient strain pulse either (a) latches the organoid to a high-stiffness, high-LY6A state that rebounds after partial softening (latch), (b) returns to one interior stiffness from both sides (setpoint), or (c) decays (no memory). AGE dose should convert (b) into a non-erasable record. | Trajectories relax monotonically to the unpulsed path, with no rebound and no bidirectional convergence | 5 / 4 |
| 2 | **Rigidity transition sets the mechanical signalling range** (R2 B2, R5 M3; anchored by Wang 2014, Chen 2022, Sharma 2016) | `oxt/network.py` | Strain decay length around a force dipole peaks or jumps near the rigidity onset (z ≈ 2.6–3.0) and shrinks when AGE crosslinks flatten K/G₀ at matched G₀ (PROPOSED; the smoke-run onset is an operational marker, not a demonstrated critical point) | Decay length depends only on G₀, not on z or crosslink dose | 5 / 4 (in silico); 4 / 4 in vitro |
| 3 | **Matched-G₀ organoids: nonlinearity, not stiffness, sets patterning** (R3 B1, R4 B1, R5 M2) | organoid + `yap_band.json`; `run_organoid.py` already has a matched-stiffness pairs analysis | At equal small-strain G₀, with the corresponding Young modulus E inside the model-specific YAP band, organoids in high-K/G₀ native gels make more budded, spatially patterned states and regrow an ablated bud more often than in glycated low-K/G₀ gels | No difference at matched G₀ | 4 / 4 (matching G₀ across glycated and native collagen changes ligand density and mesh size; needs a PIC or concentration control) |
| 4 | **Mechanical memory written into collagen** (R1, R3 B3, R5 M1, wet version; anchored by Yang 2014, Nasrollahi 2017, Almeida 2023) | organoid / cell sheet | Stiffness-primed organoids keep the high-YAP state after transfer to fresh soft gel when the original gel was lightly glycated, and the remodelled gel alone primes naive cells; test YAP and bioelectric perturbations separately, with viability, off-target and orthogonal genetic controls; erasure is untested | Immediate reversion on transfer; remodelled gel alone primes nothing | 4 / 4 |
| 5 | **Two-cluster communication across native vs glycated collagen, read out in Ca²⁺/Vmem** (R2 B2, R4 B3, R5 M3) | GAG + network | Contractile spheroid pairs synchronise Ca²⁺/Vmem over longer distances (the reviewer’s ≥2× effect size is arbitrary and unvalidated) on native strain-stiffening collagen than on G₀-matched glycated collagen or linear PA; GAG swelling shortens the range | Synchronisation distance tracks G₀ only | 4 / 5 |
| 6 | **Anthrobots as an ECM-ageing assay** (R3 B4, R4 B4, R5 M5) | anthrobots are grown embedded in ECM for ~2 weeks (Gumuskaya 2023), so the embedding matrix is a natural lever | Glycating or LOX-crosslinking the embedding matrix during formation narrows the distribution of morphotypes and motility classes; aged-donor cells freed from aged matrix recover a near-young repertoire | Repertoire tracks donor age only, not matrix state | 3 / 5 (the archive must count only reproducible states that persist; R5's dwell-time and ICC filters) |
| 7 | **Electrotonic length peaks at the rigidity transition** (R2 B1, R5 M4) | cell + proposed bioelectric layer | Gap-junction-coupled sheets show the longest Vmem decay length on matrices in the strain-stiffening band; it falls on floppy and on AGE-stiff matrices | Decay length rises monotonically with stiffness | 3 / 5 (voltage imaging of length constants is hard; z of reconstituted collagen is not directly tunable) |
| 8 | **AGE lock-in blocks execution of a bioelectric rewrite** (R1 B4, R5 M4) | planarian two-head assay (Oviedo 2010, Durant 2017) | Pre-glycated planarians keep the induced anterior depolarisation but regenerate two heads less often; matrix renewal rescues | Same penetrance with and without glycation | 2 / 5 (glycating a live planarian's ECM without systemic toxicity is unsolved) |

**Dropped or demoted by the adversarial review (agreed after checking):**
- *Vimentin polarity retention after cytoskeletal washout* (R1 B3) is the published Gan et al. 2016 assay. It shows
  persistence of a structure, not a setpoint, unless the cells are pushed against an opposing cue.
- *Buds orient along the stiff crosslink axis* (R2 B3) is ordinary contact guidance unless clamping Vmem uniform
  randomises bud orientation. Keep it only with that clamp.
- *MAP-Elites over the organoid while mutating `bud_amp`* (R4 B1) is circular: the descriptor (bud-to-interbud YAP
  contrast) is set by the input. It becomes meaningful only after C4 is fixed and positions can break symmetry themselves.
- *Gene-expression entropy under ±20% Hill-constant perturbations* (R4 B2) is a local sensitivity analysis of
  feed-forward read-outs, not evolvability.

## Where the analogy breaks (worth stating in any write-up)

- **Setpoint vs scar.** In the Levin programme a target morphology is defended: the collective corrects deviations
  in both directions and the state survives removal of the trigger (Pezzulo & Levin 2016; Durant 2017). An AGE
  crosslink is a record the tissue cannot erase. It is not a target the tissue restores. Excising an AGE-stiffened
  patch should give native matrix, not a rebuilt scar. If it does, the ECM is not a setpoint.
- **Hardware vs software.** Bioelectric states and ECM remodelling have different, context-dependent timescales.
  AGE accumulation in long-lived matrix can be slow, but LOX crosslinking and cell-driven matrix remodelling need
  not take years; no universal timescale separation is established here. A fairer analogy is that the ECM is the *substrate the pattern is executed into*.
  Crosslinking would then limit execution (bridge 8), not storage.
- **Competency needs a collective.** With uncoupled positions (C4), any loss of "competency" in the model is loss
  of single-cell dynamic range: YAP saturates above ~1 kPa. That is ordinary mechanobiology.
- **Open-endedness needs an open archive.** None of the proposed experiments shows *unbounded* novelty. At best they
  measure whether crosslinking shrinks a bounded repertoire. That is evolvability or canalisation in the
  Kirschner–Gerhart and Wagner sense, not open-ended evolution in the Packard et al. 2019 sense. Say so.

## What the model could add (proposals only, not implemented)

| Size | Change | File | What it would show | Bridge |
|---|---|---|---|---|
| done | Clamp `logS` (C3), done by another session after this review | `oxt/organoid.py:288` | removes a numerical source of fake memory | 1, 4 |
| small | Pass `age_dose` into `simulate_organoids` and scale `k_mmp_per_day` by `exp(-2.5·dose)`, as `physio.matrix_recovery_rate` already does (C2) | `oxt/organoid.py` | crosslink-locked remodelling | 1 |
| small | Optional initial state and a `pulse_fn` perturbation hook (strain pulse, partial softening, transplant to a fresh gel) | `oxt/organoid.py` | the setpoint / latch / scar test | 1, 4 |
| small | `ablate_pinning` flag (C6), already recommended by the Codex critique | `oxt/gag.py` | separates imposed from emergent loss of dissipation | 5 |
| small–medium | Force-dipole response: apply equal and opposite forces at two nodes, relax, report strain decay length ξ(z, dose, lock) | `oxt/network.py` (`Batch`) | in-silico bridge 2: does crosslinking shorten mechanical signalling range, and does ξ peak at the rigidity onset? | 2, 5 |
| medium | Let LOX write crosslink *dose* (moving along precomputed dose tables, which changes K/G₀) instead of scaling the curve (fixes C1) | `oxt/organoid.py`, `run_organoid.py` | lets the model's own nonlinearity result feed back on the tissue | 1, 3 |
| medium | Ring of N≈32 coupled positions: diffusive (gap-junction-like) coupling of a membrane-potential state Vᵢ with a strain-gated depolarising current and prestress-dependent coupling conductance, plus nearest-neighbour stress sharing; report a correlation length | `oxt/organoid.py` | the minimal "collective" every reviewer asked for; makes bridges 3 and 7 testable in silico | 3, 7 |
| medium | Vimentin cable family in the tensegrity cell: strain-stiffening, with a slowly adapting rest length (timescale to be calibrated; 12–24 h was an illustrative reviewer assumption) that carries polarity across resets | `oxt/cell.py` (`TensegrityCell`) | an intracellular memory element between fast myosin and slow ECM | 4 |
| large | Cells anchored to a shared network lattice (multi-cell `GAGBatch`) | `oxt/gag.py`, `oxt/network.py` | stress sharing through the matrix, emergent rather than imposed | 5 |

The small rows are a few lines each and would make bridge 1 runnable today. They touch `oxt/organoid.py`,
which the main session and the topology-optimisation session also use, so coordinate before editing.

## Source check

Claude Code checked the cited literature with web search; the appended audit narrows unsupported uses. **Verified** = paper exists and supports the use;
**misattributed** = paper exists but does not support the use; **wrong** = the claim is false as stated.

| Claim (reviewer) | Verdict |
|---|---|
| Levin 2022 TAME, Front Syst Neurosci, doi 10.3389/fnsys.2022.768201 (R1–R5) | verified |
| Levin 2021 Cell, bioelectric signalling, doi 10.1016/j.cell.2021.02.034 (R2, R5) | verified |
| Pezzulo & Levin 2015 Integr Biol, doi 10.1039/c5ib00221d; 2016 J R Soc Interface, doi 10.1098/rsif.2016.0555 (R1, R3, R5) | verified |
| Fields & Levin 2022 Entropy, doi 10.3390/e24060819 (R3, R5) | verified |
| Durant et al. 2017 Biophys J, bistable bioelectric pattern memory, doi 10.1016/j.bpj.2017.04.011 (R1, R5) | verified |
| Oviedo et al. 2010 Dev Biol, gap-junction cues set polarity, doi 10.1016/j.ydbio.2009.12.012 (R1, R3, R5) | verified; the persistence of the two-headed state is better attributed to the later work (Durant 2017) |
| Kriegman et al. 2020 PNAS xenobots, doi 10.1073/pnas.1910837117; Gumuskaya et al. 2023 Adv Sci anthrobots, doi 10.1002/advs.202303575 | verified |
| Shreesha & Levin 2023 Entropy (R3, R5) cited for *stress sharing* | **misattributed**: that paper (doi 10.3390/e25010131) is about cellular competency changing evolutionary dynamics, which is relevant to open-endedness. Stress sharing is Shreesha & Levin 2024, BBRC, doi 10.1016/j.bbrc.2024.150396 |
| Teuscher et al. 2024 author list in R3 | **wrong** (paper real, PMID 38177158; list garbled) |
| Ewald et al. 2015 title in R1 and R5 | **wrong title** (paper real, PMID 25517099) |
| "Vimentin links basal hemidesmosomes to lateral junctions" citing Ingber 2003 and Teuscher 2024 (R2) | **wrong**: hemidesmosomes anchor keratin, not vimentin, and neither paper says this |
| Gan et al. 2016 Cell Syst, vimentin templates microtubules for polarity persistence, doi 10.1016/j.cels.2016.08.007 (R1) | verified |
| Gjorevski et al. 2016 Nature, doi 10.1038/nature20168 (R1, R3, R4) | verified for "stiff gels expand stem cells via YAP; differentiation needs a soft matrix with laminin". R4's "requires MMP-mediated softening" is **not supported** by the abstract: the softening was engineered into the gel |
| Elosegui-Artola 2017; Ingber 2003; Broedersz 2011; Sharma 2016; Burla 2020 (doi 10.1073/pnas.1920062117); Petridou 2021 | verified |
| Lehman & Stanley 2011, doi 10.1162/EVCO_a_00025; Mouret & Clune 2015, arXiv:1504.04909; Packard et al. 2019, doi 10.1162/artl_a_00291 | verified |
| Kirschner & Gerhart 1998 PNAS; Wagner 2008 Proc R Soc B, doi 10.1098/rspb.2007.1137; Pigliucci 2008 Nat Rev Genet, doi 10.1038/nrg2278 | verified |
| Piezo1 depolarisation; Ca²⁺-gated gap-junction closure (R2) | unverified here (uncited; plausible); cite primary sources before use |
| R4 "shear-thinning" sub-isostatic collagen | **wrong term**: these networks strain-stiffen |

Anchors added by Claude Code while checking, all verified:
- Yang, Tibbitt, Basta & Anseth 2014, *Nat Mater*, doi 10.1038/nmat3889. Mechanical memory: YAP/TAZ activation
  becomes irreversible above a threshold stiff dose.
- Nasrollahi et al. 2017, *Biomaterials*, doi 10.1016/j.biomaterials.2017.09.012. Stiff-primed epithelium keeps
  nuclear YAP and faster collective migration on soft ground; the effect depends on YAP.
- Almeida et al. 2023, *Mol Biol Cell*, doi 10.1091/mbc.E22-10-0469. Primed cells **transfer their memory into
  collagen** through fibre alignment and tension, and the remodelled matrix guides later invasion. This is the
  closest published evidence that the ECM stores state.
- Wang et al. 2014, *Biophys J*, doi 10.1016/j.bpj.2014.09.044. Long-range force transmission needs fibre
  alignment and strain hardening.
- Chen et al. 2022, *PNAS* (preprint doi 10.1101/2021.09.13.460122). GAG swelling impedes fibre alignment and
  reduces long-range mechanical communication between cells.
- Shreesha & Levin 2024, *BBRC*, the stress-sharing model; Levin 2023, *Anim Cogn*, doi 10.1007/s10071-023-01780-3,
  bioelectric networks as cognitive glue.

## Run record

- Model `gemini-4-argon`, thinking level high, 24,576 output tokens per call, at most 3 concurrent requests, no
  automatic retries. API-only standard-library workers on VM `oxt-cpu32` (GCP project `scienceclaw26bos-3008`),
  using the key already provisioned there. The key was never read on or copied to the Mac.
- 5 calls: 4 first-round reviewers in parallel (setpoint and memory, signal gating, ageing and competency,
  open-endedness), then 1 adversarial reviewer given the four reviews. 236,542 prompt tokens, 45,624 answer tokens,
  48,824 thinking tokens, 330,990 total as reported by the API (usage metadata, not an invoice).
- The adversarial reply hit the output-token limit inside its citation list. The 5 ranked bridges, 3 critiques and
  3 model changes were complete. Claude Code dropped the partial final citation and the missing `strongest_bridge`
  field and closed the JSON; no wording was changed. This repair is recorded in the file.
- Packet: 12 frozen files (brief, README, hypotheses, both Codex critiques, cpu32 summary, phase smoke summary, YAP
  band, network/GAG/cell/organoid source), 116 kB, hashes in the manifest. Phase-map numbers were from the smoke
  run only; the 12×12 sweep was half done.
- Same model for all reviewers, so their agreement is not independent replication. The reviewers had no tools and
  saw only the packet.
- Personas, brief and runner: `swarm/levin_lens/`. Raw replies, packet, manifest and citation log are kept local in
  `swarm/work/levin_lens_20261031/` (not for publication).


## Final claim-scope audit and experiment controls (Codex, 2026-10-31)

**All bridge predictions above are PROPOSED.** Neither reviewer consensus nor a verified reference makes them
simulation results. In particular, a maximum of signalling range at the rigidity marker, a 2× range advantage,
a particular vimentin memory timescale, and recovery of an aged-donor repertoire remain **unverified**.
The five calls are complete as API requests; only four responses were complete schema-valid reviews. The fifth
was truncated and its repaired local JSON must not be represented as a complete original API response.

Additional verdicts on claims embedded in reviewer prose:

| Claim | Verdict and retained scope |
|---|---|
| Novelty search is necessary for open-ended discovery (R4 citation-use statement) | **Wrong as a necessity claim.** [Lehman & Stanley 2011](https://doi.org/10.1162/EVCO_a_00025) demonstrate benefits on particular deceptive tasks; they do not prove necessity or unbounded novelty. |
| Petridou 2021 establishes a collagen-to-bioelectric signalling gate | **Unverified extrapolation.** [The paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8055543/) supports embryonic contact-network rigidity and rheology; it does not measure the proposed collagen/gap-junction gate. |
| Almeida 2023 establishes ECM storage of a defended anatomical target | **Unverified extrapolation.** [The study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10208097/) combines cell invasion experiments and a model of priming-dependent collagen remodelling. This supports a mechanical-history mechanism, not anatomical error correction. |
| Chen 2022 supports GAG effects on mechanical communication | **Verified within its system.** [Published paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9169665/) supports reduced force communication through GAG-associated matrix changes; it does not establish cognitive stress sharing or the project's infinite-slip-threshold rule. |
| Xenobot and anthrobot work establishes open-ended evolution or rejuvenation | **Unverified.** The cited studies establish engineered/self-constructed forms and specified behaviours; neither demonstrates unbounded innovation or reversal of donor ageing. |
| Stress sharing means elastic stress transmission | **Wrong equivalence.** [Shreesha & Levin 2024](https://doi.org/10.1016/j.bbrc.2024.150396) is a computational model of coordinating morphogenesis. Mechanical stress may supply a candidate channel, but requires an explicit mapping to the model's signals and goals. |
| Stiffness/entropy or YAP alone measures collective competency | **Unverified.** Require successful recovery on held-out perturbations, an explicit target or task, and causal communication ablations at matched viability and mechanical capacity. |
| Pezzulo & Levin 2015 supplies an ECM-specific target-memory result | **Unverified extrapolation.** [The review](https://pubmed.ncbi.nlm.nih.gov/26571046/) motivates pattern-memory and regenerative-control experiments; it does not establish collagen as the storage substrate. |

**Minimum discriminating experiments.** For matrix memory use a factorial transplant: primed versus naive cells
crossed with conditioned versus fresh matrices. Match residual ligands, soluble carryover, stiffness, relaxation,
fibre alignment, cell number and viability. A subsequent positive and negative perturbation must elicit active
restoration before calling the state a defended setpoint. Cell removal/reseeding tests matrix-retained information;
cell transfer tests cell-retained information. Persistent damage alone satisfies neither criterion.

For communication, independently measure a local mechanical response and voltage/Ca²⁺ response, and distinguish
shared forcing, soluble signals, physical matrix coupling and direct cell-contact coupling. Separate spheroids
cannot have gap junctions across a cell-free collagen gap. Use contact-connected sheets for the electrical-coupling
arm, gap-junction genetic perturbation plus rescue, and secretion/mechanical controls. A correlation length need
not be exponential: compare candidate decay laws and boundary/size dependence before reporting a single length.

For open-endedness, begin with a bounded quality-diversity benchmark: equal evaluations for random search,
objective optimisation and novelty/QD search; held-out seeds and perturbations; fixed descriptor resolution;
reproducible morphology/behaviour classes; noise and viability controls. Do not count imposed bud amplitude as
emergent novelty. Test developmental adaptation by heritable controller variation and transfer across environments.
Continued novelty across increasing runtime, population, representation and environment capacity would strengthen
an open-endedness argument, but a finite archive alone cannot establish unbounded novelty.

## Cross-project matched-stiffness handoff (received 2026-10-31)

The originating chat supplied a bounded result from a separate H100 study, publicly described in
[matched-stiffness collagen relaxation results](https://humanavianaisymbiosis.wordpress.com/2026/10/31/matched-stiffness-collagen-network-relaxation-h100-results/).
**Status: source-chat report; underlying trajectories were not independently reanalysed in this critique.**
The web retrieval of the post was unavailable during this final audit. This study was not in the frozen Gemini packet.

At its specified kappa=.03, r=.5, beta=10 condition, the handoff reports 67.15% versus 64.40% stress retention
for uniform versus clustered dilution after five internal time units (16 paired primary seeds; difference
−2.76 percentage points, pointwise paired bootstrap interval [−3.92, −1.55]). It reports a larger-size difference
of −3.87 points with seven valid pairs. Matching initial G₀ rescales microscopic modulus and therefore does not
isolate architecture at fixed fibre stiffness. Homogeneous relaxation of all energy terms supplies an exact
architecture-independent null; selective axial relaxation relative to bending produces the reported differences.

This adds a useful **control requirement**, not evidence for cognition: matched initial stiffness experiments must
also measure relaxation and architecture. Keep the reported solver-dependent displacement nonaffinity and unresolved
later fracture curves out of mechanistic headlines. The 1,600 trajectories contain only 50 distinct graphs and are
not independent specimens. These effective parameters establish no named crosslink chemistry, physical time scale,
YAP response, ageing mechanism or organoid causation. No additional compute or publication was initiated from this handoff.

## Follow-up simulation (2026-10-31)

The top-ranked setpoint-versus-scar bridge was tested in a separate, frozen-radius assay using the current organoid gene/remodelling rules and saved cell-response calibration. Across 36 conditions and 90- and 360-model-day horizons, high-stiffness endpoints were bound-dependent and retained a positive remodelling rate; native low-stiffness states continued to relax slowly. No defended interior setpoint was found in this assay. See `SETPOINT_VS_SCAR_20261031.md` for the design, numerical results, clipping controls and scope limits. The shared organoid source was not changed for this test.

## Bioelectric ageing run on a Nebius H100, with critique (Claude Code, 2026-10-31)

**Question.** Levin and colleagues treat ageing as a loss of morphostatic information carried partly by bioelectric
patterns (Pio-Lopez & Levin 2024, *Ageing Res Rev* 97:102310; Pio-Lopez, Hartl & Levin 2025, *Adv Sci*, doi
10.1002/advs.202509872). Senescing human keratinocytes, cultured without ECM, show a measured signature (Sediqi &
Levin 2025, *iScience* 28:113275, doi 10.1016/j.isci.2025.113275):
- depolarisation;
- within-dish Vmem variability −38%;
- between-dish SD ×15–22;
- global Moran's I 0.5 → 0.13–0.26.

Its authors list ECM and mechanical gradients as missing from their model. Do the stiffness *distributions* of
crosslinked collagen, read by cells, push a coupled Vmem sheet toward that signature?

**What ran.** New code `oxt/bioelectric.py`, `run_bioelectric.py` and `tests/test_bioelectric.py` (4 checks pass).
No shared model file was changed. The steps:
- **Networks:** 312 of them (64×64), 8 seeds per condition. Col I at z 2.8–4.4 × AGE dose 0/0.25/0.5/1 ×
  iso/aniso, plus skin dermis at ages 20/40/60/80.
- **Local stiffness:** per-cell maps (16×16 patches) from an exact energy split. Patch means equal the global
  modulus.
- **Cells:** each patch drives the existing motor-clutch + tensegrity cell, giving traction and prestress.
- **Vmem sheet:** a bistable, gap-junction-coupled sheet with a stretch-activated current and either constant or
  prestress-gated junctions.
- **Sweep:** 18 parameter sets × 3 field controls (actual, shuffled positions, uniform mean).
- **Compute:** Nebius H100 (`gpu-h100-sxm`, created through Brev). The digest-pinned `pytorch/pytorch:2.5.1` image
  ran with no network, a read-only root, all capabilities dropped, a non-root user and no package installs. The
  scipy tensegrity table was precomputed on the Mac and passed in as data. The run took 41 min. The instance was up
  about 1.4 h including build and SSH setup, roughly $8 at $5.40/h (estimate, not an invoice). All 4 output files
  matched their SHA-256 hashes on both ends. Instance stopped afterwards, disk kept.

Results are in `results/bioelectric/gpu/`: `SUMMARY.md`, `DIAGNOSTICS.md`, `ageing_contrasts.csv`,
`conditions.csv` and `bioelectric_maps.png`.

**Results** (model output; trends, not measurements):
1. **Depolarisation reproduced, but built in.** Skin 20 → 80 y: +3.0 mV (mean local E only 2.0 → 2.6 kPa). Col I
   dose 0 → 1: +2.3 to +11.9 mV, in 100% of parameter sets at z ≤ 4.0. At default settings it is graded on the
   hyperpolarised branch and no cell switches. It reverses at the stiffest networks (z = 4.4, about 16 kPa: −12 mV),
   because motor-clutch traction peaks near 420 pN and falls on very stiff matrices. The traction optimum is
   standard motor-clutch behaviour (Chan & Odde 2008; Bangasser et al. 2013). The model therefore predicts
   non-monotonic Vmem versus stiffness.
2. **Clustering moves the wrong way.** Moran's I of Vmem *rises* with crosslinking in most parameter sets (skin
   0.473 → 0.501 at default) even though Moran's I of stiffness falls. No contrast in any field matches all four
   keratinocyte signs (0 of 108). Within-sheet SD mostly rises.
3. **Spatial structure is a real distribution effect.** The actual stiffness map gives higher Vmem clustering than
   the same cells shuffled in 95% of 702 comparisons (mean +0.061). Near the switching threshold, spatially
   correlated stiff patches nucleate switching that the shuffled map does not. Col I z = 3.6, G0 = 0.25, constant
   junctions:
   - actual: +37.6 mV, within-SD ratio 0.57, between-SD ratio ×52, half the aged sheets switched;
   - shuffled: +12.1 mV, within-SD ratio 1.21, between-SD ratio ×1.1.

   That reproduces three of the four signs, only near a knife-edge threshold, and Moran's I still rises.
4. **Heterogeneity smooths the mean response.** Uniform-mean sheets jump far more than actual ones (z = 3.6:
   +24.6 vs +11.9 mV; z = 4.4: −50.4 vs −12.3 mV). This is averaging a nonlinear map (a Jensen-type effect).
5. **Pattern memory depends on an assumption.** A written disk prepattern is held only with prestress-gated
   junctions on soft matrix, where low prestress nearly uncouples the cells. With constant junctions it is held only
   at weak coupling (G0 = 0.25). Crosslinking erases memory by strengthening the coupling. **Net restoration**
   after flipping 25% of cells (restore minus the un-healed flipped baseline) is about zero in every field: mean
   −0.013 actual, −0.015 shuffled, −0.047 uniform. The sheet freezes. It does not repair.

**Reading for the Levin bridge.** In this model, ECM stiffness distributions do not explain the keratinocyte
signature, which was itself measured without ECM. They predict that crosslinked collagen should make Vmem *more*
spatially clustered, not less. That is a clean, opposite-sign test: image BeRST Vmem and Moran's I on native versus
glycated collagen at matched mean stiffness. The one distribution-specific mechanism is nucleation: spatially
correlated stiff patches tip a near-threshold sheet into switching that the same cells in random positions do not.

**Critique (4 Gemini calls, `gemini-4-argon`, GCP VM, 576k tokens).** The reviewers were two Levin-lens AI
reviewers (not Levin), a biophysics sceptic and an adversarial pass. Each claim below was checked against the data
by Claude Code:

| Reviewer claim | Check |
|---|---|
| Reported pattern "restoration" is mostly the flipped baseline (V2, V3, V4) | **confirmed**: q_flipped / q_hold median 0.501; net restoration about 0. Analysis now reports `net_heal` |
| Single-cell saddle node at shunt 0.652, so switching needs traction > 1.19·F50 and F50 ≥ 400 pN never switches (V3) | **confirmed** numerically (0.6516 at −45.9 mV) |
| Prestress-gated junctions are the inverse of senescence, where coupling is thought to fall; they raise Moran's I with ageing (V1–V4) | **agreed**: an assumption to replace with a stress-uncoupling mode |
| Actual maps give 1.8–7.4× better restoration than shuffled (V2, V4) | **wrong** once the baseline is netted out (no field difference) |
| Spatially correlated stiffness nucleates switching (V4) | **confirmed** (z = 3.6 example above) |
| GAG-tether energy contaminates patch moduli (V3, V4) | **negligible**: 0.04–0.7% of patch energy |
| Explicit Euler is near instability at G0 = 4 (V3) | **no effect**: dt 0.05 vs 0.01 gives identical maps (max difference 0.0000 mV) |
| Global-strain normalisation is an energy-density proxy, not true local stiffness (V3) | **valid caveat**; local-strain or force-dipole probing is the fix |
| Seeds are reused across ages and doses (paired), and 8 seeds is low power for SD ratios (V3) | **valid**: comparisons are paired realisations; SD ratios need bootstrap intervals and more seeds |
| Noise-free relaxation cannot give the information measures Pio-Lopez, Hartl & Levin 2025 use (active information storage, transfer entropy) (V2) | **valid**: needs Langevin noise |
| Cervera, Meseguer & Mafe 2016 DOI 10.1038/srep35201 "questionable" (V4) | **wrong**: verified, Sci Rep, PMC5059667 |
| Sediqi & Levin title and first initial (V1–V3) | **invented** in V1 and V3: real title "Bioelectric characterization of senescing human keratinocytes", first author H. Sediqi |

**Top bridges after the checks:**
1. **Matched-mean stiffness maps.** Native fibrillar collagen versus glycated collagen versus uniform PA at the
   same mean E. Measure BeRST Vmem, Moran's I and the spatial cross-correlation of AFM stiffness with Vmem.
   Prediction: native collagen gives higher Vmem clustering, and crosslinking raises it further.
2. **Gap-junction coupling on aged matrix.** Calcein FRAP plus Moran's I on native versus glycated collagen, with
   ROCK inhibition. This decides which junction assumption is right.
3. **Non-monotonic Vmem versus stiffness.** Vmem and traction-force microscopy from 0.2 to 50 kPa, with and without
   vinculin reinforcement.
4. **Nucleation by stiff-patch correlation length** on photopatterned gels at matched mean and CV.

**Next model changes** (small, not done):
- a stress-uncoupling junction mode;
- Langevin noise with information measures (active information storage, transfer entropy);
- unique seeds per condition, 32 seeds, and bootstrap intervals;
- local-strain-normalised patch moduli;
- Vmem → prestress feedback, to close the morphostatic loop.

Raw API records are in `swarm/work/levin_bioelectric_20261031/` (local only). The personas and brief are in
`swarm/levin_lens/roles_bioelectric.json` and `BRIEF_BIOELECTRIC.md`.
