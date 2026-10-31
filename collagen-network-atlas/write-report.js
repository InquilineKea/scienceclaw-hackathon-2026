'use strict';
require('./run-guard.js').requireRun(__dirname, ['REPORT.md']);
const fs = require('node:fs'),
  D = require('./data/results.json'),
  A = require('./data/audit.json'),
  names = {
    aligned: 'Aligned bundles',
    isotropic: 'Disordered',
    hierarchical: 'Hierarchical',
    modular: 'Modular',
    loops: 'Diagonal reinforcement',
    bottleneck: 'Bottlenecked',
    heterogeneous: 'Degree heterogeneous',
  };
const find = (f, m) => D.summaries.find((r) => r.family === f && r.mode === m),
  fmt = (x) => (x * 1000).toFixed(3),
  cell = (r) =>
    `${fmt(r.meanWork)} ± ${fmt(r.sdWork)}${r.censored ? ' †' + r.censored + '/5' : ''}`,
  mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
let text = `# Fracture Atlas — executed results\n\n${D.date.slice(0, 10)}. **450 local simulations completed**, comprising 280 topology/protocol runs and 170 controls/sensitivities. Seven families, five main seeds and eight loading protocols. All ${A.quasistaticRuns} quasistatic runs met the specified force residual at every recorded step. Inertial runs are time integrations, not equilibria. The benchmark took ${D.runtimeSeconds.toFixed(2)} s in the recorded Node ${A.runtime} execution; browser custom runs are additional interactive calculations and are not included in the benchmark.\n\n**The tested model does not select a universal toughest collagen topology.** In X tension, diagonal reinforcement has the largest sample mean work to the operational criterion, while aligned bundles have the largest mean peak force. The two are on the mean work/strength Pareto frontier. The ranking changes in shear and under a constrained inertial pulse. Compression often reaches the cap without the criterion; it cannot provide a complete failure-toughness ranking. None of these observations is experimental collagen validation.\n\n## Main comparison\n\nAll work values below are energy density ×10⁻³ E₀, mean ± sample SD over five seeds. SD is not a confidence interval. Quasistatic work includes recoverable energy; pulse work is stored energy plus irreversible and damping loss, excluding kinetic energy. These definitions make separate sense for their protocols but do not make them one common material constant.\n\n| Architecture | X tension | Shear | Constrained pulse |\n|---|---:|---:|---:|\n`;
for (const f of Object.keys(names))
  text += `| ${names[f]} | ${cell(find(f, 'tension'))} | ${cell(find(f, 'shear'))} | ${cell(find(f, 'pulse'))} |\n`;
text += `\n† gives the number of capped runs: a mixture of criterion-limited and window-limited work is not a complete toughness estimate. The complete table for all eight protocols is in data/results.json.\n\nIn X tension, aligned bundles reach mean peak reaction ${(find('aligned', 'tension').meanStrength * 1000).toFixed(3)}×10⁻³, versus ${(find('loops', 'tension').meanStrength * 1000).toFixed(3)}×10⁻³ for diagonal reinforcement. The latter deforms farther before meeting the criterion: ${(100 * find('loops', 'tension').meanFailureStrain).toFixed(1)}% versus ${(100 * find('aligned', 'tension').meanFailureStrain).toFixed(1)}% strain. The greater work of diagonal reinforcement is therefore not evidence of greater strength. Its work distribution overlaps the disordered family and depends on the assumed rupture/regularization laws.\n\nA single cut across X makes the bottlenecked network weak in X tension, yet it has the largest sampled mean shear work (${fmt(find('bottleneck', 'shear').meanWork)}×10⁻³), close to the disordered network (${fmt(find('isotropic', 'shear').meanWork)}×10⁻³). Shear uses top/bottom grips, so that X cut does not have the same role. The selected graph motifs and their orientation are confounded; this does not show that bottlenecks are intrinsically tough.\n\nAmong pulse families with all five failures observed, degree-heterogeneous networks have the highest mean internalized work (${fmt(find('heterogeneous', 'pulse').meanWork)}×10⁻³). Modular networks have a higher mixed endpoint mean but one capped run, so they cannot be declared the pulse toughness winner. Damping, density, pulse duration and supports are essential parts of this comparison. The animation continues after first criterion crossing; the score uses the first crossing.\n\n## Pressure and acceleration: what is actually resolved\n\n`;
for (const mode of ['compression', 'confined', 'biaxial']) {
  const r = D.rows.filter((r) => r.group === 'topology' && r.mode === mode);
  text += `- ${mode}: ${r.filter((r) => r.censored).length}/35 runs reached the strain cap without the criterion; ${r.filter((r) => r.finalDamage > 0).length}/35 had permanent collagen rupture.\n`;
}
text += `\nAt 30% imposed compression, resistance can differ between architectures without any complete failure measurement. The “pressure” animation is laterally confined skeleton compression, not imposed hydraulic pressure, pore pressure or a validated hydrostatic shock. No physical extreme-load limit can be inferred.\n\nUniform free acceleration generated maximum fiber strain ${A.maxFreeStrain.toExponential(2)} and internalized work ${A.maxFreeInternalizedWork.toExponential(2)} across the 35 baseline free runs, with zero rupture. External work largely became rigid-body kinetic energy. Clamping one edge under the same acceleration produced deformation and damage. The relevant specification is body force with mass, geometry, supports and time history, not acceleration alone.\n\n## Which statistics predicted work?\n\nSpearman correlations below use converged, uncensored topology samples; they are descriptive and family-confounded. Mean degree (4.556), coordination excess (0.556) and cycle rank (47) are constant in the fixed-budget sample, so they cannot explain its variation.\n\n| Predictor | X tension (n=35) | Shear (n=30) |\n|---|---:|---:|\n`;
for (const key of [
  'lambda2',
  'weightedLambda2',
  'normalizedLambda2',
  'maxBetweenness',
  'degreeVariance',
  'anisotropy',
  'alignmentX',
  'hessianMin',
  'softIPR',
]) {
  const get = (m) =>
    D.correlations.find((r) => r.mode === m && r.predictor === key)?.spearman;
  text += `| ${key} | ${get('tension')?.toFixed(3) ?? 'undefined'} | ${get('shear')?.toFixed(3) ?? 'undefined'} |\n`;
}
text += `\nThe unweighted λ₂ association is modest in X tension and weak in shear. Degree variance has essentially no X-tension association. Betweenness and soft-mode localization have stronger negative X-tension associations in this sample, but none is a sufficient scalar explanation. Reference Hessian modes include geometry and bending; their smallest eigenvalue relates more strongly to shear work here, without establishing a general predictor.\n\nAn exact counterexample to a direction-blind graph score is the same aligned seed-17 graph under X versus Y tension: every graph eigenvalue is identical. X reaches its criterion; Y remains very soft and capped. We do not form a ratio of two “toughnesses” when one did not fail, and the tiny Y/shear work is sensitive to solver tolerance.\n\n### Held-out prediction of log work, X tension\n\nRidge penalty 1, training-only standardization; hold-out seeds 71 and 101. “Mechanical” includes the initial secant stiffness measured during loading, so it is not a zero-test topology predictor.\n\n| Features | Seed hold-out R² | Leave-one-family-out R² |\n|---|---:|---:|\n`;
for (const features of [
  'mean',
  'spectral',
  'geometry',
  'mechanical',
  'combined',
]) {
  const get = (s) =>
    D.validation.find(
      (r) => r.mode === 'tension' && r.features === features && r.split === s,
    ).logWorkR2;
  text += `| ${features} | ${get('held-out seeds').toFixed(3)} | ${get('leave-one-family-out').toFixed(3)} |\n`;
}
text += `\nThe combined predictor works on new seeds of known families, but all tested feature sets have negative family-held-out R². Purely spectral prediction fails particularly badly when transferred to a new architecture. No predictor demonstrated reliable cross-family generalization. Y-tension and shear validation results, including additional negative R² values, are retained in full.\n\n## Composition, cycles, density and uncertainty\n\nThe independent composition sweep uses three disordered-network seeds. Doubling collagen volume approximately doubles work in this law, as expected from its linear energy prefactor; this is a constitutive scaling check, not new evidence of biological toughening. Diameter, bending, crimp, segment preference, material allocation and rupture disorder have conditional effects. The elastin-like parallel background increases total material and survives collagen rupture; its higher work must not be credited to collagen topology alone.\n\nThe six subfailure cyclic runs show additional loss when hypothetical sacrificial links are present. Mean cycle work is ${mean(D.rows.filter((r) => r.group === 'cycles' && r.label === 'sacrificial=0').map((r) => r.hysteresis)).toExponential(3)} without those links and ${mean(D.rows.filter((r) => r.group === 'cycles' && r.label === 'sacrificial=0.7').map((r) => r.hysteresis)).toExponential(3)} with them. The difference tests the implemented mechanism, not a native crosslink identity. Individual irreversible-loss terms and curves are in the dataset.\n\nThe edge-count sweep includes mean degrees below and above the bulk 2D Maxwell counting value. Its rows vary connectivity at fixed collagen volume and are not pooled into the topology predictor analysis. The finite-size checks change the realization; they do not establish continuum convergence.\n\n## What the checks support — and what they do not\n\n- Nine physical/numerical checks pass; seven baseline tensile re-runs reproduce stored work within ${A.reproducibilityError.toExponential(2)} rounding error.\n- Maximum free-DOF residual among all quasistatic records: ${A.maxResidual.toExponential(3)}. All production runs passed their specified residual test.\n- Halving the load increment changes uncensored seed-17 tension/shear work by at most ${(100 * Math.max(...D.convergence.filter((r) => r.label === 'half load step' && !r.baseCensored && !r.censored).map((r) => Math.abs(r.relativeChange)))).toFixed(1)}%. Thus event resolution is useful but not fully converged.\n- Tightening force tolerance reduces the tiny aligned shear work by about 96%; that near-floppy number is numerically unresolved and is not used as an uncensored target.\n- Halving the pulse time step in three families changes internalized work by at most ${(100 * Math.max(...D.convergence.filter((r) => r.label === 'half time step').map((r) => Math.abs(r.relativeChange)))).toFixed(2)}%. Baseline constrained-pulse energy-balance error is at most ${(100 * A.maxPulseRelativeEnergyError).toFixed(3)}% of external work.\n- Changing the artificial collapse coefficient from 20 to 10 or 40 changes seed-17 tension/shear work by at most ${(100 * Math.max(...D.convergence.filter((r) => r.label.startsWith('collapse')).map((r) => Math.abs(r.relativeChange)))).toFixed(1)}%. This narrow sensitivity does not make the regularizer physical.\n\nThese are implementation and sensitivity checks, not experimental validation. Local minima, event-triggered failure, small seed counts, artificial graph generators, 2D geometry and omitted contact/fluid mechanics remain material limitations. No molecular proxy calibration or absolute extreme-load prediction was performed.\n\n## Deliverables and provenance\n\nThe interactive gallery, comparison animation, CSV/JSON results, representative trajectories, source, logs, checks, five GIFs and PNG/SVG figures are local files in this package. Every visual uses executed simulation output. See METHODS.md for equations and precise definitions, EVIDENCE.md for primary literature, and SECURITY-REVIEW.md for the bounded source inspection. Model SHA-256: ${D.modelHash}.\n`;
fs.writeFileSync('REPORT.md', text);
console.log('Wrote evidence-linked result report.');
