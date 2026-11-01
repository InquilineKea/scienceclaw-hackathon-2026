(async () => {
  const r = await (await fetch('results.json')).json(),
    f = await (await fetch('fields.json')).json();
  document.querySelector('#verdict').textContent = r.verdict;
  document.querySelector('#table').innerHTML =
    '<table><tr><th>Predictor</th><th>Vector RMSE (µm)</th><th>Raw strain NRMSE</th><th>Averaged strain NRMSE</th></tr>' +
    r.test
      .map(
        x =>
          `<tr><td>${x.label}</td><td>${x.metrics.balanced_vector_RMSE_um.toFixed(3)}</td><td>${x.metrics.strain_Frobenius_NRMSE.toFixed(3)}</td><td>${x.support.strain_Frobenius_NRMSE.toFixed(3)}</td></tr>`
      )
      .join('') +
    '</table>';
  document.querySelector('#checks').textContent = r.controls_summary;
  let controls = await (await fetch('numerical-controls.json')).json();
  let detail = document.createElement('div');
  detail.innerHTML =
    '<table><tr><th>Independent refinement</th><th>Field L2 change</th><th>Error RMSE change</th><th>Work change</th></tr>' +
    [
      ['20 vs10 load steps', controls.step_change],
      ['302 vs110 directions', controls.angular_change]
    ]
      .map(
        ([name, x]) =>
          '<tr><td>' +
          name +
          '</td>' +
          ['prediction_field_relative_L2', 'prediction_RMSE_relative', 'work_relative']
            .map(k => '<td>' + (x ? (100 * x[k]).toPrecision(3) + '%' : 'Unavailable') + '</td>')
            .join('') +
          '</tr>'
      )
      .join('') +
    '</table><p>Required: every change ≤1%. These are surrogate numerical controls, not experimental uncertainty estimates.</p>';
  document.querySelector('#checks').append(detail);

  const $ = id => document.getElementById(id),
    select = $('model');
  let timer, inspector;

  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
      $('rotate').textContent = 'Rotate camera';
    }
  }

  const scoredNodes = [];
  for (let i = 0; i < f.nodes.length; i++) {
    if (f.score[i] && i % 10 === 0 && f.targets[i] && f.nodes[i]) scoredNodes.push(f.nodes[i]);
  }

  inspector = SpatialInspector.createController({
    mount: 'spatialInspector',
    canvases: ['canvas', 'predictionCanvas'],
    bounds: SpatialInspector.computeBounds(scoredNodes, [
      [-177, 177],
      [-177, 177],
      [-178.5, 178.5]
    ]),
    unit: 'µm',
    step: 1,
    digits: 1,
    axisLabelPrefix: 'Slice axis (µm)',
    sampleLabel: 'Inspect scored node',
    emptyReadout:
      'Click any displayed vector in either 3D pane (or choose a scored node above, or press [ / ] when a canvas is focused) to inspect saved observed, predicted, and residual vectors in µm. Selecting a node never recalculates or refits any model.',
    onChange: draw
  });

  const camera = SpatialCamera.create({
    yawInput: 'angle',
    pitchInput: 'pitch',
    zoomInput: 'zoom',
    statusElement: 'cameraStatus',
    resetButton: 'resetCamera',
    canvases: ['canvas', 'predictionCanvas'],
    onChange: draw,
    onManualInteract: stop
  });

  Object.keys(f.predictions).forEach(k => {
    let o = document.createElement('option');
    o.value = k;
    o.textContent = k;
    select.append(o);
  });
  select.value = 'combined';

  function pane(id, name, field, overlayObserved) {
    const canvas = $(id),
      c = canvas.getContext('2d'),
      W = canvas.width,
      H = canvas.height,
      project = q => camera.project(q, { width: W, height: H, scaleX: 0.83, scaleY: 0.8 });
    c.clearRect(0, 0, W, H);
    c.fillStyle = '#f8fafc';
    c.fillRect(0, 0, W, H);
    c.fillStyle = '#182c42';
    c.font = '18px system-ui';
    c.fillText(name, 20, 30);
    c.fillStyle = '#aab4bf';
    for (let q of f.cell_samples_um.filter((_, i) => i % 3 === 0)) {
      if (!inspector.inSlab(q)) continue;
      let [x, y] = project(q);
      c.fillRect(x, y, 2, 2);
    }

    let order = [];
    for (let i = 0; i < f.nodes.length; i++) {
      if (!f.score[i] || i % 10 || !field[i] || !f.nodes[i]) continue;
      let q = f.nodes[i];
      if (!inspector.inSlab(q)) continue;
      order.push({ i, q, u: field[i], depth: SpatialInspector.cameraDepth(camera, q) });
    }
    order.sort((a, b) => b.depth - a.depth);

    let pickTargets = [];
    let selectedGeom = null;

    for (let item of order) {
      let { i, q, u } = item,
        a = project(q);
      if (overlayObserved && f.targets[i]) {
        let uObs = f.targets[i],
          bObs = project(q.map((v, d) => v + 8 * uObs[d]));
        c.strokeStyle = '#0f766e';
        c.lineWidth = 1.4;
        c.setLineDash([]);
        c.beginPath();
        c.moveTo(...a);
        c.lineTo(...bObs);
        c.stroke();

        let bPred = project(q.map((v, d) => v + 8 * u[d]));
        c.strokeStyle = '#c2410c';
        c.lineWidth = 1.4;
        c.setLineDash([3, 2]);
        c.beginPath();
        c.moveTo(...a);
        c.lineTo(...bPred);
        c.stroke();
        c.setLineDash([]);
        pickTargets.push({ id: i, ax: a[0], ay: a[1], bx: bPred[0], by: bPred[1] });
        if (inspector.selectedId === i) selectedGeom = { a, b: bPred };
      } else {
        let b = project(q.map((v, d) => v + 8 * u[d])),
          mag = Math.hypot(...u),
          t = Math.min(1, mag / 8);
        c.strokeStyle = `hsl(${42 - 35 * t} 70% ${55 - 12 * t}%)`;
        c.lineWidth = 1.25;
        c.setLineDash([]);
        c.beginPath();
        c.moveTo(...a);
        c.lineTo(...b);
        c.stroke();
        pickTargets.push({ id: i, ax: a[0], ay: a[1], bx: b[0], by: b[1] });
        if (inspector.selectedId === i) selectedGeom = { a, b };
      }
    }

    if (selectedGeom) {
      SpatialInspector.drawSelectedMarker(c, selectedGeom.a, selectedGeom.b, '#0f172a');
    }
    inspector.setPickTargets(id, pickTargets);
    camera.drawAxes(c, W, H);
    c.fillStyle = '#536376';
    c.font = '13px system-ui';
    c.fillText(`Same score mask · ${order.length} in slab · displacement ×8 · positions µm`, 15, H - 18);
  }

  function updateInspector(predKey, predVectors) {
    let items = [];
    for (let i = 0; i < f.nodes.length; i++) {
      if (!f.score[i] || i % 10 || !f.targets[i] || !predVectors[i] || !f.nodes[i]) continue;
      let q = f.nodes[i];
      if (!inspector.inSlab(q)) continue;
      items.push({
        id: i,
        label: `Node #${i}: (${q[0].toFixed(1)}, ${q[1].toFixed(1)}, ${q[2].toFixed(1)}) µm`
      });
    }
    inspector.setItems(items, `None selected (${items.length} displayed scored nodes in slab)`);

    let idx = inspector.selectedId;
    if (idx === null || !f.score[idx] || idx % 10 || !f.targets[idx] || !predVectors[idx] || !f.nodes[idx]) {
      inspector.setReadout(
        '<strong>No scored node selected.</strong> Click a displayed vector in either 3D canvas or choose a node above (keyboard: <code>[</code> / <code>]</code> on a focused canvas). Null vectors outside the score mask are safely skipped.'
      );
      return;
    }
    let q = f.nodes[idx],
      uObs = f.targets[idx],
      uPred = predVectors[idx],
      uRes = uPred.map((v, d) => v - uObs[d]),
      inSlab = inspector.inSlab(q);
    inspector.setReadout(
      `<strong>Selected mesh node #${idx}</strong> (score-masked sample${inSlab ? '' : ' · currently outside active slice'}) · Predictor: <strong>${predKey}</strong>` +
        `<div class="spatial-readout-grid">` +
        `<div><span>Saved position (x, y, z):</span> <code>${SpatialInspector.fmtVec(q, 2, 'µm')}</code></div>` +
        `<div><span>Observed PIV u_obs:</span> <code>${SpatialInspector.fmtVec(uObs, 3, 'µm')}</code> · ||u_obs|| = <strong>${SpatialInspector.fmt(SpatialInspector.norm3(uObs), 3)} µm</strong></div>` +
        `<div><span>Predicted u_pred:</span> <code>${SpatialInspector.fmtVec(uPred, 3, 'µm')}</code> · ||u_pred|| = <strong>${SpatialInspector.fmt(SpatialInspector.norm3(uPred), 3)} µm</strong></div>` +
        `<div><span>Residual (u_pred − u_obs):</span> <code>${SpatialInspector.fmtVec(uRes, 3, 'µm')}</code> · ||u_pred − u_obs|| = <strong>${SpatialInspector.fmt(SpatialInspector.norm3(uRes), 3)} µm</strong></div>` +
        `</div>`
    );
  }

  function draw() {
    let mode = $('fieldMode').value,
      residual = mode === 'residual',
      overlay = mode === 'overlay',
      rawPred = f.predictions[select.value];
    if (!rawPred) return;
    let vectors = rawPred;
    if (residual)
      vectors = rawPred.map((u, i) => (u && f.targets[i] ? u.map((v, k) => v - f.targets[i][k]) : null));
    inspector.setLegend(
      '<span><i class="spatial-swatch spatial-swatch-observed"></i>Observed PIV (solid teal)</span>' +
        '<span><i class="spatial-swatch spatial-swatch-predicted"></i>Predicted (dashed orange)</span>' +
        '<span><i class="spatial-swatch spatial-swatch-selected"></i>Selected node marker</span>',
      overlay
    );
    pane('canvas', 'Observed PIV', f.targets, false);
    pane(
      'predictionCanvas',
      residual
        ? 'Residual: predicted − observed'
        : overlay
        ? 'Overlay: Observed + ' + select.value
        : select.value,
      vectors,
      overlay
    );
    updateInspector(select.value, rawPred);
  }

  select.onchange = $('fieldMode').onchange = draw;
  $('rotate').onclick = () => {
    if (timer) stop();
    else {
      timer = setInterval(() => camera.stepYaw(2), 80);
      $('rotate').textContent = 'Pause camera';
    }
  };
  SpatialCamera.bindPauseOnHidden(stop);
  draw();
})().catch(e => {
  document.querySelector('#verdict').textContent = 'Could not load saved results: ' + e.message;
});
