"""Warning card rules (CLAUDE.md section 8.3). Task R5."""
import pytest

from core.loaders import load_investigations, load_tests
from core.ranking import rank
from core.warnings import get_warnings

BANNED = ("safe", "will not burn", "approved")


def titles(cards):
    return {c["title"] for c in cards}


def test_demo_story_cards():
    cards = get_warnings("moon_brief", "electrical_overheat", "smoke")
    assert {"Detector blind spot", "No data yet: partial gravity"} <= titles(cards)


def test_hidden_hazard_only_for_liquid_suppression():
    assert "Hidden hazard: cool flames" in titles(get_warnings("iss", "liquid_leak", "suppression"))
    assert "Hidden hazard: cool flames" not in titles(get_warnings("iss", "liquid_leak", "ignition"))
    assert "Hidden hazard: cool flames" not in titles(get_warnings("iss", "gas_leak", "suppression"))


def test_no_data_yet_only_partial_gravity():
    assert "No data yet: partial gravity" in titles(get_warnings("exploration", "gas_leak", "ignition"))
    assert "No data yet: partial gravity" not in titles(get_warnings("iss", "gas_leak", "ignition"))


def test_earth_not_conservative_for_solid_fuel():
    assert "Earth tests are not conservative" in titles(get_warnings("iss", "cabin_material_fire", "spread"))
    assert "Earth tests are not conservative" not in titles(get_warnings("iss", "liquid_leak", "spread"))


def test_outside_tested_range_uses_ranking():
    invs, _ = load_investigations()
    tests, _ = load_tests()
    ranked = rank(invs, tests, "suit", "gas_leak", "ignition")
    cards = get_warnings("suit", "gas_leak", "ignition", ranked)
    assert titles(cards) & {"Outside the tested range", "Conditions not reported"}


@pytest.mark.parametrize("hab", ["iss", "moon_brief", "exploration", "suit"])
def test_card_shape_and_wording(hab):
    for sc, phase in [("electrical_overheat", "smoke"), ("liquid_leak", "suppression"),
                      ("cabin_material_fire", "spread")]:
        for c in get_warnings(hab, sc, phase):
            assert set(c) == {"level", "title", "body", "sources"}
            assert c["level"] in {"error", "warning", "info"}
            assert not any(b in c["body"].lower() for b in BANNED)
