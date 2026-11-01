'use strict';
const $ = (id) => document.getElementById(id),
  NS = 'http://www.w3.org/2000/svg';
let atlas;
const text = (tag, value) => {
  const e = document.createElement(tag);
  e.textContent = value;
  return e;
};
function option(label, value) {
  const e = text('option', label);
  e.value = value;
  return e;
}
function svg(tag, attrs, value) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (value !== undefined) e.textContent = value;
  return e;
}
function selectedSuite() {
  return atlas.suites[Number($('suite').value)];
}
function showSuite() {
  const s = selectedSuite();
  $('question').textContent = s.question;
  $('plotTitle').textContent = s.title;
  $('limit').textContent = s.limit;
  $('case').replaceChildren();
  $('compare').replaceChildren(option('No comparison', ''));
  s.cases.forEach((c, i) => {
    $('case').append(option(c.label, String(i)));
    $('compare').append(option(c.label, String(i)));
  });
  $('case').value = String(s.defaultCase || 0);
  if (s.defaultCompare !== undefined)
    $('compare').value = String(s.defaultCompare);
  showCase();
}
function showCase() {
  const s = selectedSuite(),
    c = s.cases[Number($('case').value)],
    d = $('compare').value === '' ? null : s.cases[Number($('compare').value)];
  $('parameters').replaceChildren(
    ...Object.entries(c.parameters || {}).map(([k, v]) => {
      const e = text('div', k + ': ' + v);
      e.className = 'param';
      return e;
    }),
  );
  const valid = c.points.filter((p) => p.valid).length;
  $('validity').textContent =
    valid +
    ' / ' +
    c.points.length +
    ' eligible samples in the primary curve. Excluded states and unresolved derived values remain gaps; they are not zero response.';
  plot(s, c, d);
  table(s, c, d);
}
function plot(s, c, d) {
  const chart = $('chart');
  chart.replaceChildren();
  chart.append(svg('desc', { id: 'plotDesc' }, s.title + '. ' + s.limit));
  const all = [...c.points, ...(d ? d.points : [])].filter(
    (p) => p.valid && Number.isFinite(p.x) && Number.isFinite(p.y),
  );
  if (!all.length) {
    chart.append(
      svg(
        'text',
        { x: 450, y: 250, 'text-anchor': 'middle' },
        'No eligible samples for this selection',
      ),
    );
    return;
  }
  let xmin = Math.min(...all.map((p) => p.x)),
    xmax = Math.max(...all.map((p) => p.x)),
    ymin = Math.min(0, ...all.map((p) => p.y)),
    ymax = Math.max(...all.map((p) => p.y));
  if (xmax === xmin) xmax = xmin + 1;
  if (ymax === ymin) ymax = ymin + 1;
  const pad = (ymax - ymin) * 0.08;
  ymax += pad;
  ymin -= pad;
  const X = (x) => 85 + ((x - xmin) / (xmax - xmin)) * 760,
    Y = (y) => 445 - ((y - ymin) / (ymax - ymin)) * 390;
  for (let i = 0; i <= 5; i++) {
    const xv = xmin + ((xmax - xmin) * i) / 5,
      yv = ymin + ((ymax - ymin) * i) / 5;
    chart.append(
      svg('line', { x1: X(xv), x2: X(xv), y1: 55, y2: 445, class: 'gridline' }),
      svg('line', { x1: 85, x2: 845, y1: Y(yv), y2: Y(yv), class: 'gridline' }),
      svg(
        'text',
        { x: X(xv), y: 469, 'text-anchor': 'middle', 'font-size': 13 },
        fmt(xv),
      ),
      svg(
        'text',
        { x: 73, y: Y(yv) + 4, 'text-anchor': 'end', 'font-size': 13 },
        fmt(yv),
      ),
    );
  }
  chart.append(
    svg('line', { x1: 85, x2: 845, y1: 445, y2: 445, class: 'axis' }),
    svg('line', { x1: 85, x2: 85, y1: 55, y2: 445, class: 'axis' }),
    svg(
      'text',
      { x: 465, y: 510, 'text-anchor': 'middle', 'font-size': 15 },
      s.xLabel,
    ),
    svg(
      'text',
      {
        transform: 'translate(18,250) rotate(-90)',
        'text-anchor': 'middle',
        'font-size': 15,
      },
      s.yLabel,
    ),
  );
  for (const [item, color] of [
    [d, '#e56b42'],
    [c, '#007f86'],
  ]) {
    if (!item) continue;
    let path = '',
      open = false;
    for (const p of item.points) {
      if (!p.valid || !Number.isFinite(p.y)) {
        open = false;
        continue;
      }
      path += (open ? 'L' : 'M') + X(p.x) + ' ' + Y(p.y) + ' ';
      open = true;
      const dot = svg('circle', { cx: X(p.x), cy: Y(p.y), r: 3, fill: color });
      dot.append(
        svg(
          'title',
          {},
          item.label +
            ' | ' +
            s.xLabel +
            '=' +
            p.x +
            ' | ' +
            s.yLabel +
            '=' +
            p.y,
        ),
      );
      chart.append(dot);
    }
    chart.append(
      svg('path', {
        d: path,
        fill: 'none',
        stroke: color,
        'stroke-width': 2.2,
      }),
    );
  }
}
function fmt(x) {
  return Math.abs(x) >= 10000 || (Math.abs(x) < 0.001 && x !== 0)
    ? x.toExponential(2)
    : Number(x.toPrecision(4)).toString();
}
function table(s, c, d) {
  const tab = $('numbers'),
    head = document.createElement('tr');
  for (const h of ['Case', s.xLabel, s.yLabel, 'Eligible'])
    head.append(text('th', h));
  tab.replaceChildren(head);
  for (const [item, label] of [
    [c, 'Primary'],
    [d, 'Comparison'],
  ])
    if (item)
      for (const p of item.points) {
        const row = document.createElement('tr');
        for (const v of [label, p.x, p.y, p.valid ? 'yes' : 'no'])
          row.append(text('td', v === null ? 'unavailable' : String(v)));
        tab.append(row);
      }
}
async function load() {
  try {
    const r = await fetch('transition-view.json');
    if (!r.ok) throw Error('Run data unavailable');
    atlas = await r.json();
    $('runline').replaceChildren(
      ...atlas.badges.map((t) => {
        const e = text('span', t);
        e.className = 'pill';
        return e;
      }),
    );
    atlas.suites.forEach((s, i) =>
      $('suite').append(option(s.title, String(i))),
    );
    $('suite').addEventListener('change', showSuite);
    $('case').addEventListener('change', showCase);
    $('compare').addEventListener('change', showCase);
    for (const f of atlas.figures) {
      const fig = document.createElement('figure'),
        img = document.createElement('img');
      img.src = f.src;
      img.alt = f.alt;
      img.loading = 'lazy';
      fig.append(img, text('figcaption', f.caption));
      $('figures').append(fig);
    }
    for (const l of atlas.links) {
      const a = text('a', l.label);
      a.href = l.url;
      a.rel = 'noopener';
      $('links').append(a);
    }
    showSuite();
  } catch (e) {
    $('runline').textContent =
      'The verified run data could not be loaded. Please use the frozen dataset links in the repository; no substitute curves are shown.';
    console.error(e.message);
  }
}
load();
