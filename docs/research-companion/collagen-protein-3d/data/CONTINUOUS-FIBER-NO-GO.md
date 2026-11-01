# Continuous-fiber decorin–fibronectin pilot: no-go for production

**The bending/buckling equations passed their numerical checks, but the network refinement gate failed. The planned 160-case protein comparison did not run.** The task was stopped November 1, 2026 at 3:22 am Eastern (08:22 UTC), well before the12:30 pm Eastern compute cutoff. The existing shared VM remains intact; the exact task container was removed only after complete local file verification.

This outcome improves the diagnosis of the model, but supplies no validated new decorin-versus-fibronectin ranking. Numerical correctness of a single beam does not establish resolution independence of a disordered fiber network.

## What was attempted

The follow-up replaced the previous dense central-force scaffold with200 junctions and400 spans, mean junction degree4, rotation-invariant bending, geometrical buckling under compression, and material-direction continuity at junctions. The coarse mesh has1,000 collagen nodes (three segments/span); the fine mesh has2,200 (six segments/span). A correction to the fine-node count in the frozen protocol is recorded separately in PROTOCOL-ERRATA.md.

Five conditions were defined: collagen-only; a decorin surface/GAG-spacing proxy; that proxy plus a separately identified noncovalent bridge hypothesis; compliant fibronectin-like chains; and the same chains with25% of their collagen contacts locked and breakable. All protein conditions share64 collagen sites and bridge/chain conditions share32 site pairs. Two alignment and two prescribed density-clustering states were crossed with those conditions. These are reduced-unit assumptions, not measured native occupancy, binding energies, hydration forces, enzyme kinetics or actual fibrillogenesis.

The planned production design was eight graph seeds×four organizations×five conditions=160 cases. Commissioning used only seed 11:20 coarse pilots and20 planned fine repeats. Load steps and protein conditions are not independent biological replicates.

## Final coverage and acceptance

| Stage | Planned | Started | Completed | Accepted per case | Other outcomes |
|---|---:|---:|---:|---:|---|
| Revised coarse pilot |20|20|20|20|All completed; this alone did not permit production.|
| Fine repeat |20|8|4|2|Two900-second timeouts; four interrupted after a decisive failed gate; twelve not started.|
| Production |160|0|0|0|Not launched.|

The two accepted fine runs satisfied per-case numerical/energy checks. They both failed the paired coarse/fine acceptance criteria. “Accepted per case” must not be confused with “refinement passed.” The first solver attempt is separately preserved under attempts/solver-v1 in the raw archive:15 cases started,11 completed (three accepted,eight residual failures), with four interrupted and five not started when that attempt was stopped. Solver-v2 increased polishing and logged adaptive continuation without changing physics or gates.

## What passed

Analytic energy gradients and Hessian-vector products passed finite differences for all five conditions, together with rigid-motion invariance and force balance. Additional tests exercised active coating sterics (Hessian-vector error about2.0×10⁻¹²) and axial beam reaction (relative error about2.3×10⁻¹²).

Single-beam cantilever deflection errors decreased from10.24% at16 segments to4.88% at32 segments under the declared discrete clamping convention. A pinned straight beam's smallest transverse Hessian eigenvalue was positive at0.7 times the continuum Euler critical load and negative at1.3 times that load, at both tested resolutions. A perturbed compressed beam found a buckled state with roughly56% of the straight state's energy. These checks support the implemented bending and buckling mechanisms, not biological material calibration or a fully converged network assay.

## Why the refinement gate failed

Prespecified limits were5% relative difference for stress at20%strain and fitted0–2%modulus, and0.01 absolute difference for recovery fraction. The two completed fine cases gave:

| Completed pair | Stress20 difference | Original fitted modulus difference | Recovery-fraction difference | Original paired gate |
|---|---:|---:|---:|---|
| Clustered, isotropic decorin surface proxy |1.40%|9.71%|0.000338|Fail|
| Uniform, isotropic decorin bridge hypothesis |5.23%|10.46%|0.001357|Fail|

The coarse/fine modulus fits also used different low-strain sample sets: the fine loading path adds a point at1.25%strain. A separate diagnostic recomputed both fits using only the common1% and2%milestones. Differences remained **7.41% and9.33%**, respectively. This diagnostic does not redefine the original gate or rescue the campaign; it shows the observed discrepancy is not solely the sample-weighting issue. Mesh, load-step and recovery-timestep changes were combined in this pilot, so their contributions have not been isolated.

The fine uniform/isotropic control and surface-coating cases each reached the900-second per-case budget. That is a runtime/solver failure, not physical material failure. Remaining cases were stopped once the complete gate could no longer pass, retaining every available checkpoint. No gate was relaxed and no failed or interrupted case was imputed as successful.

## What this changes about the earlier study

The earlier1,088-attempt central-force study (1,082 accepted,sixrejected) showed organization-dependent responses to assumed adapter architectures and constitutive laws. It did not establish a biological protein ranking. This more detailed pilot adds evidence that its proposed replacement is not yet ready to produce that ranking either: a more physical ingredient can pass unit-level checks while the network-level comparison remains sensitive to numerical resolution.

The next numerical fix should separate fiber-mesh refinement, load-step refinement and recovery timestep; evaluate the initial modulus on identical strain samples; and examine whether the same equilibrium branch is being followed near buckling. Increase the baseline fiber resolution only after benchmarked runtime and convergence support it. These are diagnoses for a future validated model, not an authorization to bypass this no-go or run a fresh campaign.

The biological work remains distinct: constrain decorin surface binding/GAG spacing versus an explicit bridge hypothesis; represent fibronectin compliance and occupancy; and calibrate assembly endpoints, geometry and mechanics against a defined collagen-I gel system. The current short-range coating proxy acts only when its modeled spacing contacts are active. An absence of an effect cannot validate a native decorin null result. No binding exchange, dissociation kinetics, actual GAG charge/hydration, cells, integrins, secretion or enzyme reaction was modeled. Junction-site sterics do not prevent all fiber interpenetration. Collagen rupture was not part of this elastic-window pilot, and recovery time remains uncalibrated.

## Data verification, figures and publication

The raw archive contains312 files and20,258,259 uncompressed bytes, including both solver attempts, partial repeats, failure traces, frozen source, protocols and mechanics tests. Compressed archive size 17,595,492 bytes; SHA256 `4b363c09c65091a59fe362ca9723f72d75395f58154918be0bd0e79e813a393f`. The archive and every file were verified after download. Current frozen source hashes match. The independent audit found no recorded loading/preload force, finite-value, graph/site-hash or recovery-energy violations in accepted completed cases. Effective recovery force residuals were checked internally but were not stored in the raw recovery CSV, so an independent raw audit of those missing fields is unavailable.

Google's current **gemini-nano-banana-2.1** generated the selected mechanism illustration. It is labeled as a reduced-model schematic, not microscopy, a simulation snapshot, measured protein geometry or evidence of biological validation. Prompt, model metadata and sanitized response provenance are retained. Image1 is an unselected intermediate preview; image2 is the selected final illustration. Numeric tables in this report are calculated from the saved data, not generated by the image model.

Files: AUDIT.json contains complete stage/case accounting and paired diagnostics; CASE-SUMMARIES.csv contains completed-case outcomes; results.tar.gz contains all raw records and interrupted checkpoints; DOWNLOAD-VERIFICATION.json records retrieval coverage; mechanics-tests.json and additional-mechanics-tests.json record unit-level checks; CLEANUP-RECEIPT.json records exact task-container removal. Protocol, errata, source and Google visualization provenance are included. WordPress publication records will be saved beside this report. Originals are retained. A new microSD payload requires its separate approved copy scope.


## Published record

The no-go report is published at https://humanavianaisymbiosis.wordpress.com/2026/11/01/collagen-decorin-fibronectin-continuous-fiber-pilot/ . WordPress readback matches the prepared text, blocks and attributes, with one normalized space before an image-tag slash. No content warnings were returned. The public page was also fetched over verified HTTPS and contains the selected illustration. Newsletter email and social sharing were disabled and verified. Exact payload, readback, publication/media receipts and Google illustration provenance are saved beside this report. Archive-copy status is recorded separately in ARCHIVE-RECEIPT.json when that copy is performed.
