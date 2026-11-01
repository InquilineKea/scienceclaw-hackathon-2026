'use strict';
const $ = (id) => document.getElementById(id),
  NS = 'http://www.w3.org/2000/svg';
let atlas,
  selectedIndex = 0;

const text = (tag, value, className) => {
  const e = document.createElement(tag);
  e.textContent = value;
  if (className) e.className = className;
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
function fmt(x) {
  if (x === null || x === undefined || !Number.isFinite(Number(x)))
    return 'unavailable';
  const n = Number(x);
  return Math.abs(n) >= 10000 || (Math.abs(n) < 0.001 && n !== 0)
    ? n.toExponential(3)
    : Number(n.toPrecision(5)).toString();
}
function fmtExact(x) {
  if (x === null || x === undefined || !Number.isFinite(Number(x)))
    return 'unavailable (excluded / unconverged)';
  return String(x);
}
function selectedSuite() {
  return atlas.suites[Number($('suite').value)];
}
function currentCases() {
  const s = selectedSuite(),
    c = s.cases[Number($('case').value)],
    d = $('compare').value === '' ? null : s.cases[Number($('compare').value)];
  return { s, c, d };
}
function findComparisonMatch(points, targetX) {
  if (!points || !points.length || !Number.isFinite(targetX)) return null;
  let best = null,
    bestIdx = -1,
    bestDx = Infinity;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (!Number.isFinite(p.x)) continue;
    const dx = Math.abs(p.x - targetX);
    if (dx < bestDx) {
      bestDx = dx;
      best = p;
      bestIdx = i;
    }
  }
  if (!best) return null;
  return {
    point: best,
    index: bestIdx,
    deltaX: best.x - targetX,
    absDeltaX: bestDx,
    exact: bestDx <= 1e-12,
  };
}
function syncUrlState() {
  if (!window.history || !window.history.replaceState) return;
  const params = new URLSearchParams(window.location.search);
  params.set('suite', $('suite').value);
  params.set('case', $('case').value);
  if ($('compare').value !== '') params.set('compare', $('compare').value);
  else params.delete('compare');
  params.set('sample', String(selectedIndex));
  const newUrl = window.location.pathname + '?' + params.toString() + window.location.hash;
  window.history.replaceState(null, '', newUrl);
}
function applyInitialUrlState() {
  const params = new URLSearchParams(window.location.search);
  const suiteParam = params.get('suite');
  if (suiteParam !== null) {
    const idx = atlas.suites.findIndex(
      (s, i) => String(i) === suiteParam || s.id === suiteParam,
    );
    if (idx >= 0) $('suite').value = String(idx);
  }
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
  const caseParam = params.get('case');
  if (
    caseParam !== null &&
    Number.isInteger(Number(caseParam)) &&
    Number(caseParam) >= 0 &&
    Number(caseParam) < s.cases.length
  ) {
    $('case').value = String(Number(caseParam));
  } else {
    $('case').value = String(s.defaultCase || 0);
  }
  const compareParam = params.get('compare');
  if (
    compareParam !== null &&
    compareParam !== '' &&
    Number.isInteger(Number(compareParam)) &&
    Number(compareParam) >= 0 &&
    Number(compareParam) < s.cases.length
  ) {
    $('compare').value = String(Number(compareParam));
  } else if (s.defaultCompare !== undefined) {
    $('compare').value = String(s.defaultCompare);
  }
  const c = s.cases[Number($('case').value)];
  const sampleParam = params.get('sample');
  if (
    sampleParam !== null &&
    Number.isInteger(Number(sampleParam)) &&
    Number(sampleParam) >= 0 &&
    Number(sampleParam) < c.points.length
  ) {
    selectedIndex = Number(sampleParam);
  } else {
    const firstValid = c.points.findIndex((p) => p.valid && Number.isFinite(p.y));
    selectedIndex = firstValid >= 0 ? firstValid : 0;
  }
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
  const c = s.cases[Number($('case').value)];
  const firstValid = c.points.findIndex((p) => p.valid && Number.isFinite(p.y));
  selectedIndex = firstValid >= 0 ? firstValid : 0;
  showCase(true);
}
function showCase(keepSampleIndex) {
  const { s, c, d } = currentCases();
  if (!keepSampleIndex) {
    if (selectedIndex >= c.points.length) {
      selectedIndex = Math.max(0, c.points.length - 1);
    }
  }
  $('parameters').replaceChildren(
    ...Object.entries(c.parameters || {}).map(([k, v]) => {
      const e = text('div', k + ': ' + v, 'param');
      return e;
    }),
  );
  const valid = c.points.filter((p) => p.valid && Number.isFinite(p.y)).length;
  $('validity').textContent =
    valid +
    ' / ' +
    c.points.length +
    ' eligible samples in the primary curve. Excluded states and unresolved derived values remain gaps; they are not zero response.';

  const slider = $('sampleIndex');
  if (slider) {
    const maxIdx = Math.max(0, c.points.length - 1);
    slider.max = String(maxIdx);
    if (selectedIndex > maxIdx) selectedIndex = maxIdx;
    slider.value = String(selectedIndex);
    slider.disabled = c.points.length <= 1;
  }
  renderSelection();
  syncUrlState();
}
function selectSample(idx) {
  const { c } = currentCases();
  if (!c || !c.points.length) return;
  const clamped = Math.max(0, Math.min(c.points.length - 1, Number(idx)));
  selectedIndex = clamped;
  const slider = $('sampleIndex');
  if (slider) slider.value = String(selectedIndex);
  renderSelection();
  syncUrlState();
}
function renderSelection() {
  const { s, c, d } = currentCases();
  plot(s, c, d);
  updateInspector(s, c, d);
  table(s, c, d);
}
function formatParamList(params) {
  const entries = Object.entries(params || {});
  if (!entries.length) return 'none declared';
  return entries.map(([k, v]) => k + '=' + v).join(' · ');
}
function updateInspector(s, c, d) {
  const total = c.points.length;
  const p = c.points[selectedIndex] || null;
  const out = $('sampleIndexOut');
  if (out) {
    out.textContent =
      total > 0
        ? 'Sample ' +
          (selectedIndex + 1) +
          ' of ' +
          total +
          (p ? ' (' + s.xLabel + ' = ' + fmt(p.x) + ')' : '')
        : 'No samples';
  }
  const prevBtn = $('samplePrev'),
    nextBtn = $('sampleNext');
  if (prevBtn) prevBtn.disabled = selectedIndex <= 0;
  if (nextBtn) nextBtn.disabled = selectedIndex >= total - 1;

  const readout = $('sampleReadout');
  if (!readout) return;
  readout.replaceChildren();
  if (!p) {
    readout.append(text('p', 'No saved sample available for this selection.'));
    return;
  }

  const cards = document.createElement('div');
  cards.className = 'sample-cards';

  const primaryCard = document.createElement('div');
  primaryCard.className = 'sample-card primary-card';
  const pHead = document.createElement('div');
  pHead.className = 'sample-card-head';
  pHead.append(
    text('strong', 'Primary sample #' + (selectedIndex + 1) + ' · ' + c.label),
    text(
      'span',
      p.valid && Number.isFinite(p.y)
        ? 'Eligible equilibrium'
        : 'Excluded / gap (not zero)',
      p.valid && Number.isFinite(p.y)
        ? 'status-pill valid'
        : 'status-pill invalid',
    ),
  );
  const pList = document.createElement('dl');
  pList.className = 'sample-dl';
  const addRow = (dl, dtText, ddText) => {
    dl.append(text('dt', dtText), text('dd', ddText));
  };
  addRow(pList, s.xLabel, fmtExact(p.x));
  addRow(
    pList,
    s.yLabel,
    p.valid && Number.isFinite(p.y)
      ? fmtExact(p.y)
      : 'unavailable — excluded state or unresolved derivative',
  );
  addRow(pList, 'Case parameters', formatParamList(c.parameters));
  primaryCard.append(pHead, pList);
  cards.append(primaryCard);

  const compCard = document.createElement('div');
  compCard.className = 'sample-card compare-card';
  if (!d) {
    compCard.append(
      text('strong', 'Comparison case'),
      text(
        'p',
        'No comparison curve selected. Choose a second case in the controls to compare at matched or nearest saved ' +
          s.xLabel +
          ' without interpolating across gaps.',
        'sample-note',
      ),
    );
  } else {
    const match = findComparisonMatch(d.points, p.x);
    const cHead = document.createElement('div');
    cHead.className = 'sample-card-head';
    if (!match) {
      cHead.append(text('strong', 'Comparison · ' + d.label));
      compCard.append(
        cHead,
        text('p', 'No saved comparison points available.', 'sample-note'),
      );
    } else {
      const cp = match.point;
      const cpValid = cp.valid && Number.isFinite(cp.y);
      cHead.append(
        text(
          'strong',
          'Comparison sample #' + (match.index + 1) + ' · ' + d.label,
        ),
        text(
          'span',
          match.exact
            ? 'Exact saved x match (Δx = 0)'
            : 'Nearest saved x (Δx = ' + fmt(match.deltaX) + ')',
          match.exact ? 'status-pill match-exact' : 'status-pill match-nearest',
        ),
      );
      const cList = document.createElement('dl');
      cList.className = 'sample-dl';
      addRow(
        cList,
        'Matched ' + s.xLabel,
        fmtExact(cp.x) +
          (match.exact
            ? ' (exact match to primary)'
            : ' (Δx = ' +
              fmtExact(match.deltaX) +
              ' vs primary ' +
              fmtExact(p.x) +
              '; no interpolation)'),
      );
      addRow(
        cList,
        s.yLabel,
        cpValid
          ? fmtExact(cp.y)
          : 'unavailable — excluded state or unresolved derivative (no interpolation across gaps)',
      );
      if (p.valid && Number.isFinite(p.y) && cpValid) {
        const dy = cp.y - p.y;
        addRow(
          cList,
          'Difference (comparison − primary)',
          fmtExact(dy) +
            (match.exact
              ? ' at identical saved ' + s.xLabel
              : ' (caution: compared at nearest saved ' +
                s.xLabel +
                ', Δx = ' +
                fmt(match.deltaX) +
                ')'),
        );
      } else {
        addRow(
          cList,
          'Difference (comparison − primary)',
          'not computed (requires both saved samples to be eligible)',
        );
      }
      addRow(cList, 'Case parameters', formatParamList(d.parameters));
      compCard.append(cHead, cList);
    }
  }
  cards.append(compCard);
  readout.append(cards);
}
function plot(s, c, d) {
  const chart = $('chart');
  chart.replaceChildren();
  chart.append(svg('desc', { id: 'plotDesc' }, s.title + '. ' + s.limit));
  const allX = [...c.points, ...(d ? d.points : [])].filter((p) =>
    Number.isFinite(p.x),
  );
  const allValid = [...c.points, ...(d ? d.points : [])].filter(
    (p) => p.valid && Number.isFinite(p.x) && Number.isFinite(p.y),
  );
  if (!allX.length) {
    chart.append(
      svg(
        'text',
        { x: 450, y: 250, 'text-anchor': 'middle' },
        'No saved samples for this selection',
      ),
    );
    return;
  }
  let xmin = Math.min(...allX.map((p) => p.x)),
    xmax = Math.max(...allX.map((p) => p.x)),
    ymin = allValid.length ? Math.min(0, ...allValid.map((p) => p.y)) : 0,
    ymax = allValid.length ? Math.max(...allValid.map((p) => p.y)) : 1;
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
  if (!allValid.length) {
    chart.append(
      svg(
        'text',
        { x: 465, y: 235, 'text-anchor': 'middle', 'font-size': 14 },
        'All saved samples in this selection are excluded / unresolved (shown on axis below).',
      ),
    );
  }

  const selPrimary = c.points[selectedIndex] || null;
  const selCompMatch =
    d && selPrimary ? findComparisonMatch(d.points, selPrimary.x) : null;

  if (selPrimary && Number.isFinite(selPrimary.x)) {
    const sx = X(selPrimary.x);
    chart.append(
      svg('line', {
        x1: sx,
        x2: sx,
        y1: 55,
        y2: 445,
        class: 'cursor-line',
      }),
    );
    if (selCompMatch && !selCompMatch.exact && Number.isFinite(selCompMatch.point.x)) {
      const cx = X(selCompMatch.point.x);
      chart.append(
        svg('line', {
          x1: cx,
          x2: cx,
          y1: 55,
          y2: 445,
          class: 'cursor-line-compare',
        }),
      );
    }
  }

  for (const [item, color, isPrimary] of [
    [d, '#e56b42', false],
    [c, '#007f86', true],
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
    }
    if (path) {
      chart.append(
        svg('path', {
          d: path,
          fill: 'none',
          stroke: color,
          'stroke-width': 2.2,
        }),
      );
    }
    item.points.forEach((p, idx) => {
      if (!Number.isFinite(p.x)) return;
      const px = X(p.x);
      const isSelected = isPrimary
        ? idx === selectedIndex
        : Boolean(selCompMatch && idx === selCompMatch.index);
      if (!p.valid || !Number.isFinite(p.y)) {
        const gy = 445;
        const gMarker = svg('circle', {
          cx: px,
          cy: gy,
          r: isSelected ? 6.5 : 4,
          fill: '#f5f3ed',
          stroke: color,
          'stroke-width': isSelected ? 2.6 : 1.6,
          'stroke-dasharray': '2,2',
          class: 'sample-point invalid-point',
          tabindex: isPrimary ? '0' : '-1',
          role: 'button',
          'aria-label':
            (isPrimary ? 'Primary' : 'Comparison') +
            ' sample ' +
            (idx + 1) +
            ': ' +
            s.xLabel +
            ' ' +
            fmt(p.x) +
            ', excluded or unresolved gap',
        });
        gMarker.append(
          svg(
            'title',
            {},
            item.label +
              ' | ' +
              s.xLabel +
              '=' +
              p.x +
              ' | excluded / unresolved gap (click to inspect)',
          ),
        );
        const onPick = () => {
          if (isPrimary) {
            selectSample(idx);
          } else {
            const matchPrimary = findComparisonMatch(c.points, p.x);
            if (matchPrimary) selectSample(matchPrimary.index);
          }
        };
        gMarker.addEventListener('click', onPick);
        gMarker.addEventListener('keydown', (ev) => {
          if (ev.key === 'Enter' || ev.key === ' ') {
            ev.preventDefault();
            onPick();
          }
        });
        chart.append(gMarker);
        return;
      }
      const py = Y(p.y);
      if (isSelected) {
        chart.append(
          svg('circle', {
            cx: px,
            cy: py,
            r: 8.5,
            fill: 'none',
            stroke: color,
            'stroke-width': 2,
            class: 'selected-halo',
          }),
        );
      }
      const dot = svg('circle', {
        cx: px,
        cy: py,
        r: isSelected ? 5.5 : 3.8,
        fill: color,
        stroke: '#ffffff',
        'stroke-width': isSelected ? 1.8 : 1,
        class: 'sample-point',
        tabindex: isPrimary ? '0' : '-1',
        role: 'button',
        'aria-label':
          (isPrimary ? 'Primary' : 'Comparison') +
          ' sample ' +
          (idx + 1) +
          ': ' +
          s.xLabel +
          ' ' +
          fmt(p.x) +
          ', ' +
          s.yLabel +
          ' ' +
          fmt(p.y),
      });
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
            p.y +
            ' (click to inspect)',
        ),
      );
      const onPick = () => {
        if (isPrimary) {
          selectSample(idx);
        } else {
          const matchPrimary = findComparisonMatch(c.points, p.x);
          if (matchPrimary) selectSample(matchPrimary.index);
        }
      };
      dot.addEventListener('click', onPick);
      dot.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          onPick();
        } else if (ev.key === 'ArrowRight' || ev.key === 'ArrowUp') {
          ev.preventDefault();
          selectSample(selectedIndex + 1);
        } else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowDown') {
          ev.preventDefault();
          selectSample(selectedIndex - 1);
        }
      });
      chart.append(dot);
    });
  }
}
function table(s, c, d) {
  const tab = $('numbers'),
    head = document.createElement('tr');
  for (const h of ['Case', 'Sample #', s.xLabel, s.yLabel, 'Eligible'])
    head.append(text('th', h));
  tab.replaceChildren(head);
  const selPrimary = c.points[selectedIndex] || null;
  const selCompMatch =
    d && selPrimary ? findComparisonMatch(d.points, selPrimary.x) : null;
  for (const [item, label, isPrimary] of [
    [c, 'Primary', true],
    [d, 'Comparison', false],
  ])
    if (item)
      item.points.forEach((p, idx) => {
        const row = document.createElement('tr');
        const isSel = isPrimary
          ? idx === selectedIndex
          : Boolean(selCompMatch && idx === selCompMatch.index);
        if (isSel) row.className = 'selected-row';
        for (const v of [
          label,
          idx + 1,
          p.x,
          p.y,
          p.valid && Number.isFinite(p.y) ? 'yes' : 'no',
        ])
          row.append(text('td', v === null ? 'unavailable' : String(v)));
        row.addEventListener('click', () => {
          if (isPrimary) selectSample(idx);
          else {
            const m = findComparisonMatch(c.points, p.x);
            if (m) selectSample(m.index);
          }
        });
        tab.append(row);
      });
}
async function load() {
  try {
    const r = await fetch('transition-view.json');
    if (!r.ok) throw Error('Run data unavailable');
    atlas = await r.json();
    $('runline').replaceChildren(
      ...atlas.badges.map((t) => {
        const e = text('span', t, 'pill');
        return e;
      }),
    );
    atlas.suites.forEach((s, i) =>
      $('suite').append(option(s.title, String(i))),
    );
    $('suite').addEventListener('change', showSuite);
    $('case').addEventListener('change', () => showCase(false));
    $('compare').addEventListener('change', () => showCase(true));
    const slider = $('sampleIndex'),
      prevBtn = $('samplePrev'),
      nextBtn = $('sampleNext');
    if (slider) {
      slider.addEventListener('input', () => selectSample(Number(slider.value)));
    }
    if (prevBtn) {
      prevBtn.addEventListener('click', () => selectSample(selectedIndex - 1));
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', () => selectSample(selectedIndex + 1));
    }
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
    applyInitialUrlState();
    showCase(true);
  } catch (e) {
    $('runline').textContent =
      'The verified run data could not be loaded. Please use the frozen dataset links in the repository; no substitute curves are shown.';
    console.error(e.message);
  }
}
load();
