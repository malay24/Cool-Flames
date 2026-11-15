"""Interactive p5.js / three.js components (Streamlit Custom Components v2).

Registered once at import. JS lives in app/static/js/ and is passed inline (no
build step). Libraries load from a pinned CDN; every component shows a static
fallback if the CDN is unreachable, and honours prefers-reduced-motion.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from components import is_dark, tokens

JS = Path(__file__).resolve().parents[1] / "static" / "js"
_CSS = (JS / "interactive.css").read_text()

HERO_HTML = """
<div class="cf-hero3d">
  <div class="cf-h-canvas"></div>
  <div class="cf-h-text">
    <p class="cf-h-eyebrow">NASA Space Apps 2026 · Flame in Freefall</p>
    <h1>What NASA's microgravity fire tests can, and can't, tell a Moon base</h1>
    <p class="cf-h-sub">Pick a habitat and a fire scenario. Freefall Fire Atlas ranks NASA's 24 combustion
    investigations for each phase of the fire, explains every score, and shows where no test has
    been run.</p>
    <p class="cf-h-tag"></p>
  </div>
</div>"""
HERO_CSS = """
.cf-hero3d { position: relative; overflow: hidden; border-radius: 1rem; min-height: 300px;
  border: 1px solid var(--border, #24304a);
  background: radial-gradient(900px 260px at 85% -20%, rgba(240,122,58,0.28), transparent 60%),
              linear-gradient(135deg, var(--bg1, #111a2e) 0%, var(--bg2, #0d1220) 100%); }
.cf-h-canvas { position: absolute; inset: 0; }
.cf-h-canvas canvas { width: 100% !important; height: 100% !important; display: block; }
.cf-h-text { position: relative; padding: 2.2rem 2.4rem 2rem; max-width: 40rem;
  font-family: Inter, system-ui, sans-serif; pointer-events: none; }
.cf-h-eyebrow { margin: 0 0 .3rem; font-size: .74rem; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--accent, #f07a3a); }
.cf-h-text h1 { margin: .2rem 0 .7rem; font-family: 'Space Grotesk', Inter, sans-serif;
  font-size: 2.45rem; line-height: 1.12; color: var(--fg, #e8eaf0); }
.cf-h-sub { margin: 0; font-size: 1.06rem; line-height: 1.55; color: var(--muted, #9aa3b5); }
.cf-h-tag { margin: .9rem 0 0; font-size: .82rem; color: var(--muted, #9aa3b5); }
@media (max-width: 640px) {  /* the hero is a fixed 300 px tall: keep all text inside it on phones */
  .cf-h-text { padding: 1.1rem 1.1rem; } .cf-h-text h1 { font-size: 1.35rem; margin: .15rem 0 .45rem; }
  .cf-h-sub { font-size: .92rem; line-height: 1.5; } .cf-h-tag { display: none; } }
"""

_hero = st.components.v2.component("cool_flames.hero", html=HERO_HTML, css=HERO_CSS,
                                   js=(JS / "hero.js").read_text())
_flame = st.components.v2.component("cool_flames.flame_lab", html='<div class="cf-wrap"></div>',
                                    css=_CSS, js=(JS / "flame_lab.js").read_text())
_designer = st.components.v2.component("cool_flames.habitat_designer", html='<div class="cf-wrap"></div>',
                                       css=_CSS, js=(JS / "habitat_designer.js").read_text())


def _colors() -> dict:
    t = tokens()
    dark = is_dark()
    return {**t, "fuel": "#4a5468" if dark else "#9a8f80",
            # categorical series slots 1 and 3 (validated palette), for run dots
            "s1": "#3987e5" if dark else "#2a78d6", "s2": "#199e70" if dark else "#1baf7a"}


def _reduced() -> bool:
    return bool(st.session_state.get("reduce_motion", False))


def hero(habitat: dict, key: str = "cf_hero") -> None:
    g = habitat.get("gravity_g") or 0.0
    gravity = "microgravity" if g == 0 else f"{g:.2g} g"
    tag = f"Showing: {habitat['label']} · {habitat['o2_pct']:g}% O₂ · {gravity}"
    _hero(data={"gravity_g": habitat.get("gravity_g", 0.0), "o2_pct": habitat["o2_pct"],
                "colors": tokens(), "dark": is_dark(), "tag": tag, "reduced": _reduced()},
          key=key, height=300)


def flame_lab(params: dict, key: str = "cf_flame_lab") -> None:
    _flame(data={**params, "colors": _colors(), "reduced": _reduced()}, key=key)


def habitat_designer(runs: list, presets: list, point: dict | None, on_change,
                     key: str = "cf_designer"):
    """Returns the component result; `.point` is {o2, p, preset} after a drag/click."""
    return _designer(data={"runs": runs, "presets": presets, "point": point,
                           "colors": _colors(), "reduced": _reduced()},
                     key=key, on_point_change=on_change)
