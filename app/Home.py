"""Freefall Fire Atlas entry point and router. Run from the repo root: streamlit run app/Home.py

Sets the page config, logo, theme CSS and the sidebar habitat picker once,
then hands over to the selected view in app/views/. Deploy main file stays
app/Home.py.
"""
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))  # for `components`

import streamlit as st  # noqa: E402

from components import habitat_sidebar, inject_css  # noqa: E402

st.set_page_config(page_title="Freefall Fire Atlas · Fire Scenario Explorer",
                   page_icon=str(APP / "static" / "icon.svg"), layout="wide")
st.logo(str(APP / "static" / "logo.svg"), icon_image=str(APP / "static" / "icon.svg"), size="large")
inject_css()


def view(file: str, title: str, icon: str, url: str | None = None, default: bool = False):
    return st.Page(str(APP / "views" / file), title=title, icon=icon, url_path=url, default=default)


# One flat list: rendered as manila folder tabs across the top (styled in archive.css).
PAGES = [
    view("home.py", "Home", ":material/rocket_launch:", default=True),
    view("scenario.py", "Scenarios", ":material/explore:", "scenario"),
    view("gap_map.py", "Gap map", ":material/scatter_plot:", "gap-map"),
    view("flame_lab.py", "Flame Lab", ":material/local_fire_department:", "flame-lab"),
    view("overview.py", "Investigations", ":material/library_books:", "overview"),
    view("dossier.py", "Dossier", ":material/description:", "dossier"),
    view("compare.py", "Compare", ":material/compare_arrows:", "compare"),
    view("ask.py", "Ask", ":material/forum:", "ask"),
    view("earth_benefits.py", "Earth", ":material/public:", "earth-benefits"),
]

nav = st.navigation(PAGES, position="top")
habitat_sidebar()
nav.run()
