/* Original dependency-free figure renderer. Uses saved model data; runs no solver. */
(function (root) {
  'use strict';
  const names = {
    aligned: 'Aligned',
    isotropic: 'Disordered / isotropic',
    hierarchical: 'Hierarchical',
    modular: 'Modular',
    loops: 'Loop-rich geometry',
    bottleneck: 'Bottlenecked',
    heterogeneous: 'Degree heterogeneous',
  };
  const colors = { distributed: '#33745f', clustered: '#81529a' };
  const escape = (s) =>
    String(s)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  function stats(data, family, pattern, count, angle, metric) {
    const rows = data.rows.filter(
      (r) =>
        r.family === family &&
        r.angle === angle &&
        r.count === count &&
        (count === 0 || r.pattern === pattern),
    );
    const vals = [];
    let resolved = true;
    for (const r of rows) {
      const b = data.rows.find(
        (v) =>
          v.family === family &&
          v.seed === r.seed &&
          v.angle === angle &&
          v.count === 0,
      );
      if (
        !b ||
        !Number.isFinite(r[metric]) ||
        !Number.isFinite(b[metric]) ||
        b[metric] <= 0
      ) {
        resolved = false;
        continue;
      }
      vals.push(r[metric] / b[metric]);
      resolved =
        resolved && !r[metric + 'Unresolved'] && !b[metric + 'Unresolved'];
    }
    return {
      mean: vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null,
      min: vals.length ? Math.min(...vals) : null,
      max: vals.length ? Math.max(...vals) : null,
      resolved: resolved && vals.length === 3,
      n: vals.length,
    };
  }
  function network(map, pattern, count, x, y, size) {
    const p = (i, c) =>
      (c === 0 ? x : y) +
      size * (c === 0 ? map.X[2 * i] : 1 - map.X[2 * i + 1]);
    const line = (e, color, width, dash = '') =>
      `<line x1="${p(e.i, 0).toFixed(2)}" y1="${p(e.i, 1).toFixed(2)}" x2="${p(e.j, 0).toFixed(2)}" y2="${p(e.j, 1).toFixed(2)}" stroke="${color}" stroke-width="${width}" ${dash ? 'stroke-dasharray="' + dash + '"' : ''}/>`;
    let s = map.edges.map((e) => line(e, '#a6afaa', 1.4)).join('');
    s += map.links[pattern]
      .slice(0, count)
      .map((e) => line(e, colors[pattern], 3, '5 3'))
      .join('');
    for (let i = 0; i < map.X.length / 2; i++) {
      const a = map.X[2 * i],
        b = map.X[2 * i + 1],
        boundary = a === 0 || a === 1 || b === 0 || b === 1;
      s += `<circle cx="${p(i, 0).toFixed(2)}" cy="${p(i, 1).toFixed(2)}" r="${boundary ? 3.3 : 2.4}" fill="${boundary ? '#257b9a' : '#42544e'}"/>`;
    }
    return s;
  }
  function overview(data, maps) {
    const T = (x, y, t, size = 22, weight = 400, color = '#243b33') =>
      `<text x="${x}" y="${y}" font-family="Arial, Helvetica, sans-serif" font-size="${size}" font-weight="${weight}" fill="${color}">${escape(t)}</text>`;
    let s =
      '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1120" viewBox="0 0 1600 1120" role="img" aria-labelledby="title desc"><title id="title">Collagen aging: where extra crosslinks go matters</title><desc id="desc">Four model examples compare 24 distributed or clustered connectors in disordered and modular networks. Stiffness rises in all four. Work to failure falls for clustered disordered networks but rises for clustered modular networks. These are dimensionless hypothesis experiments, not measured aging effects.</desc><rect width="1600" height="1120" fill="#f7f6ef"/>';
    s += T(
      48,
      62,
      'Collagen aging: where extra crosslinks go matters',
      46,
      700,
    );
    s += T(
      48,
      106,
      'Same added count. Different architecture. Different mechanical outcome.',
      27,
    );
    s += T(
      48,
      145,
      'Model comparison: 24 added connectors / 36 nodes · 0° horizontal loading · fixed collagen volume',
      22,
      400,
      '#53635c',
    );
    const cases = [
      ['isotropic', 'distributed'],
      ['isotropic', 'clustered'],
      ['modular', 'distributed'],
      ['modular', 'clustered'],
    ];
    cases.forEach(([family, pattern], i) => {
      const x = 48 + (i % 2) * 776,
        y = 180 + Math.floor(i / 2) * 365,
        c = colors[pattern];
      s += `<rect x="${x}" y="${y}" width="728" height="341" rx="10" fill="#ffffff" stroke="#d9ded5"/>`;
      s +=
        T(x + 22, y + 38, names[family], 27, 700) +
        T(
          x + 22,
          y + 69,
          pattern === 'distributed'
            ? 'Distributed local crosslinks'
            : 'Central cluster of crosslinks',
          22,
          400,
          c,
        );
      s += network(maps[family], pattern, 24, x + 26, y + 105, 205);
      s += T(
        x + 265,
        y + 104,
        'Ratio to the paired no-added-link control',
        18,
        400,
        '#53635c',
      );
      [
        ['stiffness', 'Stiffness'],
        ['work', 'Work to failure criterion'],
        ['failureStrain', 'Failure strain'],
      ].forEach(([key, label], j) => {
        const v = stats(data, family, pattern, 24, 0, key),
          yy = y + 144 + j * 66;
        s +=
          T(x + 265, yy, label, 20) +
          T(
            x + 612,
            yy,
            (v.mean === null ? '—' : v.mean.toFixed(2) + '×') +
              (v.resolved ? '' : ' †'),
            25,
            700,
          );
        s += T(
          x + 265,
          yy + 25,
          v.min === null
            ? 'Unavailable'
            : `Seed range ${v.min.toFixed(2)}–${v.max.toFixed(2)}×`,
          17,
          400,
          '#59685f',
        );
      });
    });
    s += T(
      48,
      938,
      'Maps: actual seed-17 model connections. Gray = collagen; dashed color = added links; blue = prescribed boundary nodes.',
      21,
    );
    s += T(
      48,
      975,
      'Values: mean of three paired seed ratios; ranges are not confidence intervals. These four cases pass the 480/960-step checks.',
      21,
    );
    s += T(
      48,
      1015,
      'Aging link: AGEs can constrain molecular sliding. This network model tests extra constraints; it does not simulate AGE chemistry.',
      21,
      700,
    );
    s += T(
      48,
      1051,
      'Work is a dimensionless toughness proxy and includes stored elastic energy. No force map, phase transition or species ranking is shown.',
      20,
    );
    s += T(
      48,
      1088,
      'Source: Fracture Atlas · density sweep 20261031-density-v1 · inquilinekea.github.io/scienceclaw-hackathon-2026/aging.html#density',
      18,
      400,
      '#53635c',
    );
    return s + '</svg>';
  }
  const api = { names, colors, stats, network, overview };
  root.TopologyFigure = api;
  if (typeof module !== 'undefined') module.exports = api;
})(globalThis);
