# Campaign 2 molecular chemistry and provenance audit

Read-only evidence audit, 2026-10-31. No MD/QM calculation, imported executable, package installation, cloud access, publication, registry mutation or experiment alteration occurred. Small original Python standard-library scripts inspected JSON bond graphs and serialized XML as data. This report contains no raw peptide sequence or account identifiers.

**Decision: the chemical graph is a plausible, explicitly defined neutral-phenol dityrosine model, but no chemically validated molecule-to-network bridge is established.** In particular, it is an intramolecular telopeptide loop, not a measured intermolecular fibril junction. Wet curvature is unidentified; dry ML and classical scenarios remain conditional. Independent electronic-structure reference data and a justified load-sharing/coordinate map are missing.

## Snapshot and superseded status

The local SQLite registry was opened read-only. `dityrosine-separated-transfer-20261031` is done/unvalidated; `dityrosine-solvent-coupled-3d-20261031` is done/unvalidated, updated 2026-10-31T20:56:58+00:00. Its final owning `REPORT.md` supersedes the running snapshot in `campaign1-statistics/CAMPAIGN2-AUDIT.md`: 78/78 wet deformation states and 6/6 references completed, but 0/3 paired wet laws passed transfer. All six individual wet mixed profiles fail energy/force-Hessian consistency (normalized discrepancy 4.89–77.90; limit .25) and fit-window stability. The unresolved global wet tangent finite-difference failure remains material. This audit did not query live remote state and cannot establish later changes.

The final report retains 4/6 admissible AIMNet vacuum pairs and 1/3 classical-dry pairs. Accepted individual minimized states are not accepted constitutive laws. No final wet network/YAP law should be inferred from completed trajectories or state counts.

## Identity, graph, caps and chemical state

Owning input graphs are `oxidative-tensegrity/experiments/dityrosine-transfer-20261031/inputs/DITY_{CONTROL,LINKED}.json`. Direct graph inspection confirms:

| Property | Control | Linked |
|---|---:|---:|
| Solute atoms | 298 | 296 |
| Listed graph bonds | 302 | 301 |
| Tyr4 CE2–Tyr6 CE2 edge | absent | present |
| HE2 hydrogens across the two sites | 2 | 0 |
| Phenolic HH hydrogens across the two sites | 2 | 2 |
| Degree at either CE2, including H/link | 3 | 3 |
| Serialized dry NonbondedForce charge sum | approximately −1 e | approximately −1 e |

Atom identities differ only by the two removed HE2 atoms; the net bond-count change is consistent with deleting two C–H bonds and adding one C–C bond. CE2 is adjacent to the phenolic CZ: this is a carbon–carbon ortho phenol coupling representation, consistent with the intended dityrosine patch. Both phenolic hydrogens remain. This graph is not a phenoxyl radical, phenolate pair, ether crosslink or reaction intermediate. Fixed topology does not simulate oxidative formation/cleavage.

Both graphs use paired CHARMM ACE/CT3 terminal patches, merged into terminal residues; explicit cap atoms are present. XML dry charge sums agree between chemistries to numerical precision. These are fixed source-model protonation choices, not pKa calculations or evidence that a particular experimental pH selects them. Phenolic OH/HH partial charges change from −.54/+.43 to −.534/+.42; CE2 changes from −.115 to +.016. Thus the intervention changes charge distribution and force parameters as well as connectivity, despite unchanged net solute charge.

The source is a human collagen N-telopeptide excerpt, with a hypothesized Tyr4–Tyr6 intramolecular bond. The owning preparation protocol explicitly says this is not a measured site assignment. Neither caps nor local stereocenter checks establish representativeness of a full collagen helix/fibril, bovine tissue, or collagen VII. The unrelaxed prepared linked graph has an 8.63 Å CE2 separation; it must never be treated as a chemically realized equilibrium structure. The subsequent campaigns correctly specify relaxed trajectory-derived poses. No external stereochemical validation of every loaded state was repeated here.

## Atom typing and parameter provenance

Preparation source root, abbreviated `P` below:

`collagen-glucosepane-dityrosine-20261031/` (local preparation archive; not part of this bounded network export)

`P/parameters/DITY_TRANSLATION_AUDIT.json` records the DITY patch, source/derived XML hashes, 19 bonded parameter-type translations, and CE2 type CG2R67. Ring atoms largely retain CA; phenolic O/H use OH1/H. The patch changes side-chain charges, adds CE2–CE2 and deletes HE2. It explicitly describes charges as estimated by CGenFF and adds −.003 to each OH charge to enforce neutral side chains. A representative crossbond target is 1.49 Å with CHARMM K=300 kcal mol−1 Å−2, translated to OpenMM k=251040 kJ mol−1 nm−2. This conversion includes the factor two required because OpenMM harmonic energy has a 1/2 prefactor. [OpenMM force definitions](https://docs.openmm.org/latest/userguide/theory/02_standard_forces.html).

`P/PROTOCOL.md` and `oxidative-tensegrity/swarm/CODEX_CANDIDATE_COMPARISON_20261031.md` report local coverage of 41 bonds, 66 angles, 98 proper torsions and 40 nonbonded entries; native full-context impropers and 22 CMAP terms per peptide; successful construction and Reference/CUDA numerical comparisons. These are useful implementation records, not independent physical benchmarks. This audit inspected the patch translation and serialized charge records; it did not independently reproduce every parameter assignment, exception, CMAP interpolation or force.

The source is Graham et al., [Molecular dynamics of reversible iron–catechol complexes](https://doi.org/10.1016/j.xcrp.2026.103319), with the paper-linked [parameter archive, Zenodo 16865891](https://doi.org/10.5281/zenodo.16865891). The local owning report records checksum verification; fresh browser retrieval of these two endpoints failed during this audit, so their current remote bytes were not independently reverified. Their provenance must not be described as a collagen-specific validation. Elevated DITY torsion penalties 30 and 41.1 remain unresolved accuracy flags in the owning protocol. CGenFF documents that analogous atom-type substitution yields approximate parameters with penalties, and requires correct hydrogens, protonation and bond orders for typing. [Official CGenFF documentation](https://docs.silcsbio.com/2025/cgenff/usage.html).

For wet mechanical scans the serialized solvent system omitted some constrained solute H-bond energy terms. The protocol requires restoring exact dry-system terms before releasing those constraints. This is essential Hamiltonian completeness, not an optional optimizer adjustment. Retaining rigid-water constraints requires tangent-projected residual forces; raw constraint reactions are not minimization errors. The final report still records failure of the global energy/force check. No parameter completeness claim resolves that failure.

## Solvent, salt and sampling boundary

`oxidative-tensegrity/experiments/dityrosine-solvent-coupled-3d-20261031/inputs/DITY_{CONTROL,LINKED}/solvation.json` records CHARMM modified TIP3P/native ions, requested .15 M salt, 11 Na and 10 Cl per box, and approximately neutral total box charge. Control has 3759 waters/11596 total atoms; linked has 3689 waters/11384 atoms. Initial box dimensions differ. The earlier owning comparison reports actual salt-pair concentrations .137917 M and .140929 M, respectively, with the additional neutralizing ion separate. Requested salt is therefore not identical achieved concentration or identical solvent microstate.

The final deformation protocol retains endpoint-specific periodic boxes/PME and 1 nm nonbonded cutoffs; switching is disabled. OpenMM documents that a switching function provides a smooth cutoff with continuous first and second derivatives. This makes cutoff sensitivity a plausible diagnostic, not a proven explanation of the observed failure. Changing switching/grid/cutoff defines a changed Hamiltonian and needs explicit provenance. [OpenMM nonbonded theory](https://docs.openmm.org/latest/userguide/theory/02_standard_forces.html).

Three prior 50-ps replicas supply poses; four frames per replica in the separated study are correlated. The later six 10-ps fixed-grip wet thermal diagnostics total 60 ps, not an aqueous PMF, converged solvent ensemble or wet elastic modulus. Local minimized potential curvature can be branch-dependent and excludes thermal/entropic contributions.

## Does the comparison isolate chemistry?

It preserves peptide identity and terminal treatment, and keeps total solute charge fixed. It does **not** isolate a single added mechanical spring: it changes ring charge distribution, bonded/exclusion topology, local nonbonded interactions, and subsequent conformation. Linked and unlinked trajectory endpoints have different reference geometries, prestresses, water populations and boxes. Consequently, an observed Hessian-ratio difference can contain chemical-state, conformation and solvation effects. Neither independent endpoint relaxation nor matching only a CA distance removes this confounding.

Use two explicitly different estimands in a future design: (1) matched-backbone/common-coordinate conditional chemistry response, permitting chemically necessary local H placement/relaxation; (2) chemistry-specific ensemble-averaged response, including conformational redistribution. For (1), report crosslink strain and any incompatible matched pose rather than forcing both into an unrealistic geometry. For (2), establish sampling and weights. Do not compare absolute linked/control electronic energies as a reaction energy without accounting for the two removed hydrogens and their reference reservoir; deformation-energy differences within each fixed composition avoid that particular ambiguity.

## Admissible observable and next test

Existing evidence supports structural persistence within short fixed-topology simulations, bounded numerical geometry checks, and selected dry local potential-response scenarios. It does not establish universal dityrosine stiffening, a hydrated force law, rupture strength, formation probability, fibril relaxation, bovine calibration or measured gene regulation.

The next admissible chemistry test is a separately reviewed, prespecified independent electronic-structure benchmark of a tractable capped analogue preserving the CE2–CE2/phenolic chemistry, plus matched unlinked analogue. Freeze identity, protonation, caps, stereochemistry, grip coordinate definitions and conformer selection before results. Reference observables should include inter-ring torsion curves and the same small-deformation generalized loads and symmetric 2×2 stretch/rotation Hessian, including mixed term and prestress. Compare force/energy consistency, reference convergence, curve shape and Hessian components in common units; retain incompatible conformers and failures. Several geometries are needed because the high-penalty torsional terms can couple strongly to the measured rotation. Method/basis/dispersion/solvent choices and acceptance tolerances belong to the quantum auditor's prospective contract, not an unrun claim here.

Resolve or explicitly bound the wet global force/energy numerical failure before any wet coefficient transfer. Then obtain an environment-matched ensemble observable if hydration is the target. Finally, require an energy-consistent molecular-to-element map including the number/orientation of load-bearing molecules, series/parallel sharing and strain/rotation Jacobian. A chemically valid intramolecular loop does not itself justify assigning an intermolecular network-junction stiffness. If these gates fail, the scientifically useful result remains a documented no-go for quantitative transfer. No new compute is required to reach that present conclusion.

## Exact owning sources inspected

- `oxidative-tensegrity/experiments/registry.db` (read-only state snapshot).
- `oxidative-tensegrity/experiments/dityrosine-transfer-20261031/{PROTOCOL.md,INPUT-PROVENANCE.json,inputs/DITY_CONTROL.json,inputs/DITY_LINKED.json}`.
- `oxidative-tensegrity/experiments/dityrosine-solvent-coupled-3d-20261031/{PROTOCOL.md,REPORT.md}` and each chemistry's `inputs/*/{solvation.json,dry_system.xml}`.
- `P/PROTOCOL.md`, `P/parameters/DITY_TRANSLATION_AUDIT.json`.
- `oxidative-tensegrity/swarm/CODEX_CANDIDATE_COMPARISON_20261031.md`.
- `collagen-3d-bovine-calibration/campaign1-statistics/CAMPAIGN2-AUDIT.md` (earlier, superseded progress snapshot; useful inference cautions).

No historical memory rollout was needed; conclusions use current owning files and the linked primary documentation.
