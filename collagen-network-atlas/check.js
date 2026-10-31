'use strict';
const M = require('./model.js'),
  assert = require('node:assert/strict');
const checks = [];
function test(name, f) {
  f();
  checks.push(name);
}
test('fixed node/edge/volume budgets and connected graphs', () => {
  for (const f of M.families) {
    const n = M.build(f, 17);
    assert.equal(n.N, 36);
    assert.equal(n.edges.length, 82);
    assert.equal(new Set(n.edges.map((e) => e.i + ',' + e.j)).size, 82);
    assert.ok(
      Math.abs(n.edges.reduce((s, e) => s + e.A * e.L, 0) - 0.06) < 1e-12,
    );
    assert.ok(
      M.connectivity(
        n,
        n.edges.map(() => true),
      ).spanning,
    );
  }
});
test('analytic gradient versus central finite differences, including hinges', () => {
  const n = M.build('isotropic', 17, { sacrificial: 0.5 }),
    s = M.state(n),
    x = n.X.map((v, i) => v + (i % 2 ? 0.013 * Math.sin(i) : 0.07 * v));
  const g = M.energy(n, x, s).g;
  for (let i = 0; i < x.length; i++) {
    const a = x.slice(),
      b = x.slice(),
      h = 1e-6;
    a[i] += h;
    b[i] -= h;
    const fd = (M.energy(n, a, s).U - M.energy(n, b, s).U) / (2 * h);
    assert.ok(Math.abs(fd - g[i]) < 2e-8, `${i}: ${fd} vs ${g[i]}`);
  }
});
test('rotation and translation invariant internal energy', () => {
  const n = M.build('loops', 2),
    s = M.state(n),
    x = n.X.map((v, i) => v * (i % 2 ? 0.97 : 1.1)),
    y = [];
  for (let i = 0; i < n.N; i++)
    y.push(
      5 + 0.6 * x[2 * i] - 0.8 * x[2 * i + 1],
      -4 + 0.8 * x[2 * i] + 0.6 * x[2 * i + 1],
    );
  assert.ok(Math.abs(M.energy(n, x, s).U - M.energy(n, y, s).U) < 1e-12);
});
test('eigenvalues and unit capacity cut on analytic path', () => {
  const v = M.eigen(
    [
      [1, -1, 0],
      [-1, 2, -1],
      [0, -1, 1],
    ],
    true,
  );
  [0, 1, 3].forEach((x, i) => assert.ok(Math.abs(x - v.values[i]) < 1e-10));
  assert.equal(
    M.mincut(
      {
        N: 3,
        edges: [
          { i: 0, j: 1 },
          { i: 1, j: 2 },
        ],
      },
      0,
      2,
    ),
    1,
  );
});
test('zero load is stress-free and equilibrium reduces energy', () => {
  const n = M.build('isotropic', 17),
    s = M.state(n);
  assert.ok(M.energy(n, n.X, s).U < 1e-20);
  const b = M.boundary(n, 'tension', 0.12),
    x = n.X.map((v, i) => (i % 2 ? v : v * 1.12)),
    e = M.energy(n, x, s).U,
    r = M.relax(n, x, s, b);
  assert.ok(r.converged);
  assert.ok(M.energy(n, r.x, s).U <= e);
});
test('reaction equals finite difference of minimized energy', () => {
  const n = M.build('loops', 17),
    s = M.state(n),
    q = 0.08,
    h = 1e-4;
  function at(z) {
    const b = M.boundary(n, 'tension', z),
      r = M.relax(n, n.X, s, b, { tol: 1e-9, maxIter: 2000 }),
      e = M.energy(n, r.x, s);
    assert.ok(r.converged);
    return {
      U: e.U,
      F: [...b.deriv].reduce((sum, [i, d]) => sum + d * e.g[i], 0),
    };
  }
  const c = at(q),
    fd = (at(q + h).U - at(q - h).U) / (2 * h);
  assert.ok(Math.abs(fd - c.F) < 1e-6);
});
test('free acceleration is rigid translation without strain or rupture', () => {
  const n = M.build('isotropic', 7),
    r = M.dynamic(n, 'free', { dt: 0.025 });
  assert.ok(r.metrics.maxStrain < 1e-9);
  assert.equal(r.metrics.finalDamage, 0);
  assert.ok(r.curve.at(-1).energy < 1e-18);
});
test('rupture removes collagen and hinge stored energy irreversibly', () => {
  const n = M.build('aligned', 17),
    s = M.state(n),
    x = n.X.map((v, i) => (i % 2 ? v : 1.7 * v));
  const e = M.energy(n, x, s).U;
  assert.ok(M.damage(n, x, s));
  assert.ok(s.alive.some((v) => !v));
  assert.ok(M.energy(n, x, s).U < e);
  assert.ok(s.damageDissipation > 0);
});
test('deterministic seeded generation', () =>
  assert.deepEqual(M.build('hierarchical', 29), M.build('hierarchical', 29)));
console.log(JSON.stringify({ passed: checks.length, checks }, null, 2));
