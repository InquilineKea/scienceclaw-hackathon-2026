import { createSpatialViewer } from './explore/spatial-viewer.js?v=20261101-r3g';

const DATA_URL = './molecular-preview-data.json';
const FALLBACK_STUDIES = [
  { title: 'SNT Ligand Ensemble', href: './explore/?study=snt-ligand-ensemble' },
  { title: 'Hydroxylation Prestress', href: './explore/?study=hydroxylation-prestress' },
  { title: 'Four-Bead Calibration', href: './explore/?study=four-bead-calibration' }
];

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function safeHref(url) {
  const str = String(url || '').trim();
  if (str.startsWith('./') || str.startsWith('../') || str.startsWith('/') || str.startsWith('https://')) {
    return str;
  }
  return '#';
}

function classifyModel(m) {
  const hay = `${m.id || ''} ${m.label || ''} ${m.evidence || ''}`.toLowerCase();
  if (hay.includes('snt') || hay.includes('ligand') || hay.includes('inhibitor')) {
    return { tag: 'Small-Molecule Inhibitor (No Enzyme)', kind: 'inhibitor' };
  }
  if (hay.includes('bead') || hay.includes('coarse') || hay.includes('centroid')) {
    return { tag: 'Derived 4-Bead Centroid Mapping (From 9 C\u03b1 Groups)', kind: 'coarse' };
  }
  return { tag: 'Peptide / C\u03b1 & Central Ring Structure (Short Pilot)', kind: 'protein' };
}

function formatCoord(val) {
  const num = Number(val);
  return Number.isFinite(num) ? num.toFixed(3) : 'N/A';
}

function extractPosition(node) {
  if (!node) return ['N/A', 'N/A', 'N/A'];
  if(Array.isArray(node)&&node.length>=3)return node;
  if (Array.isArray(node.position) && node.position.length >= 3) return node.position;
  if (Array.isArray(node.coords) && node.coords.length >= 3) return node.coords;
  if (Array.isArray(node.xyz) && node.xyz.length >= 3) return node.xyz;
  if (node.x !== undefined && node.y !== undefined && node.z !== undefined) return [node.x, node.y, node.z];
  return ['N/A', 'N/A', 'N/A'];
}

function hasGenuineReference(model) {
  return Boolean(model && Array.isArray(model.referenceNodes) && model.referenceNodes.length > 0);
}

function mountBench() {
  const main = document.querySelector('main');
  if (!main || document.getElementById('snt-molecular-bench')) return;
  main.classList.add('mb-has-bench');

  const h1 = main.querySelector('h1');
  const bench = el('section', 'mb-bench');
  bench.id = 'snt-molecular-bench';
  bench.setAttribute('aria-label', '3D Molecular Inspection Bench');

  const header = el('div', 'mb-header');
  const titleRow = el('div', 'mb-title-row');
  const eyebrow = el('span', 'mb-eyebrow', 'From download to inspectable evidence');
  const title = el('h2', 'mb-title', '3D Molecular & Coarse-Grained Inspection Bench');
  const intro = el('p', 'mb-intro', 'Inspect saved coordinates directly in 3D before or alongside archive verification. Displays recorded SNT-5382 ligand conformations (without enzyme), short-pilot Hyp-peptide C\u03b1/ring coordinates, and derived 4-bead centroid mappings without runtime refitting or inferred biochemical potentials.');
  titleRow.append(eyebrow, title, intro);

  const studyNav = el('div', 'mb-study-links');
  studyNav.setAttribute('aria-label', 'Direct study explorers');
  header.append(titleRow, studyNav);

  const statusBanner = el('div', 'mb-status');
  statusBanner.hidden = true;

  const toolbar = el('div', 'mb-toolbar');

  const primaryGroup = el('div', 'mb-control-group');
  const primaryLabel = el('label', 'mb-label', 'Primary structure');
  primaryLabel.htmlFor = 'mb-select-primary';
  const primarySelect = el('select', 'mb-select');
  primarySelect.id = 'mb-select-primary';
  primaryGroup.append(primaryLabel, primarySelect);

  const refToggleWrap = el('label', 'mb-checkbox-label');
  const refCheckbox = el('input', 'mb-checkbox');
  refCheckbox.type = 'checkbox';
  refCheckbox.checked = true;
  const refText = el('span', '', 'Show saved initial/final overlay');
  refToggleWrap.append(refCheckbox, refText);

  const presetGroup = el('div', 'mb-btn-group');
  ['front', 'side', 'top', 'reset'].forEach((preset) => {
    const b = el('button', 'mb-btn mb-btn-quiet', preset.charAt(0).toUpperCase() + preset.slice(1));
    b.type = 'button';
    b.dataset.preset = preset;
    presetGroup.append(b);
  });

  const compareGroup = el('div', 'mb-control-group mb-compare-controls');
  const compareBtn = el('button', 'mb-btn', 'Compare Second View');
  compareBtn.type = 'button';
  compareBtn.setAttribute('aria-pressed', 'false');

  const secondaryLabel = el('label', 'mb-label mb-sr-only', 'Comparison structure');
  secondaryLabel.htmlFor = 'mb-select-secondary';
  const secondarySelect = el('select', 'mb-select');
  secondarySelect.id = 'mb-select-secondary';
  secondarySelect.hidden = true;

  const syncCamBtn = el('button', 'mb-btn mb-btn-quiet', 'Copy Camera 1\u21922');
  syncCamBtn.type = 'button';
  syncCamBtn.hidden = true;

  const reloadBtn = el('button', 'mb-btn mb-btn-quiet', 'Load saved structures');
  reloadBtn.type = 'button';
  reloadBtn.hidden = true;

  compareGroup.append(compareBtn, secondaryLabel, secondarySelect, syncCamBtn, reloadBtn);
  toolbar.append(primaryGroup, refToggleWrap, presetGroup, compareGroup);

  const stageGrid = el('div', 'mb-stage-grid');

  function createViewportCard(slotTitle, isSecondary) {
    const card = el('div', 'mb-viewport-card');
    if (isSecondary) card.hidden = true;

    const topBar = el('div', 'mb-viewport-bar');
    const badgeWrap = el('div', 'mb-badge-wrap');
    const slotBadge = el('span', 'mb-slot-label', slotTitle);
    const catBadge = el('span', 'mb-cat-badge', '');
    badgeWrap.append(slotBadge, catBadge);

    const fitNote = el('span', 'mb-fit-note', 'Independent camera auto-fit to model bounds (no shared world-scale lock)');
    topBar.append(badgeWrap, fitNote);

    const canvasHost = el('div', 'mb-canvas-host');
    const footerBar = el('div', 'mb-viewport-footer');
    const statsText = el('div', 'mb-stats', '');
    const modelLink = el('a', 'mb-model-link', 'Open model in study explorer \u2192');
    modelLink.hidden = true;
    footerBar.append(statsText, modelLink);

    card.append(topBar, canvasHost, footerBar);
    return { card, catBadge, canvasHost, statsText, modelLink };
  }

  const view1UI = createViewportCard('Primary Stage', false);
  const view2UI = createViewportCard('Comparison Stage (Auto-Fit Independently)', true);
  stageGrid.append(view1UI.card, view2UI.card);

  const infoGrid = el('div', 'mb-info-grid');

  const notePanel = el('div', 'mb-panel');
  const noteHeading = el('h3', 'mb-panel-title', 'Model Provenance & Scientific Scope');
  const noteBody = el('p', 'mb-note-body', 'Loading saved coordinate metadata\u2026');
  const metaList = el('dl', 'mb-meta-list');
  const legendBox = el('div', 'mb-legend');
  notePanel.append(noteHeading, noteBody, metaList, legendBox);

  const pickPanel = el('div', 'mb-panel');
  const pickHeading = el('h3', 'mb-panel-title', 'Selected Node Original Coordinates');
  const pickHint = el('p', 'mb-pick-hint', 'Click any atom, C\u03b1 node, or coarse bead in the 3D stage to inspect its unscaled original coordinates from the dataset.');
  const pickReadout = el('dl', 'mb-coord-grid');
  pickPanel.append(pickHeading, pickHint, pickReadout);

  infoGrid.append(notePanel, pickPanel);

  const limitsDetails = el('details', 'mb-limits');
  limitsDetails.open = true;
  const limitsSummary = el('summary', 'mb-limits-summary', 'Explicit Scientific Boundaries & Non-Claims (Always Preserved)');
  const limitsList = el('ul', 'mb-limits-list');
  limitsDetails.append(limitsSummary, limitsList);

  bench.append(header, statusBanner, toolbar, stageGrid, infoGrid, limitsDetails);

  if (h1 && h1.parentNode === main) {
    h1.insertAdjacentElement('afterend', bench);
  } else {
    main.prepend(bench);
  }

  const state = {
    data: null,
    models: [],
    primaryIdx: 0,
    secondaryIdx: 1,
    compareActive: false,
    showReference: true,
    viewer1: null,
    viewer2: null
  };

  function setStatus(msg, isError = false) {
    if (!msg) {
      statusBanner.hidden = true;
      statusBanner.textContent = '';
      statusBanner.classList.remove('mb-status-error');
      return;
    }
    statusBanner.hidden = false;
    statusBanner.textContent = msg;
    statusBanner.classList.toggle('mb-status-error', Boolean(isError));
  }

  function renderPickedNode(pick, sourceLabel, model) {
    if(pick?.type==='edge')return;
    pickReadout.replaceChildren();
    if (!pick || !model) {
      pickHint.hidden = false;
      return;
    }
    pickHint.hidden = true;
    const nodeObj = pick.node || (Array.isArray(model.nodes) && typeof pick.index === 'number' ? model.nodes[pick.index] : pick);
    const [x, y, z] = extractPosition(nodeObj);
    const units = model.units || '\u00c5';
    const nodeId = nodeObj?.id ?? nodeObj?.label ?? pick.id ?? pick.index ?? 'Selected';
    const groupName = nodeObj?.group ?? nodeObj?.element ?? nodeObj?.type ?? 'Recorded coordinate';

    const entries = [
      ['Stage / Model', `${sourceLabel}: ${model.label || model.id}`],
      ['Node / Label', String(nodeId)],
      ['Group / Role', String(groupName)],
      [`X (${units})`, formatCoord(x)],
      [`Y (${units})`, formatCoord(y)],
      [`Z (${units})`, formatCoord(z)]
    ];

    if (nodeObj?.refPosition || (hasGenuineReference(model) && typeof pick.index === 'number' && model.referenceNodes[pick.index])) {
      const refNode = nodeObj?.refPosition ? { position: nodeObj.refPosition } : model.referenceNodes[pick.index];
      const [rx, ry, rz] = extractPosition(refNode);
      entries.push(['Saved Ref (X, Y, Z)', `${formatCoord(rx)}, ${formatCoord(ry)}, ${formatCoord(rz)} ${units}`]);
    }

    entries.forEach(([k, v]) => {
      const dt = el('dt', '', k);
      const dd = el('dd', '', typeof v==='object'?JSON.stringify(v):v);
      pickReadout.append(dt, dd);
    });
  }

  function prepareModelPayload(model) {
    if (!model) return null;
    const copy = { ...model };
    if (!state.showReference || !hasGenuineReference(model)) {
      delete copy.referenceNodes;
    }
    return copy;
  }

  function resolveModelStudyLink(model) {
    const hay = `${model?.id || ''} ${model?.label || ''} ${model?.recordBinding || ''}`.toLowerCase();
    if (hay.includes('snt') || hay.includes('ligand')) return './explore/?study=snt-ligand-ensemble';
    if (hay.includes('bead') || hay.includes('coarse')) return './explore/?study=four-bead-calibration';
    if (hay.includes('hyp') || hay.includes('peptide') || hay.includes('hydrox')) return './explore/?study=hydroxylation-prestress';
    return '';
  }

  function updateViewportMeta(ui, model) {
    if (!model) return;
    const cls = classifyModel(model);
    ui.catBadge.textContent = cls.tag;
    ui.catBadge.dataset.kind = cls.kind;

    const nCount = Array.isArray(model.nodes) ? model.nodes.length : 0;
    const eCount = Array.isArray(model.edges) ? model.edges.length : 0;
    const units = model.units || '\u00c5';
    const refInfo = hasGenuineReference(model)
      ? (state.showReference ? ` \u00b7 Saved initial/final overlay (${model.referenceNodes.length} ref nodes)` : ' \u00b7 Saved overlay hidden')
      : ' \u00b7 Single saved coordinate state';
    ui.statsText.textContent = `${nCount} nodes / atoms \u00b7 ${eCount} edges / bonds \u00b7 Units: ${units}${refInfo}`;

    const linkHref = resolveModelStudyLink(model);
    if (linkHref) {
      ui.modelLink.href = safeHref(linkHref);
      ui.modelLink.hidden = false;
    } else {
      ui.modelLink.hidden = true;
    }
  }

  function updatePrimaryMetadata(model) {
    if (!model) return;
    noteBody.textContent = model.note || 'Inspectable 3D coordinate record loaded directly from published preview archive.';

    metaList.replaceChildren();
    const metaPairs = [
      ['Evidence Type', model.evidence || 'Saved 3D coordinate projection'],
      ['Coordinate Units', model.units || '\u00c5'],
      ['Record Binding', model.recordBinding || 'Direct archive coordinate record'],
      ['Water / Explicit Solvent', 'Not included in 3D projection (no false solvent rendering)'],
      ['Enzyme / LOXL2 Pocket', 'Not present; no docking, binding affinity, or equilibrium claim']
    ];
    metaPairs.forEach(([k, v]) => {
      const dt = el('dt', '', k);
      const dd = el('dd', '', typeof v==='object'?JSON.stringify(v):v);
      metaList.append(dt, dd);
    });

    legendBox.replaceChildren();
    const legendTitle = el('span', 'mb-legend-title', 'Groups & Coordinate Legend:');
    legendBox.append(legendTitle);

    const groups = Array.isArray(model.groups)?[...new Set(model.groups)].map(x=>[String(x),String(x)]):(model.groups&&typeof model.groups==='object'?Object.entries(model.groups):[]);
    if (groups.length > 0) {
      groups.forEach(([gKey, gVal]) => {
        const chip = el('span', 'mb-legend-chip');
        const dot = el('span', 'mb-legend-dot');
        const color = typeof gVal === 'string' ? gVal : gVal?.color;
        if (color && /^#[0-9a-fA-F]{3,8}$/.test(color)) {
          dot.style.backgroundColor = color;
        }
        const label = typeof gVal === 'object' && gVal !== null ? (gVal.label || gKey) : gKey;
        chip.append(dot, el('span', '', String(label)));
        legendBox.append(chip);
      });
    } else {
      legendBox.append(el('span', 'mb-legend-chip', 'Recorded atomic / C\u03b1 / bead positions'));
    }

    if (hasGenuineReference(model)) {
      legendBox.append(el('span', 'mb-legend-chip mb-legend-ref', 'Reference overlay: Saved initial vs. final coordinates'));
    }
  }

  function ensureViewer1() {
    if (state.viewer1) return state.viewer1;
    try {
      state.viewer1 = createSpatialViewer(view1UI.canvasHost, {
        onPick: (pick) => renderPickedNode(pick, 'Primary', state.models[state.primaryIdx])
      });
      return state.viewer1;
    } catch (err) {
      setStatus('WebGL 3D stage could not be initialized on this device. All original ZIP downloads, SHA-256 checksums, and study links below remain completely available.', true);
      return null;
    }
  }

  function ensureViewer2() {
    if (state.viewer2) return state.viewer2;
    try {
      state.viewer2 = createSpatialViewer(view2UI.canvasHost, {
        onPick: (pick) => renderPickedNode(pick, 'Comparison', state.models[state.secondaryIdx])
      });
      return state.viewer2;
    } catch (err) {
      setStatus('Secondary comparison WebGL view could not be initialized.', true);
      return null;
    }
  }

  function syncViews() {
    const m1 = state.models[state.primaryIdx];
    if (!m1) return;

    const hasRef1 = hasGenuineReference(m1);
    const m2 = state.models[state.secondaryIdx];
    const hasRef2 = state.compareActive && hasGenuineReference(m2);
    refCheckbox.disabled = !(hasRef1 || hasRef2);
    refToggleWrap.title = refCheckbox.disabled
      ? 'Selected structure does not include a second reference coordinate set'
      : 'Toggle saved initial/final reference coordinates';

    updateViewportMeta(view1UI, m1);
    updatePrimaryMetadata(m1);

    const v1 = ensureViewer1();
    if (v1 && typeof v1.setModel === 'function') {
      v1.setModel(prepareModelPayload(m1));
    }

    if (Array.isArray(m1.nodes) && m1.nodes.length > 0) {
      renderPickedNode({ node: m1.nodes[0], index: 0 }, 'Primary (Default node #0)', m1);
    }

    if (state.compareActive && m2) {
      view2UI.card.hidden = false;
      stageGrid.classList.add('mb-is-compare');
      updateViewportMeta(view2UI, m2);
      const v2 = ensureViewer2();
      if (v2 && typeof v2.setModel === 'function') {
        v2.setModel(prepareModelPayload(m2));
      }
      if (v1 && typeof v1.resize === 'function') v1.resize();
      if (v2 && typeof v2.resize === 'function') v2.resize();
    } else {
      view2UI.card.hidden = true;
      stageGrid.classList.remove('mb-is-compare');
      if (v1 && typeof v1.resize === 'function') v1.resize();
    }
  }

  function populateLinksAndLimits(data) {
    studyNav.replaceChildren();
    const links = Array.isArray(data?.links) && data.links.length > 0 ? data.links : FALLBACK_STUDIES;
    links.forEach((item) => {
      const a = el('a', 'mb-study-btn', item.title || 'Explore Study');
      a.href = safeHref(item.href);
      studyNav.append(a);
    });
    FALLBACK_STUDIES.forEach((fb) => {
      const exists = Array.from(studyNav.querySelectorAll('a')).some((a) => a.getAttribute('href') === fb.href);
      if (!exists) {
        const a = el('a', 'mb-study-btn', fb.title);
        a.href = fb.href;
        studyNav.append(a);
      }
    });

    limitsList.replaceChildren();
    const rawLimits = Array.isArray(data?.limits) ? data.limits : [];
    const mandatoryLimits = [
      'SNT-5382 coordinates show recorded ligand initial and final states in isolation (no LOXL2 enzyme, no binding pocket, no equilibrium or affinity claim).',
      'Hyp-peptide coordinates represent a short pilot C\u03b1 and central ring structure; explicit water is not included in this 3D projection.',
      'The 4-bead representation is a derived centroid mapping from 9 C\u03b1 groups, not a new atomistic force-field or runtime simulation.'
    ];
    const combined = [...rawLimits];
    mandatoryLimits.forEach((m) => {
      if (!combined.some((c) => String(c).toLowerCase().includes(m.slice(0, 22).toLowerCase()))) {
        combined.push(m);
      }
    });
    combined.forEach((txt) => {
      limitsList.append(el('li', '', String(txt)));
    });
  }

  async function loadPreviewData() {
    setStatus('Loading saved 3D coordinate records\u2026');
    reloadBtn.hidden = true;
    try {
      const res = await fetch(DATA_URL, { credentials: 'same-origin' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (!data || !Array.isArray(data.models) || data.models.length === 0) {
        throw new Error('No models found in preview JSON');
      }
      state.data = data;
      state.models = data.models;
      state.primaryIdx = 0;
      state.secondaryIdx = data.models.length > 1 ? 1 : 0;

      primarySelect.replaceChildren();
      secondarySelect.replaceChildren();
      data.models.forEach((m, idx) => {
        const label = m.label || m.id || `Structure ${idx + 1}`;
        primarySelect.append(new Option(label, String(idx), idx === state.primaryIdx, idx === state.primaryIdx));
        secondarySelect.append(new Option(label, String(idx), idx === state.secondaryIdx, idx === state.secondaryIdx));
      });

      populateLinksAndLimits(data);
      setStatus('');
      syncViews();
    } catch (err) {
      populateLinksAndLimits(null);
      reloadBtn.hidden = false;
      setStatus('Could not load ./molecular-preview-data.json (' + (err?.message || 'fetch error') + '). You can retry with "Load saved structures" or use the original ZIP downloads and checksums below.', true);
    }
  }

  primarySelect.addEventListener('change', () => {
    state.primaryIdx = Number(primarySelect.value) || 0;
    syncViews();
  });

  secondarySelect.addEventListener('change', () => {
    state.secondaryIdx = Number(secondarySelect.value) || 0;
    syncViews();
  });

  refCheckbox.addEventListener('change', () => {
    state.showReference = Boolean(refCheckbox.checked);
    syncViews();
  });

  presetGroup.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-preset]');
    if (!btn) return;
    const preset = ({front:'xy',side:'yz',top:'xz',reset:'fit'})[btn.dataset.preset]||'iso';
    if (state.viewer1 && typeof state.viewer1.setPreset === 'function') {
      state.viewer1.setPreset(preset);
    }
    if (state.compareActive && state.viewer2 && typeof state.viewer2.setPreset === 'function') {
      state.viewer2.setPreset(preset);
    }
  });

  compareBtn.addEventListener('click', () => {
    state.compareActive = !state.compareActive;
    compareBtn.setAttribute('aria-pressed', String(state.compareActive));
    compareBtn.textContent = state.compareActive ? 'Close Comparison View' : 'Compare Second View';
    secondarySelect.hidden = !state.compareActive;
    syncCamBtn.hidden = !state.compareActive;
    syncViews();
  });

  syncCamBtn.addEventListener('click', () => {
    if (state.viewer1 && state.viewer2 && typeof state.viewer1.getView === 'function' && typeof state.viewer2.setView === 'function') {
      const camState = state.viewer1.getView();
      if (camState) state.viewer2.setView(camState);
    }
  });

  reloadBtn.addEventListener('click', () => {
    loadPreviewData();
  });

  window.addEventListener('resize', () => {
    if (state.viewer1 && typeof state.viewer1.resize === 'function') state.viewer1.resize();
    if (state.compareActive && state.viewer2 && typeof state.viewer2.resize === 'function') state.viewer2.resize();
  });

  populateLinksAndLimits(null);
  loadPreviewData();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountBench, { once: true });
} else {
  mountBench();
}
