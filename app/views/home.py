"""Home: hero, key numbers, where to start, selected-habitat insight (task P1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import current_habitat, demo_badge, footer, stat_row  # noqa: E402
from components.data import habitats, load_investigations, load_tests  # noqa: E402
from components.interactive import hero  # noqa: E402
from core.scenarios import HISTORY, HISTORY_NOTE  # noqa: E402

habitat_key = current_habitat()
HABS = habitats()
invs, inv_demo = load_investigations()
tests, tests_demo = load_tests()
plotted = tests.dropna(subset=["o2_pct", "pressure_psi"])
h = HABS[habitat_key]

hero(h)
demo_badge(inv_demo or tests_demo)

dist = (((plotted["o2_pct"] - h["o2_pct"]) / 100) ** 2
        + ((plotted["pressure_psi"] - h["pressure_psi"]) / 14.7) ** 2) ** 0.5
stat_row([
    ("Investigations", f"{len(invs)}"),
    ("Test runs in PSI tables", f"{sum(i.get('n_runs') or 0 for i in invs):,}"),
    ("Runs standardized", f"{len(tests):,}", "One schema: psi, % O₂, blanks never filled with 0."),
    (f"Runs near {h['label'].split(' /')[0]}", f"{int((dist <= 0.1).sum()):,}",
     "Runs within about 10 O₂ points or 1.5 psi of the selected habitat."),
])

st.subheader("Start here", anchor=False)
c1, c2, c3 = st.columns(3)
CARDS = [
    (c1, "views/scenario.py", ":material/explore:", "Scenario Explorer",
     "Habitat + fire scenario → the investigations that matter for smoke, ignition, spread and "
     "suppression, with every score explained."),
    (c2, "views/gap_map.py", ":material/scatter_plot:", "Gap map",
     "Every test run by oxygen and pressure, with the ISS, Moon base and spacesuit on top. "
     "Empty space is missing data."),
    (c3, "views/overview.py", ":material/library_books:", "Investigations",
     "All 24 studies summarized, with fuels, tested conditions, DOIs and Earth-vs-space findings."),
]
for col, page, icon, title, text in CARDS:
    with col.container(border=True, height="stretch"):
        st.markdown(f"#### {icon} {title}")
        st.markdown(text)
        st.page_link(page, label=f"Open {title}", icon=":material/arrow_forward:")

left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Your habitat", anchor=False)
    iss = HABS["iss"]
    ppo2 = h["o2_pct"] / 100 * h["pressure_psi"]
    if habitat_key == "iss":
        st.markdown(f"**ISS air**: {h['o2_pct']:g}% O₂ at {h['pressure_psi']:g} psi "
                    f"(ppO₂ {ppo2:.2f} psi). Choose another habitat in the sidebar to compare.")
    else:
        iss_pp = iss["o2_pct"] / 100 * iss["pressure_psi"]
        st.markdown(
            f"**{h['label']}**: O₂ partial pressure **{ppo2:.2f} psi** versus **{iss_pp:.2f} psi** "
            f"on the ISS, but an O₂ fraction of **{h['o2_pct']:g}%** versus **{iss['o2_pct']:g}%**. "
            "Less inert gas absorbs heat, so materials can ignite and spread more easily than the "
            "partial pressure alone suggests."
        )
    if h.get("partial_gravity"):
        st.warning("No PSI test was run in partial gravity. Microgravity and 1 g results bound it; "
                   "FM2 and LUCI will add data.", icon=":material/public:")
with right:
    st.subheader("Why oxygen matters", anchor=False)
    for title, text in HISTORY:
        st.markdown(f"**{title}** · {text}")
    st.caption(HISTORY_NOTE)

footer()
