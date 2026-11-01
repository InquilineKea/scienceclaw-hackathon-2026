/* Original renderer upgraded to 3D C-alpha viewer: saved CDSM coordinates only, no molecular dynamics or mechanical computation. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const d = globalThis.SPECIES_PILOT;
  const statusEl = $('speciesStatus');
  if (!d) {
    if (statusEl) statusEl.textContent = 'Pilot output unavailable';
    return;
  }

  const CHAIN_COLORS = ['#20775b', '#8950a0', '#c96b32'];
  const CHAIN_NAMES = ['A', 'B', 'C'];
  const AA_NAMES = {
    A: 'Ala', R: 'Arg', N: 'Asn', D: 'Asp', C: 'Cys',
    E: 'Glu', Q: 'Gln', G: 'Gly', H: 'His', I: 'Ile',
    L: 'Leu', K: 'Lys', M: 'Met', F: 'Phe', P: 'Pro',
    S: 'Ser', T: 'Thr', W: 'Trp', Y: 'Tyr', V: 'Val', O: 'Hyp'
  };

  const state = {
    selectedChain: 2,
    selectedRes: 0,
    bendDeg: 0,
     bendPlane: 'xy',
    showGhost: true,
    showMismatches: true,
    seqKey: '',
    screenPts: { beaver: [], human: [] }
  };

  const canvasBeaver = $('speciesBeaver');
  const canvasHuman = $('speciesHuman');

  const camera = globalThis.SpatialCamera
    ? globalThis.SpatialCamera.create({
        canvases: [canvasBeaver, canvasHuman],
        yawInput: 'speciesYaw',
        pitchInput: 'speciesPitch',
        zoomInput: 'speciesZoom',
        statusElement: 'speciesCameraStatus',
        resetButton: 'speciesResetView',
        presetButtons: document.querySelectorAll('#structures [data-view-preset]'),
        defaultYaw: 18,
        defaultPitch: 16,
        defaultZoom: 1,
        minZoom: 0.5,
        maxZoom: 3.0,
        onChange: () => renderCanvases()
      })
    : null;

  function getRollRad() {
    const el = $('speciesRotation');
    return ((el ? +el.value : 30) * Math.PI) / 180;
  }

  function updateControlReadouts() {
    const rotVal = $('speciesRotationValue');
    if (rotVal && $('speciesRotation')) rotVal.textContent = `${$('speciesRotation').value}°`;
    const yawVal = $('speciesYawValue');
    if (yawVal && $('speciesYaw')) yawVal.textContent = `${$('speciesYaw').value}°`;
    const pitchVal = $('speciesPitchValue');
    if (pitchVal && $('speciesPitch')) pitchVal.textContent = `${$('speciesPitch').value}°`;
    const zoomVal = $('speciesZoomValue');
    if (zoomVal && $('speciesZoom')) zoomVal.textContent = `${(+$('speciesZoom').value).toFixed(2)}×`;
    const bendVal = $('speciesBendValue');
    if (bendVal) {
      bendVal.textContent =
        state.bendDeg === 0
          ? '0° (OFF — exact saved coordinates)'
          : `${state.bendDeg > 0 ? '+' : ''}${state.bendDeg}° illustrative arc`;
    }
    const bendBanner = $('speciesBendWarning');
    if (bendBanner) {
      bendBanner.classList.toggle('is-active', state.bendDeg !== 0);
    }
  }

  function getCurrentContext() {
    const w = $('speciesWindow').value;
    const o = $('speciesOrder').value;
    const n = +$('speciesLength').value;
    const ids = [`beaver-${w}-${o}`, `human-${w}-${o}`];
    const coords = ids.map((id) => d.outputs.caCoordinates[id]);
    const tasks = ids.map((id) => d.inputs.tasks.find((t) => t.id === id));
    return { w, o, n, ids, coords, tasks };
  }

  function isMismatch(tasks, chainIdx, resIdx) {
    const seqB = tasks[0].sequences[chainIdx];
    const seqH = tasks[1].sequences[chainIdx];
    return seqB[resIdx] !== seqH[resIdx];
  }

  function transformPoint(p, rollRad, xmin, xmax, bendDeg, bendPlane) {
    const x0 = p[0];
    const y0 = p[1];
    const z0 = p[2];
    const yr = y0 * Math.cos(rollRad) - z0 * Math.sin(rollRad);
    const zr = y0 * Math.sin(rollRad) + z0 * Math.cos(rollRad);
    if (!bendDeg || Math.abs(bendDeg) < 1e-6) {
      return [x0, yr, zr];
    }
    const L = Math.max(1e-6, xmax - xmin);
    const theta = (bendDeg * Math.PI) / 180;
    const R = L / theta;
    const xmid = 0.5 * (xmin + xmax);
    const s = x0 - xmid;
    const phi = s / R;
    const sinPhi = Math.sin(phi);
    const cosPhi = Math.cos(phi);

    if (bendPlane === 'xz') {
      const cx = xmid + R * sinPhi;
      const cz = R * (1 - cosPhi);
      const x = cx - zr * sinPhi;
      const z = cz + zr * cosPhi;
      return [x, yr, z];
    }
    const cx = xmid + R * sinPhi;
    const cy = R * (1 - cosPhi);
    const x = cx - yr * sinPhi;
    const y = cy + yr * cosPhi;
    return [x, y, zr];
  }

  function projectWithDepth(pt3d, center, scale, W, H, yawDeg, pitchDeg, zoom) {
    const dx = pt3d[0] - center[0];
    const dy = pt3d[1] - center[1];
    const dz = pt3d[2] - center[2];
    const yawRad = (yawDeg * Math.PI) / 180;
    const pitchRad = (pitchDeg * Math.PI) / 180;
    const rx = Math.cos(yawRad) * dx - Math.sin(yawRad) * dy;
    const ry = Math.sin(yawRad) * dx + Math.cos(yawRad) * dy;
    const u = rx;
    const v = Math.cos(pitchRad) * dz + Math.sin(pitchRad) * ry;
    const depth = -Math.sin(pitchRad) * dz + Math.cos(pitchRad) * ry;
    const sx = W * 0.5 + zoom * scale * u;
    const sy = H * 0.5 - zoom * scale * v;
    return { x: sx, y: sy, u, v, depth };
  }

  function populateResidueSelect(n, tasks) {
    const sel = $('speciesResidueSelect');
    if (!sel) return;
    const chainSel = $('speciesChainSelect');
    const chainIdx = chainSel ? +chainSel.value : state.selectedChain;
    if (state.selectedRes >= n) {
      state.selectedRes = n - 1;
    }
    const prevVal = state.selectedRes;
    sel.innerHTML = '';
    const seqB = tasks[0].sequences[chainIdx];
    const seqH = tasks[1].sequences[chainIdx];
    for (let i = 0; i < 90; i++) {
      const opt = document.createElement('option');
      opt.value = String(i);
      const bAA = seqB[i];
      const hAA = seqH[i];
      const diffTag = bAA !== hAA ? ` [MISMATCH ${bAA}≠${hAA}]` : ` (${bAA})`;
      const hiddenTag = i >= n ? ' [outside 30-res view]' : '';
      opt.textContent = `Residue ${i + 1}${diffTag}${hiddenTag}`;
      sel.appendChild(opt);
    }
    sel.value = String(prevVal);
  }

  function buildSequenceTable(ctx) {
    const { w, o, n, tasks } = ctx;
    const key = `${w}-${o}`;
    if (state.seqKey === key) {
      updateSequenceHighlights(n);
      return;
    }
    state.seqKey = key;

    const container = $('speciesSequences');
    container.innerHTML = '';

    const table = document.createElement('table');
    table.className = 'seq-comparison-table';
    const caption = document.createElement('caption');
    caption.textContent =
      'Full 90-residue input windows (click or press Enter on any residue to inspect 3D coordinates; mismatches are marked with ≠ and highlighted; amino-acid differences are retained in the download).';
    table.appendChild(caption);

    const thead = document.createElement('thead');
    thead.innerHTML =
      '<tr><th scope="col">Chain</th><th scope="col">Species</th><th scope="col">90-residue window sequence (interactive)</th></tr>';
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    const genes = o.split('');

    for (let cIdx = 0; cIdx < 3; cIdx++) {
      const gene = genes[cIdx];
      const seqB = tasks[0].sequences[cIdx];
      const seqH = tasks[1].sequences[cIdx];
      let diffCount = 0;
      for (let i = 0; i < 90; i++) {
        if (seqB[i] !== seqH[i]) diffCount++;
      }

      for (let sIdx = 0; sIdx < 2; sIdx++) {
        const tr = document.createElement('tr');
        tr.className = sIdx === 0 ? 'seq-row-beaver' : 'seq-row-human';
        if (sIdx === 0) {
          const thChain = document.createElement('th');
          thChain.rowSpan = 2;
          thChain.scope = 'rowgroup';
          thChain.className = `chain-header chain-badge-${cIdx}`;
          thChain.innerHTML = `<span class="chain-dot chain-color-${cIdx}"></span>Chain ${CHAIN_NAMES[cIdx]} · COL1A${gene}<div class="chain-diff-note">${diffCount} mismatch${diffCount === 1 ? '' : 'es'}</div>`;
          tr.appendChild(thChain);
        }
        const thSp = document.createElement('th');
        thSp.scope = 'row';
        thSp.className = 'species-subhead';
        thSp.textContent = sIdx === 0 ? 'Beaver' : 'Human';
        tr.appendChild(thSp);

        const td = document.createElement('td');
        const wrap = document.createElement('div');
        wrap.className = 'seq-strip';
        const seqStr = sIdx === 0 ? seqB : seqH;

        for (let rIdx = 0; rIdx < 90; rIdx++) {
          const aa = seqStr[rIdx];
          const mm = seqB[rIdx] !== seqH[rIdx];
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'seq-res-btn' + (mm ? ' is-mismatch' : '');
          btn.dataset.chain = String(cIdx);
          btn.dataset.res = String(rIdx);
          btn.setAttribute(
            'aria-label',
            `${sIdx === 0 ? 'Beaver' : 'Human'} Chain ${CHAIN_NAMES[cIdx]} (COL1A${gene}) residue ${rIdx + 1}: ${aa}${mm ? `, mismatch (${seqB[rIdx]} in Beaver vs ${seqH[rIdx]} in Human)` : ', identical'}`
          );
          btn.title = `Chain ${CHAIN_NAMES[cIdx]} res ${rIdx + 1}: Beaver ${seqB[rIdx]} / Human ${seqH[rIdx]}${mm ? ' (MISMATCH)' : ''}`;
          btn.innerHTML = `<span class="aa-char">${aa}</span>${mm ? '<span class="mm-mark" aria-hidden="true">≠</span>' : ''}`;
          btn.addEventListener('click', () => {
            selectResidue(cIdx, rIdx, true);
          });
          wrap.appendChild(btn);
        }
        td.appendChild(wrap);
        tr.appendChild(td);
        tbody.appendChild(tr);
      }
    }

    table.appendChild(tbody);
    container.appendChild(table);
    populateResidueSelect(n, tasks);
    updateSequenceHighlights(n);
  }

  function updateSequenceHighlights(n) {
    const container = $('speciesSequences');
    if (!container) return;
    const buttons = container.querySelectorAll('.seq-res-btn');
    buttons.forEach((btn) => {
      const c = +btn.dataset.chain;
      const r = +btn.dataset.res;
      const isSel = c === state.selectedChain && r === state.selectedRes;
      const isOutside = r >= n;
      btn.classList.toggle('is-selected', isSel);
      btn.classList.toggle('is-outside-window', isOutside);
      btn.setAttribute('aria-pressed', String(isSel));
    });
  }

  function selectResidue(chainIdx, resIdx, ensureVisible) {
    state.selectedChain = Math.max(0, Math.min(2, chainIdx));
    state.selectedRes = Math.max(0, Math.min(89, resIdx));
    const lenEl = $('speciesLength');
    if (ensureVisible && lenEl && +lenEl.value === 30 && state.selectedRes >= 30) {
      lenEl.value = '90';
    }
    const chainSel = $('speciesChainSelect');
    if (chainSel) chainSel.value = String(state.selectedChain);
    const resSel = $('speciesResidueSelect');
    if (resSel) resSel.value = String(state.selectedRes);
    render();
  }

  function updateInspector(ctx) {
    const { w, o, n, coords, tasks } = ctx;
    const cIdx = state.selectedChain;
    const rIdx = state.selectedRes;
    const idx = cIdx * 90 + rIdx;
    const pB = coords[0][idx];
    const pH = coords[1][idx];
    const dx = pB[0] - pH[0];
    const dy = pB[1] - pH[1];
    const dz = pB[2] - pH[2];
    const dist = Math.hypot(dx, dy, dz);
    const gene = o[cIdx];
    const aaB = tasks[0].sequences[cIdx][rIdx];
    const aaH = tasks[1].sequences[cIdx][rIdx];
    const mm = aaB !== aaH;
    const offset0 = tasks[0].helicalOffset0 || 0;
    const helPos = offset0 + rIdx + 1;

    const inspector = $('speciesInspector');
    if (!inspector) return;

    const visNote =
      rIdx >= n
        ? ' (Currently outside the 30-residue detail slice; switch Displayed residues to "All 90" to view on canvas)'
        : '';

    inspector.innerHTML =
      `<div class="inspector-head">` +
      `<span class="inspector-chain-pill chain-color-${cIdx}">Chain ${CHAIN_NAMES[cIdx]} · COL1A${gene}</span>` +
      `<strong>Window residue ${rIdx + 1} / 90</strong> (helical position ${helPos})` +
      `<span class="inspector-match-badge ${mm ? 'badge-mismatch' : 'badge-match'}">${mm ? `Sequence mismatch: Beaver ${aaB} (${AA_NAMES[aaB] || aaB}) ≠ Human ${aaH} (${AA_NAMES[aaH] || aaH})` : `Identical amino acid: ${aaB} (${AA_NAMES[aaB] || aaB})`}</span>` +
      `<span class="inspector-vis-note">${visNote}</span>` +
      `</div>` +
      `<div class="inspector-grid">` +
      `<div class="inspector-card">` +
      `<h4>Beaver saved Cα (Å)</h4>` +
      `<code>x = ${pB[0].toFixed(3)}, y = ${pB[1].toFixed(3)}, z = ${pB[2].toFixed(3)}</code>` +
      `</div>` +
      `<div class="inspector-card">` +
      `<h4>Human saved Cα (Å)</h4>` +
      `<code>x = ${pH[0].toFixed(3)}, y = ${pH[1].toFixed(3)}, z = ${pH[2].toFixed(3)}</code>` +
      `</div>` +
      `<div class="inspector-card">` +
      `<h4>Builder-frame Cα difference</h4>` +
      `<code>|Δr| = ${dist.toFixed(3)} Å (Δx ${dx.toFixed(2)}, Δy ${dy.toFixed(2)}, Δz ${dz.toFixed(2)})</code>` +
      `<span class="inspector-subnote">Unaligned builder-frame coordinate difference from saved CDSM output — not a superimposed RMSD or mechanical metric.</span>` +
      `</div>` +
      `</div>`;
  }

  function renderCanvases() {
    updateControlReadouts();
    const ctx = getCurrentContext();
    const { w, o, n, coords, tasks } = ctx;
    const rollRad = getRollRad();
    const yawDeg = camera ? camera.yaw : 18;
    const pitchDeg = camera ? camera.pitch : 16;
    const zoom = camera ? camera.zoom : 1;
    const status=$('speciesCameraStatus');if(status&&Math.abs(yawDeg-270)<.01&&Math.abs(pitchDeg)<.01)status.textContent='End-on down helix x axis · shared scale · zoom '+zoom.toFixed(2)+'× (linked panes)';

    // Compute original x bounds across both species for the displayed residue count
    let xmin = Infinity;
    let xmax = -Infinity;
    for (let s = 0; s < 2; s++) {
      for (let c = 0; c < 3; c++) {
        for (let i = 0; i < n; i++) {
          const x = coords[s][c * 90 + i][0];
          if (x < xmin) xmin = x;
          if (x > xmax) xmax = x;
        }
      }
    }

    // Transform points for both species (both bent/active and original ghost if bent)
    const transformed = [[], []];
    const ghostTransformed = [[], []];
    const allActivePts = [];

    for (let s = 0; s < 2; s++) {
      for (let c = 0; c < 3; c++) {
        for (let i = 0; i < n; i++) {
          const raw = coords[s][c * 90 + i];
          const pt = transformPoint(raw, rollRad, xmin, xmax, state.bendDeg, state.bendPlane);
          const idx = c * 90 + i;
          transformed[s][idx] = pt;
          allActivePts.push(pt);
          if (state.bendDeg !== 0 && state.showGhost) {
            const gpt = transformPoint(raw, rollRad, xmin, xmax, 0, state.bendPlane);
            ghostTransformed[s][idx] = gpt;
            allActivePts.push(gpt);
          }
        }
      }
    }

    // Compute shared 3D centroid across BOTH species and displayed geometry
    let cx = 0;
    let cy = 0;
    let cz = 0;
    for (let k = 0; k < allActivePts.length; k++) {
      cx += allActivePts[k][0];
      cy += allActivePts[k][1];
      cz += allActivePts[k][2];
    }
    const count = Math.max(1, allActivePts.length);
    const center = [cx / count, cy / count, cz / count];

    // Compute unscaled 2D projected bounds across BOTH species so end-on and side views both auto-fit cleanly with one shared scale
    let uMin = Infinity;
    let uMax = -Infinity;
    let vMin = Infinity;
    let vMax = -Infinity;
    const yawRad = (yawDeg * Math.PI) / 180;
    const pitchRad = (pitchDeg * Math.PI) / 180;
    for (let k = 0; k < allActivePts.length; k++) {
      const p = allActivePts[k];
      const dx = p[0] - center[0];
      const dy = p[1] - center[1];
      const dz = p[2] - center[2];
      const rx = Math.cos(yawRad) * dx - Math.sin(yawRad) * dy;
      const ry = Math.sin(yawRad) * dx + Math.cos(yawRad) * dy;
      const u = rx;
      const v = Math.cos(pitchRad) * dz + Math.sin(pitchRad) * ry;
      if (u < uMin) uMin = u;
      if (u > uMax) uMax = u;
      if (v < vMin) vMin = v;
      if (v > vMax) vMax = v;
    }

    const spanU = Math.max(6.5, uMax - uMin);
    const spanV = Math.max(6.5, vMax - vMin);
    const W = Math.max(1, Math.min(canvasBeaver.clientWidth || 520, canvasHuman.clientWidth || 520));
    const H = 320;
    const padX = 96;
    const padY = 86;
    const baseScale = Math.min((W - padX) / spanU, (H - padY) / spanV);

    for (let s = 0; s < 2; s++) {
      const canvas = s === 0 ? canvasBeaver : canvasHuman;
      const spKey = s === 0 ? 'beaver' : 'human';
      const cw = Math.max(1, canvas.clientWidth || W);
      const ch = H;
      const pixel = window.devicePixelRatio || 1;
      canvas.width = cw * pixel;
      canvas.height = ch * pixel;
      const c = canvas.getContext('2d');
      c.save();
      c.scale(pixel, pixel);
      c.clearRect(0, 0, cw, ch);

      const primitives = [];
      const projPts = [];

      // Optional unbent ghost reference trace when illustrative bend is active
      if (state.bendDeg !== 0 && state.showGhost) {
        for (let chain = 0; chain < 3; chain++) {
          for (let i = 0; i < n; i++) {
            const idx = chain * 90 + i;
            const gpt = ghostTransformed[s][idx];
            const pr = projectWithDepth(gpt, center, baseScale, cw, ch, yawDeg, pitchDeg, zoom);
            if (i > 0) {
              const prevPr = projectWithDepth(
                ghostTransformed[s][idx - 1],
                center,
                baseScale,
                cw,
                ch,
                yawDeg,
                pitchDeg,
                zoom
              );
              primitives.push({
                type: 'ghost-seg',
                depth: 0.5 * (pr.depth + prevPr.depth) - 50,
                x1: prevPr.x,
                y1: prevPr.y,
                x2: pr.x,
                y2: pr.y,
                chain
              });
            }
          }
        }
      }

      // Project active C-alpha points & segments
      for (let chain = 0; chain < 3; chain++) {
        for (let i = 0; i < n; i++) {
          const idx = chain * 90 + i;
          const pt = transformed[s][idx];
          const pr = projectWithDepth(pt, center, baseScale, cw, ch, yawDeg, pitchDeg, zoom);
          const mm = isMismatch(tasks, chain, i);
          const isSel = chain === state.selectedChain && i === state.selectedRes;
          projPts[idx] = {
            x: pr.x,
            y: pr.y,
            depth: pr.depth,
            chain,
            res: i,
            mismatch: mm,
            selected: isSel
          };
          primitives.push({
            type: 'node',
            depth: pr.depth,
            x: pr.x,
            y: pr.y,
            chain,
            res: i,
            mismatch: mm,
            selected: isSel
          });
          if (i > 0) {
            const prev = projPts[idx - 1];
            primitives.push({
              type: 'seg',
              depth: 0.5 * (pr.depth + prev.depth),
              x1: prev.x,
              y1: prev.y,
              x2: pr.x,
              y2: pr.y,
              chain
            });
          }
        }
      }

      state.screenPts[spKey] = projPts.filter(Boolean);

      // Depth-sort back-to-front (smaller depth drawn first)
      primitives.sort((a, b) => a.depth - b.depth);

      // Find depth range for subtle atmospheric depth cue
      let dMin = Infinity;
      let dMax = -Infinity;
      for (let k = 0; k < primitives.length; k++) {
        if (primitives[k].type === 'ghost-seg') continue;
        const dp = primitives[k].depth;
        if (dp < dMin) dMin = dp;
        if (dp > dMax) dMax = dp;
      }
      const dSpan = Math.max(1, dMax - dMin);

      for (let k = 0; k < primitives.length; k++) {
        const item = primitives[k];
        if (item.type === 'ghost-seg') {
          c.save();
          c.strokeStyle = CHAIN_COLORS[item.chain];
          c.globalAlpha = 0.22;
          c.lineWidth = 1.2;
          c.setLineDash([3, 3]);
          c.beginPath();
          c.moveTo(item.x1, item.y1);
          c.lineTo(item.x2, item.y2);
          c.stroke();
          c.restore();
          continue;
        }

        const depthNorm = Math.max(0, Math.min(1, (item.depth - dMin) / dSpan));
        const alpha = 0.45 + 0.55 * depthNorm;

        if (item.type === 'seg') {
          c.save();
          c.strokeStyle = CHAIN_COLORS[item.chain];
          c.globalAlpha = alpha;
          c.lineWidth = 1.6 + 1.2 * depthNorm;
          c.lineCap = 'round';
          c.beginPath();
          c.moveTo(item.x1, item.y1);
          c.lineTo(item.x2, item.y2);
          c.stroke();
          c.restore();
        } else if (item.type === 'node') {
          const rBase = 2.4 + 1.3 * depthNorm;
          c.save();
          if (item.mismatch && state.showMismatches) {
            c.globalAlpha = 0.98;
            c.fillStyle = '#fffbeb';
            c.strokeStyle = '#d97706';
            c.lineWidth = 2.0;
            c.beginPath();
            c.arc(item.x, item.y, rBase + 3.0, 0, Math.PI * 2);
            c.fill();
            c.stroke();
          }
          c.globalAlpha = item.selected ? 1.0 : alpha;
          c.fillStyle = CHAIN_COLORS[item.chain];
          c.strokeStyle = '#ffffff';
          c.lineWidth = 0.9;
          c.beginPath();
          c.arc(item.x, item.y, item.selected ? rBase + 2.4 : rBase, 0, Math.PI * 2);
          c.fill();
          c.stroke();

          if (item.selected) {
            c.strokeStyle = '#111827';
            c.lineWidth = 2.2;
            c.beginPath();
            c.arc(item.x, item.y, rBase + 6.0, 0, Math.PI * 2);
            c.stroke();
          }
          c.restore();
        }
      }

      // Draw selected residue callout badge on canvas
      const selIdx = state.selectedChain * 90 + state.selectedRes;
      const selPt = projPts[selIdx];
      if (selPt) {
        const aa = tasks[s].sequences[state.selectedChain][state.selectedRes];
        const label = `${CHAIN_NAMES[state.selectedChain]}${state.selectedRes + 1} (${aa})`;
        c.save();
        c.font = 'bold 11px system-ui, sans-serif';
        const tw = c.measureText(label).width;
        const bx = Math.min(cw - tw - 18, Math.max(10, selPt.x + 10));
        const by = Math.max(24, Math.min(ch - 32, selPt.y - 10));
        c.fillStyle = 'rgba(17, 24, 39, 0.88)';
        c.beginPath();
        c.roundRect ? c.roundRect(bx - 5, by - 13, tw + 10, 18, 4) : c.rect(bx - 5, by - 13, tw + 10, 18);
        c.fill();
        c.fillStyle = '#ffffff';
        c.fillText(label, bx, by);
        c.restore();
      }

      // Draw 3D orientation gizmo
      if (camera && typeof camera.drawAxes === 'function') {
        camera.drawAxes(c, cw, ch, {
          x: cw - 44,
          y: 44,
          length: 22,
          labels: ['x', 'y', 'z']
        });
      }

      // Draw scale bar in Angstroms
      const pxPerAng = baseScale * zoom;
      const candidateAng = [2, 5, 10, 20, 50];
      let barAng = 10;
      for (const cand of candidateAng) {
        if (cand * pxPerAng >= 36 && cand * pxPerAng <= 130) {
          barAng = cand;
          break;
        }
      }
      const barPx = barAng * pxPerAng;
      c.save();
      c.strokeStyle = '#334155';
      c.fillStyle = '#334155';
      c.lineWidth = 2;
      const bx0 = cw - barPx - 20;
      const by0 = ch - 18;
      c.beginPath();
      c.moveTo(bx0, by0);
      c.lineTo(bx0 + barPx, by0);
      c.moveTo(bx0, by0 - 4);
      c.lineTo(bx0, by0 + 4);
      c.moveTo(bx0 + barPx, by0 - 4);
      c.lineTo(bx0 + barPx, by0 + 4);
      c.stroke();
      c.font = '11px system-ui, sans-serif';
      c.textAlign = 'right';
      c.fillText(`${barAng} Å projected`, bx0 - 6, by0 + 4);
      c.restore();

      // Bottom-left summary caption inside canvas
      c.save();
      c.fillStyle = '#475569';
      c.font = '11px system-ui, sans-serif';
      const bendTag =
        state.bendDeg === 0
          ? 'saved coords'
          : `illustrative arc ${state.bendDeg}° (${state.bendPlane.toUpperCase()})`;
      c.fillText(
        `Axial span: ${(xmax - xmin).toFixed(1)} Å · ${n} res/chain · ${bendTag}`,
        16,
        ch - 14
      );
      c.restore();

      c.restore();
    }
  }

  function render() {
    const ctx = getCurrentContext();
    const { w, o, n, tasks } = ctx;
    buildSequenceTable(ctx);
    populateResidueSelect(n, tasks);
    updateSequenceHighlights(n);
    updateInspector(ctx);
    renderCanvases();

    const pair = d.outputs.pairedGeometry.find((p) => p.window === w && p.order === o);
    $('speciesCaption').textContent =
      `${w} window · α2 in chain ${'ABC'[o.indexOf('2')]} · full 270-CA builder-frame RMS coordinate difference: ${pair.builderFrameCaRmsDifferenceAngstrom.toFixed(3)} Å. This is not a fitted structural RMSD, force or robustness score.`;
    $('speciesStatus').textContent =
      `${d.outputs.structureCount} constructed backbones · 270 residues / structure · no dynamics`;
  }

  // Canvas click picking (distinguishes click from orbit drag)
  function bindCanvasPicking(canvas, spKey) {
    let downPos = null;
    canvas.addEventListener('pointerdown', (e) => {
      downPos = { x: e.clientX, y: e.clientY };
    });
    canvas.addEventListener('pointerup', (e) => {
      if (!downPos) return;
      const dist = Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y);
      downPos = null;
      if (dist > 5) return; // was an orbit drag
      const rect = canvas.getBoundingClientRect();
      const pixel=window.devicePixelRatio||1;
      const x=(e.clientX-rect.left)*(canvas.width/pixel)/Math.max(1,rect.width);
      const y=(e.clientY-rect.top)*(canvas.height/pixel)/Math.max(1,rect.height);
      const pts = state.screenPts[spKey] || [];
      let best = null;
      let bestDist = 18; // hit radius in CSS pixels
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        const d2 = Math.hypot(p.x - x, p.y - y);
        if (d2 < bestDist || (Math.abs(d2 - bestDist) < 1.5 && best && p.depth > best.depth)) {
          bestDist = d2;
          best = p;
        }
      }
      if (best) {
        selectResidue(best.chain, best.res, false);
      }
    });
  }

  bindCanvasPicking(canvasBeaver, 'beaver');
  bindCanvasPicking(canvasHuman, 'human');

  // Bind primary controls
  for (const id of ['speciesWindow', 'speciesOrder', 'speciesLength']) {
    const el = $(id);
    if (el) el.addEventListener('input', render);
  }
  const rotEl = $('speciesRotation');
  if (rotEl) {
    rotEl.addEventListener('input', () => {
      renderCanvases();
    });
  }

  // Bind residue selector controls
  const chainSel = $('speciesChainSelect');
  if (chainSel) {
    chainSel.addEventListener('change', () => {
      selectResidue(+chainSel.value, state.selectedRes, false);
    });
  }
  const resSel = $('speciesResidueSelect');
  if (resSel) {
    resSel.addEventListener('change', () => {
      selectResidue(state.selectedChain, +resSel.value, true);
    });
  }
  const prevBtn = $('speciesPrevMismatch');
  const nextBtn = $('speciesNextMismatch');
  function stepMismatch(dir) {
    const { tasks } = getCurrentContext();
    const list = [];
    for (let c = 0; c < 3; c++) {
      for (let r = 0; r < 90; r++) {
        if (isMismatch(tasks, c, r)) list.push({ c, r });
      }
    }
    if (!list.length) return;
    let curIdx = list.findIndex((m) => m.c === state.selectedChain && m.r === state.selectedRes);
    if (curIdx === -1) {
      curIdx = dir > 0 ? 0 : list.length - 1;
    } else {
      curIdx = (curIdx + dir + list.length) % list.length;
    }
    selectResidue(list[curIdx].c, list[curIdx].r, true);
  }
  if (prevBtn) prevBtn.addEventListener('click', () => stepMismatch(-1));
  if (nextBtn) nextBtn.addEventListener('click', () => stepMismatch(1));

  const showMmEl = $('speciesShowMismatches');
  if (showMmEl) {
    showMmEl.addEventListener('change', () => {
      state.showMismatches = showMmEl.checked;
      renderCanvases();
    });
  }

  // Bind illustrative bend controls
  const bendEl = $('speciesBendAngle');
  if (bendEl) {
    bendEl.addEventListener('input', () => {
      state.bendDeg = +bendEl.value;
      renderCanvases();
    });
  }
  const bendPlaneEl = $('speciesBendPlane');
  if (bendPlaneEl) {
    bendPlaneEl.addEventListener('change', () => {
      state.bendPlane = bendPlaneEl.value;
      renderCanvases();
    });
  }
  const ghostEl = $('speciesBendGhost');
  if (ghostEl) {
    ghostEl.addEventListener('change', () => {
      state.showGhost = ghostEl.checked;
      renderCanvases();
    });
  }
  const bendResetBtn = $('speciesBendReset');
  if (bendResetBtn) {
    bendResetBtn.addEventListener('click', () => {
      state.bendDeg = 0;
      if (bendEl) bendEl.value = '0';
      renderCanvases();
    });
  }
  const fullResetBtn = $('speciesResetAll');
  if (fullResetBtn) {
    fullResetBtn.addEventListener('click', () => {
      state.bendDeg = 0;
      if (bendEl) bendEl.value = '0';
      if (rotEl) rotEl.value = '30';
      if (camera) camera.reset();
      renderCanvases();
    });
  }

  let timer;
  window.addEventListener('resize', () => {
    clearTimeout(timer);
    timer = setTimeout(renderCanvases, 80);
  });

  // Select first mismatch in N-112 by default (Chain C res 45) or Chain A res 1
  const initial=getCurrentContext();let first={c:0,r:0};outer:for(let c=0;c<3;c++)for(let r=0;r<initial.n;r++)if(isMismatch(initial.tasks,c,r)){first={c,r};break outer;}selectResidue(first.c,first.r,false);
})();
