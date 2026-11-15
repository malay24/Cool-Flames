"""Mission-archive theme: stamp allow-list, palette, stylesheet present."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import components as c  # noqa: E402


@pytest.mark.parametrize("word", sorted(c.STAMP_WORDS) + ["FILE PSI-99", "FILE PSI-159"])
def test_allowed_stamps_render(word):
    html = c.stamp_html(word)
    assert word in html and "cf-stamp" in html


@pytest.mark.parametrize("word", ["APPROVED", "SAFE", "CLEARED", "TOP SECRET", "WILL NOT BURN",
                                  "FILE PSI-99 SAFE", "safe"])
def test_banned_or_unknown_stamps_raise(word):
    with pytest.raises(ValueError):
        c.stamp_html(word)


def test_series_palette_fixed_order_and_distinct():
    for mode in ("dark", "light"):
        colours = c.SERIES[mode]
        assert len(colours) == 4 and len(set(colours)) == 4


def test_stylesheet_exists_and_imports_first():
    css = c.CSS_FILE.read_text()
    assert css.lstrip().startswith("@import")  # @import must precede every other rule
    for hook in ("stTopNavLink", "st-key-cfcard_", ".cf-stamp", "stMetric"):
        assert hook in css


def test_authors_card_ramneek_first():
    assert c.AUTHORS == ["Ramneek Kaur", "Malay Sourav"]
    card = c.authors_card()
    assert card.index("Ramneek Kaur") < card.index("Malay Sourav")


def test_dark_look_forced_for_every_visitor():
    # light-mode browsers must get the same microfiche colours (no cream panels)
    assert c.is_dark() is True
    assert c.tokens()["bg"] == "#1c1a16" and c.series_colors() == c.SERIES["dark"]
    assert "color-scheme: dark" in c.CSS_FILE.read_text()
