# Synthetic lyrics only.
from beatles_viz.corpus import structure_of
from beatles_viz.text.sections import all_lines, split_sections
from beatles_viz.text.segment import AUTO, detect_sections, is_detected, song_sections

VERSE_A = "a lamp burns in the hallway\nthe kettle hums at seven"
VERSE_B = "the paper lies unread\na clock ticks by the door"
CHORUS = "round and round the table\nround and round again"
STANZAS = "\n\n".join([VERSE_A, CHORUS, VERSE_B, CHORUS])


def test_returning_stanza_is_a_chorus():
    kinds = [s.kind for s in detect_sections(STANZAS)]
    assert kinds == ["verse", "chorus", "verse", "chorus"]


def test_verses_are_numbered_and_marked_as_detected():
    sections = detect_sections(STANZAS)
    assert [s.number for s in sections if s.kind == "verse"] == [1, 2]
    assert all(s.label == AUTO for s in sections) and is_detected(sections)


def test_detection_keeps_every_line():
    assert all_lines(song_sections(STANZAS)) == all_lines(split_sections(STANZAS))


def test_strophic_song_has_no_chorus():
    strophic = "\n\n".join(["the river runs to the sea\nthe river runs away"] * 1 +
                           ["the river runs to the hills\nthe river runs today"])
    assert detect_sections(strophic) is None


def test_text_without_blank_lines_uses_repeated_runs():
    text = "\n".join([VERSE_A, CHORUS, VERSE_B, CHORUS])
    kinds = [s.kind for s in detect_sections(text)]
    assert kinds == ["verse", "chorus", "verse", "chorus"]


def test_tagged_lyrics_are_left_alone():
    tagged = "[Verse 1]\n" + VERSE_A + "\n[Chorus]\n" + CHORUS
    assert not is_detected(song_sections(tagged))


def test_structure_has_no_words():
    shape = structure_of(detect_sections(STANZAS))
    assert shape["sec_kinds"][1] == "chorus" and shape["sec_words"][0] == 11
    assert "lamp" not in str(shape)
