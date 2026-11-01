# Collagen fracture scale-bridge: network → MOOSE

This package is the bridge between the fiber-network scale and the tissue scale of the
fracture pipeline:

```
molecular (LAMMPS)  ->  fibril (CG fiber)  ->  fiber network (oxt, notched networks,
irreversible failure, mixed-mode loading; OWNED BY ANOTHER AGENT — do not edit oxt/)
   ->  [THIS PACKAGE]  ->  tissue (MOOSE cohesive-zone FEM; NOT INSTALLED, needs
        a security review before anyone runs it)
```

`fracture_bridge/` only *reads* network outputs and *writes* parameter templates. It never
runs MOOSE and never touches `oxt/`. Repo rules apply: stdlib + numpy only.

Registry entry: `fracture-scale-bridge-20261031` (`experiments/registry.py show
fracture-scale-bridge-20261031`).

## Contents

| file | role |
|---|---|
| `extract_cohesive.py` | extraction adapter: curve loading (JSON/CSV), G_c integration, peak/δ_f extraction, incomplete-curve flag, mean ± sd aggregation across realizations, CLI |
| `moose_template.py` | renders the MOOSE CZM input-parameter template from extracted values (+ normalized PWL curve tables) |
| `test_extract.py` | unit tests incl. synthetic triangular law with known G_c and incomplete-curve flag; run `python -m fracture_bridge.test_extract` |
| `synthetic_check.py` | 8-realization noisy synthetic dataset + recovery report + rendered MOOSE template |
| `results/synthetic_8r/` | artifacts of the synthetic verification (curves, summary, report, MOOSE template) |

## 1. Pipeline contract: network JSON/CSV → adapter → MOOSE

### Network-model output schema (what the network agent must emit)

One realization per JSON file (or a `bundle` with a `realizations` list):

```json
{
  "schema": "oxt-fracture-bridge/curve@1",
  "condition": "healthy-z3.5-age0",
  "mode": "I",
  "realization": 3,
  "units": {"delta": "m", "traction": "Pa"},
  "delta":    [0.0, 1e-6, "..."],
  "traction": [0.0, 5.1e4, "..."]
}
```

- `mode`: `"I"` (normal opening) or `"II"` (shear) — emit one curve set per mode for
  mixed-mode conditions.
- `delta`: crack opening / separation, strictly increasing, must extend PAST the
  failure point (traction fully decayed) — otherwise the curve is flagged incomplete.
- `units`: informational; see §2 — the adapter does not rescale, it reports what it is
  given.

CSV alternative: header `delta,traction` (one realization per file) or long format
`realization,mode,delta,traction` (auto-grouped).

### What the adapter computes (per realization)

| quantity | definition |
|---|---|
| `G_c` | trapezoid integral `∫ max(T,0) dδ` over the recorded range |
| `T_max`, `delta_peak` | peak traction and its separation |
| `delta_f` | separation where the decaying branch first crosses `decay_threshold × T_max` (default 2 %), linearly interpolated |
| `incomplete` | `True` iff `T(δ_max) > decay_threshold × T_max` (curve truncated before failure). Then `G_c` is marked a **lower bound** and `delta_f` is `None`. A curve that ends at its peak is also flagged. |
| `K0` | secant stiffness to peak `T_max / delta_peak` |

Across realizations of a condition it reports **mean ± sd (sample sd, ddof=1)** for every
quantity, per-realization values, and the count/list of incomplete curves. `delta_f`
statistics use only complete realizations.

### Adapter → MOOSE

`moose_template.py` turns one condition's summary into a MOOSE **input-parameter
template** (DomainBoundaryCohesiveZone mesh block + CohesiveZone action + cohesive-law
material with normal/shear stiffnesses, max tractions, G_cI/G_cII, plus a normalized
PWL curve table). The template carries the mean ± sd values in its provenance header so
the MOOSE user can propagate uncertainty (worst-case, interval runs, or stochastic).

CLI end-to-end:

```bash
python -m fracture_bridge.extract_cohesive curves/*.json --label healthy-z3.5 \
    --json out/summary.json --moose out/healthy_czm.i
# or from an existing summary:
python -m fracture_bridge.moose_template out/summary.json --condition healthy-z3.5 -o out/healthy_czm.i
```

**The template is not a verified MOOSE input file.** MOOSE is not installed here and
needs a separate security review first (repo rule). Keyword names (especially the PWL
table parameters and the triangular-law class) drift between MOOSE versions; the template
header instructs the user to diff every keyword against the approved
`modules/solid_mechanics` checkout before running. The bulk material block is an explicit
PLACEHOLDER (see §4).

## 2. Physical calibration requirement (J/m²)

The current `oxt` network model is **dimensionless** (dimensionless linearized
strut-lattice; see AGENTS.md status table). A traction–separation curve from it has no
units, so G_c comes out in *model* units [force/length]. Before any MOOSE run, the
network agent must declare three scales and the adapter output must be converted:

- `L0` — length scale [m] (network edge length / fibre segment length calibration),
- `F0` — force scale [N] (fibre axial stiffness × L0, from fibril-scale LAMMPS/CG data),
- `h`  — out-of-plane thickness [m] of the 2-D network slab (the 2-D network is a
  cross-section; traction needs an area).

Conversion of a single realization:

```
delta_phys   = L0 * delta_model
T_phys       = (F0 / (L0 * h)) * T_model          # force per area [Pa]
G_c_phys     = ∫ T_phys d(delta_phys)
             = (F0 / h) * G_c_model               # [N/m] == [J/m²]
K0_phys      = (F0 / (L0**2 * h)) * K0_model      # [Pa/m]
```

Equivalently: run the adapter on physically-scaled curves (emit `units` in the JSON
schema and pre-scaled arrays) — the adapter reports whatever it is given, so **the
MOOSE template header states the units of its inputs** and refuses to call them
physical until the calibration constants exist. Representative collagen target:
dermis G_c ~ 10–1000 J/m², collagen films 200–2000 J/m²; a value far outside that
range flags a calibration bug, not a discovery.

## 3. Crack-path caveat: controlled notch first, phase-field later

A cohesive-zone model **prescribes where the crack goes** (interface elements on the
notch plane). That is exactly right for the first tissue-scale experiments:

- notched specimens (single-edge notch, trouser/peel geometry) where the crack plane is
  known by construction;
- direct, per-condition comparison with the network-scale G_c that produced the
  parameters (J-integral / energy-release-rate readback is the acceptance test);
- mixed-mode loading of the same predefined plane (mode I + II displacement components).

It is the **wrong** tool for spontaneous crack nucleation, branching, or deflection —
oxidative-crosslink gradients may steer cracks away from the cut plane, and a CZM
cannot represent that. Once the controlled-notch validation passes, extend to
**phase-field fracture** in MOOSE (length-scale `l_pf` calibrated from the same G_c and
T_max via `l_pf ~ G_c E / (c · T_max²)`), which allows arbitrary paths. Until then,
treat CZM results away from the notch plane as extrapolation, not prediction.

## 4. Offline fracture-law-library strategy

The network model is expensive (resolved, irreversible-failure simulations per
condition × mode × seed). The tissue-scale sweep is not. The strategy:

1. **Build the library offline**: run the resolved network model over the condition
   grid (crosslink chemistry × dose × z-connectivity × alignment × mode), extract
   with this adapter, and store `(condition, mode) -> {G_c, T_max, delta_f, K0,
   normalized curve, sd, n}` in a versioned JSON library file.
2. **MOOSE consumes the library** (templates rendered per condition on demand) —
   no network simulations in the loop.
3. **Interpolation for un-swept conditions**: nearest-neighbour or linear
   interpolation in condition space, with the *interpolation* flagged as such;
   linear interpolation of curves is only trusted between adjacent grid points.
4. **Send-back protocol for uncertain conditions**: a condition goes back to the
   resolved solver when ANY of:
   - it is flagged `incomplete` (traction never decayed) — re-run with larger max
     crack opening;
   - its nearest library neighbours disagree by more than a set fraction (e.g.
     G_c spread > 25 % sd/mean) — refine locally;
   - it is an interpolation more than half a grid spacing from any swept point.
5. **Uncertainty is not smoothed away**: every library entry keeps per-realization
   values and the sd; MOOSE runs quote parameter intervals, and negative/incomplete
   results are recorded (registry `refute` convention), not tuned away.

## 5. Verification status

- `test_extract.py` (19 tests, passing): known-G_c triangular law recovered to
  < 1e-12 relative; peak/δ_f extraction; incomplete-curve flag (truncation and
  ends-at-peak); JSON/CSV loading; mean ± sd aggregation; template markers.
- `synthetic_check.py` (8 noisy realizations, passing): G_c relative error
  mean −1.7e-4 ± 7.6e-4 (max |err| 1.1e-3); every adapter G_c cross-checked against
  the closed-form triangle energy AND an independent midpoint-rule integral.
- Registry: the synthetic G_c recovery was verified by a different calculation
  (closed-form + midpoint rule vs the adapter's trapezoid) — see
  `python experiments/registry.py show fracture-scale-bridge-20261031`.
- NOT verified / NOT done: no MOOSE execution (blocked on security review); no
  real network data has flowed through the bridge yet (waiting on the notched
  3-D network T(δ) outputs); physical calibration constants (§2) do not exist yet.
