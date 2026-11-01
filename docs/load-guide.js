/* Original display-only loading annotations; the numerical model is unchanged. */
(function (root) {
  'use strict';
  const modes = {
    tension: {
      title: 'Pull the right edge along +X',
      detail:
        'Left-edge x is held at 0; right-edge x is prescribed as 1 + ε. Vertical motion is free except at the bottom-left pin.',
      direction:
        'Uniaxial X displacement. No Y traction is prescribed; individual grip forces emerge from the network.',
      formula: 'uₓ(left) = 0; uₓ(right) = ε; uᵧ(bottom-left) = 0',
    },
    tensionY: {
      title: 'Pull the top edge along +Y',
      detail:
        'Bottom-edge y is held at 0; top-edge y is prescribed as 1 + ε. Horizontal motion is free except at the bottom-left pin.',
      direction:
        'Uniaxial Y displacement. No X traction is prescribed; individual grip forces emerge from the network.',
      formula: 'uᵧ(bottom) = 0; uᵧ(top) = ε; uₓ(bottom-left) = 0',
    },
    shear: {
      title: 'Slide the top edge along +X',
      detail:
        'The bottom edge is fixed in X and Y. The top moves horizontally by γ while its height stays fixed. Side-edge nodes are free except at the corners.',
      direction:
        'Directional simple shear, not an isotropic pressure. At small strain its principal extension/compression directions are ±45°.',
      formula: 'u(bottom) = 0; uₓ(top) = γ; uᵧ(top) = 0',
    },
    compression: {
      title: 'Push the right edge along −X',
      detail:
        'Left-edge x stays at 0; right-edge x becomes 1 − ε. Vertical motion is free except at the bottom-left pin.',
      direction:
        'Uniaxial X compression with free lateral motion. A uniform displacement does not imply uniform fiber stress.',
      formula: 'uₓ(left) = 0; uₓ(right) = −ε; uᵧ(bottom-left) = 0',
    },
    confined: {
      title: 'Push along −X with lateral confinement',
      detail:
        'The right edge moves left. Left-edge x is held; top and bottom y coordinates stay fixed. The boundary nodes can slide tangentially unless also constrained at a corner.',
      direction:
        'X shortening with zero Y displacement at the lateral boundaries. Lateral reactions develop; this is not hydrostatic pressure.',
      formula: 'uₓ(right) = −ε; uₓ(left) = 0; uᵧ(top/bottom) = 0',
    },
    biaxial: {
      title: 'Move all four sides inward equally',
      detail:
        'Opposite faces approach the center with equal normal strain in X and Y. Tangential coordinates are free except where the two boundary constraints meet at a corner.',
      direction:
        'Equal biaxial normal strain in 2D. An anisotropic network can still have unequal X and Y stresses. No fluid or 3D hydrostatic pressure is imposed.',
      formula: 'x′ = ½ + (x − ½)(1 − ε) on X faces; similarly for Y',
    },
    pulse: {
      title: 'Accelerate every node along +X; clamp the left',
      detail:
        'Every node is assigned the same body force per unit mass, along +X. All left-edge nodes are held in both coordinates. Their support reaction includes their own applied body force.',
      direction:
        'Spatially uniform but entirely X-directed body forcing. The clamp converts the acceleration into internal loading.',
      formula: 'fᵢ = mᵢ a(t) eₓ; x(left) = 0 and y(left) held',
    },
    free: {
      title: 'Accelerate every node along +X; no clamps',
      detail:
        'All nodes are free and receive the same body force per unit mass. There are no supports or imposed edge displacements.',
      direction:
        'Entirely X-directed acceleration with no imposed relative motion. This control translates nearly rigidly and has negligible internal strain.',
      formula: 'fᵢ = mᵢ a(t) eₓ; no prescribed node coordinates',
    },
  };
  function fabric(net) {
    let xx = 0,
      xy = 0,
      yy = 0,
      volume = 0;
    for (const e of net.edges) {
      const dx = (net.X[2 * e.j] - net.X[2 * e.i]) / e.L,
        dy = (net.X[2 * e.j + 1] - net.X[2 * e.i + 1]) / e.L,
        v = e.A * e.L;
      xx += v * dx * dx;
      xy += v * dx * dy;
      yy += v * dy * dy;
      volume += v;
    }
    return {
      anisotropy: Math.sqrt((xx - yy) ** 2 + 4 * xy * xy) / volume,
      alignmentX: xx / volume,
      alignmentY: yy / volume,
    };
  }
  function markers(net, mode) {
    return Array.from({ length: net.N }, (_, i) => {
      const x = net.X[2 * i],
        y = net.X[2 * i + 1],
        m = {
          node: i,
          holdX: false,
          holdY: false,
          driveX: 0,
          driveY: 0,
          bodyX: mode === 'pulse' || mode === 'free',
        };
      if (mode === 'shear') {
        m.holdX = y === 0;
        m.holdY = y === 0 || y === 1;
        if (y === 1) m.driveX = 1;
      } else if (mode === 'biaxial') {
        if (x === 0 || x === 1) m.driveX = x === 0 ? 1 : -1;
        if (y === 0 || y === 1) m.driveY = y === 0 ? 1 : -1;
      } else if (mode === 'pulse') {
        m.holdX = m.holdY = x === 0;
      } else if (mode !== 'free') {
        const a = mode === 'tensionY',
          v = a ? y : x,
          sign = mode === 'compression' || mode === 'confined' ? -1 : 1;
        if (v === 0) {
          if (a) m.holdY = true;
          else m.holdX = true;
          if ((a ? x : y) === 0) {
            if (a) m.holdX = true;
            else m.holdY = true;
          }
        }
        if (v === 1) {
          if (a) m.driveY = sign;
          else m.driveX = sign;
        }
        if (mode === 'confined' && (y === 0 || y === 1)) m.holdY = true;
      }
      return m;
    });
  }
  function diagram(net, mode) {
    let s =
      '<title id="loadDiagramTitle">' +
      modes[mode].title +
      '. Schematic boundary directions, not force magnitudes.</title><rect x="76" y="36" width="180" height="180" rx="3" fill="#142a29"/>';
    const arrow = (x, y, dx, dy) => {
      const X = x + dx,
        Y = y + dy,
        a = Math.atan2(dy, dx),
        r = 4;
      return `<path d="M${x} ${y}L${X} ${Y}M${X - r * Math.cos(a - 0.5)} ${Y - r * Math.sin(a - 0.5)}L${X} ${Y}L${X - r * Math.cos(a + 0.5)} ${Y - r * Math.sin(a + 0.5)}" fill="none" stroke="#b6dd8e" stroke-width="1.7"/>`;
    };
    for (const m of markers(net, mode)) {
      const x = 76 + 180 * net.X[2 * m.node],
        y = 216 - 180 * net.X[2 * m.node + 1];
      if (m.holdX)
        s += `<path d="M${x - 4} ${y - 6}v12" stroke="#8bd9df" stroke-width="2.5"/>`;
      if (m.holdY)
        s += `<path d="M${x - 6} ${y + 4}h12" stroke="#8bd9df" stroke-width="2.5"/>`;
      if (m.driveX) s += arrow(x, y, m.driveX * 20, 0);
      if (m.driveY) s += arrow(x, y, 0, -m.driveY * 20);
      if (m.bodyX) s += arrow(x, y, 16, 0);
      s += `<circle cx="${x}" cy="${y}" r="2.3" fill="#dce7d7"/>`;
    }
    return (
      s +
      '<text x="270" y="239" fill="#64736e" font-size="12">X →</text><text x="32" y="25" fill="#64736e" font-size="12">Y ↑</text><text x="100" y="247" fill="#64736e" font-size="10">Reference square · L₀ = 1</text>'
    );
  }
  root.AtlasLoadGuide = { modes, fabric, markers, diagram };
  if (typeof module !== 'undefined') module.exports = root.AtlasLoadGuide;
})(globalThis);
