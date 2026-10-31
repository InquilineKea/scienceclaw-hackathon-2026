# Explicit-solvent collagen–GAG binding free energy — accuracy upgrade to the rigid AIMNet2 scan

**Scripts:** `alchemi_collagen_gag_explicit.py` (pipeline) · `remote/brev_alchemi_explicit.sh` (GPU runner)
**Supersedes, for quantitative claims:** the rigid-scan contact energies in `alchemi_collagen_gag.py`.

## Why the rigid scan was not a binding free energy

`alchemi_collagen_gag.py` scans two **rigid** fragments along a fixed cation–anion axis and reports AIMNet2
short-range energy plus a **Debye–Hückel** screened-Coulomb term (fixed ε = 78.5, Debye length 0.8 nm). Its own
docstring is explicit that these are *contact energies to rank chemistries, not binding free energies*, because it has:

- no explicit water or counterions — only an analytic screening constant;
- no relaxation — fragments are frozen at their gas-phase MMFF geometry;
- no conformational or solvent entropy — a single pose, single conformer (`seed=11`).

For the biology question — *does glycation (CML-Lys, MG-H1-Arg; loss of the + charge) weaken the collagen–GAG
interface?* — a ranking can invert once real solvent screening and entropy enter. Hence the free-energy version.

## What the explicit-solvent pipeline does

Same chemistry (imported directly from `alchemi_collagen_gag`: `COLLAGEN_SIDE`, `GAG_SIDE`), now as a **potential
of mean force (PMF)** by umbrella sampling of the two fragments' centre-of-mass separation:

1. **Parametrise** each fragment with GAFF-2.11 + AM1-BCC (openmmforcefields / OpenFF / AmberTools).
2. **Solvate** in TIP3P with **0.15 M NaCl**, neutralised, PME electrostatics, 1 nm padding.
3. **Umbrella windows** every 0.05 nm from 0.30 → 1.45 nm, harmonic COM restraint k = 4000 kJ/mol/nm².
4. **Sample** each window (Langevin middle integrator, NPT via Monte-Carlo barostat, 2 fs, HBonds constraints),
   recording the COM distance.
5. **Unbias** all windows together with **MBAR** (`pymbar>=4`) → continuous PMF with analytic error bars.
6. **Binding ΔG** = PMF well depth relative to the dissociated plateau, with the spherical-shell → 1 M
   **standard-state correction** applied.

### Each step is a specific accuracy gain over the rigid scan

| Rigid scan | Explicit-solvent PMF | Why it matters |
|---|---|---|
| Debye–Hückel constant | TIP3P water + 0.15 M NaCl, PME | real dielectric screening & ion condensation around the sulfates |
| frozen fragments | full relaxation inside every window | removes the rigid-fragment artefact that dominates short contacts |
| single pose/conformer | thermal sampling | folds in conformational + solvent entropy → a *free* energy |
| arbitrary contact energy | PMF well depth + standard-state corr. | a binding ΔG in kcal/mol, comparable across chemistries |

## Running it

```bash
# full run, the four glycation comparisons at a 4-sulfate dermatan-sulfate (answers the core question)
bash remote/brev_alchemi_explicit.sh

# fast smoke test first (verify the toolchain and that windows overlap)
QUICK=1 bash remote/brev_alchemi_explicit.sh

# every collagen x GAG pair (12 PMFs — expensive)
PAIRS="all" bash remote/brev_alchemi_explicit.sh
```

Output `results/alchemi_gag/collagen_gag_pmf.json` carries, per pair: `dG_bind_kcal`, the raw well depth, the
well position `r_min_nm`, the full `pmf_nm` / `pmf_kcal` / `pmf_err_kcal` profile, and the standard-state term.
The expected, testable result if glycation weakens binding: `dG_bind_kcal` is **less negative** for
`CML-Lys|DS-4S` than `Lys|DS-4S`, and for `MG-H1-Arg|DS-4S` than `Arg|DS-4S`.

## Residual caveats (do not drop these from any writeup)

- **GAFF-2.11 is only approximate for sulfated carbohydrates.** For publication, re-run with GLYCAM06 or
  CHARMM36-carb on the GAG and compare; swap via `--sugar-ff` once those templates are available. AM1-BCC
  charges throughout.
- **Single COM separation coordinate** captures the dominant cation–anion approach, not every bound pose. For a
  rigorous *absolute* ΔG, follow with a double-decoupling / alchemical (FEP) calculation.
- **One disaccharide fragment**, not a full GAG chain or triple-helix context.
- **Convergence is not automatic:** confirm adjacent-window histogram overlap and block-average the ΔG before
  trusting it; lengthen `--sample-ps` if windows are sparse.

## Validation checklist before quoting a number

1. `QUICK=1` run completes and writes JSON without NaNs.
2. Adjacent umbrella windows overlap in the recorded CV (plot `*.traces.npz`).
3. PMF plateau is flat over the last ~3 bins (the unbound reference is real).
4. ΔG stable to within error when `--sample-ps` is doubled.
