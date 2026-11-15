"""Landing page (task P1). Run from the repo root: streamlit run app/Home.py"""
import streamlit as st

from components import footer, habitat_label, setup_page
from components.data import habitats, load_investigations, load_tests

habitat = setup_page("Fire Scenario Explorer")

st.title("Cool Flames: Fire Scenario Explorer")
st.markdown(
    "Pick a **habitat** and a **fire scenario** to see which of NASA's microgravity "
    "combustion investigations matter for each phase of the fire, how close their test "
    "conditions come to your habitat's atmosphere, and where **no data exists**."
)

invs, inv_demo = load_investigations()
tests, tests_demo = load_tests()
plotted = tests.dropna(subset=["o2_pct", "pressure_psi"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Investigations", len(invs))
c2.metric("Test runs in PSI tables", f"{sum(i.get('n_runs') or 0 for i in invs):,}")
c3.metric("Runs standardized", f"{len(tests):,}")
c4.metric("Runs with O₂ and pressure", f"{len(plotted):,}")

h = habitats()[habitat]
iss = habitats().get("iss")
st.subheader(f"Selected habitat: {habitat_label(habitat)}")
ppo2 = h["o2_pct"] / 100 * h["pressure_psi"]
if iss and habitat != "iss":
    iss_pp = iss["o2_pct"] / 100 * iss["pressure_psi"]
    st.markdown(
        f"O₂ partial pressure **{ppo2:.2f} psi** vs **{iss_pp:.2f} psi** on the ISS, "
        f"but an O₂ fraction of **{h['o2_pct']:g}%** vs **{iss['o2_pct']:g}%**. "
        "Less inert gas absorbs heat, so materials can ignite and spread more easily "
        "than the partial pressure alone suggests."
    )
else:
    st.markdown(f"O₂ partial pressure **{ppo2:.2f} psi** at {h['o2_pct']:g}% O₂.")

st.subheader("Pages")
st.page_link("pages/1_Overview.py", label="Overview: every investigation, summarized", icon="🗂️")
st.page_link("pages/2_Scenario.py", label="Scenario Explorer: ranked by fire phase", icon="🧭")
st.page_link("pages/3_Gap_map.py", label="Gap map: tested conditions vs habitats", icon="🗺️")
st.page_link("pages/4_Compare.py", label="Compare: 2 to 4 investigations side by side", icon="⚖️")
st.page_link("pages/6_Earth_benefits.py", label="Earth benefits: what the records say", icon="🌍")

if inv_demo or tests_demo:
    st.info("Some pages are showing demo data until the real data files are built.")

footer()
