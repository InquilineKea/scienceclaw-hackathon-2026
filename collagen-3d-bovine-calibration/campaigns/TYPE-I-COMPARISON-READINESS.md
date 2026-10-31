# Type-I collagen comparison: a calibration-ready question and its data boundary

Public evidence review, 2026-10-31. No simulation, external contact or new cloud compute was performed for this review.

**Narrow question:** At the same collagen concentration, medium, temperature and assay, how do the measured small-amplitude G′ and G″ of reconstituted, non-pepsinized bovine-dermis and rat-tail type-I gels differ? This is a comparison of two material sources, not a species-only causal effect. It is a practical calibration target before attempting the original beaver-versus-human robustness hypothesis.

**Readiness:** A bovine-only raw frequency-response fit can run now from the already retrieved [Zenodo dataset](https://zenodo.org/records/17413651). A BOV-versus-RAT fit to **digitized published curves or concentration summaries** is also possible after explicit image digitization and uncertainty checks: an actual downloadable figure archive has now been inspected. A matched raw-replicate BOV/RAT fit, independent 3D architecture validation, and organism-specific fracture/aging calibration remain unavailable in the recovered files. These are different evidence levels and must keep different labels.

## Best matched material pair: the 2024 hydrogel atlas

[Blázquez-Carmona et al., Acta Biomaterialia185 (2024)281–295](https://doi.org/10.1016/j.actbio.2024.07.002) provides a substantially cleaner source comparison than combining unrelated tissue studies.

| Contract field | BOV | RAT | Consequence |
|---|---|---|---|
| Species and source tissue | Bovine dermis | Rat tail | Species remains confounded with tissue/source and supplier. |
| Collagen | TypeI, non-pepsinized acidified solution | TypeI, non-pepsinized acidified solution | Similar extraction class; telopeptide/covalent-crosslink density is not directly measured. |
| Supplier and stock | CollagenG, Matrix Bioscience;4.0mg/mL | Merck Millipore;3.95mg/mL | Preserve product and preparation identifiers. |
| Final concentrations | 0.8,1.5,2.3mg/mL | Same | Use2.3 from figures/archive; some paper prose says2.5. |
| Assembly | pH7.4;DMEM/bicarbonate;37°C,1h | Same | Prepared on ice before assembly; compare like conditions. |
| Rheology | MCR301,25mm/1° cone;37°C;1% strain;0.1–10Hz | Same | Primary0.1–1Hz band; keep higher frequencies a challenge. |
| Hydration | Aqueous gel;silicone oil limits evaporation | Same | Do not substitute dehydrated imaging geometry for hydrated dimensions. |
| Replication | Paper reports n=3 per condition | Same | Source-specific batches are not independent donors. |

The1:1 BOV/RAT MIX series can serve as a composition/control condition; it is not another organism. Apparent E is derived from shear response with assumed Poisson ratio0.34, not an independently measured tensile modulus. FIB-SEM preparation involves fixation/dehydration; its pore/fiber metrics carry preparation uncertainty.

### What was actually downloaded

The public [Figures dataset, DOI10.12795/11441/188036](https://doi.org/10.12795/11441/188036) resolves to an institutional record. Its6,710,494-byte `Figures.zip` was downloaded and its directory inspected; SHA256 is `a6a2a6af87558d6719a1e13a020a7e0f49f2e8888bac4f4a0c52648afbcf6e5b`. It contains exactly ten TIF figures, **no CSV/XLS replicate tables or 3D coordinate/edge exports**. The public README and visual inspection confirm:

- `Figura_3.tif`: source/concentration G′, G″ and derived E summaries with error bars, plus structural summaries/images.
- `Figura_Suplementaria_2.tif`: BOV/MIX/RAT time traces and G′/G″ frequency traces at all three concentrations. These are usable plotted observations, but the recovered image alone does not establish whether each trace is an individual representative, mean or other aggregate. Resolve that provenance before assigning replicate counts or statistical weights.

This is a real route to a limited literature-summary fit, not raw-data recovery. The archive's license is CC BY-NC-ND4.0; link the original figures, and document numeric digitization and provenance rather than republishing modified source figures indiscriminately. The inventory and exact public download URL are in `atlas2024-figure-archive-inventory.json`.

The retrieved Zenodo rheology archive contains ten bovine frequency sweeps:4/3/3 files across0.8/1.5/2.3mg/mL,210 observations. All four low-concentration files must be retained and the difference from the article's n=3 disclosed. No raw RAT or MIX sweeps were present in the retrieved frequency-file inventory. A plotted BOV trace and the full bovine archive must not be assumed identical without checking their correspondence.

## What Burla2020 contributes, and what it does not

[Burla et al., PNAS117 (2020)8326–8334](https://pmc.ncbi.nlm.nih.gov/articles/PMC7165426/) supplies shear-fracture and plasticity tests. The [author's institutional chapter and supplementary tables](https://research.vu.nl/ws/files/101278934/931951.pdf) clarify source classes:

| Material class | Source | Telopeptides / preparation distinction |
|---|---|---|
| Bovine atelo, PureCol | Dermis;CellSystems;3.2mg/mL stock in0.01MHCl | Telopeptides absent;pepsin-solubilized class. |
| RatCol | Tail tendon;Corning;8.34mg/mL stock in0.02Macetic acid | Telopeptides retained;acid-solubilized class. |
| Human, VitriCol | Neonatal cells;CellSystems;3mg/mL stock in0.01MHCl | **Atelo, not telo.** Not an adult native human-tissue sample. |
| Bovine telo | Dermal typeI, intact-telopeptide class | Treat separately from PureCol; do not infer supplier/lot from the atelo row. |

For the principal standard-rheometer comparison, gels are aqueous PBS,pH7.4;typically1mg/mL, with a separate0.5mg/mL control. Polymerization is2h at the specified27/30/34/37°C. Linear monitoring uses0.5% strain/0.5Hz; differential K′ is measured under prestress plus a0.5Hz oscillation. Fracture uses a0.5%/s strain ramp. The separate confocal-rheometer setup polymerizes at22°C, so it must not silently inherit37°C metadata. Plate size, gap, coating and rate controls address slip/interface failure. SEM diameters are semi-quantitative after drying/coating.

The important inference limit is that reported connectivity z was calibrated from nonlinear rheology against a2D model; it is not an independent measured3D degree distribution. Reusing z inferred from the same mechanical curve as both architectural input and a validation target would leak information. The human condition's critical strain is0.045, not0.45; search/OCR snippets can shift table rows or mislabel atelo as telo. Prefer the actual table and its label.

Raw data are stated to be available on request. Public article/SI plots can constrain a digitized normalized curve or peak strain, but no downloadable raw specimen-linked curve/graph archive was located in this bounded search. Shear peak strain/stress are not a notched fracture toughness Gc. The10–20% fiber rupture thresholds used to bracket network behavior are model assumptions supported by other fibril studies, not a species-specific measured cohesive law.

## Executable calibration contract

1. **Start with the atlas BOV/RAT pair at1.5mg/mL and37°C.** Fit a minimal G′/G″ law separately for each source in0.1–1Hz. Do not fit fiber axial rigidity, bending rigidity, viscosity distribution and crosslink chemistry simultaneously from these bulk observations. Keep all those unidentifiable quantities marked as assumptions.
2. **Keep evidence levels separate.** Use raw bovine files for a raw-data fit. For RAT and MIX, first digitize the advertised TIF traces/summaries with independently checked axis mappings, pixel/line-width uncertainty and source-aggregation labels. Do not invent raw replicas from a plotted line or count its frequency points as biological replicates. Resolve error-bar type before uncertainty weighting.
3. **Reserve targets before fitting.** A simple concentration law can fit0.8/2.3mg/mL and predict1.5mg/mL as a within-study summary challenge. That is not independent donor/batch validation. A full matched raw-data comparison needs original RAT/MIX sweeps and explicit batch/specimen identifiers. Nonlinear/failure and local-strain targets require separate files and protocols.
4. **Test controls independently.** A source-specific fit does not identify why sources differ. Subsequent models should separately hold mass, hydrated volume, graph connectivity and crosslink treatment fixed, reporting which quantities change in each control. Do not encode all four differences under a species label.
5. **Use Burla as a protocol-specific nonlinear/plasticity challenge.** Compare the appropriate telo/atelo class, concentration and temperature; request raw curve histories before fitting a calibrated rupture/plasticity law. Keep bovine typeII excluded from a typeI-only comparison.

**Answer to “can we fit now?”** Yes for bovine raw bulk rheology, and conditionally for a clearly labeled BOV/RAT figure-digitized bulk-response comparison. No recovered dataset yet supports a raw-replicate, measured-3D, organism-specific stiffness-and-fracture fit with independent held-out observations. The original beaver-versus-human typeI robustness hypothesis remains open; neither these source comparisons nor a sequence/structure pilot establishes a beaver robustness advantage.

## Access and provenance limits

The canonical idUS record, README and ZIP inventory were accessed successfully. The web tool could not ingest the4.9MB atlas PDF in one call; selected methods were checked through its institutional full-text index. The PMC PNAS supplementary PDF link encountered an access challenge; the author's institutional supplement supplied the source table instead. No challenge was bypassed, no author was contacted, and no private Drive identifiers or full paper text are included here.
