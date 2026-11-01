'use strict';
(function (root) {
  function distToSegment(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1,
      dy = y2 - y1,
      l2 = dx * dx + dy * dy;
    if (l2 <= 1e-12) return Math.hypot(px - x1, py - y1);
    const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / l2));
    return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
  }
  function fmt(v, d = 4) {
    if (v === null || v === undefined || !Number.isFinite(v)) return '—';
    if (Math.abs(v) < 1e-12) return '0';
    if (Math.abs(v) < 1e-3 || Math.abs(v) >= 1e4) return v.toExponential(2);
    return Number(v.toPrecision(d)).toString();
  }
  function createGroup(config) {
    const bar = document.createElement('div');
    bar.className = 'canvas-probe';
    bar.setAttribute('role', 'region');
    bar.setAttribute('aria-label', config.label || 'Network element inspector');
    bar.innerHTML =
      '<div class="canvas-probe-controls">' +
      '<span class="canvas-probe-tag">ELEMENT INSPECTOR</span>' +
      '<label>Panel <select data-role="panel"></select></label>' +
      '<label>Element <select data-role="item"><option value="">Click a node/segment or choose…</option></select></label>' +
      '<button type="button" class="secondary" data-role="prev" aria-label="Previous network element">◀ Prev</button>' +
      '<button type="button" class="secondary" data-role="next" aria-label="Next network element">Next ▶</button>' +
      '<button type="button" class="secondary" data-role="clear">Clear</button>' +
      '</div>' +
      '<div class="canvas-probe-readout" role="status" aria-live="polite">' +
      (config.emptyText ||
        'Click any displayed node, fiber, or connector on the canvas (or select via keyboard) to inspect exact model coordinates and state.') +
      '</div>';
    const anchor =
      typeof config.mountAfter === 'string'
        ? document.getElementById(config.mountAfter)
        : config.mountAfter;
    if (anchor && anchor.parentNode) anchor.insertAdjacentElement('afterend', bar);
    const panelSel = bar.querySelector('[data-role="panel"]'),
      itemSel = bar.querySelector('[data-role="item"]'),
      prevBtn = bar.querySelector('[data-role="prev"]'),
      nextBtn = bar.querySelector('[data-role="next"]'),
      clearBtn = bar.querySelector('[data-role="clear"]'),
      readout = bar.querySelector('.canvas-probe-readout');
    const scenes = new Map();
    let selected = null;
    for (const p of config.panels) {
      const o = document.createElement('option');
      o.value = p.id;
      o.textContent = p.title;
      panelSel.append(o);
      const el = document.getElementById(p.id);
      if (!el) continue;
      el.style.cursor = 'crosshair';
      el.addEventListener('click', (ev) => {
        const sc = scenes.get(p.id);
        if (!sc || !sc.items || !sc.items.length) return;
        const rect = el.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1) return;
        const x = ev.clientX - rect.left,
          y = ev.clientY - rect.top;
        let bestNode = null,
          bestNodeD = 12,
          bestSeg = null,
          bestSegD = 9;
        for (const it of sc.items) {
          if (it.kind === 'node') {
            const d = Math.hypot(x - it.px, y - it.py);
            if (d < bestNodeD) {
              bestNodeD = d;
              bestNode = it;
            }
          } else {
            const d = distToSegment(x, y, it.x1, it.y1, it.x2, it.y2);
            if (d < bestSegD) {
              bestSegD = d;
              bestSeg = it;
            }
          }
        }
        const hit = bestNode || bestSeg;
        panelSel.value = p.id;
        if (hit) {
          selected = { panelId: p.id, key: hit.key };
        } else if (selected && selected.panelId === p.id) {
          selected = null;
        }
        syncControls();
        if (config.onSelect) config.onSelect();
      });
    }
    if (config.panels.length <= 1) {
      panelSel.parentElement.hidden = true;
    }
    function activePanelId() {
      return selected?.panelId || panelSel.value || config.panels[0]?.id;
    }
    function describe(sc, it) {
      const parts = [`[${sc.title}] ${it.label}`];
      if (it.status) parts.push(`status: ${it.status}`);
      if (it.endpoints) parts.push(`nodes: ${it.endpoints}`);
      if (it.refCoords) parts.push(`ref (X₀, Y₀): (${fmt(it.refCoords[0], 3)}, ${fmt(it.refCoords[1], 3)})`);
      if (it.curCoords) parts.push(`current (x, y): (${fmt(it.curCoords[0], 3)}, ${fmt(it.curCoords[1], 3)})`);
      if (it.refLength !== undefined && it.curLength !== undefined) {
        const ext = it.refLength > 1e-12 ? it.curLength / it.refLength - 1 : 0;
        parts.push(`L₀=${fmt(it.refLength, 3)}, L=${fmt(it.curLength, 3)} (ε=${(ext * 100).toFixed(2)}%)`);
      }
      if (it.force !== undefined && it.force !== null) {
        const sign = Math.abs(it.force) < 1e-12 ? 'neutral' : it.force > 0 ? 'tension' : 'compression';
        parts.push(`axial force: ${fmt(it.force, 3)} (${sign})`);
      }
      if (it.area !== undefined) parts.push(`A=${fmt(it.area, 3)}`);
      if (it.stiffness !== undefined) parts.push(`k=${fmt(it.stiffness, 3)}`);
      if (it.phasors) {
        for (const ph of it.phasors) {
          parts.push(
            `${ph.name} |u|=${fmt(ph.amp, 3)}, dominant-component lag (−arg u)=${ph.phaseDeg.toFixed(1)}°, u(φ)=(${fmt(ph.ux, 3)}, ${fmt(ph.uy, 3)})`,
          );
        }
      }
      if (sc.note) parts.push(sc.note);
      return parts.join(' · ');
    }
    let optionSignature='';
    function syncControls() {
      const pid=activePanelId(),sc=scenes.get(pid);
      if(selected&&!scenes.get(selected.panelId)?.items?.some(x=>x.key===selected.key))selected=null;
      const items=sc?.items||[];
      const sig=pid+'|'+items.map(x=>x.key+':'+(x.shortLabel||x.label)).join('|');
      if(sig!==optionSignature){
        optionSignature=sig;itemSel.replaceChildren(new Option('Click a node/segment or choose…',''));
        for(const it of items)itemSel.append(new Option(it.shortLabel||it.label,it.key));
      }
      itemSel.value=selected?.panelId===pid?selected.key:'';
      if(selected){const selectedScene=scenes.get(selected.panelId),it=selectedScene.items.find(x=>x.key===selected.key);panelSel.value=selected.panelId;readout.textContent=describe(selectedScene,it)}
      else readout.textContent=config.emptyText||'Click a displayed node, fiber, or connector (or use the element selector) to inspect its model state.';
    }
    panelSel.onchange = () => {
      const pid = panelSel.value,
        sc = scenes.get(pid);
      if (selected && selected.panelId !== pid) {
        if (sc?.items?.some((x) => x.key === selected.key)) {
          selected = { panelId: pid, key: selected.key };
        } else {
          selected = null;
        }
      }
      syncControls();
      if (config.onSelect) config.onSelect();
    };
    itemSel.onchange = () => {
      const pid = panelSel.value,
        key = itemSel.value;
      selected = key ? { panelId: pid, key } : null;
      syncControls();
      if (config.onSelect) config.onSelect();
    };
    function step(delta) {
      const pid = activePanelId(),
        sc = scenes.get(pid);
      if (!sc || !sc.items || !sc.items.length) return;
      const idx = selected && selected.panelId === pid
        ? sc.items.findIndex((x) => x.key === selected.key)
        : -1;
      const nextIdx = (idx + delta + sc.items.length) % sc.items.length;
      selected = { panelId: pid, key: sc.items[nextIdx].key };
      syncControls();
      if (config.onSelect) config.onSelect();
    }
    prevBtn.onclick = () => step(-1);
    nextBtn.onclick = () => step(1);
    clearBtn.onclick = () => {
      selected = null;
      syncControls();
      if (config.onSelect) config.onSelect();
    };
    function drawHighlight(ctx, it) {
      ctx.save();
      ctx.setLineDash([]);
      if (it.kind === 'node') {
        ctx.strokeStyle = '#14231f';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(it.px, it.py, 7.5, 0, Math.PI * 2);
        ctx.stroke();
        ctx.strokeStyle = '#ffdf6b';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.arc(it.px, it.py, 7.5, 0, Math.PI * 2);
        ctx.stroke();
      } else {
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#14231f';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(it.x1, it.y1);
        ctx.lineTo(it.x2, it.y2);
        ctx.stroke();
        ctx.strokeStyle = '#ffdf6b';
        ctx.lineWidth = 2.6;
        ctx.beginPath();
        ctx.moveTo(it.x1, it.y1);
        ctx.lineTo(it.x2, it.y2);
        ctx.stroke();
      }
      ctx.restore();
    }
    return {
      updateScene(panelId, ctx, scene) {
        const pMeta = config.panels.find((p) => p.id === panelId);
        const fullScene = { ...scene, title: scene.title || pMeta?.title || panelId };
        scenes.set(panelId, fullScene);
        if (selected && selected.panelId === panelId) {
          const found = fullScene.items.find((x) => x.key === selected.key);
          if (found && ctx) drawHighlight(ctx, found);
        }
        syncControls();
      },
      clearScene(panelId) {
        scenes.delete(panelId);
        if (selected && selected.panelId === panelId) selected = null;
        syncControls();
      },
    };
  }
  function buildMechanicalItems(opts) {
    const { net, frame, pt, fixedDofs, links, linkAlive, linkForces } = opts;
    const X = frame?.x || net.X,
      items = [];
    for (let i = 0; i < net.N; i++) {
      const [px, py] = pt(X[2 * i], X[2 * i + 1]);
      const pinned =
        fixedDofs &&
        (fixedDofs.has(2 * i) || fixedDofs.has(2 * i + 1));
      items.push({
        key: `node:${i}`,
        kind: 'node',
        label: `Node #${i}`,
        shortLabel: `Node #${i}`,
        status: pinned ? 'prescribed/supported' : 'free interior/boundary',
        px,
        py,
        refCoords: [net.X[2 * i], net.X[2 * i + 1]],
        curCoords: [X[2 * i], X[2 * i + 1]],
      });
    }
    net.edges.forEach((e, k) => {
      const [x1, y1] = pt(X[2 * e.i], X[2 * e.i + 1]),
        [x2, y2] = pt(X[2 * e.j], X[2 * e.j + 1]),
        alive = frame ? frame.alive[k] : true,
        force = frame?.forces ? frame.forces[k] : null,
        curL = Math.hypot(X[2 * e.j] - X[2 * e.i], X[2 * e.j + 1] - X[2 * e.i + 1]);
      items.push({
        key: `edge:${k}`,
        kind: 'edge',
        label: `Collagen fiber #${k}`,
        shortLabel: `Fiber #${k} (${e.i}–${e.j})`,
        endpoints: `${e.i}–${e.j}`,
        status: alive ? 'intact' : 'ruptured',
        x1,
        y1,
        x2,
        y2,
        refLength: e.L,
        curLength: curL,
        force,
        area: e.A,
      });
    });
    if (links && links.length) {
      links.forEach((e, k) => {
        const [x1, y1] = pt(X[2 * e.i], X[2 * e.i + 1]),
          [x2, y2] = pt(X[2 * e.j], X[2 * e.j + 1]),
          alive = linkAlive ? linkAlive[k] : true,
           curL = Math.hypot(X[2 * e.j] - X[2 * e.i], X[2 * e.j + 1] - X[2 * e.i + 1]),
          force = linkForces
            ? linkForces[k]
            : alive && Number.isFinite(e.k)
              ? e.k * (curL - e.L)
              : 0;
        items.push({
          key: `link:${k}`,
          kind: 'link',
          label: `Added connector #${k}`,
          shortLabel: `Connector #${k} (${e.i}–${e.j})`,
          endpoints: `${e.i}–${e.j}`,
          status: alive ? 'intact' : 'broken',
          x1,
          y1,
          x2,
          y2,
          refLength: e.L,
          curLength: curL,
          force,
          stiffness: e.k,
        });
      });
    }
    return items;
  }
  function buildMicroItems(opts) {
    const { c, vectors, phase, delta, point } = opts,
      items = [],
      freeSet = new Set(c.free || []);
    for (let i = 0; i < c.X.length / 2; i++) {
      const [px, py] = point(i),
        isProbe = c.probe && c.probe.includes(i),
        isClamped = c.free ? !freeSet.has(2 * i) : null,
        phasors = [];
      if (vectors) {
        for (const key of delta ? ['after'] : ['intact', 'after']) {
          const u = vectors[key],
            rx = u.real[2 * i],
            ix = u.imag[2 * i],
            ry = u.real[2 * i + 1],
            iy = u.imag[2 * i + 1],
            amp = Math.hypot(rx, ix, ry, iy),
            domR = Math.hypot(rx, ix) >= Math.hypot(ry, iy) ? rx : ry,
            domI = Math.hypot(rx, ix) >= Math.hypot(ry, iy) ? ix : iy,
            phaseDeg = (Math.atan2(-domI, domR) * 180) / Math.PI,
            ux = rx * Math.cos(phase) - ix * Math.sin(phase),
            uy = ry * Math.cos(phase) - iy * Math.sin(phase);
          phasors.push({
            name: key === 'intact' ? 'intact' : delta ? 'Δ(damaged−intact)' : 'damaged',
            amp,
            phaseDeg,
            ux,
            uy,
          });
        }
      }
      items.push({
        key: `node:${i}`,
        kind: 'node',
        label: `Node #${i}`,
        shortLabel: `Node #${i}${isProbe ? ' (probe)' : ''}`,
        status: isProbe ? 'driven probe node' : isClamped === null ? 'support status not stored in this field record' : isClamped ? 'clamped boundary' : 'free interior',
        px,
        py,
        refCoords: [c.X[2 * i], c.X[2 * i + 1]],
        phasors,
      });
    }
    c.edges.forEach((e, k) => {
      const [x1, y1] = point(e.i),
        [x2, y2] = point(e.j),
        inLesion = c.lesion && c.lesion.includes(k);
      items.push({
        key: `edge:${k}`,
        kind: 'edge',
        label: `Collagen fiber #${k}`,
        shortLabel: `Fiber #${k} (${e.i}–${e.j})${inLesion ? ' [lesion]' : ''}`,
        endpoints: `${e.i}–${e.j}`,
        status: inLesion ? 'prescribed lesion (removed in damaged state)' : 'intact in both states',
        x1,
        y1,
        x2,
        y2,
        refLength: e.L,
        curLength: e.L,
        area: e.A,
      });
    });
    if (c.links && c.links.length) {
      c.links.forEach((e, k) => {
        const [x1, y1] = point(e.i),
          [x2, y2] = point(e.j);
        items.push({
          key: `link:${k}`,
          kind: 'link',
          label: `Added connector #${k}`,
          shortLabel: `Connector #${k} (${e.i}–${e.j})`,
          endpoints: `${e.i}–${e.j}`,
          status: 'intact harmonic spring',
          x1,
          y1,
          x2,
          y2,
          refLength: e.L,
          curLength: e.L,
          stiffness: e.k,
        });
      });
    }
    return items;
  }
  root.AtlasCanvasProbe = { createGroup, buildMechanicalItems, buildMicroItems };
})(globalThis);
