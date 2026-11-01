'use strict';
const fs = require('node:fs'),
  { Worker, isMainThread, parentPort } = require('node:worker_threads'),
  A = require('../aging.js');
function measure(net, r) {
  const f = r.frames.findLast((x) => x.q <= 0.05 + 1e-10);
  let participation = null,
    maxShare = null;
  if (f && f.q >= 0.048 && f.damage === 0) {
    const w = f.forces.map(Math.abs),
      s = w.reduce((a, b) => a + b, 0);
    participation = (s * s) / (w.length * w.reduce((a, b) => a + b * b, 0));
    maxShare = Math.max(...w) / s;
  }
  const hit = r.frames.find((x) => x.damage >= 0.1);
  let spread = null,
    patch = null;
  if (hit) {
    const broken = net.edges
        .map((e, idx) => ({ ...e, idx }))
        .filter((e) => !hit.alive[e.idx]),
      pts = broken.map((e) => [
        (net.X[e.i * 2] + net.X[e.j * 2]) / 2,
        (net.X[e.i * 2 + 1] + net.X[e.j * 2 + 1]) / 2,
        e.A * e.L,
      ]);
    const total = pts.reduce((s, p) => s + p[2], 0),
      cx = pts.reduce((s, p) => s + p[0] * p[2], 0) / total,
      cy = pts.reduce((s, p) => s + p[1] * p[2], 0) / total;
    spread =
      Math.sqrt(
        pts.reduce(
          (s, p) => s + p[2] * ((p[0] - cx) ** 2 + (p[1] - cy) ** 2),
          0,
        ) / total,
      ) / Math.SQRT2;
    const seen = new Set(),
      masses = [];
    for (const e of broken) {
      if (seen.has(e.idx)) continue;
      const q = [e];
      seen.add(e.idx);
      let mass = 0;
      for (let j = 0; j < q.length; j++) {
        const a = q[j];
        mass += a.A * a.L;
        for (const b of broken)
          if (
            !seen.has(b.idx) &&
            (a.i === b.i || a.i === b.j || a.j === b.i || a.j === b.j)
          ) {
            seen.add(b.idx);
            q.push(b);
          }
      }
      masses.push(mass);
    }
    patch = Math.max(...masses) / total;
  }
  return {
    participation,
    maxShare,
    spread,
    patch,
    damageAtSample: hit?.damage ?? null,
    strainAtDamage: hit?.q ?? null,
    valid: r.metrics.valid,
    criterion: r.metrics.criterion,
  };
}
// Edge IDs must be separate from endpoint IDs.
if (!isMainThread) {
  parentPort.on('message', (t) => {
    const net = A.build(t.family, t.seed, { count: 24, pattern: t.pattern }),
      a = measure(net, A.simulate(net, t.angle, { steps: 480 })),
      b = measure(net, A.simulate(net, t.angle, { steps: 960 }));
    const flags = {};
    for (const k of ['participation', 'maxShare', 'spread', 'patch'])
      flags[k] =
        !a.valid ||
        !b.valid ||
        a[k] === null ||
        b[k] === null ||
        Math.abs(a[k] - b[k]) /
          Math.max(Math.abs(a[k]), Math.abs(b[k]), 1e-12) >=
          0.05;
    parentPort.postMessage({ ...t, ...b, coarse: a, unresolved: flags });
  });
} else if (require.main === module) {
  const seeds = [17, 29, 43, 67, 83, 101, 127, 149, 173, 197],
    angles = Array.from({ length: 12 }, (_, i) => 15 * i),
    tasks = [];
  for (const family of ['isotropic', 'modular'])
    for (const seed of seeds)
      for (const angle of angles)
        for (const pattern of ['distributed', 'clustered'])
          tasks.push({ family, seed, angle, pattern });
  let next = 0,
    done = 0;
  const rows = [],
    workers = [],
    start = Date.now();
  for (let i = 0; i < 2; i++) {
    const w = new Worker(__filename);
    workers.push(w);
    w.on('message', (r) => {
      rows.push(r);
      done++;
      if (done % 40 === 0) console.log(done + '/' + tasks.length);
      if (done === tasks.length) {
        fs.writeFileSync(
          'results.json',
          JSON.stringify({
            seeds,
            angles,
            steps: [480, 960],
            count: 24,
            started: new Date(start).toISOString(),
            elapsedSeconds: (Date.now() - start) / 1000,
            rows,
          }),
        );
        for (const x of workers) x.terminate();
      } else if (next < tasks.length) w.postMessage(tasks[next++]);
    });
    w.postMessage(tasks[next++]);
  }
}

module.exports = { measure };
