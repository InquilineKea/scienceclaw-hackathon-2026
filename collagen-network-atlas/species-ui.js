/* Original renderer: saved CDSM coordinates only, no molecular computation. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id),
    d = globalThis.SPECIES_PILOT;
  if (!d) {
    $('speciesStatus').textContent = 'Pilot output unavailable';
    return;
  }
  const colors = ['#20775b', '#8950a0', '#c96b32'];
  function render() {
    const w = $('speciesWindow').value,
      o = $('speciesOrder').value,
      n = +$('speciesLength').value,
      angle = (+$('speciesRotation').value * Math.PI) / 180,
      ids = ['beaver-' + w + '-' + o, 'human-' + w + '-' + o],
      coords = ids.map((id) => d.outputs.caCoordinates[id]),
      xs = coords.flatMap((a) =>
        a.filter((p, i) => i % 90 < n).map((p) => p[0]),
      ),
      xmin = Math.min(...xs),
      xmax = Math.max(...xs);
    for (let s = 0; s < 2; s++) {
      const canvas = $(s ? 'speciesHuman' : 'speciesBeaver'),
        W = canvas.clientWidth,
        H = 230,
        pixel = devicePixelRatio || 1;
      canvas.width = W * pixel;
      canvas.height = H * pixel;
      const c = canvas.getContext('2d');
      c.scale(pixel, pixel);
      c.clearRect(0, 0, W, H);
      const scale = (W - 48) / (xmax - xmin);
      for (let chain = 0; chain < 3; chain++) {
        c.strokeStyle = colors[chain];
        c.fillStyle = colors[chain];
        c.lineWidth = 1.5;
        c.beginPath();
        for (let i = 0; i < n; i++) {
          const p = coords[s][chain * 90 + i],
            x = 24 + (p[0] - xmin) * scale,
            y =
              H / 2 + (p[1] * Math.cos(angle) + p[2] * Math.sin(angle)) * scale;
          if (i) c.lineTo(x, y);
          else c.moveTo(x, y);
        }
        c.stroke();
        for (let i = 0; i < n; i++) {
          const p = coords[s][chain * 90 + i];
          c.beginPath();
          c.arc(
            24 + (p[0] - xmin) * scale,
            H / 2 + (p[1] * Math.cos(angle) + p[2] * Math.sin(angle)) * scale,
            2,
            0,
            2 * Math.PI,
          );
          c.fill();
        }
      }
      c.fillStyle = '#667168';
      c.font = '11px system-ui';
      c.fillText(
        `Axial view span: ${(xmax - xmin).toFixed(1)} Å · ${n} residues / chain`,
        24,
        H - 15,
      );
    }
    const pair = d.outputs.pairedGeometry.find(
      (p) => p.window === w && p.order === o,
    );
    $('speciesCaption').textContent =
      `${w} window · α2 in chain ${'ABC'[o.indexOf('2')]} · full 270-CA builder-frame RMS coordinate difference: ${pair.builderFrameCaRmsDifferenceAngstrom.toFixed(3)} Å. This is not a fitted structural RMSD, force or robustness score.`;
    const tasks = ids.map((id) => d.inputs.tasks.find((t) => t.id === id));
    $('speciesSequences').innerHTML =
      '<table><caption>Full 90-residue input windows; amino-acid differences are retained in the download.</caption><thead><tr><th>Chain</th><th>Beaver</th><th>Human</th></tr></thead><tbody>' +
      o
        .split('')
        .map(
          (g, i) =>
            `<tr><th>${'ABC'[i]} · COL1A${g}</th><td><code>${tasks[0].sequences[i]}</code></td><td><code>${tasks[1].sequences[i]}</code></td></tr>`,
        )
        .join('') +
      '</tbody></table>';
    $('speciesStatus').textContent =
      `${d.outputs.structureCount} constructed backbones · 270 residues / structure · no dynamics`;
  }
  for (const id of [
    'speciesWindow',
    'speciesOrder',
    'speciesLength',
    'speciesRotation',
  ])
    $(id).addEventListener('input', render);
  let timer;
  window.addEventListener('resize', () => {
    clearTimeout(timer);
    timer = setTimeout(render, 100);
  });
  render();
})();
