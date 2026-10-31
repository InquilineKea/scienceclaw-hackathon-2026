'use strict';
const assert = require('node:assert/strict'),
  M = require('./model.js'),
  A = require('./directional.js');
const net = M.build('aligned', 17),
  b = A.boundary(net, 45, 0.1),
  h = 1e-6;
assert.equal(b.nodes.length, 20);
assert.equal(b.free.length, 32);
for (const angle of [0, 17, 45, 90, 135, 180]) {
  const lo = A.boundary(net, angle, 0.1 - h),
    hi = A.boundary(net, angle, 0.1 + h),
    at = A.boundary(net, angle, 0.1);
  for (const [i, d] of at.deriv)
    assert.ok(
      Math.abs((hi.fixed.get(i) - lo.fixed.get(i)) / (2 * h) - d) < 1e-9,
    );
  for (const [i, v] of at.fixed)
    assert.ok(
      Math.abs(v - A.boundary(net, angle + 180, 0.1).fixed.get(i)) < 1e-12,
    );
}
const initial = M.energy(net, net.X, M.state(net));
assert.ok(Math.abs(initial.U) < 1e-20);
// Virtual work: dU/dstrain at an affine state equals the conjugate boundary reaction.
const affine = (q) => {
  const x = net.X.slice(),
    n = A.direction(31);
  for (let i = 0; i < net.N; i++) {
    const d = n[0] * (net.X[2 * i] - 0.5) + n[1] * (net.X[2 * i + 1] - 0.5);
    x[2 * i] += q * n[0] * d;
    x[2 * i + 1] += q * n[1] * d;
  }
  return x;
};
const q = 0.02,
  x = affine(q),
  ev = M.energy(net, x, M.state(net)),
  n = A.direction(31);
let conjugate = 0;
for (let i = 0; i < net.N; i++) {
  const d = n[0] * (net.X[2 * i] - 0.5) + n[1] * (net.X[2 * i + 1] - 0.5);
  conjugate += d * (n[0] * ev.g[2 * i] + n[1] * ev.g[2 * i + 1]);
}
const numerical =
  (M.energy(net, affine(q + h), M.state(net)).U -
    M.energy(net, affine(q - h), M.state(net)).U) /
  (2 * h);
assert.ok(Math.abs(conjugate - numerical) < 1e-9);
const a = A.simulate(net, 0, { steps: 20, cap: 0.12, frames: false }),
  p = A.simulate(net, 180, { steps: 20, cap: 0.12, frames: false }),
  y = A.simulate(net, 90, { steps: 20, cap: 0.12, frames: false });
assert.deepEqual(a.metrics, p.metrics);
assert.ok(a.metrics.stiffnessValid && y.metrics.stiffnessValid);
assert.ok(a.metrics.stiffness > y.metrics.stiffness * 2);
assert.ok(a.metrics.censored && y.metrics.censored);
assert.equal(a.frames.length, 0);
assert.ok(a.metrics.work >= 0);
// A single horizontal fiber gives an exact analytical conjugate reaction.
const bar = {
  N: 2,
  X: [0, 0.5, 1, 0.5],
  p: { ...M.defaults, crimp: 0 },
  edges: [{ i: 0, j: 1, A: 0.06, L: 1, threshold: 9, sac: false }],
  hinges: [],
};
const br = A.simulate(bar, 0, { steps: 4, cap: 0.01, frames: false });
assert.ok(
  Math.abs(br.metrics.stiffness - (0.06 * M.axial(0.002, bar.p).f) / 0.002) <
    1e-12,
);
assert.equal(
  A.simulate(bar, 90, { steps: 4, cap: 0.01, frames: false }).metrics.stiffness,
  0,
);
// Rotate both the material and imposed direction by 90 degrees: response is invariant.
const rotated = M.build('aligned', 17);
for (let i = 0; i < rotated.N; i++) {
  const x = rotated.X[2 * i],
    y = rotated.X[2 * i + 1];
  rotated.X[2 * i] = 1 - y;
  rotated.X[2 * i + 1] = x;
}
const rr = A.simulate(rotated, 90, { steps: 20, cap: 0.12, frames: false });
assert.ok(Math.abs(rr.metrics.work - a.metrics.work) / a.metrics.work < 1e-6);
console.log(
  JSON.stringify({
    status: 'passed',
    boundaryNodes: 20,
    interiorFreeCoordinates: 32,
    checks: [
      'boundary derivative',
      '180-degree periodicity',
      'zero reference energy',
      'energy gradient virtual work',
      'aligned directional stiffness',
      'censoring',
      'frames disabled',
    ],
    alignedStiffnessX: a.metrics.stiffness,
    alignedStiffnessY: y.metrics.stiffness,
  }),
);
