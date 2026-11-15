"""Spot-check cleaned rows against the raw tables (task D7).

Samples rows from data/clean/tests.csv (fixed seed, spread across tables),
finds each source row in data/raw/tables/ via its mapping, and prints the raw
cells next to the cleaned values for a human to compare.

Usage (from the repo root):
    python -m pipeline.spot_check            # 20 rows, seed 7
    python -m pipeline.spot_check -n 30 --seed 1
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "data" / "raw" / "tables"
MAPPINGS = ROOT / "pipeline" / "mappings"
TESTS = ROOT / "data" / "clean" / "tests.csv"

SHOW = ["fuel", "fuel_phase", "o2_pct", "pressure_psi", "ppo2_psi", "diluent", "airflow_cms",
        "sample_size_mm", "outcome", "metric_name", "metric_value", "metric_unit"]


def raw_body(table: str) -> tuple[list[str], list[list[str]]]:
    with (TABLES / table).open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.reader(fh)
        header = [h.strip() for h in next(reader)]
        body = [row for row in reader if any(c.strip() for c in row)]
    return header, body


def find_source(row: dict, mappings: list[dict]) -> tuple[dict, list[str], list[str]] | None:
    """Return (mapping, header, raw_row) for a cleaned row, or None."""
    for m in mappings:
        header, body = raw_body(m["table"])
        idx = {h: i for i, h in enumerate(header)}
        id_col = next((src for src, spec in m.get("columns", {}).items()
                       if spec == "run_id"), None)
        if id_col:
            for r in body:
                i = idx.get(id_col)
                if i is not None and i < len(r) and r[i].strip() == row["run_id"]:
                    return m, header, r
        elif row["run_id"].isdigit() and int(row["run_id"]) < len(body):
            return m, header, body[int(row["run_id"])]
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)

    with TESTS.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_psi: dict[str, list[dict]] = {}
    for r in rows:
        by_psi.setdefault(r["psi_id"], []).append(r)
    maps: dict[str, list[dict]] = {}
    for mf in sorted(MAPPINGS.glob("PSI-*.json")):
        m = json.loads(mf.read_text())
        maps.setdefault(m["psi_id"], []).append(m)

    # Round-robin across investigations so every table is represented.
    rng = random.Random(args.seed)
    pools = {k: rng.sample(v, len(v)) for k, v in sorted(by_psi.items())}
    sample: list[dict] = []
    while len(sample) < min(args.n, len(rows)):
        for k in list(pools):
            if pools[k] and len(sample) < args.n:
                sample.append(pools[k].pop())

    missing = 0
    for n, row in enumerate(sample, 1):
        print(f"\n[{n}] {row['psi_id']} run {row['run_id']}  ({row['mapping_confidence']})")
        found = find_source(row, maps.get(row["psi_id"], []))
        if not found:
            print("   !! source row not found")
            missing += 1
            continue
        m, header, raw = found
        idx = {h: i for i, h in enumerate(header)}
        print(f"   table: {m['table']}")
        for src, spec in m.get("columns", {}).items():
            target = spec if isinstance(spec, str) else spec["to"]
            i = idx.get(src)
            rawv = raw[i].strip() if i is not None and i < len(raw) else "<missing column>"
            print(f"   {src!r:45} {rawv!r:28} -> {target} = {row.get(target, '')!r}")
        for key in ("metric", "outcome_from"):
            spec = m.get(key)
            if spec:
                i = idx.get(spec["source"])
                rawv = raw[i].strip() if i is not None and i < len(raw) else "<missing column>"
                print(f"   {spec['source']!r:45} {rawv!r:28} -> {key}")
        print("   cleaned: " + ", ".join(f"{c}={row[c]}" for c in SHOW if row.get(c)))
    print(f"\n{len(sample)} rows checked, {missing} without a findable source row")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
