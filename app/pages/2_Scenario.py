"""Scenario Explorer: phase tabs, ranked list, sliders (section 9). Task P3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import footer, setup_page  # noqa: E402

setup_page("Scenario Explorer")

st.title("Scenario Explorer")
st.info("Scenario Explorer — ranked list, score breakdown, warnings (P3, not built yet).")

footer()
