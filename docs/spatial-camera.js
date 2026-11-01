'use strict';
(function (global) {
  const PRESETS = {
    iso: { yaw: 45, pitch: 35, label: 'Isometric' },
    xy: { yaw: 0, pitch: 90, label: 'XY (top)' },
    xz: { yaw: 0, pitch: 0, label: 'XZ (front)' },
    yz: { yaw: 270, pitch: 0, label: 'YZ (side)' }
  };

  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  function normYaw(deg) {
    if (!Number.isFinite(deg)) return 0;
    return ((deg % 360) + 360) % 360;
  }

  function resolveEl(ref) {
    if (!ref) return null;
    return typeof ref === 'string' ? document.getElementById(ref) : ref;
  }

  function prefersReducedMotion() {
    return Boolean(
      global.matchMedia &&
      global.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }

  function bindPauseOnHidden(stopCallback) {
    if (typeof stopCallback !== 'function') return;
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stopCallback('hidden');
    });
    if (global.matchMedia) {
      const mq = global.matchMedia('(prefers-reduced-motion: reduce)');
      const listener = function (e) {
        if (e.matches) stopCallback('reduced-motion');
      };
      if (typeof mq.addEventListener === 'function') {
        mq.addEventListener('change', listener);
      } else if (typeof mq.addListener === 'function') {
        mq.addListener(listener);
      }
    }
  }

  function create(options) {
    const opts = options || {};
    const defaultYaw = normYaw(opts.defaultYaw !== undefined ? opts.defaultYaw : 28);
    const defaultPitch = clamp(opts.defaultPitch !== undefined ? opts.defaultPitch : 28, -90, 90);
    const defaultZoom = clamp(opts.defaultZoom !== undefined ? opts.defaultZoom : 1, 0.5, 2.5);
    const minZoom = opts.minZoom !== undefined ? opts.minZoom : 0.5;
    const maxZoom = opts.maxZoom !== undefined ? opts.maxZoom : 2.5;

    const yawInput = resolveEl(opts.yawInput);
    const pitchInput = resolveEl(opts.pitchInput);
    const zoomInput = resolveEl(opts.zoomInput);
    const statusEl = resolveEl(opts.statusElement);
    const resetBtn = resolveEl(opts.resetButton);
    const presetButtons = Array.from(
      opts.presetButtons || document.querySelectorAll('[data-view-preset]')
    );
    const canvases = (opts.canvases || []).map(resolveEl).filter(Boolean);

    const state = {
      yaw: yawInput && Number.isFinite(Number(yawInput.value)) ? normYaw(Number(yawInput.value)) : defaultYaw,
      pitch: pitchInput && Number.isFinite(Number(pitchInput.value)) ? clamp(Number(pitchInput.value), -90, 90) : defaultPitch,
      zoom: zoomInput && Number.isFinite(Number(zoomInput.value)) ? clamp(Number(zoomInput.value), minZoom, maxZoom) : defaultZoom
    };

    function activePresetLabel() {
      for (const key of Object.keys(PRESETS)) {
        const p = PRESETS[key];
        const dy = Math.abs(((state.yaw - p.yaw + 540) % 360) - 180);
        const dp = Math.abs(state.pitch - p.pitch);
        if (dy <= 0.6 && dp <= 0.6) return p.label;
      }
      const dyDef = Math.abs(((state.yaw - defaultYaw + 540) % 360) - 180);
      const dpDef = Math.abs(state.pitch - defaultPitch);
      if (dyDef <= 0.6 && dpDef <= 0.6 && Math.abs(state.zoom - defaultZoom) <= 0.03) {
        return 'Default 3D';
      }
      return 'Free orbit';
    }

    function syncControls() {
      if (yawInput) yawInput.value = String(Math.round(state.yaw));
      if (pitchInput) pitchInput.value = String(Math.round(state.pitch));
      if (zoomInput) zoomInput.value = String(Number(state.zoom.toFixed(2)));

      for (const btn of presetButtons) {
        const key = btn.getAttribute('data-view-preset');
        if (key && PRESETS[key]) {
          const p = PRESETS[key];
          const dy = Math.abs(((state.yaw - p.yaw + 540) % 360) - 180);
          const dp = Math.abs(state.pitch - p.pitch);
          btn.setAttribute('aria-pressed', String(dy <= 0.6 && dp <= 0.6));
        }
      }

      if (statusEl) {
        statusEl.textContent =
          activePresetLabel() +
          ' · yaw ' +
          Math.round(state.yaw) +
          '° · pitch ' +
          Math.round(state.pitch) +
          '° · zoom ' +
          state.zoom.toFixed(2) +
          '× (linked panes)';
      }
    }

    function notify() {
      syncControls();
      if (typeof opts.onChange === 'function') {
        opts.onChange(api);
      }
    }

    const api = {
      get yaw() {
        return state.yaw;
      },
      get pitch() {
        return state.pitch;
      },
      get zoom() {
        return state.zoom;
      },
      setYaw: function (deg, silent) {
        state.yaw = normYaw(Number(deg));
        if (!silent) notify();
        else syncControls();
      },
      setPitch: function (deg, silent) {
        state.pitch = clamp(Number(deg), -90, 90);
        if (!silent) notify();
        else syncControls();
      },
      setZoom: function (z, silent) {
        state.zoom = clamp(Number(z), minZoom, maxZoom);
        if (!silent) notify();
        else syncControls();
      },
      stepYaw: function (deltaDeg) {
        state.yaw = normYaw(state.yaw + Number(deltaDeg));
        notify();
      },
      applyPreset: function (name) {
        if (name === 'reset') {
          state.yaw = defaultYaw;
          state.pitch = defaultPitch;
          state.zoom = defaultZoom;
          notify();
          return;
        }
        const preset = PRESETS[name];
        if (!preset) return;
        state.yaw = preset.yaw;
        state.pitch = preset.pitch;
        notify();
      },
      reset: function () {
        state.yaw = defaultYaw;
        state.pitch = defaultPitch;
        state.zoom = defaultZoom;
        notify();
      },
      project: function (q, cfg) {
        const c = cfg || {};
        const center = c.center || [0, 0, 0];
        const dx = q[0] - center[0];
        const dy = q[1] - center[1];
        const dz = q[2] - center[2];
        const yawRad = (state.yaw * Math.PI) / 180;
        const pitchRad = (state.pitch * Math.PI) / 180;
        const rx = Math.cos(yawRad) * dx - Math.sin(yawRad) * dy;
        const ry = Math.sin(yawRad) * dx + Math.cos(yawRad) * dy;
        const u = rx;
        const v = Math.cos(pitchRad) * dz + Math.sin(pitchRad) * ry;
        const ox = c.originX !== undefined ? c.originX : (c.width || 560) / 2;
        const oy = c.originY !== undefined ? c.originY : (c.height || 450) / 2;
        const sx = c.scaleX !== undefined ? c.scaleX : 1;
        const sy = c.scaleY !== undefined ? c.scaleY : sx;
        return [
          ox + state.zoom * sx * u,
          oy - state.zoom * sy * v
        ];
      },
      drawAxes: function (ctx, W, H, axisOpts) {
        const o = axisOpts || {};
        const labels = o.labels || ['x', 'y', 'z'];
        const cx = o.x !== undefined ? o.x : W - 46;
        const cy = o.y !== undefined ? o.y : 46;
        const len = o.length !== undefined ? o.length : 24;
        const yawRad = (state.yaw * Math.PI) / 180;
        const pitchRad = (state.pitch * Math.PI) / 180;

        const basis = [
          { vec: [1, 0, 0], label: labels[0], color: '#c84b31' },
          { vec: [0, 1, 0], label: labels[1], color: '#168273' },
          { vec: [0, 0, 1], label: labels[2], color: '#2563eb' }
        ].map(function (axis) {
          const dx = axis.vec[0];
          const dy = axis.vec[1];
          const dz = axis.vec[2];
          const rx = Math.cos(yawRad) * dx - Math.sin(yawRad) * dy;
          const ry = Math.sin(yawRad) * dx + Math.cos(yawRad) * dy;
          const u = rx;
          const v = Math.cos(pitchRad) * dz + Math.sin(pitchRad) * ry;
          const depth = -Math.sin(pitchRad) * dz + Math.cos(pitchRad) * ry;
          return {
            label: axis.label,
            color: axis.color,
            tx: cx + len * u,
            ty: cy - len * v,
            lx: cx + (len + 9) * u,
            ly: cy - (len + 9) * v,
            depth: depth
          };
        });

        basis.sort(function (a, b) {
          return b.depth - a.depth;
        });

        ctx.save();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.88)';
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(cx, cy, len + 15, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        ctx.font = 'bold 12px system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        for (const a of basis) {
          ctx.strokeStyle = a.color;
          ctx.fillStyle = a.color;
          ctx.lineWidth = 1.8;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(a.tx, a.ty);
          ctx.stroke();

          const dx = a.tx - cx;
          const dy = a.ty - cy;
          const l = Math.hypot(dx, dy);
          if (l > 3) {
            const ux = dx / l;
            const uy = dy / l;
            ctx.beginPath();
            ctx.moveTo(a.tx, a.ty);
            ctx.lineTo(a.tx - 5 * ux + 2.6 * uy, a.ty - 5 * uy - 2.6 * ux);
            ctx.lineTo(a.tx - 5 * ux - 2.6 * uy, a.ty - 5 * uy + 2.6 * ux);
            ctx.closePath();
            ctx.fill();
          }
          ctx.fillText(a.label, a.lx, a.ly);
        }
        ctx.restore();
      },
      syncControls: syncControls
    };

    if (yawInput) {
      yawInput.addEventListener('input', function () {
        api.setYaw(Number(yawInput.value));
      });
    }
    if (pitchInput) {
      pitchInput.addEventListener('input', function () {
        api.setPitch(Number(pitchInput.value));
      });
    }
    if (zoomInput) {
      zoomInput.addEventListener('input', function () {
        api.setZoom(Number(zoomInput.value));
      });
    }
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        if (typeof opts.onManualInteract === 'function') opts.onManualInteract();
        api.reset();
      });
    }
    for (const btn of presetButtons) {
      if (btn === resetBtn) continue;
      btn.addEventListener('click', function () {
        const preset = btn.getAttribute('data-view-preset');
        if (typeof opts.onManualInteract === 'function') opts.onManualInteract();
        api.applyPreset(preset);
      });
    }

    function attachCanvasInteractions(canvas) {
      if (!canvas.hasAttribute('tabindex')) {
        canvas.setAttribute('tabindex', '0');
      }
      const pointers = new Map();
      let lastPinchDist = null;

      canvas.addEventListener('pointerdown', function (e) {
        if (e.button !== undefined && e.button !== 0) return;
        if (typeof opts.onManualInteract === 'function') opts.onManualInteract();
        canvas.focus({ preventScroll: true });
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
        if (typeof canvas.setPointerCapture === 'function') {
          try {
            canvas.setPointerCapture(e.pointerId);
          } catch (_) {}
        }
        if (pointers.size === 2) {
          const pts = Array.from(pointers.values());
          lastPinchDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        }
      });

      canvas.addEventListener('pointermove', function (e) {
        if (!pointers.has(e.pointerId)) return;
        const prev = pointers.get(e.pointerId);
        const curr = { x: e.clientX, y: e.clientY };
        pointers.set(e.pointerId, curr);

        if (pointers.size === 1) {
          const dx = curr.x - prev.x;
          const dy = curr.y - prev.y;
          if (Math.abs(dx) > 0 || Math.abs(dy) > 0) {
            e.preventDefault();
            state.yaw = normYaw(state.yaw - dx * 0.65);
            state.pitch = clamp(state.pitch + dy * 0.55, -90, 90);
            notify();
          }
        } else if (pointers.size === 2) {
          const pts = Array.from(pointers.values());
          const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
          if (lastPinchDist && lastPinchDist > 8 && dist > 8) {
            e.preventDefault();
            state.zoom = clamp(state.zoom * (dist / lastPinchDist), minZoom, maxZoom);
            notify();
          }
          lastPinchDist = dist;
        }
      });

      function endPointer(e) {
        pointers.delete(e.pointerId);
        if (pointers.size < 2) lastPinchDist = null;
      }

      canvas.addEventListener('pointerup', endPointer);
      canvas.addEventListener('pointercancel', endPointer);
      canvas.addEventListener('lostpointercapture', endPointer);

      canvas.addEventListener('wheel', function(e) { e.preventDefault(); if (typeof opts.onManualInteract === 'function') opts.onManualInteract(); api.setZoom(state.zoom * Math.exp(-e.deltaY * 0.001)); }, {passive:false});
      canvas.addEventListener('dblclick', function () {
        api.reset();
      });

      canvas.addEventListener('keydown', function (e) {
        const step = e.shiftKey ? 15 : 5;
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          api.setYaw(state.yaw - step);
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          api.setYaw(state.yaw + step);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          api.setPitch(state.pitch + step);
        } else if (e.key === 'ArrowDown') {
          e.preventDefault();
          api.setPitch(state.pitch - step);
        } else if (e.key === '+' || e.key === '=') {
          e.preventDefault();
          api.setZoom(state.zoom + 0.1);
        } else if (e.key === '-' || e.key === '_') {
          e.preventDefault();
          api.setZoom(state.zoom - 0.1);
        } else if (e.key === '1') {
          e.preventDefault();
          api.applyPreset('xy');
        } else if (e.key === '2') {
          e.preventDefault();
          api.applyPreset('xz');
        } else if (e.key === '3') {
          e.preventDefault();
          api.applyPreset('yz');
        } else if (e.key === '4' || e.key === 'i' || e.key === 'I') {
          e.preventDefault();
          api.applyPreset('iso');
        } else if (e.key === '0' || e.key === 'r' || e.key === 'R' || e.key === 'Home') {
          e.preventDefault();
          api.reset();
        }
      });
    }

    for (const c of canvases) {
      attachCanvasInteractions(c);
    }

    syncControls();
    return api;
  }

  global.SpatialCamera = {
    create: create,
    prefersReducedMotion: prefersReducedMotion,
    bindPauseOnHidden: bindPauseOnHidden
  };
})(window);
