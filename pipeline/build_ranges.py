"""Per-investigation ranges and run counts to data/clean/ranges.csv (task D8).

Ranges are computed from data/clean/tests.csv, never from an LLM, and merged
into data/ai/investigations.json by ai/tag_summarize.py. Blank cells are
ignored (not treated as 0); a range with no reported values stays blank.

Usage (from the repo root):
    python -m pipeline.build_ranges
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "data" / "clean" / "tests.csv"
OUT = ROOT / "data" / "clean" / "ranges.csv"

RANGE_SOURCES = {"o2": "o2_pct", "pressure": "pressure_psi", "airflow": "airflow_cms",
                 "sample_size": "sample_size_mm"}
FIELDS = (["psi_id", "n_standardized_runs", "n_with_o2_and_pressure"]
          + [f"{k}_{b}" for k in RANGE_SOURCES for b in ("min", "max")])


def build() -> list[dict]:
    with TESTS.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_psi: dict[str, list[dict]] = {}
    for r in rows:
        by_psi.setdefault(r["psi_id"], []).append(r)

    out = []
    for psi_id in sorted(by_psi, key=lambda s: int(s.split("-")[1])):
        runs = by_psi[psi_id]
        entry: dict = {
            "psi_id": psi_id,
            "n_standardized_runs": len(runs),
            "n_with_o2_and_pressure": sum(1 for r in runs if r["o2_pct"] and r["pressure_psi"]),
        }
        for key, col in RANGE_SOURCES.items():
            vals = [float(r[col]) for r in runs if r[col] != ""]
            entry[f"{key}_min"] = round(min(vals), 2) if vals else ""
            entry[f"{key}_max"] = round(max(vals), 2) if vals else ""
        out.append(entry)
    return out


def main() -> int:
    ranges = build()
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ranges)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(ranges)} investigations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
