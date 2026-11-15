"""Every app page loads through the router without errors (UI smoke tests)."""
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
VIEWS = ["views/home.py", "views/overview.py", "views/scenario.py", "views/gap_map.py",
         "views/compare.py", "views/ask.py", "views/earth_benefits.py", "views/flame_lab.py",
         "views/dossier.py"]


def router() -> AppTest:
    return AppTest.from_file(str(APP / "Home.py"), default_timeout=120)


@pytest.mark.parametrize("view", VIEWS)
def test_page_loads(view):
    at = router().run()
    at.switch_page(view).run()
    assert not at.exception, [e.value for e in at.exception]


def test_habitat_persists_and_demo_ranking():
    at = router().run()
    at.sidebar.selectbox[0].select("moon_brief").run()
    at.switch_page("views/scenario.py").run()
    assert at.session_state["habitat"] == "moon_brief"
    spec = json.loads(at.tabs[0].get("plotly_chart")[0].proto.spec)
    order = spec["data"][0]["y"]  # rank order, "1. SAME-R", "2. SAME", ...
    assert order[0] == "1. SAME-R" and order[1] == "2. SAME"
    warnings = " ".join(e.value for e in at.tabs[0].error) + " ".join(w.value for w in at.tabs[0].warning)
    assert "Detector blind spot" in warnings and "No data yet" in warnings


def test_dossier_deep_link_and_card_links():
    at = router().run()
    at.query_params["id"] = "PSI-69"
    at.switch_page("views/dossier.py").run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.selectbox(key="dossier_pick").value == "PSI-69"
    at.switch_page("views/overview.py").run()
    assert len(at.get("page_link")) >= 24  # one "Open dossier" per investigation card


def test_authors_in_sidebar_on_every_page():
    at = router().run()
    html = " ".join(h.proto.body for h in at.sidebar.get("html"))
    assert html.index("Ramneek Kaur") < html.index("Malay Sourav")
