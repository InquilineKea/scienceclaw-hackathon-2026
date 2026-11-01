'use strict';
require('./run-guard.js').requireRun(__dirname, [
  'data/results.json',
  'data/summary.csv',
  'data/curves.csv',
  'data/replays.js',
  'data/benchmark.js',
  'data/predictors.csv',
  'data/validation.csv',
  'data/convergence.csv',
]);

// Original bounded local benchmark. Only Node standard library + our model.
const fs = require('node:fs'),
  crypto = require('node:crypto'),
  M = require('./model.js');
const seeds = [17, 29, 43, 71, 101],
  modes = [
    'tension',
    'tensionY',
    'shear',
    'compression',
    'confined',
    'biaxial',
    'pulse',
    'free',
  ];
const rows = [],
  examples = {},
  networks = [],
  curves = [],
  start = Date.now();
const round = (x) => (typeof x === 'number' ? Number(x.toPrecision(7)) : x);
function compact(v) {
  if (Array.isArray(v)) return v.map(compact);
  if (v && typeof v === 'object')
    return Object.fromEntries(
      Object.entries(v).map(([k, x]) => [k, compact(x)]),
    );
  return round(v);
}
function run(
  group,
  family,
  seed,
  p = {},
  mode = 'tension',
  options = {},
  label = 'baseline',
) {
  const net = M.build(family, seed, p),
    r = M.simulate(net, mode, {
      ...options,
      frames: group === 'topology' && seed === 17,
    }),
    metrics = M.graphMetrics(net, group === 'topology');
  const row = {
    group,
    label,
    family,
    seed,
    mode,
    nodes: net.N,
    edges: net.edges.length,
    ...net.p,
    ...metrics,
    ...r.metrics,
  };
  rows.push(row);
  r.curve.forEach((c) =>
    curves.push({ group, label, family, seed, mode, ...c }),
  );
  if (group === 'topology' && seed === 17)
    examples[family + ':' + mode] = {
      net: {
        family,
        seed,
        p: net.p,
        N: net.N,
        X: net.X,
        edges: net.edges,
        hinges: net.hinges,
      },
      ...r,
      frames: r.frames.map(({ strains, sac, ...f }) => f),
    };
  return { net, result: r, row };
}
for (const family of M.families) {
  for (const seed of seeds) {
    const net = M.build(family, seed),
      gm = M.graphMetrics(net);
    networks.push({ family, seed, ...gm });
    for (const mode of modes) {
      const r = M.simulate(net, mode, { frames: seed === 17 }),
        row = {
          group: 'topology',
          label: 'baseline',
          family,
          seed,
          mode,
          nodes: net.N,
          edges: net.edges.length,
          ...net.p,
          ...gm,
          ...r.metrics,
        };
      rows.push(row);
      r.curve.forEach((c) =>
        curves.push({
          group: 'topology',
          label: 'baseline',
          family,
          seed,
          mode,
          ...c,
        }),
      );
      if (seed === 17)
        examples[family + ':' + mode] = {
          net: {
            family,
            seed,
            p: net.p,
            N: net.N,
            X: net.X,
            edges: net.edges,
            hinges: net.hinges,
          },
          ...r,
          frames: r.frames.map(({ strains, sac, ...f }) => f),
        };
    }
  }
  console.log(
    'completed topology',
    family,
    Math.round((Date.now() - start) / 1000) + 's',
  );
}
// Density sweep is independent of topology: fixed collagen volume, changing E.
for (const edges of [55, 68, 82, 100])
  for (const seed of seeds.slice(0, 3))
    for (const mode of ['tension', 'shear'])
      run('density', 'isotropic', seed, { edges }, mode, {}, 'edges=' + edges);
// Independent hypotheses; none named after molecular crosslink identities.
const variants = [
  ['reference', {}],
  ['half volume', { phi: 0.03 }],
  ['double volume', { phi: 0.12 }],
  ['thin fibrils', { diameter: 0.0125 }],
  ['thick fibrils', { diameter: 0.05 }],
  ['straight', { crimp: 0 }],
  ['more crimp', { crimp: 0.08 }],
  ['low bending', { bend: 2 }],
  ['high bending', { bend: 80 }],
  ['sacrificial links', { sacrificial: 0.7 }],
  ['elastic background', { elastin: 0.1 }],
  ['heterogeneous allocation', { distribution: 1.2 }],
  ['longer segments', { lengthBias: 0.25 }],
  ['high rupture disorder', { disorder: 0.45 }],
];
for (const [label, p] of variants)
  for (const seed of seeds.slice(0, 3))
    run('composition', 'isotropic', seed, p, 'tension', {}, label);
for (const seed of seeds.slice(0, 3))
  for (const f of [0, 0.7])
    run(
      'cycles',
      'isotropic',
      seed,
      { sacrificial: f, rupture: 2 },
      'tension',
      { cycle: true, cap: 0.18, steps: 60 },
      'sacrificial=' + f,
    );
const convergence = [];
for (const family of M.families)
  for (const mode of ['tension', 'shear']) {
    const base = rows.find(
      (r) =>
        r.group === 'topology' &&
        r.family === family &&
        r.seed === 17 &&
        r.mode === mode,
    );
    for (const [label, opt, p] of [
      ['half load step', { steps: 120 }, {}],
      ['tight force tolerance', { tol: 2e-8, maxIter: 3000 }, {}],
      ['collapse coefficient 10', {}, { collapse: 10 }],
      ['collapse coefficient 40', {}, { collapse: 40 }],
    ]) {
      const q = run('convergence', family, 17, p, mode, opt, label).row;
      convergence.push({
        family,
        mode,
        label,
        baseWork: base.work,
        work: q.work,
        relativeChange: (q.work - base.work) / Math.max(base.work, 1e-12),
        valid: q.valid,
        baseCensored: base.censored,
        censored: q.censored,
      });
    }
  }
for (const f of ['isotropic', 'aligned', 'bottleneck']) {
  const base = rows.find(
    (r) =>
      r.group === 'topology' &&
      r.family === f &&
      r.seed === 17 &&
      r.mode === 'pulse',
  );
  const q = run(
    'convergence',
    f,
    17,
    {},
    'pulse',
    { dt: 0.00625 },
    'half time step',
  ).row;
  convergence.push({
    family: f,
    mode: 'pulse',
    label: 'half time step',
    baseWork: base.work,
    work: q.work,
    relativeChange: (q.work - base.work) / Math.max(base.work, 1e-12),
    valid: q.valid,
    baseCensored: base.censored,
    censored: q.censored,
  });
}
for (const pulse of [2, 8, 24])
  for (const density of [0.5, 1, 2])
    for (const seed of seeds.slice(0, 3))
      run(
        'pulse_sensitivity',
        'isotropic',
        seed,
        { pulse, density },
        'pulse',
        {},
        `duration=${pulse}; density=${density}`,
      );
// A small finite-size sensitivity, not a claimed continuum convergence study.
for (const n of [5, 7])
  for (const family of ['isotropic', 'loops'])
    for (const seed of seeds.slice(0, 3))
      run(
        'size',
        family,
        seed,
        { n, edges: Math.round((82 * n * n) / 36) },
        'tension',
        {},
        'grid=' + n,
      );
const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length,
  sd = (a) =>
    a.length < 2
      ? 0
      : Math.sqrt(
          a.reduce((s, x) => s + (x - mean(a)) ** 2, 0) / (a.length - 1),
        );
function ranks(x) {
  return x.map(
    (v) =>
      x.filter((t) => t < v).length + (x.filter((t) => t === v).length - 1) / 2,
  );
}
function corr(a, b) {
  const ma = mean(a),
    mb = mean(b),
    num = a.reduce((s, x, i) => s + (x - ma) * (b[i] - mb), 0),
    den = Math.sqrt(
      a.reduce((s, x) => s + (x - ma) ** 2, 0) *
        b.reduce((s, x) => s + (x - mb) ** 2, 0),
    );
  return den > 1e-20 ? num / den : null;
}
const predictors = [
  'degree',
  'degreeVariance',
  'coordinationExcess',
  'cycles',
  'kcore',
  'edgeConnectivity',
  'maxBetweenness',
  'anisotropy',
  'alignmentX',
  'clustering',
  'modularity',
  'lambda2',
  'lambda3minus2',
  'weightedLambda2',
  'normalizedLambda2',
  'hessianMin',
  'softModes',
  'softIPR',
  'meanLength',
];
const correlations = [],
  summaries = [];
for (const mode of modes) {
  const subset = rows.filter(
    (r) => r.group === 'topology' && r.mode === mode && r.valid && !r.censored,
  );
  if (subset.length >= 10)
    for (const key of predictors)
      correlations.push({
        mode,
        predictor: key,
        n: subset.length,
        spearman: corr(
          ranks(subset.map((r) => r[key])),
          ranks(subset.map((r) => r.work)),
        ),
      });
  for (const family of M.families) {
    const rr = rows.filter(
        (r) => r.group === 'topology' && r.mode === mode && r.family === family,
      ),
      valid = rr.filter((r) => r.valid);
    summaries.push({
      mode,
      family,
      n: rr.length,
      valid: valid.length,
      censored: valid.filter((r) => r.censored).length,
      meanWork: mean(valid.map((r) => r.work)),
      sdWork: sd(valid.map((r) => r.work)),
      meanStrength: mean(valid.map((r) => r.strength)),
      sdStrength: sd(valid.map((r) => r.strength)),
      meanFailureStrain: valid.some((r) => r.failureStrain !== null)
        ? mean(
            valid
              .filter((r) => r.failureStrain !== null)
              .map((r) => r.failureStrain),
          )
        : null,
      regularized: valid.filter((r) => r.collapseUsed).length,
    });
  }
}
function solve(A, b) {
  A = A.map((r, i) => r.concat(b[i]));
  const n = b.length;
  for (let i = 0; i < n; i++) {
    let p = i;
    for (let j = i + 1; j < n; j++)
      if (Math.abs(A[j][i]) > Math.abs(A[p][i])) p = j;
    [A[i], A[p]] = [A[p], A[i]];
    const div = A[i][i];
    if (Math.abs(div) < 1e-15) return Array(n).fill(0);
    for (let k = i; k <= n; k++) A[i][k] /= div;
    for (let j = 0; j < n; j++)
      if (j !== i) {
        const z = A[j][i];
        for (let k = i; k <= n; k++) A[j][k] -= z * A[i][k];
      }
  }
  return A.map((r) => r[n]);
}
function fitPredict(train, test, keys) {
  const mu = keys.map((k) => mean(train.map((r) => r[k]))),
    sigma = keys.map((k, i) => sd(train.map((r) => r[k])) || 1),
    features = (r) => [1, ...keys.map((k, i) => (r[k] - mu[i]) / sigma[i])],
    X = train.map(features),
    y = train.map((r) => Math.log(r.work + 1e-12)),
    d = keys.length + 1;
  const A = Array.from({ length: d }, (_, i) =>
      Array.from(
        { length: d },
        (_, j) =>
          X.reduce((s, x) => s + x[i] * x[j], 0) + (i === j && i > 0 ? 1 : 0),
      ),
    ),
    b = Array.from({ length: d }, (_, i) =>
      X.reduce((s, x, j) => s + x[i] * y[j], 0),
    ),
    beta = solve(A, b);
  return test.map((r) => ({
    actual: Math.log(r.work + 1e-12),
    prediction: features(r).reduce((s, v, i) => s + v * beta[i], 0),
  }));
}
const featureSets = {
    mean: [],
    spectral: ['lambda2', 'weightedLambda2', 'normalizedLambda2'],
    geometry: ['alignmentX', 'anisotropy', 'meanLength'],
    mechanical: ['hessianMin', 'softIPR', 'stiffness'],
    combined: ['lambda2', 'maxBetweenness', 'alignmentX', 'stiffness'],
  },
  validation = [];
for (const mode of ['tension', 'tensionY', 'shear']) {
  const r = rows.filter(
    (r) => r.group === 'topology' && r.mode === mode && r.valid && !r.censored,
  );
  if (r.length < 15) continue;
  for (const [label, keys] of Object.entries(featureSets))
    for (const split of ['held-out seeds', 'leave-one-family-out']) {
      let pred = [];
      if (split === 'held-out seeds')
        pred = fitPredict(
          r.filter((a) => seeds.slice(0, 3).includes(a.seed)),
          r.filter((a) => seeds.slice(3).includes(a.seed)),
          keys,
        );
      else
        for (const f of M.families) {
          const train = r.filter((a) => a.family !== f),
            test = r.filter((a) => a.family === f);
          if (test.length) pred.push(...fitPredict(train, test, keys));
        }
      const avg = mean(pred.map((p) => p.actual)),
        sse = pred.reduce((s, p) => s + (p.actual - p.prediction) ** 2, 0),
        sst = pred.reduce((s, p) => s + (p.actual - avg) ** 2, 0);
      validation.push({
        mode,
        features: label,
        split,
        n: pred.length,
        logWorkR2: 1 - sse / sst,
        logWorkRMSE: Math.sqrt(sse / pred.length),
      });
    }
}
const pareto = summaries
  .filter((s) => s.mode === 'tension' && s.valid === 5 && s.censored === 0)
  .filter(
    (a) =>
      !summaries.some(
        (b) =>
          b.mode === 'tension' &&
          b.valid === 5 &&
          b.censored === 0 &&
          b.family !== a.family &&
          b.meanWork >= a.meanWork &&
          b.meanStrength >= a.meanStrength &&
          (b.meanWork > a.meanWork || b.meanStrength > a.meanStrength),
      ),
  )
  .map((x) => x.family);
const data = compact({
  date: new Date().toISOString(),
  modelHash: crypto
    .createHash('sha256')
    .update(fs.readFileSync(__dirname + '/model.js'))
    .digest('hex'),
  seeds,
  modes,
  defaults: M.defaults,
  rows,
  summaries,
  correlations,
  validation,
  convergence,
  pareto,
  runtimeSeconds: (Date.now() - start) / 1000,
});
function csv(path, rr) {
  const keys = [...new Set(rr.flatMap(Object.keys))],
    quote = (v) => (v === null || v === undefined ? '' : JSON.stringify(v));
  fs.writeFileSync(
    path,
    keys.join(',') +
      '\n' +
      rr.map((r) => keys.map((k) => quote(r[k])).join(',')).join('\n') +
      '\n',
  );
}
fs.writeFileSync(
  __dirname + '/data/results.json',
  JSON.stringify(data, null, 2),
);
fs.writeFileSync(
  __dirname + '/data/benchmark.js',
  'globalThis.ATLAS_DATA=' + JSON.stringify(data) + ';\n',
);
fs.writeFileSync(
  __dirname + '/data/replays.js',
  'globalThis.ATLAS_REPLAYS=' + JSON.stringify(compact(examples)) + ';\n',
);
csv(__dirname + '/data/summary.csv', data.rows);
csv(__dirname + '/data/curves.csv', curves);
csv(__dirname + '/data/predictors.csv', data.correlations);
csv(__dirname + '/data/validation.csv', data.validation);
csv(__dirname + '/data/convergence.csv', data.convergence);
console.log(
  JSON.stringify(
    {
      runs: rows.length,
      unconverged: rows.filter((r) => !r.valid).length,
      runtimeSeconds: data.runtimeSeconds,
      pareto,
    },
    null,
    2,
  ),
);
