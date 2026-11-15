"""Habitat presets, fire scenarios and phases (CLAUDE.md sections 2 and 8.1).

Task R1. Pure data, no Streamlit imports.
"""
from __future__ import annotations

# Habitat atmospheres (CLAUDE.md section 2). ppo2_psi = o2_pct / 100 * pressure_psi.
# partial_gravity marks Moon/Mars habitats, where PSI has no data.
HABITATS: dict[str, dict] = {
    "iss": {
        "label": "ISS", "o2_pct": 21.0, "pressure_psi": 14.7, "ppo2_psi": 3.09,
        "partial_gravity": False, "gravity_g": 0.0, "source": "challenge brief",
    },
    "moon_brief": {
        "label": "Moon Base / pressurized rover", "o2_pct": 30.0, "pressure_psi": 10.2,
        "ppo2_psi": 3.06, "partial_gravity": True, "gravity_g": 0.166,
        "source": "challenge brief (30%+ O2 at 10.2 psi or less)",
    },
    "exploration": {
        "label": "Exploration habitat (NASA)", "o2_pct": 34.0, "pressure_psi": 8.2,
        "ppo2_psi": 2.79, "partial_gravity": True, "gravity_g": 0.166,
        "source": "NASA exploration atmosphere, revised in 2012",
    },
    "suit": {
        "label": "Spacesuit", "o2_pct": 100.0, "pressure_psi": 4.3, "ppo2_psi": 4.30,
        "partial_gravity": False, "gravity_g": 0.0, "source": "challenge brief",
    },
}

# gravity_g (Earth = 1) drives the illustrative Flame Lab and hero animation only:
# ISS and the ISS spacewalk suit are in microgravity; the Moon base and NASA's
# exploration habitat are taken as lunar-surface habitats (1/6 g).


def resolve_habitat(habitat: str | dict) -> dict:
    """Return a habitat dict for a preset key or a custom atmosphere dict.

    A custom dict needs o2_pct and pressure_psi; label, ppo2_psi,
    partial_gravity and gravity_g are filled in when missing.
    """
    if isinstance(habitat, str):
        return HABITATS[habitat]
    if not isinstance(habitat, dict) or "o2_pct" not in habitat or "pressure_psi" not in habitat:
        raise ValueError("custom habitat needs o2_pct and pressure_psi")
    o2, p = float(habitat["o2_pct"]), float(habitat["pressure_psi"])
    if not (0 < o2 <= 100 and p > 0):
        raise ValueError(f"unphysical habitat: {o2}% O2 at {p} psi")
    g = float(habitat.get("gravity_g", 0.0))
    return {"label": habitat.get("label", "Custom atmosphere"), "o2_pct": o2, "pressure_psi": p,
            "ppo2_psi": round(o2 / 100 * p, 2), "gravity_g": g,
            "partial_gravity": bool(habitat.get("partial_gravity", 0 < g < 1)),
            "source": habitat.get("source", "designed in the app")}


PHASES = ["smoke", "ignition", "spread", "suppression"]

# Fire phase -> NASA fire-safety area (CLAUDE.md section 8.1).
PHASE_AREA: dict[str, str] = {
    "smoke": "detection",
    "ignition": "prevention",
    "spread": "prevention",
    "suppression": "suppression",
}
BASIC_AREA_CREDIT = 0.5  # investigations with area "basic" get partial credit

SCENARIOS: dict[str, dict] = {
    "electrical_overheat": {
        "label": "Electrical overheat (wiring, avionics)",
        "short": "Electrical overheat", "icon": ":material/electric_bolt:",
        "phases": ["smoke", "ignition", "spread", "suppression"],
        "fuel_phases": ["solid"],
    },
    "cabin_material_fire": {
        "label": "Cabin material fire (fabric, plastics)",
        "short": "Cabin material fire", "icon": ":material/chair:",
        "phases": ["ignition", "spread", "suppression"],
        "fuel_phases": ["solid"],
    },
    "liquid_leak": {
        "label": "Liquid leak (lubricant, cleaning fluid)",
        "short": "Liquid leak", "icon": ":material/water_drop:",
        "phases": ["ignition", "spread", "suppression"],
        "fuel_phases": ["liquid"],
    },
    "gas_leak": {
        "label": "Gas leak (O2 or fuel line)",
        "short": "Gas leak", "icon": ":material/gas_meter:",
        "phases": ["ignition", "spread", "suppression"],
        "fuel_phases": ["gas"],
    },
    "oxygen_rich_cabin": {
        "label": "Oxygen-rich cabin (Apollo 1 type)",
        "short": "Oxygen-rich cabin", "icon": ":material/air:",
        "phases": ["ignition", "spread", "suppression"],
        "fuel_phases": ["solid", "gas"],
    },
    "lunar_dust": {
        "label": "Lunar dust and detectors",
        "short": "Lunar dust", "icon": ":material/dark_mode:",
        "phases": ["smoke"],
        "fuel_phases": [],  # detection only
    },
}

PHASE_ICONS = {"smoke": ":material/cloud:", "ignition": ":material/local_fire_department:",
               "spread": ":material/trending_up:", "suppression": ":material/fire_extinguisher:"}

PHASE_LABELS = {
    "smoke": "Smoke (detection)",
    "ignition": "Ignition (prevention)",
    "spread": "Spread (prevention)",
    "suppression": "Suppression",
}

# Static historical context for the UI (CLAUDE.md section 8.1).
HISTORY = [
    ("Apollo 1 (1967)", "Fire in a pure-oxygen cabin during a pre-launch test; the crew was lost."),
    ("Apollo 13 (1970)", "Oxygen tank failure; damaged insulation in pure oxygen."),
    ("Mir (1997)", "Fire in an oxygen generator, which supplied its own oxygen."),
]
HISTORY_NOTE = ("All three involved extra oxygen, the condition planned for the Moon Base "
                "(30%+ O2).")
