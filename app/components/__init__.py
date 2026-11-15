"""Shared UI helpers: page setup, sidebar habitat picker, cards, DOI links.

Every page starts with `from components import setup_page; setup_page("Title")`.
Streamlit puts app/ on sys.path; this module also adds the repo root so pages
can import core/ and ai/.
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
AREA_COLORS = {"prevention": "orange", "suppression": "blue", "detection": "violet",
               "basic": "green", "modelling": "gray"}
DEFAULT_HABITAT = "iss"


def setup_page(title: str, icon: str = "🔥") -> str:
    """Page config, sidebar habitat picker and disclaimer. Returns the habitat key."""
    st.set_page_config(page_title=f"{title} · Cool Flames", page_icon=icon, layout="wide")
    habs = habitats()
    keys = list(habs)
    if st.session_state.get("habitat") not in keys:
        st.session_state["habitat"] = DEFAULT_HABITAT if DEFAULT_HABITAT in keys else keys[0]
    choice = st.sidebar.selectbox(
        "Habitat",
        keys,
        index=keys.index(st.session_state["habitat"]),
        format_func=lambda k: habitat_label(k, habs),
    )
    st.session_state["habitat"] = choice
    st.sidebar.caption(DISCLAIMER)
    return choice


def habitat_label(key: str, habs: dict | None = None) -> str:
    h = (habs or habitats())[key]
    return f"{h['label']} ({h['o2_pct']:g}% O₂, {h['pressure_psi']:g} psi)"


def footer() -> None:
    st.divider()
    st.caption(DISCLAIMER)


def demo_badge(is_demo: bool) -> None:
    if is_demo:
        st.badge("Demo data: real files not built yet", icon="🧪", color="orange")


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


def investigation_card(inv: dict) -> None:
    """One bordered card for the Overview grid."""
    with st.container(border=True):
        st.markdown(f"**{inv['name']}** · `{inv['psi_id']}`  \n{area_badge(inv['area'])}")
        if inv.get("name") != inv.get("title") and inv.get("title"):
            st.caption(inv["title"])
        summary = inv.get("summary_3line") or ""
        if summary:
            st.markdown(summary.replace("\n", "  \n"))
        else:
            st.caption("AI summary pending.")
        phases = ", ".join(inv.get("fuel_types") or []) or "none"
        fuels = ", ".join(inv.get("fuels") or [])
        st.markdown(f"**Fuel:** {fuels + ' · ' if fuels else ''}{phases}")
        st.markdown(
            f"**O₂:** {fmt_range(inv.get('o2_range'), '%')}  \n"
            f"**Pressure:** {fmt_range(inv.get('pressure_range'), 'psi')}  \n"
            f"**Airflow:** {fmt_range(inv.get('airflow_range'), 'cm/s')}"
        )
        runs = inv.get("n_runs") or 0
        std = inv.get("n_standardized_runs")
        run_txt = f"{runs} test runs" if runs else "text only (no test table)"
        if runs and std is not None and std < runs:
            run_txt += f" ({std} standardized)"
        st.caption(f"{run_txt} · {inv.get('n_publications', 0)} publications · {inv.get('platform') or ''}")
        st.markdown(doi_link(inv.get("doi", "")))
        if inv.get("key_findings"):
            with st.expander("Key findings"):
                for kf in inv["key_findings"]:
                    st.markdown(f"- {kf}")


def warning_card(w: dict) -> None:
    """Render one {level, title, body, sources} card from core/warnings.py."""
    level = w.get("level", "info")
    box = {"error": st.error, "warning": st.warning}.get(level, st.info)
    sources = w.get("sources") or []
    src = f"  \n*Sources: {'; '.join(sources)}*" if sources else ""
    box(f"**{w.get('title', '')}**  \n{w.get('body', '')}{src}")
