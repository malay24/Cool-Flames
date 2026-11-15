"""Scenario Explorer: phase tabs, ranked list, weight sliders, warning cards.

Tasks P3 and P5. CLAUDE.md sections 8 and 9. Ranking and warnings come from
core/ (pure, template explanations, no LLM).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from components import (area_badge, demo_badge, doi_link, footer, habitat_label,  # noqa: E402
                        setup_page, warning_card)
from components.data import load_investigations, load_tests, scenarios  # noqa: E402
from core.ranking import COMPONENTS, DEFAULT_WEIGHTS, area_match, rank  # noqa: E402
from core.scenarios import HISTORY, HISTORY_NOTE, PHASE_AREA, PHASE_LABELS  # noqa: E402
from core.warnings import get_warnings  # noqa: E402

habitat_key = setup_page("Scenario Explorer")
SCEN = scenarios()

COMP_LABELS = {"area_match": "Area match", "condition_overlap": "Condition overlap",
               "fuel_realism": "Fuel realism", "data_richness": "Data richness"}
COMP_HELP = {
    "area_match": "1 if the study's fire-safety area matches the phase, 0.5 for basic flame "
                  "science, 0 otherwise (or if its fuel phase does not fit the scenario).",
    "condition_overlap": "How close its nearest test (O₂ %, psi) comes to the habitat.",
    "fuel_realism": "Cabin materials score above idealized liquids, which score above gas burners.",
    "data_richness": "Test runs (log scale) and publications; large-scale tests get a bonus.",
}
theme = getattr(st.context, "theme", None)
DARK = bool(theme and getattr(theme, "type", None) == "dark")
# Categorical slots 1-4 in validated adjacent order (dataviz reference palette).
COMP_COLORS = dict(zip(COMPONENTS, ["#3987e5", "#d95926", "#199e70", "#c98500"] if DARK
                       else ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]))
INK = {"primary": "#f0efec" if DARK else "#0b0b0b", "secondary": "#c3c2b7" if DARK else "#52514e",
       "grid": "#2c2c2a" if DARK else "#e1e0d9", "surface": "#1a1a19" if DARK else "#fcfcfb"}

# ---- sidebar: weights ----
st.sidebar.subheader("Ranking weights")


def _reset_weights() -> None:
    for k, v in DEFAULT_WEIGHTS.items():
        st.session_state[f"w_{k}"] = v


weights = {}
for k in COMPONENTS:
    st.session_state.setdefault(f"w_{k}", DEFAULT_WEIGHTS[k])
    weights[k] = st.sidebar.slider(COMP_LABELS[k], 0.0, 1.0, step=0.05, key=f"w_{k}",
                                   help=COMP_HELP[k])
st.sidebar.button("Reset weights", on_click=_reset_weights)
if sum(weights.values()) == 0:
    st.sidebar.warning("All weights are 0; every study scores 0.")

# ---- header ----
st.title("Scenario Explorer")
invs, inv_demo = load_investigations()
tests, tests_demo = load_tests()
demo_badge(inv_demo or tests_demo)

keys = list(SCEN)
default = "electrical_overheat" if "electrical_overheat" in keys else keys[0]
c1, c2 = st.columns([3, 2])
scenario_key = c1.selectbox("Fire scenario", keys, index=keys.index(default),
                            format_func=lambda k: SCEN[k]["label"])
show_all = c2.toggle("Include studies from other fire-safety areas", value=False,
                     help="Off: only studies whose area matches the phase (or basic flame "
                          "science). On: every investigation, ranked.")
top_n = c2.slider("Studies shown per phase", 3, 24, 8)
scenario = SCEN[scenario_key]
st.caption(f"Habitat: **{habitat_label(habitat_key)}** (change it in the sidebar) · "
           f"fuel: {', '.join(scenario['fuel_phases']) or 'none (detection only)'}")

with st.expander("Why oxygen-rich fires matter: historical context"):
    for title, text in HISTORY:
        st.markdown(f"- **{title}:** {text}")
    st.caption(HISTORY_NOTE)


def breakdown_chart(results: list[dict]) -> go.Figure:
    """Stacked horizontal bars of weighted components, rank 1 at the top."""
    names = [f"{r['rank']}. {r['name']}" for r in results]
    fig = go.Figure()
    for k in COMPONENTS:
        fig.add_trace(go.Bar(
            y=names, x=[r["weighted"][k] for r in results], name=COMP_LABELS[k],
            orientation="h", marker=dict(color=COMP_COLORS[k],
                                         line=dict(color=INK["surface"], width=2)),
            customdata=[[r["components"][k]] for r in results],
            hovertemplate=(f"<b>%{{y}}</b><br>{COMP_LABELS[k]}: %{{customdata[0]:.2f}}"
                           " × weight → %{x:.3f}<extra></extra>"),
        ))
    fig.update_layout(
        barmode="stack", height=80 + 34 * len(results), margin=dict(l=10, r=10, t=30, b=50),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", bargap=0.35,
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK["primary"]),
        xaxis=dict(title="Score (weighted sum of components)", range=[0, 1],
                   gridcolor=INK["grid"], zeroline=False, tickfont=dict(color=INK["secondary"])),
        yaxis=dict(autorange="reversed", automargin=True, tickfont=dict(color=INK["primary"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, traceorder="normal",
                    font=dict(color=INK["secondary"])),
        hoverlabel=dict(bgcolor=INK["surface"], font_color=INK["primary"]),
    )
    return fig


def result_card(r: dict) -> None:
    with st.container(border=True):
        left, right = st.columns([5, 1])
        left.markdown(f"**{r['rank']}. {r['name']}** · `{r['psi_id']}` {area_badge(r['area'])}")
        right.metric("Score", f"{r['score']:.2f}", label_visibility="collapsed")
        st.caption(r["explanation"])
        comps = " · ".join(f"{COMP_LABELS[k]} {r['components'][k]:.2f}" for k in COMPONENTS)
        st.markdown(f"<small>{comps}</small>", unsafe_allow_html=True)
        if not r["conditions_reported"]:
            st.markdown(":gray-badge[conditions not reported]")
        st.markdown(doi_link(r["doi"]))


tabs = st.tabs([PHASE_LABELS[p] for p in scenario["phases"]])
for phase, tab in zip(scenario["phases"], tabs):
    with tab:
        # Rank only the studies shown, so rank numbers and explanations agree.
        pool = invs if show_all else [i for i in invs if area_match(i, scenario, phase) > 0]
        shown = rank(pool, tests, habitat_key, scenario_key, phase, weights)
        for card in get_warnings(habitat_key, scenario_key, phase, shown):
            warning_card(card)
        st.markdown(f"**{PHASE_LABELS[phase]}** → studies in the *{PHASE_AREA[phase]}* area "
                    f"rank highest. {len(shown)} of {len(invs)} investigations shown.")
        if not shown:
            st.info("No investigation in PSI covers this phase for this fuel. That is a data gap.")
            continue
        top = shown[:top_n]
        st.plotly_chart(breakdown_chart(top), width="stretch", theme=None,
                        key=f"chart_{scenario_key}_{phase}")
        for r in top:
            result_card(r)
        if len(shown) > top_n:
            st.caption(f"{len(shown) - top_n} more not shown; raise 'Studies shown per phase'.")

footer()
