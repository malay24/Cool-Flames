"""Cached data access for the app (no PSI calls; reads files under data/).

Reads data/ai/investigations.json and data/clean/tests.csv, falling back to
data/fake/ (pages then show a "demo data" badge). Ranges missing from
investigations.json are filled from tests.csv here, at load time, so the app
never waits on data/clean/ranges.csv (D8).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
REAL_INV = ROOT / "data" / "ai" / "investigations.json"
REAL_TESTS = ROOT / "data" / "clean" / "tests.csv"
FAKE_INV = ROOT / "data" / "fake" / "investigations.json"
FAKE_TESTS = ROOT / "data" / "fake" / "tests.csv"

NUMERIC = ["o2_pct", "pressure_psi", "ppo2_psi", "airflow_cms", "sample_size_mm", "metric_value"]
RANGE_COLS = {"o2_range": "o2_pct", "pressure_range": "pressure_psi", "airflow_range": "airflow_cms"}

# Fallback habitat presets (CLAUDE.md section 2) until core/scenarios.py lands.
_FALLBACK_HABITATS = {
    "iss": {"label": "ISS", "o2_pct": 21.0, "pressure_psi": 14.7},
    "moon_brief": {"label": "Moon Base / pressurized rover", "o2_pct": 30.0, "pressure_psi": 10.2},
    "exploration": {"label": "Exploration habitat (NASA)", "o2_pct": 34.0, "pressure_psi": 8.2},
    "suit": {"label": "Spacesuit", "o2_pct": 100.0, "pressure_psi": 4.3},
}


def habitats() -> dict[str, dict]:
    """Habitat presets: core.scenarios.HABITATS if defined, else the fallback."""
    try:
        from core.scenarios import HABITATS  # type: ignore[attr-defined]
        if HABITATS:
            return HABITATS
    except ImportError:
        pass
    return _FALLBACK_HABITATS


@st.cache_data
def load_tests() -> tuple[pd.DataFrame, bool]:
    """(tests dataframe, is_demo). Blank cells stay NaN, never 0."""
    is_demo = not REAL_TESTS.exists()
    df = pd.read_csv(FAKE_TESTS if is_demo else REAL_TESTS, dtype={"run_id": str})
    for col in NUMERIC:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df, is_demo


@st.cache_data
def load_investigations() -> tuple[list[dict], bool]:
    """(investigations, is_demo), with null ranges filled from tests.csv."""
    is_demo = not REAL_INV.exists()
    invs = json.loads((FAKE_INV if is_demo else REAL_INV).read_text())
    tests, _ = load_tests()
    for inv in invs:
        rows = tests[tests["psi_id"] == inv["psi_id"]]
        inv["n_standardized_runs"] = int(len(rows))
        for key, col in RANGE_COLS.items():
            if inv.get(key) is None and col in rows:
                vals = rows[col].dropna()
                if len(vals):
                    inv[key] = [round(float(vals.min()), 2), round(float(vals.max()), 2)]
    return invs, is_demo
