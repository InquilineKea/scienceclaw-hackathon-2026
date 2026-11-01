# Standalone collagen mechanics dashboard data handoff

Prepared2026-11-01 for the requested Argon visualization/publication work. All operations here read/parse saved data; no study code, workbook formula, simulation, optimization or new fit was executed. Originals remain untouched.

## Release inputs

Use `gallery-ready/*.json` for the shared dashboard engine:17studies,30models,33.16MBtotal, lazy-loading recommended. Each file has title/sourceURLs/evidence/units/limitations, exact saved scalar tables, curated defaultView and scientific gate semantics. `models` contains only preserved spatial data or explicitly marked1Ddisplay schematics. `normalization-receipt.json` checks all table rows/columns against the recovered originals and verifies node/edge/frame consistency.

`public-studies/` retains original extraction schema; `studies/` additionally retains exact local source paths for private audit. `source-provenance-private.json`, inventory.json and download hashes retain provenance. The public copies omit host absolute paths. Several source artifacts were recovered from preserved local scientific outputs whose results were already described publicly; do not claim every raw file previously had a public download URL. The user's current request authorizes publication of the related dashboards; root handles final publication and security checks.

## Coverage

| Post | Data | Spatial display / key restriction |
|---|---|---|
|677|16ownership/grip/placement controls with saved1Dstates|16illustrative layouts,93axial nodes each. Three backbones remain present; ownership2/3 means number of backbone owners represented by a junction, not two/three total backbones. Arbitrary yoffset and z0 are display layout. Condensed mechanical pair edges are not chemical bond geometry.|
|670|192degree-controlled graph records; scalar dotted keys|Four exact savedW3graph examples; candidate geometry()source identical to preserved FCCgeometry, graph SHA matches record. Other scalar records must retain independent-example label.|
|659|192four-arm matched-budget records|Four exact savedFCCgraph examples; random/triangles/hubs/even retain isolated nodes.|
|656|54graph,64mechanical,64rank-control summaries|One exact saved dilutedW3specimen. Spanning, clamped response and whole-sample rigidity are separate. `qualified` is a count, never a Boolean.|
|593|620final finite-attachment rows|Scalar data only; no fabricated finite-attachment deformation. Main/legacy_rigid/tighter_solver/stiff_limit remain distinct.|
|574|4352final beam/cavity rows|One genuine3Dequilibrium example. Original displacement layout is interleaved6DOF: translationu[6i:6i+3], rotationu[6i+3:6i+6]. Models use reference+translation; never rotations.|
|538|104search designs,208search evaluations,14reevaluation means,larger-grid controls|2Donly. Reverification flags join saved src IDs;14reevaluations include baselines with src=-1 and are not14unique original search dots.|
|494|7accepted36particle cases plus4primary recorded cycle histories|4actual3Dtrajectories with native initial bonds and step-stamped break events, final bondcounts checked. Internal grip-force sign preserved. External loop work is not pure dissipation.|
|457|324case workbook rows,8load-path controls,all324signed spectra|Free vs constrained eigenmodes and saved cutoffs remain separate.310valid/14rejected; tiny negative roundoff is not automatically buckling.|
|205|102maincases,18refinedcases,full saved curves/contrasts|Generic reduced-unit two-network LAMMPS study; separate collagen-only/both grips and permanent/reversible laws.|
|192|192controlled mechanical records,34560saved signaling summaries,geometry balance,earlier unmatchedpilot|Earlier2Dcampaign. Gene/YAP SD is spatial site variation, not replicate CI. Three-dimensional later campaign is separate.|
|179|500individual cases and100condition summaries|Extracted public PDF at printed precision.500unique cases/100groups×5seeds checked; maxpeakmean rounding mismatch6e-7.19all-constrained/1baseline spanning-loss counts reproduce report. Blankfailurethresholds are right-censored, not zero. Full trajectoryZIP was not publicly uploaded.|
|165|Two published historical modulus ratios and two acceptance denominators|Prose-extracted exact numbers, not reconstructed full curves. Existing controlled-networks page already supplies1600FEniCSx comparisons; link it.|
|128|91topologyrecords,513tension/90shear/136cycle/168relaxation rows,contrasts|Saved2DCPUload-sharing model; original public supplement code blocks parsed only as CSV, no program execution.|
|222|36conditions at90days and360days,all saved trajectories|Assumed-input clipping-bound negative control; no empirical aging clock.|
|258|Pinned public graph-audit/control CSVs|Converged/eligible gates; retained step/rate controls and graph groups.|
|235|Pinned public CPUtopology CSVs|`accepted`counts rewiring proposals, not scientific validity. Use converged; matched retention comparisons also require eligibility.|

## Existing controlled-networks page

Fresh public HTTPS verifies currentmain82f61b282180853357483cf81b938d756f63fe60 and exact raw path `docs/controlled-networks-20261101/index.html` (200,4216bytes). Public URL:
https://inquilinekea.github.io/scienceclaw-hackathon-2026/controlled-networks-20261101/

It covers matched-stiffness/equal-material triangular2d,FCC3D,geometrically-disorderedFCC work/censoring across10seeds, seed101GIFs, and all1600FEniCSx comparisons. It partially satisfies post165acceptance separation, not the specific659/670/656topological interventions. No new mainadvance was established; this folder was already preserved in the published tree. Initial inference that it was a concurrent new change was corrected.

## Extraction and integrity limits

- Public WordPress supplements127/204 store data code blocks with literal newline escapes; only those CSV blocks were normalized and parsed. Source programs were not executed or published by this subtask.
- Rigidity XLSX has formulas in Overview/Load paths. Only formula-free Results and literal JSON chunks from Raw Files were extracted. No macro/formula execution. Source sheet was not exported.
- The500case PDF contains printed rounded values, so its case rows are not full precision trajectory records. Do not imply otherwise.
- Shared FCCgeometry reuse was verified with exact geometry()source function SHA and exact canonical saved graphSHA. No generator/solver was run.
- The gallerymodels preserve actual recorded frames.677is deliberately a planar1Dschematic, not a3Dmolecular reproduction. No molecularly calibrated adhesion/YAP claim follows from any display improvement.
