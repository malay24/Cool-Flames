"""Shared UI: theme helpers, page header, sidebar habitat picker, cards, footer.

The router (app/Home.py) calls `inject_css()` and `habitat_sidebar()` once per
run; every view calls `current_habitat()` and `page_header()`. Streamlit puts
app/ on sys.path; this module also adds the repo root so views can import
core/ and ai/.
"""
from __future__ import annotations

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
AREA_COLORS = {"prevention": "orange", "suppression": "blue", "detection": "violet",
               "basic": "green", "modelling": "gray"}
AREA_ICONS = {"prevention": ":material/local_fire_department:", "suppression": ":material/fire_extinguisher:",
              "detection": ":material/sensors:", "basic": ":material/science:",
              "modelling": ":material/model_training:"}

# Theme tokens mirrored from .streamlit/config.toml (for charts and custom HTML).
THEMES = {
    "dark": {"bg": "#0d1220", "panel": "#161d2e", "border": "#24304a", "text": "#e8eaf0",
             "muted": "#9aa3b5", "accent": "#f07a3a", "grid": "#1f2940", "axis": "#2c3852"},
    "light": {"bg": "#fbfaf8", "panel": "#f2efe9", "border": "#e3ded4", "text": "#1d1f24",
              "muted": "#6b6f78", "accent": "#d9541e", "grid": "#e6e1d7", "axis": "#cfc8bb"},
}


def is_dark() -> bool:
    # Theme is forced dark in .streamlit/config.toml; default to dark unless the
    # viewer explicitly switches to light, so custom CSS/charts stay in step.
    theme = getattr(st.context, "theme", None)
    return getattr(theme, "type", "dark") != "light"


def tokens() -> dict:
    return THEMES["dark" if is_dark() else "light"]


# ---------------------------------------------------------------- shell

def inject_css() -> None:
    """Small global CSS: hero band, eyebrow labels, chips. Uses our own classes only."""
    t = tokens()
    hero_bg = ("radial-gradient(1200px 300px at 85% -20%, rgba(240,122,58,0.35), transparent 60%),"
               "linear-gradient(135deg, #111a2e 0%, #0d1220 55%, #1a1320 100%)") if is_dark() else \
              ("radial-gradient(1000px 260px at 85% -20%, rgba(217,84,30,0.18), transparent 60%),"
               "linear-gradient(135deg, #fffaf3 0%, #f6f1e8 100%)")
    st.html(f"""
<style>
.cf-eyebrow {{ font-size: 0.74rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase;
  color: {t['accent']}; margin: 0 0 0.15rem 0; }}
.cf-sub {{ color: {t['muted']}; font-size: 1.02rem; margin: 0.1rem 0 0.6rem 0; max-width: 62rem; }}
.cf-hero {{ background: {hero_bg}; border: 1px solid {t['border']}; border-radius: 1rem;
  padding: 2.2rem 2.4rem 2rem 2.4rem; margin-bottom: 1.2rem; }}
.cf-hero h1 {{ font-family: 'Space Grotesk', Inter, sans-serif; font-size: 2.5rem; line-height: 1.12;
  margin: 0.2rem 0 0.7rem 0; color: {t['text']}; padding: 0; }}
.cf-hero p {{ color: {t['muted']}; font-size: 1.08rem; max-width: 46rem; margin: 0; }}
.cf-hero p.cf-eyebrow {{ color: {t['accent']}; font-size: 0.74rem; margin-bottom: 0.2rem; }}
.cf-chip {{ display: inline-block; padding: 0.12rem 0.55rem; margin: 0 0.3rem 0.3rem 0; border-radius: 999px;
  border: 1px solid {t['border']}; background: {t['panel']}; font-size: 0.82rem; color: {t['text']}; }}
.cf-chip b {{ color: {t['muted']}; font-weight: 500; margin-right: 0.25rem; }}
.cf-rank {{ font-family: 'Space Grotesk', Inter, sans-serif; font-size: 2rem; font-weight: 700;
  color: {t['accent']}; line-height: 1; }}
.cf-foot {{ text-align: center; color: {t['muted']}; font-size: 0.82rem; padding: 0.4rem 0 1rem 0; }}
.cf-atmo {{ border: 1px solid {t['border']}; border-radius: 0.6rem; padding: 0.6rem 0.75rem;
  font-size: 0.86rem; line-height: 1.55; }}
.cf-atmo .v {{ font-weight: 600; }}
@media (max-width: 640px) {{ .cf-hero {{ padding: 1.4rem 1.2rem; }} .cf-hero h1 {{ font-size: 1.75rem; }} }}
</style>""")


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
        gravity += ("<br>⚠️ partial gravity: no PSI data" if h.get("partial_gravity") else "")
        st.html(f"""<div class="cf-atmo">O₂ <span class="v">{h['o2_pct']:g}%</span> ·
            total <span class="v">{h['pressure_psi']:g} psi</span><br>
            ppO₂ <span class="v">{h.get('ppo2_psi', h['o2_pct'] / 100 * h['pressure_psi']):.2f} psi</span>
            · {gravity}</div>""")
        st.caption(DISCLAIMER)
    return choice


def current_habitat() -> str:
    """Selected habitat key (works when a view runs on its own, e.g. in tests)."""
    key = st.session_state.get("habitat")
    return key if key in habitats() else DEFAULT_HABITAT


def page_header(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.html(f'<p class="cf-eyebrow">{eyebrow}</p>')
    st.title(title, anchor=False)
    if subtitle:
        st.html(f'<p class="cf-sub">{subtitle}</p>')


def stat_row(items: list[tuple]) -> None:
    """items: (label, value) or (label, value, help)."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, *rest = item
        col.metric(label, value, border=True, help=rest[0] if rest else None)


def footer() -> None:
    st.divider()
    st.html('<div class="cf-foot">Research and reference tool, not an operational safety system · '
            'Data: NASA Physical Sciences Informatics (CC0) · every claim links its DOI</div>')


def demo_badge(is_demo: bool) -> None:
    if is_demo:
        st.badge("Demo data: real files not built yet", icon=":material/science:", color="orange")


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

def investigation_card(inv: dict) -> None:
    """One bordered card for the Overview grid."""
    with st.container(border=True):
        st.markdown(f"#### {inv['name']}")
        st.markdown(f"{area_badge(inv['area'])} &nbsp; `{inv['psi_id']}`")
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


def result_card(r: dict) -> None:
    """One ranked investigation on the Scenario page."""
    with st.container(border=True):
        left, mid = st.columns([1, 9], vertical_alignment="top")
        left.html(f'<div class="cf-rank">{r["rank"]}</div>')
        with mid:
            st.markdown(f"**{r['name']}** &nbsp; {area_badge(r['area'])} &nbsp; `{r['psi_id']}`")
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
