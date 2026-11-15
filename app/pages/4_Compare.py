"""Compare page (stretch): 2 to 4 investigations side by side. Task P7."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import footer, setup_page  # noqa: E402

setup_page("Compare")

st.title("Compare")
st.info("Compare page — stretch (P7, not built yet).")

footer()
