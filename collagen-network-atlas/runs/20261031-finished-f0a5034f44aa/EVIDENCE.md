# Evidence ledger

Checked 31 October 2026. No measured calibration was loaded. All numerical material controls in this application are hypothetical. Citations motivate mechanisms and limits; they do not validate this implementation.

| Source | Supported observation / context | Use here and limit |
|---|---|---|
| Licup et al. (2015), *Stress controls the mechanics of collagen networks*, [PNAS, DOI 10.1073/pnas.1504258112](https://doi.org/10.1073/pnas.1504258112); [primary full text](https://www.pnas.org/content/pnas/112/31/9573.full.pdf) | Reconstituted type-I collagen experiments covered 0.45–3.6 mg/mL and showed nonlinear stress-dependent stiffness. Modeling includes bending, stretching and non-affine relaxation. | Mechanistic motivation; reported concentrations are literature context only. We do not map mg/mL to φ, fit an E₀, or reproduce their experiment. |
| Sharma et al. (2016), *Strain-controlled criticality governs the nonlinear mechanics of fibre networks*, [Nature Physics, DOI 10.1038/nphys3628](https://doi.org/10.1038/nphys3628) | Subisostatic networks can gain rigidity under strain; experiments and modeling probe critical behavior. | Motivates distinguishing graph connectedness, rigidity and strain-dependent mechanical modes. Our sparse finite graph motifs do not reproduce the paper’s critical exponents. |
| Fantner et al. (2005), *Sacrificial bonds and hidden length dissipate energy as mineralized fibrils separate during bone fracture*, [Nature Materials, DOI 10.1038/nmat1428](https://doi.org/10.1038/nmat1428); [author-hosted primary paper](https://hansmalab.physics.ucsb.edu/pdf/317%20-%20Fantner%2C%20G.E._Nature.Mats._2005.pdf) | Experiments support additional energy dissipation through weak, reformable interactions in a mineralized bone composite. | Motivates a hypothetical reversible-link control. The implemented threshold and spring coefficient are not measurements; a mineralized composite is not a pure collagen gel. |
| Busby et al., *Development and mechanical characterisation of self-compressed collagen gels*, [PubMed 29519435](https://pubmed.ncbi.nlm.nih.gov/29519435/) | Initial gels at 0.2–0.4% w/v were compressed and characterized with a biphasic model; fluid loss and permeability matter. | Literature range and protocol context only. Dry fiber fraction, w/v concentration and compressed w/w concentration are not interchangeable inputs. |
| *Response of Collagen Matrices Under Pressure and Hydraulic Resistance in Hydrogels* (2019), [Soft Matter, DOI 10.1039/C8SM02143K](https://doi.org/10.1039/C8SM02143K), [primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC6512315/) | Pressure-step experiments are analyzed using poroelastic theory; confinement changes hydraulic response. | Supports the need to distinguish hydraulic, pore and solid stress. No poroelastic pressure prediction is implemented. |

## Evidence classes in the explorer

**Measured inputs:** none. No specimen geometry, fiber modulus, rupture law, density, permeability or molecular crosslink mechanics were imported from measurement.

**Literature context:** concentrations and mechanisms in the table above. They are displayed as provenance, not as default parameter bounds with experimental validation.

**Hypothetical controls:** all generator scores, fiber volume fraction, fibril diameter relative to L₀, crimp, bending multiplier, axial compression law, collapse regularizer, rupture thresholds, background elasticity, sacrificial-link kinetics, lumped density and damping. Bounds are computational controls, not clinical or materials specifications.

**Model-derived observations:** every curve, energy, graph statistic, deformation and animation in this package. Statistical fits are descriptive tests on the generated sample.

## Prior molecular evidence remains separate

The earlier H100 ALCHEMI/MACE-OFF run completed eight neutral-fragment geometry relaxations (two starting seeds for four truncated molecular motifs). Pre-existing L4 MACE-OFF and MACE-MP scans covered eight simplified proxy fragments. Their report describes substantial model sensitivity, an approximate glucosepane representation, a neutral pyridinoline proxy, and boundary minima for sulfilimine with OFF and pyridinoline proxy with MP.

Those computations do not establish native collagen crosslinks, chemical reaction barriers, rupture forces, solvent free energies or tissue stiffness. Neither k nor k_rel from them appears in `model.js`. Read the separate [molecular results report](https://humanavianaisymbiosis.wordpress.com/2026/10/31/scienceclaw-collagen-brev-alchemi-results/) and [molecular reproducibility supplement](https://humanavianaisymbiosis.wordpress.com/2026/10/31/scienceclaw-alchemi-collagen-data-code-logs/) for their own evidence and limitations. No molecular or cloud workload was started for this explorer.

Related source critique: [eight-reviewer collagen report](https://humanavianaisymbiosis.wordpress.com/2026/10/31/gemini-collagen-review-findings-eight-reviewer-report/). Its concerns about imposed rupture laws and scale mappings helped motivate explicit separation here; it is not an independent validation of this new model.
