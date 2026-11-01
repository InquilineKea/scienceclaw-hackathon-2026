'use strict';
let DATA, timer, inspector;
const $ = id => document.getElementById(id),
  fmt = (x, n = 3) => (Number.isFinite(x) ? x.toFixed(n) : 'unavailable');
const camera = SpatialCamera.create({
  yawInput: 'rotation',
  pitchInput: 'pitch',
  zoomInput: 'zoom',
  statusElement: 'cameraStatus',
  resetButton: 'resetCamera',
  canvases: ['observed', 'predicted'],
  defaultYaw: 28,
  defaultPitch: 28,
  onChange: () => DATA && render(),
  onManualInteract: () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
      $('rotate').textContent = 'Rotate camera';
    }
  }
});

inspector = SpatialInspector.createController({
  mount: 'spatialInspector',
  canvases: ['observed', 'predicted'],
  bounds: [
    [-177, 177],
    [-177, 177],
    [-178.5, 178.5]
  ],
  unit: 'µm',
  step: 1,
  digits: 1,
  axisLabelPrefix: 'Slice axis (µm)',
  sampleLabel: 'Inspect guarded sample',
  emptyReadout:
    'Click any displayed displacement vector in either 3D pane (or choose a guarded sample above, or press [ / ] when a canvas is focused) to inspect saved observed, predicted, and residual vectors in µm. Selecting a node inspects saved arrays only and never refits a model.',
  onChange: () => DATA && render()
});

for (let b of document.querySelectorAll('[data-tab]'))
  b.onclick = () => {
    for (let t of document.querySelectorAll('[data-tab]')) t.setAttribute('aria-selected', String(t === b));
    for (let s of document.querySelectorAll('main>section')) s.hidden = s.id !== b.dataset.tab;
    if (DATA) render();
  };
for (let id of ['model', 'rotation', 'scale']) $(id).oninput = () => DATA && render();
$('rotate').onclick = () => {
  if (timer) {
    clearInterval(timer);
    timer = null;
    $('rotate').textContent = 'Rotate camera';
  } else {
    timer = setInterval(() => {
      camera.stepYaw(2);
    }, 120);
    $('rotate').textContent = 'Stop rotation';
  }
};

function vectorStroke(mag) {
  let v = Math.min(1, mag / 8);
  return `rgb(${Math.round(190 + 65 * v)},${Math.round(150 - 105 * v)},${Math.round(65 - 35 * v)})`;
}

function draw(id, field, overlayObserved) {
  let canvas = $(id),
    c = canvas.getContext('2d'),
    W = canvas.width,
    H = canvas.height,
    scale = Number($('scale').value),
    f = DATA.field;
  let project = q => camera.project(q, { width: W, height: H, scaleX: 0.9, scaleY: 0.86 });
  c.clearRect(0, 0, W, H);
  c.fillStyle = '#f8fafc';
  c.fillRect(0, 0, W, H);
  c.strokeStyle = '#acbccb';
  c.lineWidth = 1;
  for (let i = 0; i < 8; i++)
    for (let d = 0; d < 3; d++)
      if (!(i >> d & 1)) {
        let j = i | (1 << d),
          p = project([0, 1, 2].map(k => (i >> k & 1 ? 1 : -1) * 177)),
          q = project([0, 1, 2].map(k => (j >> k & 1 ? 1 : -1) * 177));
        c.beginPath();
        c.moveTo(...p);
        c.lineTo(...q);
        c.stroke();
      }
  c.fillStyle = '#9ba6b0';
  for (let q of f.cell_samples_um.filter((_, i) => i % 3 === 0)) {
    if (!inspector.inSlab(q)) continue;
    let [x, y] = project(q);
    c.fillRect(x, y, 1.8, 1.8);
  }

  let order = [];
  for (let k = 0; k < f.nodes.length; k++) {
    let q = f.nodes[k],
      u = field[k];
    if (!q || !u || !inspector.inSlab(q)) continue;
    order.push({ k, q, u, depth: SpatialInspector.cameraDepth(camera, q) });
  }
  order.sort((a, b) => b.depth - a.depth);

  let pickTargets = [];
  let selectedGeom = null;

  for (let item of order) {
    let { k, q, u } = item,
      p = project(q);
    if (overlayObserved && f.observed[k]) {
      let uObs = f.observed[k],
        rObs = project(q.map((v, d) => v + scale * uObs[d]));
      c.strokeStyle = '#0f766e';
      c.lineWidth = 1.35;
      c.setLineDash([]);
      SpatialInspector.drawArrow2D(c, p, rObs, 3, 2);

      let rPred = project(q.map((v, d) => v + scale * u[d]));
      c.strokeStyle = '#c2410c';
      c.lineWidth = 1.35;
      c.setLineDash([3, 2]);
      SpatialInspector.drawArrow2D(c, p, rPred, 3, 2);
      c.setLineDash([]);
      pickTargets.push({ id: k, ax: p[0], ay: p[1], bx: rPred[0], by: rPred[1] });
      if (inspector.selectedId === k) selectedGeom = { p, r: rPred };
    } else {
      let r = project(q.map((v, d) => v + scale * u[d])),
        mag = Math.hypot(...u);
      c.strokeStyle = vectorStroke(mag);
      c.lineWidth = 1.2;
      c.setLineDash([]);
      SpatialInspector.drawArrow2D(c, p, r, 3, 2);
      pickTargets.push({ id: k, ax: p[0], ay: p[1], bx: r[0], by: r[1] });
      if (inspector.selectedId === k) selectedGeom = { p, r };
    }
  }

  if (selectedGeom) {
    SpatialInspector.drawSelectedMarker(c, selectedGeom.p, selectedGeom.r, '#0f172a');
  }
  inspector.setPickTargets(id, pickTargets);
  c.fillStyle = '#173047';
  c.font = '14px system-ui';
  c.fillText('Positions µm · arrows magnified ×' + scale, 14, H - 16);
  camera.drawAxes(c, W, H);
  return order.length;
}

function updateInspectorState(name, label) {
  let f = DATA.field,
    predField = f.predictions[name],
    items = [];
  for (let k = 0; k < f.nodes.length; k++) {
    let q = f.nodes[k];
    if (!q || !inspector.inSlab(q)) continue;
    items.push({
      id: k,
      label: `Sample #${k}: (${q[0].toFixed(1)}, ${q[1].toFixed(1)}, ${q[2].toFixed(1)}) µm`
    });
  }
  inspector.setItems(items, `None selected (${items.length} of ${f.nodes.length} displayed in slab)`);

  let k = inspector.selectedId;
  if (k === null || k < 0 || k >= f.nodes.length || !f.nodes[k]) {
    inspector.setReadout(
      '<strong>No sample selected.</strong> Click a vector in either 3D canvas or select a guarded sample above (keyboard: <code>[</code> / <code>]</code> on a focused canvas). Values report saved vectors in µm; residuals are prediction differences, not uncertainty.'
    );
    return;
  }
  let q = f.nodes[k],
    uObs = f.observed[k],
    uPred = predField[k],
    uRes = uPred.map((v, d) => v - uObs[d]),
    inCurrentSlab = inspector.inSlab(q);
  inspector.setReadout(
    `<strong>Selected displayed sample #${k}</strong> (saved thinned index <code>${k}</code>${inCurrentSlab ? '' : ' · currently outside active slice'}) · Predictor: <strong>${label}</strong>` +
      `<div class="spatial-readout-grid">` +
      `<div><span>Saved position (x, y, z):</span> <code>${SpatialInspector.fmtVec(q, 2, 'µm')}</code></div>` +
      `<div><span>Observed u_obs:</span> <code>${SpatialInspector.fmtVec(uObs, 3, 'µm')}</code> · ||u_obs|| = <strong>${fmt(SpatialInspector.norm3(uObs), 3)} µm</strong></div>` +
      `<div><span>Predicted u_pred:</span> <code>${SpatialInspector.fmtVec(uPred, 3, 'µm')}</code> · ||u_pred|| = <strong>${fmt(SpatialInspector.norm3(uPred), 3)} µm</strong></div>` +
      `<div><span>Residual (u_pred − u_obs):</span> <code>${SpatialInspector.fmtVec(uRes, 3, 'µm')}</code> · ||u_pred − u_obs|| = <strong>${fmt(SpatialInspector.norm3(uRes), 3)} µm</strong></div>` +
      `</div>`
  );
}

function render() {
  if (!DATA) return;
  let name = $('model').value,
    mode = $('fieldMode').value,
    labels = {
      elastic_nu_0: 'Selected isotropic elasticity, ν=0',
      harmonic_interpolation: 'Harmonic interpolation',
      affine_boundary_fit: 'Affine boundary fit',
      zero: 'Zero centered displacement'
    };
  let visibleCount = draw('observed', DATA.field.observed, false);
  let vectors = DATA.field.predictions[name],
    residual = mode === 'residual',
    overlay = mode === 'overlay';
  if (residual) vectors = vectors.map((u, i) => u.map((v, k) => v - DATA.field.observed[i][k]));
  draw('predicted', vectors, overlay);
  inspector.setLegend(
    '<span><i class="spatial-swatch spatial-swatch-observed"></i>Observed PIV displacement (solid teal)</span>' +
      '<span><i class="spatial-swatch spatial-swatch-predicted"></i>Predicted displacement (dashed orange)</span>' +
      '<span><i class="spatial-swatch spatial-swatch-selected"></i>Selected node marker</span>',
    overlay
  );
  $('modelTitle').textContent = residual
    ? 'Residual: predicted − observed'
    : overlay
    ? 'Overlay: observed (teal) + ' + labels[name] + ' (dashed orange)'
    : labels[name];
  updateInspectorState(name, labels[name]);
  $('viewInfo').textContent = `Position008 · ${visibleCount} in view of ${DATA.field.nodes.length} displayed (${4355} valid guarded test vectors) · same known-boundary inputs · rotation ${$('rotation').value}°.`;
}

fetch('report-data.json')
  .then(r => {
    if (!r.ok) throw Error('Saved benchmark data unavailable');
    return r.json();
  })
  .then(d => {
    DATA = d;
    inspector.setBounds(SpatialInspector.computeBounds(d.field.nodes, [[-177, 177], [-177, 177], [-178.5, 178.5]]));
    $('status').textContent = 'Saved final-test results loaded. No fitting or test-set tuning runs in your browser.';
    $('rotate').disabled = false;
    $('sourceLink').href = d.source_url;
    $('bulkTable').innerHTML =
      '<table><thead><tr><th>Held-out C concentration</th><th>Selected nonlinear NRMSE</th><th>Linear NRMSE</th><th>Stress bias (Pa)</th></tr></thead><tbody>' +
      [0.6, 1.2, 2.4]
        .map(
          c =>
            `<tr><td>${c} mg/mL</td><td>${fmt(d.bulk.test[c].NRMSE)}</td><td>${fmt(d.bulk.linear_test[c].NRMSE)}</td><td>${fmt(d.bulk.test[c].mean_bias_Pa, 2)}</td></tr>`
        )
        .join('') +
      '</tbody></table>';
    $('spatialTable').innerHTML =
      '<table><thead><tr><th>Predictor</th><th>Displacement RMSE (µm)</th><th>Displacement NRMSE</th><th>Raw P1 strain NRMSE</th></tr></thead><tbody>' +
      d.spatial.results
        .map(
          r =>
            `<tr><td>${r.name}</td><td>${fmt(r.metrics.balanced_vector_RMSE_um)}</td><td>${fmt(r.metrics.balanced_vector_NRMSE)}</td><td>${fmt(r.metrics.strain_Frobenius_NRMSE)}</td></tr>`
        )
        .join('') +
      '</tbody></table>';
    render();
  })
  .catch(e => {
    $('status').textContent = e.message;
    console.error(e);
  });

$('fieldMode').onchange = () => DATA && render();
SpatialCamera.bindPauseOnHidden(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
    $('rotate').textContent = 'Rotate camera';
  }
});
