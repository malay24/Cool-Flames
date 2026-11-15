"""Cached wrappers around core.loaders for the app (no PSI calls)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import loaders
from core.scenarios import HABITATS, SCENARIOS


def habitats() -> dict[str, dict]:
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
