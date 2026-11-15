"""Unit conversions for the data pipeline (CLAUDE.md section 6.4).

Task D3. Pure numeric helpers only — parsing messy source strings (e.g. "~21.5",
"20 cm/s") is the job of build_tests.py (D5), not this module.

Reference conversions:
    1 atm  = 14.696 psi
    1 kPa  = 0.14504 psi
    1 mmHg = 0.019337 psi
    1 bar  = 14.504 psi
    O2 mole fraction 0.21 -> 21 % (fractions, value <= 1.0, are multiplied by 100)

A computed ppO2 outside 0.5 to 16 psi is flagged (not dropped) by callers.
"""
from __future__ import annotations

# Pressure unit -> psi multiplier. Keys are lowercase, stripped.
_PRESSURE_FACTORS: dict[str, float] = {
    "psi": 1.0,
    "atm": 14.696,
    "kpa": 0.14504,
    "mmhg": 0.019337,
    "bar": 14.504,
}

# Plausible ppO2 band for these investigations (CLAUDE.md section 6.4).
PPO2_MIN_PSI = 0.5
PPO2_MAX_PSI = 16.0


def pressure_to_psi(value: float, unit: str) -> float:
    """Convert a pressure to psi. `unit` is one of atm, kPa, mmHg, bar, psi."""
    key = unit.strip().lower()
    try:
        factor = _PRESSURE_FACTORS[key]
    except KeyError:
        raise ValueError(
            f"unknown pressure unit {unit!r}; expected one of "
            f"{sorted(_PRESSURE_FACTORS)}"
        ) from None
    return value * factor


def fraction_to_pct(fraction: float) -> float:
    """Convert a mole fraction (0.21) to a percentage (21.0)."""
    return fraction * 100.0


def normalize_o2_pct(value: float) -> float:
    """Return O2 as a percentage, treating values <= 1.0 as mole fractions.

    0.21 -> 21.0; 21 -> 21.0. Use when a column may hold either form. When the
    source form is known, prefer fraction_to_pct for clarity.
    """
    return value * 100.0 if value <= 1.0 else float(value)


def ppo2_psi(o2_pct: float, pressure_psi: float) -> float:
    """Partial pressure of O2 in psi: o2_pct / 100 * pressure_psi."""
    return o2_pct / 100.0 * pressure_psi


def ppo2_in_range(value_psi: float) -> bool:
    """True if a ppO2 (psi) falls within the plausible 0.5 to 16 psi band."""
    return PPO2_MIN_PSI <= value_psi <= PPO2_MAX_PSI
