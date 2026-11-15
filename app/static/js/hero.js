// Animated Home hero (three.js): starfield + a glowing flame cloud whose shape follows the
// selected habitat: a sphere in microgravity, a taller teardrop as gravity rises, embers
// drifting outward (0 g) or rising (g > 0); brightness grows with O2.
// The headline is plain HTML in the component, so it still reads if three.js fails.

const REDUCED = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.min.js";

function glowTexture(THREE) {
  const c = document.createElement("canvas"); c.width = c.height = 64;
  const g = c.getContext("2d"), grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, "rgba(255,255,255,1)"); grad.addColorStop(0.35, "rgba(255,255,255,0.55)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grad; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement.querySelector(".cf-hero3d");
  const applyText = (d) => {
    root.style.setProperty("--fg", d.colors.text);
    root.style.setProperty("--muted", d.colors.muted);
    root.style.setProperty("--accent", d.colors.accent);
    root.style.setProperty("--border", d.colors.border);
    root.style.setProperty("--bg1", d.colors.paper2 || d.colors.panel);
    root.style.setProperty("--bg2", d.colors.bg);
    root.querySelector(".cf-h-tag").textContent = d.tag;
  };
  applyText(data);
  if (parentElement.__cfState) { parentElement.__cfState.data = data; return; }
  const S = { data };
  parentElement.__cfState = S;
  let stop = false, cleanup = () => {};

  // Typewriter reveal of the headline, once per mount (the full text is already in the
  // HTML, so it reads without JS; skipped when motion is reduced).
  let typing = 0;
  const h1 = root.querySelector("h1");
  if (h1 && !(data.reduced || REDUCED())) {
    const full = h1.textContent.trim();
    const caret = document.createElement("span"); caret.className = "cf-caret";
    const text = document.createTextNode("");
    h1.textContent = ""; h1.append(text, caret); h1.setAttribute("aria-label", full);
    let i = 0;
    typing = setInterval(() => {
      i = Math.min(full.length, i + 1 + (Math.random() < 0.25 ? 1 : 0));
      text.data = full.slice(0, i);
      if (i >= full.length) { clearInterval(typing); typing = 0; }
    }, 34);
  }

  import(THREE_URL).then((THREE) => {
    if (stop) return;
    const host = root.querySelector(".cf-h-canvas");
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    host.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 2, 0.1, 100);
    camera.position.set(0, 0, 9);
    const tex = glowTexture(THREE);

    // starfield
    const NS = 700, sp = new Float32Array(NS * 3);
    for (let i = 0; i < NS; i++) { sp[3 * i] = (Math.random() - 0.5) * 30; sp[3 * i + 1] = (Math.random() - 0.5) * 14; sp[3 * i + 2] = -Math.random() * 20; }
    const sg = new THREE.BufferGeometry(); sg.setAttribute("position", new THREE.BufferAttribute(sp, 3));
    const sm = new THREE.PointsMaterial({ size: 0.06, color: 0xffffff, transparent: true, opacity: 0.7, depthWrite: false });
    const stars = new THREE.Points(sg, sm); scene.add(stars);

    // flame cloud + embers
    const NF = 900, fp = new Float32Array(NF * 3), fc = new Float32Array(NF * 3), seed = new Float32Array(NF * 4);
    for (let i = 0; i < NF; i++) { seed[4 * i] = Math.random(); seed[4 * i + 1] = Math.random() * Math.PI * 2; seed[4 * i + 2] = Math.acos(2 * Math.random() - 1); seed[4 * i + 3] = Math.random(); }
    const fg = new THREE.BufferGeometry();
    fg.setAttribute("position", new THREE.BufferAttribute(fp, 3));
    fg.setAttribute("color", new THREE.BufferAttribute(fc, 3));
    const fm = new THREE.PointsMaterial({ size: 0.42, map: tex, vertexColors: true, transparent: true,
      blending: THREE.AdditiveBlending, depthWrite: false });
    const flame = new THREE.Points(fg, fm); flame.position.set(3.3, -0.2, 0); scene.add(flame);

    const resize = () => {
      const w = host.clientWidth || 800, h = host.clientHeight || 300;
      renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
      // keep the flame in the right quarter of the banner, clear of the headline
      const halfW = Math.tan((camera.fov * Math.PI) / 360) * camera.position.z * camera.aspect;
      flame.position.x = w < 640 ? halfW * 0.45 : halfW * 0.68;
      flame.position.y = w < 640 ? -1.6 : -0.2;
    };
    resize();
    const ro = new ResizeObserver(resize); ro.observe(host);

    let visible = true;
    const io = new IntersectionObserver((e) => { visible = e[0].isIntersecting; });
    io.observe(host);

    const clock = new THREE.Clock();
    const frame = () => {
      const d = S.data, g = Math.max(0, d.gravity_g || 0), o2 = d.o2_pct || 21;
      const t = clock.getElapsedTime();
      // light theme: additive glow washes out on a pale background, so use solid ember colours
      const light = !d.dark;
      const wantBlend = light ? THREE.NormalBlending : THREE.AdditiveBlending;
      if (fm.blending !== wantBlend) { fm.blending = wantBlend; fm.opacity = light ? 0.85 : 1; fm.needsUpdate = true; }
      sm.color.set(light ? 0x8a8170 : 0xece2cb);  // dust specks on the film
      const bright = Math.min(1.25, 0.45 + o2 / 60);
      const stretch = 1 + 1.6 * Math.sqrt(g);      // sphere in 0 g, teardrop under gravity
      const rise = 0.9 * Math.sqrt(g);
      const blue = Math.max(0, 1 - Math.sqrt(g) * 1.6);  // microgravity flames: dimmer, bluer
      for (let i = 0; i < NF; i++) {
        const life = (seed[4 * i] + t * (0.08 + 0.12 * seed[4 * i + 3])) % 1;
        const th = seed[4 * i + 1] + t * 0.15, ph = seed[4 * i + 2];
        const ember = seed[4 * i + 3] > 0.82;
        let r = ember ? 1.1 + life * 2.4 : 0.55 + 0.75 * life * (0.6 + 0.4 * Math.sin(t * 2 + i));
        let x = r * Math.sin(ph) * Math.cos(th), y = r * Math.cos(ph), z = r * Math.sin(ph) * Math.sin(th);
        y = y * (y > 0 ? stretch : 1 / Math.sqrt(stretch)) + (ember ? rise * life * 3 : rise * life * 0.8);
        if (y > 0) { x *= 1 / (1 + 0.35 * (stretch - 1) * (y / 3)); z *= 1 / (1 + 0.35 * (stretch - 1) * (y / 3)); }
        fp[3 * i] = x; fp[3 * i + 1] = y; fp[3 * i + 2] = z;
        const k = 1 - life;
        const hot = light ? [0.93, 0.36 + 0.25 * k, 0.1] : [1.0, 0.55 + 0.35 * k, 0.15 + 0.25 * k];
        const cold = light ? [0.2, 0.42, 0.9] : [0.35, 0.6, 1.0];
        const b = (ember ? 0.6 : 1) * bright * (0.35 + 0.65 * k);
        for (let c = 0; c < 3; c++) fc[3 * i + c] = (hot[c] * (1 - blue) + cold[c] * blue) * b;
      }
      fg.attributes.position.needsUpdate = true; fg.attributes.color.needsUpdate = true;
      stars.rotation.y = t * 0.01;
      flame.rotation.y = t * 0.1;
      renderer.render(scene, camera);
    };

    let raf = 0;
    const loop = () => { raf = requestAnimationFrame(loop); if (visible && !document.hidden) frame(); };
    if (S.data.reduced || REDUCED()) frame(); else loop();
    cleanup = () => { cancelAnimationFrame(raf); ro.disconnect(); io.disconnect(); renderer.dispose(); fg.dispose(); sg.dispose(); tex.dispose(); };
  }).catch(() => { /* static hero text stays */ });

  return () => { stop = true; if (typing) clearInterval(typing); cleanup(); delete parentElement.__cfState; };
}
