"""Flame Lab: an illustrative animated flame driven by gravity, oxygen, airflow and fuel.

Not a simulation. The rules (in app/static/js/flame_lab.js) are qualitative and each
cites its source; below the animation, the page lists which NASA investigations
actually tested the chosen regime, or says that no data exists.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import (area_badge, current_habitat, doi_link, footer, page_header,  # noqa: E402
                        warning_card)
from components.data import habitats, load_earth_vs_space, load_investigations  # noqa: E402
from components.interactive import flame_lab  # noqa: E402
from core.warnings import get_warnings  # noqa: E402

GRAVITY = {"μg": 0.0, "Moon": 0.166, "Mars": 0.38, "Earth": 1.0}
GRAVITY_LONG = {"μg": "Microgravity (ISS)", "Moon": "Moon · 1/6 g", "Mars": "Mars · 3/8 g", "Earth": "Earth · 1 g"}
FUELS = {"Solid sheet": "solid", "Fuel droplet": "droplet"}
TRIES = {
    "Fabric fire on the ISS": dict(g="μg", o2=21, u=10, fuel="Solid sheet"),
    "Turn off the fans": dict(g="μg", o2=21, u=0, fuel="Solid sheet"),
    "Same fire on Earth": dict(g="Earth", o2=21, u=0, fuel="Solid sheet"),
    "Moon base air (30% O₂)": dict(g="Moon", o2=30, u=10, fuel="Solid sheet"),
    "Cool flame (FLEX droplet)": dict(g="μg", o2=18, u=0, fuel="Fuel droplet"),
    "Too much airflow": dict(g="μg", o2=21, u=140, fuel="Solid sheet"),
}
STUDIES = {"solid": ["PSI-25", "PSI-26", "PSI-98", "PSI-99", "PSI-100"],
           "droplet": ["PSI-69", "PSI-68", "PSI-39"]}
EVS_MATCH = {"solid": ("PMMA", "cellulose", "Silicone", "SIBAL"), "droplet": ("Decane",)}

hab = habitats()[current_habitat()]


def _near_gravity(g: float) -> str:
    return min(GRAVITY, key=lambda k: abs(GRAVITY[k] - g))


st.session_state.setdefault("fl_g", _near_gravity(hab.get("gravity_g") or 0.0))
st.session_state.setdefault("fl_o2", int(min(100, max(10, round(hab["o2_pct"])))))
st.session_state.setdefault("fl_u", 10)
st.session_state.setdefault("fl_fuel", "Solid sheet")


def _apply_try() -> None:
    choice = st.session_state.get("fl_try")
    if choice in TRIES:
        t = TRIES[choice]
        st.session_state.update(fl_g=t["g"], fl_o2=t["o2"], fl_u=t["u"], fl_fuel=t["fuel"])


def _from_habitat() -> None:
    st.session_state.update(fl_g=_near_gravity(hab.get("gravity_g") or 0.0),
                            fl_o2=int(min(100, max(10, round(hab["o2_pct"])))))


page_header("Explore · Flame Lab", "How does a fire behave without gravity?",
            "Change gravity, oxygen and airflow and watch the flame respond. This is an "
            "<b>illustrative model, not a simulation</b>: each rule comes from a cited NASA "
            "result, and the list below shows which experiments actually tested these conditions.")

st.pills("Try this", list(TRIES), key="fl_try", on_change=_apply_try, selection_mode="single")

with st.container(border=True):
    r1a, r1b = st.columns([3, 2], vertical_alignment="bottom")
    r1a.segmented_control("Gravity", list(GRAVITY), key="fl_g",
                          help="μg = microgravity (ISS); Moon 1/6 g; Mars 3/8 g; Earth 1 g.")
    r1b.segmented_control("Fuel", list(FUELS), key="fl_fuel")
    r2a, r2b, r2c = st.columns([2, 2, 1], vertical_alignment="bottom")
    r2a.slider("Oxygen (% by volume)", 10, 100, key="fl_o2")
    r2b.slider("Airflow (cm/s)", 0, 150, key="fl_u",
               help="Spacecraft ventilation is about 5–20 cm/s (Olson 2004).")
    r2c.button("Use my habitat", icon=":material/home_pin:", on_click=_from_habitat, width="stretch",
               help=f"Load gravity and oxygen from {hab['label']}.")

g_label = st.session_state["fl_g"] or "μg"
fuel_label = st.session_state["fl_fuel"] or "Solid sheet"
g = GRAVITY[g_label]
fuel = FUELS[fuel_label]
o2 = float(st.session_state["fl_o2"])
u_air = float(st.session_state["fl_u"])

flame_lab({"g": g, "g_label": GRAVITY_LONG[g_label].split(" (")[0], "o2": o2, "u_air": u_air, "fuel": fuel})

# ---- what NASA actually tested here ----
st.subheader("What NASA tested in this regime", anchor=False)
invs, _ = load_investigations()
by_id = {i["psi_id"]: i for i in invs}
if g == 0.0:
    st.caption(f"Microgravity {fuel_label.lower()} experiments in NASA PSI, with their tested oxygen range.")
    cols = st.columns(3)
    for n, pid in enumerate([p for p in STUDIES[fuel] if p in by_id]):
        inv = by_id[pid]
        rng = inv.get("o2_range")
        tested = (f"tested {rng[0]:g}–{rng[1]:g}% O₂" if rng else "O₂ not tabulated")
        inside = rng and rng[0] <= o2 <= rng[1]
        with cols[n % 3].container(border=True):
            st.markdown(f"**{inv['name']}** {area_badge(inv['area'])}")
            st.caption((inv.get("summary_3line") or "").split("\n")[0])
            st.markdown(f":{'green' if inside else 'gray'}-badge[{tested}]" +
                        (" &nbsp; :green-badge[your O₂ is inside]" if inside else ""))
            st.markdown(doi_link(inv["doi"]))
elif g < 1.0:
    probe = {"label": GRAVITY_LONG[g_label], "o2_pct": o2, "pressure_psi": 14.7, "gravity_g": g}
    for card in get_warnings(probe, "cabin_material_fire", "ignition"):
        if card["title"].startswith("No data yet"):
            warning_card(card)
    st.caption("The animation here interpolates between microgravity and Earth behaviour; "
               "no PSI experiment has measured it.")
else:
    st.caption("Normal gravity: how Earth results compare with microgravity, from sourced findings.")
    evs = load_earth_vs_space()
    rows = [r for r in evs.to_dict("records")
            if any(k.lower() in r["material"].lower() for k in EVS_MATCH[fuel])]
    cols = st.columns(2)
    for n, r in enumerate(rows):
        with cols[n % 2].container(border=True):
            st.markdown(f"**{r['material']}** · {r['flag'].replace('O2', 'O₂')}")
            st.markdown(r["finding"])
            st.caption(f"[{r['source']}]({r['source_url']})")

with st.expander("How this animation works", icon=":material/info:"):
    st.markdown(
        "- **Buoyancy:** hot gas rises only under gravity. The model uses a buoyant flow of "
        "about 50·√g cm/s, roughly 20 cm/s at Moon gravity; Olson (2004) notes lunar and Martian "
        "buoyant flows above 20 cm/s. In microgravity only the cabin airflow feeds the flame.\n"
        "- **Gentle breeze:** flames burn best in a gentle flow; with no flow they starve, and "
        "too much flow blows them out. A fraction of a cm/s can keep a weak flame alive "
        "(Olson 2004).\n"
        "- **Oxygen limit:** below a limiting oxygen level the flame goes out. In microgravity with "
        "gentle flow the limit is lower: BASS-II PMMA burned at 17% O₂ versus 18% on Earth "
        "(Link et al. 2018). The exact limits here are illustrative.\n"
        "- **Cool flames:** large fuel droplets in microgravity kept burning in an invisible "
        "low-temperature flame after the visible flame went out, at 14–21% O₂; at 25% O₂ that "
        "stage did not occur (Nayagam et al. 2014, FLEX).\n\n"
        "Shapes, colours and timings are qualitative. Use the Scenario Explorer and the linked "
        "papers for real values."
    )
    st.caption("Sources: [Olson 2004, NASA/TM-2004-213114](https://ntrs.nasa.gov/citations/20040084156) · "
               "[Link et al. 2018, Scientific Reports](https://doi.org/10.1038/s41598-017-18398-4) · "
               "[Nayagam et al. 2014](https://ntrs.nasa.gov/citations/20140006750)")

footer()
