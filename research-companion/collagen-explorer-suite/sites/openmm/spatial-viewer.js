const readableLabel=v=>v&&typeof v==='object'?Object.entries(v).map(([k,x])=>`${k}: ${x}`).join(' · '):String(v??'');
import * as THREE from './vendor/three.module.js';
import { OrbitControls } from './vendor/OrbitControls.js';

const PALETTE = [
  0x0284c7, 0x0d9488, 0xd97706, 0x7c3aed, 0xdb2777, 0x4f46e5, 0x059669, 0xdc2626
];
const UP = new THREE.Vector3(0, 1, 0);
const DUMMY = new THREE.Object3D();
const V1 = new THREE.Vector3();
const V2 = new THREE.Vector3();
const V3 = new THREE.Vector3();
const C1 = new THREE.Color();

function isFin(n) {
  return typeof n === 'number' && Number.isFinite(n);
}

function validVec(v) {
  return Array.isArray(v) && v.length >= 3 && isFin(v[0]) && isFin(v[1]) && isFin(v[2]);
}

function fmt(n, d = 3) {
  return isFin(n) ? Number(n).toFixed(d) : '—';
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

export function createSpatialViewer(host, { onPick } = {}) {
  if (!host) throw new Error('Host element required');
  host.innerHTML = '';
  const root = el('div', 'sv-root');
  host.appendChild(root);

  const header = el('div', 'sv-header');
  const titleBar = el('div', 'sv-title-row');
  const titleEl = el('span', 'sv-title', 'No model loaded');
  const badgesEl = el('div', 'sv-badges');
  const evidenceEl = el('span', 'sv-badge', '');
  const planarEl = el('span', 'sv-badge sv-badge-warn sv-hidden', '2D Planar Dataset (Z = 0)');
  badgesEl.append(evidenceEl, planarEl);
  titleBar.append(titleEl, badgesEl);
  const caveatEl = el('div', 'sv-caveat', 'Saved geometry / illustrative model, as labeled. View controls do not run molecular dynamics.');
  header.append(titleBar, caveatEl);

  const stage = el('div', 'sv-stage');
  const canvasWrap = el('div', 'sv-canvas-wrap');
  const hud = el('div', 'sv-hud');
  const legendEl = el('div', 'sv-legend');

  const mkBtn = (txt, title, fn) => {
    const b = el('button', 'sv-btn', txt);
    b.type = 'button';
    if (title) b.title = title;
    b.addEventListener('click', fn);
    return b;
  };

  const camBar = el('div', 'sv-toolbar');
  const btnIso = mkBtn('Iso', 'Isometric view', () => setPreset('iso'));
  const btnXY = mkBtn('XY', 'XY plane view', () => setPreset('xy'));
  const btnXZ = mkBtn('XZ', 'XZ plane view', () => setPreset('xz'));
  const btnYZ = mkBtn('YZ', 'YZ plane view', () => setPreset('yz'));
  const btnFit = mkBtn('Fit', 'Reset / Fit view', () => setPreset('fit'));
  const btnProj = mkBtn('Persp', 'Toggle Perspective / Orthographic', () => toggleProjection());
  camBar.append(btnIso, btnXY, btnXZ, btnYZ, btnFit, btnProj);
  hud.append(camBar, legendEl);
  stage.append(canvasWrap, hud);

  const controlsPanel = el('div', 'sv-controls');

  // Row 1: Sliders & Toggles
  const visRow = el('div', 'sv-row');
  const radLabel = el('label', 'sv-ctrl-label', 'Thickness ');
  const radInput = el('input', 'sv-range');
  Object.assign(radInput, { type: 'range', min: '0.3', max: '2.5', step: '0.1', value: '1.0' });
  radLabel.appendChild(radInput);

  const ghostWrap = el('label', 'sv-ctrl-label sv-hidden');
  const ghostChk = el('input');
  ghostChk.type = 'checkbox';
  ghostChk.checked = true;
  ghostWrap.append(ghostChk, document.createTextNode(' Ref Ghost'));

  const dispWrap = el('label', 'sv-ctrl-label sv-hidden');
  const dispSpan = el('span', '', 'Disp 1x ');
  const dispInput = el('input', 'sv-range');
  Object.assign(dispInput, { type: 'range', min: '0', max: '4', step: '1', value: '1' });
  const DISP_STEPS = [0, 1, 2, 5, 10, 25, 100];dispInput.max='6';
  dispWrap.append(dispSpan, dispInput);

  const forceWrap = el('label', 'sv-ctrl-label sv-hidden');
  const forceChk = el('input');
  forceChk.type = 'checkbox';
  forceChk.checked = false;
  const forceSpan = el('span', '', ' Vectors (1x) ');
  const forceInput = el('input', 'sv-range');
  Object.assign(forceInput, { type: 'range', min: '0.25', max: '4', step: '0.25', value: '1' });
  forceWrap.append(forceChk, forceSpan, forceInput);

  visRow.append(radLabel, ghostWrap, dispWrap, forceWrap);

  // Row 2: Slab Slicer
  const sliceRow = el('div', 'sv-row');
  const sliceAxisLbl = el('label', 'sv-ctrl-label', 'Slice ');
  const sliceAxis = el('select', 'sv-select');
  ['full', 'x', 'y', 'z'].forEach(a => {
    const o = el('option', '', a === 'full' ? 'Full Volume' : `${a.toUpperCase()} Slab`);
    o.value = a;
    sliceAxis.appendChild(o);
  });
  sliceAxisLbl.appendChild(sliceAxis);

  const sliceMinInput = el('input', 'sv-range sv-hidden');
  Object.assign(sliceMinInput, { type: 'range', min: '0', max: '100', step: '1', value: '0', title: 'Slab minimum' });
  const sliceMaxInput = el('input', 'sv-range sv-hidden');
  Object.assign(sliceMaxInput, { type: 'range', min: '0', max: '100', step: '1', value: '100', title: 'Slab maximum' });
  const sliceReadout = el('span', 'sv-mono sv-slice-lbl sv-hidden', '');
  sliceRow.append(sliceAxisLbl, sliceMinInput, sliceMaxInput, sliceReadout);

  // Row 3: Accessible Selectors & Inspector
  const navRow = el('div', 'sv-row sv-nav-row');
  const nodeNav = el('div', 'sv-nav-group');
  const btnPrevNode = mkBtn('◀', 'Previous visible node', () => stepNode(-1));
  const nodeSel = el('select', 'sv-select');
  nodeSel.setAttribute('aria-label', 'Select Node');
  const btnNextNode = mkBtn('▶', 'Next visible node', () => stepNode(1));
  nodeNav.append(el('span', 'sv-ctrl-label', 'Node:'), btnPrevNode, nodeSel, btnNextNode);

  const edgeNav = el('div', 'sv-nav-group');
  const edgeSel = el('select', 'sv-select');
  edgeSel.setAttribute('aria-label', 'Select Edge');
  edgeNav.append(el('span', 'sv-ctrl-label', 'Edge:'), edgeSel);
  navRow.append(nodeNav, edgeNav);

  const inspector = el('div', 'sv-inspector', 'Select a node or edge to inspect original saved coordinates.');
  controlsPanel.append(visRow, sliceRow, navRow, inspector);
  root.append(header, stage, controlsPanel);

  // State
  let state = {
    nodes: [], edges: [], groups: [], labels: [], refNodes: null, forces: null,
    nodeValues: null, edgeValues: null, units: '', forceUnits: '',
    hasRef: false, hasForces: false, isPlanar: false,
    bounds: { min: [0, 0, 0], max: [1, 1, 1], center: [0, 0, 0], span: [1, 1, 1], radius: 1 },
    groupMap: new Map(), groupList: [],
    nodeVis: [], edgeVis: [],
    selNode: -1, selEdge: -1,
    radiusScale: 1.0, showGhost: true, dispMag: 1, showForces: false, forceMag: 1.0,
    slice: 'full', sMin: 0, sMax: 100,
    ortho: false
  };

  let webglOk = false;
  let renderer = null, scene = null, pCam = null, oCam = null, activeCam = null, controls = null;
  let meshGroup = null, instNodes = null, instEdges = null, instGhostNodes = null, instGhostEdges = null;
  let instForceShafts = null, instForceHeads = null;
  let selNodeMesh = null, selEdgeMesh = null, gridHelper = null;
  let baseSphere = null, baseCyl = null, baseCone = null, baseRing = null;
  let matNode = null, matEdge = null, matGhost = null, matForce = null, matSelNode = null, matSelEdge = null;
  let rafId = 0, isHidden = false, syncingView = false, disposed = false;
  let downPt = { x: 0, y: 0, t: 0 };
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  // Init WebGL or Fallback
  try {
    const canvas = el('canvas', 'sv-canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) throw new Error('WebGL disabled');
    renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0xf8fafc, 1);
    canvasWrap.appendChild(canvas);

    scene = new THREE.Scene();
    const amb = new THREE.AmbientLight(0xffffff, 0.75);
    const dir1 = new THREE.DirectionalLight(0xffffff, 0.85);
    dir1.position.set(1.5, 2.5, 2.0);
    const dir2 = new THREE.DirectionalLight(0x94a3b8, 0.4);
    dir2.position.set(-2.0, -1.5, -1.0);
    scene.add(amb, dir1, dir2);

    pCam = new THREE.PerspectiveCamera(42, 1, 0.01, 1000);
    oCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 1000);
    activeCam = pCam;

    controls = new OrbitControls(activeCam, canvas);
    controls.enableDamping = false;
    controls.addEventListener('change', () => { requestRender(); });

    meshGroup = new THREE.Group();
    scene.add(meshGroup);

    baseSphere = new THREE.SphereGeometry(1, 16, 12);
    baseCyl = new THREE.CylinderGeometry(1, 1, 1, 10, 1);
    baseCone = new THREE.ConeGeometry(1, 1, 10);
    baseRing = new THREE.SphereGeometry(1.38, 16, 12);

    matNode = new THREE.MeshStandardMaterial({ roughness: 0.35, metalness: 0.1 });
    matEdge = new THREE.MeshStandardMaterial({ roughness: 0.45, metalness: 0.1 });
    matGhost = new THREE.MeshBasicMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.28, depthWrite: false });
    matForce = new THREE.MeshStandardMaterial({ color: 0xe11d48, roughness: 0.3, metalness: 0.1 });
    matSelNode = new THREE.MeshBasicMaterial({ color: 0x0f172a, wireframe: true });
    matSelEdge = new THREE.MeshBasicMaterial({ color: 0xf59e0b });

    selNodeMesh = new THREE.Mesh(baseRing, matSelNode);
    selNodeMesh.visible = false;
    selEdgeMesh = new THREE.Mesh(baseCyl, matSelEdge);
    selEdgeMesh.visible = false;
    scene.add(selNodeMesh, selEdgeMesh);

    canvas.addEventListener('pointerdown', onPointerDown);
    canvas.addEventListener('pointerup', onPointerUp);
    canvas.setAttribute('tabindex', '0');
    canvas.setAttribute('aria-label', '3D structure viewer canvas. Use arrow keys to rotate, plus or minus to zoom.');
    canvas.addEventListener('keydown', onCanvasKey);
    webglOk = true;
  } catch (_) {
    webglOk = false;
    hud.classList.add('sv-hidden');
    radLabel.classList.add('sv-hidden');
    const fb = el('div', 'sv-fallback', '3D WebGL view is unavailable in this environment. Use the node, edge, and slab controls below to inspect exact saved coordinates, displacements, and vectors.');
    canvasWrap.appendChild(fb);
  }

  // UI Listeners
  radInput.addEventListener('input', () => {
    state.radiusScale = parseFloat(radInput.value) || 1;
    updateGeometryTransforms();
  });
  ghostChk.addEventListener('change', () => {
    state.showGhost = ghostChk.checked;
    updateGeometryTransforms();
  });
  dispInput.addEventListener('input', () => {
    const idx = parseInt(dispInput.value, 10) || 0;
    state.dispMag = DISP_STEPS[idx] ?? 1;
    dispSpan.textContent = `Disp ${state.dispMag}x `;
    updateGeometryTransforms();
  });
  forceChk.addEventListener('change', () => {
    state.showForces = forceChk.checked;
    updateGeometryTransforms();
  });
  forceInput.addEventListener('input', () => {
    state.forceMag = parseFloat(forceInput.value) || 1;
    forceSpan.textContent = ` Vectors (${state.forceMag}x) `;
    updateGeometryTransforms();
  });

  sliceAxis.addEventListener('change', () => {
    state.slice = sliceAxis.value;
    const active = state.slice !== 'full';
    sliceMinInput.classList.toggle('sv-hidden', !active);
    sliceMaxInput.classList.toggle('sv-hidden', !active);
    sliceReadout.classList.toggle('sv-hidden', !active);
    updateSliceAndTransforms();
  });
  sliceMinInput.addEventListener('input', () => {
    let v = parseInt(sliceMinInput.value, 10);
    if (v > state.sMax) { v = state.sMax; sliceMinInput.value = String(v); }
    state.sMin = v;
    updateSliceAndTransforms();
  });
  sliceMaxInput.addEventListener('input', () => {
    let v = parseInt(sliceMaxInput.value, 10);
    if (v < state.sMin) { v = state.sMin; sliceMaxInput.value = String(v); }
    state.sMax = v;
    updateSliceAndTransforms();
  });

  nodeSel.addEventListener('change', () => {
    const idx = parseInt(nodeSel.value, 10);
    selectNode(Number.isNaN(idx) ? -1 : idx, true);
  });
  edgeSel.addEventListener('change', () => {
    const idx = parseInt(edgeSel.value, 10);
    selectEdge(Number.isNaN(idx) ? -1 : idx, true);
  });

  const onVisChange = () => {
    isHidden = document.hidden;
    if (!isHidden) requestRender();
  };
  document.addEventListener('visibilitychange', onVisChange);

  const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => resize()) : null;
  if (ro) ro.observe(stage);

  function onCanvasKey(e) {
    if (!controls || !activeCam) return;
    const step = state.bounds.radius * 0.12;
    const off = V1.copy(activeCam.position).sub(controls.target);
    let handled = true;
    if (e.key === 'ArrowLeft') off.applyAxisAngle(UP, 0.12);
    else if (e.key === 'ArrowRight') off.applyAxisAngle(UP, -0.12);
    else if (e.key === 'ArrowUp') off.y += step;
    else if (e.key === 'ArrowDown') off.y -= step;
    else if (e.key === '+' || e.key === '=') off.multiplyScalar(0.88);
    else if (e.key === '-') off.multiplyScalar(1.14);
    else handled = false;
    if (handled) {
      e.preventDefault();
      activeCam.position.copy(controls.target).add(off);
      controls.update();
      requestRender();
    }
  }

  function onPointerDown(e) {
    downPt = { x: e.clientX, y: e.clientY, t: performance.now() };
  }

  function onPointerUp(e) {
    if (!webglOk || !renderer || state.nodes.length === 0) return;
    const dx = e.clientX - downPt.x, dy = e.clientY - downPt.y;
    if (Math.hypot(dx, dy) > 5 || performance.now() - downPt.t > 500) return;
    const rect = renderer.domElement.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, activeCam);

    const targets = [];
    if (instNodes) targets.push(instNodes);
    if (instEdges) targets.push(instEdges);
    const hits = raycaster.intersectObjects(targets, false);
    for (const h of hits) {
      if (h.object === instNodes && h.instanceId !== undefined && state.nodeVis[h.instanceId]) {
        selectNode(h.instanceId, true);
        return;
      }
      if (h.object === instEdges && h.instanceId !== undefined && state.edgeVis[h.instanceId]) {
        selectEdge(h.instanceId, true);
        return;
      }
    }
  }

  function clearInstanced() {
    if (!meshGroup) return;
    while (meshGroup.children.length > 0) {
      const c = meshGroup.children[0];
      meshGroup.remove(c);
      if (c.dispose) c.dispose();
    }
    instNodes = instEdges = instGhostNodes = instGhostEdges = instForceShafts = instForceHeads = null;
    if (gridHelper) { scene.remove(gridHelper); gridHelper.geometry.dispose(); gridHelper.material.dispose(); gridHelper = null; }
  }

  function setModel(model) {
    if (disposed) return;
    const rawNodes = Array.isArray(model?.nodes) ? model.nodes : [];
    const nodes = [];
    const origIdxMap = new Map();
    for (let i = 0; i < rawNodes.length; i++) {
      if (validVec(rawNodes[i])) {
        origIdxMap.set(i, nodes.length);
        nodes.push([Number(rawNodes[i][0]), Number(rawNodes[i][1]), Number(rawNodes[i][2])]);
      }
    }
    const N = nodes.length;
    const rawEdges = Array.isArray(model?.edges) ? model.edges : [];
    const edges = [];
    const edgeValues = [];
    const hasEdgeVals = Array.isArray(model?.edgeValues);
    for (let i = 0; i < rawEdges.length; i++) {
      const e = rawEdges[i];
      if (Array.isArray(e) && e.length >= 2) {
        const a = origIdxMap.get(e[0]), b = origIdxMap.get(e[1]);
        if (a !== undefined && b !== undefined && a !== b) {
          edges.push([a, b]);
          if (hasEdgeVals) edgeValues.push(model.edgeValues[i]);
        }
      }
    }

    const groups = [];
    const labels = [];
    const nodeValues = [];
    const hasNodeVals = Array.isArray(model?.nodeValues);
    const groupMap = new Map();
    const groupList = [];

    let refNodes = null;
    let hasRef = Array.isArray(model?.referenceNodes) && model.referenceNodes.length === rawNodes.length;
    if (hasRef) refNodes = [];

    let forces = null;
    let hasForces = Array.isArray(model?.forces) && model.forces.length === rawNodes.length;
    if (hasForces) forces = [];

    let refDiffers = false;
    let maxForce = 0;

    for (let origI = 0; origI < rawNodes.length; origI++) {
      if (!origIdxMap.has(origI)) continue;
      const idx = origIdxMap.get(origI);
      const g = model?.groups?.[origI] != null ? String(model.groups[origI]) : (model.elements?.[origI]||'Coordinate group');
      groups.push(g);
      if (!groupMap.has(g)) {
        groupMap.set(g, PALETTE[groupList.length % PALETTE.length]);
        groupList.push(g);
      }
      labels.push(model?.labels?.[origI] != null ? readableLabel(model.labels[origI]) : `${model.elements?.[origI]||"Node"} ${idx}`);
      if (hasNodeVals) nodeValues.push(model.nodeValues[origI]);

      if (hasRef) {
        const rv = model.referenceNodes[origI];
        if (validVec(rv)) {
          refNodes.push([Number(rv[0]), Number(rv[1]), Number(rv[2])]);
          const n = nodes[idx];
          if (Math.hypot(n[0] - rv[0], n[1] - rv[1], n[2] - rv[2]) > 1e-6) refDiffers = true;
        } else {
          hasRef = false;
        }
      }
      if (hasForces) {
        const fv = model.forces[origI];
        if (validVec(fv)) {
          const fx = Number(fv[0]), fy = Number(fv[1]), fz = Number(fv[2]);
          forces.push([fx, fy, fz]);
          const m = Math.hypot(fx, fy, fz);
          if (m > maxForce) maxForce = m;
        } else {
          forces.push(null);
        }
      }
    }
    if (!refDiffers) hasRef = false;
    if (!forces?.some(validVec)) hasForces = false;

    // Compute Bounds
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    const includePt = (p) => {
      for (let d = 0; d < 3; d++) {
        if (p[d] < min[d]) min[d] = p[d];
        if (p[d] > max[d]) max[d] = p[d];
      }
    };
    nodes.forEach(includePt);
    if (hasRef && refNodes) refNodes.forEach(includePt);
    if (N === 0) { min.fill(-1); max.fill(1); }

    const center = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];
    const span = [max[0] - min[0], max[1] - min[1], max[2] - min[2]];
    const radius = Math.max(Math.hypot(span[0], span[1], span[2]) * 0.5, 1e-3);
    const isPlanar = N > 0 && span[2] <= Math.max(span[0], span[1], 1e-6) * 1e-4;

    state = {
      ...state,
      nodes, edges, groups, labels,
      refNodes: hasRef ? refNodes : null,
      forces: hasForces ? forces : null,
      maxForce,
      nodeValues: hasNodeVals ? nodeValues : null,
      edgeValues: hasEdgeVals ? edgeValues : null,
      units: model?.units ? String(model.units) : '',
      forceUnits: model?.forceUnits ? String(model.forceUnits) : '',
      hasRef, hasForces, isPlanar,
      bounds: { min, max, center, span, radius },
      groupMap, groupList,
      nodeVis: new Array(N).fill(true),
      edgeVis: new Array(edges.length).fill(true),
      selNode: N > 0 ? 0 : -1,
      selEdge: -1,
      dispMag: 1, showGhost: true, showForces: false, forceMag: 1.0,
      slice: 'full', sMin: 0, sMax: 100
    };

    // Update Header & Controls UI
    titleEl.textContent = model?.label ? String(model.label) : 'Collagen Structural Model';
    evidenceEl.textContent = model?.evidence ? String(model.evidence) : (state.units ? `Units: ${state.units}` : 'Saved Record');
    planarEl.classList.toggle('sv-hidden', !isPlanar);

    ghostWrap.classList.toggle('sv-hidden', !hasRef);
    dispWrap.classList.toggle('sv-hidden', !hasRef);
    ghostChk.checked = true;
    dispInput.value = '1';
    dispSpan.textContent = 'Disp 1x ';

    forceWrap.classList.toggle('sv-hidden', !hasForces);
    forceChk.checked = false;
    forceInput.value = '1';
    forceSpan.textContent = ' Vectors (1x) ';

    sliceAxis.value = 'full';
    sliceMinInput.value = '0';
    sliceMaxInput.value = '100';
    sliceMinInput.classList.add('sv-hidden');
    sliceMaxInput.classList.add('sv-hidden');
    sliceReadout.classList.add('sv-hidden');

    // Legend
    legendEl.innerHTML = '';
    if (groupList.length > 1 || (groupList.length === 1 && groupList[0] !== 'Chain A')) {
      groupList.slice(0, 6).forEach(g => {
        const item = el('span', 'sv-legend-item');
        const dot = el('span', 'sv-dot');
        dot.style.backgroundColor = '#' + groupMap.get(g).toString(16).padStart(6, '0');
        item.append(dot, document.createTextNode(g));
        legendEl.appendChild(item);
      });
    }

    buildInstancedMeshes();
    updateSliceAndTransforms();
    resize();
    setPreset('iso');
    updateInspector();
  }

  function buildInstancedMeshes() {
    if (!webglOk) return;
    clearInstanced();
    const N = state.nodes.length, E = state.edges.length;
    if (N === 0) return;

    const { center, span, min, radius } = state.bounds;
    const gridSz = Math.max(span[0], span[2], radius * 1.6);
    gridHelper = new THREE.GridHelper(gridSz, 10, 0xcbd5e1, 0xe2e8f0);
    gridHelper.position.set(center[0], min[1] - radius * 0.08, center[2]);
    scene.add(gridHelper);

    instNodes = new THREE.InstancedMesh(baseSphere, matNode, N);
    for (let i = 0; i < N; i++) {
      C1.setHex(state.groupMap.get(state.groups[i]) || PALETTE[0]);
      instNodes.setColorAt(i, C1);
    }
    if (instNodes.instanceColor) instNodes.instanceColor.needsUpdate = true;
    meshGroup.add(instNodes);

    if (E > 0) {
      instEdges = new THREE.InstancedMesh(baseCyl, matEdge, E);
      for (let i = 0; i < E; i++) {
        const [a, b] = state.edges[i];
        const ca = state.groupMap.get(state.groups[a]) || PALETTE[0];
        const cb = state.groupMap.get(state.groups[b]) || PALETTE[0];
        C1.setHex(ca).lerp(new THREE.Color(cb), 0.5);
        instEdges.setColorAt(i, C1);
      }
      if (instEdges.instanceColor) instEdges.instanceColor.needsUpdate = true;
      meshGroup.add(instEdges);
    }

    if (state.hasRef) {
      instGhostNodes = new THREE.InstancedMesh(baseSphere, matGhost, N);
      meshGroup.add(instGhostNodes);
      if (E > 0) {
        instGhostEdges = new THREE.InstancedMesh(baseCyl, matGhost, E);
        meshGroup.add(instGhostEdges);
      }
    }

    if (state.hasForces) {
      instForceShafts = new THREE.InstancedMesh(baseCyl, matForce, N);
      instForceHeads = new THREE.InstancedMesh(baseCone, matForce, N);
      meshGroup.add(instForceShafts, instForceHeads);
    }
  }

  function getDisplayPos(i, out) {
    const n = state.nodes[i];
    if (state.hasRef && state.refNodes) {
      const r = state.refNodes[i];
      const m = state.dispMag;
      out.set(r[0] + (n[0] - r[0]) * m, r[1] + (n[1] - r[1]) * m, r[2] + (n[2] - r[2]) * m);
    } else {
      out.set(n[0], n[1], n[2]);
    }
    return out;
  }

  function setCylinderMatrix(mesh, idx, pA, pB, rad) {
    V3.subVectors(pB, pA);
    const len = V3.length();
    if (len <= 1e-9 || rad <= 0) {
      DUMMY.scale.set(0, 0, 0);
      DUMMY.updateMatrix();
      mesh.setMatrixAt(idx, DUMMY.matrix);
      return;
    }
    DUMMY.position.copy(pA).add(pB).multiplyScalar(0.5);
    DUMMY.quaternion.setFromUnitVectors(UP, V3.normalize());
    DUMMY.scale.set(rad, len, rad);
    DUMMY.updateMatrix();
    mesh.setMatrixAt(idx, DUMMY.matrix);
  }

  function updateSliceAndTransforms() {
    const N = state.nodes.length, E = state.edges.length;
    const { min, span } = state.bounds;
    const axisIdx = state.slice === 'x' ? 0 : state.slice === 'y' ? 1 : state.slice === 'z' ? 2 : -1;

    if (axisIdx >= 0) {
      const lo = min[axisIdx] + (span[axisIdx] * state.sMin) / 100;
      const hi = min[axisIdx] + (span[axisIdx] * state.sMax) / 100;
      const u = state.units ? ` ${state.units}` : '';
      sliceReadout.textContent = `${ state.slice.toUpperCase() }: [${fmt(lo, 2)}, ${fmt(hi, 2)}]${u}`;
      const eps = Math.max(span[axisIdx] * 1e-5, 1e-7);
      for (let i = 0; i < N; i++) {
        const v = state.nodes[i][axisIdx];
        state.nodeVis[i] = v >= lo - eps && v <= hi + eps;
      }
    } else {
      state.nodeVis.fill(true);
    }

    for (let i = 0; i < E; i++) {
      const [a, b] = state.edges[i];
      state.edgeVis[i] = state.nodeVis[a] && state.nodeVis[b];
    }

    populateSelectors();
    updateGeometryTransforms();
  }

  function populateSelectors() {
    nodeSel.innerHTML = '';
    const emptyN = el('option', '', '— None —');
    emptyN.value = '-1';
    nodeSel.appendChild(emptyN);
    for (let i = 0; i < state.nodes.length; i++) {
      if (!state.nodeVis[i]) continue;
      const o = el('option', '', `#${i} ${state.labels[i]} (${state.groups[i]})`);
      o.value = String(i);
      nodeSel.appendChild(o);
    }
    if (state.selNode >= 0 && !state.nodeVis[state.selNode]) {
      state.selNode = state.nodeVis.indexOf(true);
    }
    nodeSel.value = String(state.selNode);

    edgeSel.innerHTML = '';
    const emptyE = el('option', '', `— Edges (${state.edgeVis.filter(Boolean).length}) —`);
    emptyE.value = '-1';
    edgeSel.appendChild(emptyE);
    for (let i = 0; i < state.edges.length; i++) {
      if (!state.edgeVis[i]) continue;
      const [a, b] = state.edges[i];
      const o = el('option', '', `Edge #${i}: ${a} ↔ ${b}`);
      o.value = String(i);
      edgeSel.appendChild(o);
    }
    if (state.selEdge >= 0 && !state.edgeVis[state.selEdge]) state.selEdge = -1;
    edgeSel.value = String(state.selEdge);
  }

  function updateGeometryTransforms() {
    if (!webglOk || !instNodes) {
      updateSelectionHighlight();
      return;
    }
    const N = state.nodes.length, E = state.edges.length;
    const baseR = Math.max(state.bounds.radius * 0.022, 1e-4) * state.radiusScale;
    const nodeR = baseR;
    const edgeR = baseR * 0.42;

    for (let i = 0; i < N; i++) {
      if (state.nodeVis[i]) {
        getDisplayPos(i, V1);
        DUMMY.position.copy(V1);
        DUMMY.quaternion.identity();
        DUMMY.scale.setScalar(nodeR);
      } else {
        DUMMY.scale.setScalar(0);
      }
      DUMMY.updateMatrix();
      instNodes.setMatrixAt(i, DUMMY.matrix);

      if (instGhostNodes) {
        if (state.showGhost && state.nodeVis[i]) {
          const r = state.refNodes[i];
          DUMMY.position.set(r[0], r[1], r[2]);
          DUMMY.scale.setScalar(nodeR * 0.8);
        } else {
          DUMMY.scale.setScalar(0);
        }
        DUMMY.updateMatrix();
        instGhostNodes.setMatrixAt(i, DUMMY.matrix);
      }

      if (instForceShafts && instForceHeads) {
        const f = state.forces[i];
        const fMag = f ? Math.hypot(f[0], f[1], f[2]) : 0;
        if (state.showForces && state.nodeVis[i] && fMag > 1e-12 && state.maxForce > 0) {
          getDisplayPos(i, V1);
          const arrowLen = (fMag / state.maxForce) * state.bounds.radius * 0.28 * state.forceMag;
          const headLen = Math.min(arrowLen * 0.35, nodeR * 2.2);
          const shaftLen = Math.max(arrowLen - headLen, 1e-5);
          V2.set(f[0] / fMag, f[1] / fMag, f[2] / fMag);
          V3.copy(V1).addScaledVector(V2, shaftLen);
          setCylinderMatrix(instForceShafts, i, V1, V3, edgeR * 0.7);

          DUMMY.position.copy(V3).addScaledVector(V2, headLen * 0.5);
          DUMMY.quaternion.setFromUnitVectors(UP, V2);
          DUMMY.scale.set(edgeR * 1.6, headLen, edgeR * 1.6);
          DUMMY.updateMatrix();
          instForceHeads.setMatrixAt(i, DUMMY.matrix);
        } else {
          DUMMY.scale.setScalar(0);
          DUMMY.updateMatrix();
          instForceShafts.setMatrixAt(i, DUMMY.matrix);
          instForceHeads.setMatrixAt(i, DUMMY.matrix);
        }
      }
    }
    instNodes.instanceMatrix.needsUpdate = true;
    instNodes.computeBoundingSphere();
    if (instGhostNodes) instGhostNodes.instanceMatrix.needsUpdate = true;
    if (instForceShafts) {
      instForceShafts.instanceMatrix.needsUpdate = true;
      instForceHeads.instanceMatrix.needsUpdate = true;
    }

    if (instEdges) {
      for (let i = 0; i < E; i++) {
        const [a, b] = state.edges[i];
        if (state.edgeVis[i]) {
          getDisplayPos(a, V1);
          getDisplayPos(b, V2);
          setCylinderMatrix(instEdges, i, V1, V2, edgeR);
        } else {
          setCylinderMatrix(instEdges, i, V1, V1, 0);
        }
        if (instGhostEdges) {
          if (state.showGhost && state.edgeVis[i]) {
            const ra = state.refNodes[a], rb = state.refNodes[b];
            V1.set(ra[0], ra[1], ra[2]);
            V2.set(rb[0], rb[1], rb[2]);
            setCylinderMatrix(instGhostEdges, i, V1, V2, edgeR * 0.75);
          } else {
            setCylinderMatrix(instGhostEdges, i, V1, V1, 0);
          }
        }
      }
      instEdges.instanceMatrix.needsUpdate = true;
      instEdges.computeBoundingSphere();
      if (instGhostEdges) instGhostEdges.instanceMatrix.needsUpdate = true;
    }

    updateSelectionHighlight();
    requestRender();
  }

  function updateSelectionHighlight() {
    if (!webglOk) return;
    const baseR = Math.max(state.bounds.radius * 0.022, 1e-4) * state.radiusScale;
    if (state.selNode >= 0 && state.selNode < state.nodes.length && state.nodeVis[state.selNode]) {
      getDisplayPos(state.selNode, V1);
      selNodeMesh.position.copy(V1);
      selNodeMesh.scale.setScalar(baseR);
      selNodeMesh.visible = true;
    } else {
      selNodeMesh.visible = false;
    }

    if (state.selEdge >= 0 && state.selEdge < state.edges.length && state.edgeVis[state.selEdge]) {
      const [a, b] = state.edges[state.selEdge];
      getDisplayPos(a, V1);
      getDisplayPos(b, V2);
      V3.subVectors(V2, V1);
      const len = V3.length();
      selEdgeMesh.position.copy(V1).add(V2).multiplyScalar(0.5);
      selEdgeMesh.quaternion.setFromUnitVectors(UP, V3.normalize());
      selEdgeMesh.scale.set(baseR * 0.7, len, baseR * 0.7);
      selEdgeMesh.visible = true;
    } else {
      selEdgeMesh.visible = false;
    }
  }

  function updateInspector() {
    inspector.innerHTML = '';
    const u = state.units ? ` ${state.units}` : '';
    const fu = state.forceUnits ? ` ${state.forceUnits}` : '';

    if (state.selEdge >= 0 && state.selEdge < state.edges.length) {
      const [a, b] = state.edges[state.selEdge];
      const na = state.nodes[a], nb = state.nodes[b];
      const len = Math.hypot(nb[0] - na[0], nb[1] - na[1], nb[2] - na[2]);
      const title = el('div', 'sv-insp-title', `Edge #${state.selEdge}: Node ${a} (${state.labels[a]}) ↔ Node ${b} (${state.labels[b]})`);
      const coords = el('div', 'sv-mono', `Saved Endpoints: [${fmt(na[0])}, ${fmt(na[1])}, ${fmt(na[2])}] → [${fmt(nb[0])}, ${fmt(nb[1])}, ${fmt(nb[2])}]${u} | Length: ${fmt(len)}${u}`);
      inspector.append(title, coords);
      if (state.hasRef && state.refNodes) {
        const ra = state.refNodes[a], rb = state.refNodes[b];
        const rLen = Math.hypot(rb[0] - ra[0], rb[1] - ra[1], rb[2] - ra[2]);
        inspector.appendChild(el('div', 'sv-mono', `Ref Length: ${fmt(rLen)}${u} | ΔLength: ${fmt(len - rLen)}${u}`));
      }
      if (state.edgeValues && state.edgeValues[state.selEdge] !== undefined) {
        inspector.appendChild(el('div', 'sv-mono', `Saved Edge Value: ${fmt(state.edgeValues[state.selEdge])}`));
      }
      return;
    }

    if (state.selNode >= 0 && state.selNode < state.nodes.length) {
      const i = state.selNode;
      const n = state.nodes[i];
      const title = el('div', 'sv-insp-title', `Node #${i}: ${state.labels[i]} — Group: ${state.groups[i]}`);
      const coords = el('div', 'sv-mono', `Saved XYZ: (${fmt(n[0])}, ${fmt(n[1])}, ${fmt(n[2])})${u}`);
      inspector.append(title, coords);

      if (state.hasRef && state.refNodes) {
        const r = state.refNodes[i];
        const dx = n[0] - r[0], dy = n[1] - r[1], dz = n[2] - r[2];
        const dMag = Math.hypot(dx, dy, dz);
        inspector.appendChild(el('div', 'sv-mono', `Ref XYZ: (${fmt(r[0])}, ${fmt(r[1])}, ${fmt(r[2])})${u} | ΔXYZ: (${fmt(dx)}, ${fmt(dy)}, ${fmt(dz)}) | |Δ|: ${fmt(dMag)}${u} [View Mag: ${state.dispMag}x]`));
      }
      if (state.hasForces && validVec(state.forces?.[i])) {
        const f = state.forces[i];
        const fMag = Math.hypot(f[0], f[1], f[2]);
        inspector.appendChild(el('div', 'sv-mono', `Saved Vector: (${fmt(f[0])}, ${fmt(f[1])}, ${fmt(f[2])})${fu} | |F|: ${fmt(fMag)}${fu}`));
      }
      if (state.nodeValues && state.nodeValues[i] !== undefined) {
        inspector.appendChild(el('div', 'sv-mono', `Saved Node Value: ${fmt(state.nodeValues[i])}`));
      }
      return;
    }

    inspector.textContent = 'Select a node or edge to inspect original saved coordinates.';
  }

  function selectNode(index, emit = false) {
    if (disposed) return;
    const i = typeof index === 'number' && index >= 0 && index < state.nodes.length ? index : -1;
    state.selNode = i;
    state.selEdge = -1;
    nodeSel.value = String(i);
    edgeSel.value = '-1';
    updateSelectionHighlight();
    updateInspector();
    requestRender();
    if (emit && typeof onPick === 'function' && i >= 0) {
      const n = state.nodes[i];
      onPick({
        type: 'node',
        index: i,
        label: state.labels[i],
        group: state.groups[i],
        position: [n[0], n[1], n[2]],
        referencePosition: state.hasRef ? [...state.refNodes[i]] : null,
        force: state.hasForces && validVec(state.forces[i]) ? [...state.forces[i]] : null,
        value: state.nodeValues ? state.nodeValues[i] : undefined
      });
    }
  }

  function selectEdge(index, emit = false) {
    if (disposed) return;
    const i = typeof index === 'number' && index >= 0 && index < state.edges.length ? index : -1;
    state.selEdge = i;
    if (i >= 0) { state.selNode = -1; nodeSel.value = '-1'; }
    edgeSel.value = String(i);
    updateSelectionHighlight();
    updateInspector();
    requestRender();
    if (emit && typeof onPick === 'function' && i >= 0) {
      const [a, b] = state.edges[i];
      onPick({
        type: 'edge',
        index: i,
        endpoints: [a, b],
        value: state.edgeValues ? state.edgeValues[i] : undefined
      });
    }
  }

  function stepNode(dir) {
    const vis = [];
    for (let i = 0; i < state.nodes.length; i++) if (state.nodeVis[i]) vis.push(i);
    if (vis.length === 0) return;
    const cur = vis.indexOf(state.selNode);
    const next = cur === -1 ? vis[0] : vis[(cur + dir + vis.length) % vis.length];
    selectNode(next, true);
  }

  function toggleProjection() {
    if (!webglOk) return;
    state.ortho = !state.ortho;
    btnProj.textContent = state.ortho ? 'Ortho' : 'Persp';
    const prevCam = activeCam;
    activeCam = state.ortho ? oCam : pCam;
    activeCam.position.copy(prevCam.position);
    activeCam.quaternion.copy(prevCam.quaternion);
    activeCam.up.copy(prevCam.up);
    controls.object = activeCam;
    resize();
    controls.update();
    requestRender();
  }

  function setPreset(name) {
    if (!webglOk || !controls || !activeCam) return;
    const { center, radius } = state.bounds;
    const dist = radius * 2.5;
    controls.target.set(center[0], center[1], center[2]);
    activeCam.up.set(0, 1, 0);
    const p = String(name || 'iso').toLowerCase();
    if (p === 'xy') {
      activeCam.position.set(center[0], center[1], center[2] + dist);
    } else if (p === 'xz') {
      activeCam.position.set(center[0], center[1] + dist, center[2] + 1e-4);
      activeCam.up.set(0, 0, -1);
    } else if (p === 'yz') {
      activeCam.position.set(center[0] + dist, center[1], center[2]);
    } else {
      const d = dist * 0.62;
      activeCam.position.set(center[0] + d, center[1] + d * 0.85, center[2] + d);
    }
    activeCam.near = Math.max(radius * 0.005, 0.001);
    activeCam.far = Math.max(radius * 40, 100);
    if (state.ortho) {
      oCam.zoom = 1;
      syncOrthoFrustum();
    }
    activeCam.updateProjectionMatrix();
    controls.update();
    requestRender();
  }

  function syncOrthoFrustum() {
    if (!oCam || !renderer) return;
    const rect = stage.getBoundingClientRect();
    const aspect = rect.width > 0 && rect.height > 0 ? rect.width / rect.height : 1;
    const r = state.bounds.radius * 1.35;
    oCam.left = -r * aspect;
    oCam.right = r * aspect;
    oCam.top = r;
    oCam.bottom = -r;
    oCam.updateProjectionMatrix();
  }

  function getView() {
    if (!webglOk || !activeCam || !controls) return null;
    return {
      position: activeCam.position.toArray(),
      target: controls.target.toArray(),
      up: activeCam.up.toArray(),
      zoom: activeCam.zoom,
      ortho: state.ortho
    };
  }

  function setView(v) {
    if (!webglOk || !v || syncingView) return;
    syncingView = true;
    try {
      if (typeof v.ortho === 'boolean' && v.ortho !== state.ortho) toggleProjection();
      if (validVec(v.position)) activeCam.position.fromArray(v.position);
      if (validVec(v.target)) controls.target.fromArray(v.target);
      if (validVec(v.up)) activeCam.up.fromArray(v.up);
      if (isFin(v.zoom) && v.zoom > 0) {
        activeCam.zoom = v.zoom;
        activeCam.updateProjectionMatrix();
      }
      controls.update();
      requestRender();
    } finally {
      syncingView = false;
    }
  }

  function resize() {
    if (disposed || !webglOk || !renderer) return;
    const rect = stage.getBoundingClientRect();
    const w = Math.max(Math.floor(rect.width), 1);
    const h = Math.max(Math.floor(rect.height), 1);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);
    pCam.aspect = w / h;
    pCam.updateProjectionMatrix();
    syncOrthoFrustum();
    requestRender();
  }

  function requestRender() {
    if (disposed || !webglOk || isHidden || rafId) return;
    rafId = requestAnimationFrame(() => {
      rafId = 0;
      if (!disposed && webglOk && renderer && scene && activeCam) {
        renderer.render(scene, activeCam);
      }
    });
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    if (rafId) { cancelAnimationFrame(rafId); rafId = 0; }
    if (ro) ro.disconnect();
    document.removeEventListener('visibilitychange', onVisChange);
    if (webglOk) {
      clearInstanced();
      if (baseSphere) baseSphere.dispose();
      if (baseCyl) baseCyl.dispose();
      if (baseCone) baseCone.dispose();
      if (baseRing) baseRing.dispose();
      [matNode, matEdge, matGhost, matForce, matSelNode, matSelEdge].forEach(m => m && m.dispose());
      if (controls) controls.dispose();
      if (renderer) renderer.dispose();
    }
    host.innerHTML = '';
  }

  function setDisplayMagnification(value){state.dispMag=Math.max(0,Math.min(100,Number(value)||1));dispSpan.textContent='Disp '+state.dispMag+'x ';const idx=DISP_STEPS.indexOf(state.dispMag);if(idx>=0)dispInput.value=String(idx);updateGeometryTransforms();}
  return { setModel, selectNode, setPreset, getView, setView, resize, dispose, setDisplayMagnification };
}
