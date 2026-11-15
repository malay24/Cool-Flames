"""Overview: one card per investigation, filters by area and fuel phase (task P2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import demo_badge, footer, investigation_card, setup_page  # noqa: E402
from components.data import load_investigations  # noqa: E402

setup_page("Overview")
st.title("Overview")
invs, is_demo = load_investigations()
demo_badge(is_demo)
st.caption("Every NASA PSI combustion investigation, with its conditions and DOI. "
           "Summaries are AI-generated from the PSI record text and reviewed by the team.")

AREA_ORDER = ["prevention", "suppression", "detection", "basic", "modelling"]
areas = [a for a in AREA_ORDER if any(i["area"] == a for i in invs)]
phases = sorted({p for i in invs for p in (i.get("fuel_types") or [])})

f1, f2, f3 = st.columns([2, 2, 3])
pick_areas = f1.multiselect("Fire-safety area", areas, placeholder="All areas")
pick_phases = f2.multiselect("Fuel phase", phases, placeholder="All fuel phases")
query = f3.text_input("Search", placeholder="Name, fuel or keyword")

def matches(inv: dict) -> bool:
    if pick_areas and inv["area"] not in pick_areas:
        return False
    if pick_phases and not set(pick_phases) & set(inv.get("fuel_types") or []):
        return False
    if query:
        hay = " ".join([inv.get("name", ""), inv.get("title", ""), inv.get("summary_3line", ""),
                        " ".join(inv.get("fuels") or []), inv["psi_id"]]).lower()
        return query.lower() in hay
    return True

shown = sorted((i for i in invs if matches(i)),
               key=lambda i: (AREA_ORDER.index(i["area"]) if i["area"] in AREA_ORDER else 9,
                              int(i["psi_id"].split("-")[1])))
st.caption(f"Showing {len(shown)} of {len(invs)} investigations")

cols = st.columns(3)
for n, inv in enumerate(shown):
    with cols[n % 3]:
        investigation_card(inv)

footer()
