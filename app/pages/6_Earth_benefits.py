"""Earth benefits (stretch): static spinoffs panel. Task P9."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import footer, setup_page  # noqa: E402

setup_page("Earth benefits")

st.title("Earth benefits")
st.info("Earth benefits — stretch, static panel (P9, not built yet).")

footer()
