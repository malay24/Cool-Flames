"""Build data/ai/investigations.json (tasks A1/A2, contract in SCHEMA.md / CLAUDE.md 6.2).

Facts (psi_id, name, doi, hardware, platform, area, test_scale, publications,
n_runs) come from data/raw/ and the team's hand maps, never from an LLM.
AI fields (fuels, fuel_types, summary_3line, key_findings) come from a batch
file produced offline (no API key needed), or optionally from Gemini.

`fuel_types` follows the signed contract: fuel PHASES (solid/liquid/gas), as
used by core/ranking.py. `fuels` (material names, display only) is additive.
Ranges come from data/clean/ranges.csv (D8: python -m pipeline.build_ranges).

Usage:
    python ai/tag_summarize.py                                  # facts only, AI fields empty
    python ai/tag_summarize.py --import data/ai/ai_fields.json  # merge batch output
    python ai/tag_summarize.py --export-batch                   # write data/ai/batch_input.jsonl
    python ai/tag_summarize.py --llm --only PSI-26,PSI-69       # optional Gemini fallback
    python ai/tag_summarize.py --dry-run --only PSI-26          # print one prompt

Batch output format (data/ai/ai_fields.json):
    {"PSI-26": {"fuels": ["PMMA"], "fuel_types": ["solid"],
                "summary_3line": "line 1\\nline 2\\nline 3",
                "key_findings": ["...", "..."]}, ...}
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RAW = ROOT / "data" / "raw"
TABLES = RAW / "tables"
OUT = ROOT / "data" / "ai" / "investigations.json"
CACHE = ROOT / "data" / "ai" / "cache"
BATCH_IN = ROOT / "data" / "ai" / "batch_input.jsonl"
PROMPT = ROOT / "ai" / "prompts" / "tag_summarize.md"
RANGES = ROOT / "data" / "clean" / "ranges.csv"

AREAS = ["prevention", "suppression", "detection", "basic", "modelling"]
PHASES = ["solid", "liquid", "gas"]

# Fire-safety area per investigation (CLAUDE.md section 3).
AREA: dict[str, str] = {
    **dict.fromkeys(["PSI-26", "PSI-25", "PSI-98", "PSI-99", "PSI-100", "PSI-20"], "prevention"),
    **dict.fromkeys(["PSI-69", "PSI-68", "PSI-39"], "suppression"),
    **dict.fromkeys(["PSI-102", "PSI-101", "PSI-47"], "detection"),
    **dict.fromkeys(["PSI-107", "PSI-106", "PSI-21", "PSI-10", "PSI-23", "PSI-22", "PSI-159"], "basic"),
    **dict.fromkeys(["PSI-62", "PSI-115", "PSI-117", "PSI-142", "PSI-60"], "modelling"),
}

# Fuel phases per investigation (CLAUDE.md section 3 fuel map). Modelling studies
# take the phase of the flight data they model. DAFT studies dust, not a fuel.
FUEL_TYPES: dict[str, list[str]] = {
    **dict.fromkeys(["PSI-26", "PSI-25", "PSI-98", "PSI-99", "PSI-100",
                     "PSI-102", "PSI-101", "PSI-62", "PSI-115"], ["solid"]),
    **dict.fromkeys(["PSI-69", "PSI-68", "PSI-39", "PSI-117", "PSI-142"], ["liquid"]),
    **dict.fromkeys(["PSI-20", "PSI-21", "PSI-10", "PSI-23", "PSI-22", "PSI-159",
                     "PSI-107", "PSI-106", "PSI-60"], ["gas"]),
    "PSI-47": [],
}
LARGE_SCALE = {"PSI-98", "PSI-99", "PSI-100"}  # Saffire I-III on Cygnus

# Gemini response schema (OpenAPI subset), only used with --llm.
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "fuels": {"type": "ARRAY", "items": {"type": "STRING"}},
        "fuel_types": {"type": "ARRAY", "items": {"type": "STRING", "enum": PHASES}},
        "summary_3line": {"type": "STRING"},
        "key_findings": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["fuels", "fuel_types", "summary_3line", "key_findings"],
}

MAX_FIELD = 3000      # chars per text field in the prompt
MAX_PUBS = 20
SAMPLE_ROWS = 3


# ---------- raw record helpers ----------

def _clean(text: str | None, limit: int = MAX_FIELD) -> str:
    text = " ".join((text or "").split())
    return text[:limit] or "(not given)"


def read_table(path: Path) -> list[list[str]]:
    """Non-empty rows of a raw CSV (handles BOM; many tables pad with blank rows)."""
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
        return [row for row in csv.reader(fh) if any(c.strip() for c in row)]


def table_files(record: dict) -> list[Path]:
    files = []
    for entry in record.get("experimentalTable") or []:
        p = TABLES / (entry.get("file_name") or "")
        if p.is_file():
            files.append(p)
    return files


def describe_tables(files: list[Path]) -> str:
    parts = []
    for p in files:
        rows = read_table(p)
        if not rows:
            continue
        lines = [f"{p.name} ({len(rows) - 1} rows)",
                 "header: " + " | ".join(c.strip() for c in rows[0])]
        for r in rows[1:1 + SAMPLE_ROWS]:
            lines.append("row: " + " | ".join(c.strip() for c in r)[:300])
        parts.append("\n".join(lines))
    return "\n\n".join(parts) or "(no experiment table)"


def load_records() -> dict[str, dict]:
    recs = {}
    for p in RAW.glob("PSI-*.json"):
        d = json.loads(p.read_text())
        recs[d["accession"]] = d
    return dict(sorted(recs.items(), key=lambda kv: int(kv[0][4:])))


def load_ranges() -> dict[str, dict]:
    """Ranges from data/clean/ranges.csv (D8): psi_id -> contract range fields."""
    if not RANGES.exists():
        return {}
    out = {}
    with RANGES.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            def rng(key: str):
                lo, hi = r.get(f"{key}_min", ""), r.get(f"{key}_max", "")
                return [float(lo), float(hi)] if lo != "" and hi != "" else None
            out[r["psi_id"]] = {
                "o2_range": rng("o2"), "pressure_range": rng("pressure"),
                "airflow_range": rng("airflow"), "sample_size_range": rng("sample_size"),
                "n_standardized_runs": int(r["n_standardized_runs"]),
            }
    return out


_RANGES: dict[str, dict] | None = None


def facts(record: dict) -> dict:
    """Contract fields copied from the raw record and hand maps (no LLM)."""
    global _RANGES
    if _RANGES is None:
        _RANGES = load_ranges()
    psi_id = record["accession"]
    pubs = record.get("publications") or []
    files = table_files(record)
    area = AREA.get(psi_id, "basic")
    rng = _RANGES.get(psi_id, {})
    return {
        "psi_id": psi_id,
        "name": (record.get("investigationAcronym") or "").strip() or record.get("title", psi_id),
        "title": record.get("title", ""),
        "doi": record.get("doi", ""),
        "area": area,
        "fuel_types": list(FUEL_TYPES.get(psi_id, [])),
        "fuels": [],
        "hardware": record.get("experimentHardware", ""),
        "platform": record.get("flightProgram", ""),
        "summary_3line": "",
        "key_findings": [],
        "n_runs": sum(max(len(read_table(p)) - 1, 0) for p in files),  # raw table rows
        "n_publications": len(pubs),
        "n_standardized_runs": rng.get("n_standardized_runs", 0),
        "o2_range": rng.get("o2_range"),            # from ranges.csv (D8), never the LLM
        "pressure_range": rng.get("pressure_range"),
        "airflow_range": rng.get("airflow_range"),
        "sample_size_range": rng.get("sample_size_range"),
        "test_scale": "large" if psi_id in LARGE_SCALE
        else "ground" if area == "modelling" else "orbital",
        "start_date": record.get("investigationStartDate", ""),
        "end_date": record.get("investigationEndDate", ""),
        "publications": [
            {"title": p.get("title", ""), "authors": p.get("authorList", ""), "doi": p.get("doi", "")}
            for p in pubs
        ],
        "ai_source": None,
    }


def build_prompt(record: dict, f: dict) -> str:
    pubs = record.get("publications") or []
    pub_lines = "\n".join(f"- {_clean(p.get('title'), 300)}" for p in pubs[:MAX_PUBS]) or "(none)"
    return PROMPT.read_text().format(
        name=f["name"], psi_id=f["psi_id"], title=f["title"], area=f["area"],
        platform=_clean(f["platform"], 200), hardware=_clean(f["hardware"], 300),
        sub_area=_clean(record.get("subResearchArea"), 200),
        objective=_clean(record.get("objective")),
        hypothesis=_clean(record.get("hypothesis")),
        approach=_clean(record.get("approach")),
        impacts=_clean(record.get("researchImpacts")),
        description=_clean(record.get("description")),
        publications=pub_lines,
        tables=describe_tables(table_files(record)),
    )


# ---------- AI field validation ----------

def validate(out: dict) -> list[str]:
    errs = []
    if not isinstance(out, dict):
        return ["not an object"]
    if not isinstance(out.get("fuels", []), list):
        errs.append("fuels not a list")
    ft = out.get("fuel_types")
    if not isinstance(ft, list) or any(p not in PHASES for p in ft):
        errs.append(f"bad fuel_types: {ft!r}")
    summary = out.get("summary_3line")
    if not isinstance(summary, str) or not summary.strip():
        errs.append("empty summary_3line")
    kf = out.get("key_findings")
    if not isinstance(kf, list) or not 1 <= len(kf) <= 4:
        errs.append(f"key_findings must have 1-4 items, got {kf!r}")
    return errs


def normalise(out: dict) -> dict:
    lines = [ln.strip(" -•\t") for ln in out["summary_3line"].splitlines() if ln.strip()]
    return {
        "fuels": [s.strip() for s in out.get("fuels", []) if s.strip()][:8],
        "fuel_types": sorted(set(out["fuel_types"]), key=PHASES.index),
        "summary_3line": "\n".join(lines[:3]),
        "key_findings": [s.strip() for s in out["key_findings"] if s.strip()][:4],
    }


def merge(f: dict, ai: dict, source: str) -> dict:
    """AI text fields win; fuel_types keeps the hand map unless it is empty."""
    merged = {**f, **ai, "ai_source": source}
    if f["fuel_types"]:
        merged["fuel_types"] = f["fuel_types"]
    return merged


def summarize_llm(record: dict, f: dict, *, force: bool) -> dict | None:
    from ai.llm import LLMUnavailable, call_llm_json

    cache = CACHE / f"{f['psi_id']}.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text())
    prompt = build_prompt(record, f)
    last_err = ""
    for _ in (1, 2):  # retry once on invalid output
        try:
            out = call_llm_json(prompt, SCHEMA)
        except (LLMUnavailable, ValueError) as exc:
            last_err = str(exc)
            continue
        errs = validate(out)
        if not errs:
            out = normalise(out)
            CACHE.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(out, indent=2, ensure_ascii=False))
            return out
        last_err = "; ".join(errs)
    print(f"  ! {f['psi_id']}: {last_err}", file=sys.stderr)
    return None


# ---------- main ----------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build data/ai/investigations.json")
    ap.add_argument("--only", help="comma-separated PSI ids, e.g. PSI-26,PSI-69")
    ap.add_argument("--import", dest="import_path", help="batch AI output JSON to merge")
    ap.add_argument("--export-batch", action="store_true", help="write prompts to batch_input.jsonl")
    ap.add_argument("--llm", action="store_true", help="call Gemini (needs GEMINI_API_KEY)")
    ap.add_argument("--force", action="store_true", help="with --llm: ignore the cache")
    ap.add_argument("--dry-run", action="store_true", help="print prompts, write nothing")
    args = ap.parse_args(argv)

    records = load_records()
    ids = [s.strip() for s in args.only.split(",")] if args.only else list(records)
    missing = [i for i in ids if i not in records]
    if missing:
        print(f"unknown PSI ids: {missing}", file=sys.stderr)
        return 2

    if args.dry_run or args.export_batch:
        lines = []
        for psi_id in ids:
            prompt = build_prompt(records[psi_id], facts(records[psi_id]))
            if args.dry_run:
                print(f"===== {psi_id} =====\n{prompt}\n")
            lines.append(json.dumps({"psi_id": psi_id, "prompt": prompt}, ensure_ascii=False))
        if args.export_batch:
            BATCH_IN.parent.mkdir(parents=True, exist_ok=True)
            BATCH_IN.write_text("\n".join(lines) + "\n")
            print(f"wrote {len(lines)} prompts to {BATCH_IN.relative_to(ROOT)}")
        return 0

    batch: dict = {}
    if args.import_path:
        batch = json.loads(Path(args.import_path).read_text())

    # Start from the existing file so AI fields already merged are kept.
    existing = {}
    if OUT.exists():
        existing = {d["psi_id"]: d for d in json.loads(OUT.read_text())}

    failures = 0
    for psi_id, record in records.items():
        f = facts(record)
        prev = existing.get(psi_id, {})
        if prev.get("ai_source"):  # keep earlier AI text unless regenerated below
            f = merge(f, {k: prev[k] for k in ("fuels", "summary_3line", "key_findings")
                          if k in prev}, prev["ai_source"])
        if psi_id in ids:
            if psi_id in batch:
                errs = validate(batch[psi_id])
                if errs:
                    print(f"  ! {psi_id}: {'; '.join(errs)}", file=sys.stderr)
                    failures += 1
                else:
                    f = merge(f, normalise(batch[psi_id]), "batch")
            elif args.llm:
                ai = summarize_llm(record, f, force=args.force)
                if ai is None:
                    failures += 1
                else:
                    f = merge(f, ai, "gemini")
        existing[psi_id] = f

    if args.import_path:
        unknown = sorted(set(batch) - set(records))
        if unknown:
            print(f"  ! ignored unknown ids in batch file: {unknown}", file=sys.stderr)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ordered = [existing[i] for i in records]
    OUT.write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n")
    with_ai = sum(1 for d in ordered if d.get("summary_3line"))
    print(f"wrote {len(ordered)} investigations to {OUT.relative_to(ROOT)} "
          f"({with_ai} with summaries, {failures} failed)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
