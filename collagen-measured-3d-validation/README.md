# Measured 3D collagen held-out benchmark

See REPORT.md for results and limits. The tests reveal poor batch transfer and an elastic field baseline that loses to harmonic interpolation. Physical/chemical aging validation is not established.

Public explorer: https://inquilinekea.github.io/scienceclaw-hackathon-2026/measured-3d/

## Inputs and reproduction

Download authors' original ClassicSingleCellTFM images/evaluated assets from https://github.com/rgerum/saenopy/releases/tag/v0.7.4 and the paper's Extended Data Fig.2 source spreadsheet (MOESM21), https://doi.org/10.1038/s41567-024-02632-8 . Check INPUT_HASHES.json. Public access is verified; no explicit image-data redistribution license was found in the ZIPs. Images, publisher spreadsheets and full article files are not included in this bounded public package.

Original scripts use Node.js or Python standard libraries only. They do not import Saenopy, NumPy or pickle. To reproduce, copy the files in source/ into a new working directory, then place inputs in data/ beneath that directory and retain helpers together, extract PIV with extract-classic.py and cached rheology cells with read-rheology.py, run reference-only mask freezing and exact support purge, numerical checks, A/B selection and final tests. Do not retrospectively optimize masks or parameters using test errors. Historical frozen hashes and input-support amendments are retained. The saved masks are reference-only artifacts and use truncated near-cell distances; sentinel distances are not valid global radial distances.

Splits: bulk Afit/Bselection/Ctest; spatial004implementation/007selection/008test. Primary spatial score is equal-octant vector MSE. Raw P1 strains are exploratory; wider-stencil strain is an explicitly post-test diagnostic. Absolute stiffness is unidentifiable from homogeneous displacement-boundary fields. The mesh is the PIV sampling grid, not measured collagen fiber connectivity. Full physical boundary loads and specimen-matched geometry/rheology remain missing.

Numerical checks and independent readback are under audit/. The published web package contains derived visualization data and original plots, including a camera-rotation animation of one measured field, not a time-resolved experiment. Reproduction requires an execution environment reviewed under your local policy; original input parsing never runs downloaded code.
