"""The Streamlit theme (.streamlit/config.toml) and the Python palette (config.py, viz.theme) are one design,
written twice: they must not drift apart."""
import tomllib

import pytest

from beatles_viz import config
from beatles_viz.config import ROOT, VOICE_COLORS
from beatles_viz.viz import theme

CONFIG = tomllib.loads((ROOT / ".streamlit/config.toml").read_text())
THEME = CONFIG["theme"]
SIDEBAR = THEME["sidebar"]


@pytest.mark.parametrize("key, expected", [
    ("primaryColor", config.INK), ("textColor", config.INK), ("backgroundColor", config.PAPER),
    ("secondaryBackgroundColor", config.CARD), ("dataframeBorderColor", config.RULE),
    ("codeBackgroundColor", config.SOFT), ("grayColor", config.MUTED),
    ("blueColor", VOICE_COLORS["Lennon"]), ("redColor", VOICE_COLORS["McCartney"]),
    ("yellowColor", VOICE_COLORS["Harrison"]), ("greenColor", VOICE_COLORS["Starr"]),
    ("violetColor", VOICE_COLORS["Shared"]), ("orangeColor", config.ACCENT),
])
def test_theme_colours_come_from_the_palette(key, expected):
    assert THEME[key].lower() == expected.lower()


def test_sidebar_uses_card_and_paper():
    assert SIDEBAR["backgroundColor"].lower() == config.CARD.lower()
    assert SIDEBAR["secondaryBackgroundColor"].lower() == config.PAPER.lower()


def test_native_charts_and_plotly_share_the_colour_order():
    assert [c.lower() for c in THEME["chartCategoricalColors"]] == [c.lower() for c in theme.COLORWAY]


def test_native_sequential_scale_is_the_plotly_one():
    stops = [stop for _, stop in theme.SEQUENTIAL]
    assert THEME["chartSequentialColors"][0].lower() == stops[0].lower()
    assert THEME["chartSequentialColors"][-1].lower() == stops[-1].lower()


def test_every_declared_font_file_exists_and_is_named_in_the_theme():
    families = {f["family"] for f in THEME["fontFaces"]}
    for face in THEME["fontFaces"]:
        assert (ROOT / face["url"]).is_file(), face["url"]
    assert {THEME["font"].split(",")[0], THEME["headingFont"].split(",")[0], THEME["codeFont"].split(",")[0]} <= families
    assert theme.BODY_FONT.startswith(f"'{THEME['font'].split(',')[0]}'")
    assert theme.TITLE_FONT.startswith(f"'{THEME['headingFont'].split(',')[0]}'")
    assert theme.MONO_FONT.startswith(f"'{THEME['codeFont'].split(',')[0]}'")


def test_static_serving_is_on_for_the_self_hosted_fonts():
    assert CONFIG["server"]["enableStaticServing"] is True
