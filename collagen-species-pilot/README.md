# Beaver–human type-I collagen: molecular-to-network pilot

This pilot commissions the sequence-to-backbone step using CDSM. It does **not** determine whether beaver collagen is stronger, tougher, more damage-resistant or less affected by aging. No molecular mechanical parameters have been transferred to the network atlas.

## Matched inputs

North American beaver (*Castor canadensis*) COL1A1 [A0A250Y7T0](https://www.uniprot.org/uniprotkb/A0A250Y7T0/entry) and COL1A2 [A0A8B7UHI7](https://www.uniprot.org/uniprotkb/A0A8B7UHI7/entry) are unreviewed predicted records. Human canonical reviewed entries are [P02452](https://www.uniprot.org/uniprotkb/P02452/entry) and [P08123](https://www.uniprot.org/uniprotkb/P08123/entry). Full downloaded records, precursor FASTA, sequence hashes and extracted-region coordinates are retained in `inputs/`.

The longest uninterrupted GXY runs are beaver COL1A1 precursor residues 175–1188 and human 179–1192 (1,014 residues), and COL1A2 residues 91–1107 in both species (1,017 residues). Original Needleman–Wunsch alignment, match +2, mismatch −1, linear gap −3, diagonal tie priority, gives no gaps. COL1A1 identity is 993/1014 = 97.929%; COL1A2 is 945/1017 = 92.920%. These are identities of the extracted regions, not full precursors or measured mechanical similarity.

Three prespecified 90-residue windows start at offsets 0, 462 and 924 from each extracted region. The last COL1A2 window does not include its extra final triplet. Each trimer has two alpha-1 chains and one alpha-2 chain. Orders 112, 121 and 211 test where the alpha-2 chain sits in the builder; they are sensitivity cases, not independent biological replicates or an experimentally assigned register. Relative alpha-1/alpha-2 longitudinal alignment is a modeling assumption requiring structural confirmation.

## Structure generation and limits

Only `step1_backbone_builder.py` from [CDSM commit 074a6f3](https://github.com/lamm-mit/Collagen-Structure-Modeler/tree/074a6f3aa76c987fde3fa39746c33256429a081a) and its four required numeric tables are used, retained under `vendor/` with the Apache 2.0 license. This deterministic THeBuScr-derived stage constructs N, CA, C and O backbone atoms. It is not the full CDSM relaxation pipeline. Eighteen configurations are specified (2 species × 3 windows × 3 chain orders).

Input P residues remain P in the written backbone. However, the builder's `getprop` internally maps Y-position P to O for its propensity lookup. Consequently this stage cannot cleanly compare hydroxylation chemistry. Native hydroxyproline/hydroxylysine occupancy, glycosylation, hydration, mature enzymatic crosslinks and AGE adducts are not inferred from gene sequences. Geometry differences and builder-frame CA coordinate differences are not stiffness, stability, force, work or robustness estimates.

## Concrete route from molecular damage to network parameters

The appropriate chemistry-aware follow-on is a matched force-field study informed by [AGEs-ColBuilder](https://github.com/gggguido/AGEs-ColBuilder/tree/4e51b2bb6ab747ba4c8743b3f676a448f8b26d43) and its [2026 paper](https://doi.org/10.1093/bioinformatics/btag409). That code/data supplies AGE-related modeling components; compatibility with the CDSM/Amber setup, charge states, attachment sites, stereochemistry and complete topology must first be checked. The published large fibril workflow is not reproduced by this small pilot.

Use a factorial design: species × matched damage chemistry, with paired unmodified controls, several independently equilibrated replicas, fixed temperature/hydration/PTM assumptions, and overlapping loading rates. Start with one explicitly defined glucosepane bridge and its matched control; test non-crosslinking oxidative adducts separately. Choose sites conserved between the paired windows where possible. Do not combine sequence differences, PTM differences and arbitrary damage burdens into one “robust” preset.

| Molecular observable | Candidate coarse parameter | Additional evidence required |
|---|---|---|
| Reversible axial force–extension slope k | Axial rigidity EA = k L₀ | Units, fitted strain interval, equilibrium replicas; fibril packing and load-sharing calibration before a network edge assignment |
| Bending fluctuations or controlled bending energy | Bending rigidity κ; persistence length κ/(kBT) under an appropriate chain model | Finite-size/end effects, solvent and temperature matching, a beam/hinge coarse-graining rule |
| Relative molecular/fibril sliding free energy and time dependence | Sliding barrier, friction or viscoelastic relaxation | A sliding coordinate and rate-dependent constitutive law; current atlas springs do not have one |
| Reversible AGE connector force–extension curve | Connector spring or nonlinear potential | Actual attachment geometry and coarse length scale; density mapped from explicit sites rather than age labels |
| Bond rupture / irreversible damage | Rupture distribution and dissipated work | Reactive or otherwise validated rupture model and rate dependence; ordinary fixed-topology harmonic MD cannot supply covalent rupture thresholds |

Transfer paired ratios with uncertainty only after the relevant observable and homogenization rule are supported. Keep network topology fixed for the first species/damage contrast; later vary fibril architecture separately. Compare stiffness, failure strain, work and anisotropy without calling any species “robust” in advance. An increase in stiffness need not mean increased work capacity.

`calibration-contract.json` deliberately leaves all mechanical fields null. It records what must be supplied to activate a molecularly calibrated network run. Backbone geometry alone must never silently populate those fields. The atlas's current crosslinks remain an independent dimensionless hypothesis experiment.

## Execution and provenance

See `SECURITY_REVIEW.md`, `INPUT_MANIFEST.json`, the original `run-backbones.py`, and the bounded remote bootstrap `cloud-backbones.py`. The runner is executed only remotely under the user's policy; importing the vendor module locally requires separate approval. A successful output must contain 18 PDBs, 270 residues / 1,080 backbone atoms per structure, `backbones.json`, and a verified result manifest. Runtime receipt, source bundle and output archive are preserved after collection. A completed backbone build is a pipeline result, not an MD or biological result.
