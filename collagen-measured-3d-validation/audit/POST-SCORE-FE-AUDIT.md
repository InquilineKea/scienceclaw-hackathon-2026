# Independent readback after the frozen spatial test

2026-10-31. The parent completed candidate selection on Pos007, wrote SPATIAL-MODEL-FROZEN.json and scored Pos008 once. This audit does not refit parameters, change masks, rerank candidates or alter those outcomes. It uses an independently authored Python standard-library element operator and reads the saved predictions as inert data. No Saenopy, numerical package or production solver is imported.

## Mathematical and numerical readback

The original JavaScript P1 tetrahedral gradients, Lamé stress, elastic and vector-harmonic operators, analytical Jacobi diagonal and free-DOF Dirichlet elimination are correct on static review. CG preserves zero constrained correction components, so its free-block operator is symmetric; it does not make the row-only-overwrite mistake. The code independently recomputes its free equilibrium residual after iteration. Physical coordinates and displacements are both converted from meters to micrometers, giving dimensionless strain. Material coefficients are normalized and no absolute force or modulus identification follows from this displacement-controlled solve.

`independent-fe-readback.py` separately reconstructs every tetrahedron's shape gradients with cross products, assembles the internal vector and energy, checks the exact boundary constraints, independently reconstructs the boundary-only mean offset and test mask, and recomputes every primary test score. Evidence is saved in INDEPENDENT-FE-READBACK.json.

For Pos008:

- All stored centered measured targets exactly equal raw image-derived PIV displacement minus the mean computed **only from supplied valid boundary nodes**.
- The current main source hash and all frozen mask hashes match the selection record.
- Harmonic relative free residual independently recomputes as9.38e-9; selected elastic residual as9.50e-9. Both boundary-value max errors are zero.
- Applying a constant translation to the full field changes the independently assembled operator by relative2.2e-15/2.4e-15. Energy invariance under that translation also passes.
- Energy agrees with one-half u·Ku to relative2.7e-15/1.7e-14.
- Primary equal-octant vector MSE is reproduced exactly for all four stored reference/model fields.

These are implementation checks, not experimental adequacy or independent material calibration.

## Frozen test outcome

Primary equal-octant vector RMSE on the4,355 scored valid nodes is2.99026µm for the centered zero predictor,1.69315µm for the boundary-fit affine predictor,1.06214µm for vector-harmonic interpolation, and1.17353µm for the selected elasticν=0 baseline.

The selected mechanical baseline has51.961% lower MSE than affine motion but22.074% **higher** MSE than the harmonic interpolation baseline. Harmonic has lower squared error in six of eight correlated octants. This does not support a claim that the tested mechanical law beats the best kinematic baseline. It also does not measure collagen's Poisson ratio: ν=0 is a candidate chosen under this discretization, domain and input contract, not a separately measured parameter. No biological significance test or independent specimen replication can be inferred from octant/vector counts.

## Actual boundary/domain interpretation

The implementation retains all76,176 original sampling tetrahedra. It does not cut a cell cavity out of the mechanical mesh. The mask supplies nodes within30µm of reference-intensity cell samples plus **one** outer nodal layer, not the draft's proposed two-layer shell. Missing prescribed vectors become free degrees of freedom:151/181/212 nodes on Pos004/Pos007/Pos008. Pos008 supplies3,385 valid prescribed nodes out of3,597 initially designated nodes.

The actual test is therefore a partial-Dirichlet continuum box with internal nodal constraints and zero applied nodal force elsewhere, including missing-input nodes and artificial material retained inside the cell region. It is not a complete independently observed cavity-boundary-value problem. Keeping this as a clearly named conditional interpolation test is legitimate; calling it measured cell-cavity mechanics or absolute force propagation would overstate the implementation. A cut-out mesh, complete-boundary interpolation rule or alternative treatment of missing inputs would define a new/post-test sensitivity and must retain the original outcomes. The protocol should record the executed one-layer/partial-constraint choices rather than silently retain the proposed two-layer wording.

The exact support-purge rule was included before scoring and remains intact. Missing test vectors were excluded by the source finite mask rather than their prediction error. The octants are Cartesian blocks about the sampling-box origin, not independently fitted cell-centered material axes. They are correlated averaging blocks, not eight biological replicates.

## Strain and measurement resolution

The stored strain metric is the Frobenius norm of raw P1 tetrahedral gradients on roughly15µm vector spacing; the off-diagonal factors of two are correct. It is not the >=35µm support-averaged strain operator proposed in the draft. Pointwise FE predictions have not been passed through a calibrated DVC/PIV measurement operator either. Preserve those raw-strain scores as derivative descriptors/exploratory outputs, not resolution-matched local-strain validation.

The parent's proposed new5³/9³ complete-neighborhood least-squares gradient diagnostic is appropriately **post-test** if it keeps the selectedν and all original scores unchanged, uses physical coordinates, fits an intercept, applies the same operator to observed and predicted fields, and requires every neighboring vector to remain valid and in the frozen held-out mask. Report absent neighborhoods/octants instead of shrinking the support after seeing errors. A neighborhood wider than35µm is a declared support-averaging sensitivity, not proof that the exact DVC measurement transfer function has been reproduced.

The secondary NRMSE uses the observed held-out RMS as its denominator. That is a descriptive outcome-based metric, not a prediction/fitting input, and rankings within a specimen remain determined by the primary MSE. It differs from the draft's stricter training-only normalization wording; document this metric definition explicitly. Physical RMSE remains primary and avoids a near-zero normalization ambiguity. Independent measurement/boundary uncertainty is still needed before any adequacy pass/fail claim.

## Further geometry/reader cautions

The bounded nearest-cell search stores31622.8µm sentinel values for far nodes. Its search covers all distances needed for the30/65µm masks, so this does not invalidate those masks, but `cell_distance_um` is not a valid full-domain radial-distance field. Recompute global distances using geometry only before any radial-decay plot, and label that change as a geometry diagnostic.

The actual TIFF decoder handles the observed uncompressed8-bit four-strip files, including out-of-line offsets. For future inputs it should reject unexpected photometric interpretation, orientation, next-IFD layout and out-of-bounds tags rather than silently interpreting them as the observed format. Actual source hashes and metadata-only header audits are retained separately. NPY object arrays remain rejected; explicit null+finite masks now replace invalid JSON NaNs in extracted measurements.
