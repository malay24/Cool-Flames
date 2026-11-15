"""Earth benefits (stretch): static panel, task P9.

Every statement is taken from the "research impacts" text of the PSI records
themselves (data/raw/), with the investigation's DOI. Nothing from memory.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import doi_link, footer, page_header  # noqa: E402

page_header("About · Earth benefits", "What this research means on Earth",
            "What the investigations' own PSI records say their results mean on Earth. Quotes "
            "are from each record's research-impacts text.")

ITEMS = [
    {
        "title": "Fire suppression and fire safety in confined spaces",
        "icon": ":material/fire_extinguisher:",
        "points": [
            ("FLEX", "10.60555/mbq8-0451",
             "Findings on the effectiveness of fire suppressants (CO₂, He, SF₆) \"can lead to "
             "the development of more efficient and less harmful fire suppression systems\", "
             "and can \"advance fire safety in confined and reduced-gravity environments, such "
             "as submarines or high-altitude aircraft.\""),
            ("SAFFIRE-II", "10.60555/2chp-m469",
             "\"Studying fire in small, sealed environments such as the Cygnus cargo supply "
             "vehicle benefits fire safety and prevention efforts on Earth, including inside "
             "mines, airplanes, or submarines.\""),
        ],
    },
    {
        "title": "Smoke detectors for extreme environments",
        "icon": ":material/sensors:",
        "points": [
            ("SAME", "10.60555/gd4k-8h62",
             "\"The smoke detectors developed from the results of SAME can also be useful in "
             "other extreme environments on Earth, such as submarines or underwater "
             "laboratories. Accurate detection of smoke in these environments can save lives.\""),
            ("DAFT / DAFT-2", "10.60555/ztgj-d202",
             "Adapting the P-Trak particle counter for microgravity \"can inform the design of "
             "instruments for use in other challenging Earth environments, such as submarines "
             "or underwater laboratories.\""),
            ("SAME smoke modelling (PSI-115)", "10.60555/q0v5-1v28",
             "Smoke-particle models \"would directly lead to better smoke detection devices.\""),
        ],
    },
    {
        "title": "Fire models for wildfires and building fires",
        "icon": ":material/forest:",
        "points": [
            ("BASS-II", "10.60555/4qc4-de67",
             "Simpler flames in space let researchers test computer models of burning, which "
             "\"can then be used to more accurately study flames on Earth, such as in "
             "wildfires, building fires, energy recapture from waste recycling.\" BASS-II also "
             "\"helps engineers select the safest materials and improve firefighting methods\" "
             "on future missions."),
        ],
    },
]

for item in ITEMS:
    with st.container(border=True):
        st.subheader(f"{item['icon']} {item['title']}", anchor=False)
        for name, doi, text in item["points"]:
            st.markdown(f"**{name}:** {text}  \n{doi_link(doi)}")

st.caption("Water-mist extinguishers and firefighter gear, mentioned in the challenge brief, "
           "are not discussed in these PSI records, so no claim is made about them here.")

footer()
