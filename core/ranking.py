"""Transparent weighted ranking score (CLAUDE.md section 8.2). Task R2.

score = w1*area_match + w2*condition_overlap + w3*fuel_realism + w4*data_richness

Each component is in [0, 1]. Weights are divided by their sum, so the score
stays in [0, 1] whatever the sliders say (the order is unaffected). The
one-sentence explanation is a template, never an LLM. Pure logic, no Streamlit.
"""
from __future__ import annotations

import math

import pandas as pd

from core.scenarios import BASIC_AREA_CREDIT, HABITATS, PHASE_AREA, SCENARIOS

DEFAULT_WEIGHTS: dict[str, float] = {
    "area_match": 0.35,
    "condition_overlap": 0.30,
    "fuel_realism": 0.20,
    "data_richness": 0.15,
}
COMPONENTS = list(DEFAULT_WEIGHTS)
OVERLAP_RADIUS = 0.5   # normalized distance at which overlap reaches 0
O2_SCALE = 100.0       # dx = (o2_pct - h_o2) / 100
P_SCALE = 14.7         # dy = (pressure_psi - h_p) / 14.7


def area_match(inv: dict, scenario: dict, phase: str) -> float:
    """1 if the area matches the phase, 0.5 for basic science, else 0.

    Zero if none of the investigation's fuel phases is relevant to the scenario,
    except in detection phases, which ignore fuel type.
    """
    target = PHASE_AREA[phase]
    area = inv.get("area")
    score = 1.0 if area == target else BASIC_AREA_CREDIT if area == "basic" else 0.0
    if score and target != "detection":
        if not set(inv.get("fuel_types") or []) & set(scenario["fuel_phases"]):
            score = 0.0
    return score


def condition_overlap(runs: pd.DataFrame, habitat: dict) -> tuple[float, dict | None]:
    """Closeness of the nearest run (O2 %, psi) to the habitat, and that run."""
    pts = runs.dropna(subset=["o2_pct", "pressure_psi"])
    if pts.empty:
        return 0.0, None
    dx = (pts["o2_pct"] - habitat["o2_pct"]) / O2_SCALE
    dy = (pts["pressure_psi"] - habitat["pressure_psi"]) / P_SCALE
    dist = (dx ** 2 + dy ** 2) ** 0.5
    i = dist.idxmin()
    d = float(dist[i])
    nearest = {"run_id": str(pts.at[i, "run_id"]), "o2_pct": float(pts.at[i, "o2_pct"]),
               "pressure_psi": float(pts.at[i, "pressure_psi"]), "distance": round(d, 3)}
    return max(0.0, 1.0 - d / OVERLAP_RADIUS), nearest


def fuel_realism(runs: pd.DataFrame) -> float:
    """cabin_material 1.0; idealized solid/liquid 0.6; idealized gas burner 0.3."""
    classes = runs["fuel_class"].dropna()
    if classes.empty:
        return 0.0
    dominant = classes.mode().iloc[0]
    if dominant == "cabin_material":
        return 1.0
    phases = runs.loc[runs["fuel_class"] == dominant, "fuel_phase"].dropna()
    phase = phases.mode().iloc[0] if not phases.empty else ""
    return 0.3 if phase == "gas" else 0.6


def data_richness(inv: dict) -> float:
    """Test runs (log scale) and publications, with a bonus for large-scale tests."""
    n_runs = inv.get("n_runs") or inv.get("n_standardized_runs") or 0
    n_pubs = inv.get("n_publications") or 0
    score = min(1.0, math.log10(1 + n_runs) / 3) * 0.7 + min(1.0, n_pubs / 10) * 0.3
    if inv.get("test_scale") == "large":
        score += 0.2
    return min(1.0, score)


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _fuel_text(inv: dict, runs: pd.DataFrame) -> str:
    names = list(inv.get("fuels") or [])
    if not names and not runs.empty:
        names = [f for f in runs["fuel"].dropna().astype(str).value_counts().index[:3]]
    if names:
        return " of " + ", ".join(names[:3])
    phases = inv.get("fuel_types") or []
    return f" of {'/'.join(phases)} fuel" if phases else ""


def explain(rank: int, inv: dict, runs: pd.DataFrame, nearest: dict | None) -> str:
    cond = (f"nearest test at {nearest['o2_pct']:g}% O₂ / {nearest['pressure_psi']:g} psi"
            if nearest else "test O₂ and pressure not reported together")
    n_runs = inv.get("n_runs") or 0
    runs_txt = f"{n_runs} runs" if n_runs else "text only, no test table"
    return f"Ranked {_ordinal(rank)}: {inv.get('area', '?')} study{_fuel_text(inv, runs)}; {cond}; {runs_txt}."


def rank(investigations: list[dict], tests: pd.DataFrame, habitat_key: str,
         scenario_key: str, phase: str, weights: dict[str, float] | None = None) -> list[dict]:
    """Score every investigation for one habitat, scenario and phase; best first."""
    habitat = HABITATS[habitat_key]
    scenario = SCENARIOS[scenario_key]
    if phase not in scenario["phases"]:
        raise ValueError(f"phase {phase!r} is not part of scenario {scenario_key!r}")
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    total_w = sum(max(0.0, v) for v in w.values()) or 1.0

    results = []
    for inv in investigations:
        runs = tests[tests["psi_id"] == inv["psi_id"]]
        overlap, nearest = condition_overlap(runs, habitat)
        comps = {
            "area_match": area_match(inv, scenario, phase),
            "condition_overlap": overlap,
            "fuel_realism": fuel_realism(runs),
            "data_richness": data_richness(inv),
        }
        weighted = {k: max(0.0, w[k]) * v / total_w for k, v in comps.items()}
        results.append({
            "psi_id": inv["psi_id"], "name": inv.get("name", inv["psi_id"]),
            "doi": inv.get("doi", ""), "area": inv.get("area", ""),
            "score": round(sum(weighted.values()), 4),
            "components": {k: round(v, 4) for k, v in comps.items()},
            "weighted": {k: round(v, 4) for k, v in weighted.items()},
            "nearest": nearest, "conditions_reported": nearest is not None,
            "_runs": runs, "_inv": inv,
        })

    results.sort(key=lambda r: (-r["score"], int(r["psi_id"].split("-")[1])))
    for i, r in enumerate(results, 1):
        r["rank"] = i
        r["explanation"] = explain(i, r.pop("_inv"), r.pop("_runs"), r["nearest"])
    return results
