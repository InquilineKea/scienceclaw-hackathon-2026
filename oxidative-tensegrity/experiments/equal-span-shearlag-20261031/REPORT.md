# Linking the spatial metric to stiffness: equal-span controls, glucosepane density, atomistic power and cost

Claude Code, 2026-10-31 (local CPU only; no cloud jobs). This continues the Codex ColBuilder thread.
Sources: `/Users/simfish/Documents/Codex/2026-10-30/can-you-read-https-drive-google/outputs/colbuilder-study/`.
Code is `equal_span_shearlag.py` and `atomistic_power_plan.py`; outputs are in `results/`.

## 1. Toy shear-lag model: dispersal effect is load-transfer span, not clumpiness

Codex's 16-case three-owner toy compares clustered junction centres [12,13,14,16,17,18]/30 with dispersed
[3,8,13,17,22,27]/30. These sets span 0.2 L and 0.8 L respectively, so the reported "dispersing
raised K by 15% (2-owner) / 30% (3-owner)" mixes clumpiness with load-transfer length.

**Independent reimplementation.** Junction coordinates are explicit DOFs joined by κ arms, solved with
`numpy.linalg.solve`; Codex instead used condensed κ/3 pair springs with its own Cholesky. This
reproduces all four primary staggered K values to ≤5×10⁻⁸, which is the rounding of the published
7-digit values. The all-ends values are 3.0126–3.0130. Refining the mesh 2× and 4× with the same
physical sites leaves K unchanged to 1e-13, as expected for point-loaded linear elements.

**Equal-span controls (same model, same loading, same KDE definition C at h/L=0.05).**

| Set | span/L | C | K (2-owner) | K (3-owner) |
|---|---:|---:|---:|---:|
| dispersed (original), even | 0.80 | 1.07 | 0.818 | 1.053 |
| two end clumps | 0.80 | 2.46 | **0.940** | **1.144** |
| centre clump + endpoints | 0.80 | 1.99 | 0.782 | 1.006 |
| left clump + right endpoint | 0.80 | 2.95 | 0.694 | 1.031 |
| mirror: right clump | 0.80 | 2.95 | 0.888 | 1.031 |
| clustered (original) | 0.20 | 3.10 | 0.710 | 0.810 |
| clustered shifted ±9 nodes | 0.20 | 3.10 | 0.710 | 0.810 |
| even, spacing 1→5 nodes | 0.17→0.83 | 3.62→1.04 | 0.703→0.832 | 0.798→1.077 |

In 3000 random 6-junction layouts:

- **3-owner:** span alone explains R²=0.90 of K. Adding C raises this to 0.903, and adding centroid to
  0.904. Within span bins of width 0.1 L, C explains ≈0 of K for spans ≥0.5.
- **2-owner:** span explains R²=0.46 and C adds nothing (0.457). The large remaining within-span spread
  (up to 31% K range) is not clumpiness. It comes from which owner holds two sites relative to the
  staggered grips. Mirror-image layouts with identical span and C differ by 28% (0.694 vs 0.888).

**Conclusion.** In this toy, "dispersed is stiffer" is a load-transfer-span effect. At equal span, a
*more* clumped layout (two end clumps) can be the stiffest. A compact cluster gives the same K wherever
it sits, because the series path length is unchanged. The KDE concentration C therefore does not
predict K even inside the model that produced both numbers. Codex's equal-KDE/different-K controls
(ownership, grips) already showed this; these controls extend it to placement.
The model is still a dimensionless scalar toy with no chemistry, rupture or transverse mechanics.

## 2. Is the atomistic glucosepane density realistic?

**Measured from the deposited model:**

- 34,754 Cα correspond to 11.02 collagen-I molecule-equivalents (3154 Cα per molecule).
- The dry structure spans ~67 nm (one D-period); 41–60 triple-helix segments cross each axial plane.
- All 10 GLU bridges are the same residue pair (AGS523/LGX286) inside a **0.25 nm axial band** at
  z = 46.2–46.5 nm.
- The 20 PYD bridges sit in two bands at z ≈ 33.6 and 61.1 nm.

**Literature:** old non-diabetic skin reaches about 2000 pmol glucosepane per mg collagen, and diabetic
skin about 4000–4300 pmol/mg (Sell et al., 2005, JBC 280:12310; Monnier review). At about 290 kDa per
molecule, 1 mg is 3.45 nmol of molecules. That gives **≈0.58 glucosepane per molecule (old) and ≈1.2
(old diabetic)**.

**Model:** GLU5 is 0.45 per molecule (≈0.8× old skin) and GLU10 is 0.91 per molecule (≈1.6× old skin,
≈0.75× old diabetic). **The bulk density is in the aged range.** The placement is not: one site is about
90% occupied (10 bridges per ~11 molecule-copies) while every other site is empty. Mass spectrometry
finds glucosepane spread over many sites, mostly in overlap regions (2026 human cortical bone).

The clustered and dispersed GLU5 arms differ only *laterally* within one plane, so they cannot
test axial clustering.

## 3. Atomistic four-arm study: global slope is underpowered; local readouts are feasible

Assumptions are E = 0.3–2 GPa, protein area = (41 segments) × 1.3–2.0 nm², and ρ = 1.2 g/cm³.
Both the protein area and k depend on these assumptions. Using the water-box area would overstate k
by 5–7×.

- **Acoustic transit across L0 = 65 nm is 50–130 ps.** Codex's commissioning cycle uses 5-ps ramps at
  10⁹ s⁻¹ (grip speed 65 m/s). Its dF/dq is therefore an inertial/viscous transient, not an elastic
  slope. Ramps and holds need to be at least ~300 ps.
- **Global slope precision.** Equipartition bounds the relative SE of the slope at 6–20% per
  independent sample. Detecting a 1% arm difference (80% power, α=0.05) would need **25–1260 ns per
  arm**. Even the published short-peptide 3–8.5% range needs 0.3–17 ns per arm at an integrated
  correlation time of 20–100 ps. Five extra bridges against 20 PYD and thousands of contacts are very
  unlikely to give a 3% global change. **Recommendation: do not report a global force–extension slope
  difference from this design.**
- **Local readout per bridge site.** Measure the relative axial sliding of the two attachment segments
  (±2 nm around each bridge, affine part removed), paired with the *same residue pairs* in native0,
  where they are unbridged. Assuming local fluctuations of 0.05–0.1 nm with a 5–10 ps correlation
  time, 200-ps holds give an arm-contrast MDE of 0.016–0.046 nm (5 sites × 3 replicas). That is well
  below the likely ~0.1 nm unbridged sliding at 1% strain, though that sliding magnitude is an
  assumption to check in native0. Add section traction across z = 46.3 nm versus untouched planes,
  computed from pairwise forces, never per-atom totals.
- **Cost.** Throughput has not been measured; assume 3–6 ns/day on the L40S at 1 fs.
  - The full revised schedule (1.9 ns per run: 300-ps ramps and holds to 2% plus 600-ps drift) for
    4 arms × 3 replicas is 91–182 GPU-h, costing $195–390 on L40S or $290–580 on H100. That is
    23–46 h of wall time on 4 GPUs, which **does not fit before the Sunday-night account deletion.**
  - **A version that fits:** native0 vs GLU10 only (the largest contrast) × 3 replicas, 1% strain only,
    about 1 ns per run. That is 6 runs × 4–8 h, or 4–8 h wall time on 6 GPUs, for roughly $60–200.
    It needs new paid instances (user approval) and Codex's own EM/NVT gates on GLU10.
  - Pulling to failure (≥10% strain) is out of reach atomistically before the deadline.
- **Gate first.** Codex's 10-ps restrained NVT on native0 gives measured throughput; re-cost from it
  before allocating.

## What this does not show

The toy is dimensionless and says nothing about PYD or AGE chemistry. The power figures are order of
magnitude, from equipartition with assumed E, area and correlation times. Nothing here is MD.
The fibril-modification model's mesh-sensitivity issue (treatment effects smaller than the 9–10% stress
and 53–56% sliding sensitivity) is not addressed here. Its fix is to freeze physical site coordinates
and contact randomness, then map them onto each mesh.
