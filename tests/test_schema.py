"""Enum and column validation of tests.csv (CLAUDE.md sections 6.1, 11). Task D5.

Runs against the fake data (always present) and the real clean data (if built).
"""
import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SCHEMA_COLS = [
    "psi_id", "run_id", "fuel", "fuel_phase", "fuel_class", "o2_pct",
    "pressure_psi", "ppo2_psi", "diluent", "airflow_cms", "sample_size_mm",
    "outcome", "metric_name", "metric_value", "metric_unit", "mapping_confidence",
]
ENUMS = {
    "fuel_phase": {"solid", "liquid", "gas"},
    "fuel_class": {"cabin_material", "idealized"},
    "outcome": {"burned", "extinguished", "no_ignition", "unknown"},
    "mapping_confidence": {"hand", "llm_checked", "llm_unchecked"},
}
FLOAT_COLS = ["o2_pct", "pressure_psi", "ppo2_psi", "airflow_cms",
              "sample_size_mm", "metric_value"]

CSV_PATHS = [ROOT / "data" / "fake" / "tests.csv",
             ROOT / "data" / "clean" / "tests.csv"]


def _load(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("path", CSV_PATHS, ids=lambda p: p.parent.name)
def test_tests_csv(path: Path):
    if not path.exists():
        pytest.skip(f"{path} not built yet")
    rows = _load(path)
    assert rows, "no rows"
    assert list(rows[0].keys()) == SCHEMA_COLS, "column set/order mismatch"

    for r in rows:
        assert r["psi_id"], "missing psi_id"
        assert r["run_id"] != "", "missing run_id"
        assert r["mapping_confidence"] in ENUMS["mapping_confidence"]
        # enum columns: blank allowed (not reported); when present must be valid
        for col, allowed in ENUMS.items():
            if r[col] != "":
                assert r[col] in allowed, f"bad {col}={r[col]!r}"
        # float columns must be blank or parseable (blank == not reported)
        for col in FLOAT_COLS:
            if r[col] != "":
                float(r[col])
        # ppo2 is present only when both inputs are present, and consistent
        if r["o2_pct"] and r["pressure_psi"]:
            exp = float(r["o2_pct"]) / 100 * float(r["pressure_psi"])
            assert abs(exp - float(r["ppo2_psi"])) < 0.02
        else:
            assert r["ppo2_psi"] == "", "ppo2 set without o2 and pressure"
