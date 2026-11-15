"""Cached wrappers around core.loaders for the app (no PSI calls)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import loaders
from core.scenarios import HABITATS, SCENARIOS, resolve_habitat


CUSTOM_KEY = "custom"


def habitats() -> dict[str, dict]:
    """Preset habitats, plus the atmosphere designed on the Scenario page if any."""
    custom = st.session_state.get("custom_habitat")
    if custom:
        return {**HABITATS, CUSTOM_KEY: resolve_habitat(custom)}
    return HABITATS


def scenarios() -> dict[str, dict]:
    return SCENARIOS


@st.cache_data
def load_tests() -> tuple[pd.DataFrame, bool]:
    """(tests dataframe, is_demo). Blank cells stay NaN, never 0."""
    return loaders.load_tests()


@st.cache_data
def load_investigations() -> tuple[list[dict], bool]:
    """(investigations, is_demo), with ranges filled from ranges.csv / tests.csv."""
    return loaders.load_investigations()


@st.cache_data
def load_earth_vs_space() -> pd.DataFrame:
    return loaders.load_earth_vs_space()


# ---- dossier (ai/dossier.py reads data/raw/ and data/ai/index/; nothing is generated) ----

@st.cache_data
def load_record(psi_id: str) -> dict:
    """Raw PSI record ({} for demo IDs)."""
    from ai import dossier
    return dossier.load_record(psi_id)


@st.cache_data
def load_table_profile(psi_id: str) -> list[dict]:
    from ai import dossier
    return dossier.table_profile(psi_id)


@st.cache_data
def load_raw_tables(psi_id: str) -> list[tuple[str, pd.DataFrame]]:
    """(table name, raw table as text) for the dossier's verification view."""
    from ai import dossier
    out = []
    for path in dossier.table_files(psi_id):
        header, rows = dossier.read_table(path)
        width = len(header)
        frame = pd.DataFrame([(r + [""] * width)[:width] for r in rows],
                             columns=[dossier.display_name(h) or f"col {i + 1}" for i, h in enumerate(header)])
        out.append((path.stem.split("_Experimental table_")[-1], frame))
    return out


@st.cache_data
def load_similar(psi_id: str, k: int = 4) -> list[dict]:
    from ai import dossier
    invs, _ = load_investigations()
    return dossier.similar_studies(psi_id, invs, _vectors(), k=k)


@st.cache_resource
def _vectors() -> dict:
    from ai import dossier
    return dossier.investigation_vectors()
