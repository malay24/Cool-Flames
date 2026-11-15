// Habitat designer: drag a point on the O2-vs-pressure plane to design an atmosphere.
// Two-way Streamlit component (st.components.v2). Sends {o2, p, preset} on release.
// Real test runs are drawn as faint dots; the halo shows the same "nearby" radius as
// the Gap map (normalized distance 0.1: about 10 O2 points or 1.5 psi).

const REDUCED = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const P5_URL = "https://cdn.jsdelivr.net/npm/p5@1.11.1/lib/p5.min.js";

function loadP5() {
  if (!window.__cfP5) {
    window.__cfP5 = new Promise((resolve, reject) => {
      if (window.p5) return resolve(window.p5);
      const s = document.createElement("script");
      s.src = P5_URL;
      s.onload = () => resolve(window.p5);
      s.onerror = () => { window.__cfP5 = null; reject(new Error("p5 could not load")); };
      document.head.appendChild(s);
    });
  }
  return window.__cfP5;
}

const XMAX = 30, YMAX = 100, M = { l: 52, r: 18, t: 18, b: 44 };
const PPO2 = [[2.8, [4, 4]], [3.1, [10, 6]], [4.3, [18, 6]]];
const LABEL_OFF = { suit: [10, 4], exploration: [-10, -12], moon_brief: [10, 12], iss: [10, -12] };

function nearby(runs, o2, p) {
  let n = 0;
  for (const [rp, ro2] of runs) {
    const dx = (ro2 - o2) / 100, dy = (rp - p) / 14.7;
    if (dx * dx + dy * dy <= 0.01) n++;
  }
  return n;
}

export default function (component) {
  const { data, parentElement, setStateValue } = component;
  let wrap = parentElement.querySelector(".cf-wrap");
  if (!wrap) { wrap = document.createElement("div"); wrap.className = "cf-wrap"; parentElement.appendChild(wrap); }

  // Re-render with new data: update the live sketch instead of rebuilding it.
  if (parentElement.__cfState) { parentElement.__cfState.data = data; return; }
  const state = { data, dragging: false, point: data.point ? { ...data.point } : { p: 14.7, o2: 21 } };
  parentElement.__cfState = state;
  let inst = null, ro = null;

  loadP5().then((P5) => {
    inst = new P5((p) => {
      const H = 400;
      const W = () => Math.max(320, wrap.clientWidth || 640);
      const X = (v) => M.l + (v / XMAX) * (p.width - M.l - M.r);
      const Y = (v) => p.height - M.b - (v / YMAX) * (p.height - M.t - M.b);
      const iX = (px) => ((px - M.l) / (p.width - M.l - M.r)) * XMAX;
      const iY = (py) => ((p.height - M.b - py) / (p.height - M.t - M.b)) * YMAX;
      const clampPt = (pt) => ({ p: Math.min(XMAX, Math.max(0.5, pt.p)), o2: Math.min(100, Math.max(5, pt.o2)) });
      const inPlot = (x, y) => x >= M.l && x <= p.width - M.r && y >= M.t && y <= p.height - M.b;

      p.setup = () => {
        const c = p.createCanvas(W(), H);
        c.elt.style.visibility = "visible";  // p5 un-hides canvases via document; we live in a shadow root
        p.textFont("Inter");
        if (state.data.reduced || REDUCED()) p.noLoop();
      };

      p.draw = () => {
        const d = state.data, C = d.colors;
        if (!state.dragging && d.point) state.point = { ...d.point };
        p.background(C.panel);
        // grid + axes
        p.stroke(C.grid); p.strokeWeight(1);
        for (let v = 0; v <= XMAX; v += 5) p.line(X(v), Y(0), X(v), Y(YMAX));
        for (let v = 0; v <= YMAX; v += 20) p.line(X(0), Y(v), X(XMAX), Y(v));
        p.noStroke(); p.fill(C.muted); p.textSize(11);
        p.textAlign(p.CENTER, p.TOP);
        for (let v = 0; v <= XMAX; v += 5) p.text(v, X(v), Y(0) + 6);
        p.text("Total pressure (psi)", (X(0) + X(XMAX)) / 2, p.height - 18);
        p.textAlign(p.RIGHT, p.CENTER);
        for (let v = 0; v <= YMAX; v += 20) p.text(v, X(0) - 8, Y(v));
        p.push(); p.translate(14, (Y(0) + Y(YMAX)) / 2); p.rotate(-p.HALF_PI);
        p.textAlign(p.CENTER, p.CENTER); p.text("O₂ (% by volume)", 0, 0); p.pop();

        // iso-ppO2 curves (o2 = 100 * pp / p)
        p.noFill(); p.stroke(C.muted); p.strokeWeight(1.3);
        for (const [pp, dash] of PPO2) {
          p.drawingContext.setLineDash(dash);
          p.beginShape();
          for (let x = 0.5; x <= XMAX; x += 0.25) { const o2 = (100 * pp) / x; if (o2 <= YMAX) p.vertex(X(x), Y(o2)); }
          p.endShape();
          p.drawingContext.setLineDash([]);
        }
        // legend for the curves (bottom-right, clear of the data)
        p.noStroke(); p.fill(C.muted); p.textSize(10); p.textAlign(p.RIGHT, p.BOTTOM);
        p.text("dashed curves: equal O₂ partial pressure 2.8 · 3.1 · 4.3 psi", X(XMAX) - 4, Y(0) - 6);

        // real test runs
        p.noStroke();
        for (const [rp, ro2, a] of d.runs) {
          if (rp > XMAX) continue;
          p.fill(a === "suppression" ? C.s1 : C.s2); p.circle(X(rp), Y(ro2), 4);
        }

        // presets
        p.textSize(11);
        for (const h of d.presets) {
          const x = X(h.p), y = Y(h.o2);
          p.fill(C.text); p.noStroke(); star(p, x, y, 4, 9);
          const off = LABEL_OFF[h.key] || [10, -10];
          p.fill(C.muted); p.textAlign(off[0] < 0 ? p.RIGHT : p.LEFT, p.CENTER); p.text(h.label, x + off[0], y + off[1]);
        }

        // handle, halo and readout
        const pt = state.point, hx = X(pt.p), hy = Y(pt.o2);
        const rx = X(pt.p + 1.47) - hx, ry = Y(pt.o2) - Y(pt.o2 + 10);
        p.noStroke(); p.fill(p.color(C.accent + "33")); p.ellipse(hx, hy, rx * 2, ry * 2);
        p.stroke(C.accent); p.strokeWeight(1); p.noFill(); p.ellipse(hx, hy, rx * 2, ry * 2);
        p.fill(C.accent); p.stroke(C.panel); p.strokeWeight(3);
        p.circle(hx, hy, state.dragging ? 20 : 16 + 2 * Math.sin(p.frameCount / 15));
        const n = nearby(d.runs, pt.o2, pt.p), pp = (pt.o2 / 100) * pt.p;
        const msg = `O₂ ${pt.o2.toFixed(1)}%  ·  ${pt.p.toFixed(1)} psi  ·  ppO₂ ${pp.toFixed(2)} psi  ·  ${n} test run${n === 1 ? "" : "s"} nearby`;
        p.noStroke(); p.textSize(13); p.textAlign(p.LEFT, p.TOP);
        const tw = p.textWidth(msg) + 20;
        p.fill(C.bg); p.rect(p.width - M.r - tw, M.t + 6, tw, 26, 6);
        p.fill(n ? C.text : C.accent); p.text(msg, p.width - M.r - tw + 10, M.t + 12);
        if (!state.dragging) {
          p.fill(C.muted); p.textSize(11); p.textAlign(p.LEFT, p.TOP);
          p.textAlign(p.LEFT, p.BOTTOM);
          p.text("Drag the orange point, or click a preset star", M.l + 8, Y(0) - 6);
        }
      };

      let preset = null;
      p.mousePressed = () => {
        if (!inPlot(p.mouseX, p.mouseY)) return;
        preset = null;
        for (const h of state.data.presets) {
          if (p.dist(p.mouseX, p.mouseY, X(h.p), Y(h.o2)) < 12) { preset = h.key; state.point = { p: h.p, o2: h.o2 }; }
        }
        state.dragging = true;
        if (!preset) state.point = clampPt({ p: iX(p.mouseX), o2: iY(p.mouseY) });
        p.redraw();
        return false;
      };
      p.mouseDragged = () => {
        if (!state.dragging) return;
        preset = null;
        state.point = clampPt({ p: iX(p.mouseX), o2: iY(p.mouseY) });
        p.redraw();
        return false;
      };
      p.mouseReleased = () => {
        if (!state.dragging) return;
        state.dragging = false;
        const pt = state.point;
        setStateValue("point", { o2: Math.round(pt.o2 * 10) / 10, p: Math.round(pt.p * 10) / 10, preset });
        p.redraw();
      };
      p.touchStarted = p.mousePressed; p.touchMoved = p.mouseDragged; p.touchEnded = p.mouseReleased;

      ro = new ResizeObserver(() => { if (Math.abs(p.width - W()) > 2) { p.resizeCanvas(W(), H); p.redraw(); } });
      ro.observe(wrap);
    }, wrap);
  }).catch(() => {
    wrap.innerHTML = '<div class="cf-fallback">The interactive designer could not load (no connection to the p5.js CDN). Use the number inputs below instead.</div>';
  });

  return () => { if (ro) ro.disconnect(); if (inst) inst.remove(); delete parentElement.__cfState; };
}

function star(p, x, y, r1, r2) {
  p.beginShape();
  for (let i = 0; i < 10; i++) {
    const r = i % 2 ? r1 : r2, a = -Math.PI / 2 + (i * Math.PI) / 5;
    p.vertex(x + r * Math.cos(a), y + r * Math.sin(a));
  }
  p.endShape(p.CLOSE);
}
