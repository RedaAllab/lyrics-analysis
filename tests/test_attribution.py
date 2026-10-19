from beatles_viz.attribution import lead_voice, resolve_voice
from beatles_viz.text.sections import Section


def section(singers):
    return Section("verse", "Verse 1", 1, frozenset(singers), ["x"], 1)


def test_lead_voice():
    assert lead_voice("Lennon") == "Lennon"
    assert lead_voice("Lennon; (with McCartney)") == "Lennon"
    assert lead_voice("Lennon; and McCartney") == "Shared"
    assert lead_voice("–") == "Neutral"
    assert lead_voice("Tony Sheridan") == "Neutral"


def test_section_tag_wins_over_song_lead():
    assert resolve_voice(section({"Harrison"}), "Lennon") == "Harrison"
    assert resolve_voice(section({"Lennon", "McCartney"}), "Lennon") == "Shared"


def test_falls_back_to_song_lead_then_neutral():
    assert resolve_voice(section(()), "McCartney") == "McCartney"
    assert resolve_voice(section(()), "Sound Collage") == "Neutral"
