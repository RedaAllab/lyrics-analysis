import html
import re

import pytest

from beatles_viz.config import VOICE_COLORS
from beatles_viz.effects import REGISTRY, get_effect
from beatles_viz.text.sections import Section

EFFECTS = sorted(REGISTRY)
LINE = "the kettle hums <loud> & the cat's asleep"
SECTION = Section("chorus", "Chorus", None, frozenset({"Lennon", "McCartney"}), [LINE], 1)
FREQ = {"the": 200, "hums": 40, "loud": 30, "cat's": 20, "asleep": 15, "kettle": 1}
CTX = {"members": frozenset({"Lennon", "McCartney"}), "doc_freq": FREQ, "line_in_section": 2}


def luminance(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def text_of(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def test_expected_effects_registered():
    assert set(EFFECTS) == {"lennon", "mccartney", "harrison", "starr", "shared", "neutral"}
    assert get_effect("Lennon").name == "lennon" and get_effect("someone else").name == "neutral"


@pytest.mark.parametrize("name", EFFECTS)
def test_css_rules_are_prefixed(name):
    effect = REGISTRY[name]
    css = effect.css(effect.params())
    assert css.strip()
    for selector in re.findall(r"(?:^|})\s*([^{}]+)\{", css):
        selector = selector.strip()
        if selector in ("from", "to") or re.fullmatch(r"[\d%,\s]+", selector):
            continue
        prefix = f"fx-{name}" if selector.startswith("@keyframes") else f".fx-{name}"
        assert prefix in selector, selector


@pytest.mark.parametrize("name", EFFECTS)
def test_text_is_never_changed_and_is_escaped(name):
    effect = REGISTRY[name]
    out = effect.wrap_line(LINE, effect.params(), CTX)
    assert "<loud>" not in out
    assert text_of(out) == LINE
    section = effect.wrap_section(out, SECTION, effect.params(), CTX)
    assert text_of(section) == LINE and f"fx-{name}" in section


@pytest.mark.parametrize("name", EFFECTS)
def test_text_colours_meet_wcag_aa(name):
    effect = REGISTRY[name]
    for key in effect.text_keys:
        assert contrast(effect.defaults[key], effect.defaults["bg"]) >= 4.5, key


@pytest.mark.parametrize("name", EFFECTS)
def test_numeric_params_have_ranges(name):
    effect = REGISTRY[name]
    for key, value in effect.defaults.items():
        if isinstance(value, (int, float)):
            lo, hi, _ = effect.ranges[key]
            assert lo <= value <= hi


def test_lennon_marks_rare_words_only():
    out = get_effect("Lennon").wrap_line(LINE, get_effect("Lennon").params(), CTX)
    assert re.findall(r'class="fx-rare">([^<]+)<', out) == ["kettle"]


def test_shared_border_uses_member_colours():
    effect = get_effect("Shared")
    style = effect.section_style(SECTION, effect.params(), CTX)
    assert VOICE_COLORS["Lennon"] in style and VOICE_COLORS["McCartney"] in style
