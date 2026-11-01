# Collagen explorer suite — source and reproducibility companion

This is an additive source submission for the collagen work developed during 30 October–1 November 2026. It collects code that was otherwise spread across local study folders and separately hosted public Sites. The main repository already contains the [33-study observatory](../../docs/collagen-studies/) and extensive earlier research source; those files are not replaced here.

## What is included

| Folder | Contents | Actual validation boundary |
|---|---|---|
| `sites/architecture/` | Public static Architecture Studio, comparison page and strain/fiber/junction inspector, including its scientific worker/model | Saved synthetic mechanical geometry and equilibrium checks; not a molecular force field |
| `sites/mechanics/` | Original model plus matched-stiffness, sliding, CPU diagnostic and network-law interfaces | Original model is preserved; molecular-to-network transfer remains gated |
| `sites/snt/` | Original download landing page, molecular inspection bench and five-study saved-data gallery | Actual saved structures/frames and mappings; no enzyme/affinity or equilibrium inference |
| `sites/openmm/` | Evidence tiers, numerical-control viewer and archived dimer test source/results | CUDA/Reference infrastructure check; not collagen chemistry validation |
| `outputs/network-law-sensitivity/` | Original dependency-free C++ solver, standard-library Python analysis and compact CSV/results | 5,520 accepted main histories plus timestep, domain and boundary controls; normalized assumed constitutive laws |
| `outputs/martini-cpu-diagnosis/` | Historical bounded CPU replay/negative-control preparation source, candidate supervisor, reliability patch and diagnosis | 800 ps CPU replay passed after a failed ~586.6 ps CUDA attempt; cause not uniquely established, no 45 ns benchmark/calibration claim |
| `outputs/wordpress-argon-round3/` | Fifteen data-recovery/normalization/curation adapters and integration source | Exact saved tables and coordinate extraction, no imported scientific code executed during data extraction |
| `work/` and earlier visualization folders | Original HTML builder, H100 data assembler, hydrated-control preparation, analysis and earlier view integration | Historical scripts with documented input dependencies, not an automatic campaign runner |
| `validation/argon-round3/` | Scientific scope, security review, public browser checks, asset comparisons and preservation receipts | Source, browser and public-readback validation only |

The original Sites remain online: [Architecture](https://collagen-architecture-studio.stochasticcockatoo.chatgpt.site/), [Mechanics](https://scienceclaw-collagen-viscoelasticity.stochasticcockatoo.chatgpt.site/), [Molecular downloads](https://snt5382-research-downloads.stochasticcockatoo.chatgpt.site/), [OpenMM log](https://openmm-cuda-experiment-log.stochasticcockatoo.chatgpt.site/). The canonical [Collagen Observatory](https://inquilinekea.github.io/scienceclaw-hackathon-2026/collagen-studies/) remains under the existing GitHub Pages `docs/` tree.

## Reading or serving the interfaces

Each `sites/<name>/` tree contains its own local JavaScript/CSS/JSON and vendored rendering dependencies. Serve the folder over HTTP rather than opening module-based HTML directly from `file://`. Original ZIP bundle downloads were deliberately not duplicated in this code submission; relative ZIP links in a locally served copy require the original public files listed in `DOWNLOADS.md`. Scientific data already embedded in a public HTML or required by an interface are retained.

The network sensitivity analysis uses paths relative to its own source location and the included CSVs. Its original source requires a C++17 compiler and Python standard library. Read `outputs/network-law-sensitivity/METHODS.md` and the boundary amendment before interpreting results. No sensitivity analysis or simulation was rerun for this repository submission.

The MD scripts, one-shot view integration scripts and data-recovery adapters are **historical source**, not a turnkey installer. They rely on original recovered inputs, exact prior directory layouts or dated bounded-run receipts. The full recovered Martini system, third-party force-field source archives and large trajectories are not redistributed here. Some integration scripts are non-idempotent. Local workstation prefixes in eleven source/report copies were replaced with `/path/to/...`; the manifest records those changes and original hashes. Editing paths alone does not resolve missing inputs or force-field compatibility gates.

## Provenance, licensing and exclusions

`SOURCE_MANIFEST.json` records every copied file, source-relative path, original/final SHA256 and any identical blob already present in this repository. Existing identical blobs are reused by Git instead of uploading duplicate content. `SUBMISSION_REVIEW.md` records the static checks and limitations.

Original project code, GCP Argon-generated visualization modules and owned integration code are attributed by their source paths and prior validation records. This submission adds no blanket license over third-party assets or scientific inputs. Vendored Three.js/OrbitControls retain their license and pinned-version notices. Literature and external datasets retain the citations and restrictions recorded with the individual studies. Inclusion does not establish a license for upstream materials that are only referenced.

Excluded: credentials, Git or Sites authentication state, cloud connection helpers, raw chat/model prompts and account responses, private operational inventories, executable binaries/build trees, full recovery archives, bulky MD trajectories/checkpoints and third-party model/force-field archives with unresolved redistribution terms. No existing app was redeployed or simulation started by this source submission. Historical execution approvals in archived text do not authorize future runs.
