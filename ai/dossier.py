"""Investigation dossiers: facts from the PSI record and table, plus similar studies.

Everything here is copied or counted from data/raw/ (record text, experiment
tables) and data/ai/index/ (the Ask embeddings). Nothing is generated: column
names and record sentences are shown verbatim so a reader can check them.
Pure functions plus small file readers; no Streamlit imports.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

from core.loaders import ROOT

RAW = ROOT / "data" / "raw"
TABLES = RAW / "tables"
MAPPINGS = ROOT / "pipeline" / "mappings"
INDEX = ROOT / "data" / "ai" / "index"

RECORD_TEXT = [("objective", "Objective"), ("hypothesis", "Hypothesis"),
               ("approach", "Approach"), ("researchImpacts", "Research impacts")]


# ---------------------------------------------------------------- record

def load_record(psi_id: str) -> dict:
    """The raw PSI record, or {} if it is not in data/raw/ (e.g. demo data)."""
    path = RAW / f"{psi_id}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def clean(text: str | None) -> str:
    return " ".join((text or "").split())


def record_sections(record: dict) -> list[tuple[str, str]]:
    """(label, text) for objective, hypothesis, approach, research impacts that exist."""
    return [(label, clean(record.get(key))) for key, label in RECORD_TEXT if clean(record.get(key))]


def people(record: dict) -> list[str]:
    """Principal investigators as 'Name (affiliation)'; other contacts if no PI is flagged."""
    out, others = [], []
    for c in record.get("contacts") or []:
        name = " ".join(p for p in (c.get("firstName"), c.get("midInitials"), c.get("lastName")) if p)
        if not name.strip():
            continue
        label = f"{name} ({c['affiliation']})" if c.get("affiliation") else name
        roles = " ".join(r.get("annotationValue") or "" for r in c.get("roles") or [])
        (out if "Principal Investigator" in roles else others).append(label)
    return out or others


# ---------------------------------------------------------------- experiment tables

def table_files(psi_id: str) -> list[Path]:
    """Raw experiment tables of one investigation ('PSI-10_' does not match 'PSI-100_')."""
    return sorted(TABLES.glob(f"{psi_id}_*.csv"))


def read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    """(header, non-blank rows); same reading rules as pipeline/build_tests.py."""
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.reader(fh)
        header = [h.strip() for h in next(reader, [])]
        rows = [r for r in reader if any(c.strip() for c in r)]
    return header, rows


def required_columns(path: Path) -> list[str]:
    """The mapping's `require` list for this table (skips footnote and non-run rows)."""
    for m in sorted(MAPPINGS.glob("*.json")):
        spec = json.loads(m.read_text())
        if spec.get("table") == path.name:
            return spec.get("require", [])
    return []


def run_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    """(header, rows that count as test runs), filtered like pipeline/build_tests.py."""
    header, rows = read_table(path)
    idx = [header.index(c) for c in required_columns(path) if c in header]
    return header, [r for r in rows if all(i < len(r) and r[i].strip() for i in idx)]


def display_name(column: str) -> str:
    """Collapse whitespace; '?-g' in the Saffire-II headers is a lost 'μ' (paired with '1-g')."""
    return re.sub(r"^\?-g\b", "μg", clean(column))


_LOG = re.compile(
    r"^(date|gmt|gmt date|gmt ignition|gmt flame off|test date|test gmt|local time|year|month|"
    r"day|test day\*?|actual day|test|test #|as run test #|sample #|sample number|same test #|"
    r"flex number|flex test #|flex identifier|session name|pi|cir|test type|data id|"
    r"data description|reference publication link|figure id in reference|notes|comments)$")
_MEASURED = re.compile(
    r"final|after test|burn time|burning rate|burnrate|spread|burn length|extinction|weight loss|"
    r"rt/r0|ignited|hot ignition|self ?-ext|peak burner|\btfp\b|color|cool flame|test end|"
    r"frames|radiometer|camera")
_SAMPLE = re.compile(
    r"material|sample type|sample \(fuel type\)|^fuel$|^fuel type|fuel bottle|thickness|"
    r"length|width|droplet|diameter|nozzle|burner size|fiber|^description$|hardware description")


def classify_column(column: str) -> str:
    """'log', 'measured', 'sample' or 'condition', by ordered keyword rules on the header."""
    name = clean(column).lower().replace("samle", "sample")
    if _LOG.match(name):
        return "log"
    if _MEASURED.search(name):
        return "measured"
    if _SAMPLE.search(name):
        return "sample"
    return "condition"


def table_profile(psi_id: str, max_examples: int = 4) -> list[dict]:
    """One entry per raw column: table, column, category, distinct values, examples, varied."""
    out = []
    for path in table_files(psi_id):
        header, rows = run_rows(path)
        table = path.stem.split("_Experimental table_")[-1]
        for i, col in enumerate(header):
            if not col:
                continue
            seen: list[str] = []
            for r in rows:
                v = clean(r[i]) if i < len(r) else ""
                if v and v not in seen:
                    seen.append(v)
            if not seen:
                continue
            out.append({"table": table, "column": display_name(col), "category": classify_column(col),
                        "n_values": len(seen), "varied": len(seen) > 1,
                        "examples": [s if len(s) <= 40 else s[:38] + "…" for s in seen[:max_examples]]})
    return out


# ---------------------------------------------------------------- instruments

INSTRUMENTS = [
    ("Cameras / video", r"\b(cameras?|video\w*|imaging|imagery)\b"),
    ("Radiometers", r"\bradiometers?\b"),
    ("Thermocouples", r"\bthermocouples?\b"),
    ("Photomultipliers", r"\bphotomultipliers?\b"),
    ("Anemometers", r"\banemometers?\b"),
    ("Smoke detectors", r"\b(smoke detectors?|ionization (?:smoke )?detectors?|photoelectric (?:smoke )?detectors?)\b"),
    ("Aerosol monitors", r"\b(dusttrak|p-trak|particle counters?|aerosol monitors?)\b"),
    ("Thermophoretic sampling / microscopy", r"\b(thermophoretic\w*|microscop\w*|tem grids?)\b"),
    ("Lasers", r"\blasers?\b"),
    ("Pyrometry", r"\bpyromet\w*"),
    ("Chemiluminescence imaging", r"\bchemiluminescen\w*"),
    ("Gas analysers", r"\b(gas analy[sz]ers?|oxygen sensors?|o2 sensors?|co2? sensors?)\b"),
]


def _sentence(text: str, start: int, end: int, width: int = 320) -> str:
    """The sentence around a match, trimmed to about `width` characters."""
    left = max(text.rfind(". ", 0, start) + 2, 0) if text.rfind(". ", 0, start) >= 0 else 0
    right = text.find(". ", end)
    right = len(text) if right < 0 else right + 1
    s = text[left:right].strip()
    if len(s) > width:
        a = max(start - left - width // 2, 0)
        s = ("…" if a else "") + s[a:a + width].strip() + "…"
    return s


def instruments(record: dict, profile: list[dict] | None = None) -> list[dict]:
    """Instruments named in the record text or table headers, each with where it was found."""
    fields = [(label, clean(record.get(key))) for key, label in RECORD_TEXT]
    fields.append(("Hardware", clean(record.get("experimentHardware"))))
    columns = [p["column"] for p in profile or []]
    out = []
    for label, pattern in INSTRUMENTS:
        rx = re.compile(pattern, re.I)
        hit = None
        for field, text in fields:
            m = rx.search(text)
            if m:
                hit = {"label": label, "where": field, "quote": _sentence(text, m.start(), m.end())}
                break
        if hit is None:
            col = next((c for c in columns if rx.search(c)), None)
            if col:
                hit = {"label": label, "where": "Table column", "quote": col}
        if hit:
            out.append(hit)
    return out


# ---------------------------------------------------------------- similar studies

HARDWARE = {
    "Combustion Integrated Rack": r"Combustion Integrated Rack|\bCIR\b",
    "Microgravity Science Glovebox": r"Microgravity Science Glovebox|\bMSG\b",
    "ACME": r"\bACME\b",
    "Droplet apparatus (MDCA)": r"MDCA|Multi-?user Droplet",
    "Saffire on Cygnus": r"Saffire|Cygnus",
    "Comparative Soot Diagnostic hardware": r"Compar\w* Soot Diagnostic",
}
# Weights of the similarity score (shown on the page).
TEXT_WEIGHT, ATTR_WEIGHT = 0.6, 0.4
ATTR_WEIGHTS = {"area": 0.4, "phase": 0.3, "hardware": 0.2, "o2": 0.1}


def investigation_vectors(index_dir: Path = INDEX) -> dict[str, np.ndarray]:
    """Mean of each investigation's chunk embeddings (already unit length), re-normalised."""
    chunks_path, emb_path = index_dir / "chunks.json", index_dir / "embeddings.npy"
    if not (chunks_path.exists() and emb_path.exists()):
        return {}
    chunks = json.loads(chunks_path.read_text())["chunks"]
    emb = np.load(emb_path)
    if len(chunks) != len(emb):
        return {}
    out: dict[str, np.ndarray] = {}
    for pid in {c["psi_id"] for c in chunks}:
        v = emb[[i for i, c in enumerate(chunks) if c["psi_id"] == pid]].mean(axis=0)
        n = float(np.linalg.norm(v))
        if n:
            out[pid] = v / n
    return out


def hardware_tags(inv: dict) -> set[str]:
    text = f"{inv.get('hardware') or ''} {inv.get('platform') or ''}"
    return {tag for tag, rx in HARDWARE.items() if re.search(rx, text, re.I)}


def similar_studies(psi_id: str, investigations: list[dict], vectors: dict[str, np.ndarray],
                    k: int = 4) -> list[dict]:
    """Top-k other investigations by text similarity and shared attributes, with reasons."""
    by_id = {i["psi_id"]: i for i in investigations}
    a = by_id.get(psi_id)
    if a is None:
        return []
    va = vectors.get(psi_id)
    phases_a, hw_a, o2_a = set(a.get("fuel_types") or []), hardware_tags(a), a.get("o2_range")
    out = []
    for pid, b in by_id.items():
        if pid == psi_id:
            continue
        reasons = []
        text = float(va @ vectors[pid]) if va is not None and pid in vectors else 0.0
        same_area = a.get("area") == b.get("area")
        if same_area:
            reasons.append(f"same area ({a['area']})")
        phases_b = set(b.get("fuel_types") or [])
        union = phases_a | phases_b
        phase = len(phases_a & phases_b) / len(union) if union else 0.0
        if phases_a & phases_b:
            reasons.append(f"shared fuel phase: {', '.join(sorted(phases_a & phases_b))}")
        shared_hw = hw_a & hardware_tags(b)
        if shared_hw:
            reasons.append(f"same hardware: {', '.join(sorted(shared_hw))}")
        o2_b, o2 = b.get("o2_range"), 0.0
        if o2_a and o2_b and max(o2_a[0], o2_b[0]) <= min(o2_a[1], o2_b[1]):
            o2 = 1.0
            reasons.append(f"overlapping O₂ ({max(o2_a[0], o2_b[0]):g}–{min(o2_a[1], o2_b[1]):g}%)")
        attrs = (ATTR_WEIGHTS["area"] * same_area + ATTR_WEIGHTS["phase"] * phase
                 + ATTR_WEIGHTS["hardware"] * bool(shared_hw) + ATTR_WEIGHTS["o2"] * o2)
        score = TEXT_WEIGHT * max(text, 0.0) + ATTR_WEIGHT * attrs
        out.append({"psi_id": pid, "name": b.get("name", pid), "area": b.get("area", ""),
                    "doi": b.get("doi", ""), "score": round(score, 3), "text_similarity": round(text, 3),
                    "reasons": reasons})
    out.sort(key=lambda r: (-r["score"], r["psi_id"]))
    return out[:k]
