"""Ask page (stretch): Q&A answered only from texts, cites DOIs. Task P8."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import footer, setup_page  # noqa: E402

setup_page("Ask")

st.title("Ask")
st.info("Ask page — stretch, Q&A with DOI citations (P8, not built yet).")

footer()
