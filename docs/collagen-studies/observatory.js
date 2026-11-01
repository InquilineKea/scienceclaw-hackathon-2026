const readableLabel=v=>v&&typeof v==='object'?Object.entries(v).map(([k,x])=>`${k}: ${x}`).join(' · '):String(v??'');
import { createSpatialViewer } from './spatial-viewer.js?v=20261101-r3g';

const PALETTE = ['#0d9488', '#d97706', '#2563eb', '#9333ea', '#e11d48', '#059669', '#4f46e5', '#b45309'];
const PAGE_SIZE = 50;
const MAX_PLOT_PTS = 2000;

const state = {
  catalog: [],
  search: '',
  category: 'all',
  studyMeta: null,
  studyData: null,
  abortCtrl: null,
  tableIdx: 0,
  recordIdx: 0,
  page: 0,
  xCol: '',
  yCol: '',
  colorCol: '',
  filterVal: '__all__',
  qualFilter: 'all',
  logX: false,
  logY: false,
  connectLine: false,
  compareMode: false,
  panes: [
    { viewer: null, modelIdx: 0, frameIdx: 0, lastKey: '' },
    { viewer: null, modelIdx: 0, frameIdx: 0, lastKey: '' }
  ]
};

const el = (id) => document.getElementById(id);
const announce = (msg) => { const n = el('live-status'); if (n) n.textContent = msg; };

function safeHttpsUrl(raw) {
  if (!raw || typeof raw !== 'string') return null;
  try {
    const u = new URL(raw, window.location.href);
    if (u.protocol === 'https:' || u.protocol === 'http:') return u.href;
  } catch { /* ignore */ }
  return null;
}

function safeRelativeUrl(raw) {
  if (!raw || typeof raw !== 'string') return null;
  const cleaned = raw.startsWith('/') ? '.' + raw : raw;
  try {
    const u = new URL(cleaned, document.baseURI);
    if (u.origin === window.location.origin) return u.href;
  } catch { /* ignore */ }
  return null;
}

function formatVal(v) {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return Number.isFinite(v) ? (Math.abs(v) >= 1e4 || (Math.abs(v) > 0 && Math.abs(v) < 1e-3) ? v.toExponential(4) : String(Number(v.toPrecision(6)))) : String(v);
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

function readUrlParams() {
  const p = new URLSearchParams(window.location.search);
  return {
    study: p.get('study') || '',
    table: p.get('table') || '',
    record: p.has('record') ? parseInt(p.get('record'), 10) : 0
  };
}

function syncUrlParams() {
  if (!state.studyMeta) return;
  const p = new URLSearchParams();
  p.set('study', state.studyMeta.id);
  const tbl = getCurrentTable();
  if (tbl && tbl.id) p.set('table', tbl.id);
  p.set('record', String(state.recordIdx));
  const hash = window.location.hash || '';
  window.history.replaceState(null, '', `${window.location.pathname}?${p.toString()}${hash}`);
}

function getCurrentTable() {
  const tables = state.studyData?.tables;
  if (!Array.isArray(tables) || !tables.length) return null;
  return tables[state.tableIdx] || tables[0];
}

function isRowQualified(row) {
 const q=getCurrentTable()?.qualification;if(!q)return true;
 const yes=v=>v===true||v===1||v==='true'||v==='True';
 if(q.mode==='all_true')return q.columns.every(k=>yes(row[k]));
 return (q.passValues||[true]).includes(row[q.field]);
}
function tableHasQualification(tbl){return Boolean(tbl?.qualification);}

async function init() {
  bindStaticControls();
  await loadCatalog();
}

function bindStaticControls() {
  el('study-search').addEventListener('input', (e) => {
    state.search = e.target.value.trim().toLowerCase();
    renderSidebar();
  });
  el('retry-btn').addEventListener('click', () => {
    if (state.studyMeta) selectStudy(state.studyMeta.id);
    else loadCatalog();
  });
  el('toggle-compare-btn').addEventListener('click', () => {
    state.compareMode = !state.compareMode;
    el('toggle-compare-btn').setAttribute('aria-pressed', String(state.compareMode));
    el('pane-right').hidden = !state.compareMode;
    el('sync-cam-btn').hidden = !state.compareMode;
    el('spatial-stage-grid').classList.toggle('compare-active', state.compareMode);
    updateSpatialStage(true);
    state.panes.forEach((p) => p.viewer?.resize?.());
  });
  el('sync-cam-btn').addEventListener('click', () => {
    const v0 = state.panes[0].viewer;
    const v1 = state.panes[1].viewer;
    if (v0?.getView && v1?.setView) {
      v1.setView(v0.getView());
      announce('Copied left camera orientation to right viewer.');
    }
  });

  [0, 1].forEach((paneIdx) => {
    const paneEl = el(paneIdx === 0 ? 'pane-left' : 'pane-right');
    el(`model-select-${paneIdx}`).addEventListener('change', (e) => {
      state.panes[paneIdx].modelIdx = parseInt(e.target.value, 10) || 0;
      state.panes[paneIdx].frameIdx = 0;
      renderPaneModel(paneIdx, true);
    });
    el(`node-select-${paneIdx}`).addEventListener('change', (e) => {
      const idx = parseInt(e.target.value, 10);
      if (!Number.isNaN(idx) && idx >= 0) {
        state.panes[paneIdx].viewer?.selectNode?.(idx);
        showNodeReadout(paneIdx, idx);
      }
    });
    paneEl.querySelectorAll('[data-preset]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.panes[paneIdx].viewer?.setPreset?.(btn.dataset.preset);
      });
    });
    const fBar = el(`frame-bar-${paneIdx}`);
    const slider = fBar.querySelector('.frame-slider');
    fBar.querySelector('.frame-prev').addEventListener('click', () => {
      setPaneFrame(paneIdx, state.panes[paneIdx].frameIdx - 1);
    });
    fBar.querySelector('.frame-next').addEventListener('click', () => {
      setPaneFrame(paneIdx, state.panes[paneIdx].frameIdx + 1);
    });
    slider.addEventListener('input', (e) => {
      setPaneFrame(paneIdx, parseInt(e.target.value, 10) || 0);
    });
  });

  el('table-select').addEventListener('change', (e) => {
    state.tableIdx = parseInt(e.target.value, 10) || 0;
    state.recordIdx = 0;
    state.page = 0;
    initTableColumns();
    renderAllDataViews();
    updateSpatialBindingOnRowSelect();
    syncUrlParams();
  });
  el('x-col-select').addEventListener('change', (e) => { state.xCol = e.target.value; renderPlot(); });
  el('y-col-select').addEventListener('change', (e) => { state.yCol = e.target.value; renderPlot(); });
  el('color-col-select').addEventListener('change', (e) => {
    state.colorCol = e.target.value;
    state.filterVal = '__all__';
    populateFilterValues();
    renderPlot();
  });
  el('filter-val-select').addEventListener('change', (e) => { state.filterVal = e.target.value; renderPlot(); });
  el('qual-filter-select').addEventListener('change', (e) => { state.qualFilter = e.target.value; renderPlot(); });
  el('log-x-chk').addEventListener('change', (e) => { state.logX = e.target.checked; renderPlot(); });
  el('log-y-chk').addEventListener('change', (e) => { state.logY = e.target.checked; renderPlot(); });
  el('connect-line-chk').addEventListener('change', (e) => { state.connectLine = e.target.checked; renderPlot(); });
  el('record-index-input').addEventListener('change', (e) => {
    const tbl = getCurrentTable();
    if (!tbl || !tbl.rows.length) return;
    const v = Math.max(0, Math.min(tbl.rows.length - 1, parseInt(e.target.value, 10) || 0));
    selectRecord(v);
  });
  el('page-prev-btn').addEventListener('click', () => {
    if (state.page > 0) { state.page--; renderRawTable(); }
  });
  el('page-next-btn').addEventListener('click', () => {
    const tbl = getCurrentTable();
    if (tbl && (state.page + 1) * PAGE_SIZE < tbl.rows.length) { state.page++; renderRawTable(); }
  });
  window.addEventListener('resize', () => state.panes.forEach((p) => p.viewer?.resize?.()));
}

async function loadCatalog() {
  const banner = el('catalog-status');
  banner.hidden = false;
  banner.textContent = 'Loading catalog.json...';
  el('error-banner').hidden = true;
  try {
    const res = await fetch(new URL('./catalog.json?v=20261101r3h', document.baseURI));
    if (!res.ok) throw new Error(`Catalog HTTP ${res.status}`);
    const data = await res.json();
    state.catalog = Array.isArray(data?.studies) ? data.studies : [];
    banner.hidden = true;
    renderCategoryPills();
    renderSidebar();
    const params = readUrlParams();
    const initial = state.catalog.find((s) => s.id === params.study) || state.catalog[0];
    if (initial) await selectStudy(initial.id, params.table, params.record);
  } catch (err) {
    banner.hidden = true;
    showError(`Failed to load study catalog: ${err.message}`);
  }
}

function renderCategoryPills() {
  const wrap = el('category-filters');
  wrap.replaceChildren();
  const cats = ['all', ...new Set(state.catalog.map((s) => s.category).filter(Boolean))];
  cats.forEach((cat) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'pill-btn';
    b.textContent = cat === 'all' ? 'All' : cat;
    b.setAttribute('aria-pressed', String(state.category === cat));
    b.addEventListener('click', () => {
      state.category = cat;
      renderCategoryPills();
      renderSidebar();
    });
    wrap.appendChild(b);
  });
}

function renderSidebar() {
  const nav = el('study-list');
  nav.replaceChildren();
  const filtered = state.catalog.filter((s) => {
    if (state.category !== 'all' && s.category !== state.category) return false;
    if (!state.search) return true;
    const hay = `${s.title} ${s.category} ${s.evidence} ${s.geometryType} ${s.summary || ''}`.toLowerCase();
    return hay.includes(state.search);
  });
  if (!filtered.length) {
    const p = document.createElement('p');
    p.className = 'subtitle';
    p.style.padding = '0.5rem';
    p.textContent = 'No matching studies.';
    nav.appendChild(p);
    return;
  }
  const byCat = new Map();
  filtered.forEach((s) => {
    const c = s.category || 'Uncategorized';
    if (!byCat.has(c)) byCat.set(c, []);
    byCat.get(c).push(s);
  });
  byCat.forEach((items, cat) => {
    const h = document.createElement('div');
    h.className = 'cat-heading';
    h.textContent = cat;
    nav.appendChild(h);
    items.forEach((s) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'study-item';
      btn.setAttribute('aria-current', String(state.studyMeta?.id === s.id));
      const title = document.createElement('span');
      title.className = 'study-item-title';
      title.textContent = s.title;
      const tags = document.createElement('div');
      tags.className = 'study-item-tags';
      if (s.evidence) {
        const t1 = document.createElement('span');
        t1.className = 'tag tag-ev';
        t1.textContent = s.evidence;
        tags.appendChild(t1);
      }
      if (s.geometryType) {
        const t2 = document.createElement('span');
        t2.className = 'tag tag-geo';
        t2.textContent = s.geometryType;
        tags.appendChild(t2);
      }
      btn.append(title, tags);
      btn.addEventListener('click', () => selectStudy(s.id));
      nav.appendChild(btn);
    });
  });
}

async function selectStudy(studyId, preferredTableId = '', preferredRecord = 0) {
  const meta = state.catalog.find((s) => s.id === studyId);
  if (!meta) return;
  if (state.abortCtrl) state.abortCtrl.abort();
  const ctrl = new AbortController();
  state.abortCtrl = ctrl;
  state.studyMeta = meta;
  renderSidebar();
  el('error-banner').hidden = true;
  el('study-title').textContent = `Loading ${meta.title}...`;

  try {
    const url = safeRelativeUrl(meta.dataURL);
    if (!url) throw new Error('Invalid local dataURL');
    const res = await fetch(url, { signal: ctrl.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (ctrl.signal.aborted) return;
    state.studyData = data;
    const tables = Array.isArray(data.tables) ? data.tables : [];
    const tIdx = preferredTableId ? Math.max(0, tables.findIndex((t) => t.id === preferredTableId)) : 0;
    state.tableIdx = tIdx >= 0 ? tIdx : 0;
    const rows = tables[state.tableIdx]?.rows || [];
    state.recordIdx = Number.isInteger(preferredRecord) && preferredRecord >= 0 && preferredRecord < rows.length ? preferredRecord : 0;
    state.page = Math.floor(state.recordIdx / PAGE_SIZE);
    state.panes[0].modelIdx = 0;
    state.panes[0].frameIdx = 0;
    state.panes[0].lastKey = '';
    state.panes[1].modelIdx = Math.min(1, Math.max(0, (data.models?.length || 1) - 1));
    state.panes[1].frameIdx = 0;
    state.panes[1].lastKey = '';

    renderStudyHeader();
    initSpatialControls();
    initTableSelector();
    initTableColumns();
    renderAllDataViews();
    if(data.views?.[0]&&(!preferredTableId||data.views[0].table===preferredTableId))applyCuratedView(data.views[0]);
    updateSpatialStage(true);
    syncUrlParams();
    announce(`Loaded study ${data.title || meta.title}`);
  } catch (err) {
    if (err.name === 'AbortError') return;
    showError(`Could not load study data (${meta.title}): ${err.message}`);
  }
}

function showError(msg) {
  const b = el('error-banner');
  b.hidden = false;
  el('error-message').textContent = msg;
  announce(msg);
}

function renderStudyHeader() {
  const m = state.studyMeta;
  const d = state.studyData;
  el('study-title').textContent = d.title || m.title;
  el('study-summary').textContent = m.summary || '';

  const badges = el('study-badges');
  badges.replaceChildren();
  [m.category, d.evidence || m.evidence, m.geometryType].filter(Boolean).forEach((txt, i) => {
    const s = document.createElement('span');
    s.className = i === 1 ? 'tag tag-ev' : i === 2 ? 'tag tag-geo' : 'tag';
    s.textContent = txt;
    badges.appendChild(s);
  });

  const links = el('study-links');
  links.replaceChildren();
  const repUrl = safeRelativeUrl(m.reportURL) || safeHttpsUrl(m.reportURL);
  if (repUrl) {
    const a = document.createElement('a');
    a.className = 'btn-link outline';
    a.href = repUrl;
    a.textContent = 'Original Report';
    links.appendChild(a);
  }
  const jsonUrl = safeRelativeUrl(m.dataURL);
  if (jsonUrl) {
    const a = document.createElement('a');
    a.className = 'btn-link';
    a.href = jsonUrl;
    a.setAttribute('download', `${m.id}.json`);
    a.textContent = 'Download Full JSON';
    links.appendChild(a);
  }

  const limUl = el('study-limitations');
  limUl.replaceChildren();
  const lims = Array.isArray(d.limitations) && d.limitations.length ? d.limitations : ['No study-specific limitations array archived.'];
  lims.forEach((l) => {
    const li = document.createElement('li');
    li.textContent = String(l);
    limUl.appendChild(li);
  });

  const uWrap = el('study-units');
  uWrap.replaceChildren();
  if (typeof d.units === 'string') {
    uWrap.textContent = d.units;
  } else if (d.units && typeof d.units === 'object') {
    Object.entries(d.units).forEach(([k, v]) => {
      const span = document.createElement('span');
      span.className = 'kv-item';
      const st = document.createElement('strong');
      st.textContent = `${k}: `;
      span.append(st, document.createTextNode(formatVal(v)));
      uWrap.appendChild(span);
    });
  } else {
    uWrap.textContent = 'See column labels';
  }

  const sWrap = el('study-sources');
  sWrap.replaceChildren();
  const urls = Array.isArray(d.sourceURLs) ? d.sourceURLs : [];
  urls.forEach((raw, idx) => {
    const safe = safeHttpsUrl(raw) || safeRelativeUrl(raw);
    if (!safe) return;
    const a = document.createElement('a');
    a.href = safe;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.textContent = `Source [${idx + 1}]`;
    a.title = safe;
    sWrap.appendChild(a);
  });
}

function initSpatialControls() {
  const models = Array.isArray(state.studyData?.models) ? state.studyData.models : [];
  const hasModels = models.length > 0;
  el('spatial-empty').hidden = hasModels;
  el('spatial-stage-grid').hidden = !hasModels;
  el('toggle-compare-btn').disabled = !hasModels;

  [0, 1].forEach((paneIdx) => {
    const sel = el(`model-select-${paneIdx}`);
    sel.replaceChildren();
    models.forEach((mdl, idx) => {
      const opt = document.createElement('option');
      opt.value = String(idx);
      const bTag = mdl.recordBinding && !mdl.recordBinding.type ? ' [Saved matching case]' : ' [Fixed reference/example]';
      opt.textContent = `${mdl.label || mdl.id || 'Model ' + (idx + 1)}${bTag}`;
      sel.appendChild(opt);
    });
    sel.value = String(state.panes[paneIdx].modelIdx);
  });
}

function findBoundModelIndexForRow(row) {
  const models = Array.isArray(state.studyData?.models) ? state.studyData.models : [];
  if (!row || !models.length) return -1;
  return models.findIndex((m) => {
    const rb = m.recordBinding;
    if (!rb || typeof rb !== 'object') return false;
    const keys = Object.keys(rb);
    if (!keys.length) return false;
    return keys.every((k) => k in row && String(row[k]) === String(rb[k]));
  });
}

function updateSpatialBindingOnRowSelect() {
  const models = Array.isArray(state.studyData?.models) ? state.studyData.models : [];
  const statusEl = el('spatial-binding-status');
  if (!models.length) {
    statusEl.textContent = 'No spatial coordinates archived for this study; use saved numeric plots below.';
    return;
  }
  const tbl = getCurrentTable();
  const row = tbl?.rows?.[state.recordIdx];
  const boundIdx = findBoundModelIndexForRow(row);
  if (boundIdx >= 0) {
    const mdl = models[boundIdx];
    statusEl.textContent = `Exact record-bound geometry active: ${mdl.label || mdl.id}`;
    if (state.panes[0].modelIdx !== boundIdx) {
      state.panes[0].modelIdx = boundIdx;
      state.panes[0].frameIdx = 0;
      el('model-select-0').value = String(boundIdx);
      renderPaneModel(0, false);
    }
  } else {
    const cur = models[state.panes[0].modelIdx] || models[0];
    statusEl.textContent = `Scalar record #${state.recordIdx} selected; spatial example remains ${cur.label || cur.id} (fixed/unbound).`;
  }
}

function updateSpatialStage(forceRender = false) {
  const models = Array.isArray(state.studyData?.models) ? state.studyData.models : [];
  if (!models.length) return;
  updateSpatialBindingOnRowSelect();
  renderPaneModel(0, forceRender);
  if (state.compareMode) renderPaneModel(1, forceRender);
}

function setPaneFrame(paneIdx, nextFrameIdx) {
  const models = state.studyData?.models || [];
  const mdl = models[state.panes[paneIdx].modelIdx];
  const frames = Array.isArray(mdl?.frames) ? mdl.frames : [];
  if (!frames.length) return;
  const clamped = Math.max(0, Math.min(frames.length - 1, nextFrameIdx));
  state.panes[paneIdx].frameIdx = clamped;
  renderPaneModel(paneIdx, true);
}

function buildEffectiveModel(mdl, frameIdx) {
  const frames = Array.isArray(mdl.frames) ? mdl.frames : [];
  if (!frames.length) return mdl;
  const f = frames[frameIdx] || frames[0];
  return {
    ...mdl,
    nodes: f.nodes || mdl.nodes,
    edges: f.edges ?? mdl.edges,
    forces: Object.hasOwn(f,'forces') ? f.forces : mdl.forces
  };
}

function ensureViewer(paneIdx) {
  const pane = state.panes[paneIdx];
  if (pane.viewer) return pane.viewer;
  const host = el(`canvas-host-${paneIdx}`);
  try {
    pane.viewer = createSpatialViewer(host, {
      onPick: (pick) => {
        if (!pick || pick.type==='edge') return;
        const idx = typeof pick.index === 'number' ? pick.index : (typeof pick.nodeIndex === 'number' ? pick.nodeIndex : -1);
        if (idx >= 0) {
          el(`node-select-${paneIdx}`).value = String(idx);
          showNodeReadout(paneIdx, idx, pick);
        }
      }
    });
  } catch (err) {
    host.textContent = `3D viewer unavailable (${err.message}); use accessible coordinate table below.`;
  }
  return pane.viewer;
}

function renderPaneModel(paneIdx, forceRender = false) {
  const models = Array.isArray(state.studyData?.models) ? state.studyData.models : [];
  const pane = state.panes[paneIdx];
  const mdl = models[pane.modelIdx] || models[0];
  if (!mdl) return;

  const frames = Array.isArray(mdl.frames) ? mdl.frames : [];
  const fBar = el(`frame-bar-${paneIdx}`);
  if (frames.length > 1) {
    fBar.hidden = false;
    const slider = fBar.querySelector('.frame-slider');
    slider.max = String(frames.length - 1);
    slider.value = String(pane.frameIdx);
    const fObj = frames[pane.frameIdx] || {};
    const fLbl = fObj.label || fObj.step || `${pane.frameIdx + 1}/${frames.length}`;
    fBar.querySelector('.frame-label').textContent = `Frame ${pane.frameIdx + 1}/${frames.length} (${fLbl})`;
  } else {
    fBar.hidden = true;
  }

  const eff = buildEffectiveModel(mdl, pane.frameIdx);
  const nodes = Array.isArray(eff.nodes) ? eff.nodes : [];
  const edges = Array.isArray(eff.edges) ? eff.edges : [];

  el(`model-meta-${paneIdx}`).textContent = `${mdl.type || 'Geometry'} · ${nodes.length} nodes · ${edges.length} edges`;

  const nodeSel = el(`node-select-${paneIdx}`);
  nodeSel.replaceChildren();
  nodes.forEach((n, idx) => {
    const opt = document.createElement('option');
    opt.value = String(idx);
    const lbl = (n && typeof n === 'object' && (n.label || n.id)) ? `${n.label || n.id} (#${idx})` : `${readableLabel(mdl.labels?.[idx]) || "Node #"+idx}`;
    opt.textContent = lbl;
    nodeSel.appendChild(opt);
  });

  const key = `${state.studyMeta?.id}:${pane.modelIdx}:${pane.frameIdx}`;
  const viewer = ensureViewer(paneIdx);
  if (viewer && (forceRender || pane.lastKey !== key)) {
    pane.lastKey = key;
    const oldView=viewer.getView?.();const sameModel=pane.previousModel===mdl.id;viewer.setModel?.(eff);if(sameModel&&oldView)viewer.setView?.(oldView);pane.previousModel=mdl.id;
  }

  if (paneIdx === 0) {
    renderGeometryFallbackTable(eff);
    if (nodes.length > 0) {
      showNodeReadout(0, 0);
    } else {
      el('node-readout').textContent = 'Model contains no explicit node array.';
    }
  }
}

function getNodeCoords(n) {
  if (Array.isArray(n)) return [n[0] ?? 0, n[1] ?? 0, n[2] ?? 0];
  if (n && typeof n === 'object') {
    if (Array.isArray(n.pos)) return [n.pos[0] ?? 0, n.pos[1] ?? 0, n.pos[2] ?? 0];
    if (Array.isArray(n.position)) return [n.position[0] ?? 0, n.position[1] ?? 0, n.position[2] ?? 0];
    return [n.x ?? 0, n.y ?? 0, n.z ?? 0];
  }
  return [0, 0, 0];
}

function showNodeReadout(paneIdx, nodeIdx, pickInfo = null) {
  const models = Array.isArray(state.studyData?.models) ? state.studyData.models : [];
  const pane = state.panes[paneIdx];
  const mdl = models[pane.modelIdx] || models[0];
  const box = el('node-readout');
  if (!mdl) {
    box.textContent = 'No model active.';
    return;
  }
  const eff = buildEffectiveModel(mdl, pane.frameIdx);
  const nodes = Array.isArray(eff.nodes) ? eff.nodes : [];
  const n = nodes[nodeIdx];
  if (!n) {
    box.textContent = `Node #${nodeIdx} not found.`;
    return;
  }
  const [x, y, z] = getNodeCoords(n);
  box.replaceChildren();
  const title = document.createElement('strong');
  const paneTag = paneIdx === 0 ? 'Model A' : 'Model B';
  const nLabel=' ('+readableLabel(mdl.labels?.[nodeIdx]??n.label??nodeIdx)+')';
  title.textContent = `[${paneTag}] Node #${nodeIdx}${nLabel}: `;
  box.appendChild(title);

  const coordSpan = document.createElement('span');
  coordSpan.textContent = `x=${formatVal(x)}, y=${formatVal(y)}, z=${formatVal(z)}`;
  box.appendChild(coordSpan);

  if (Array.isArray(eff.forces) && eff.forces[nodeIdx]) {
    const [fx, fy, fz] = getNodeCoords(eff.forces[nodeIdx]);
    const fSpan = document.createElement('span');
    fSpan.textContent = ` | Force/Vec: (${formatVal(fx)}, ${formatVal(fy)}, ${formatVal(fz)})`;
    box.appendChild(fSpan);
  }
  if (n && typeof n === 'object' && !Array.isArray(n)) {
    const extra = Object.entries(n)
      .filter(([k]) => !['x', 'y', 'z', 'pos', 'position', 'id', 'label'].includes(k))
      .map(([k, v]) => `${k}=${formatVal(v)}`)
      .join(', ');
    if (extra) {
      const exSpan = document.createElement('span');
      exSpan.textContent = ` | ${extra}`;
      box.appendChild(exSpan);
    }
  }
  if (pickInfo && typeof pickInfo.edgeIndex === 'number' && pickInfo.edgeIndex >= 0) {
    const eSpan = document.createElement('span');
    eSpan.textContent = ` (Picked near Edge #${pickInfo.edgeIndex})`;
    box.appendChild(eSpan);
  }
}

function renderGeometryFallbackTable(effModel) {
  const tbl = el('geometry-fallback-table');
  if (!tbl) return;
  tbl.replaceChildren();
  const nodes = Array.isArray(effModel?.nodes) ? effModel.nodes : [];
  const edges = Array.isArray(effModel?.edges) ? effModel.edges : [];

  const thead = document.createElement('thead');
  const hr = document.createElement('tr');
  ['Node #', 'Label/Role', 'X', 'Y', 'Z', 'Connected Edges'].forEach((h) => {
    const th = document.createElement('th');
    th.textContent = h;
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  tbl.appendChild(thead);

  const adj = new Map();
  edges.forEach((e, eIdx) => {
    const u = Array.isArray(e) ? e[0] : (e?.source ?? e?.u ?? e?.from);
    const v = Array.isArray(e) ? e[1] : (e?.target ?? e?.v ?? e?.to);
    if (typeof u === 'number' && typeof v === 'number') {
      if (!adj.has(u)) adj.set(u, []);
      if (!adj.has(v)) adj.set(v, []);
      adj.get(u).push(`${v} (e${eIdx})`);
      adj.get(v).push(`${u} (e${eIdx})`);
    }
  });

  const tbody = document.createElement('tbody');
  const limit = Math.min(nodes.length, 200);
  for (let i = 0; i < limit; i++) {
    const n = nodes[i];
    const [x, y, z] = getNodeCoords(n);
    const tr = document.createElement('tr');
    const lbl = (n && typeof n === 'object' && !Array.isArray(n)) ? (n.label || n.role || n.id || '—') : '—';
    const conn = (adj.get(i) || []).slice(0, 6).join(', ') || '—';
    [String(i), String(lbl), formatVal(x), formatVal(y), formatVal(z), conn].forEach((val) => {
      const td = document.createElement('td');
      td.textContent = val;
      tr.appendChild(td);
    });
    tr.addEventListener('click', () => {
      el('node-select-0').value = String(i);
      state.panes[0].viewer?.selectNode?.(i);
      showNodeReadout(0, i);
    });
    tbody.appendChild(tr);
  }
  tbl.appendChild(tbody);
}

function renderCuratedViewsBar() {
  let bar = el('curated-views-bar');
  const views = Array.isArray(state.studyData?.views) ? state.studyData.views : [];
  if (!bar) {
    const plotCard = document.querySelector('.plot-card');
    if (!plotCard) return;
    bar = document.createElement('div');
    bar.id = 'curated-views-bar';
    bar.className = 'filter-pills';
    bar.style.marginBottom = '0.75rem';
    plotCard.insertBefore(bar, plotCard.firstChild);
  }
  bar.replaceChildren();
  if (!views.length) {
    bar.hidden = true;
    return;
  }
  bar.hidden = false;
  const lbl = document.createElement('span');
  lbl.style.fontSize = '0.8rem';
  lbl.style.fontWeight = '600';
  lbl.style.marginRight = '0.4rem';
  lbl.textContent = 'Curated Comparisons:';
  bar.appendChild(lbl);

  views.forEach((v) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pill-btn';
    btn.textContent = v.title || v.id || 'Preset';
    if (v.description) btn.title = v.description;
    btn.addEventListener('click', () => applyCuratedView(v));
    bar.appendChild(btn);
  });
}

function applyCuratedView(v) {
  if (!v || !state.studyData) return;
  const tables = Array.isArray(state.studyData.tables) ? state.studyData.tables : [];
  if (v.table) {
    const tIdx = tables.findIndex((t) => t.id === v.table);
    if (tIdx >= 0 && tIdx !== state.tableIdx) {
      state.tableIdx = tIdx;
      state.recordIdx = 0;
      state.page = 0;
      el('table-select').value = String(tIdx);
      initTableColumns();
    }
  }
  const cols = getTableColumns(getCurrentTable());
  if (v.x && cols.includes(v.x)) { state.xCol = v.x; el('x-col-select').value = v.x; }
  if (v.y && cols.includes(v.y)) { state.yCol = v.y; el('y-col-select').value = v.y; }
  if (v.color && cols.includes(v.color)) {
    state.colorCol = v.color;
    el('color-col-select').value = v.color;
    populateFilterValues();
  } else if (v.filterKey && cols.includes(v.filterKey)) {
    state.colorCol = v.filterKey;
    el('color-col-select').value = v.filterKey;
    populateFilterValues();
  }
  if (v.filterValue !== undefined && v.filterValue !== null && v.filterValue !== '') {
    state.filterVal = String(v.filterValue);
    el('filter-val-select').value = state.filterVal;
  } else {
    state.filterVal = '__all__';
    el('filter-val-select').value = '__all__';
  }
  renderAllDataViews();
  if (v.description) announce(`Applied view ${v.title}: ${v.description}`);
}

function initTableSelector() {
  renderCuratedViewsBar();
  const sel = el('table-select');
  sel.replaceChildren();
  const tables = Array.isArray(state.studyData?.tables) ? state.studyData.tables : [];
  tables.forEach((t, idx) => {
    const opt = document.createElement('option');
    opt.value = String(idx);
    const cnt = Array.isArray(t.rows) ? t.rows.length : 0;
    opt.textContent = `${t.label || t.title || t.id || 'Table ' + (idx + 1)} (${cnt} rows)`;
    sel.appendChild(opt);
  });
  sel.value = String(state.tableIdx);
}

function getTableColumns(tbl) {
  if (!tbl) return [];
  if (Array.isArray(tbl.columns) && tbl.columns.length) {
    return tbl.columns.map((c) => (typeof c === 'string' ? c : (c.key || c.id || c.name))).filter(Boolean);
  }
  const rows = Array.isArray(tbl.rows) ? tbl.rows : [];
  const set = new Set();
  rows.slice(0, 50).forEach((r) => {
    if (r && typeof r === 'object') Object.keys(r).forEach((k) => set.add(k));
  });
  return Array.from(set);
}

function isNumericColumn(rows, col) {
  for (let i = 0; i < rows.length; i++) {
    const v = rows[i]?.[col];
    if (typeof v === 'number' && Number.isFinite(v)) return true;
  }
  return false;
}

function initTableColumns() {
  const tbl = getCurrentTable();
  const rows = Array.isArray(tbl?.rows) ? tbl.rows : [];
  const cols = getTableColumns(tbl);
  const numCols = cols.filter((c) => isNumericColumn(rows, c));
  const xCandidates = cols;
  const yCandidates = numCols.length ? numCols : cols;

  state.xCol = xCandidates[0] || '';
  state.yCol = yCandidates[1] || yCandidates[0] || '';
  const catCols = cols.filter((c) => !numCols.includes(c));
  state.colorCol = catCols[0] || '';
  state.filterVal = '__all__';
  state.qualFilter = 'all';
  state.logX = false;
  state.logY = false;
  el('log-x-chk').checked = false;
  el('log-y-chk').checked = false;

  const fillSelect = (id, list, includeNone = false) => {
    const s = el(id);
    s.replaceChildren();
    if (includeNone) {
      const o = document.createElement('option');
      o.value = '';
      o.textContent = 'None';
      s.appendChild(o);
    }
    list.forEach((c) => {
      const o = document.createElement('option');
      o.value = c;
      o.textContent = c;
      s.appendChild(o);
    });
  };

  fillSelect('x-col-select', xCandidates);
  fillSelect('y-col-select', yCandidates);
  fillSelect('color-col-select', cols, true);

  el('x-col-select').value = state.xCol;
  el('y-col-select').value = state.yCol;
  el('color-col-select').value = state.colorCol;

  const hasQual = tableHasQualification(tbl);
  el('qual-filter-wrap').hidden = !hasQual;
  el('qual-filter-select').value = 'all';

  populateFilterValues();
}

function populateFilterValues() {
  const sel = el('filter-val-select');
  sel.replaceChildren();
  const allOpt = document.createElement('option');
  allOpt.value = '__all__';
  allOpt.textContent = 'All Values';
  sel.appendChild(allOpt);

  const tbl = getCurrentTable();
  const rows = Array.isArray(tbl?.rows) ? tbl.rows : [];
  if (!state.colorCol || !rows.length) return;

  const vals = new Set();
  rows.forEach((r) => {
    const v = r?.[state.colorCol];
    if (v !== undefined && v !== null) vals.add(String(v));
  });
  Array.from(vals).slice(0, 100).forEach((v) => {
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = v;
    sel.appendChild(opt);
  });
  sel.value = state.filterVal;
}

function selectRecord(rowIdx) {
  const tbl = getCurrentTable();
  const rows = Array.isArray(tbl?.rows) ? tbl.rows : [];
  if (!rows.length) return;
  state.recordIdx = Math.max(0, Math.min(rows.length - 1, rowIdx));
  state.page = Math.floor(state.recordIdx / PAGE_SIZE);
  el('record-index-input').value = String(state.recordIdx);
  renderRecordInspector();
  renderPlot();
  renderRawTable();
  updateSpatialBindingOnRowSelect();
  syncUrlParams();
}

function renderAllDataViews() {
  const tbl = getCurrentTable();
  const rows = Array.isArray(tbl?.rows) ? tbl.rows : [];
  const recIn = el('record-index-input');
  recIn.max = String(Math.max(0, rows.length - 1));
  recIn.value = String(state.recordIdx);
  renderPlot();
  renderRecordInspector();
  renderRawTable();
}

function renderPlot() {
  const svg = el('scatter-svg');
  const legend = el('legend-bar');
  const warnEl = el('plot-warnings');
  const countEl = el('plot-counts');
  svg.replaceChildren();
  legend.replaceChildren();
  warnEl.textContent = '';

  const tbl = getCurrentTable();
  const rows = Array.isArray(tbl?.rows) ? tbl.rows : [];
  if (!rows.length || !state.xCol || !state.yCol) {
    countEl.textContent = '0 records';
    return;
  }

  const categoricalX=!isNumericColumn(rows,state.xCol);
  const categories=categoricalX?[...new Set(rows.map(r=>String(r[state.xCol]??'Missing')))]:[];
  if(categoricalX){state.logX=false;el('log-x-chk').checked=false;}
  let matrix=document.getElementById('categorical-record-cards');
  if(!matrix){matrix=document.createElement('div');matrix.id='categorical-record-cards';svg.before(matrix);}
  matrix.replaceChildren();
  const matrixMode=rows.length>0&&!isNumericColumn(rows,state.yCol);
  matrix.hidden=!matrixMode;svg.hidden=matrixMode;
  if(matrixMode){for(const row of rows.slice(0,50)){const card=document.createElement('article');card.className='evidence-record-card';for(const [k,v] of Object.entries(row)){const line=document.createElement('p');const key=document.createElement('strong');key.textContent=k+': ';line.append(key,document.createTextNode(formatVal(v)));card.append(line);}matrix.append(card);}countEl.textContent=`${rows.length} saved categorical records · evidence matrix (no numeric axis implied)`;return;}
  let omittedNonPos = 0;
  let omittedNonFinite = 0;
  const validPts = [];

  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (state.qualFilter === 'accepted' && !isRowQualified(r)) continue;
    if (state.colorCol && state.filterVal !== '__all__') {
      if (String(r?.[state.colorCol]) !== state.filterVal) continue;
    }
    const numeric=v=>v===null||v===undefined||v===''?NaN:Number(v);
    const rawX=categoricalX?categories.indexOf(String(r[state.xCol]??'Missing')):numeric(r[state.xCol]);
    const rawY=numeric(r[state.yCol]);
    if (!Number.isFinite(rawX) || !Number.isFinite(rawY)) {
      omittedNonFinite++;
      continue;
    }
    if ((state.logX && rawX <= 0) || (state.logY && rawY <= 0)) {
      omittedNonPos++;
      continue;
    }
    const px = state.logX ? Math.log10(rawX) : rawX;
    const py = state.logY ? Math.log10(rawY) : rawY;
    const grp = state.colorCol ? String(r?.[state.colorCol] ?? '—') : 'All';
    const uncertainty=tbl.uncertainty;const sd=uncertainty?.y===state.yCol?Number(r[uncertainty.sd]):NaN;validPts.push({ idx: i, px, py, rawX, rawY, grp,sd });
  }

  let plottedPts = validPts;
  let thinned = false;
  if (validPts.length > MAX_PLOT_PTS) {
    thinned = true;
    const step = validPts.length / MAX_PLOT_PTS;
    const sampled = [];
    let hasSelected = false;
    for (let k = 0; k < MAX_PLOT_PTS; k++) {
      const pt = validPts[Math.floor(k * step)];
      if (pt.idx === state.recordIdx) hasSelected = true;
      sampled.push(pt);
    }
    if (!hasSelected) {
      const selPt = validPts.find((p) => p.idx === state.recordIdx);
      if (selPt) sampled[sampled.length - 1] = selPt;
    }
    plottedPts = sampled;
  }

  countEl.textContent = `${plottedPts.length} plotted / ${validPts.length} finite filtered / ${rows.length} table rows`;
  const warns = [];
  if (omittedNonPos > 0) warns.push(`${omittedNonPos} non-positive row(s) omitted by log10 scale`);
  if (omittedNonFinite > 0) warns.push(`${omittedNonFinite} non-numeric row(s) skipped`);
  if (thinned) warns.push(`deterministic stride thinning applied (${MAX_PLOT_PTS} max)`);
  warnEl.textContent = warns.join(' · ');

  const ns = 'http://www.w3.org/2000/svg';
  const W = 680, H = 360, padL = 68, padR = 24, padT = 20, padB = 46;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  if (!plottedPts.length) {
    const txt = document.createElementNS(ns, 'text');
    txt.setAttribute('x', String(W / 2));
    txt.setAttribute('y', String(H / 2));
    txt.setAttribute('text-anchor', 'middle');
    txt.setAttribute('fill', '#64748b');
    txt.textContent = 'No finite records match current axis/filter settings.';
    svg.appendChild(txt);
    return;
  }

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (let i = 0; i < validPts.length; i++) {
    const p = validPts[i];
    if (p.px < minX) minX = p.px;
    if (p.px > maxX) maxX = p.px;
    if (p.py < minY) minY = p.py;
    if (p.py > maxY) maxY = p.py;
  }
  for(const p of validPts){if(Number.isFinite(p.sd)&&!state.logY){minY=Math.min(minY,p.rawY-p.sd);maxY=Math.max(maxY,p.rawY+p.sd);}}
  if (minX === maxX) { minX -= 1; maxX += 1; }
  if (minY === maxY) { minY -= 1; maxY += 1; }

  const sx = (v) => padL + ((v - minX) / (maxX - minX)) * plotW;
  const sy = (v) => padT + plotH - ((v - minY) / (maxY - minY)) * plotH;

  const gGrid = document.createElementNS(ns, 'g');
  const ticks = 5;
  for (let t = 0; t <= ticks; t++) {
    const frac = t / ticks;
    const vx = minX + frac * (maxX - minX);
    const vy = minY + frac * (maxY - minY);
    const cx = padL + frac * plotW;
    const cy = padT + plotH - frac * plotH;

    const lx = document.createElementNS(ns, 'line');
    lx.setAttribute('x1', String(cx)); lx.setAttribute('x2', String(cx));
    lx.setAttribute('y1', String(padT)); lx.setAttribute('y2', String(padT + plotH));
    lx.setAttribute('stroke', '#e2e8f0');
    gGrid.appendChild(lx);

    const tx = document.createElementNS(ns, 'text');
    tx.setAttribute('x', String(cx)); tx.setAttribute('y', String(padT + plotH + 16));
    tx.setAttribute('text-anchor', 'middle'); tx.setAttribute('font-size', '11'); tx.setAttribute('fill', '#475569');
    tx.textContent = categoricalX ? (categories[Math.round(vx)]||'').slice(0,22) : formatVal(vx);
    gGrid.appendChild(tx);

    const ly = document.createElementNS(ns, 'line');
    ly.setAttribute('x1', String(padL)); ly.setAttribute('x2', String(padL + plotW));
    ly.setAttribute('y1', String(cy)); ly.setAttribute('y2', String(cy));
    ly.setAttribute('stroke', '#e2e8f0');
    gGrid.appendChild(ly);

    const ty = document.createElementNS(ns, 'text');
    ty.setAttribute('x', String(padL - 8)); ty.setAttribute('y', String(cy + 4));
    ty.setAttribute('text-anchor', 'end'); ty.setAttribute('font-size', '11'); ty.setAttribute('fill', '#475569');
    ty.textContent = formatVal(vy);
    gGrid.appendChild(ty);
  }

  if (!state.logX && minX < 0 && maxX > 0) {
    const zx = sx(0);
    const zl = document.createElementNS(ns, 'line');
    zl.setAttribute('x1', String(zx)); zl.setAttribute('x2', String(zx));
    zl.setAttribute('y1', String(padT)); zl.setAttribute('y2', String(padT + plotH));
    zl.setAttribute('stroke', '#94a3b8'); zl.setAttribute('stroke-dasharray', '4,3');
    gGrid.appendChild(zl);
  }
  if (!state.logY && minY < 0 && maxY > 0) {
    const zy = sy(0);
    const zl = document.createElementNS(ns, 'line');
    zl.setAttribute('x1', String(padL)); zl.setAttribute('x2', String(padL + plotW));
    zl.setAttribute('y1', String(zy)); zl.setAttribute('y2', String(zy));
    zl.setAttribute('stroke', '#94a3b8'); zl.setAttribute('stroke-dasharray', '4,3');
    gGrid.appendChild(zl);
  }
  svg.appendChild(gGrid);

  const xLbl = document.createElementNS(ns, 'text');
  xLbl.setAttribute('x', String(padL + plotW / 2)); xLbl.setAttribute('y', String(H - 6));
  xLbl.setAttribute('text-anchor', 'middle'); xLbl.setAttribute('font-size', '12'); xLbl.setAttribute('font-weight', '600'); xLbl.setAttribute('fill', '#1e293b');
  xLbl.textContent = state.logX ? `log10(${state.xCol})` : state.xCol;
  svg.appendChild(xLbl);

  const yLbl = document.createElementNS(ns, 'text');
  yLbl.setAttribute('transform', `translate(16, ${padT + plotH / 2}) rotate(-90)`);
  yLbl.setAttribute('text-anchor', 'middle'); yLbl.setAttribute('font-size', '12'); yLbl.setAttribute('font-weight', '600'); yLbl.setAttribute('fill', '#1e293b');
  yLbl.textContent = state.logY ? `log10(${state.yCol})` : state.yCol;
  svg.appendChild(yLbl);

  const groups = Array.from(new Set(plottedPts.map((p) => p.grp)));
  const colorMap = new Map();
  groups.forEach((g, idx) => colorMap.set(g, PALETTE[idx % PALETTE.length]));

  if (state.connectLine && plottedPts.length > 1) {
    const gLines = document.createElementNS(ns, 'g');
    groups.forEach((grp) => {
      const sub = plottedPts.filter((p) => p.grp === grp).sort((a,b)=>tbl.preserveRowOrder?a.idx-b.idx:a.px-b.px);
      if (sub.length < 2) return;
      const poly = document.createElementNS(ns, 'polyline');
      poly.setAttribute('fill', 'none');
      poly.setAttribute('stroke', colorMap.get(grp));
      poly.setAttribute('stroke-width', '1.5');
      poly.setAttribute('opacity', '0.65');
      poly.setAttribute('points', sub.map((p) => `${sx(p.px).toFixed(1)},${sy(p.py).toFixed(1)}`).join(' '));
      gLines.appendChild(poly);
    });
    svg.appendChild(gLines);
  }

  if(tbl.uncertainty?.y===state.yCol&&!state.logY){const errorBars=document.createElementNS(ns,'g');errorBars.setAttribute('aria-label',tbl.uncertainty.label);for(const p of plottedPts){if(!Number.isFinite(p.sd))continue;const line=document.createElementNS(ns,'line');line.setAttribute('x1',sx(p.px));line.setAttribute('x2',sx(p.px));line.setAttribute('y1',sy(p.rawY-p.sd));line.setAttribute('y2',sy(p.rawY+p.sd));line.setAttribute('stroke',colorMap.get(p.grp));line.setAttribute('stroke-width','2');errorBars.append(line);}svg.append(errorBars);warnEl.textContent+=' · '+tbl.uncertainty.label;}
  const gPts = document.createElementNS(ns, 'g');
  let selectedPt = null;
  plottedPts.forEach((p) => {
    if (p.idx === state.recordIdx) { selectedPt = p; return; }
    const c = document.createElementNS(ns, 'circle');
    c.setAttribute('cx', sx(p.px).toFixed(1));
    c.setAttribute('cy', sy(p.py).toFixed(1));
    c.setAttribute('r', '3.5');
    c.setAttribute('fill', colorMap.get(p.grp));
    c.setAttribute('opacity', '0.8');
    c.style.cursor = 'pointer';
    const title = document.createElementNS(ns, 'title');
    title.textContent = `Row #${p.idx}: ${state.xCol}=${formatVal(p.rawX)}, ${state.yCol}=${formatVal(p.rawY)} (${p.grp})`;
    c.appendChild(title);
    c.setAttribute('tabindex','0');c.setAttribute('role','button');c.setAttribute('aria-label',title.textContent);
    c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectRecord(p.idx);}});
    c.addEventListener('click', () => selectRecord(p.idx));
    gPts.appendChild(c);
  });

  if (selectedPt) {
    const c = document.createElementNS(ns, 'circle');
    c.setAttribute('cx', sx(selectedPt.px).toFixed(1));
    c.setAttribute('cy', sy(selectedPt.py).toFixed(1));
    c.setAttribute('r', '6.5');
    c.setAttribute('fill', colorMap.get(selectedPt.grp));
    c.setAttribute('stroke', '#0f172a');
    c.setAttribute('stroke-width', '2');
    const title = document.createElementNS(ns, 'title');
    title.textContent = `SELECTED Row #${selectedPt.idx}: ${state.xCol}=${formatVal(selectedPt.rawX)}, ${state.yCol}=${formatVal(selectedPt.rawY)}`;
    c.appendChild(title);
    gPts.appendChild(c);
  }
  svg.appendChild(gPts);
  if(state.studyData?.defaultView?.plotKind==='histogram' && state.xCol==='bin_low' && state.yCol==='density'){
    const bars=document.createElementNS(ns,'g');bars.setAttribute('aria-label','Saved shared-bin density histograms');
    for(const p of plottedPts){const hi=Number(rows[p.idx].bin_high);if(!Number.isFinite(hi))continue;const rect=document.createElementNS(ns,'rect');rect.setAttribute('x',sx(p.px));rect.setAttribute('y',sy(p.py));rect.setAttribute('width',Math.max(1,sx(hi)-sx(p.px)));rect.setAttribute('height',Math.max(0,sy(Math.max(0,minY))-sy(p.py)));rect.setAttribute('fill',colorMap.get(p.grp));rect.setAttribute('opacity','.22');const title=document.createElementNS(ns,'title');title.textContent=`${p.grp}: [${p.rawX},${hi}] density=${p.rawY}`;rect.append(title);bars.append(rect);}svg.insertBefore(bars,gPts);warnEl.textContent+=' · Exact saved shared bins; density overlay, not a fitted distribution.';
  }


  groups.slice(0, 12).forEach((grp) => {
    const item = document.createElement('span');
    item.className = 'legend-item';
    const sw = document.createElement('span');
    sw.className = 'legend-swatch';
    sw.style.backgroundColor = colorMap.get(grp);
    item.append(sw, document.createTextNode(grp));
    legend.appendChild(item);
  });
}

function renderRecordInspector() {
  const box = el('record-readout');
  box.replaceChildren();
  const tbl = getCurrentTable();
  const row = tbl?.rows?.[state.recordIdx];
  if (!row || typeof row !== 'object') {
    box.textContent = 'No record available in this table.';
    return;
  }
  Object.entries(row).forEach(([k, v]) => {
    const div = document.createElement('div');
    div.className = 'kv-cell';
    const dt = document.createElement('span');
    dt.className = 'kv-key';
    dt.textContent = k;
    const dd = document.createElement('span');
    dd.className = 'kv-val';
    dd.textContent = formatVal(v);
    div.append(dt, dd);
    box.appendChild(div);
  });
}

function renderRawTable() {
  const tableEl = el('raw-data-table');
  tableEl.replaceChildren();
  const tbl = getCurrentTable();
  const rows = Array.isArray(tbl?.rows) ? tbl.rows : [];
  const cols = getTableColumns(tbl);

  const total = rows.length;
  const start = state.page * PAGE_SIZE;
  const end = Math.min(total, start + PAGE_SIZE);

  el('table-page-info').textContent = total ? `Showing ${start + 1}–${end} of ${total}` : 'Showing 0 of 0';
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  el('page-num-label').textContent = `Page ${state.page + 1} / ${totalPages}`;
  el('page-prev-btn').disabled = state.page <= 0;
  el('page-next-btn').disabled = end >= total;

  if (!total || !cols.length) return;

  const thead = document.createElement('thead');
  const hr = document.createElement('tr');
  const thIdx = document.createElement('th');
  thIdx.textContent = 'Row #';
  hr.appendChild(thIdx);
  cols.forEach((c) => {
    const th = document.createElement('th');
    th.textContent = c;
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  tableEl.appendChild(thead);

  const tbody = document.createElement('tbody');
  for (let i = start; i < end; i++) {
    const r = rows[i];
    const tr = document.createElement('tr');
    if (i === state.recordIdx) tr.className = 'selected-row';
    const tdIdx = document.createElement('td');
    tdIdx.textContent = String(i);
    tr.appendChild(tdIdx);
    cols.forEach((c) => {
      const td = document.createElement('td');
      td.textContent = formatVal(r?.[c]);
      tr.appendChild(td);
    });
    tr.addEventListener('click', () => selectRecord(i));
    tbody.appendChild(tr);
  }
  tableEl.appendChild(tbody);
}

init();
