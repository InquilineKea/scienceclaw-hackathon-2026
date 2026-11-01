import { createSpatialViewer } from './spatial-viewer.js?v=20261101-r3g';

const GATE_WARNING = 'Infrastructure pass is not collagen chemistry validation';

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'className') node.className = v;
    else if (k === 'textContent') node.textContent = String(v ?? '');
    else if (k.startsWith('on') && typeof v === 'function') {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (v !== null && v !== undefined) {
      node.setAttribute(k, String(v));
    }
  }
  for (const c of children) {
    if (typeof c === 'string') node.appendChild(document.createTextNode(c));
    else if (c instanceof Node) node.appendChild(c);
  }
  return node;
}

function safeHttpsUrl(raw) {
  try {
    const u = new URL(String(raw), window.location.origin);
    return u.protocol === 'https:' ? u.href : null;
  } catch {
    return null;
  }
}

function fmtVec(arr, digits = 7) {
  if (!Array.isArray(arr)) return 'n/a';
  return '[' + arr.map(n => Number(n).toFixed(digits)).join(', ') + ']';
}

function normModel(models, stateKey) {
  if (!Array.isArray(models) || !models.length) return null;
  const byId = models.find(m => m.id === stateKey || m.state === stateKey);
  if (byId) return byId;
  const s = stateKey.toLowerCase();
  if (s.includes('final')) return models.find(m => /final/i.test(m.id + ' ' + m.label)) || models[models.length - 1];
  if (s.includes('ref')) return models.find(m => /ref/i.test(m.id + ' ' + m.label)) || models[0];
  return models.find(m => /cuda/i.test(m.id + ' ' + m.label) && !/final/i.test(m.id + ' ' + m.label)) || models[0];
}

function extractParticle(model, idx, stateKey) {
  if (!model) return null;
  const useRef = stateKey === 'initial_reference' && Array.isArray(model.referenceNodes);
  const nodes = useRef ? model.referenceNodes : (model.nodes || []);
  const n = nodes[idx] || nodes[0] || {};
  const pos = Array.isArray(n)?n:(n.position || n.xyz || [n.x ?? 0, n.y ?? 0, n.z ?? 0]);
  let force = n.force || null;
  if (!force && Array.isArray(model.forces)) {
    const fEntry = model.forces[idx];
    force = Array.isArray(fEntry) ? fEntry : (fEntry?.vector || fEntry?.force || null);
  }
  return {
    id: n.id ?? `Particle ${idx}`,
    label: n.label || `Dimer Mass ${idx + 1}`,
    pos,
    refPos: Array.isArray(model.referenceNodes?.[idx])?model.referenceNodes[idx]:(model.referenceNodes?.[idx]?.position || model.referenceNodes?.[idx]?.xyz || null),
    force,
    units: model.units || 'nm',
    forceUnits: model.forceUnits || 'kJ/mol/nm'
  };
}

function buildChecksTable(checks, meta) {
  const rows = Array.isArray(checks) && checks.length ? checks : [
    { quantity: 'Initial Potential Energy', Reference: '0.2', CUDA: '0.19999991357326508', difference: '8.642673e-8', units: 'kJ/mol' },
    { quantity: 'Max Initial Force Component Error', Reference: '20.0', CUDA: '19.999994278', difference: '5.722e-6', units: 'kJ/mol/nm' },
    { quantity: 'Final Relative Energy Drift (1000 steps, 1 fs)', Reference: '0.0 (analytic)', CUDA: String(meta?.relative_energy_drift ?? '3.6648566e-5'), difference: '3.6648566e-5', units: 'dimensionless' }
  ];
  const tbody = el('tbody');
  rows.forEach(r => {
    tbody.appendChild(el('tr', {}, [
      el('td', { textContent: r.quantity }),
      el('td', { className: 'el-mono', textContent: r.Reference ?? '—' }),
      el('td', { className: 'el-mono', textContent: r.CUDA ?? '—' }),
      el('td', { className: 'el-mono el-diff', textContent: r.difference ?? '—' }),
      el('td', { className: 'el-unit', textContent: r.units ?? '' })
    ]));
  });
  return el('div', { className: 'el-table-wrap' }, [
    el('table', { className: 'el-table' }, [
      el('thead', {}, [el('tr', {}, [
        el('th', { textContent: 'Check Quantity' }),
        el('th', { textContent: 'Analytic / Reference' }),
        el('th', { textContent: 'CUDA (L4)' }),
        el('th', { textContent: '|Δ| / Drift' }),
        el('th', { textContent: 'Units' })
      ])]),
      tbody
    ])
  ]);
}

async function initEvidenceLens() {
  const main = document.getElementById('main') || document.querySelector('main');
  if (!main || document.getElementById('evidence-lens-root')) return;

  let data;
  try {
    const res = await fetch('./evidence-lens-data.json', { credentials: 'same-origin' });
    if (!res.ok) return;
    data = await res.json();
  } catch {
    return;
  }
  if (!data || typeof data !== 'object') return;

  const tiers = Array.isArray(data.tiers) ? data.tiers : [];
  const models = Array.isArray(data.models) ? data.models : [];
  const checks = Array.isArray(data.checks) ? data.checks : [];
  const meta = data.metadata || {};

  const section = el('section', { id: 'evidence-lens-root', className: 'el-section', 'aria-label': 'Interactive Evidence Matrix and Numerical Control' });

  const gateBanner = el('div', { className: 'el-gate-banner', role: 'status' }, [
    el('span', { className: 'el-gate-badge', textContent: 'SCIENTIFIC GATE' }),
    el('strong', { textContent: GATE_WARNING }),
    el('span', { className: 'el-gate-meta', textContent: `Platform: ${meta.platform || 'OpenMM CUDA (L4)'} · ${meta.steps ?? 1000} steps · dt = ${meta.dt_fs ?? 1} fs · Bio-validation: ${String(meta.biological_validation ?? false)}` })
  ]);

  const cardsWrap = el('div', { className: 'el-tier-grid', role: 'tablist' });
  const detailPane = el('div', { className: 'el-tier-detail', role: 'tabpanel' });

  let activeTierIdx = 0;
  function renderTierDetail(idx) {
    activeTierIdx = idx;
    Array.from(cardsWrap.children).forEach((c, i) => {
      c.classList.toggle('is-active', i === idx);
      c.setAttribute('aria-selected', String(i === idx));
    });
    detailPane.replaceChildren();
    const t = tiers[idx];
    if (!t) return;

    const claimsList = el('ul', { className: 'el-list el-claims' }, (t.claims || []).map(c => el('li', { textContent: c })));
    const limitsList = el('ul', { className: 'el-list el-limits' }, (t.doesNotEstablish || []).map(c => el('li', { textContent: c })));

    const linksRow = el('div', { className: 'el-links' }, [el('span', { className: 'el-links-label', textContent: 'Verified Sources:' })]);
    (t.sourceURLs || []).forEach(u => {
      const safe = safeHttpsUrl(u);
      if (safe) {
        linksRow.appendChild(el('a', { href: safe, target: '_blank', rel: 'noopener noreferrer', className: 'el-link', textContent: safe.replace(/^https:\/\//, '') }));
      }
    });

    detailPane.appendChild(el('div', { className: 'el-detail-header' }, [
      el('div', {}, [
        el('span', { className: 'el-kind-pill', textContent: t.kind || 'Evidence Tier' }),
        el('h3', { className: 'el-detail-title', textContent: t.title || t.id })
      ]),
      el('span', { className: 'el-scope-tag', textContent: t.scope || '' })
    ]));

    detailPane.appendChild(el('div', { className: 'el-detail-cols' }, [
      el('div', { className: 'el-col-box' }, [
        el('h4', { textContent: 'Supported Claims within Scope' }),
        claimsList
      ]),
      el('div', { className: 'el-col-box el-col-warn' }, [
        el('h4', { textContent: 'Does NOT Establish (Boundary Gate)' }),
        limitsList
      ])
    ]));
    if (linksRow.childNodes.length > 1) detailPane.appendChild(linksRow);
  }

  tiers.forEach((t, idx) => {
    const card = el('button', {
      type: 'button',
      role: 'tab',
      className: 'el-tier-card' + (idx === 0 ? ' is-active' : ''),
      'aria-selected': String(idx === 0),
      onClick: () => renderTierDetail(idx)
    }, [
      el('div', { className: 'el-card-top' }, [
        el('span', { className: 'el-card-kind', textContent: t.kind || `Tier ${idx + 1}` }),
        el('span', { className: 'el-card-scope', textContent: t.scope || '' })
      ]),
      el('div', { className: 'el-card-title', textContent: t.title || t.id }),
      el('div', { className: 'el-card-sub', textContent: `${(t.claims || []).length} supported · ${(t.doesNotEstablish || []).length} explicit boundaries` })
    ]);
    cardsWrap.appendChild(card);
  });
  if (tiers.length) renderTierDetail(0);

  const stateSelect = el('select', { className: 'el-select', 'aria-label': 'Select Discrete Stored Endpoint State' }, [
    el('option', { value: 'initial_reference', textContent: 'Initial Reference (t = 0 fs, Analytic/CPU)' }),
    el('option', { value: 'initial_cuda', textContent: 'Initial CUDA (t = 0 fs, L4 GPU)' }),
    el('option', { value: 'final_cuda', textContent: 'Final CUDA Endpoint (t = 1000 fs, step 1000)' })
  ]);

  const magSelect = el('select', { className: 'el-select', 'aria-label': 'Display Vector/Displacement Magnification' }, [
    el('option', { value: '1', textContent: '1× displacement display (saved coordinates)' }),
    el('option', { value: '25', textContent: '25× Display Exaggeration (Visual Aid Only)' }),
    el('option', { value: '100', textContent: '100× Display Exaggeration (Visual Aid Only)' })
  ]);

  const p0Btn = el('button', { type: 'button', className: 'el-pbtn is-active', textContent: 'Particle 0' });
  const p1Btn = el('button', { type: 'button', className: 'el-pbtn', textContent: 'Particle 1' });

  const viewportHost = el('div', { className: 'el-viewport', 'aria-label': '3D Harmonic Dimer Numerical Control Viewport' });
  const inspectorBody = el('div', { className: 'el-inspector-body' });

  let viewer = null;
  let currentState = 'initial_cuda';
  let selectedIdx = 0;
  let dispMag = 1;

  let lastDisplayedModel=null;
  function adaptModelForViewer(rawModel){return {...rawModel,nodes:rawModel.nodes.map(n=>Array.isArray(n)?n.slice():n.position||n.xyz),referenceNodes:rawModel.referenceNodes?.map(n=>Array.isArray(n)?n.slice():n.position||n.xyz)};}

  function syncViewerAndInspector() {
    const m = normModel(models, currentState);
    if (viewer && m) {
      try {
        const vModel = adaptModelForViewer(m, currentState, dispMag);
        if (typeof viewer.setModel === 'function' && lastDisplayedModel!==m.id){viewer.setModel(vModel);lastDisplayedModel=m.id;}viewer.setDisplayMagnification?.(dispMag);
        if (typeof viewer.selectNode === 'function') viewer.selectNode(selectedIdx);
      } catch {
        /* preserve UI on viewer API mismatch */
      }
    }
    p0Btn.classList.toggle('is-active', selectedIdx === 0);
    p1Btn.classList.toggle('is-active', selectedIdx === 1);

    const p = extractParticle(m, selectedIdx, currentState);
    inspectorBody.replaceChildren();
    if (!p) {
      inspectorBody.appendChild(el('p', { textContent: 'No particle coordinates found in model.' }));
      return;
    }
    const kv = [
      ['Control Identity', '2-Particle Harmonic Dimer (NOT Collagen)'],
      ['Stored Endpoint State', stateSelect.options[stateSelect.selectedIndex]?.text || currentState],
      ['Selected Particle', `${p.label} (index ${selectedIdx})`],
      [`Position (${p.units})`, fmtVec(p.pos, 7)],
      ['Reference Position (nm)', p.refPos ? fmtVec(p.refPos, 7) : fmtVec(p.pos, 7)],
      [`Force Vector (${p.forceUnits})`, p.force ? fmtVec(p.force, 7) : 'Stored on initial state only'],
      ['Display Magnification', `${dispMag}× (underlying numbers unscaled)`],
      ['Trajectory Note', 'Endpoints only stored (t=0, t=1000 fs); no interpolated frames.']
    ];
    kv.forEach(([k, v]) => {
      inspectorBody.appendChild(el('div', { className: 'el-kv-row' }, [
        el('span', { className: 'el-kv-k', textContent: k }),
        el('span', { className: 'el-kv-v el-mono', textContent: v })
      ]));
    });
  }

  stateSelect.value = currentState;
  stateSelect.addEventListener('change', () => { currentState = stateSelect.value; syncViewerAndInspector(); });
  magSelect.addEventListener('change', () => { dispMag = Number(magSelect.value) || 1; syncViewerAndInspector(); });
  p0Btn.addEventListener('click', () => { selectedIdx = 0; syncViewerAndInspector(); });
  p1Btn.addEventListener('click', () => { selectedIdx = 1; syncViewerAndInspector(); });

  const viewerPanel = el('div', { className: 'el-3d-shell' }, [
    el('div', { className: 'el-3d-header' }, [
      el('div', {}, [
        el('span', { className: 'el-ctrl-badge', textContent: 'NUMERICAL CONTROL ONLY · NOT COLLAGEN' }),
        el('h3', { className: 'el-3d-title', textContent: 'OpenMM 2-Particle Harmonic Dimer Verification (L4 CUDA vs Analytic Reference)' }),
        el('p', { className: 'el-3d-sub', textContent: 'Exact stored coordinates (nm) and force vectors (kJ/mol/nm) at discrete endpoints (1000 steps, dt = 1 fs). No trajectory interpolation.' })
      ]),
      el('div', { className: 'el-toolbar' }, [
        el('label', { className: 'el-ctrl-label' }, ['Endpoint:', stateSelect]),
        el('label', { className: 'el-ctrl-label' }, ['Visual Scale:', magSelect]),
        el('div', { className: 'el-pbtn-group' }, [p0Btn, p1Btn])
      ])
    ]),
    el('div', { className: 'el-3d-grid' }, [
      viewportHost,
      el('div', { className: 'el-inspector' }, [
        el('h4', { textContent: 'Original Executed Numerics (Unscaled)' }),
        inspectorBody,
        el('div', { className: 'el-key-metrics' }, [
          el('div', { className: 'el-metric' }, [el('span', { textContent: 'Analytic / CUDA E₀ (kJ/mol)' }), el('strong', { className: 'el-mono', textContent: '0.2 vs 0.19999991357326508' })]),
          el('div', { className: 'el-metric' }, [el('span', { textContent: 'Max Force Error (kJ/mol/nm)' }), el('strong', { className: 'el-mono', textContent: '5.722e-6' })]),
          el('div', { className: 'el-metric' }, [el('span', { textContent: 'Final Rel. Energy Drift' }), el('strong', { className: 'el-mono', textContent: '3.6648566e-5' })])
        ])
      ])
    ]),
    buildChecksTable(checks, meta)
  ]);

  section.append(gateBanner, cardsWrap, detailPane, viewerPanel);

  const resultSec = document.getElementById('result');
  if (resultSec && resultSec.parentNode === main) {
    resultSec.insertAdjacentElement('afterend', section);
  } else {
    main.prepend(section);
  }

  try {
    viewer = createSpatialViewer(viewportHost, {
      onPick: (nodeOrIdx) => {
        if(nodeOrIdx?.type==='edge')return;
        const idx = typeof nodeOrIdx === 'number' ? nodeOrIdx : (nodeOrIdx?.index ?? 0);
        if (idx === 0 || idx === 1) {
          selectedIdx = idx;
          syncViewerAndInspector();
        }
      }
    });
  } catch {
    viewportHost.appendChild(el('div', { className: 'el-viewer-fallback', textContent: '3D WebGL view unavailable; exact numerical control records shown in inspector.' }));
  }
  syncViewerAndInspector();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initEvidenceLens);
} else {
  initEvidenceLens();
}
