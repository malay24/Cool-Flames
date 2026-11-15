"""Unit conversion tests (CLAUDE.md sections 6.4, 11). Task D3."""
import pytest

from pipeline import units


@pytest.mark.parametrize(
    "value, unit, expected",
    [
        (1.0, "atm", 14.696),        # 1 atm
        (101.325, "kPa", 14.696),    # 1 atm in kPa
        (760.0, "mmHg", 14.696),     # 1 atm in mmHg
        (1.0, "bar", 14.504),        # 1 bar
        (14.7, "psi", 14.7),         # passthrough
        (757.7, " MMHG ", 14.652),   # real FLEX ambient pressure, messy unit
    ],
)
def test_pressure_to_psi(value, unit, expected):
    assert units.pressure_to_psi(value, unit) == pytest.approx(expected, abs=0.01)


def test_pressure_unknown_unit_raises():
    with pytest.raises(ValueError):
        units.pressure_to_psi(1.0, "furlongs")


@pytest.mark.parametrize("frac, pct", [(0.21, 21.0), (0.34, 34.0), (1.0, 100.0)])
def test_fraction_to_pct(frac, pct):
    assert units.fraction_to_pct(frac) == pytest.approx(pct)


@pytest.mark.parametrize(
    "value, pct",
    [
        (0.21, 21.0),   # fraction -> percent
        (0.34, 34.0),
        (21.0, 21.0),   # already a percentage, left alone
        (34.0, 34.0),
    ],
)
def test_normalize_o2_pct(value, pct):
    assert units.normalize_o2_pct(value) == pytest.approx(pct)


@pytest.mark.parametrize(
    "o2_pct, pressure_psi, expected",
    [
        (21.0, 14.7, 3.087),   # ISS
        (30.0, 10.2, 3.06),    # Moon (brief)
        (34.0, 8.2, 2.788),    # exploration habitat
        (100.0, 4.3, 4.3),     # spacesuit (pure O2)
    ],
)
def test_ppo2_psi(o2_pct, pressure_psi, expected):
    assert units.ppo2_psi(o2_pct, pressure_psi) == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize(
    "ppo2, ok",
    [(3.09, True), (0.5, True), (16.0, True), (0.3, False), (17.0, False)],
)
def test_ppo2_in_range(ppo2, ok):
    assert units.ppo2_in_range(ppo2) is ok
