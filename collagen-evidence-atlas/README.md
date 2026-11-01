# Collagen Evidence Atlas

A redesigned interactive workbench and cross-study research map, co-designed/reviewed with Gemini4Argon on the existing GCP lab VM and implemented in original buildless HTML/CSS/JavaScript.

Public route: https://inquilinekea.github.io/scienceclaw-hackathon-2026/evidence-atlas/

The explorer contains synchronized3D views, slice/octant filtering, signed pairwise error maps, node inspection, selectable global score charts, conditional histograms, CSV export, numerical controls and links to ten prior studies. A new presentation does not upgrade the scientific evidence. See web/METHODS.md and the prior source snapshot11b57e1daf9724ac6d169c3fa1289f5e09ce18ab.

Serve web/ with an ordinary local HTTP server; no dependencies or build are required. Original prepare-data.mjs derives the visualization from the sibling collagen-nonlinear-heldout results and its frozen setup. validate-data.py checks score IDs, quantization and global metrics. No simulations are rerun and visitors make no LLM API calls. Source data/publication under the prior benchmark retain their own limitations and provenance.

Argon made two bounded calls. Design and static review, prompt hashes, model IDs, usage receipts and our resolution of its findings are retained. Final non-thought model responses only; no keys, hidden thinking or signatures. API cost is estimated from published token pricing, not an invoice; existing VM costs are separate. Raw reviewer prose may contain unverified claims which are explicitly not promoted to scientific evidence. No generated executable code was imported or run.


## Integrated crosslinks and microrheology

[Crosslink comparisons](https://inquilinekea.github.io/scienceclaw-hackathon-2026/evidence-atlas/#crosslinks) and [microrheology](https://inquilinekea.github.io/scienceclaw-hackathon-2026/evidence-atlas/#micro) now run directly in this atlas, with matched axes, paired seeds, qualification flags and saved field replays. See web/INTEGRATION-METHODS.md and integration/ for exact source provenance and validation. No new solver or Argon call was used for this extension.


## Selection-responsive animations

Force/damage now solves the selected network/count/angle/seed at960 steps in a bounded browser worker. Uniform-drag microrheology solves selected architecture,size,seed,frequency,density and drive angle; exact saved fluid coverage remains labeled and unsupported pressure selections stay unavailable. See web/ANIMATION-METHODS.md and responsive-animation/ for provenance and commissioning. No external dependencies, cloud run or paid API.
