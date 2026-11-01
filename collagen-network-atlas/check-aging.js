'use strict';
const assert = require('node:assert/strict'),
  M = require('./model.js'),
  D = require('./directional.js'),
  A = require('./aging.js');
const checks = [];
for (const f of M.families) {
  const n = A.build(f, 17),
    base = M.build(f, 17);
  assert.deepEqual(n.X, base.X);
  assert.deepEqual(n.edges, base.edges);
  assert.deepEqual(n.hinges, base.hinges);
  assert.equal(n.links.length, 12);
  assert.ok(n.crosslink.eligibleSites >= 24);
  assert.deepEqual(A.build(f, 17, { count: 4 }).links, n.links.slice(0, 4));
}
checks.push(
  'same collagen geometry, fiber properties, volume and hinges; nested connector sets for all seven families',
);
const n = A.build('loops', 17),
  s = A.state(n),
  x = n.X.map((v, i) => v + 0.003 * Math.sin(i)),
  e = A.energy(n, x, s),
  h = 1e-6;
let error = 0;
for (let i = 0; i < x.length; i++) {
  const p = x.slice(),
    m = x.slice();
  p[i] += h;
  m[i] -= h;
  error = Math.max(
    error,
    Math.abs((A.energy(n, p, s).U - A.energy(n, m, s).U) / (2 * h) - e.g[i]),
  );
}
assert.ok(error < 1e-9);
checks.push('total energy gradient versus finite differences');
const a = 0.37,
  rot = [];
for (let i = 0; i < n.N; i++)
  rot.push(
    Math.cos(a) * x[2 * i] - Math.sin(a) * x[2 * i + 1] + 3,
    Math.sin(a) * x[2 * i] + Math.cos(a) * x[2 * i + 1] - 2,
  );
assert.ok(Math.abs(A.energy(n, rot, s).U - e.U) < 1e-14);
checks.push('rotation/translation invariant connector energy');
const no = A.build('aligned', 17, { count: 0 }),
  r = A.simulate(no, 35, { steps: 30, cap: 0.2, frames: false }),
  b = D.simulate(M.build('aligned', 17), 35, {
    steps: 30,
    cap: 0.2,
    frames: false,
  });
for (const k of ['work', 'stiffness', 'strength', 'finalDamage', 'maxResidual'])
  assert.equal(r.metrics[k], b.metrics[k]);
checks.push('zero added connectors exactly reproduce directional baseline');
const zero = A.simulate(A.build('aligned', 17, { stiffness: 0 }), 35, {
  steps: 30,
  cap: 0.2,
  frames: false,
});
for (const k of ['work', 'stiffness', 'strength', 'finalDamage'])
  assert.equal(zero.metrics[k], b.metrics[k]);
checks.push('zero-stiffness connector control');
const weak = A.build('isotropic', 17, { rupture: 0.001 }),
  ws = A.state(weak),
  stretched = weak.X.map((v) => 0.5 + 1.02 * (v - 0.5)),
  before = A.energy(weak, stretched, ws).U;
assert.ok(A.damage(weak, stretched, ws));
const after = A.energy(weak, stretched, ws).U;
assert.ok(Math.abs(before - after - ws.linkDissipation) < 1e-12);
assert.ok(ws.alive.every(Boolean));
assert.ok(ws.linkAlive.every((v) => !v));
assert.equal(ws.damageDissipation, 0);
checks.push(
  'connector rupture energy accounting separate from collagen damage',
);
const periodic = A.simulate(no, 215, { steps: 30, cap: 0.2, frames: false });
assert.deepEqual(periodic.metrics, r.metrics);
checks.push('180-degree periodicity');
console.log(
  JSON.stringify({ status: 'passed', checks, maximumGradientError: error }),
);
