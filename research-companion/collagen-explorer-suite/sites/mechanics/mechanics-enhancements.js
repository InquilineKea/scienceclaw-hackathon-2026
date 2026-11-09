import { createSpatialViewer } from './spatial-viewer.js?v=20261101-r3g';

const SVG_NS = 'http://www.w3.org/2000/svg';

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null) continue;
    if (k === 'className') node.className = v;
    else if (k === 'textContent') node.textContent = v;
    else node.setAttribute(k, String(v));
  }
  for (const c of children) {
    if (typeof c === 'string') node.appendChild(document.createTextNode(c));
    else if (c) node.appendChild(c);
  }
  return node;
}

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) node.setAttribute(k, String(v));
  }
  return node;
}

function fmt(num, digits = 4) {
  return typeof num === 'number' && Number.isFinite(num) ? num.toFixed(digits) : 'N/A';
}

function buildEvidenceStrip() {
  const strip = el('nav', {
    className: 'me-evidence-strip',
    'aria-label': 'Cross-section scientific evidence and gate status'
  });

  const header = el('div', { className: 'me-strip-header' }, [
    el('span', {
      className: 'me-strip-title',
      textContent: 'Cross-Section Evidence & Gate Ledger (No Biochemical Calibration Inferred)'
    })
  ]);

  const items = [
    {
      href: '#original-model',
      badge: 'Hypothetical',
      cls: 'me-badge-hyp',
      text: 'Original model: hypothetical dimensionless proxy'
    },
    {
      href: '#matched-stiffness',
      badge: 'Normalized',
      cls: 'me-badge-hyp',
      text: 'H100 paired matched-stiffness: normalized topology comparison'
    },
    {
      href: '#hydrated-sliding',
      badge: 'Gate Failed',
      cls: 'me-badge-fail',
      text: 'Hydrated sliding: stiffness-transfer gate failed'
    },
    {
      href: '#martini-benchmark',
      badge: 'Failed ~586.591 ps',
      cls: 'me-badge-fail',
      text: 'Martini CUDA failed ~586.591 ps (PYD not started; 0 accepted post-30 ns windows); ARM64 CPU replay 800.0025 ps passed (root cause unresolved, no calibration)'
    },
    {
      href: '#network-sensitivity',
      badge: 'Reversible',
      cls: 'me-badge-warn',
      text: 'Network sliding-law sensitivity: can reverse contrast direction'
    }
  ];

  const list = el('ul', { className: 'me-strip-pills' });
  for (const item of items) {
    const a = el('a', { className: 'me-pill', href: item.href }, [
      el('span', { className: `me-badge ${item.cls}`, textContent: item.badge }),
      el('span', { textContent: item.text })
    ]);
    list.appendChild(el('li', {}, [a]));
  }

  const details = el('details', { className: 'me-scope-details' }, [
    el('summary', { textContent: 'Detailed scope & gate notes (click to expand)' }),
    el('ul', { className: 'me-scope-list' }, [
      el('li', { textContent: 'Original model metrics (E′, tan δ, traction, YAP_spatial) are dimensionless exploratory proxies; they do not provide a unique biological YAP prediction.' }),
      el('li', { textContent: 'H100 paired matched-stiffness comparisons evaluate normalized network topology effects without establishing molecular crosslink calibration.' }),
      el('li', { textContent: 'Hydrated sliding failed its stiffness-transfer gate; molecular-to-network parameter handoff remains unvalidated.' }),
      el('li', { textContent: 'Martini original x86 CUDA H100 production failed at ~586.591 ps with 0 accepted post-30 ns windows and PYD not started; the 800.0025 ps native ARM64 CPU replay passed short integration but does not resolve GPU failure causation or validate 45 ns stability.' }),
      el('li', { textContent: 'Network sliding-law sensitivity demonstrates that constitutive sliding assumptions can reverse predicted contrast direction.' })
    ])
  ]);

  strip.append(header, list, details);
  const anchorSection = document.getElementById('original-model');
  if (anchorSection && anchorSection.parentNode) {
    anchorSection.parentNode.insertBefore(strip, anchorSection);
  } else {
    document.body.prepend(strip);
  }
}

function initAdhesionExplorer() {
  const hostSection = document.getElementById('original-model');
  if (!hostSection) return;

  const state = {
    colorMode: 'protein',
    proteinFilter: 'ALL',
    selectedAdhesion: 0,
    snapshot: null,
    viewer: null
  };

  const card = el('section', {
    className: 'me-card',
    id: 'planar-adhesion-explorer',
    'aria-labelledby': 'me-adhesion-title'
  });

  const header = el('div', { className: 'me-card-header' }, [
    el('div', {}, [
      el('h3', {
        className: 'me-card-title',
        id: 'me-adhesion-title',
        textContent: 'Exploratory Planar Adhesion Inspector (z = 0 Saved Coordinates in 3D)'
      }),
      el('p', {
        className: 'me-card-sub',
        textContent: 'Explicitly planar saved model (actual site x, y with z = 0 only; no reconstructed 3D cell or invented force vectors from scalar traction).'
      })
    ])
  ]);

  const colorSelect = el('select', { id: 'me-color-mode', 'aria-label': 'Node color and size encoding' }, [
    el('option', { value: 'protein', textContent: 'Protein identity (FN vs Col) + late traction' }),
    el('option', { value: 'initial_traction', textContent: 'Saved initial_traction (dimensionless)' }),
    el('option', { value: 'late_traction', textContent: 'Saved late_traction (dimensionless)' }),
    el('option', { value: 'local_persistence', textContent: 'Saved local_persistence (dimensionless)' })
  ]);

  const filterSelect = el('select', { id: 'me-protein-filter', 'aria-label': 'Filter adhesion sites by protein' }, [
    el('option', { value: 'ALL', textContent: 'All proteins (12 sites)' }),
    el('option', { value: 'FN', textContent: 'FN only' }),
    el('option', { value: 'Col', textContent: 'Non-FN / Collagen-associated only' })
  ]);

  const siteSelect = el('select', { id: 'me-site-select', 'aria-label': 'Select adhesion site' });

  const controls = el('div', { className: 'me-controls' }, [
    el('label', { className: 'me-control-group', for: 'me-color-mode' }, ['Encoding mode', colorSelect]),
    el('label', { className: 'me-control-group', for: 'me-protein-filter' }, ['Protein filter', filterSelect]),
    el('label', { className: 'me-control-group', for: 'me-site-select' }, ['Inspect site (linked to 3D viewer)', siteSelect])
  ]);

  const viewerHost = el('div', {
    className: 'me-viewer-host',
    role: 'region',
    'aria-label': 'Planar 3D spatial viewer of 12 saved adhesion sites at z = 0'
  });

  const readoutFields = {
    adhesion: el('span', { className: 'me-kv-val', textContent: '-' }),
    protein: el('span', { className: 'me-kv-val', textContent: '-' }),
    coords: el('span', { className: 'me-kv-val', textContent: '-' }),
    angle: el('span', { className: 'me-kv-val', textContent: '-' }),
    initial: el('span', { className: 'me-kv-val', textContent: '-' }),
    late: el('span', { className: 'me-kv-val', textContent: '-' }),
    persist: el('span', { className: 'me-kv-val', textContent: '-' }),
    units: el('span', { className: 'me-kv-val', textContent: 'Dimensionless / unitless saved scalar' })
  };

  function kvItem(label, valNode) {
    return el('div', { className: 'me-kv' }, [
      el('span', { className: 'me-kv-label', textContent: label }),
      valNode
    ]);
  }

  const barsGrid = el('div', {
    className: 'me-bars-grid',
    role: 'group',
    'aria-label': 'Paired initial and late scalar traction across 12 adhesion sites'
  });

  const readoutBox = el('div', { className: 'me-readout-box' }, [
    el('strong', { textContent: 'Selected Adhesion Site Readout (Scalar Only)' }),
    el('div', { className: 'me-kv-grid' }, [
      kvItem('Adhesion ID', readoutFields.adhesion),
      kvItem('Protein Channel', readoutFields.protein),
      kvItem('Saved Planar Coord (x, y, z=0)', readoutFields.coords),
      kvItem('Angle (degrees)', readoutFields.angle),
      kvItem('Initial Traction (scalar)', readoutFields.initial),
      kvItem('Late Traction (scalar)', readoutFields.late),
      kvItem('Local Persistence', readoutFields.persist),
      kvItem('Units / Calibration', readoutFields.units)
    ]),
    el('div', { className: 'me-bars-wrap' }, [
      el('div', {
        className: 'me-kv-label',
        textContent: '12-Site Paired Scalar Traction Bar Plot (Teal = initial_traction, Sand = late_traction; click to select site)'
      }),
      barsGrid
    ])
  ]);

  const grid = el('div', { className: 'me-adhesion-grid' }, [viewerHost, readoutBox]);

  const rowSummaryText = el('p', { style: 'margin:0.3rem 0 0 0;' });
  const sepGrid = el('div', { className: 'me-sep-grid' }, [
    el('div', { className: 'me-note-box' }, [
      el('strong', { textContent: 'Saved Dimensionless Metric Row Summary' }),
      rowSummaryText
    ]),
    el('div', { className: 'me-note-box' }, [
      el('strong', { textContent: 'Hypothesis Scope vs Biological YAP Claim Separation' }),
      el('p', {
        style: 'margin:0.3rem 0 0 0;',
        textContent: 'YAP_spatial, YAP_mean_only, and YAP_permuted are algebraic functions of dimensionless model tractions and assumed signaling thresholds. They test sensitivity to spatial force permutation in a planar toy model and must not be interpreted as calibrated biological YAP nuclear translocation measurements.'
      })
    ])
  ]);

  card.append(header, controls, grid, sepGrid);
  hostSection.appendChild(card);

  try {
    state.viewer = createSpatialViewer(viewerHost, {
      onPick(pickedId) {
        if (pickedId === undefined || pickedId === null) return;
        if(pickedId.type==='edge')return;const site=state.snapshot?.sites.filter(matchesFilter)[pickedId.index];const numeric=site?.adhesion;
        if (Number.isFinite(numeric)) {
          state.selectedAdhesion = numeric;
          renderFromState(false);
        }
      }
    });
  } catch (_err) {
    viewerHost.appendChild(
      el('div', {
        className: 'me-error-box',
        textContent: '3D spatial viewer unavailable in this environment; scalar readouts and bar plots remain active.'
      })
    );
  }

  function matchesFilter(site) {
    if (state.proteinFilter === 'ALL') return true;
    if (state.proteinFilter === 'FN') return site.protein === 'FN';
    return site.protein !== 'FN';
  }

  function updateViewerModel(sites, row) {
    if (!state.viewer || typeof state.viewer.setModel !== 'function') return;
    const activeSites = sites.filter(matchesFilter);
    const nodes = activeSites.map((s) => {
      const val =
        state.colorMode === 'initial_traction'
          ? s.initial_traction
          : state.colorMode === 'local_persistence'
          ? s.local_persistence
          : s.late_traction;
      return {
        id: s.adhesion,
        x: Number(s.x),
        y: Number(s.y),
        z: 0,
        protein: s.protein,
        group: state.colorMode === 'protein' ? s.protein : state.colorMode,
        value: Number(val),
        label: `#${s.adhesion + 1} (${s.protein})`
      };
    });
    const groups = {};
    const labels = {};
    const nodeValues = {};
    for (const n of nodes) {
      groups[n.id] = n.group;
      labels[n.id] = n.label;
      nodeValues[n.id] = n.value;
    }
    try {
      state.viewer.setModel({
        nodes:nodes.map(n=>[n.x,n.y,n.z]),
        edges: [],
        groups:nodes.map(n=>n.group),
        labels:nodes.map(n=>n.label),
        nodeValues:nodes.map(n=>n.value),
        units: 'dimensionless (z = 0 planar saved coordinates; scalar magnitude only)',
        label: `Planar Adhesion Sites (${row.chemistry}, zone=${row.location}, density=${row.collagen_density}, seed=${row.seed})`,
        evidence: 'Hypothetical dimensionless planar model; z=0 exact saved coordinates; no force vectors or 3D cell reconstruction.'
      });
      if (typeof state.viewer.selectNode === 'function') {
        state.viewer.selectNode(nodes.findIndex(n=>n.id===state.selectedAdhesion));
      }
    } catch (_e) {
      // Keep UI functional if viewer rejects optional parameters
    }
  }

  function renderFromState(rebuildViewerModel = true) {
    const snap = state.snapshot;
    if (!snap || !snap.row || !Array.isArray(snap.sites) || !snap.sites.length) return;
    const { row, sites } = snap;

    if (!sites.some((s) => s.adhesion === state.selectedAdhesion)) {
      state.selectedAdhesion = sites[0].adhesion;
    }

    siteSelect.replaceChildren(
      ...sites.map((s) =>
        el('option', {
          value: String(s.adhesion),
          textContent: `Site #${s.adhesion + 1} (${s.protein}, θ=${s.angle_degrees}°, ${matchesFilter(s) ? 'shown' : 'filtered'})`
        })
      )
    );
    siteSelect.value = String(state.selectedAdhesion);

    const sel = sites.find((s) => s.adhesion === state.selectedAdhesion) || sites[0];
    readoutFields.adhesion.textContent = `#${sel.adhesion + 1} (index ${sel.adhesion})`;
    readoutFields.protein.textContent = String(sel.protein);
    readoutFields.coords.textContent = `(${fmt(sel.x, 3)}, ${fmt(sel.y, 3)}, 0.000)`;
    readoutFields.angle.textContent = `${fmt(sel.angle_degrees, 1)}°`;
    readoutFields.initial.textContent = fmt(sel.initial_traction, 4);
    readoutFields.late.textContent = fmt(sel.late_traction, 4);
    readoutFields.persist.textContent = fmt(sel.local_persistence, 4);

    const maxTraction = Math.max(
      0.0001,
      ...sites.map((s) => Math.max(Number(s.initial_traction) || 0, Number(s.late_traction) || 0))
    );

    barsGrid.replaceChildren(
      ...sites.map((s) => {
        const initH = Math.max(4, Math.round((s.initial_traction / maxTraction) * 74));
        const lateH = Math.max(4, Math.round((s.late_traction / maxTraction) * 74));
        const isSel = s.adhesion === state.selectedAdhesion;
        const inFilter = matchesFilter(s);
        const btn = el(
          'button',
          {
            type: 'button',
            className: `me-bar-slot${inFilter ? '' : ' me-dimmed'}`,
            'aria-pressed': isSel ? 'true' : 'false',
            title: `Site #${s.adhesion + 1} (${s.protein}): initial=${fmt(s.initial_traction, 4)}, late=${fmt(s.late_traction, 4)}`
          },
          [
            el('div', { className: 'me-bar-pair' }, [
              el('span', { className: 'me-bar-init', style: `height:${initH}px` }),
              el('span', { className: 'me-bar-late', style: `height:${lateH}px` })
            ]),
            el('span', { textContent: `#${s.adhesion + 1}` })
          ]
        );
        btn.addEventListener('click', () => {
          state.selectedAdhesion = s.adhesion;
          renderFromState(false);
          if (state.viewer && typeof state.viewer.selectNode === 'function') {
            try {
              state.viewer.selectNode(nodes.findIndex(n=>n.id===state.selectedAdhesion));
            } catch (_e) {}
          }
        });
        return btn;
      })
    );

    rowSummaryText.textContent = `chemistry=${row.chemistry}, density=${row.collagen_density}, zone=${row.location}, profile=${row.density_profile}, seed=${row.seed} | E′=${fmt(row.Eprime_mid, 3)}, tan δ=${fmt(row.tandelta_mid, 3)}, persistence=${fmt(100 * row.traction_persistence, 1)}%, YAP_spatial=${fmt(row.YAP_spatial, 3)}, YAP_mean_only=${fmt(row.YAP_mean_only, 3)}, YAP_permuted=${fmt(row.YAP_permuted, 3)}.`;

    if (rebuildViewerModel) {
      updateViewerModel(sites, row);
    } else if (state.viewer && typeof state.viewer.selectNode === 'function') {
      try {
        state.viewer.selectNode(nodes.findIndex(n=>n.id===state.selectedAdhesion));
      } catch (_e) {}
    }
  }

  function refreshFromBridge() {
    if (typeof globalThis.CollagenMechanicsSnapshot !== 'function') return;
    const snap = globalThis.CollagenMechanicsSnapshot();
    if (!snap || !snap.row) return;
    state.snapshot = snap;
    renderFromState(true);
  }

  colorSelect.addEventListener('change', () => {
    state.colorMode = colorSelect.value;
    renderFromState(true);
  });

  filterSelect.addEventListener('change', () => {
    state.proteinFilter = filterSelect.value;
    renderFromState(true);
  });

  siteSelect.addEventListener('change', () => {
    state.selectedAdhesion = Number(siteSelect.value);
    renderFromState(false);
  });

  for (const selId of ['density', 'chemistry', 'zone', 'profile', 'seed']) {
    const domSel = document.getElementById(selId);
    if (domSel) {
      domSel.addEventListener('change', () => {
        queueMicrotask(refreshFromBridge);
      });
    }
  }

  refreshFromBridge();
}

async function initMartiniDiagnosticCard() {
  const section = document.getElementById('martini-benchmark');
  if (!section) return;

  const card = el('section', {
    className: 'me-card',
    id: 'martini-diagnostic-traces',
    'aria-labelledby': 'me-martini-diag-title'
  });

  const title = el('h3', {
    className: 'me-card-title',
    id: 'me-martini-diag-title',
    textContent: 'Martini LINCS Diagnostic Replay Traces (Short 800.0025 ps ARM64 CPU Replay vs ~586.591 ps x86 CUDA Failure Marker)'
  });

  const subtitle = el('p', {
    className: 'me-card-sub',
    textContent: 'Full unsmoothed scalar trajectory log from ./martini/diagnostic-data.json. Short diagnostic replay is NOT 45 ns validation; GPU failure causation remains unresolved; logged pulled-model pressure is not physiological tissue pressure.'
  });

  const bodyWrap = el('div');
  card.append(el('div', { className: 'me-card-header' }, [el('div', {}, [title, subtitle])]), bodyWrap);
  section.appendChild(card);

  let data;
  try {
    const res = await fetch('./martini/diagnostic-data.json', { credentials: 'same-origin' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
    if (!data || !Array.isArray(data.rows) || !data.rows.length) {
      throw new Error('Diagnostic JSON contains no sample rows.');
    }
  } catch (err) {
    bodyWrap.appendChild(
      el('div', { className: 'me-error-box', role: 'alert' }, [
        el('strong', { textContent: 'Diagnostic trace data failed to load (./martini/diagnostic-data.json): ' }),
        el('span', { textContent: err && err.message ? err.message : 'Unknown fetch error' })
      ])
    );
    return;
  }

  const rows = data.rows;
  const failurePs = Number(data.failure_marker_ps) || 586.591;
  const completedPs = Number(data.cpu_completed_ps) || rows[rows.length - 1].time_ps;

  const metrics = {
    temperature_K: { label: 'Temperature (K)', unit: 'K', digits: 3, color: '#85d5c2' },
    pressure_bar: {
      label: 'Logged Pulled-Model Pressure (bar, non-physiological)',
      unit: 'bar',
      digits: 2,
      color: '#f3a467'
    },
    constraint_rmsd: { label: 'LINCS Constraint RMSD (dimensionless)', unit: 'rmsd', digits: 7, color: '#85d5c2' }
  };

  const state = {
    metric: 'temperature_K',
    sampleIndex: rows.reduce((bestIdx, r, i) =>
      Math.abs(r.time_ps - failurePs) < Math.abs(rows[bestIdx].time_ps - failurePs) ? i : bestIdx,
    0)
  };

  const backendNote = el('div', { className: 'me-note-box', style: 'margin-bottom:0.75rem;' }, [
    el('div', {
      textContent: `CPU Replay Backend: ${data.cpu_backend || 'GROMACS 2022.5 native ARM64 CPU'} (completed ${completedPs} ps, ${rows.length} logged samples, no smoothing, no invented CI) | Failed Production Backend: ${data.failed_backend || 'GROMACS 2023.2-dev x86 CUDA H100'} (failed at ~${failurePs} ps; reference marker only, no paired GPU time-series trace exists).`
    })
  ]);

  const metricSelect = el('select', { id: 'me-diag-metric', 'aria-label': 'Select diagnostic scalar trace' }, [
    el('option', { value: 'temperature_K', textContent: 'Temperature (K)' }),
    el('option', { value: 'pressure_bar', textContent: 'Pressure (bar) [logged pulled-model]' }),
    el('option', { value: 'constraint_rmsd', textContent: 'Constraint RMSD' })
  ]);

  const sampleSlider = el('input', {
    id: 'me-diag-slider',
    type: 'range',
    min: '0',
    max: String(rows.length - 1),
    step: '1',
    value: String(state.sampleIndex),
    'aria-label': 'Scrub exact logged diagnostic sample index'
  });

  const sampleBadge = el('span', { className: 'me-kv-val', style: 'align-self:center;' });

  const controls = el('div', { className: 'me-controls' }, [
    el('label', { className: 'me-control-group', for: 'me-diag-metric' }, ['Diagnostic channel', metricSelect]),
    el('label', { className: 'me-control-group', for: 'me-diag-slider', style: 'flex:1;min-width:210px;' }, [
      `Sample scrubber (0 to ${rows.length - 1} of ${rows.length} exact samples)`,
      sampleSlider
    ]),
    sampleBadge
  ]);

  const svg = svgEl('svg', {
    class: 'me-diag-svg',
    viewBox: '0 0 760 250',
    role: 'img',
    'aria-label': '2D SVG diagnostic trace over time in picoseconds with x86 CUDA failure marker at 586.591 ps'
  });
  const svgWrap = el('div', { className: 'me-svg-wrap' }, [svg]);

  const tdStep = el('td');
  const tdTime = el('td');
  const tdTemp = el('td');
  const tdPress = el('td');
  const tdRmsd = el('td');
  const tdDelta = el('td');

  const table = el('table', { className: 'me-table', 'aria-label': 'Selected diagnostic sample exact values' }, [
    el('thead', {}, [
      el('tr', {}, [
        el('th', { scope: 'col', textContent: 'Sample / Step' }),
        el('th', { scope: 'col', textContent: 'Time (ps)' }),
        el('th', { scope: 'col', textContent: 'Temperature (K)' }),
        el('th', { scope: 'col', textContent: 'Pulled-Model Pressure (bar)' }),
        el('th', { scope: 'col', textContent: 'Constraint RMSD' }),
        el('th', { scope: 'col', textContent: 'Δt vs 586.591 ps Marker' })
      ])
    ]),
    el('tbody', {}, [el('tr', {}, [tdStep, tdTime, tdTemp, tdPress, tdRmsd, tdDelta])])
  ]);

  const limitsList = el('ul', { className: 'me-scope-list' });
  for (const lim of data.limits || []) {
    limitsList.appendChild(el('li', { textContent: String(lim) }));
  }

  const provenance = el('div', { className: 'me-note-box', style: 'margin-top:0.75rem;' }, [
    el('strong', { textContent: 'Scientific Limits & Provenance' }),
    limitsList,
    el('p', {
      style: 'margin:0.45rem 0 0 0;font-size:0.76rem;',
      textContent: `SHA-256: ${data.source_sha256 || 'N/A'} | Report: ${data.source_report || 'N/A'}`
    })
  ]);

  bodyWrap.append(backendNote, controls, svgWrap, table, provenance);

  function renderTrace() {
    const m = metrics[state.metric];
    const pad = { l: 68, r: 22, t: 24, b: 36 };
    const W = 760 - pad.l - pad.r;
    const H = 250 - pad.t - pad.b;

    let minY = Infinity;
    let maxY = -Infinity;
    for (const r of rows) {
      const v = Number(r[state.metric]);
      if (v < minY) minY = v;
      if (v > maxY) maxY = v;
    }
    if (minY === maxY) {
      minY -= 1;
      maxY += 1;
    }
    const maxTime = Math.max(completedPs, failurePs, rows[rows.length - 1].time_ps, 1);

    const xOf = (t) => pad.l + (t / maxTime) * W;
    const yOf = (v) => pad.t + (1 - (v - minY) / (maxY - minY)) * H;

    svg.replaceChildren();

    for (let i = 0; i <= 4; i++) {
      const frac = i / 4;
      const y = pad.t + (1 - frac) * H;
      const val = minY + frac * (maxY - minY);
      svg.appendChild(
        svgEl('line', {
          x1: pad.l,
          y1: y,
          x2: 760 - pad.r,
          y2: y,
          stroke: 'rgba(154,173,194,0.14)',
          'stroke-width': 1
        })
      );
      const lbl = svgEl('text', {
        x: pad.l - 6,
        y: y + 4,
        fill: '#9aadc2',
        'font-size': '10',
        'text-anchor': 'end'
      });
      lbl.textContent = m.digits > 4 ? val.toExponential(2) : val.toFixed(m.digits);
      svg.appendChild(lbl);
    }

    for (const tTick of [0, 200, 400, 600, 800]) {
      if (tTick > maxTime) continue;
      const x = xOf(tTick);
      const lbl = svgEl('text', {
        x,
        y: 250 - 10,
        fill: '#9aadc2',
        'font-size': '10',
        'text-anchor': 'middle'
      });
      lbl.textContent = `${tTick} ps`;
      svg.appendChild(lbl);
    }

    svg.appendChild(
      svgEl('polyline', {
        fill: 'none',
        stroke: '#516779',
        'stroke-width': 1.2,
        points: `${pad.l},${pad.t} ${pad.l},${250 - pad.b} ${760 - pad.r},${250 - pad.b}`
      })
    );

    const pts = rows.map((r) => `${xOf(r.time_ps).toFixed(2)},${yOf(r[state.metric]).toFixed(2)}`).join(' ');
    svg.appendChild(
      svgEl('polyline', {
        fill: 'none',
        stroke: m.color,
        'stroke-width': 1.35,
        points: pts
      })
    );

    const failX = xOf(failurePs);
    svg.appendChild(
      svgEl('line', {
        x1: failX,
        y1: pad.t,
        x2: failX,
        y2: 250 - pad.b,
        stroke: '#e27c7c',
        'stroke-width': 1.6,
        'stroke-dasharray': '5,3'
      })
    );
    const failText = svgEl('text', {
      x: failX - 6,
      y: pad.t + 12,
      fill: '#e27c7c',
      'font-size': '10',
      'text-anchor': 'end'
    });
    failText.textContent = `Original x86 CUDA failure time (${failurePs} ps; reference marker; different backend)`;
    svg.appendChild(failText);

    const selRow = rows[state.sampleIndex] || rows[0];
    const selX = xOf(selRow.time_ps);
    const selY = yOf(selRow[state.metric]);
    svg.appendChild(
      svgEl('line', {
        x1: selX,
        y1: pad.t,
        x2: selX,
        y2: 250 - pad.b,
        stroke: '#e8b574',
        'stroke-width': 1
      })
    );
    svg.appendChild(
      svgEl('circle', {
        cx: selX,
        cy: selY,
        r: 4.2,
        fill: '#f3a467',
        stroke: '#0f1d26',
        'stroke-width': 1.5
      })
    );

    const fmtMetric = (v) =>
      m.digits > 4 ? Number(v).toExponential(5) : Number(v).toFixed(m.digits);

    sampleBadge.textContent = `Sample #${state.sampleIndex} | t = ${selRow.time_ps.toFixed(4)} ps | ${m.label}: ${fmtMetric(selRow[state.metric])}`;
    tdStep.textContent = `#${state.sampleIndex} (step ${selRow.step})`;
    tdTime.textContent = `${selRow.time_ps.toFixed(4)} ps`;
    tdTemp.textContent = `${selRow.temperature_K.toFixed(3)} K`;
    tdPress.textContent = `${selRow.pressure_bar.toFixed(2)} bar`;
    tdRmsd.textContent = Number(selRow.constraint_rmsd).toExponential(5);
    const dt = selRow.time_ps - failurePs;
    tdDelta.textContent = `${dt >= 0 ? '+' : ''}${dt.toFixed(4)} ps`;
  }

  metricSelect.addEventListener('change', () => {
    state.metric = metricSelect.value;
    renderTrace();
  });

  sampleSlider.addEventListener('input', () => {
    state.sampleIndex = Number(sampleSlider.value);
    renderTrace();
  });

  renderTrace();
}

function boot() {
  buildEvidenceStrip();
  initAdhesionExplorer();
  initMartiniDiagnosticCard();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
