# Matched discrete-solid / FEniCSx poroelastic microrheology

This is a hybrid calculation: the discrete collagen network supplies the exact solid Hessian from the published uniform-drag study; FEniCSx supplies a continuum fluid pressure field and Darcy/Biot coupling. It does not replace the network with a calibrated continuum solid.

## Matched design

40 specimens = two sizes (100 and 196 nodes) × disordered and modular architecture × distributed and clustered effective crosslinks × five seeds (17, 29, 43, 67, 83). The added-link counts are 67 and 131. Each is solved intact and after removing the same three original collagen fibers nearest (0.55L, 0.50L), with x and y drive. L = 1.8 or 2.6. Reference node spacing is 0.2.

A virtual four-node probe near (0.35L, 0.50L) distributes a unit force equally and reads its weighted displacement. It is not a rigid bead or an optical trap. All outer solid nodes are clamped. Free-node response at distance ≥0.6 from the probe centroid defines remote RMS. Receiver sets are unchanged within a damage pair. Lesion/probe spacing increases from 0.36 to 0.52 with size, so comparing sizes does not isolate boundary effects.

The original normalized Hessian K (divided by the median reference collagen tangent stiffness for that skeleton; step 5e-7; sparse entries below 1e-13 dropped), collagen topology, crosslinks, lesion and unit nodal drag are preserved exactly. Uniform-drag results are replayed against the earlier published output. Both models linearize about zero prestress. Damage is imposed before probing; there is no additional failure during the harmonic measurement.

## Coupled equations and numerical implementation

Using exp(iΩt), the coupled system is

```
(K + iΩ I) u − Bᵀ p = f
 iΩ B u + (κ D + iΩ S M) p = 0.
```

M is the pressure mass matrix, D the Darcy Laplacian, and B the weak solid divergence operator with coupling coefficient 1. Storage S=0.1. Dimensionless fluid mobility κ=0.001 or 0.1. All pressure boundary nodes have p=0 (fully drained perimeter). Original background nodal drag I is retained in both models to isolate the additional fluid coupling. Mobility is unchanged after the lesion: no new hydraulic channel is inserted at the cut.

FEniCSx/DOLFINx 0.10.0 assembles real P1 triangular pressure, divergence and mass operators with PETSc. SciPy sparse complex LU solves the assembled frequency-domain block system. This is not a PETSc complex-build solve. One MPI rank is used. Frequencies are Ω=0,0.03,0.1,0.3,1,3 for uniform drag and the five positive frequencies for each coupled setting. Ω is not hertz.

The coarse pressure mesh triangulates the original jittered network grid; the fine pressure mesh subdivides each triangle into four. A piecewise linear prolongation maps the same original solid DOFs onto the fluid assembly mesh. Refinement therefore changes pressure resolution without changing K, collagen geometry or the solid DOF count. This controls a frequent confound in comparing continuum and discrete models.

## Validation and exclusions

- Linear-system residual threshold 1e-8; singular or inaccurate solves are flagged. A free zero-stiffness motion can make a static drag response nonunique even if positive-frequency damping resolves it.
- Removing the coupling must recover the matched drag response to relative error below 1e-10.
- Assembled divergence applied to u=(x,y) must reproduce constant divergence 2 to relative error below 1e-10. Integrated mass must reproduce domain area, and the Laplacian must annihilate a constant.
- A manufactured drained Darcy-Poisson solution sin(πx/L)sin(πy/L) must improve its L2 error by a factor greater than 2.5 on refinement.
- Published drag replay must agree with prior algebraically valid results within 1e-5 relative error.
- Coupled response must be passive under the chosen harmonic convention.
- A paired observable is pressure-mesh qualified only when intact and damaged magnitudes each change by at most 5%, and the damaged/intact ratio changes by at most 0.5 percentage points. Tables require both drive directions per seed. These thresholds are practical screening criteria, not a proof of continuum convergence.

Frequency plots include all algebraically resolved fine-mesh responses, including ones that may fail the mesh comparison. The damage-ratio figure and summary table include only qualified full seed pairs. Data retain all values and flags. Seed ranges are descriptive and are not confidence intervals; x/y directions from one seed are not independent biological samples.

## Animations

Example fields use 196-node seed 17, x drive, Ω=0.1, κ=0.001 and the fine pressure mesh. The first view compares damaged poroelastic displacement with matched damaged uniform drag. The second displays poroelastic damaged-minus-intact displacement and pressure. Every frame is the real part of a complex phasor times exp(i phase), with fixed pressure/vector scales across the four architecture/placement panels. Arrows are enlarged. The GIFs reconstruct one oscillation, not progressive failure or a newly computed transient.

## Biological and physical scope

Parameters are normalized exploratory choices. No permeability, storage, physical frequency, three-dimensional collagen architecture or species/age calibration is inferred. This is not a prediction of human or beaver tissue, microrheology-derived storage/loss moduli, mechanotransduction or clinical damage. The central lesion sits near the crosslink cluster; protection here cannot establish a universal ranking across lesion sites. Real damage may alter permeability and prestress, and a continuum fluid field does not resolve flow through each fiber-scale pore. Further pressure refinement, alternative drainage, mobility changes at damage, 3D geometries and experimentally calibrated parameters are separate questions.

## Runtime provenance

Official FEniCSx image, pinned Linux amd64 manifest:
`ghcr.io/fenics/dolfinx/dolfinx@sha256:f3e532f96eb91454f13e7aae5289990cd0348124302c003a2002b4cfadb26b1a`

The runtime was reviewed statically before remote execution. No third-party runtime was executed on the Mac. The remote child used a scrubbed environment, UID/GID 65534, bounded CPU/time/output, and socket denial after MPI/runtime initialization. See the source archive and security review for residual binary provenance and initialization-window risks. Exact versions, residuals, refinement errors and file hashes are in the result records.

DOLFINx API reference used for the corrected mesh constructor: https://docs.fenicsproject.org/dolfinx/v0.10.0.post0/python/generated/dolfinx.mesh.html#dolfinx.mesh.create_mesh .
