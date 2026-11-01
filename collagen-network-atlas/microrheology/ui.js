'use strict';
(() => {
  const D = MICRO_ANIMATION,
    $ = (id) => document.getElementById(id),
    g = $('view').getContext('2d');
  let timer = null,
    total = 0,
    diff = 0;
  for (const c of D) {
    const a = c.fields.find((x) => !x.damaged),
      b = c.fields.find((x) => x.damaged);
    for (let j = 0; j < a.real.length; j += 2) {
      total = Math.max(
        total,
        Math.hypot(a.real[j], a.imag[j], a.real[j + 1], a.imag[j + 1]),
        Math.hypot(b.real[j], b.imag[j], b.real[j + 1], b.imag[j + 1]),
      );
      diff = Math.max(
        diff,
        Math.hypot(
          b.real[j] - a.real[j],
          b.imag[j] - a.imag[j],
          b.real[j + 1] - a.real[j + 1],
          b.imag[j + 1] - a.imag[j + 1],
        ),
      );
    }
  }
  function draw() {
    const delta = $('mode').value === 'difference',
      phase = (+$('phase').value * Math.PI) / 180,
      gain = +$('gain').value,
      amp = (35 / (delta ? diff : total)) * gain;
    g.fillStyle = '#f7f5ed';
    g.fillRect(0, 0, 1200, 1000);
    g.fillStyle = '#203b32';
    g.font = 'bold 25px system-ui';
    g.fillText(
      delta
        ? 'Damaged − intact displacement'
        : 'Intact and damaged displacement',
      25,
      35,
    );
    $('status').textContent =
      `196 nodes · seed 17 · x drive · Ω=0.1 · phase ${$('phase').value}° · shared vector magnification ${gain}×`;
    const line = (x, y, X, Y, color, w = 1, dash = []) => {
      g.beginPath();
      g.strokeStyle = color;
      g.lineWidth = w;
      g.setLineDash(dash);
      g.moveTo(x, y);
      g.lineTo(X, Y);
      g.stroke();
    };
    const circle = (x, y, r, col) => {
      g.fillStyle = col;
      g.beginPath();
      g.arc(x, y, r, 0, Math.PI * 2);
      g.fill();
    };
    D.forEach((c, index) => {
      const ox = 25 + (index % 2) * 590,
        oy = 70 + Math.floor(index / 2) * 450,
        sc = 320 / c.size,
        X = c.net.X,
        px = (x) => ox + 120 + x * sc,
        py = (y) => oy + 390 - y * sc,
        a = c.fields.find((f) => !f.damaged),
        b = c.fields.find((f) => f.damaged);
      g.fillStyle = 'white';
      g.fillRect(ox, oy, 565, 430);
      g.fillStyle = '#203b32';
      g.font = 'bold 22px system-ui';
      g.fillText(
        (c.family === 'isotropic' ? 'Disordered' : 'Modular') +
          ' / ' +
          c.pattern,
        ox + 15,
        oy + 30,
      );
      c.net.edges.forEach((e, k) =>
        line(
          px(X[2 * e.i]),
          py(X[2 * e.i + 1]),
          px(X[2 * e.j]),
          py(X[2 * e.j + 1]),
          c.lesion.includes(k) ? '#c52233' : '#c4cdc0',
          c.lesion.includes(k) ? 2 : 0.7,
          c.lesion.includes(k) ? [4, 3] : [],
        ),
      );
      c.net.links.forEach((e) =>
        line(
          px(X[2 * e.i]),
          py(X[2 * e.i + 1]),
          px(X[2 * e.j]),
          py(X[2 * e.j + 1]),
          '#d2c7df',
          0.6,
          [3, 3],
        ),
      );
      for (let j = 0; j < c.free.length; j += 2) {
        const i = c.free[j],
          x = px(X[i]),
          y = py(X[i + 1]),
          ax = a.real[j] * Math.cos(phase) - a.imag[j] * Math.sin(phase),
          ay =
            a.real[j + 1] * Math.cos(phase) - a.imag[j + 1] * Math.sin(phase),
          bx = b.real[j] * Math.cos(phase) - b.imag[j] * Math.sin(phase),
          by =
            b.real[j + 1] * Math.cos(phase) - b.imag[j + 1] * Math.sin(phase);
        if (!delta) line(x, y, x + ax * amp, y - ay * amp, '#999', 1.8);
        const dx = (delta ? bx - ax : bx) * amp,
          dy = (delta ? by - ay : by) * amp;
        line(x, y, x + dx, y - dy, '#2b7352', 1.4);
        circle(x + dx, y - dy, 1.5, '#2b7352');
        if (c.probe.includes(i / 2)) circle(x, y, 3, '#db8b16');
      }
    });
  }
  for (const id of ['mode', 'phase', 'gain']) $(id).oninput = draw;
  $('play').onclick = () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
      $('play').textContent = 'Play';
    } else {
      timer = setInterval(() => {
        $('phase').value = (+$('phase').value + 4) % 360;
        draw();
      }, 60);
      $('play').textContent = 'Pause';
    }
  };
  draw();
})();
