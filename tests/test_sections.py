# Synthetic lyrics only: real lyrics never go into the test suite.
from beatles_viz.text.sections import all_lines, normalize_label, parse_members, split_sections

SONG = """[Intro]
tin cans on a wire

[Verse 1: Paul McCartney]
the kettle hums at seven
the cat ignores the rain

[Chorus: John Lennon & Paul McCartney]
round and round the table
round and round again
[x2]

[Instrumental Bridge]

[Verse 2: George Harrison and George Martin]
a lamp left on in the hallway [?]
"""


def test_labels_are_normalized():
    assert normalize_label("Verse 3") == ("verse", 3)
    assert normalize_label("Guitar solo") == ("instrumental", None)
    assert normalize_label("Instrumental Bridge")[0] == "instrumental"
    assert normalize_label("Chours 1") == ("chorus", 1)
    assert normalize_label("Refrain")[0] == "chorus"
    assert normalize_label("Pre-Chorus 2") == ("pre_chorus", 2)
    assert normalize_label("​​Interlude")[0] == "instrumental"
    assert normalize_label("Spoken")[0] == "other"


def test_members_are_parsed():
    assert parse_members("Paul McCartney & John Lennon") == {"McCartney", "Lennon"}
    assert parse_members("George Harrison and George Martin") == {"Harrison"}
    assert parse_members("Paul McCartney (& John Lennon and George Harrison)") == {"McCartney"}
    assert parse_members("Ringo Starr & Lennon/McCartney/Harrison") == {"Starr", "Lennon", "McCartney", "Harrison"}
    assert parse_members("Billy Preston") == frozenset()
    assert parse_members("") == frozenset()


def test_split_sections():
    sections = split_sections(SONG)
    assert [s.kind for s in sections] == ["intro", "verse", "chorus", "instrumental", "verse"]
    assert sections[1].singers == {"McCartney"} and sections[1].number == 1
    assert sections[2].repeat == 2
    assert sections[3].lines == []
    assert sections[4].lines == ["a lamp left on in the hallway"]


def test_untagged_song_is_one_section():
    sections = split_sections("one line\nanother line")
    assert len(sections) == 1 and sections[0].kind == "song"


def test_unclosed_tag_does_not_swallow_lines():
    sections = split_sections("[Chorus\nfirst line\nsecond line\n[Verse]\nthird line")
    assert all_lines(sections) == ["first line", "second line", "third line"]


def test_tag_and_repeat_on_one_line():
    sections = split_sections("[Chorus] [x3]\nla la line")
    assert sections[0].kind == "chorus" and sections[0].repeat == 3 and sections[0].lines == ["la la line"]
