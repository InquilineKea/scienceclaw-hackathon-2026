# Brief: collagen stiffness distributions and bioelectric ageing (in-silico test, 2026-10-31)

You are reviewing one new in-silico experiment from a hackathon model (MIT ScienceClaw). The code
(`oxt/bioelectric.py`, `run_bioelectric.py`) and its results (`SUMMARY.md`, `ageing_contrasts.csv`,
`conditions_default.csv`) follow this brief. Treat every result as model output, not measurement.

## Why it was run

Levin and colleagues frame ageing as a loss of morphostatic information or goal-directedness, carried partly by
bioelectric patterns (Pio-Lopez & Levin 2024, Ageing Res Rev; Pio-Lopez, Hartl & Levin 2025, Adv Sci). Measured
on senescing human keratinocytes (Sediqi & Levin 2025, iScience; one neonatal donor, cultures on poly-L-lysine,
days 10 to 50, BeRST lifetime imaging), the signature was:
- depolarisation;
- within-dish Vmem variability down about 38%;
- between-dish SD up 15–22×;
- global Moran's I down from about 0.5 to 0.13–0.26.

That study had no ECM, and its authors list ECM and mechanical gradients as missing from the culture model. The
question here: if cells read their collagen matrix, does the change in the *distribution* of local matrix
stiffness produced by oxidative/AGE crosslinking push a coupled Vmem sheet toward or away from that signature?
Does it change the sheet's ability to hold and restore a bioelectric pattern?

## What the experiment does

1. **Networks.** 2D diluted triangular collagen fibre networks, 64×64 lattice, 8 seeds per condition:
   - young to aged skin dermis (ages 20/40/60/80, crosslink dose from the project's turnover model);
   - Col I at connectivity z = 2.8–4.4 with AGE dose 0/0.25/0.5/1, in isotropic and anisotropic modes.
2. **Local stiffness map.** Under a global shear, network energy is split onto nodes and binned into 16×16 patches
   (one patch = one cell). An energy-equivalent secant modulus is computed per patch at 5 shear strains. The patch
   mean equals the global modulus exactly. Lattice units are converted to Pa by setting young dermis to 2 kPa.
3. **Cells.** Each patch's curve goes through the existing motor-clutch + 6-strut tensegrity cell, giving
   traction F, prestress ratio PS and YAP.
4. **Vmem sheet**, 16×16 periodic grid. Each cell has:
   - a bistable inward-rectifier K current (hyperpolarised about −68 mV or depolarised about 0 mV);
   - a leak;
   - a stretch-activated cation current gM = 0.6·hill(F; F50, n=4);
   - gap-junction coupling G0 to 4 neighbours, either constant or gated by prestress (`gj_mode`).

   **Depolarisation with stiffer matrix is therefore partly built in** through gM.
5. **Protocols.** *rest*: start hyperpolarised and relax, then report Vmem mean, within-sheet SD, fraction
   depolarised and Moran's I. *memory*: clamp a disk/surround prepattern, release, then measure overlap `q_hold`
   (1 = kept, 0 = lost). *restore*: flip 25% of cells of the held pattern, relax, then measure `q_restore`.
6. **Field controls**, which separate distribution effects from mean effects:
   - *actual* map;
   - *shuffled*: the same cells with positions permuted, which keeps the distribution and removes spatial
     structure;
   - *uniform*: every cell gets the network-mean curve, which removes the distribution.
7. **Sweep:** G0 ∈ {0.25, 1, 4} × F50 ∈ {300, 400, 500} pN × gj_mode ∈ {const, prestress}.
   "Between-sheet SD" is the SD of sheet-mean Vmem across the 8 seeds.

## What the project wants

Honest calls on what the model shows, what is built in, and what experiment would test it. No flattering
analogies. You are AI reviewers. Those applying Levin's ideas must not speak for him or imply his endorsement.
