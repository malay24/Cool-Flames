"""Download all PSI investigations to data/raw/ (CLAUDE.md sections 3, 7).

Task D1. Saves the raw JSON for each investigation untouched. Idempotent: skips
files that already exist unless --force. Inspect the real JSON in data/raw/
before writing any parser; do not assume field names.

Endpoint (not formally documented):
    https://psi.nasa.gov/geode-py/ws/repo/investigations/<PSI-ID>

Usage:
    python pipeline/fetch_psi.py [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
TABLES = RAW / "tables"
ENDPOINT = "https://psi.nasa.gov/geode-py/ws/repo/investigations/{psi_id}"
# Experiment tables are separate files behind the GEODE data-manager download
# route (file= is the bare file_name from the record's experimentalTable entry).
TABLE_URL = "https://psi.nasa.gov/geode-py/ws/studies/{acc}/download?source=datamanager&file={file}"
TIMEOUT = 30

# The 24 combustion investigations (CLAUDE.md section 3), grouped by area.
PSI_IDS: list[str] = [
    # prevention
    "PSI-26", "PSI-25", "PSI-98", "PSI-99", "PSI-100", "PSI-20",
    # suppression
    "PSI-69", "PSI-68", "PSI-39",
    # detection
    "PSI-102", "PSI-101", "PSI-47",
    # basic flame science
    "PSI-107", "PSI-106", "PSI-21", "PSI-10", "PSI-23", "PSI-22", "PSI-159",
    # modelling (text only)
    "PSI-62", "PSI-115", "PSI-117", "PSI-142", "PSI-60",
]


def fetch_one(psi_id: str, *, force: bool) -> str:
    """Fetch one investigation record to data/raw/<psi_id>.json.

    Returns a short status string: 'skipped', 'ok' or 'error: ...'.
    """
    out = RAW / f"{psi_id}.json"
    if out.exists() and not force:
        return "skipped"
    try:
        resp = requests.get(ENDPOINT.format(psi_id=psi_id), timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return f"error: {exc}"
    except ValueError as exc:  # non-JSON body
        return f"error: not JSON ({exc})"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return "ok"


def fetch_tables(psi_id: str, *, force: bool) -> list[str]:
    """Download every experiment table referenced by a saved investigation record.

    Returns one status string per referenced table (may be empty for text-only
    investigations). Tables are saved under data/raw/tables/ using their original
    file_name from the record.
    """
    record = RAW / f"{psi_id}.json"
    if not record.exists():
        return [f"error: {psi_id}.json not fetched yet"]
    data = json.loads(record.read_text())
    acc = data.get("accession", psi_id)
    statuses: list[str] = []
    for entry in data.get("experimentalTable") or []:
        file_name = entry.get("file_name")
        if not file_name:
            statuses.append("error: table entry has no file_name")
            continue
        out = TABLES / file_name
        if out.exists() and not force:
            statuses.append(f"skipped  {file_name}")
            continue
        url = TABLE_URL.format(acc=acc, file=urllib.parse.quote(file_name))
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            statuses.append(f"error: {file_name}: {exc}")
            continue
        out.write_bytes(resp.content)
        statuses.append(f"ok       {file_name}")
        time.sleep(0.5)
    return statuses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download PSI investigations to data/raw/.")
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    args = parser.parse_args(argv)

    RAW.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    errors = 0

    print("== investigation records ==")
    for psi_id in PSI_IDS:
        status = fetch_one(psi_id, force=args.force)
        print(f"{psi_id:>8}  {status}")
        if status.startswith("error"):
            errors += 1
        time.sleep(0.5)  # be polite to the endpoint

    print("\n== experiment tables ==")
    n_tables = 0
    for psi_id in PSI_IDS:
        for status in fetch_tables(psi_id, force=args.force):
            print(f"{psi_id:>8}  {status}")
            if status.startswith("error"):
                errors += 1
            else:
                n_tables += 1

    n_saved = len(list(RAW.glob("PSI-*.json")))
    n_csv = len(list(TABLES.glob("*.csv")))
    print(f"\n{n_saved}/{len(PSI_IDS)} records in data/raw/, "
          f"{n_csv} tables in data/raw/tables/  ({errors} error(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
