"""Warning card rules (CLAUDE.md section 8.3). Task R5.

get_warnings() returns a list of {level, title, body, sources}; the app renders
them. Wording follows the positioning rule: "tests show", "no data", never
"safe". Pure logic, no Streamlit.
"""
from __future__ import annotations

from core.scenarios import SCENARIOS, resolve_habitat

# Citations from CLAUDE.md section 14.
SRC_FM2 = "Ferkul, Kralik, Liao 2026, Material flammability at lunar and Martian gravity (LPSC)"
SRC_FLEX_COOL = ("Nayagam et al. 2012, Can cool flames support quasi-steady alkane droplet "
                 "burning?, Combustion and Flame 159 (FLEX)")
SRC_MEYER = ("Meyer et al. 2018, Spacecraft smoke detector performance in low gravity, "
             "Fire Safety Journal (SAME, SAME-R)")
SRC_URBAN_SMOKE = "Urban et al. 2009, Smoke particle sizes in low-gravity, SAE (SAME)"
SRC_BASS_PMMA = "Flame spread over PMMA in microgravity, Scientific Reports 2018 (BASS)"
SRC_OLSON = "Olson 2004, Why NASA's current Test 1 might not always be conservative (NTRS)"

NEAR_TOLERANCE = 0.02  # normalized distance treated as "inside the tested range"
TOP_N = 3


def _no_data_yet(habitat: dict) -> dict:
    return {
        "level": "warning",
        "title": "No data yet: partial gravity",
        "body": (f"{habitat['label']} sits in partial gravity (Moon 1/6 g, Mars about 3/8 g). "
                 "PSI holds no partial-gravity combustion data. Microgravity and 1 g results "
                 "bound the in-between, and weak buoyancy may act like the gentle breeze in "
                 "which materials burn most readily. FM2 and LUCI will add data."),
        "sources": [SRC_FM2],
    }


def _hidden_hazard() -> dict:
    return {
        "level": "error",
        "title": "Hidden hazard: cool flames",
        "body": ("FLEX heptane droplets kept burning invisibly, at roughly 500 to 800 K, after "
                 "the visible flame went out. A liquid fire that looks extinguished may still "
                 "be reacting."),
        "sources": [SRC_FLEX_COOL],
    }


def _detector_blind_spot() -> dict:
    return {
        "level": "error",
        "title": "Detector blind spot",
        "body": ("Tests show the ISS smoke detector often missed the small smoke particles "
                 "from overheated Teflon and Kapton, materials common in wiring and "
                 "electronics, the most likely ignition source."),
        "sources": [SRC_MEYER, SRC_URBAN_SMOKE],
    }


def _earth_not_conservative() -> dict:
    return {
        "level": "warning",
        "title": "Earth tests are not conservative",
        "body": ("Some materials burn at lower oxygen in microgravity than on Earth: BASS "
                 "PMMA sustained flame spread at 17% O₂ in microgravity versus 18% in Earth "
                 "gravity, and opposed-flow flames have been sustained at 14% O₂ under the "
                 "right flow."),
        "sources": [SRC_BASS_PMMA, SRC_OLSON],
    }


def _outside_tested_range(habitat: dict, ranked: list[dict]) -> dict | None:
    top = [r for r in ranked if r["components"]["area_match"] > 0][:TOP_N]
    if not top:
        return None
    with_cond = [r for r in top if r.get("nearest")]
    names = ", ".join(r["name"] for r in top)
    if not with_cond:
        return {
            "level": "info",
            "title": "Conditions not reported",
            "body": (f"The top-ranked investigations ({names}) do not report O₂ and pressure "
                     f"together, so their closeness to {habitat['label']} "
                     f"({habitat['o2_pct']:g}% O₂, {habitat['pressure_psi']:g} psi) cannot "
                     "be checked."),
            "sources": [],
        }
    best = min(with_cond, key=lambda r: r["nearest"]["distance"])
    near = best["nearest"]
    if near["distance"] <= NEAR_TOLERANCE:
        return None
    d_o2 = near["o2_pct"] - habitat["o2_pct"]
    d_p = near["pressure_psi"] - habitat["pressure_psi"]
    return {
        "level": "info",
        "title": "Outside the tested range",
        "body": (f"No top-ranked test matches {habitat['label']} "
                 f"({habitat['o2_pct']:g}% O₂, {habitat['pressure_psi']:g} psi). The nearest "
                 f"is {best['name']} run {near['run_id']} at {near['o2_pct']:g}% O₂ / "
                 f"{near['pressure_psi']:g} psi: {abs(d_o2):.1f} O₂ points "
                 f"{'above' if d_o2 > 0 else 'below'} and {abs(d_p):.1f} psi "
                 f"{'above' if d_p > 0 else 'below'}."),
        "sources": [],
    }


def get_warnings(habitat_key: str | dict, scenario_key: str, phase: str,
                 ranked: list[dict] | None = None) -> list[dict]:
    """Warning cards for one habitat, scenario and phase (most severe first)."""
    habitat = resolve_habitat(habitat_key)
    scenario = SCENARIOS[scenario_key]
    fuels = set(scenario["fuel_phases"])
    cards: list[dict] = []
    if scenario_key == "electrical_overheat" and phase == "smoke":
        cards.append(_detector_blind_spot())
    if "liquid" in fuels and phase == "suppression":
        cards.append(_hidden_hazard())
    if habitat.get("partial_gravity"):
        cards.append(_no_data_yet(habitat))
    if "solid" in fuels:
        cards.append(_earth_not_conservative())
    if ranked:
        card = _outside_tested_range(habitat, ranked)
        if card:
            cards.append(card)
    return cards
