'use strict';
(function (global) {
  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  function fmt(v, n) {
    const digits = n !== undefined ? n : 3;
    return Number.isFinite(v) ? Number(v).toFixed(digits) : 'unavailable';
  }

  function fmtVec(vec, n, unit) {
    if (!Array.isArray(vec) || vec.length < 3 || !vec.every(Number.isFinite)) {
      return 'unavailable';
    }
    const d = n !== undefined ? n : 3;
    const s = '(' + vec[0].toFixed(d) + ', ' + vec[1].toFixed(d) + ', ' + vec[2].toFixed(d) + ')';
    return unit ? s + ' ' + unit : s;
  }

  function norm3(vec) {
    if (!Array.isArray(vec) || vec.length < 3 || !vec.every(Number.isFinite)) return NaN;
    return Math.hypot(vec[0], vec[1], vec[2]);
  }

  function cameraDepth(camera, q, center) {
    const c = center || [0, 0, 0];
    const dx = q[0] - c[0];
    const dy = q[1] - c[1];
    const dz = q[2] - c[2];
    const yawRad = ((Number(camera && camera.yaw) || 0) * Math.PI) / 180;
    const pitchRad = ((Number(camera && camera.pitch) || 0) * Math.PI) / 180;
    const ry = Math.sin(yawRad) * dx + Math.cos(yawRad) * dy;
    return -Math.sin(pitchRad) * dz + Math.cos(pitchRad) * ry;
  }

  function computeBounds(points, fallback) {
    const fb = fallback || [
      [-180, 180],
      [-180, 180],
      [-180, 180]
    ];
    if (!Array.isArray(points) || !points.length) return fb;
    const min = [Infinity, Infinity, Infinity];
    const max = [-Infinity, -Infinity, -Infinity];
    let count = 0;
    for (let i = 0; i < points.length; i++) {
      const p = points[i];
      if (!Array.isArray(p) || p.length < 3) continue;
      if (!Number.isFinite(p[0]) || !Number.isFinite(p[1]) || !Number.isFinite(p[2])) continue;
      count++;
      for (let d = 0; d < 3; d++) {
        if (p[d] < min[d]) min[d] = p[d];
        if (p[d] > max[d]) max[d] = p[d];
      }
    }
    if (!count) return fb;
    return [
      [min[0], max[0]],
      [min[1], max[1]],
      [min[2], max[2]]
    ];
  }

  function pointToSegmentDist2(px, py, ax, ay, bx, by) {
    const dx = bx - ax;
    const dy = by - ay;
    const l2 = dx * dx + dy * dy;
    if (l2 <= 1e-9) {
      const ex = px - ax;
      const ey = py - ay;
      return ex * ex + ey * ey;
    }
    const t = clamp(((px - ax) * dx + (py - ay) * dy) / l2, 0, 1);
    const qx = ax + t * dx;
    const qy = ay + t * dy;
    const ex = px - qx;
    const ey = py - qy;
    return ex * ex + ey * ey;
  }

  function canvasLogicalPoint(canvas, clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const rw = Math.max(1, rect.width);
    const rh = Math.max(1, rect.height);
    const x = ((clientX - rect.left) * canvas.width) / rw;
    const y = ((clientY - rect.top) * canvas.height) / rh;
    return [x, y, rw, rh];
  }

  function drawArrow2D(ctx, p, r, headLen, headHalfWidth) {
    const hl = headLen !== undefined ? headLen : 3.5;
    const hw = headHalfWidth !== undefined ? headHalfWidth : 2.1;
    ctx.beginPath();
    ctx.moveTo(p[0], p[1]);
    ctx.lineTo(r[0], r[1]);
    const dx = r[0] - p[0];
    const dy = r[1] - p[1];
    const l = Math.hypot(dx, dy);
    if (l > 2) {
      for (const s of [-1, 1]) {
        ctx.moveTo(r[0], r[1]);
        ctx.lineTo(r[0] - (hl * dx) / l + (s * hw * dy) / l, r[1] - (hl * dy) / l - (s * hw * dx) / l);
      }
    }
    ctx.stroke();
  }

  function drawSelectedMarker(ctx, p, r, color) {
    ctx.save();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    ctx.strokeStyle = color || '#0f172a';
    ctx.fillStyle = '#ffffff';
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.arc(p[0], p[1], 5.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    if (r && Number.isFinite(r[0]) && Number.isFinite(r[1])) {
      ctx.beginPath();
      ctx.arc(r[0], r[1], 3.4, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  function createController(options) {
    const opts = options || {};
    const mount = typeof opts.mount === 'string' ? document.getElementById(opts.mount) : opts.mount;
    const bounds = opts.bounds || [
      [-177, 177],
      [-177, 177],
      [-178.5, 178.5]
    ];
    const unit = opts.unit !== undefined ? opts.unit : 'µm';
    const step = opts.step !== undefined ? opts.step : 1;
    const digits = opts.digits !== undefined ? opts.digits : 1;
    const axisLabelPrefix = opts.axisLabelPrefix || 'Slice axis';
    const sampleLabel = opts.sampleLabel || 'Inspect sample';

    const state = {
      axis: 'all',
      min: bounds[0][0],
      max: bounds[0][1],
      bounds: bounds,
      selectedId: null,
      items: []
    };

    let axisSel, minInput, maxInput, resetSliceBtn, slabStatusEl;
    let sampleSel, prevBtn, nextBtn, clearBtn, readoutEl, legendEl;
    const pickMap = new Map();

    function axisIndex(a) {
      return a === 'x' ? 0 : a === 'y' ? 1 : a === 'z' ? 2 : -1;
    }

    function formatBound(v) {
      return Number(v).toFixed(digits);
    }

    function updateSlabStatus() {
      if (!slabStatusEl) return;
      const idx = axisIndex(state.axis);
      if (idx < 0) {
        const bx = state.bounds[0];
        const by = state.bounds[1];
        const bz = state.bounds[2];
        slabStatusEl.textContent =
          'Full volume enabled (' +
          'x: [' + formatBound(bx[0]) + ', ' + formatBound(bx[1]) + '], ' +
          'y: [' + formatBound(by[0]) + ', ' + formatBound(by[1]) + '], ' +
          'z: [' + formatBound(bz[0]) + ', ' + formatBound(bz[1]) + ']' +
          (unit ? ' ' + unit : '') +
          ')';
      } else {
        const lo = Math.min(state.min, state.max);
        const hi = Math.max(state.min, state.max);
        slabStatusEl.textContent =
          state.axis.toUpperCase() +
          ' slab [' +
          formatBound(lo) +
          ', ' +
          formatBound(hi) +
          ']' +
          (unit ? ' ' + unit : '');
      }
    }

    function syncAxisInputs(resetRange) {
      const idx = axisIndex(state.axis);
      if (!minInput || !maxInput) return;
      if (idx < 0) {
        minInput.disabled = true;
        maxInput.disabled = true;
      } else {
        const b = state.bounds[idx];
        minInput.disabled = false;
        maxInput.disabled = false;
        minInput.min = String(b[0]);
        minInput.max = String(b[1]);
        minInput.step = String(step);
        maxInput.min = String(b[0]);
        maxInput.max = String(b[1]);
        maxInput.step = String(step);
        if (resetRange) {
          state.min = b[0];
          state.max = b[1];
        } else {
          state.min = clamp(state.min, b[0], b[1]);
          state.max = clamp(state.max, b[0], b[1]);
        }
        minInput.value = String(state.min);
        maxInput.value = String(state.max);
      }
      updateSlabStatus();
    }

    function triggerChange() {
      if (typeof opts.onChange === 'function') opts.onChange(api);
    }

    function buildUI() {
      if (!mount) return;
      mount.innerHTML = '';
      const bar = document.createElement('div');
      bar.className = 'spatial-inspector-bar';
      bar.setAttribute('role', 'region');
      bar.setAttribute('aria-label', opts.ariaLabel || '3D slice filter and sample inspector');

      const sliceRow = document.createElement('div');
      sliceRow.className = 'spatial-inspector-row';

      const axisWrap = document.createElement('label');
      axisWrap.textContent = axisLabelPrefix + ' ';
      axisSel = document.createElement('select');
      const axisOptions = opts.axisOptions || [
        { value: 'all', label: 'All axes (full volume)' },
        { value: 'x', label: 'X slab' },
        { value: 'y', label: 'Y slab' },
        { value: 'z', label: 'Z slab' }
      ];
      for (const o of axisOptions) {
        const opt = document.createElement('option');
        opt.value = o.value;
        opt.textContent = o.label;
        axisSel.appendChild(opt);
      }
      axisWrap.appendChild(axisSel);

      const minWrap = document.createElement('label');
      minWrap.textContent = 'Slab min ';
      minInput = document.createElement('input');
      minInput.type = 'range';
      minWrap.appendChild(minInput);

      const maxWrap = document.createElement('label');
      maxWrap.textContent = 'Slab max ';
      maxInput = document.createElement('input');
      maxInput.type = 'range';
      maxWrap.appendChild(maxInput);

      resetSliceBtn = document.createElement('button');
      resetSliceBtn.type = 'button';
      resetSliceBtn.textContent = 'Full volume';

      slabStatusEl = document.createElement('span');
      slabStatusEl.className = 'spatial-slab-status';
      slabStatusEl.setAttribute('role', 'status');
      slabStatusEl.setAttribute('aria-live', 'polite');

      sliceRow.append(axisWrap, minWrap, maxWrap, resetSliceBtn, slabStatusEl);

      const pickRow = document.createElement('div');
      pickRow.className = 'spatial-inspector-row';

      const sampleWrap = document.createElement('label');
      sampleWrap.textContent = sampleLabel + ' ';
      sampleSel = document.createElement('select');
      sampleWrap.appendChild(sampleSel);

      prevBtn = document.createElement('button');
      prevBtn.type = 'button';
      prevBtn.textContent = 'Prev';
      prevBtn.title = 'Previous visible sample ([)';

      nextBtn = document.createElement('button');
      nextBtn.type = 'button';
      nextBtn.textContent = 'Next';
      nextBtn.title = 'Next visible sample (])';

      clearBtn = document.createElement('button');
      clearBtn.type = 'button';
      clearBtn.textContent = 'Clear selection';

      pickRow.append(sampleWrap, prevBtn, nextBtn, clearBtn);

      legendEl = document.createElement('div');
      legendEl.className = 'spatial-overlay-legend';
      legendEl.hidden = true;

      readoutEl = document.createElement('div');
      readoutEl.className = 'spatial-readout';
      readoutEl.setAttribute('role', 'region');
      readoutEl.setAttribute('aria-live', 'polite');
      readoutEl.textContent = opts.emptyReadout || 'Click any displayed vector/segment on a 3D canvas or choose a sample above to inspect saved numerical values.';

      bar.append(sliceRow, pickRow, legendEl, readoutEl);
      mount.appendChild(bar);

      axisSel.addEventListener('change', function () {
        state.axis = axisSel.value;
        syncAxisInputs(true);
        triggerChange();
      });

      minInput.addEventListener('input', function () {
        state.min = Number(minInput.value);
        if (state.min > state.max) {
          state.max = state.min;
          maxInput.value = String(state.max);
        }
        updateSlabStatus();
        triggerChange();
      });

      maxInput.addEventListener('input', function () {
        state.max = Number(maxInput.value);
        if (state.max < state.min) {
          state.min = state.max;
          minInput.value = String(state.min);
        }
        updateSlabStatus();
        triggerChange();
      });

      resetSliceBtn.addEventListener('click', function () {
        state.axis = 'all';
        axisSel.value = 'all';
        syncAxisInputs(true);
        triggerChange();
      });

      sampleSel.addEventListener('change', function () {
        const v = sampleSel.value;
        state.selectedId = v === '' ? null : Number(v);
        triggerChange();
      });

      prevBtn.addEventListener('click', function () {
        api.stepSelection(-1);
      });

      nextBtn.addEventListener('click', function () {
        api.stepSelection(1);
      });

      clearBtn.addEventListener('click', function () {
        state.selectedId = null;
        if (sampleSel) sampleSel.value = '';
        triggerChange();
      });

      syncAxisInputs(true);
    }

    function attachCanvasPicking(canvasId) {
      const canvas = typeof canvasId === 'string' ? document.getElementById(canvasId) : canvasId;
      if (!canvas) return;
      let downPos = null;
      canvas.addEventListener('pointerdown', function (e) {
        if (e.button !== undefined && e.button !== 0) return;
        downPos = { x: e.clientX, y: e.clientY, id: e.pointerId };
      });
      canvas.addEventListener('pointerup', function (e) {
        if (!downPos || downPos.id !== e.pointerId) return;
        const dist = Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y);
        downPos = null;
        if (dist > 6) return;
        const [lx, ly, rw] = canvasLogicalPoint(canvas, e.clientX, e.clientY);
        const scaleFactor = canvas.width / Math.max(1, rw);
        const tol = 16 * scaleFactor;
        const targets = pickMap.get(canvas.id) || [];
        let bestId = null;
        let bestD2 = tol * tol;
        for (let i = 0; i < targets.length; i++) {
          const t = targets[i];
          const d2 = pointToSegmentDist2(lx, ly, t.ax, t.ay, t.bx, t.by);
          if (d2 <= bestD2) {
            bestD2 = d2;
            bestId = t.id;
          }
        }
        if (bestId !== null) {
          state.selectedId = bestId;
          if (sampleSel) sampleSel.value = String(bestId);
          triggerChange();
        }
      });
      canvas.addEventListener('keydown', function (e) {
        if (e.key === '[') {
          e.preventDefault();
          api.stepSelection(-1);
        } else if (e.key === ']') {
          e.preventDefault();
          api.stepSelection(1);
        } else if (e.key === 'Escape') {
          e.preventDefault();
          state.selectedId = null;
          if (sampleSel) sampleSel.value = '';
          triggerChange();
        }
      });
    }

    let lastItemSignature = '';

    const api = {
      get axis() {
        return state.axis;
      },
      get selectedId() {
        return state.selectedId;
      },
      setSelectedId: function (id, silent) {
        state.selectedId = id === null || id === undefined ? null : Number(id);
        if (sampleSel) sampleSel.value = state.selectedId === null ? '' : String(state.selectedId);
        if (!silent) triggerChange();
      },
      setBounds: function (newBounds) {
        if (!Array.isArray(newBounds) || newBounds.length < 3) return;
        state.bounds = newBounds;
        syncAxisInputs(state.axis === 'all');
      },
      inSlab: function (q) {
        const idx = axisIndex(state.axis);
        if (idx < 0) return true;
        if (!Array.isArray(q) || !Number.isFinite(q[idx])) return false;
        const lo = Math.min(state.min, state.max);
        const hi = Math.max(state.min, state.max);
        return q[idx] >= lo - 1e-9 && q[idx] <= hi + 1e-9;
      },
      setItems: function (items, placeholderText) {
        state.items = Array.isArray(items) ? items : [];
        if (!sampleSel) return;
        const sig = state.items.map(function (it) { return it.id + ':' + it.label; }).join('|');
        if (sig !== lastItemSignature) {
          lastItemSignature = sig;
          sampleSel.innerHTML = '';
          const noneOpt = document.createElement('option');
          noneOpt.value = '';
          noneOpt.textContent = placeholderText || ('None selected (' + state.items.length + ' in view)');
          sampleSel.appendChild(noneOpt);
          for (let i = 0; i < state.items.length; i++) {
            const it = state.items[i];
            const opt = document.createElement('option');
            opt.value = String(it.id);
            opt.textContent = it.label;
            sampleSel.appendChild(opt);
          }
        } else if (sampleSel.options.length > 0) {
          sampleSel.options[0].textContent = placeholderText || ('None selected (' + state.items.length + ' in view)');
        }
        const hasSelected = state.selectedId !== null && state.items.some(function (it) { return it.id === state.selectedId; });
        if(!hasSelected)state.selectedId=null;
        sampleSel.value = hasSelected ? String(state.selectedId) : '';
      },
      stepSelection: function (delta) {
        if (!state.items.length) return;
        let idx = state.items.findIndex(function (it) { return it.id === state.selectedId; });
        if (idx < 0) {
          idx = delta >= 0 ? 0 : state.items.length - 1;
        } else {
          idx = (idx + delta + state.items.length) % state.items.length;
        }
        state.selectedId = state.items[idx].id;
        if (sampleSel) sampleSel.value = String(state.selectedId);
        triggerChange();
      },
      setPickTargets: function (canvasId, targets) {
        pickMap.set(canvasId, Array.isArray(targets) ? targets : []);
      },
      setLegend: function (htmlOrText, visible) {
        if (!legendEl) return;
        legendEl.hidden = !visible;
        if (visible) legendEl.innerHTML = htmlOrText;
      },
      setReadout: function (html) {
        if (!readoutEl) return;
        readoutEl.innerHTML = html;
      }
    };

    buildUI();
    for (const cId of opts.canvases || []) {
      attachCanvasPicking(cId);
    }
    return api;
  }

  global.SpatialInspector = {
    createController: createController,
    computeBounds: computeBounds,
    cameraDepth: cameraDepth,
    fmt: fmt,
    fmtVec: fmtVec,
    norm3: norm3,
    drawArrow2D: drawArrow2D,
    drawSelectedMarker: drawSelectedMarker
  };
})(window);
