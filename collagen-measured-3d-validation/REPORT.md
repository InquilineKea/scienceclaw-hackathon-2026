# Measured 3D collagen: held-out rheology and local-field benchmark

The public Saenopy ClassicSingleCellTFM example supplies three measured collagen reflection image pairs and separate image-derived displacement estimates. We used these data for a held-out internal field test, alongside the associated study's batch-separated nonlinear rheology summaries. The tests reveal substantial predictive errors. They do not establish a validated model of collagen aging or a measured fiber-connectivity model.

## Data and separation

Source: Böhringer et al., *Dynamic traction force measurements of migrating immune cells in 3D biopolymer matrices*, Nature Physics20,1816–1823(2024), https://doi.org/10.1038/s41567-024-02632-8 . Public measured images and evaluated PIV data: https://github.com/rgerum/saenopy/releases/tag/v0.7.4 . The source spreadsheets are the paper's Extended Data Fig.2/3 tables. No imported Saenopy code was executed. Published inverse-model forces and reconstructed displacement fields are never validation targets.

Bulk: batchA fitted, B selected, C tested without refitting or rescaling. The published curves are aggregate averages, not recovered raw replicate histories.1.2mg/mL is primary;0.6/2.4 secondary. Source strain-coordinate coverage required a pre-selection correction of the common target range from0.005–0.30 to0.005–0.19; the first attempted run stopped on its no-extrapolation guard before any frozen selection or C response score. The final26-candidate selection is preserved. These are nonlinear ramp tests, not held-out G′/G″ or rate-dependent validation.

Spatial: positions004/007/008 provide24×24×25 PIV samples over approximately354×354×357µm.004 is implementation/training;007 selects ν;008 is the held-out position. Exact specimen/batch-to-rheology mapping and independently measured applied forces are missing. The positions are not established as independent donors or batches. Imaging and bulk tests therefore remain separate.

## Main findings

At1.2mg/mL, the selected semi-affine fiber law has final-batch stress NRMSE0.685506 versus0.697353 for the linear comparator, with stress bias−8.8789Pa. This is only1.699% relative error reduction and substantial underprediction. The selected law has λs=.04,ds=.05,fixed d0=.0025 and concentration-specific scales fitted on A. Its small improvement does not establish accurate batch transfer.

On final position008, equal-octant displacement RMSE is1.17353µm for selected isotropic elasticity(ν=0), versus1.06214µm for harmonic interpolation,1.69315µm for an affine boundary fit and2.99026µm for zero centered displacement. Harmonic interpolation wins six of eight correlated octants. A mechanical model beating zero/affine while losing to interpolation is not evidence that its constitutive law explains the observed local field.

All4355 reference-eligible test vectors are finite in008;18931 all-eligible tets support the raw strain descriptor.3385valid prescribed nodal vectors are used, while212 geometrically prescribed nodes lack finite vectors and remain unconstrained. There are240 missing vectors overall. No finite large residual is removed. Test vectors are correlated observations, not4355replicates.

## Actual spatial operator and limits

The mesh is a regular image-correlation sampling mesh, not segmented collagen fiber paths or chemical crosslink connectivity. Linear P1 tetrahedral energy is V[λ/2(trε)²+με:ε], with μ normalized to1. ν candidates0,.25,.45 were selected only on007. The comparison harmonic operator is vector Laplace interpolation, explicitly not a collagen material law.

The operator retains all76176 tetrahedra, including material within the reference-cell mask. It imposes valid measured displacement on ONE outer-face node layer and nodes within30µm of the fluorescence-derived mask. It is an internally constrained partial-Dirichlet box, not a complete cutout cavity. Unknown boundary nodes have the natural zero-applied-traction condition; this is an assumption about a cropped interior volume. There is no independent force validation. Uniform stiffness cancels from the homogeneous displacement-boundary solve, so the field cannot identify absolute modulus or validate the rheology scale. Missing internal prescribed nodes can leave artificial material in the cell region; that limitation is retained rather than repaired using test errors.

Reference-only masks and the specimen split were frozen before outcome scoring. Before any field score, an exact axis-aligned35µm support-overlap purge excluded test nodes sharing an interrogation support with any geometrically prescribed node. The radial/outer guards remain as well. These guards reduce direct support overlap but do not create statistical independence. All models use identical valid constraints and score locations. Centering uses only supplied boundary vectors, making it independent of the source's global translation estimate. Secondary NRMSE divides by held-out observed RMS after that shift, a documented departure from the optional boundary-derived normalization in the prospective protocol; primary absolute MSE and model selection are unaffected.

## Strain resolution

Original raw P1 infinitesimal tensor-gradient NRMSE is0.771420(elastic) and0.742073(harmonic), volume-weighted. Approximately15µm mesh edges are finer than the35µm image-correlation window; these are derivative descriptors, not measurement-resolution-matched or independent ground-truth strains. Predictions have not been convolved with the complete PIV measurement operator.

An explicitly POST-TEST, non-selecting diagnostic applies the same least-squares gradient operator to observed and predicted displacement on complete guarded5×5×5 neighborhoods, spanning61.5×61.5×59.4µm.303centers qualify; strain NRMSE is0.658272(elastic) versus0.604762(harmonic). A9³ stencil has0eligible centers and is reported unavailable. No model is reselected or refitted from this result. The local strain remains derived from the same measured displacement estimates and correlated with them. No independent zero-load repeat/noise ground truth or full mesh-convergence study is established.

## Numerical, security and provenance checks

Nine original analytic FE tests pass: unit volume, rigid translation/rotation, shear/dilation energy, symmetry, directional derivative and two affine Dirichlet patches. Independent standard-library readback exactly reproduces the primary metrics, boundary values and source/mask hashes; recomputed free residuals are below1e−8. Translation invariance is at roundoff. Outcome-free256-versus8192 direction quadrature differs by at most0.0135% across the full candidate grid. These checks support implementation, not physical accuracy.

All numerical work uses original dependency-free JavaScript or Python standard libraries. Public image ZIPs, TIFFs, NPY and XLSX are read as inert data; no pickle, spreadsheet formula, package installer or downloaded scientific code executes. No cloud instance or GPU is launched. Original image/data licenses were not explicit inside the example ZIPs; the bounded public package links to authors' raw assets rather than redistributing images, publisher spreadsheets or full articles. It contains original code, derived numeric tables/plots and provenance hashes.

The earlier organoid field is24×24×3, too thin for the guarded3D primary test. NIST's separately measured collagen inclusion dataset is an explicitly licensed alternative, but its download endpoints timed out in this session. Its synthetic collagen challenge was not substituted. Raw measured fiber connectivity, matched specimen rheology/local strains and independently controlled boundary loads remain the next requirements for stronger architecture validation. No aging/fracture/species parameters are inferred from this benchmark.
