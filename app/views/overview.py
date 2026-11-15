"""Investigations: one card per investigation, filters, Earth-vs-space findings (P2, R4)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import (demo_badge, footer, investigation_card, page_header,  # noqa: E402
                        stat_row)
from components.data import load_earth_vs_space, load_investigations  # noqa: E402

page_header("Explore · Investigations", "All 24 NASA combustion investigations",
            "Every PSI microgravity combustion study with its fuels, tested conditions and DOI. "
            "Summaries are AI-written from each record's own text; open the DOI to check them.")
invs, is_demo = load_investigations()
demo_badge(is_demo)

AREA_ORDER = ["prevention", "suppression", "detection", "basic", "modelling"]
counts = {a: sum(1 for i in invs if i["area"] == a) for a in AREA_ORDER}
stat_row([("Prevention", counts["prevention"]), ("Suppression", counts["suppression"]),
          ("Detection", counts["detection"]), ("Basic flame science", counts["basic"]),
          ("Modelling (ground)", counts["modelling"])])

areas = [a for a in AREA_ORDER if counts[a]]
phases = sorted({p for i in invs for p in (i.get("fuel_types") or [])})
with st.container(border=True):
    f1, f2, f3 = st.columns([2, 2, 3])
    pick_areas = f1.multiselect("Fire-safety area", areas, placeholder="All areas")
    pick_phases = f2.multiselect("Fuel phase", phases, placeholder="All fuel phases")
    query = f3.text_input("Search", placeholder="Name, fuel or keyword", icon=":material/search:")


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

# ---- Earth vs space (R4, data/manual/earth_vs_space.csv) ----
st.divider()
page_header("Earth vs space", "Do Earth tests tell the whole story?",
            "NASA screens materials with a normal-gravity test (NASA-STD-6001 Test 1). These "
            "sourced findings compare 1 g with microgravity, in both directions.")
evs = load_earth_vs_space()
FLAG_COLORS = {"Burns at lower O2 in space": "red", "Mixed": "orange", "Space-only": "violet",
               "Different": "blue", "Burned less": "green", "Burned in both": "gray"}
if evs.empty:
    st.info("No Earth-vs-space findings recorded yet.")
else:
    ecols = st.columns(2)
    for n, row in enumerate(evs.to_dict("records")):
        color = next((c for k, c in FLAG_COLORS.items() if row["flag"].startswith(k)), "gray")
        with ecols[n % 2].container(border=True):
            st.markdown(f":{color}-badge[{row['flag'].replace('O2', 'O₂')}]")
            st.markdown(f"**{row['material']}** · {row['measure']}")
            if row["value_1g"] or row["value_ug"]:
                unit = f" {row['unit']}" if row["unit"] else ""
                st.markdown(f"1 g: **{row['value_1g'] or '–'}**{unit if row['value_1g'] else ''} "
                            f"&nbsp;→&nbsp; microgravity: **{row['value_ug'] or '–'}**"
                            f"{unit if row['value_ug'] else ''}")
            st.markdown(row["finding"])
            st.caption(f"[{row['source']}]({row['source_url']})")

footer()
