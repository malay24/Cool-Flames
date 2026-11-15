"""Shared UI: theme helpers, page header, sidebar habitat picker, cards, footer.

The router (app/Home.py) calls `inject_css()` and `habitat_sidebar()` once per
run; every view calls `current_habitat()` and `page_header()`. Streamlit puts
app/ on sys.path; this module also adds the repo root so views can import
core/ and ai/.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from components.data import habitats  # noqa: E402

DISCLAIMER = ("Research and reference tool, not an operational safety system. "
              "Data: NASA PSI (CC0).")
DEFAULT_HABITAT = "iss"
# Badge colours follow the chart series: suppression blue, prevention rust, basic verdigris,
# detection ochre (see series_colors / gap map).
AREA_COLORS = {"prevention": "orange", "suppression": "blue", "detection": "yellow",
               "basic": "green", "modelling": "gray"}
AREA_ICONS = {"prevention": ":material/local_fire_department:", "suppression": ":material/fire_extinguisher:",
              "detection": ":material/sensors:", "basic": ":material/science:",
              "modelling": ":material/model_training:"}

# Theme tokens mirrored from .streamlit/config.toml (for charts, CSS and the animations).
# "dark" is the mission-archive microfiche look every visitor gets; "light" is only a
# fallback if someone switches theme in the app menu.
THEMES = {
    "dark": {"bg": "#1c1a16", "panel": "#26231e", "paper2": "#2e2a23", "border": "#4a4336",
             "text": "#ece2cb", "muted": "#a99d85", "accent": "#d8673f", "link": "#8fb4dc",
             "grid": "#33302a", "axis": "#5a5244"},
    "light": {"bg": "#efe6d2", "panel": "#e7dcc3", "paper2": "#e0d3b6", "border": "#b6a37f",
              "text": "#2a2723", "muted": "#665b47", "accent": "#a63d26", "link": "#1f4a73",
              "grid": "#d6c8a8", "axis": "#9c8b6a"},
}
# Categorical series, fixed order (ink blue, rust, verdigris, ochre). Dark set checked with
# the dataviz validate_palette.js on #1c1a16: all checks pass. Light = the previous validated set.
SERIES = {"dark": ["#4f8bd0", "#d8673f", "#3f9c74", "#bb8316"],
          "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]}
SERIES_OTHER = "#8a8170"
FONT_STACK = "'Courier Prime', 'Courier New', Courier, monospace"
CSS_FILE = Path(__file__).resolve().parents[1] / "static" / "css" / "archive.css"


def is_dark() -> bool:
    # Theme is forced dark in .streamlit/config.toml; default to dark unless the
    # viewer explicitly switches to light, so custom CSS/charts stay in step.
    theme = getattr(st.context, "theme", None)
    return getattr(theme, "type", "dark") != "light"


def tokens() -> dict:
    return THEMES["dark" if is_dark() else "light"]


def series_colors() -> list[str]:
    """The four validated categorical colours for the current mode, in fixed order."""
    return SERIES["dark" if is_dark() else "light"]


def style_figure(fig, **layout):
    """Archive look for any Plotly figure: typewriter text, dotted graph-paper grid, ink axes.

    Call after the figure's own update_layout; ranges, titles and traces are kept.
    """
    t = tokens()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_STACK, color=t["text"], size=13),
        hoverlabel=dict(bgcolor=t["paper2"], bordercolor=t["border"], font_color=t["text"],
                        font_family=FONT_STACK),
        legend=dict(font=dict(color=t["muted"], family=FONT_STACK)),
        **layout,
    )
    ax = dict(gridcolor=t["grid"], griddash="dot", linecolor=t["axis"], linewidth=1, zeroline=False,
              tickfont=dict(color=t["muted"], family=FONT_STACK),
              title_font=dict(color=t["muted"], family=FONT_STACK), ticks="outside",
              tickcolor=t["axis"], ticklen=4)
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax)
    return fig


# ---------------------------------------------------------------- shell

def inject_css() -> None:
    """Load the archive stylesheet (app/static/css/archive.css) with theme variables on :root."""
    t = tokens()
    variables = "".join(f"--cf-{k}:{v};" for k, v in t.items())
    variables += "".join(f"--cf-s{n}:{c};" for n, c in enumerate(series_colors(), 1))
    # The file comes first: its @import (Jost) must precede every other rule.
    st.html(f"<style>{CSS_FILE.read_text()}\n:root{{{variables}}}</style>")


# ---------------------------------------------------------------- rubber stamps

# Only these words may be stamped (CLAUDE.md: never "safe", "approved" and the like).
STAMP_WORDS = {"NO DATA", "UNTESTED", "PARTIAL GRAVITY · NO DATA", "ILLUSTRATIVE", "AI-WRITTEN",
               "VERBATIM", "ARCHIVE COPY", "0 RUNS NEARBY", "DEMO DATA"}
_FILE_STAMP = re.compile(r"^FILE PSI-\d+$")


def stamp_html(text: str, tone: str = "rust") -> str:
    """A rotated rubber stamp. Raises ValueError for any word outside the allow-list."""
    if text not in STAMP_WORDS and not _FILE_STAMP.match(text):
        raise ValueError(f"not an allowed stamp: {text!r}")
    tone = tone if tone in ("rust", "ink", "ochre") else "rust"
    return f'<span class="cf-stamp cf-stamp-{tone}" role="note">{text}</span>'


def stamp(text: str, tone: str = "rust") -> None:
    st.html(stamp_html(text, tone))


def habitat_label(key: str, habs: dict | None = None) -> str:
    h = (habs or habitats())[key]
    return f"{h['label']} ({h['o2_pct']:g}% O₂, {h['pressure_psi']:g} psi)"


def habitat_sidebar() -> str:
    """Sidebar habitat picker + atmosphere card. Rendered once by the router."""
    habs = habitats()
    keys = list(habs)
    if st.session_state.get("habitat") not in keys:
        st.session_state["habitat"] = DEFAULT_HABITAT if DEFAULT_HABITAT in keys else keys[0]
    with st.sidebar:
        choice = st.selectbox(
            "Habitat atmosphere", keys, index=keys.index(st.session_state["habitat"]),
            format_func=lambda k: habs[k]["label"],
            help="Every page uses this habitat: ranking distance, gap-map highlight, warnings.",
        )
        st.session_state["habitat"] = choice
        h = habs[choice]
        g = h.get("gravity_g") or 0.0
        gravity = "microgravity" if g == 0 else f"{g:.2g} g"
        ppo2 = h.get("ppo2_psi", h["o2_pct"] / 100 * h["pressure_psi"])
        mark = stamp_html("PARTIAL GRAVITY · NO DATA") if h.get("partial_gravity") else ""
        st.html(f"""<div class="cf-atmo"><div class="cf-atmo-h">Mission card</div>
            <div class="cf-atmo-row"><span>O₂</span><span class="v">{h['o2_pct']:g}%</span></div>
            <div class="cf-atmo-row"><span>Total</span><span class="v">{h['pressure_psi']:g} psi</span></div>
            <div class="cf-atmo-row"><span>ppO₂</span><span class="v">{ppo2:.2f} psi</span></div>
            <div class="cf-atmo-row"><span>Gravity</span><span class="v">{gravity}</span></div>
            {mark}</div>""")
        st.caption(DISCLAIMER)
    return choice


def current_habitat() -> str:
    """Selected habitat key (works when a view runs on its own, e.g. in tests)."""
    key = st.session_state.get("habitat")
    return key if key in habitats() else DEFAULT_HABITAT


def page_header(eyebrow: str, title: str, subtitle: str = "") -> None:
    """File-reference header: typed folder label, typewriter title, double rule."""
    st.html(f'<p class="cf-eyebrow"><span class="cf-file">File</span>{eyebrow}</p>')
    st.title(title, anchor=False)
    st.html('<div class="cf-rule"></div>' + (f'<p class="cf-sub">{subtitle}</p>' if subtitle else ""))


def stat_row(items: list[tuple]) -> None:
    """items: (label, value) or (label, value, help)."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, *rest = item
        col.metric(label, value, border=True, help=rest[0] if rest else None)


def footer() -> None:
    st.html('<div class="cf-foot"><div class="cf-rule"></div>' + stamp_html("ARCHIVE COPY", "ink")
            + '<p>Research and reference tool, not an operational safety system · Data: NASA '
            'Physical Sciences Informatics (CC0) · every claim links its DOI</p></div>')


def demo_badge(is_demo: bool) -> None:
    if is_demo:
        st.html(stamp_html("DEMO DATA", "ochre")
                + '<span class="cf-stamp-note">real data files not built yet</span>')


# ---------------------------------------------------------------- small formatters

def doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


def doi_link(doi: str) -> str:
    """Markdown link for a DOI (PSI requires citing each investigation by DOI)."""
    return f"[doi:{doi}]({doi_url(doi)})" if doi else "DOI not listed"


def area_badge(area: str) -> str:
    return f":{AREA_COLORS.get(area, 'gray')}-badge[{area}]"


def fmt_range(rng, unit: str) -> str:
    if not rng:
        return "not reported"
    lo, hi = rng
    return f"{lo:g} {unit}" if lo == hi else f"{lo:g}–{hi:g} {unit}"


def chips(pairs: list[tuple[str, str]]) -> str:
    return "".join(f'<span class="cf-chip"><b>{k}</b>{v}</span>' for k, v in pairs)


DOSSIER_PAGE = str(Path(__file__).resolve().parents[1] / "views" / "dossier.py")


def dossier_link(psi_id: str, label: str = "Open dossier") -> None:
    """Link to one investigation's dossier (keeps the session, so the habitat stays)."""
    try:
        st.page_link(DOSSIER_PAGE, label=label, icon=":material/description:",
                     query_params={"id": psi_id})
    except Exception:  # view run on its own, without the router: plain link
        st.markdown(f"[{label}](dossier?id={psi_id})")


# ---------------------------------------------------------------- cards

def card_head(psi_id: str, area: str) -> str:
    """Typed index-card header row: PSI-99 ········ PREVENTION."""
    return (f'<div class="cf-cardhead"><span>{psi_id}</span><span class="cf-leader"></span>'
            f'<span class="cf-area cf-area-{area}">{area}</span></div>')


def investigation_card(inv: dict) -> None:
    """One index card for the Investigations grid."""
    with st.container(border=True, key=f"cfcard_{inv['psi_id']}"):
        st.html(card_head(inv["psi_id"], inv["area"]))
        st.markdown(f"#### {inv['name']}")
        if inv.get("name") != inv.get("title") and inv.get("title"):
            st.caption(inv["title"])
        summary = inv.get("summary_3line") or ""
        if summary:
            st.markdown(summary.replace("\n", "  \n"))
        else:
            st.caption("AI summary pending.")
        fuels = ", ".join(inv.get("fuels") or []) or ", ".join(inv.get("fuel_types") or []) or "none"
        st.html(chips([("Fuel", fuels)]) + "<br>" + chips([
            ("O₂", fmt_range(inv.get("o2_range"), "%")),
            ("Pressure", fmt_range(inv.get("pressure_range"), "psi")),
            ("Airflow", fmt_range(inv.get("airflow_range"), "cm/s")),
        ]))
        runs = inv.get("n_runs") or 0
        std = inv.get("n_standardized_runs") or 0
        if not runs:
            run_txt = "text only, no test table"
        elif std and std < runs:
            run_txt = f"{runs} test runs ({std} standardized)"
        elif not std:
            run_txt = f"{runs} test runs (table not standardized)"
        else:
            run_txt = f"{runs} test runs"
        st.caption(f"{run_txt} · {inv.get('n_publications', 0)} publications · "
                   f"{inv.get('platform') or 'ground study'}")
        st.markdown(doi_link(inv.get("doi", "")))
        if inv.get("key_findings"):
            with st.expander("Key findings"):
                for kf in inv["key_findings"]:
                    st.markdown(f"- {kf}")
        dossier_link(inv["psi_id"])


COMP_LABELS = {"area_match": "Area", "condition_overlap": "Conditions",
               "fuel_realism": "Fuel", "data_richness": "Data"}


def result_card(r: dict, key: str = "") -> None:
    """One ranked investigation on the Scenario page, as a case slip."""
    with st.container(border=True, key=f"cfslip_{key or r['psi_id']}"):
        left, mid = st.columns([1, 7], vertical_alignment="top")
        left.html(f'<div class="cf-rank">{r["rank"]}</div>')
        with mid:
            st.html(card_head(r["psi_id"], r["area"]))
            st.markdown(f"**{r['name']}**")
            st.progress(min(1.0, max(0.0, r["score"])), text=f"Score {r['score']:.2f}")
            st.html(chips([(COMP_LABELS[k], f"{v:.2f}") for k, v in r["components"].items()]))
            st.caption(r["explanation"])
            if not r["conditions_reported"]:
                st.markdown(":gray-badge[conditions not reported]")
            st.markdown(doi_link(r["doi"]))
            dossier_link(r["psi_id"])


WARNING_ICONS = {
    "Detector blind spot": ":material/visibility_off:",
    "Hidden hazard: cool flames": ":material/local_fire_department:",
    "No data yet: partial gravity": ":material/public:",
    "Earth tests are not conservative": ":material/balance:",
    "Outside the tested range": ":material/straighten:",
    "Conditions not reported": ":material/help:",
}


def warning_card(w: dict) -> None:
    """Render one {level, title, body, sources} card from core/warnings.py."""
    level = w.get("level", "info")
    box = {"error": st.error, "warning": st.warning}.get(level, st.info)
    sources = w.get("sources") or []
    src = f"  \n*Sources: {'; '.join(sources)}*" if sources else ""
    box(f"**{w.get('title', '')}**  \n{w.get('body', '')}{src}",
        icon=WARNING_ICONS.get(w.get("title", ""), ":material/info:"))
