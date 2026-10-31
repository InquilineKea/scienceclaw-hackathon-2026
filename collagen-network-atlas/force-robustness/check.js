const assert = require('node:assert/strict'),
  { measure } = require('./run.js');
const net = {
  X: [0, 0, 0.1, 0, 0.2, 0, 0.8, 0, 0.9, 0, 1, 0],
  edges: [
    { i: 0, j: 1, A: 1, L: 1 },
    { i: 1, j: 2, A: 1, L: 1 },
    { i: 3, j: 4, A: 1, L: 1 },
    { i: 4, j: 5, A: 1, L: 1 },
  ],
};
const run = (forces, alive) =>
  measure(net, {
    metrics: { valid: true, criterion: 'test' },
    frames: [
      { q: 0.05, damage: 0, forces },
      { q: 0.1, damage: 0.5, alive },
    ],
  });
let a = run([1, 1, 1, 1], [false, false, true, true]),
  b = run([1, 0, 0, 0], [false, true, false, true]);
assert.equal(a.participation, 1);
assert.equal(a.maxShare, 0.25);
assert.equal(b.participation, 0.25);
assert.equal(b.maxShare, 1);
assert.equal(a.patch, 1);
assert.equal(b.patch, 0.5);
assert.ok(Math.abs(a.spread - 0.05 / Math.SQRT2) < 1e-12);
assert.ok(Math.abs(b.spread - 0.4 / Math.SQRT2) < 1e-12);
const d = require('./results.json');
assert.equal(d.rows.length, 480);
assert.equal(
  new Set(d.rows.map((r) => [r.family, r.seed, r.angle, r.pattern].join(':')))
    .size,
  480,
);
assert.ok(d.rows.every((r) => r.valid && r.coarse.valid));
console.log(
  'Passed analytical force limits, connected/disconnected damage geometry, unique complete sweep, all equilibria valid',
);
