# Campaign 1: from bovine rheology to measured 3D architecture

The available [bovine hydrogel rheology dataset](https://zenodo.org/records/17413651) supports calibration of bulk storage and loss moduli within its documented concentration, temperature, strain and frequency range. A synthetic 3D network calibrated to that response is a useful comparator. Such calibration does not establish that the network reproduces measured collagen architecture, nonlinear deformation, aging or fracture.

The closest structural reference is [Núñez-Ortega et al., *Materials Today Bio* (2025)](https://doi.org/10.1016/j.mtbio.2025.101962). Its Table 1 reports three reconstructed bovine hydrogel volumes:

| Architecture measurement | Published value |
|---|---:|
| Volume per VOI | 111.8 µm³ |
| Segments, VOIs 1 / 2 / 3 | 2,108 / 2,070 / 2,128 |
| Nodes, VOIs 1 / 2 / 3 | 1,710 / 1,751 / 1,766 |
| Segment arclength, overall mean (SD) | 346.55 (338.75) nm |
| Endpoint distance, overall mean (SD) | 302.70 (283.37) nm |
| Tortuosity, overall mean (SD) | 1.13 (0.31) |
| Azimuth, overall mean (SD) | 169.72 (101.88)° |
| Elevation from Z, overall mean (SD) | 54.95 (22.62)° |

The paper fits a beam-network model to shear measurements and states that data are available on request. Its published moments are usable constraints, but raw coordinates, segment polylines, adjacency, degree distributions, numeric histogram bins and joint/spatial correlations have not been recovered for this campaign. These omissions prevent a claim that a generated ensemble preserves the measured architecture. Finite-volume endpoints also prevent interpreting the segment/node ratio directly as an interior-junction degree distribution. The beam model's bending rigidity requires a constitutive mapping before use in a junction-angle spring model.

For a genuine predictive test, reserve complete independent specimens or batches **before fitting**. Their mechanical observations must be linked to the corresponding imaged architecture and preparation. Fit parameters using the training specimens, freeze them, and then compare predicted G′, G″, nonlinear stiffening and local strain with the reserved observations. Frequency points, fibers and overlapping volumes from one specimen do not supply independent biological replication. The [2024 quantitative atlas](https://doi.org/10.1016/j.actbio.2024.07.002), the existing frequency dataset and the 2025 structural study should not be assumed to contain identical specimens or batches without a documented mapping.

A separate route to measured spatial deformation is the public [NIST DVC Challenge 2.0](https://data.nist.gov/od/id/mds2-4129), DOI **10.18434/mds2-4129**. Its metadata list an experimental collagen confocal dataset, `optical_data/Notbohm_Fibrous_S1.zip`, and a distinct synthetic shear benchmark, `synthetic_data/Notbohm_Fibrous_S2.zip`. The experimental data concern a contracting inclusion; they are an external structure–deformation challenge, not matched bovine rheology. Image contents, specimen provenance, boundary conditions and displacement uncertainty must be checked before a mechanics comparison. Synthetic DVC ground truth must remain separate from experimentally estimated displacement fields.

[PDB 1CAG](https://www.rcsb.org/structure/1CAG) provides molecular coordinates for a short collagen-like triple-helical peptide. It can inform molecular geometry questions. It does not supply a measured hydrogel network, fiber orientation/connectivity distributions, collagen–elastin architecture or organism-specific material calibration.

**Can run now / data needed:** A transparent synthetic comparator can be calibrated to the available bulk measurements, and approximate ensembles can be constrained by the tabulated moments while testing assumed distribution families and connectivity choices. Label these as summary-constrained synthetic networks. The measured-architecture campaign needs raw image/graph exports, full geometric distributions, specimen-to-rheology mapping and untouched mechanical/local-deformation observations. Until those are available, measured-architecture validation remains a data gate, not a completed result.
