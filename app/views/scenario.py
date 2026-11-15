"""Scenario Explorer: phase tabs, ranked list, weight sliders, warning cards.

Tasks P3 and P5. CLAUDE.md sections 8 and 9. Ranking and warnings come from
core/ (pure, template explanations, no LLM).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from components import (current_habitat, demo_badge, footer, habitat_label,  # noqa: E402
                        is_dark, page_header, result_card, tokens, warning_card)
from components.data import load_investigations, load_tests, scenarios  # noqa: E402
from core.ranking import COMPONENTS, DEFAULT_WEIGHTS, area_match, rank  # noqa: E402
from core.scenarios import (HISTORY, HISTORY_NOTE, PHASE_AREA, PHASE_ICONS,  # noqa: E402
                            PHASE_LABELS)
from core.warnings import get_warnings  # noqa: E402

habitat_key = current_habitat()
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
DARK = is_dark()
T = tokens()
# Categorical slots 1-4 in validated adjacent order (dataviz reference palette).
COMP_COLORS = dict(zip(COMPONENTS, ["#3987e5", "#d95926", "#199e70", "#c98500"] if DARK
                       else ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]))

# ---- sidebar: weights ----


def _reset_weights() -> None:
    for k, v in DEFAULT_WEIGHTS.items():
        st.session_state[f"w_{k}"] = v


weights = {}
with st.sidebar.expander("Ranking weights", icon=":material/tune:", expanded=True):
    for k in COMPONENTS:
        st.session_state.setdefault(f"w_{k}", DEFAULT_WEIGHTS[k])
        weights[k] = st.slider(COMP_LABELS[k], 0.0, 1.0, step=0.05, key=f"w_{k}", help=COMP_HELP[k])
    st.button("Reset weights", on_click=_reset_weights, icon=":material/restart_alt:",
              width="stretch")
    if sum(weights.values()) == 0:
        st.warning("All weights are 0; every study scores 0.")

# ---- header + scenario picker ----
page_header("Explore · Scenario Explorer", "Which NASA studies matter for this fire?",
            f"Habitat: <b>{habitat_label(habitat_key)}</b> (change it in the sidebar). Pick a "
            "scenario; each tab ranks the investigations for one phase of the fire.")
invs, inv_demo = load_investigations()
tests, tests_demo = load_tests()
demo_badge(inv_demo or tests_demo)

keys = list(SCEN)
st.session_state.setdefault("scenario", "electrical_overheat" if "electrical_overheat" in keys
                            else keys[0])
picked = st.pills("Fire scenario", keys, selection_mode="single", default=st.session_state["scenario"],
                  format_func=lambda k: f"{SCEN[k].get('icon', '')} {SCEN[k].get('short', SCEN[k]['label'])}")
scenario_key = picked or st.session_state["scenario"]
st.session_state["scenario"] = scenario_key
scenario = SCEN[scenario_key]

c1, c2, c3 = st.columns([3, 2, 2], vertical_alignment="bottom")
c1.caption(f"**{scenario['label']}** · fuel: "
           f"{', '.join(scenario['fuel_phases']) or 'none (detection only)'}")
top_n = c2.slider("Studies shown per phase", 3, 24, 6)
show_all = c3.toggle("Include other fire-safety areas", value=False,
                     help="Off: only studies whose area matches the phase (or basic flame "
                          "science). On: every investigation, ranked.")


def breakdown_chart(results: list[dict]) -> go.Figure:
    """Stacked horizontal bars of weighted components, rank 1 at the top."""
    names = [f"{r['rank']}. {r['name'][:38]}" for r in results]
    fig = go.Figure()
    for k in COMPONENTS:
        fig.add_trace(go.Bar(
            y=names, x=[r["weighted"][k] for r in results], name=COMP_LABELS[k],
            orientation="h", marker=dict(color=COMP_COLORS[k], line=dict(color=T["bg"], width=2)),
            customdata=[[r["components"][k]] for r in results],
            hovertemplate=(f"<b>%{{y}}</b><br>{COMP_LABELS[k]}: %{{customdata[0]:.2f}}"
                           " × weight → %{x:.3f}<extra></extra>"),
        ))
    fig.update_layout(
        barmode="stack", height=90 + 34 * len(results), margin=dict(l=10, r=10, t=30, b=50),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", bargap=0.35,
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, sans-serif", color=T["text"]),
        xaxis=dict(title="Score (weighted sum of components)", range=[0, 1], gridcolor=T["grid"],
                   zeroline=False, tickfont=dict(color=T["muted"]), title_font=dict(color=T["muted"])),
        yaxis=dict(autorange="reversed", automargin=True, tickfont=dict(color=T["text"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, traceorder="normal",
                    font=dict(color=T["muted"])),
        hoverlabel=dict(bgcolor=T["panel"], font_color=T["text"]),
    )
    return fig


tabs = st.tabs([f"{PHASE_ICONS.get(p, '')} {PHASE_LABELS[p]}" for p in scenario["phases"]])
for phase, tab in zip(scenario["phases"], tabs):
    with tab:
        # Rank only the studies shown, so rank numbers and explanations agree.
        pool = invs if show_all else [i for i in invs if area_match(i, scenario, phase) > 0]
        shown = rank(pool, tests, habitat_key, scenario_key, phase, weights)
        for card in get_warnings(habitat_key, scenario_key, phase, shown):
            warning_card(card)
        st.caption(f"Studies in the **{PHASE_AREA[phase]}** area rank highest in this phase · "
                   f"{len(shown)} of {len(invs)} investigations ranked.")
        if not shown:
            st.info("No investigation in PSI covers this phase for this fuel. That is a data gap.",
                    icon=":material/search_off:")
            continue
        top = shown[:top_n]
        st.plotly_chart(breakdown_chart(top), width="stretch", theme=None,
                        key=f"chart_{scenario_key}_{phase}")
        grid = st.columns(2)
        for n, r in enumerate(top):
            with grid[n % 2]:
                result_card(r)
        if len(shown) > top_n:
            st.caption(f"{len(shown) - top_n} more not shown; raise 'Studies shown per phase'.")

with st.expander("Why oxygen-rich fires matter: historical context", icon=":material/history:"):
    for title, text in HISTORY:
        st.markdown(f"- **{title}:** {text}")
    st.caption(HISTORY_NOTE)

footer()
