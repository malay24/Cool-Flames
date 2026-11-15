"""Investigation dossiers (ai/dossier.py): facts copied from data/raw/, similar studies."""
import json

import pytest

from ai import dossier as d
from core.loaders import ROOT

INVS = json.loads((ROOT / "data" / "ai" / "investigations.json").read_text())


@pytest.mark.parametrize("column, category", [
    ("Test #", "log"), ("GMT", "log"), ("Notes", "log"),
    ("Burn Time (s)", "measured"), ("Visible flame extinction diameter; mm", "measured"),
    ("Calibrated final O2 % by vol", "measured"), ("Camera 1", "measured"),
    ("Sample Thickness (cm)", "sample"), ("Samle Thickness ", "sample"), ("Material", "sample"),
    ("Droplet initial diameter; mm", "sample"), ("Fuel", "sample"),
    ("Percent O2 (Note 1)", "condition"), ("Fuel Rate (mg/s)", "condition"),
    ("Ambient pressure; mmHg", "condition"), ("Air Flow (cm/s)", "condition"),
])
def test_classify_column(column, category):
    assert d.classify_column(column) == category


def test_display_name_restores_lost_mu():
    assert d.display_name("?-g Spread Length") == "μg Spread Length"
    assert d.display_name("  Sample   Width (cm) ") == "Sample Width (cm)"


def test_table_files_do_not_mix_prefixes():
    assert all(p.name.startswith("PSI-10_") for p in d.table_files("PSI-10"))
    assert len(d.table_files("PSI-10")) == 2


def test_table_profile_saffire_ii():
    prof = {p["column"]: p for p in d.table_profile("PSI-99")}
    assert prof["Material"]["category"] == "sample" and prof["Material"]["varied"]
    assert prof["Ignition Power (W)"]["category"] == "condition"
    assert prof["μg Spread Length"]["category"] == "measured"


def test_people_and_sections_copied_from_record():
    rec = d.load_record("PSI-99")
    assert d.people(rec) == ["David L. Urban (NASA GRC)"]
    labels = [label for label, _ in d.record_sections(rec)]
    assert labels[0] == "Objective" and "Approach" in labels


@pytest.mark.parametrize("psi_id", [i["psi_id"] for i in INVS])
def test_instrument_quotes_are_verbatim(psi_id):
    rec = d.load_record(psi_id)
    prof = d.table_profile(psi_id)
    text = " ".join(d.clean(rec.get(k)) for k in
                    ("objective", "hypothesis", "approach", "researchImpacts", "experimentHardware"))
    columns = {p["column"] for p in prof}
    for hit in d.instruments(rec, prof):
        if hit["where"] == "Table column":
            assert hit["quote"] in columns
        else:
            for part in hit["quote"].strip("…").split("…"):
                assert part.strip() in text, (psi_id, hit)


def test_similar_studies_find_the_same_family():
    vec = d.investigation_vectors()
    assert len(vec) == len(INVS)
    top = {i["psi_id"]: d.similar_studies(i["psi_id"], INVS, vec, k=2) for i in INVS}
    assert "PSI-98" in {s["psi_id"] for s in top["PSI-99"]}     # Saffire-II -> Saffire-I
    assert top["PSI-101"][0]["psi_id"] == "PSI-102"              # SAME-R -> SAME
    assert top["PSI-25"][0]["psi_id"] == "PSI-26"                # BASS-II -> BASS
    for pid, sims in top.items():
        assert pid not in {s["psi_id"] for s in sims}
        assert all(0.0 <= s["score"] <= 1.0 for s in sims)


def test_unknown_investigation_is_empty_not_an_error():
    assert d.load_record("PSI-900") == {}
    assert d.table_profile("PSI-900") == []
    assert d.similar_studies("PSI-900", INVS, {}) == []


def test_profile_skips_footnote_rows_like_the_pipeline():
    prof = {p["column"]: p for p in d.table_profile("PSI-99")}
    assert not any("Pre-test flow" in e for e in prof["Material"]["examples"])
    assert prof["Material"]["n_values"] == 4  # Silicone, SIBAL, PMMA & Nomex, PMMA (2 cells blank)
