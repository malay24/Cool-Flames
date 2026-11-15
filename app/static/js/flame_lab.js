// Flame Lab: an ILLUSTRATIVE particle flame (not a simulation) driven by gravity,
// oxygen, airflow and fuel type. Rules and their sources:
//  - Buoyant flow scales with sqrt(g): u_b = 50*sqrt(g) cm/s, ~20 cm/s at Moon gravity
//    (Olson 2004, NASA/TM-2004-213114: lunar/Martian buoyant flows > 20 cm/s).
//  - Flames burn best in a gentle flow: too little starves them, too much blows them out;
//    a fraction of a cm/s can keep a weak flame alive (Olson 2004).
//  - Limiting O2 is about 1 point lower in microgravity with gentle flow (BASS-II PMMA:
//    17% vs 18%, Link et al. 2018). The limits used here are illustrative.
//  - A droplet flame is a spherical diffusion flame: it burns in still microgravity air
//    (FLEX droplets burned in a quiescent chamber), so the 'no flow starves it' rule is
//    applied to surface (solid) flames only.
//  - Large alkane droplets in microgravity keep burning in an invisible cool flame after the
//    visible flame goes out, seen at 14-21% O2; at 25% O2 there is no such stage
//    (Nayagam et al. 2014, FLEX).

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

// ---- illustrative model ----------------------------------------------------
export function model(d) {
  const g = Math.max(0, d.g), uAir = Math.max(0, d.u_air), o2 = d.o2;
  const uB = 50 * Math.sqrt(g);
  const U = Math.hypot(uB, uAir);
  const vigorFlow = d.fuel === "droplet"
    ? 0.75 + 0.25 * (U / (U + 10))              // diffusion-fed: no starvation in still air
    : (U / (U + 4)) * (1 / (1 + (U / 60) ** 2)); // surface flame: gentle-breeze bump
  const gentle = g === 0 && U > 2 && U < 30;
  const loi = d.fuel === "droplet" ? 13 : (gentle ? 17 : 18);
  const o2f = o2 <= loi ? 0 : Math.min(1.35, Math.pow((o2 - loi) / (35 - loi), 0.7));
  const intensity = vigorFlow * o2f;
  let state = "burning";
  if (o2 <= loi) state = "below_loi";
  else if (U < 0.3 && d.fuel !== "droplet") state = "starved";
  else if (vigorFlow < 0.12 && U > 40) state = "blowout";
  else if (vigorFlow < 0.12) state = "weak";
  return { g, uB, uAir, U, vigorFlow, loi, o2f, intensity, state };
}

const STATE_TEXT = {
  burning: "Burning",
  weak: "Weak flame: barely enough flow brings oxygen",
  starved: "Starving: no flow, oxygen arrives only by slow diffusion",
  blowout: "Blowing out: the flow is too strong",
  below_loi: "Out: oxygen below the (illustrative) limit for this fuel",
};

export default function (component) {
  const { data, parentElement } = component;
  let wrap = parentElement.querySelector(".cf-wrap");
  if (!wrap) { wrap = document.createElement("div"); wrap.className = "cf-wrap"; parentElement.appendChild(wrap); }
  if (parentElement.__cfState) { parentElement.__cfState.data = data; parentElement.__cfState.changed = true; return; }
  const S = { data, changed: true, parts: [], life: 1, drop: null };
  parentElement.__cfState = S;
  let inst = null, ro = null;

  loadP5().then((P5) => {
    inst = new P5((p) => {
      const H = 460;
      const W = () => Math.max(320, wrap.clientWidth || 700);

      p.setup = () => {
        const c = p.createCanvas(W(), H);
        c.elt.style.visibility = "visible";
        p.textFont("Courier Prime");
        if (S.data.reduced || REDUCED()) p.frameRate(4);  // reduced motion: slow, near-static
      };

      const resetDroplet = () => { S.drop = { d0: 36, d: 36, phase: "hot", t: 0 }; };

      p.draw = () => {
        const d = S.data, C = d.colors, m = model(d);
        if (S.changed) { S.changed = false; if (d.fuel === "droplet") resetDroplet(); S.life = 1; }
        p.blendMode(p.BLEND);
        p.background(C.bg);
        drawGrid(p, C);

        // flow direction: wind from the left, buoyancy up
        const dir = p.createVector(m.uAir, m.uB);
        const flowSpeed = Math.min(1, m.U / 60);
        if (dir.mag() < 1e-6) dir.set(0, 0); else dir.normalize();

        const cx = p.width * 0.5, cy = d.fuel === "droplet" ? H * 0.55 : H * 0.7;
        // fuel
        p.noStroke();
        let flameScale = 1, coolPhase = false, visible = true, radius = 60;
        if (d.fuel === "droplet") {
          const dr = S.drop || (resetDroplet(), S.drop);
          const coolPossible = m.g === 0 && d.o2 >= 14 && d.o2 <= 21.5;
          dr.t += 1;
          if (dr.phase === "hot" && m.state === "burning") dr.d = Math.sqrt(Math.max(0, dr.d * dr.d - 3.0));
          else if (dr.phase === "cool") dr.d = Math.sqrt(Math.max(0, dr.d * dr.d - 1.6));
          else dr.d = Math.sqrt(Math.max(0, dr.d * dr.d - 1.2));
          if (dr.phase === "hot" && coolPossible && dr.d < dr.d0 * 0.62) dr.phase = "cool";
          if (dr.phase === "cool" && dr.d < dr.d0 * 0.32) dr.phase = "evap";
          if (dr.phase === "hot" && dr.d < dr.d0 * 0.2) dr.phase = "evap";
          if (dr.d < 3) resetDroplet();
          coolPhase = dr.phase === "cool";
          visible = dr.phase === "hot" && m.state !== "below_loi" && m.state !== "starved";
          radius = dr.d * 2.6;
          p.fill(C.fuel); p.circle(cx, cy, dr.d);
        } else {
          p.fill(C.fuel); p.rect(cx - 90, cy, 180, 10, 3);
          radius = 46;
        }

        // flame life (decays when starved / out, recovers otherwise)
        const alive = m.state === "burning" || m.state === "weak";
        S.life = alive ? Math.min(1, S.life + 0.03) : Math.max(0, S.life - 0.012);
        flameScale = S.life * (0.45 + 0.8 * Math.min(1.2, m.intensity));

        // particles (additive glow)
        p.blendMode(p.ADD);
        const emit = visible ? Math.round(6 + 22 * Math.min(1.2, m.intensity) * S.life) : 0;
        const blue = (d.fuel === "droplet" ? 1 : 0.7) * Math.max(0, 1 - Math.min(1, m.U / 25));  // weak flow -> dim, bluish
        for (let i = 0; i < emit; i++) {
          const a = p.random(p.TWO_PI), r = radius * flameScale * p.random(0.15, 0.35);
          const base = d.fuel === "droplet"
            ? p.createVector(cx + Math.cos(a) * r, cy + Math.sin(a) * r)
            : p.createVector(cx + p.random(-40, 40), cy - 2);
          const radial = d.fuel === "droplet" ? p.createVector(Math.cos(a), Math.sin(a)).mult(0.6) : p.createVector(p.random(-0.3, 0.3), -0.3);
          const v = radial.add(p.createVector(dir.x, -dir.y).mult(0.3 + 4.2 * flowSpeed));
          S.parts.push({ x: base.x, y: base.y, vx: v.x, vy: v.y, age: 0, max: p.random(30, 60) * (0.6 + flameScale), blue });
        }
        p.noStroke();
        const next = [];
        for (const q of S.parts) {
          q.x += q.vx; q.y += q.vy; q.age += 1;
          if (q.age > q.max) continue;
          const t = q.age / q.max, s = (0.35 + 0.65 * (1 - t)) * 14 * (0.6 + flameScale);
          const hot = [255, 230 - 120 * t, 120 - 110 * t], cold = [90 + 60 * (1 - t), 140 + 60 * (1 - t), 255];
          const k = q.blue;
          p.fill(hot[0] * (1 - k) + cold[0] * k, hot[1] * (1 - k) + cold[1] * k, hot[2] * (1 - k) + cold[2] * k,
                 (1 - t) * (1 - t) * (d.fuel === "droplet" ? 26 : 15) * (0.45 + 0.55 * Math.min(1, m.intensity + 0.2)));
          p.circle(q.x, q.y, s);
          next.push(q);
        }
        S.parts = next.slice(-2200);

        // cool flame shell: invisible to cameras in FLEX, seen only by radiometers
        if (coolPhase) {
          const pulse = 0.5 + 0.5 * Math.sin(p.frameCount / 10);
          p.noFill(); p.stroke(120, 200, 255, 40 + 30 * pulse); p.strokeWeight(6);
          p.circle(cx, cy, radius * 2.1);
          p.stroke(120, 200, 255, 90); p.strokeWeight(1.5); p.circle(cx, cy, radius * 2.1);
        }
        p.blendMode(p.BLEND);

        // overlay text
        p.noStroke(); p.textAlign(p.LEFT, p.TOP);
        p.fill(C.muted); p.textSize(12);
        p.text(`${d.g_label}  ·  ${d.o2.toFixed(0)}% O₂  ·  airflow ${d.u_air.toFixed(0)} cm/s  ·  buoyant flow ≈ ${m.uB.toFixed(0)} cm/s`, 16, 14);
        p.fill(C.text); p.textSize(19);
        let label = STATE_TEXT[m.state];
        if (d.fuel === "droplet") {
          if (coolPhase) label = "Cool flame: still burning, invisible to cameras";
          else if (S.drop && S.drop.phase === "evap") label = "Flame out: droplet evaporating";
        }
        p.text(label, 16, 34);
        p.fill(C.muted); p.textSize(11); p.textAlign(p.RIGHT, p.BOTTOM);
        p.text("Illustrative model, not a simulation", p.width - 12, H - 10);
        if (m.uAir > 0.5) arrow(p, 24, H * 0.5, Math.min(70, 20 + m.uAir), C.muted);
      };

      ro = new ResizeObserver(() => { if (Math.abs(p.width - W()) > 2) p.resizeCanvas(W(), H); });
      ro.observe(wrap);
    }, wrap);
  }).catch(() => {
    wrap.innerHTML = '<div class="cf-fallback">The flame animation could not load (no connection to the p5.js CDN). The explanations below still apply.</div>';
  });

  return () => { if (ro) ro.disconnect(); if (inst) inst.remove(); delete parentElement.__cfState; };
}

function drawGrid(p, C) {
  p.stroke(C.grid); p.strokeWeight(1);
  p.drawingContext.setLineDash([2, 4]);  // graph paper
  for (let x = 0; x < p.width; x += 40) p.line(x, 0, x, p.height);
  for (let y = 0; y < p.height; y += 40) p.line(0, y, p.width, y);
  p.drawingContext.setLineDash([]);
}

function arrow(p, x, y, len, col) {
  p.stroke(col); p.strokeWeight(2); p.line(x, y, x + len, y);
  p.noStroke(); p.fill(col); p.triangle(x + len, y, x + len - 8, y - 5, x + len - 8, y + 5);
  p.textSize(10); p.textAlign(p.LEFT, p.TOP); p.text("airflow", x, y + 8);
}
