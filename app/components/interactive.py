"""Interactive p5.js / three.js components (Streamlit Custom Components v2).

Registered once at import. JS lives in app/static/js/ and is passed inline (no
build step). Libraries load from a pinned CDN; every component shows a static
fallback if the CDN is unreachable, and honours prefers-reduced-motion.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from components import is_dark, series_colors, tokens

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
/* Mission-archive hero: a frame of microfiche film with sprocket holes, typewriter text. */
.cf-hero3d { position: relative; overflow: hidden; border-radius: .2rem; min-height: 330px;
  border: 1px solid var(--border, #4a4336); box-shadow: 4px 4px 0 rgba(0,0,0,.4);
  background: radial-gradient(700px 240px at 82% 15%, rgba(216,103,63,.16), transparent 62%),
              linear-gradient(180deg, var(--bg1, #2e2a23) 0%, var(--bg2, #1c1a16) 100%); }
.cf-hero3d::before, .cf-hero3d::after { content: ""; position: absolute; left: 0; right: 0; height: 14px;
  z-index: 2; pointer-events: none; background-color: rgba(0,0,0,.45);
  background-image: repeating-linear-gradient(90deg, transparent 0 10px, rgba(236,226,203,.16) 10px 22px, transparent 22px 30px);
  background-size: 30px 6px; background-repeat: repeat-x; background-position: 0 4px; }
.cf-hero3d::before { top: 0; border-bottom: 1px solid var(--border, #4a4336); }
.cf-hero3d::after { bottom: 0; border-top: 1px solid var(--border, #4a4336); }
.cf-h-canvas { position: absolute; inset: 0; }
.cf-h-canvas canvas { width: 100% !important; height: 100% !important; display: block;
  filter: sepia(.3) saturate(1.15) contrast(1.05); }
.cf-h-text { position: relative; padding: 2.1rem 2.4rem 1.9rem; max-width: 41rem;
  font-family: 'Courier Prime', 'Courier New', monospace; pointer-events: none; }
.cf-h-eyebrow { margin: 0 0 .35rem; font-family: Jost, sans-serif; font-size: .72rem; font-weight: 600;
  letter-spacing: .2em; text-transform: uppercase; color: var(--accent, #d8673f); }
.cf-h-text h1 { margin: .15rem 0 .7rem; font-family: 'Special Elite', 'Courier New', monospace;
  font-weight: 400; font-size: 2.3rem; line-height: 1.16; color: var(--fg, #ece2cb); min-height: 2.3em; }
.cf-caret { display: inline-block; width: .5em; height: .9em; margin-left: .05em; vertical-align: -.08em;
  background: var(--accent, #d8673f); animation: cf-blink 1s steps(1) infinite; }
@keyframes cf-blink { 50% { opacity: 0; } }
.cf-h-sub { margin: 0; font-size: 1.02rem; line-height: 1.55; color: var(--muted, #a99d85); }
.cf-h-tag { display: inline-block; margin: .85rem 0 0; padding: .1rem .5rem; font-size: .8rem;
  color: var(--muted, #a99d85); border: 1px dashed var(--border, #4a4336); }
@media (max-width: 640px) {  /* the hero is a fixed 330 px tall: keep all text inside it on phones */
  .cf-h-text { padding: 1.15rem 1.1rem; } .cf-h-text h1 { font-size: 1.3rem; margin: .15rem 0 .45rem; min-height: 0; }
  .cf-h-sub { font-size: .9rem; line-height: 1.5; } .cf-h-tag { display: none; } }
@media (prefers-reduced-motion: reduce) { .cf-caret { animation: none; } }
"""

_hero = st.components.v2.component("cool_flames.hero", html=HERO_HTML, css=HERO_CSS,
                                   js=(JS / "hero.js").read_text())
_flame = st.components.v2.component("cool_flames.flame_lab", html='<div class="cf-wrap"></div>',
                                    css=_CSS, js=(JS / "flame_lab.js").read_text())
_designer = st.components.v2.component("cool_flames.habitat_designer", html='<div class="cf-wrap"></div>',
                                       css=_CSS, js=(JS / "habitat_designer.js").read_text())


def _colors() -> dict:
    t = tokens()
    s = series_colors()
    # run dots use categorical slots 1 and 3 (validated palette, same as the Gap map)
    return {**t, "fuel": "#6b6354" if is_dark() else "#9a8f80", "s1": s[0], "s2": s[2]}


def _reduced() -> bool:
    return bool(st.session_state.get("reduce_motion", False))


def hero(habitat: dict, key: str = "cf_hero") -> None:
    g = habitat.get("gravity_g") or 0.0
    gravity = "microgravity" if g == 0 else f"{g:.2g} g"
    tag = f"Showing: {habitat['label']} · {habitat['o2_pct']:g}% O₂ · {gravity}"
    _hero(data={"gravity_g": habitat.get("gravity_g", 0.0), "o2_pct": habitat["o2_pct"],
                "colors": tokens(), "dark": is_dark(), "tag": tag, "reduced": _reduced()},
          key=key, height=330)


def flame_lab(params: dict, key: str = "cf_flame_lab") -> None:
    _flame(data={**params, "colors": _colors(), "reduced": _reduced()}, key=key)


def habitat_designer(runs: list, presets: list, point: dict | None, on_change,
                     key: str = "cf_designer"):
    """Returns the component result; `.point` is {o2, p, preset} after a drag/click."""
    return _designer(data={"runs": runs, "presets": presets, "point": point,
                           "colors": _colors(), "reduced": _reduced()},
                     key=key, on_point_change=on_change)
