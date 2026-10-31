# Fracture Atlas

Interactive collagen-inspired network comparison with original numerical code, 450 bounded local runs, seed variability, held-out predictor tests, static plots and real simulation-derived animations. No packages or network services are required for the core explorer.

Open `index.html` directly in a modern browser, or serve this folder on loopback:

```sh
python3 -I -m http.server 8769 --bind 127.0.0.1
```

Visit http://127.0.0.1:8769. Choose two architectures, select a loading mode and scrub or play the synchronized timeline. “Edit assumptions” computes new original model traces locally. Browser workers keep computation separate from the interface when served over HTTP; direct file opening uses a main-thread fallback. The scientific benchmark never changes when a custom slider changes.

## Reproduce the numerical results

Use an already trusted Node.js runtime (the recorded run used Node 26.12.1; no npm/pnpm installation):

```sh
node check.js
node benchmark.js
node prepare-media.js
```

`benchmark.js` deterministically rewrites `data/results.json`, CSVs, `benchmark.js` and `replays.js`. Runtime is machine-dependent. Run logs are retained. Seeds and model hash are embedded in the analysis. Rendering on macOS uses only original drawing code and native frameworks:

```sh
swift -module-cache-path /tmp/collagen-atlas-swift-cache render-media.swift
```

No generative image model fabricated any scientific geometry or plotted point. `prepare-media.js` creates a standalone accessible SVG, and `render-media.swift` creates PNGs and five animated GIFs from computed trajectories.

## Contents

- `model.js`: generator, axial/bending mechanics, rupture, equilibrium and inertial solvers, graph and Hessian diagnostics.
- `benchmark.js`: controlled topology/edge-count/composition sweeps, cycles, convergence, held-out analysis.
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
