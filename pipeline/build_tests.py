"""Merge mapped tables into data/clean/tests.csv (CLAUDE.md sections 6.1, 7).

Task D5. Reads every mapping JSON in pipeline/mappings/, applies the cleaning
rules documented in pipeline/mappings/_FORMAT.md (BOM strip, messy-value parsing,
unit conversion via units.py), computes ppo2_psi, validates enums, and writes
one row per test run to data/clean/tests.csv.

Blank means "not reported" and is never zero-filled (CLAUDE.md section 6.1).

Usage (run as a module from the repo root so `pipeline` is importable):
    python -m pipeline.build_tests
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from pipeline import units

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "data" / "raw" / "tables"
MAPPINGS = ROOT / "pipeline" / "mappings"
OUT = ROOT / "data" / "clean" / "tests.csv"

SCHEMA_COLS = [
    "psi_id", "run_id", "fuel", "fuel_phase", "fuel_class", "o2_pct",
    "pressure_psi", "ppo2_psi", "diluent", "airflow_cms", "sample_size_mm",
    "outcome", "metric_name", "metric_value", "metric_unit", "mapping_confidence",
]
STR_TARGETS = {"run_id", "fuel"}
NUM_TARGETS = {"o2_pct", "pressure_psi", "airflow_cms", "sample_size_mm"}
ROUNDING = {"o2_pct": 2, "pressure_psi": 2, "ppo2_psi": 2,
            "airflow_cms": 2, "sample_size_mm": 2, "metric_value": 4}

ENUMS = {
    "fuel_phase": {"solid", "liquid", "gas"},
    "fuel_class": {"cabin_material", "idealized"},
    "outcome": {"burned", "extinguished", "no_ignition", "unknown"},
    "mapping_confidence": {"hand", "llm_checked", "llm_unchecked"},
}
# Tokens that mean "no value" in the source tables.
_BLANKISH = {"", "n/a", "na", "nan", "none", "-", "--"}
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
# Digits that are not measurements: note references ("Note 4", "(note 2)") and
# chemical formulas ("O2", "N2", "C2H4"). Removed before extracting numbers (D7).
_NOTE_RE = re.compile(r"\(?\bnotes?\s*\d+\)?", re.IGNORECASE)
_FORMULA_RE = re.compile(r"\b[A-Za-z]+\d[A-Za-z0-9]*\b")


def is_list_value(raw: str | None) -> bool:
    """True for cells listing several test conditions ('21; 26.5', '~30% and ~21%')."""
    if not raw:
        return False
    s = _FORMULA_RE.sub(" ", _NOTE_RE.sub(" ", raw)).lower()
    return len(_NUM_RE.findall(s)) >= 2 and (";" in s or " and " in s or " or " in s)


def parse_number(raw: str | None) -> float | None:
    """Extract one number from a messy source value (see _FORMAT.md).

    'x to y' -> midpoint; 'x and y' -> max; strips '~' and inline units;
    ignores note references and chemical formulas; blank-ish or number-less
    strings -> None.
    """
    if raw is None:
        return None
    s = raw.strip()
    if s.lower() in _BLANKISH:
        return None
    s = _FORMULA_RE.sub(" ", _NOTE_RE.sub(" ", s))
    nums = [float(m) for m in _NUM_RE.findall(s)]
    if not nums:
        return None
    low = s.lower()
    if " to " in low and len(nums) >= 2:
        return (nums[0] + nums[1]) / 2.0
    if " and " in low and len(nums) >= 2:
        return max(nums)
    return nums[0]


def convert(num: float, unit: str) -> float:
    """Apply a unit hint from the mapping (see _FORMAT.md)."""
    u = unit.strip().lower()
    if u == "fraction":
        return units.fraction_to_pct(num)
    if u == "cm":
        return num * 10.0          # cm -> mm
    if u in {"mmhg", "kpa", "atm", "bar", "psi"}:
        return units.pressure_to_psi(num, u)
    # pct, cms, mm, ratio, '' and metric units: identity
    return num


def _round(target: str, value: float) -> float:
    return round(value, ROUNDING.get(target, 4))


def _col_spec(spec: object) -> tuple[str, str]:
    """Normalise a mapping 'columns' value to (target, unit)."""
    if isinstance(spec, dict):
        return spec["to"], spec.get("unit", "")
    return str(spec), ""


def build_rows(mapping: dict, flags: list[str]) -> list[dict]:
    psi_id = mapping["psi_id"]
    path = TABLES / mapping["table"]
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.reader(fh)
        header = [h.strip() for h in next(reader)]
        body = [row for row in reader if any(c.strip() for c in row)]
    idx = {name: i for i, name in enumerate(header)}

    def cell(row: list[str], name: str) -> str | None:
        i = idx.get(name)
        return row[i] if i is not None and i < len(row) else None

    constants = mapping.get("constants", {})
    columns = mapping.get("columns", {})
    metric = mapping.get("metric")
    outcome_from = mapping.get("outcome_from")
    diluent_from = mapping.get("diluent_from")
    conf = mapping["mapping_confidence"]
    required = mapping.get("require", [])

    out_rows: list[dict] = []
    for n, row in enumerate(body):
        # Skip rows that are not test runs (notes, continuation lines, flow-vis).
        if any(not (cell(row, src) or "").strip() for src in required):
            continue
        r = {c: "" for c in SCHEMA_COLS}
        r["psi_id"] = psi_id
        r["mapping_confidence"] = conf
        for k, v in constants.items():
            r[k] = v

        for source, spec in columns.items():
            target, unit = _col_spec(spec)
            raw = cell(row, source)
            if target in STR_TARGETS:
                r[target] = (raw or "").strip()
            elif target in NUM_TARGETS:
                # A list of conditions in one cell is not one test point: blank it.
                if target in {"o2_pct", "pressure_psi"} and is_list_value(raw):
                    flags.append(f"{psi_id} row {n}: list-valued {target} {raw!r} -> blank")
                    continue
                num = parse_number(raw)
                if num is not None:
                    val = convert(num, unit)
                    # A non-positive pressure is unphysical (0 mmHg is a data gap,
                    # not a vacuum test): treat as not reported, not 0. Zero airflow,
                    # by contrast, is a real condition and is kept.
                    if target == "pressure_psi" and val <= 0:
                        flags.append(f"{psi_id} row {n}: "
                                     f"non-positive pressure {raw!r} -> blank")
                        continue
                    # Negative flow speed is unphysical (sensor offset); 0 is kept.
                    if target == "airflow_cms" and val < 0:
                        flags.append(f"{psi_id} row {n}: negative airflow {raw!r} -> blank")
                        continue
                    r[target] = _round(target, val)

        if metric:
            num = parse_number(cell(row, metric["source"]))
            if num is not None:
                r["metric_name"] = metric["name"]
                r["metric_value"] = _round("metric_value", num)
                r["metric_unit"] = metric.get("unit", "")

        if outcome_from:
            raw = (cell(row, outcome_from["source"]) or "").strip()
            if raw:
                mapped = outcome_from.get("map", {}).get(raw)
                r["outcome"] = mapped or outcome_from.get("default", "")

        if diluent_from:
            best, best_val = "", 0.0
            for name, col in diluent_from.items():
                num = parse_number(cell(row, col))
                if num is not None and num > best_val:
                    best, best_val = name, num
            if best:
                r["diluent"] = best

        # ppo2 only when both inputs are present
        if r["o2_pct"] != "" and r["pressure_psi"] != "":
            pp = units.ppo2_psi(float(r["o2_pct"]), float(r["pressure_psi"]))
            r["ppo2_psi"] = _round("ppo2_psi", pp)
            if not units.ppo2_in_range(pp):
                flags.append(f"{psi_id} run {r['run_id'] or n}: ppo2 {pp:.2f} psi "
                             f"outside 0.5-16")

        if not r["run_id"]:
            r["run_id"] = str(n)
        out_rows.append(r)
    return out_rows


def validate(rows: list[dict]) -> list[str]:
    errors = []
    for r in rows:
        for col, allowed in ENUMS.items():
            v = r[col]
            # fuel_phase/fuel_class/outcome may be blank (not reported); when
            # present they must be in the enum. mapping_confidence is required.
            if col == "mapping_confidence" and v == "":
                errors.append(f"{r['psi_id']} {r['run_id']}: empty mapping_confidence")
            elif v != "" and v not in allowed:
                errors.append(f"{r['psi_id']} {r['run_id']}: bad {col}={v!r}")
    return errors


def main() -> int:
    mapping_files = sorted(MAPPINGS.glob("PSI-*.json"))
    flags: list[str] = []
    rows: list[dict] = []
    print("== building tests.csv ==")
    for mf in mapping_files:
        mapping = json.loads(mf.read_text())
        built = build_rows(mapping, flags)
        rows.extend(built)
        print(f"  {mapping['psi_id']:>8}  {len(built):>4} rows  ({mf.name})")

    errors = validate(rows)
    if errors:
        print("\nENUM/VALIDATION ERRORS:")
        for e in errors:
            print("  -", e)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SCHEMA_COLS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(rows)} rows, "
          f"{len(mapping_files)} tables")
    if flags:
        print(f"{len(flags)} data flag(s) (rows kept, values handled, not dropped):")
        for f in flags:
            print("  -", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
