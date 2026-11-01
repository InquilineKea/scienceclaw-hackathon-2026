/* Original static visualization of saved, paired density experiments. */
(() => {
  'use strict';
  const data = globalThis.ATLAS_DENSITY_DATA,
    $ = (id) => document.getElementById(id);
  if (!data) {
    $('densityStatus').textContent = 'Density data unavailable.';
    return;
  }
  const families = CollagenAtlas.families,
    colors = { distributed: '#20775b', clustered: '#8950a0' },
    names = {
      aligned: 'Aligned',
      isotropic: 'Isotropic',
      hierarchical: 'Hierarchical',
      modular: 'Modular',
      loops: 'Loops',
      bottleneck: 'Bottleneck',
      heterogeneous: 'Heterogeneous',
    };
  const labels = {
    stiffness: 'Stiffness K',
    work: 'Work to failure criterion W',
    failureStrain: 'Strain at failure criterion',
    workBeforeDamage: 'Work before first bond damage',
    workBeforeCollagenDamage: 'Work before first collagen damage',
  };
  const fmt = (v) =>
    Number.isFinite(v)
      ? Math.abs(v) < 0.01 && v !== 0
        ? v.toExponential(2)
        : v.toFixed(3)
      : '—';
  const index = new Map(
    data.rows.map((r) => [
      [r.family, r.seed, r.angle, r.count, r.pattern].join('|'),
      r,
    ]),
  );
  function row(f, s, a, c, p) {
    return index.get([f, s, a, c, c === 0 ? 'distributed' : p].join('|'));
  }
  function sample(f, c, p, k) {
    const angle = +$('densityAngle').value,
      seeds =
        $('densitySeed').value === 'all'
          ? data.seeds
          : [+$('densitySeed').value],
      ratio = $('densityScale').value === 'ratio';
    const points = seeds.map((s) => {
      const r = row(f, s, angle, c, p),
        b = row(f, s, angle, 0, p);
      if (!r || !b) return null;
      const ok =
        Number.isFinite(r[k]) &&
        (!ratio || (Number.isFinite(b[k]) && b[k] > 0));
      return {
        v: ok ? (ratio ? r[k] / b[k] : r[k]) : null,
        resolved:
          ok && !r[k + 'Unresolved'] && (!ratio || !b[k + 'Unresolved']),
      };
    });
    const finite = points.filter((p) => p && Number.isFinite(p.v)),
      vals = finite.map((p) => p.v);
    return {
      mean:
        vals.length === seeds.length
          ? vals.reduce((a, b) => a + b, 0) / vals.length
          : null,
      min: vals.length ? Math.min(...vals) : null,
      max: vals.length ? Math.max(...vals) : null,
      resolved: points.every((p) => p && p.resolved),
      n: finite.length,
      total: seeds.length,
    };
  }
  function draw(canvas, f, k) {
    const width = Math.max(280, canvas.clientWidth),
      height = 240,
      dpr = devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);
    const sets = Object.keys(colors).map((p) => ({
      p,
      points: data.counts.map((c) => ({ c, ...sample(f, c, p, k) })),
    }));
    const ymax =
        Math.max(
          0.000001,
          ...sets.flatMap((s) => s.points.map((p) => p.max || 0)),
        ) * 1.12,
      L = 64,
      R = 16,
      T = 20,
      B = 43,
      w = width - L - R,
      h = height - T - B,
      x = (c) => L + (c / 24) * w,
      y = (v) => T + h - (v / ymax) * h;
    ctx.font = '10px system-ui';
    ctx.fillStyle = '#667168';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const v = (ymax * i) / 4;
      ctx.strokeStyle = '#dce3d8';
      ctx.beginPath();
      ctx.moveTo(L, y(v));
      ctx.lineTo(width - R, y(v));
      ctx.stroke();
      ctx.fillText(fmt(v), L - 7, y(v) + 3);
    }
    ctx.textAlign = 'center';
    for (const c of [0, 6, 12, 18, 24])
      ctx.fillText((c / 36).toFixed(2), x(c), height - 24);
    ctx.fillText('Added connectors / node', L + w / 2, height - 8);
    if ($('densityScale').value === 'ratio' && ymax >= 1) {
      ctx.setLineDash([3, 4]);
      ctx.strokeStyle = '#8b938a';
      ctx.beginPath();
      ctx.moveTo(L, y(1));
      ctx.lineTo(width - R, y(1));
      ctx.stroke();
      ctx.setLineDash([]);
    }
    for (const { p, points } of sets) {
      ctx.strokeStyle = colors[p];
      ctx.fillStyle = colors[p];
      ctx.lineWidth = 1.8;
      for (let i = 0; i < points.length; i++) {
        const q = points[i],
          prev = points[i - 1];
        if (!Number.isFinite(q.mean)) continue;
        if (q.resolved && prev?.resolved) {
          ctx.beginPath();
          ctx.moveTo(x(prev.c), y(prev.mean));
          ctx.lineTo(x(q.c), y(q.mean));
          ctx.stroke();
        }
        if (q.resolved && q.total > 1) {
          ctx.globalAlpha = 0.35;
          ctx.beginPath();
          ctx.moveTo(x(q.c), y(q.min));
          ctx.lineTo(x(q.c), y(q.max));
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
        ctx.beginPath();
        ctx.arc(x(q.c), y(q.mean), q.resolved ? 2.7 : 4, 0, 2 * Math.PI);
        ctx.fillStyle = q.resolved ? colors[p] : '#fafbf7';
        ctx.fill();
        ctx.stroke();
      }
    }
    canvas.setAttribute(
      'aria-label',
      `${names[f]}: ${labels[k]} versus connector density. Green distributed; purple clustered. Values and quality flags in the table below.`,
    );
  }
  const cards = $('densityPlots');
  for (const f of families) {
    const card = document.createElement('article');
    card.className = 'density-card';
    card.innerHTML = `<h3>${names[f]}</h3><div class="density-pair"><div><h4>Stiffness</h4><canvas id="density-${f}-k" role="img"></canvas></div><div><h4 class="densityMetricLabel"></h4><canvas id="density-${f}-w" role="img"></canvas></div></div>`;
    cards.append(card);
  }
  function render() {
    const metric = $('densityMetric').value,
      count = +$('densityCount').value,
      ratio = $('densityScale').value === 'ratio';
    $('densityAngleOut').textContent = $('densityAngle').value + '°';
    $('densityCountOut').textContent =
      `${count} (${(count / 36).toFixed(3)} / node)`;
    document
      .querySelectorAll('.densityMetricLabel')
      .forEach((e) => (e.textContent = labels[metric]));
    for (const f of families) {
      draw($('density-' + f + '-k'), f, 'stiffness');
      draw($('density-' + f + '-w'), f, metric);
    }
    const cell = (q) =>
      Number.isFinite(q.mean)
        ? `${fmt(q.mean)}${q.resolved ? '' : ' †'}${q.total > 1 ? ` <small>[${fmt(q.min)}, ${fmt(q.max)}]</small>` : ''}`
        : '— †';
    const rows = [];
    for (const f of families)
      for (const p of Object.keys(colors))
        rows.push(
          `<tr><th scope="row">${names[f]} · ${p}</th><td>${cell(sample(f, count, p, 'stiffness'))}</td><td>${cell(sample(f, count, p, 'work'))}</td><td>${cell(sample(f, count, p, 'failureStrain'))}</td><td>${cell(sample(f, count, p, 'workBeforeDamage'))}</td></tr>`,
        );
    $('densityTable').innerHTML =
      `<table><caption>Selected density: ${count} connectors / 36 nodes. ${ratio ? 'Paired ratios to the same seed at zero added connectors' : 'Dimensionless values'}. Brackets show seed range, not confidence intervals.</caption><thead><tr><th>Network · placement</th><th>Stiffness</th><th>Work to criterion</th><th>Failure strain</th><th>Work before damage</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
    $('densityStatus').textContent =
      `${data.rows.length.toLocaleString()} configurations · ${(data.rows.length * 2).toLocaleString()} solves · ${data.resolution.displayed} load steps displayed; checked against ${data.resolution.coarse}. ${ratio ? '1 = paired unmodified skeleton. A mean is the mean of individual seed ratios.' : 'All axes are dimensionless; scales differ between panels.'} Solid points require every selected seed to pass the metric-specific check. Hollow points and † are unresolved; do not rank them. Missing values are omitted.`;
  }
  for (const id of [
    'densityAngle',
    'densityCount',
    'densitySeed',
    'densityScale',
    'densityMetric',
  ])
    $(id).addEventListener('input', render);
  let timer;
  window.addEventListener('resize', () => {
    clearTimeout(timer);
    timer = setTimeout(render, 150);
  });
  render();
})();
