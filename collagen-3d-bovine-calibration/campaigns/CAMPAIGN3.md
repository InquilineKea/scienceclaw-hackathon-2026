# Campaign 3: collagen–elastin anisotropy and species comparisons

## What the existing archives support

The orientation and dual-network archives are reusable **synthetic mechanics benchmarks**. The retained orientation campaign reports486 numerical cases; the separate collagen/elastin extension reports576 nonlinear cases,4,608 sampled strain points and324 frequency-response records. These counts are execution records in the archive, not experimental validation. The networks are2D, and their fiber laws, damage, recoil and effective crosslink chemistry are uncalibrated. An orientation index is not automatically an aligned-fiber fraction.

The archive's evidence registry contains87 source-linked observations across16 target taxa/species and80 species–tissue combinations, with640 species×tissue×component coverage cells. Its own readiness table marks **0/80 full-profile calibration-ready pairs** and **0 pairs with a ready orientation histogram**. This is a coverage result under that registry's broad collagen-I–VII-plus-elastin requirements, not a claim that all biological data are absent or that a focused type-I-only hydrogel fit requires every collagen subtype. A narrower model should have a question-specific minimum evidence contract.

A static integrity check found **76/77 embedded file hashes matching**, with only `README.md` mismatching and no declared files missing. Preserve the source archive and record the stale manifest; do not describe it as fully manifest-verified. File identity checks establish provenance, not scientific correctness. No imported archive code was executed for this audit.

The earlier “fixed fiber budget” experiment held150 selected collagen+elastin segments constant. It did **not** hold dry mass, total segment length, diameter, fiber volume or effective crosslink count constant. Its output is therefore a selected-segment substitution scenario, not a fixed-mass species or composition comparison.

## Sequence provenance

Retained public accession records and their FASTA inputs agree with the earlier input manifest:

| Species | Type-I alpha1 | Type-I alpha2 | Retained provenance status |
|---|---|---|---|
| Human, *Homo sapiens* | [P02452](https://www.uniprot.org/uniprotkb/P02452/entry) | [P08123](https://www.uniprot.org/uniprotkb/P08123/entry) | Reviewed UniProt records; sequence versions6/7 |
| North American beaver, *Castor canadensis* | [A0A250Y7T0](https://www.uniprot.org/uniprotkb/A0A250Y7T0/entry) | [A0A8B7UHI7](https://www.uniprot.org/uniprotkb/A0A8B7UHI7/entry) | Unreviewed predicted records; sequence versions1/1 |

These are retained-record provenance statements, not new experimental sequence confirmation. The backbone pilot does not determine mechanical robustness. Mature-chain boundaries, collagen chain register, hydroxylation/glycosylation, enzymatic and age-related crosslinks, hydration and fibril packing need separate evidence. Its mechanical calibration contract remains null and network transfer disabled. No species-specific modulus or rupture threshold should be populated from sequence identity.

## Candidate comparisons and current readiness

**No calibration-ready cross-species pair was established by this audit.** The following are useful acquisition targets with explicit limits:

| Candidate | Comparable observations available | Important distinctions | Current use / missing data |
|---|---|---|---|
| Human versus porcine processed acellular dermal matrix | One study measured SAXS structure and tensile/tear behavior on commercial ADM materials. | Human/porcine products were supplied hydrated; bovine products required hydration. Processing, thickness and donor ages vary. SAXS orientation index is not a full3D orientation/connectivity distribution. | Use as a processed-material benchmark after recovering protocol, orientation distributions and specimen-level data. Not an intrinsic species comparison. |
| Aged human versus young porcine ascending aorta or matched aortic sinus region | One protocol compares biaxial responses and histology in both species. | Eight human donors averaged90.1±6.8years; ten pigs were6–9months. Species and age are confounded. Testing protocol, reference state, storage and hydration must remain matched to that study. | Candidate dual-network material benchmark; cannot isolate species from age. Published curves/histology exist, but a public specimen-paired raw3D geometry/mechanics dataset was not identified here. |
| Bovine versus human reconstituted collagen preparations in the same shear-fracture study | Shared rheology/microscopy framework includes cow, rat and human sources, with nonlinear response and failure measurements. | Tissue source, telopeptide extraction, concentration and polymerization temperature vary. Verify the exact supplier/tissue entries in the supplementary table before choosing a matched pair; do not presume all preparations are dermal typeI. | Good protocol-level acquisition target, not a ready species-only comparison. Raw data are offered by the authors upon request; the study's connectivity was inferred from mechanics rather than directly resolved junction counts. |
| North American beaver versus human type-I collagen | The retained sequence/backbone pilot is available. | No compatible beaver/human same-tissue mechanics, full orientation distributions and matched crosslink/PTM data were established. European beaver muscle composition from other literature is a different species/tissue/assay. | Keep as an explicit uncalibrated hypothesis until appropriate measurements are available. |

The ADM comparison and its hydration/processing distinction come from [“Collagen Fibril Structure and Strength in Acellular Dermal Matrix Materials of Bovine, Porcine, and Human Origin”](https://pubs.acs.org/doi/10.1021/acsbiomaterials.5b00310). The paper cautions against a universal cross-species orientation–strength relation.

The matched-region arterial study is [Martin, Pham and Sun, “Significant differences in the material properties between aged human and porcine aortic tissues”](https://doi.org/10.1016/j.ejcts.2010.08.056). It is informative for those specimens and age groups; it does not isolate a pure species effect.

The collagen-gel candidate is [Burla et al., “Connectivity and plasticity determine collagen network fracture”](https://pmc.ncbi.nlm.nih.gov/articles/PMC7165426/). Its rheology includes0.5% amplitude at0.5Hz during polymerization and a0.5%/s fracture ramp; these differ from the present bovine37°C,1% oscillatory0.1–1Hz calibration. Its microscopy does not directly establish junction valency, and raw data are available on request. Peak shear strain/stress are not a notched Gc measurement.

A useful preceding **within-species** control is porcine thoracic aorta before and after elastin degradation, with biaxial mechanics, biochemical assays and microscopy. This can test the assumed coupling/recruitment mechanism before attempting species transfer. Enzymatic digestion is not ordinary aging and may change residual stress and architecture. See [“Characterization of biaxial mechanical behavior of porcine aorta under gradual elastin degradation”](https://pmc.ncbi.nlm.nih.gov/articles/PMC3638071/). Raw3D specimen-paired inputs were not recovered in this review.

## Separate controls for a new dual-network campaign

Use the same skeleton, loading protocol and random realization within a paired intervention. Do not combine the controls below into a single species label:

| Control arm | What is fixed | What is varied / recorded |
|---|---|---|
| Fiber orientation | Dry mass, total fiber volume, length/diameter distributions, junction counts and constitutive laws | Collagen or elastin orientation separately; report realized3D distributions and any rewiring consequences |
| Fixed dry mass | Total dry collagen+elastin mass with explicit protein density and hydration definitions | Composition; allow physical volume to change or specify compensating changes explicitly |
| Fixed fiber volume | Sum of fiber cross-sectional area×length and specimen volume | Collagen/elastin allocation; this is not necessarily fixed mass |
| Fixed connectivity | Degree/valency distribution, junction count and preferably loop/spatial statistics | Constitutive chemistry or composition without accidentally adding support routes |
| Fixed crosslink occupancy | Chemical links per mole of the relevant protein and explicit number/location in the model | Protein abundance or orientation; collagen crosslinks and elastin desmosine-like links remain separate |
| Fixed architecture / chemistry intervention | Geometry, mass, volume, exposure sites, loading and hydration | Only a measured chemical constitutive difference, with its uncertainty |
| Coupling ablation | Both component graphs and their material laws | Collagen–elastin tether strength/number separately from component amount; report force partition and residual stress |

Mass, volume, connectivity and chemical occupancy constraints may be mutually incompatible if imposed without compensating geometry changes. State the actual adjustment for each control; never claim all were held fixed just because the selected edge count was fixed. At minimum, report realized mass proxy, length, area, volume, degree, link counts, loop statistics, orientation and constituent force fractions for every arm.

Fit within a well-defined material/tissue protocol and hold complete specimens or batches out. Species is an external prediction target only after age, anatomical region, preparation, hydration, temperature, loading rate and collagen/elastin measurements are comparably defined. Propagate between-specimen uncertainty and keep local direction/strain samples nested within specimen. A species label, lifespan or sequence difference is not a mechanical parameter.
