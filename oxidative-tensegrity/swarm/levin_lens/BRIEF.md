# Brief for the Levin-lens and open-endedness reviewers (2026-10-31)

You are reviewing a hackathon model (MIT ScienceClaw, 2026-10-30 to 11-01). The full source files are attached
after this brief. This page summarises what the model does, what it has shown, and what has been withdrawn, so
that you do not rebuild claims the project has already retracted.

## What the model is

A multiscale model of how oxidative and AGE (advanced glycation end-product) collagen crosslinks change tissue
mechanics and mechanotransduction:

- `oxt/network.py`: 2D diluted triangular fibre network at mean connectivity z (isostatic point z = 4 in 2D),
  stretching + bending + locked-junction angular springs + elastin + GAG embedding. LOX-type crosslinks "lock"
  junction angles; oxidative/AGE crosslinks add bridging links, stiff brittle intrafibrillar segments and locked
  junctions. Bond rupture under load.
- `oxt/gag.py`: GAG models (bridge, sliding, polyelectrolyte) under cyclic load; sliding is blocked at
  crosslink-locked junctions (an imposed rule).
- `oxt/cell.py`: motor-clutch adhesions on the network's nonlinear secant modulus, a 6-strut tensegrity cell
  whose basal face is closed by the matrix, YAP = f(adhesion force) x f(prestress reaching the nucleus), a
  YAP -> myosin positive feedback, and a linearised "recovery rate" of that loop.
- `oxt/organoid.py`: an epithelial organoid in a collagen gel; growth strains the gel, each cell runs the cell
  model, YAP and a prestress (MRTF) proxy drive a small gene network (CTGF/CYR61/ANKRD1, AMOTL2 negative
  feedback, LOX stiffening, MMP14 softening, Wnt delivery through the gel). All gene parameters are assumptions.
- `oxt/physio.py`: lumped tissue/organ read-outs (transport, heart, artery). Not central here.

There is **no** bioelectric layer, **no** gap-junction coupling between cells, **no** vimentin or other
intermediate-filament network, **no** cell-cell mechanical coupling except through a shared gel in the organoid
model, and **no** memory/hysteresis test. Each cell is one tensegrity unit.

## Results the reviewers may use (SIMULATED, model output, trends not absolute numbers)

1. Stiffness is dominated by connectivity z. Healthy Col I shear modulus G rises ~260x from z = 2.8 to 5.0
   (16x16 lattices, 4 seeds). AGE dose 1 multiplies G ~14x at z = 2.8 but only 1.4-2.2x above z = 4.
2. Crosslinks erase strain stiffening: K(gamma=0.4)/G0 at z = 2.8 is 8.8-14.7 in healthy networks, 3-4.6 at
   AGE dose 1, ~1.1 for every network at z = 5. The matrix loses mechanical dynamic range before it gets much
   stiffer.
3. Anisotropic crosslinks make the network anisotropic (Cx/Cy 1.2-3.6); isotropic ones do not.
4. Col I becomes brittle: strain at peak stress 0.20 -> 0.08-0.11 with crosslinks. **Caveat:** damaged segments
   receive an imposed 0.45 rupture-strain multiplier, so part of this is by construction.
5. Cells: YAP saturates on matrices stiffer than ~1 kPa. The YAP response band is E ~ 120-285 Pa in this model
   (`results/topo/yap_band.json`). Healthy Col VII holds only 14% of rigid-anchor prestress and is not
   self-supporting; crosslinked Col VII becomes self-supporting.
6. GAG sliding: dissipated fraction per load cycle falls from ~0.55 (dose 0) to 0.02-0.10 (dose 0.5-1) while
   stiffness rises ~6x. Partly imposed by the pinning rule, partly emergent.
7. Phase map (in progress; only a small "smoke" run is complete, 8x8 lattices, 1 seed): rigidity onset (steepest
   dlogG/dz) at z ~ 2.6 with LOX locking 0 or 1, shifted to z ~ 3.0 at AGE dose 1; LOX lock 1 makes failure
   brittle (single-step stress drop > 50%) above z ~ 4.6; toughness peaks at z ~ 5.5-5.9 on these small lattices.
   A 12x12, 4-seed run is half done; do not treat these numbers as final.

## Withdrawn or narrowed claims (do not rebuild them)

- "Dityrosine is the stiffest crosslink" and "glucosepane is no stiffer than pyridinoline": withdrawn. Atomistic
  stretch scans mostly measured the starting conformer of each fragment.
- "The YAP-myosin recovery-rate dip is critical slowing down / an aging clock": narrowed. The maximum loop gain
  in the saved scenarios is 0.23 against a bifurcation at 1; no bistable rows; the recovery-rate variation is
  real within the model but proximity to a tipping point is not shown.
- GAG dissipation loss and brittleness both contain imposed rules (pinning; 0.45 multiplier) that need ablations.

## External anchors the project already uses (verified)

Burla et al. 2020 PNAS (collagen network fracture vs connectivity, optimum near z ~ 3-4); Sharma et al. 2016
Nature Physics (strain-controlled criticality in fibre networks); Petridou et al. 2021 Cell (rigidity
percolation in the zebrafish blastoderm); Teuscher et al. 2024 Nat Commun (ECM stiffening, YAP-1 and longevity in
C. elegans); Ewald et al. 2015 Nature (collagen remodelling in longevity).

## What the project wants from you

Concrete, testable bridges between this collagen/ECM network model and (a) Michael Levin's published research
programme and (b) open-endedness research. Bridges must say which part of the model they hook into, what it
predicts, what experiment would test it, and what result would falsify it. Flattering analogies with no
measurable consequence are not useful.
