"""Gap map: O2 vs psi scatter, habitats, ppO2 lines (section 9). Task P4."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import footer, setup_page  # noqa: E402

setup_page("Gap map")

st.title("Gap map")
st.info("Gap map — test-run scatter with ppO2 iso-lines (P4, not built yet).")

footer()
