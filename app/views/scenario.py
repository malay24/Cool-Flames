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
from components.data import habitats, load_investigations, load_tests, scenarios  # noqa: E402
from components.interactive import habitat_designer  # noqa: E402
from core.ranking import COMPONENTS, DEFAULT_WEIGHTS, area_match, rank  # noqa: E402
from core.scenarios import (HABITATS, HISTORY, HISTORY_NOTE, PHASE_AREA, PHASE_ICONS,  # noqa: E402
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

# ---- habitat designer (two-way p5.js component) ----
WHERE = {"Orbit": 0.0, "Moon": 0.166, "Mars": 0.38}
SHORT = {"iss": "ISS", "moon_brief": "Moon base", "exploration": "Exploration", "suit": "Suit"}


def _where_from(g: float) -> str:
    return min(WHERE, key=lambda k: abs(WHERE[k] - (g or 0.0)))


def _set_custom(o2: float, p: float) -> None:
    g = WHERE[st.session_state.get("design_where") or "Orbit"]
    st.session_state["custom_habitat"] = {"label": "Custom atmosphere", "o2_pct": float(o2),
                                          "pressure_psi": float(p), "gravity_g": g}
    st.session_state["habitat"] = "custom"


def _on_design() -> None:
    val = st.session_state.get("cf_designer") or {}
    pt = val.get("point") if isinstance(val, dict) else getattr(val, "point", None)
    if not pt:
        return
    if pt.get("preset"):
        st.session_state["habitat"] = pt["preset"]
        st.session_state["design_where"] = _where_from(HABITATS[pt["preset"]].get("gravity_g", 0.0))
    else:
        _set_custom(pt["o2"], pt["p"])


def _on_where() -> None:
    custom = st.session_state.get("custom_habitat")
    if custom and st.session_state.get("habitat") == "custom":
        _set_custom(custom["o2_pct"], custom["pressure_psi"])


def _on_exact() -> None:
    _set_custom(st.session_state["exact_o2"], st.session_state["exact_p"])


hab_now = habitats()[habitat_key]
st.session_state.setdefault("design_where", _where_from(hab_now.get("gravity_g", 0.0)))
plot_runs = tests.dropna(subset=["o2_pct", "pressure_psi"])
area_of = {i["psi_id"]: i["area"] for i in invs}
runs_payload = [[round(float(r.pressure_psi), 2), round(float(r.o2_pct), 2), area_of.get(r.psi_id, "basic")]
                for r in plot_runs.itertuples()]
presets_payload = [{"key": k, "label": SHORT.get(k, h["label"]), "p": h["pressure_psi"], "o2": h["o2_pct"]}
                   for k, h in HABITATS.items()]

with st.container(border=True):
    st.markdown("#### :material/tune: Design your own atmosphere")
    left, right = st.columns([3, 1], gap="medium")
    with left:
        habitat_designer(runs_payload, presets_payload,
                         {"p": hab_now["pressure_psi"], "o2": hab_now["o2_pct"]}, on_change=_on_design)
    with right:
        st.caption("Drag the orange point to any oxygen level and cabin pressure. When you let go, "
                   "every ranking, warning and the sidebar switch to that atmosphere. Faint dots are "
                   "real NASA test runs; the halo counts the runs nearby.")
        st.segmented_control("Where is it?", list(WHERE), key="design_where", on_change=_on_where,
                             help="Orbit = microgravity. Moon (1/6 g) and Mars (3/8 g) are partial gravity, "
                                  "where PSI has no test data.")
        with st.popover("Type exact values", icon=":material/keyboard:", width="stretch"):
            st.number_input("O₂ (% by volume)", 5.0, 100.0, float(hab_now["o2_pct"]), 0.5, key="exact_o2")
            st.number_input("Total pressure (psi)", 0.5, 30.0, float(hab_now["pressure_psi"]), 0.1, key="exact_p")
            st.button("Use these values", on_click=_on_exact, type="primary", width="stretch")
        if habitat_key == "custom":
            st.button("Back to ISS", icon=":material/restart_alt:", width="stretch",
                      on_click=lambda: st.session_state.update(habitat="iss"))

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
        shown = rank(pool, tests, hab_now, scenario_key, phase, weights)
        for card in get_warnings(hab_now, scenario_key, phase, shown):
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
