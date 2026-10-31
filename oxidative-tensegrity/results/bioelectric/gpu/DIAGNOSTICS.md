# Sweep diagnostics (computed from conditions.csv / sheets.csv by Claude Code)

- At default parameters (G0=1, F50=400 pN, prestress-gated junctions) no cell switches to the depolarised branch
  (frac_depol = 0 for every condition). Depolarisation is graded on the hyperpolarised branch: sheet-mean Vmem goes
  from -68 mV (E ~ 10 Pa) to about -49 mV (E ~ 5-10 kPa). Some sweep settings (low F50, const junctions) depolarise
  whole sheets (max frac_depol = 1.0).
- Clutch traction rises with local stiffness and plateaus near 420 pN above ~2 kPa; at the stiffest networks
  (Col I z=4.4 dose 1, ~16 kPa) traction and depolarisation fall again (V_mean -61 mV): the motor-clutch
  traction optimum makes Vmem non-monotonic in stiffness.
- Pattern memory (q_hold, Col I z=2.8, iso): with constant junctions q_hold = 0 for every G0, F50 and dose. With
  prestress-gated junctions q_hold falls with dose, e.g. G0=1: 0.86 / 0.50 / 0.02 / 0.00 at dose 0 / 0.25 / 0.5 / 1;
  G0=0.25 keeps memory longer (1.00 -> 0.01-0.87 at dose 1). Memory exists only where low prestress weakens
  coupling, so its loss with crosslinking is the prestress-gating assumption strengthening coupling.
- Spatial imprint: Moran's I of Vmem is higher with the actual stiffness map than with the shuffled map in 95% of
  702 condition x parameter comparisons (mean +0.061). Skin 20 -> 80 y raises Moran's I slightly (e.g. actual,
  prestress, G0=1: 0.495 -> 0.526), the opposite direction from the keratinocyte data.
- Uniform vs actual: sheet-mean Vmem differs by a median of 0 mV but the dose contrast can differ strongly
  (Col I z=3.6: +24.6 mV uniform vs +11.9 mV actual; z=4.4: -50.4 vs -12.3 mV): heterogeneity smooths the
  response of mean Vmem to dose (averaging a nonlinear map).
- Skin dermis modelled dose is small: mean local E rises only 1.31x from 20 to 80 y (2.0 -> 2.6 kPa).
