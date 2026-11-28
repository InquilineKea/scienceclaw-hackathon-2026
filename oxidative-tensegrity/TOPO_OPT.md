# Topology optimisation of Col I fibre networks for organoid scaffolds

Question: which bond and crosslink layouts make a 2D Col I fibre network that is **resilient** (tough, not
brittle) while giving an embedded organoid the right **stiffness**, a usable **mechanical channel** (strain
transmission, force propagation) and a usable **chemical channel** (diffusive access)?

Everything below is computed with the existing fibre-network model (`oxt/network.py`, Col I parameters from
`oxt/materials.py`, no AGE damage). Those parameters are model assumptions, not measurements, so every
result here describes what this model does. Code: `topo_opt.py` (search), `analyze_topo.py` (front, rules,
figure). Outputs: `results/topo/`.

## Design space (7 genes, `topo_opt.decode`)

| gene | range | meaning |
|---|---|---|
| z | 2.6–5.0 | mean connectivity of the matrix outside the pore |
| pattern | uniform, graded, layered, clustered, aligned | spatial pattern of bond probability, p = p0 (1 + amp f) |
| amp | −1…1 | graded: + = denser next to the pore; aligned: + = more bonds along x; layered/clustered: contrast |
| scale | 0–1 | layered: 1–3 bands parallel to x; clustered: correlation length 0.8–3 lattice units |
| lock | 0–1 | fraction of matrix junctions angle-locked (LOX/pyridinoline-type, kx = 2e-3, as `run_phase.py`) |
| place | random, near pore, far from pore, crossings | where the locks go (crossings = highest-degree nodes) |
| pore | 1 to W/4 | radius of the empty region left for the organoid (all bonds touching it removed) |

p0 is set by bisection so that the expected matrix connectivity equals z; one bond per fibre line is cut as in
`build_spec` (lines already cut by the pore are left alone). The realised z is recorded (`z_matrix`).

## Objectives and how each is computed

Each design is built twice with independent random realisations; one is pulled along x and one along y.
Resilience takes the **worse** of the two, everything else the mean, so a design cannot win by lining its fibres
up with a single load axis.

| objective | definition | direction |
|---|---|---|
| toughness | ∫σ dε of a laterally constrained uniaxial pull with bond rupture, 0.04–0.44 in 0.04 steps (`Batch.failure_curve`, unchanged) | max (worst axis) |
| brittleness | largest one-step stress drop / peak stress (same definition as `run_phase.py`) | min (worst axis) |
| sensing | √(T_ring × reach): **T_ring** = mean \|bond strain\| in a 2-unit ring around the pore divided by the affine bond strain, under a small uniaxial stretch along the pull axis (how much bulk strain the organoid's neighbourhood actually receives); **reach** = share of the work of an isotropic contraction at the pore (net force removed) that is stored in fibres (stretch + bending + locks) beyond the midpoint between pore edge and box edge, divided by the same share in a fully bonded (z = 6) sheet with the same pore and box, capped at 1.5 and gated by the share of work stored in fibres rather than the background tether | max |
| transport | effective radial D/D0 of an exosome-sized probe (r = 50 nm) from the outer shell to the pore, shells in series, Ogston hindrance per shell (`oxt.physio.ogston`, φ = 0.15 × local bond density / native) | max |
| constraint | linear shear modulus G inside the stiffness band below; violation = \|log10\| distance to the band | Deb constraint-domination |

Also recorded: strain at peak, largest rupture avalanche, strength, residual stress, Cx, Cy, bulk
non-affinity, displacement decay ratio, giant-cluster fraction and `mesh_size`.

**Linear response.** G, Cx, Cy, the strain field under bulk stretch and the response to the pore contraction
all come from one exact Hessian of the model energy at its stress-free reference state, solved directly
(Cholesky), not from L-BFGS. On test designs (W = 10) this matches `Batch.small_strain_moduli` to 1–6 % for G
and Cx across z = 2.9–5.4, and is 10–100× faster near the rigidity onset where L-BFGS crawls. The rupture pull
still uses the model's own `failure_curve`.

**How the reach metric was arrived at (three versions; the first two were wrong).**
1. *Displacement decay* made floppy, low-z networks look like long-range transmitters: they move as a whole
   on the weak tether (k_gag = 1e-6) while carrying almost no fibre tension.
2. *Far/near fibre-strain ratio* came out above the fully bonded sheet for most diluted networks. At W ≤ 12 the
   far shell is only 1–3 lattice units from the pore and periodic images interfere, and below z ≈ 4 most of the
   work goes into fibre bending, which a stretch-strain ratio does not see. The first implementation also left a
   small net force that translated the whole box against the tether; that was a bug, now fixed by removing the
   mean force. Both quantities are still recorded (`decay_ratio`, `decay_len`, `u_ratio`) but not optimised.
3. *Far-field work share relative to a full sheet* (used): energy-based, so bending counts. Normalising by the
   same geometry removes box and pore size. On W = 12 uniform test networks it is 0.83 at z = 2.9, 1.1–1.45 at
   z = 3.4–3.9 and about 1.0 at z ≥ 4.4. In other words, the contraction reaches furthest near the rigidity
   onset, as expected from the critical-transmission literature (Sharma et al. 2016), though this is a
   linear-response, small-box measure.

## Stiffness band (model assumption)

`topo_opt.py --calibrate-yap` runs the unchanged cell model (`oxt/cell.py`: motor-clutch, tensegrity, YAP with
myosin feedback, clutch_T = 40 s) on matrices of constant modulus E from 1 Pa to 32 kPa
(`results/topo/yap_calibration.csv`). Steady YAP switches on between ~50 and ~300 Pa and saturates by ~1 kPa.
The band is defined as the E range where YAP crosses 25–75 % of its span, i.e. where a cell can still *read*
a change in stiffness:

**E ≈ 120–284 Pa → G ≈ 0.0032–0.0075 model units** (`results/topo/yap_band.json`; S_pa = 12 667 Pa per stress
unit from `results/cpu32/summary.json`, which fixes young dermis at E = 2 kPa).

Both ends are assumptions: the clutch parameters, the Pa calibration and the choice of "responsive" over
"saturated" YAP. For organoids it is a defensible choice, since Matrigel-like matrices sit in the same few-hundred-Pa
range and intestinal-organoid PEG matrices are softened for differentiation, but nothing here was fitted to
organoid data.

## Search

NSGA-II written in numpy (`topo_opt.py`): Latin-hypercube start with one design per pattern, binary tournament
on (rank, crowding), SBX crossover (η = 15) and polynomial mutation (η = 20) on the 7 genes in [0, 1],
constraint-domination (feasible beats infeasible; infeasible ranked by violation), (μ + λ) survival.
Realisations whose G is more than 3× outside the band skip the rupture pull: they are infeasible regardless (so
their resilience never enters the ranking), and the floppy ones are the slowest to relax.

## Runs

| run | where | W | designs × realisations | wall time | output |
|---|---|---|---|---|---|
| prototype | Mac, 6 workers | 10 | 24 × 2 (2 generations) | 35 min | `results/topo/local_W10_*` |
| GA | oxt-cpu32, 26 workers | 12 | 104 × 2 (4 generations, pop 26) | 40 min | `results/topo/ga_W12_*` |
| re-evaluation, larger box | oxt-cpu32, 28 workers | 16 | 10 front designs + 4 uniform baselines × 2 | 10 min | `results/topo/reeval_W16_*` |
| re-evaluation, more realisations | oxt-cpu32, 28 workers | 12 | same 14 × 8 | 31 min | `results/topo/reeval_W12x8_*`, `reeval_W12x8_means.csv` |

The 10 re-evaluated designs are the best on each objective plus the most spread-out by crowding distance
(`--max-designs 10`). The baselines are plain uniform networks with no locks at z = 3.2/3.4/3.6/3.8 (realised
z 3.39/3.55/3.82/4.08), with the median front pore size. The pore gene scales with W, so the pore-to-box
ratio is held fixed between W = 12 and 16. Four generations is a short search, so the front is a pilot, not converged: in-band offspring per generation
were still rising (4, 7, 10, 13 of 26; `ga_W12_summary.md`).

## Results

### 1. Where the designs sit relative to the rigidity onset

Every design that lands in the YAP-responsive stiffness band is **sub-isostatic**. In the GA, in-band designs have
z_matrix 3.17 / 3.38 / 3.80 (10th / 50th / 90th percentile) and the front 3.19 / 3.39 / 3.84. With 8 realisations, the
designs that stay in band in at least half of them sit at **z = 3.19–3.63**: on or just above the
bending-stabilised onset (z ≈ 3.2–3.5 here), and well below the central-force isostatic point z = 4. The two
front designs at z ≈ 3.9 were in band at W = 12 with 2 realisations by luck. With 8 realisations their median G is
0.012–0.016 (1.6–2× above the band) and they are in band in 1 of 8. In other words, the stiffness a cell can read
in this model coincides with the connectivity range where G changes fastest with z and varies most between
realisations (main session: seed-to-seed CV of G peaks at z ≈ 2.9–3.2).

**Reproducibility is the binding constraint.** Even the best designs are in band in only 5–6 of 8
realisations. Plain uniform networks reach at most 4 of 8 (z = 3.55). Scaffold-to-scaffold variability near
the onset is as large as the band itself.

### 2. Resilience: no layout beats a plain network of the same stiffness (negative result)

8-realisation means, W = 12 (`reeval_W12x8_means.csv`; ± is the standard error):

| design | z | in band | toughness ×10³ | largest drop / peak | strain at peak | T_ring | reach | D/D0 |
|---|---|---|---|---|---|---|---|---|
| uniform, no locks (baseline) | 3.55 | 4/8 | 2.1 ± 0.3 | 0.70 | 0.175 | 0.040 ± 0.008 | 0.96 | 0.42 |
| uniform, no locks (baseline) | 3.39 | 3/8 | 2.2 ± 0.2 | 0.81 | 0.225 | 0.040 ± 0.006 | 1.05 | 0.43 |
| uniform, no locks (baseline, out of band) | 3.82 | 2/8 | 2.8 ± 0.4 | 0.74 | 0.19 | 0.113 ± 0.022 | 1.05 | 0.41 |
| uniform, 65 % random LOX locks, minimal pore (#47) | 3.25 | 6/8 | 2.2 ± 0.3 | 0.77 | 0.22 | 0.029 ± 0.007 | ≥1.5 | 0.47 |
| same family (#81, #92) | 3.19–3.21 | 2–3/8 | 2.5 ± 0.3–0.4 | 0.66–0.72 | 0.23–0.24 | 0.030–0.033 | ≥1.5 | 0.47 |
| layered, 78 % locks far from pore (#54) | 3.39 | 4/8 | 2.6 ± 0.3 | 0.73 | 0.23 | 0.042 ± 0.010 | 1.06 | 0.43 |
| **aligned (x-rich, amp 0.5), 8 % locks at crossings (#99)** | 3.63 | **6/8** | 2.5 ± 0.3 | 0.65 | 0.18 | **0.140 ± 0.033** | 1.05 | 0.41 |
| **same, second realisation family (#64)** | 3.63 | **5/8** | 2.7 ± 0.1 | 0.68 | 0.185 | **0.141 ± 0.029** | 1.04 | 0.40 |
| clustered, high contrast (#63) | 3.65 | 1/8 | 1.3 ± 0.4 | 0.56 | 0.22 | 0.12 ± 0.08 | 1.09 | 0.46 |

- **Toughness.** All in-band designs reach 2.2–2.7 ×10⁻³ against 2.1–2.2 ×10⁻³ for the matched baselines. The
  differences are 1–1.5 standard errors at most. The GA's apparent toughness gains did not survive re-evaluation:
  the rank correlation between the GA values (2 realisations) and the re-evaluations is 0.19 at
  W = 16 and 0.22 with 8 realisations at W = 12. Restricted range contributes (every front design was selected into the same narrow G
  band), but the conclusion stands: **in this model, toughness at fixed stiffness is set by connectivity, not by
  layout**, within what 8 realisations can resolve.
- **Brittleness.** Nearly every network loses 55–100 % of its peak stress in one 0.04 strain step in at least
  one realisation. Aligned designs have the smallest mean drop (0.65–0.68 vs 0.70–0.81) but it is not separable from
  noise. With worst-case aggregation over 8 realisations the drop saturates near 1 for almost everything (the rank
  columns in `reeval_W12x8_designs.csv`), so the mean table is the one to read.
- **Strain at peak** falls with z, as in the main session's phase map. Heavy LOX locking lets a network reach the
  band at lower z (3.2 vs 3.55), which delays the peak (0.22–0.24 vs 0.175).

### 3. Sensing is the real design lever

- **Aligned + sparse crossing locks** is the one layout effect that survives every check. At the same stiffness band
  it transmits **~3.5× more bulk strain to the pore neighbourhood** (T_ring 0.14 ± 0.03 vs 0.040 ± 0.008 for the
  uniform baseline at z = 3.55, ≈ 3 standard errors). That equals the transmission of a uniform network at z = 3.82,
  which is out of band. At W = 12 it is also the most reproducible in-band design (6/8). The cost is slightly lower
  transport (D/D0 0.41 vs 0.42) and an earlier stress peak (0.18). T_ring is averaged over realisations pulled along x
  and y, so this is not an artefact of the pull axis.
  **Correction (2026-11-01, 8-realisation re-run at W = 16, section 6):** at W = 16 the same design (#99) has mean
  G = 0.0031, just below the band's lower edge (0.00316), and is in band in only 2 of 8 builds. Its strain-transmission
  advantage over the uniform-locked design #47 holds at W = 16 (T_ring 0.074 vs 0.028), but "same stiffness" and "most
  reproducible" are W = 12 results only. Near the onset, band membership of every design tested depends on box size.
- The sensing ranking transfers between runs (Spearman 0.86 at W = 16, 0.73 with 8 realisations); the stiffness and
  toughness rankings do not.
- **LOX locking trades local strain for reach.** Controlling for z (partial Spearman over the 34 in-band GA designs),
  lock fraction lowers T_ring (−0.33) and the sensing score (−0.66), raises brittleness (+0.32) and delays the peak
  (+0.30). Heavily locked low-z networks (#47, #81, #92) have the lowest T_ring (0.03) but the largest far-field work
  share (reach ≥ 1.5, the cap): a contraction at the pore is felt further away, while bulk strain reaching the pore
  is small. Whether a scaffold should favour the organoid *sensing the tissue* (T_ring) or *signalling to it* (reach) is
  a design choice, not something the model decides.

### 4. Transport (chemical channel) barely discriminates

Radial D/D0 for an exosome-sized probe spans only 0.39–0.48 across in-band designs. It is set almost entirely by
fibre density, i.e. z and pore size (Spearman with z −0.68, with pore radius −0.68). Collagen-fibre Ogston hindrance with
R_f = 40 nm is weak; in tissue, GAGs dominate hindrance (`oxt/physio.py`). Locking at low z is the only layout
lever (+0.05 D/D0). This objective needs a better model (GAG content, binding) before it can steer design.

### 5. Layouts that did not work

- **Graded connectivity around the pore.** In this GA, none of 9 graded designs landed in the band (5× too stiff
  at z ≈ 3.8, 3× too soft at z ≈ 3.2). An independent pymoo NSGA-II run (main session, 2 realisations, W = 12)
  **did** find graded designs on its feasible front (56% of it). Re-run with 8 realisations at W = 12 and W = 16
  (section 6), **none of the 6 real-gradient graded designs stays in band at both box sizes**. The two denser-near-pore
  designs (#132, #159) have the highest sensing of anything tested, but are above the band at W = 12 and in band at
  W = 16. The sparser-near-pore designs lose strain transmission at the pore entirely at W = 16 (T_ring ≈ 0).
  Status: pymoo's 2-realisation graded front did not survive 8 realisations; "graded never lands in band" is too
  strong, and "graded designs sit on the band edge and cross it with box size" is what the data show.
- **High-contrast clustered** fields give the most variable networks (median G 0.0003, CV of G ≈ 2 over 8
  realisations): they leave poorly connected regions, and the pore can end up in one.
- **Lock placement** is unresolved. Heavy locking near the pore or at crossings never reached the front, and
  with only 2–4 in-band designs per placement the GA cannot rank placements. The only placement result is "a few
  locks at crossings" within the aligned family.
- **Variance reduction by locking**, seen in the main session's finite-size data (CV 0.67–0.82 → 0.40 with
  full LOX locking, no pore), was not detectable here (lock fraction vs CV of G: ρ = 0.00 over 73 near-band
  designs, 2 realisations each). Unresolved, not contradicted.

### 6. Cross-check against an independent optimiser (pymoo, 2026-11-01)

The main session ran pymoo 0.6.2 NSGA-II (seed 77, 6 generations × 28 = 168 designs, 2 realisations, W = 12; `team/topo_pymoo.py`,
`results/topo/pymoo_compare.json`) on the same encoding, objectives and band. Its front overlaps this GA's in z by 63%,
has a larger hypervolume (0.110 vs 0.070) and is 56% graded where this GA's is 52% uniform. To decide whether the graded
designs are real or 2-realisation luck, the 6 real-gradient graded designs (|amp| ≥ 0.45), 4 near-uniform "graded" designs
(sanity group) and comparators (GA #47, #92, #12, #99, #64, uniform baselines) were re-run with 8 realisations each:
136 tasks at W = 12 (46 min) and 80 tasks at W = 16 (two runs, 29 + 11 min). The decision rule was fixed in
`results/topo/graded_crosscheck_protocol.json` before running. A graded design survives if its 8-realisation mean G is in
band at both W and no in-band comparator dominates it on 8-realisation means. One amendment was made before W = 16 ran:
for time, the W = 16 comparators were reduced to #47, #99 and the two baselines. Decision: `crosscheck_graded.py` →
`results/topo/graded_crosscheck_summary.json`.

| design | gradient | mean G, W = 12 (builds in band) | mean G, W = 16 (builds in band) | sensing W12 / W16 | T_ring W16 |
|---|---|---|---|---|---|
| pymoo #164 | sparser near pore (amp −0.82) | **0.0061** (2/8) | 0.0084 (3/8) | 0.04 / 0.00 | 0.000 |
| pymoo #58, #128, #131 | sparser near pore (amp −0.80) | 0.016–0.018 (0–2/8) | 0.011–0.015 (0–1/8) | 0.03–0.08 / 0.00 | ≈ 0 |
| pymoo #132 | denser near pore (amp +0.53) | 0.0085 (4/8) | **0.0069** (3/8) | 0.41 / 0.21 | 0.146 |
| pymoo #159 | denser near pore (amp +0.45) | 0.0127 (3/8) | **0.0052** (1/8) | 0.42 / 0.22 | 0.094 |
| GA #47 (uniform, 65 % locks) | – | **0.0040** (5/8) | **0.0053** (3/8) | 0.23 / 0.20 | 0.028 |
| GA #99 (aligned, crossing locks) | – | **0.0065** (5/8) | 0.0031 (2/8) | 0.37 / 0.25 | 0.074 |

Band: G 0.00316–0.00748; bold = mean in band. Results:
- **No graded design survives** (in band at both W: 0 of 6). The registry entry is refuted.
- At the one size where each is in band, no comparator dominates it (#164 at W = 12 by having the highest transport;
  #132 and #159 at W = 16 by sensing). So graded designs are not worse when they land in band. They just do not land there
  reliably.
- The same box-size instability affects this GA's own best designs: #99 drops out of band at W = 16. Of all designs
  re-run at both sizes, only #47 (uniform, heavy random locking) has its mean in band at both, and only 3/8 builds are
  in band at W = 16. **The stiffness window sits on the rigidity onset, where finite-size effects are largest. Design
  rankings by band membership at W ≤ 16 are not reliable, while the strain-transmission ranking (aligned and
  denser-near-pore > uniform-locked > sparser-near-pore) holds at both sizes.**
- The sanity group (near-uniform "graded", |amp| < 0.07) behaves like uniform networks. Only #67 is in band at W = 12,
  and it is dominated by #47.

## Model assumptions vs results

| | status |
|---|---|
| Col I fibre parameters, kx = 2e-3, k_gag = 1e-6, no AGE damage | assumptions (`oxt/materials.py`, `run_phase.py`) |
| Pa calibration (young dermis E = 2 kPa) and the YAP band 120–284 Pa | assumptions (cell model unchanged, band definition chosen here) |
| Exosome-probe Ogston transport, φ0 = 0.15 | assumption, proxy only |
| Sensing metrics (T_ring, reach) | definitions chosen here; reach went through three versions (above) |
| In-band designs are sub-isostatic, z 3.2–3.65 | result (GA + 8-realisation re-evaluation) |
| Toughness at fixed stiffness not improved by layout | result, within ±0.3 ×10⁻³ (1 SE, 8 realisations) |
| Aligned + sparse crossing locks: ~3.5× strain transmission at the same stiffness | result at W = 12 (8 realisations); at W = 16 the design falls just below the band (2/8 in band) while its transmission advantage over uniform-locked #47 persists |
| Graded layouts (pymoo front) in band | refuted at 8 realisations: none in band at both W = 12 and 16 (registry `topo-graded-front-8rep-20261101`) |
| Locking trades strain transmission for far-field reach and transport | result (association, partial correlation) |

**Scope of the ranking: 2D only.** Every design was evaluated on the 2D diluted triangular lattice of
`oxt/network.py`. No 3D generator exists in this repo, so nothing was re-evaluated in 3D. The front sits at
z ≈ 3.2–3.8, just below the 2D central-force isostatic point (4) but far below the 3D one (6). Bending-stabilised
onsets, how much an aligned layout gains and which layouts land in the stiffness window could all shift in 3D. Treat
the design ranking as a 2D model result, not a scaffold prescription.

**Evidence behind each claim.** Layout claims above rest on the 8-realisation re-evaluation at W = 12, with
the W = 16 run as a cross-check. The GA's own 2-realisation values are not used to rank designs: at the onset, G
varies by 0.5–0.8× its mean between realisations (main session's W = 16 phase map), larger than most layout effects.

**Crosslink chemistry is not a variable here.** The only crosslink parameter is a generic LOX/pyridinoline-type
junction lock (kx = 2e-3, k_rel = 1). The chemistry-specific `k_rel` values in `oxt/materials.py` are unfitted
placeholders and are not used. Nothing in this study ranks crosslink chemistries.

Limitations: 2D, small boxes (W ≤ 16, pore radius ≤ W/4), periodic images, linear response for all sensing
metrics (no strain-stiffening long-range transmission), quasi-static rupture with no viscoelasticity or remodelling,
and a short 4-generation search with 2 realisations per design during the search. Resilience was measured as uniaxial
pulls, not as an expanding organoid pushing on the pore.

## Next steps

1. **Search with more realisations, not more generations.** Realisation noise near the onset is larger than any
   layout effect on toughness. Use ≥ 6 realisations per design and a mean, or a chance-constrained objective
   (P(G in band) ≥ 0.8), instead of a 2-sample worst case.
2. **Give organoid scaffolds a reproducibility objective**: the fraction of realisations in band. This is what an
   experimenter would see as batch-to-batch variation.
3. **Test the aligned + crossing-lock rule at W = 24–32 and under radial loading** (pore expansion), with the
   rupture pull replaced or supplemented by inflation of the pore.
4. **Re-evaluate the aligned + crossing-lock rule and the uniform baselines on a 3D network** (for example a diluted
   fcc lattice with bending, isostatic z = 6). This would need a new generator. Until then the ranking is 2D only.
5. **Add AGE dose** (`Damage("iso", d)`) to the best designs to see which layouts keep the organoid in band as the
   scaffold ages, connecting this to the main session's oxidative-crosslink phase map.
6. Replace the transport proxy with GAG-aware hindrance and binding before using it to rank designs.
7. Use the Hessian linear-response path (`topo_opt.linear_response`) for the FSS moduli runs. It removes the L-BFGS
   stall near the onset.

## Reproduce

```
python3 topo_opt.py --calibrate-yap
OMP_NUM_THREADS=1 python3 topo_opt.py --profile cpu32 --pop 26 --workers 26 --budget-min 40 --tag ga_W12
OMP_NUM_THREADS=1 python3 topo_opt.py --reeval results/topo/ga_W12_designs.csv --profile cpu32 --W 16 --reps 2 --workers 28 --max-designs 10 --tag reeval_W16
OMP_NUM_THREADS=1 python3 topo_opt.py --reeval results/topo/ga_W12_designs.csv --profile cpu32 --W 12 --reps 8 --workers 28 --max-designs 10 --tag reeval_W12x8
python3 analyze_topo.py --tag ga_W12 --reeval reeval_W16 reeval_W12x8
```
Set `OMP_NUM_THREADS=1` (and the OpenBLAS/MKL equivalents). Otherwise every worker's numpy linear algebra spawns one
thread per core.


## Cross-study validation context (31 October 2026)

The originating chat “Publish collagen artifact to WordPress” supplied a bounded
handoff from its [matched-stiffness study](https://humanavianaisymbiosis.wordpress.com/2026/10/31/matched-stiffness-collagen-network-relaxation-h100-results/).
The statements below are attributed handoff findings; this topology study has not
independently audited that study's trajectories or reproduced its estimates.

- That study reports architecture-dependent stress retention under selective axial
  relaxation, but an exact architecture-independent null when all energy terms
  relax homogeneously. Its stiffness matching rescales microscopic modulus per
  specimen; this is a different control from holding fibre parameters fixed here.
- It reports no universal architecture ranking for mean local RMS strain, and
  displacement non-affinity differences up to 60.5% between solvers despite stable
  stress/strain. Treat our non-affinity as a diagnostic pending solver checks.
  Our fibre-strain transmission metric still needs its own numerical validation.
- Later fracture curves remained resolution-sensitive in that study, including
  work-to-strain differences up to 29.5%. Our field named `toughness` integrates a
  finite prescribed pull: interpret it as **work to the terminal sampled strain**
  unless complete failure is demonstrated. First rupture, peak stress, and complete
  failure are distinct events. A coarse-step Pareto front cannot establish an
  ultimate-toughness winner without event/step refinement.
- Repeated solvers, load axes and resolutions are not independent graph specimens.
  Report graph-realisation counts separately from evaluation counts. In our current
  two-realisation design, axis and seed vary together; their separate effects
  require both axes on each of multiple held-out graphs.

Before promoting search candidates to scaffold design rules, validate held-out
seeds, both axes per graph, strain-step refinement around rupture, residual stress
at the terminal strain, and sensitivity to the background tether and sensing
metric. Compare matched connectivity and lock budget, and distinguish matching G
through topology from matching it through fibre-modulus rescaling. The handoff
provides no calibration of this study's chemistry, YAP window, or organoid response.

## Publication

Published 2026-10-31 as WordPress post 538,
<https://humanavianaisymbiosis.wordpress.com/2026/10/31/collagen-organoid-scaffold-topology-search-2d/>
(categories: Collagen & ECM Aging, Collagen Network Mechanics, ScienceClaw Hackathon, Simulation Results;
subscriber email and social sharing off; featured image = media 544, `results/topo/ga_W12_pareto.png`).
Body source: `results/topo/wp_topo_opt_draft.html`. Public page, image and all 8 internal links returned HTTP 200.
No existing post was edited; source and data are not in the public GitHub snapshot.

Corrected 2026-11-01 (user-approved, block-level edits; no other posts touched): an "Update · 1 November 2026" note in
the summary box, result 1 (window membership depends on box size), result 3 ("most reproducible" and "same stiffness"
are W = 12 only; #99 below band at W = 16), result 5 (graded wording), and a new section "Update, 1 November: a second
optimiser and a bigger box" summarising section 6. `results/topo/wp_topo_opt_draft.html` matches the live post block
for block; the pre-correction copy is not kept in the repo.
