# Fracture Atlas

**[Launch the public interactive explorer](https://inquilinekea.github.io/scienceclaw-hackathon-2026/).** Green arrows show prescribed motion/body-force directions; cyan marks identify held coordinates. Initial fiber orientation is reported separately from loading direction. Public hosting uses the bounded static `/docs` copy described in [PAGES.md](../PAGES.md); the numerical model and frozen archives are unchanged.

Interactive collagen-inspired network comparison with original numerical code, 450 bounded local runs, seed variability, held-out predictor tests, static plots and real simulation-derived animations. No packages or network services are required for the core explorer.

Open `index.html` directly in a modern browser, or serve this folder on loopback:

```sh
python3 -I -m http.server 8769 --bind 127.0.0.1
```

Visit http://127.0.0.1:8769. Choose two architectures, select a loading mode and scrub or play the synchronized timeline. “Edit assumptions” computes new original model traces locally. Browser workers keep computation separate from the interface when served over HTTP; direct file opening uses a main-thread fallback. The scientific benchmark never changes when a custom slider changes.

## Reproduce without overwriting any saved run

Use an already trusted Node.js and Python 3 runtime. No package installation is required:

```sh
node benchmark.js
# On macOS, also create the PNG/GIF outputs:
node benchmark.js --render
```

Every command reserves a new `runs/<UTC-timestamp>-<random-id>/` folder, snapshots the current source, and records parameters, results, logs and file checksums there. Failed jobs retain their folder and logs. An explicit `--run-id NAME` is optional and **fails if NAME already exists**. There is no overwrite/resume option. `--prepare-only` creates a source snapshot without running the model.

The pipeline runs the original numerical checks, 450-case benchmark, audit, media preparation and report generation. `--render` adds native macOS rendering. Open the resulting run's `index.html` to inspect that run; the root viewer continues to show the frozen baseline. Do not redirect output into an older run's files or invoke historical writer scripts from a frozen folder.

The completed baseline is in [runs/20261031-finished-f0a5034f44aa](runs/20261031-finished-f0a5034f44aa/). Its media were rebuilt to match the final numerical results after an earlier rendering bundle was found to contain older pulse/free states. Original media and archives remain preserved with provenance. See [RUN_STORAGE.md](RUN_STORAGE.md).

## Contents

- `model.js`: generator, axial/bending mechanics, rupture, equilibrium and inertial solvers, graph and Hessian diagnostics.
- `benchmark.js` / `run-atlas.py`: non-overwriting run entry point. `benchmark-core.js`: controlled sweeps and analysis within a fresh run.
- `check.js`: original numerical and physical-invariance checks.
- `index.html`, `style.css`, `app.js`, `worker.js`: local accessible explorer.
- `data/summary.csv`: 450 complete per-run input/output records. `n` is grid width; `nodes` is node count.
- `data/curves.csv`: all recorded force/work/damage traces, including convergence and control runs.
- `data/results.json`: analysis, means/SDs, correlations, regression scores and sensitivity records.
- `data/replays.js`: representative seed-17 geometries and simulation frames for every topology/protocol; not idealized interpolation.
- `figures/`: standalone chart, static animation fallbacks and five actual simulations as GIFs.
- `METHODS.md`: equations, supports, energy definitions, criteria and limitations.
- `REPORT.md`: tested findings and negative results.
- `EVIDENCE.md`: primary-literature ledger and molecular-evidence exclusions.
- `SECURITY-REVIEW.md`: inspected prior context and execution boundary.

## Read the result correctly

All material laws are hypothetical. These are small, embedded 2D graphs with common assumed rupture rules; they are not experimentally calibrated collagen tissues. Work density is not crack-area fracture energy. Pressure modes solve solid skeleton compression only. Pulse work excludes kinetic energy. A capped run has not measured complete work to failure. All families have the same edge count and cycle rank in the main comparison. The diagonal-reinforcement family’s name does not mean it has more cycles.

The model is useful for asking how geometry, support direction and failure redistribution defeat simple scalar graph predictors. It cannot establish native crosslink strength, hydration response, shock resistance, safety under extreme loads or a universal toughest network.
