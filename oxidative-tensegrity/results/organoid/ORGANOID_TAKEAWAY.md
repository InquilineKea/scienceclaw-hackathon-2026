# Collagen tensegrity networks → organoid gene expression: takeaway

Run 2026-10-31 on Brev `organoid-a6000-20261031` (RTX A6000). Code: `run_organoid.py`, `oxt/organoid.py`,
`make_organoid_figures.py`, `remote/brev_organoid.sh`. Data: `results/organoid/gpu/` (`SUMMARY.md`, CSVs,
`figures/`, `logs/`). **These are model outputs, not measurements.** The gene network, growth and
remodelling parameters are assumptions (see Caveats).

## What was simulated

- **156 gels**: Col I fibre networks at 6 connectivities (z 2.8–4.4, a proxy for collagen concentration and
  branching) × 4 crosslinkers (pyridinoline ≈ LOX, glucosepane ≈ ribose glycation, dityrosine ≈ photo/ROS, TG2
  isopeptide) × 3 doses × isotropic or aligned, plus native Col I and a soft Col IV "Matrigel-like" reference.
- **Network mechanics** (2D bond-bending lattice, float64 LBFGS): small-strain moduli and shear curve at W=32
  with 4 seeds on the GPU (624 networks, 70 min). Bond-rupture failure curve at W=16 with 1 seed on 26 CPU cores
  (61 min). Only the failure curve's peak strain and post-peak retention are used downstream.
- **Cell**: motor-clutch with talin reinforcement (torch, GPU) plus a 6-strut tensegrity cell. This gives
  nuclear YAP and transmitted prestress on a grid of organoid-imposed gel pre-strain (0–50 %) × remodelling factor
  (0.4–2.5×). That makes 7,020 cell conditions in 137 s.
- **Organoid** (7 days): a growing epithelial cyst strains its gel (viscoplastic hoop strain; crosslinks slow
  plastic relaxation). Five positions run from bud tip to inter-bud. The gene network has YAP targets CYR61, CTGF,
  ANKRD1, AMOTL2 (negative feedback), MMP14, LY6A (fetal/regenerative), an MRTF read-out ACTA2, and LOX.
  Wnt-dependent LGR5, KRT20 (differentiated) and MKI67 come from Wnt/R-spondin delivery through the gel
  (Ogston sieving plus binding). LOX stiffens the gel; MMP14 softens it, and crosslinks resist MMP14
  (`exp(-2.5·dose)`).
- **Analysis**: cross-validated prediction of each read-out from linear stiffness alone vs network descriptors
  (ridge and kNN). Also: 389 gel pairs matched within 10 % linear stiffness, and decoding the gel back from a noisy
  gene panel (15 % noise, 8 replicate organoids, folds split by gel). A control run removes AMOTL2 feedback.

## Takeaways

1. **Organoid size is the most reliable mechanical read-out.** By day 7, radius falls monotonically with gel
   stiffness, from about 150 µm in soft gels to about 55 µm above 10 kPa. Linear stiffness explains R² 0.90 of it.
   Native Col I reaches 121 µm (median), crosslinked Col I 66–77 µm, Col IV 146 µm. Measure size before
   sequencing anything.

2. **YAP-target expression is biphasic, with a wide plateau, so most crosslinked gels look the same.**
   YAP, ANKRD1, CTGF and LY6A rise from about 10 to 200 Pa, stay flat from about 200 Pa to 5 kPa, then fall above
   about 8 kPa (frictional slippage in the motor-clutch model). Crosslinked gels sit at a median 2–3 kPa, on the
   plateau. There, pyridinoline, dityrosine, TG2 and glucosepane give the same YAP-target levels (ANKRD1
   0.34–0.36 vs native 0.36). **Design implication:** to see a crosslink's effect through YAP, work on the
   rising arm (about 50–300 Pa, i.e. low-concentration Col I with light crosslinking) or the falling arm
   (>8 kPa). Mid-range gels collapse onto the plateau.

3. **Network nonlinearity did not add predictive power beyond linear stiffness. This is a negative result for
   the tensegrity-nonlinearity hypothesis in this model.** Strain stiffening, failure strain, mesh size and
   alignment did not improve prediction of any YAP target over linear stiffness, with either ridge or kNN
   (day 7 ANKRD1: kNN R² 0.74 from stiffness alone vs 0.66 with all descriptors). The reason: organoid growth
   pushes the gel interface to 5–16 % hoop strain, and crosslinked gels peak at only 10–15 % strain. So almost
   every gel is partly torn at the interface: 91 % of cell conditions at ≥20 % pre-strain have lost >10 % of
   their peak stress. Tearing therefore cannot separate gels. At matched stiffness most pairs differ by
   only 1–3 % of each gene's range (median). A few pairs differ by up to 77–91 %, but they sit in the soft,
   noisy part of the cell model (clutch noise SD 0.2–0.3 in YAP below 300 Pa), so treat them as unconfirmed.

4. **The gene panel reports stiffness, not crosslink identity or dose.** At day 7, radius + ACTA2 + ANKRD1 + LOX
   decode linear stiffness with R² 0.79. Connectivity (z) and mesh decode at about 0.66, failure strain at 0.41,
   and crosslink dose at only 0.22. Day 1 decoding is much weaker (stiffness 0.45). **Sample at day 5–7, not
   day 1.**

5. **Glycation has a non-mechanical channel that confounds stiffness studies (model assumption, but
   testable).** In the model, AGE-modified collagen binds Wnt/R-spondin-like ligands. At glycation dose 1, Wnt
   delivery falls from 0.71 to 0.35, LGR5 halves (0.41 → 0.21), KRT20 doubles (0.12 → 0.26) and MKI67 drops
   (0.69 → 0.52). Over the same range, LOX, TG2 and dityrosine leave these genes unchanged. LGR5, KRT20 and MKI67
   are essentially unexplained by stiffness (R² ≈ 0). So **ribose-stiffened gels are not a clean stiffness
   control**. Compare them with LOX- or TG2-stiffened gels at matched stiffness.

6. **AMOTL2 negative feedback compresses YAP from about 0.85 to about 0.5** but does not change which read-outs
   carry information (control run in `no_amotl2_feedback/`). Without it, LGR5 becomes partly stiffness-driven
   (R² 0.34), because high YAP suppresses LGR5 in the model.

## Proposed organoid experiment (follows from 2–5)

A 2 × 3 design. Crosslink route: ribose glycation vs TG2 or LOX. Stiffness: three levels matched by rheometry
across routes, all inside 50–300 Pa or straddling the 200 Pa knee. Add one arm with a freely diffusing Wnt agonist
(CHIR99021) to switch off the ligand-sequestration channel. Read out at day 5–7: organoid size,
then a panel of ANKRD1, CTGF, ACTA2, LOX (stiffness reporters) and LGR5, KRT20, MKI67 (Wnt reporters), ideally by
spatial transcriptomics for bud vs inter-bud. Predictions: the stiffness reporters track measured stiffness
whichever route made it. LGR5 and KRT20 diverge for ribose only, and CHIR99021 abolishes that divergence.
Failing either prediction falsifies the corresponding model channel.

## Caveats

- Gene-network gains, Hill constants, growth rate, stall stress, plastic time constant, Wnt binding and the
  AGE-binding factor are assumptions, not fits. Takeaway 5 is driven directly by the assumed AGE binding.
- The 2D lattice stands in for a 3D gel. The failure test is W=16 with 1 seed. The motor clutch runs 40 s and is
  noisy in soft gels.
- Open items from the Levin-lens critique (`swarm/LEVIN_LENS_CRITIQUE_20261031.md`): remodelling rescales
  stiffness but cannot change the strain-stiffening ratio (C1), and the five positions are uncoupled with an
  imposed cosine strain (C4). That is why bud/inter-bud contrast is near zero for most gels. Crosslink MMP
  resistance (C2) is now included.
- Pip installs on the Brev box pinned the direct packages, but transitive dependencies resolved to current
  versions (e.g. fsspec 2026.9.0, pytz 2026.6). The box held no credentials.
