"""Ranking tests (CLAUDE.md section 8.2). Tasks R2/R3.

Must pass: moon_brief + electrical_overheat, phase smoke ranks SAME/SAME-R top.
"""
import pandas as pd
import pytest

from core.loaders import load_investigations, load_tests
from core.ranking import (COMPONENTS, DEFAULT_WEIGHTS, area_match, condition_overlap,
                          data_richness, rank)
from core.scenarios import HABITATS, SCENARIOS


@pytest.fixture(scope="module")
def data():
    invs, _ = load_investigations()
    tests, _ = load_tests()
    return invs, tests


def test_sanity_moon_electrical_smoke(data):
    """R3: SAME (PSI-102) and SAME-R (PSI-101) rank top in the smoke phase."""
    invs, tests = data
    top2 = {r["psi_id"] for r in rank(invs, tests, "moon_brief", "electrical_overheat", "smoke")[:2]}
    assert top2 == {"PSI-101", "PSI-102"}


@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_components_in_unit_interval(data, scenario):
    invs, tests = data
    for phase in SCENARIOS[scenario]["phases"]:
        for r in rank(invs, tests, "iss", scenario, phase):
            assert 0.0 <= r["score"] <= 1.0
            assert set(r["components"]) == set(COMPONENTS)
            assert all(0.0 <= v <= 1.0 for v in r["components"].values())


def test_weights_change_order(data):
    invs, tests = data
    default = [r["psi_id"] for r in rank(invs, tests, "moon_brief", "electrical_overheat", "smoke")]
    overlap_only = {k: 0.0 for k in DEFAULT_WEIGHTS} | {"condition_overlap": 1.0}
    reweighted = [r["psi_id"] for r in rank(invs, tests, "moon_brief", "electrical_overheat",
                                            "smoke", weights=overlap_only)]
    assert default[0] != reweighted[0]


def test_explanation_is_template(data):
    invs, tests = data
    top = rank(invs, tests, "iss", "liquid_leak", "suppression")[0]
    assert top["explanation"].startswith("Ranked 1st:")


def test_area_match_rules():
    sc = SCENARIOS["liquid_leak"]
    assert area_match({"area": "suppression", "fuel_types": ["liquid"]}, sc, "suppression") == 1.0
    assert area_match({"area": "basic", "fuel_types": ["liquid"]}, sc, "suppression") == 0.5
    assert area_match({"area": "suppression", "fuel_types": ["gas"]}, sc, "suppression") == 0.0
    # detection phases ignore fuel type
    smoke = SCENARIOS["lunar_dust"]
    assert area_match({"area": "detection", "fuel_types": []}, smoke, "smoke") == 1.0


def test_condition_overlap_exact_and_missing():
    hab = HABITATS["iss"]
    exact = pd.DataFrame({"run_id": ["a"], "o2_pct": [21.0], "pressure_psi": [14.7]})
    assert condition_overlap(exact, hab)[0] == pytest.approx(1.0)
    none = pd.DataFrame({"run_id": ["a"], "o2_pct": [21.0], "pressure_psi": [float("nan")]})
    assert condition_overlap(none, hab) == (0.0, None)


def test_data_richness_large_bonus_capped():
    base = {"n_runs": 999, "n_publications": 10, "test_scale": "large"}
    assert data_richness(base) == 1.0
    assert data_richness({"n_runs": 0, "n_publications": 0}) == 0.0
