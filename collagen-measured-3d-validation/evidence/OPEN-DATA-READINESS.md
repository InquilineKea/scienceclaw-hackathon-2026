# Final primary dataset update

The final benchmark uses the larger public ClassicSingleCellTFM v0.7.4 archive: three cubic measured collagen image pairs, positions004/007/008, with24×24×25 PIV samples per position. The initially attractive organoid example discussed below is secondary because its actual PIV grid is24×24×3 and is too thin for the guarded interior test. See REPORT.md and CLASSIC-GEOMETRY-INVENTORY.json for final scope; the evidence search below is retained as history.

# Open measured 3D collagen data: verified files and a defensible first test

Evidence audit, 31 October 2026. Public archives and primary publications were inspected as data. No downloaded code was executed, no packages were installed, no authors were contacted and no compute or publication was initiated by this audit.

**Practical recommendation:** Begin with the small, actually downloaded Saenopy intestinal-organoid example for a measured-image / local-displacement challenge. It supplies real 3D collagen reflection images and image-derived displacement estimates, together with the publication's bulk rheology tables. It does **not** supply a measured fiber graph, independent cellular force truth, same-specimen bulk rheology, or independent biological replication. A boundary-conditioned prediction of withheld interior displacement regions is a narrower defensible test, subject to the gates below. No dataset recovered in this bounded search supplies the entire requested combination of specimen-linked measured 3D graph, independent held-out rheology, and independent local-strain observations.

## 1. Verified small measured-image candidate: Saenopy / Nature Physics 2024

Primary study: [Böhringer et al., Dynamic traction force measurements of migrating immune cells in 3D biopolymer matrices](https://doi.org/10.1038/s41567-024-02632-8). The paper offers source data and says full raw images are available on request. Independently of that general limitation, the authors' [public Saenopy release](https://github.com/rgerum/saenopy/releases/tag/v0.7.4) contains working downloadable example images and evaluated results. Their [organoid tutorial](https://saenopy.readthedocs.io/en/stable/3d_tfm/auto_examples/4_OrganoidTFM.html) identifies the actual sample and imaging protocol.

| Verified public file | Downloaded bytes | SHA-256 |
|---|---:|---|
| [4_OrganoidTFM.zip](https://github.com/rgerum/saenopy/releases/download/v0.7.4/4_OrganoidTFM.zip) | 16,345,299 | `20da6febe89e7d95f277ffc0f2db0efba4c180c689266cc0c20c096f9fea4190` |
| [4_OrganoidTFM_evaluated.zip](https://github.com/rgerum/saenopy/releases/download/v0.7.4/4_OrganoidTFM_evaluated.zip) | 1,026,883 | `d896a5f81c29af030f765eb67ea9129d4f5ed9857910250c34f73f096cc313dc` |

The image ZIP contains 104 TIFFs: two 52-slice stacks of one intestinal organoid in 1.2 mg/mL collagen, approximately 23 h after embedding and after drug relaxation about two hours later. The contracted series is labeled `t50`; the lower `t6` index is the later relaxed reference because a new acquisition series started. The tutorial specifies Triton X-100 relaxation; the paper's organoid video describes cytochalasin D plus Triton X-100. Preserve this difference rather than silently declaring an exact treatment match.

The downloadable example declares voxel spacing 1.444 × 1.444 × 1.976 µm. The inspected first TIFF is 512 × 512, 8-bit grayscale, compression tag 259 = 1 (uncompressed), four strips of 128 rows. These are downsampled example dimensions, so use their spacing rather than substituting the original publication's finer acquisition spacing. Images represent measured reflection intensity; they are not an exported segmentation, centerline graph, junction map or fiber-diameter measurement.

The evaluated ZIP contains a `.saenopy` file that is itself a ZIP of typed `.npy` arrays. Inert ZIP/NPY-header inspection, without NumPy or pickle, establishes:

| Contents | Shape | Interpretation |
|---|---|---|
| `mesh_piv/0/nodes` | 1,728 × 3 | Positions of image-correlation samples |
| `mesh_piv/0/tetrahedra` | 6,348 × 4 | Correlation mesh, not measured fibers |
| `mesh_piv/0/displacements_measured` | 1,728 × 3 | Image-derived displacement estimates; uncertainty remains |
| Solver mesh nodes / tetrahedra | 15,625 × 3 / 82,944 × 4 | Computational continuum mesh |
| Solver displacements / forces | 15,625 × 3 each | Inverse-model outputs, not independent force observations |
| Displacement targets and masks | Present | Inputs/interpolations used in reconstruction |

The example uses a semi-affine constitutive law and regularized inverse force reconstruction. Agreement between reconstructed displacements and their fitted targets is not a new forward validation. The forces cannot be treated as independently measured loading for a second model. The general article identifies the organoid demonstration as batch C; no specimen identifier linking this example to an individual bulk rheology replicate was recovered.

### Public bulk rheology files actually retrieved

The primary article HTML advertises nine source-data XLSX files; these were downloaded as data and inspected only through ZIP/XML sheet names, shared-string labels and dimensions. Numeric rheology outcome cells were not inspected or used to choose a holdout.

- [Source file 21, Extended Data Fig. 2](https://static-content.springer.com/esm/art%3A10.1038%2Fs41567-024-02632-8/MediaObjects/41567_2024_2632_MOESM21_ESM.xlsx): 4,501,238 bytes; nonlinear strain/stress tables, sheets Batch A, Batch B and Batch C, concentration labels 0.6, 1.2 and 2.4 mg/mL, and stress standard-error labels. These are publication source tables; do not assume every row is an independent replicate. Exact checksums and sheet dimensions are recorded in the companion JSON inventories.
- [Source file 22, Extended Data Fig. 3](https://static-content.springer.com/esm/art%3A10.1038%2Fs41567-024-02632-8/MediaObjects/41567_2024_2632_MOESM22_ESM.xlsx): 13,623 bytes; Batch A frequency-response means/SD at the three concentrations, storage-modulus summaries and loss tangent. Frequency is labeled angular frequency in rad/s; do not confuse it with Hz. **Batch A frequency data are not batch C organoid-specific calibration.**

Batch C nonlinear response offers a relevant external mechanical challenge for the organoid example, but it still does not establish same-specimen matching. The prospective statistical split reserves Batch C completely: Batch A nonlinear curves fit parameters, Batch B selects the model family, and Batch C tests the frozen choice. Do not fit the Batch C curve before presenting it as held out. Frequency-source summaries constrain bulk storage/loss behavior; local quasistatic images alone cannot validate G′ and G″ across frequency. No held-out frequency batch has been identified.

### License and publication boundary

The Saenopy repository has an MIT-style software/documentation license. Neither downloaded example ZIP contains a data-specific README or license, and the software license does not unambiguously resolve rights for every experimental image or evaluated data array. The Nature article is under its publisher's stated copyright terms. Public accessibility is verified; unrestricted raw-image redistribution is not. Keep the raw ZIPs in the research archive, link the authors' downloads, and preserve attribution. Before publishing image-containing animations or substantial derived image renditions, establish the applicable image-data license. Independently generated numeric comparison plots should cite the source and transformation, distinguish measurements from inverse outputs, and undergo the publication license check; this audit does not assert a blanket derivative-rights grant. No licensing request was sent.

## 2. Prospective local-displacement test that avoids fitted-force leakage

Freeze the data hashes, image coordinate conventions, reference direction, material law, geometry extraction settings, masks, and spatial partition before reading or optimizing against the withheld displacement outcomes. Use external bulk constraints where justified, with batch mismatch explicit. Define an exterior boundary and an organoid exclusion surface; impose measured displacements only on prespecified conditioning boundaries. Exclude the active cell region from passive-collagen equilibrium tests.

Predict an entire reserved interior region, separated from conditioning points by a buffer reflecting the correlation window and spatial dependence. Compare predictions with raw image-derived PIV displacements, with drift/noise/interpolation uncertainty. Derive strain only after selecting a documented smoothing/differentiation rule. Do not condition on all measured interior displacements, reuse inverse forces fitted to those targets, or choose segmentation/material parameters to improve held-out errors. Include an affine or homogeneous-elastic baseline. Report this as a **within-specimen, boundary-conditioned spatial prediction**, not independent biological, traction-force or fracture validation. One organoid example cannot establish generality across organisms, ages or network types.

## 3. Larger external candidate: NIST DVC Challenge 2.0

The [NIST public record, DOI 10.18434/mds2-4129](https://data.nist.gov/od/id/mds2-4129), lists `optical_data/Notbohm_Fibrous_S1.zip`: 1,483,787,647 bytes, SHA-256 `8b02a4e6ae885bd64278c1c7fe0fb010ce00198f6c3fa1a63cf3fa16aed9f2cc`. This is measured 3D fluorescence imaging of 2 mg/mL collagen I around a thermally contracting PNIPAAm inclusion. The paper describes image stacks before/after contraction and rigid-body drift. NIST metadata specify the [NIST open license](https://www.nist.gov/open/license). The full ZIP was not downloaded in this audit, so actual internal file content, completeness, segmentation, contraction boundary and available displacement tables remain unverified here.

The separate `synthetic_data/Notbohm_Fibrous_S2.zip` is synthetic fiber-image shear ground truth, not experimentally measured collagen. Use it for image-correlation verification, never as an experimental material validation. The [original measured-inclusion study](https://doi.org/10.1039/C7SM00561J) provides a useful nonuniform-load challenge; no same-specimen oscillatory rheology archive was established. NIST is the stronger explicit-license route if the smaller example's image rights remain unresolved.

## 4. Other primary repositories checked and excluded from the full claim

- [Dryad 10.5061/dryad.tr2f1](https://datadryad.org/dataset/doi:10.5061/dryad.tr2f1): actual advertised raw cyclic force archive (24.68 MB) and TEM images (606.32 MB). The images are en-face/transverse sections, not a measured 3D network or local-displacement volume. Useful mechanical challenge, insufficient architecture pairing.
- [Dryad 10.5061/dryad.gxd25481t](https://datadryad.org/dataset/doi:10.5061/dryad.gxd25481t): public file inventory includes rheology CSVs and SHG TIFFs for collagen–alginate interpenetrating hydrogels. The README identifies 4°C rheology and fiber-assembly imaging. Actual 3D stack depth and local displacement pairing were not verified, and the measured mechanics include the alginate network. Do not relabel it pure-collagen 3D validation.
- [2024 bovine/rat atlas figure archive](https://doi.org/10.12795/11441/188036): previously verified ten TIFF figures, not raw 3D graphs or specimen-linked displacement data. The [2025 bovine nanoarchitecture study](https://doi.org/10.1016/j.mtbio.2025.101962) states raw data are available on request. Neither presently removes the measured-architecture gate.

**Readiness conclusion:** Open measured 3D image data exist and a small paired-image example has been recovered with checked bytes and typed displacement arrays. This enables a narrower, carefully partitioned spatial mechanics challenge. Full measured-graph, independent rheology and local-strain validation remains a stronger claim requiring additional specimen/batch mapping, geometry/uncertainty work and validation data.
