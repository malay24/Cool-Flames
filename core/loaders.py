"""Load clean data for the app and tests. Single source of the repo ROOT path.

Pure data access, no Streamlit imports (CLAUDE.md section 11). Reads data/clean/
and data/ai/ if present, otherwise falls back to data/fake/ (is_demo=True).
Blank cells stay NaN: blank means "not reported", never 0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REAL_TESTS = ROOT / "data" / "clean" / "tests.csv"
RANGES = ROOT / "data" / "clean" / "ranges.csv"
REAL_INV = ROOT / "data" / "ai" / "investigations.json"
FAKE_TESTS = ROOT / "data" / "fake" / "tests.csv"
FAKE_INV = ROOT / "data" / "fake" / "investigations.json"

NUMERIC = ["o2_pct", "pressure_psi", "ppo2_psi", "airflow_cms", "sample_size_mm", "metric_value"]
# investigations.json range key -> (tests.csv column, ranges.csv min/max prefix)
RANGE_COLS = {"o2_range": ("o2_pct", "o2"),
              "pressure_range": ("pressure_psi", "pressure"),
              "airflow_range": ("airflow_cms", "airflow")}


def load_tests() -> tuple[pd.DataFrame, bool]:
    """Return (tests dataframe, is_demo)."""
    is_demo = not REAL_TESTS.exists()
    df = pd.read_csv(FAKE_TESTS if is_demo else REAL_TESTS, dtype={"run_id": str})
    for col in NUMERIC:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df, is_demo


def _ranges_from_tests(tests: pd.DataFrame) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for psi_id, rows in tests.groupby("psi_id"):
        entry: dict = {"n_standardized_runs": int(len(rows))}
        for key, (col, _) in RANGE_COLS.items():
            vals = rows[col].dropna() if col in rows else pd.Series(dtype=float)
            entry[key] = [round(float(vals.min()), 2), round(float(vals.max()), 2)] if len(vals) else None
        out[str(psi_id)] = entry
    return out


def _ranges_from_csv() -> dict[str, dict]:
    df = pd.read_csv(RANGES)
    out: dict[str, dict] = {}
    for r in df.to_dict("records"):
        entry: dict = {"n_standardized_runs": int(r["n_standardized_runs"])}
        for key, (_, prefix) in RANGE_COLS.items():
            lo, hi = r.get(f"{prefix}_min"), r.get(f"{prefix}_max")
            entry[key] = None if pd.isna(lo) or pd.isna(hi) else [float(lo), float(hi)]
        out[str(r["psi_id"])] = entry
    return out


def load_investigations() -> tuple[list[dict], bool]:
    """Return (investigations, is_demo), with null ranges filled.

    Ranges come from data/clean/ranges.csv (D8) when it exists, else are
    computed from tests.csv. Values already in the JSON are kept.
    """
    is_demo = not REAL_INV.exists()
    invs = json.loads((FAKE_INV if is_demo else REAL_INV).read_text())
    tests, tests_demo = load_tests()
    ranges = _ranges_from_csv() if RANGES.exists() and not tests_demo else _ranges_from_tests(tests)
    for inv in invs:
        r = ranges.get(inv["psi_id"], {})
        inv.setdefault("n_standardized_runs", r.get("n_standardized_runs", 0))
        for key in RANGE_COLS:
            if inv.get(key) is None:
                inv[key] = r.get(key)
    return invs, is_demo
