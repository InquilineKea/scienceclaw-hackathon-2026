# Draft only — not sent

Subject: Request for specimen-linked 3D collagen networks and rheology data from your 2024 atlas and 2025 virtual-testing study

Dear Drs. Núñez-Ortega, Blázquez-Carmona, Sanz-Herrera and Reina-Romo,

I’m building a collagen network mechanics study and would like to test it against measured architecture and observations withheld from fitting. Your 2024 quantitative atlas and 2025 FIB-SEM virtual-testing study are particularly relevant. I have located the bovine frequency-sweep data in Zenodo10.5281/zenodo.17413651 and the geometric summaries in Table1 of the 2025 paper.

Would you be willing to share the following, with permission to use them for an independently documented comparison?

1. The original FIB-SEM stacks, segmented volumes and skeleton/spatial-graph exports for the three2025 volumes of interest, plus any additional independent volumes. For each graph, I need calibrated coordinates, segment polylines, segment-to-endpoint connectivity, junction identities, the retained/removed isolated components, and the VOI boundary mask. CSV, HDF5, VTK or Avizo exports would all be useful. Please include voxel dimensions, coordinate conventions, imaging/preparation metadata and any estimated shrinkage or segmentation uncertainty.
2. The segment-level data behind the length, endpoint-distance, tortuosity and orientation distributions in FiguresSM1/SM2. If full graph exports are unavailable, numeric histogram bins/counts, joint distributions, branch-degree distributions and an explanation of whether the reported nodes include boundary-cut or dangling endpoints would help. Are the threeVOIs disjoint regions from one specimen, or independent preparations?
3. Raw rheometer exports for the two0.8mg/mL stress-ramp tests in the 2025 paper, including imposed stress, measured strain, time, loading history, ramp/dwell settings, normal force if recorded, sample dimensions, and all replicates rather than only the plotted mean. I would also appreciate the complete small-amplitude G′/G″ sweeps and any raw rat-tail or mixed-collagen rheology from the 2024 atlas.
4. A sample/batch mapping between each imaging volume and mechanical measurement. If imaging and rheology were performed on different specimens, please identify the shared batch/preparation level. Is the 2025 experiment from the same collagen batch as the2024 atlas or Zenodo deposit? Any metadata on collagen product, extraction/pepsinization, lot, polymerization temperature/time, pH, medium and concentration would help us avoid conflating preparation with material effects.
5. Any independent measurements of deformation or fiber reorientation under load, including registered image pairs, local displacement/strain fields, and their measurement uncertainty. I would reserve these, along with complete independent specimens or batches where available, as validation targets rather than fit targets.
6. The constitutive/model implementation and boundary-condition details needed to reproduce the beam-network tests: beam interpolation and rotational constraints at junctions, handling of finite-volume boundaries, element/segment discretization, normalization by hydrated versus prepared volume, fitted parameter objective, and any calibration/validation split. The published effective axial and bending rigidities would be treated in the context of your beam operator, rather than copied directly into a different angular-spring model.

The aim is to determine which architecture and constitutive assumptions reproduce bulk and local mechanics, then study crosslink placement as a separately labeled hypothesis. I would not describe the untreated bovine data as an aging, crosslink-chemistry or fracture calibration. I can preserve your attribution, data version, license and any restrictions on redistribution; a nonpublic research-use transfer would still be useful if a public deposit is not possible.

Thank you,
[Name and affiliation]

References: doi:10.1016/j.actbio.2024.07.002; doi:10.1016/j.mtbio.2025.101962.
