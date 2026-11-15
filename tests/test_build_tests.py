"""Messy-value parsing in pipeline/build_tests.py (D5, regression cases from D7)."""
import pytest

from pipeline.build_tests import is_list_value, parse_number


@pytest.mark.parametrize("raw, expected", [
    ("~ 21.5", 21.5),
    ("22.1 to 22.0", 22.05),
    ("5 and 24 cm", 24.0),
    ("20 cm/s", 20.0),
    ("1 atm", 1.0),
    ("n/a", None),
    ("", None),
    ("Note 4", None),             # Saffire-II spread column: a note, not 4 mm/s
    ("2.6 mm/s (note 3)", 2.6),
    ("LOW O2", None),             # Flame Design XO2: not a mole fraction of 2
    ("RAMP", None),
    ("~21% O2 with N2", 21.0),
])
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("21; 26.5; 40", True),
    ("~30% and ~21% O2 with He", True),
    ("0.5; 1.0; 1.5; 2.0; or 3.0", True),
    ("~21% O2 with N2", False),
    ("22.1 to 22.0", False),
    ("0.21", False),
])
def test_is_list_value(raw, expected):
    assert is_list_value(raw) is expected
