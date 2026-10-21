# Synthetic lines only.
from collections import Counter

from beatles_viz.text.narrative import is_past, line_markers, word_markers


def test_word_markers_are_shares_of_words():
    m = word_markers(Counter({"she": 2, "was": 1, "walked": 1, "tomorrow": 1, "table": 5}))
    assert m["third_person"] == 0.2 and m["past"] == 0.2 and m["future"] == 0.1


def test_regular_past_skips_look_alikes():
    assert is_past("walked") and is_past("said")
    assert not is_past("need") and not is_past("bed") and not is_past("red")


def test_full_names_count_as_one_character():
    assert word_markers(Counter({"eleanor": 1, "rigby": 1, "mckenzie": 1}))["characters"] == 1
    assert word_markers(Counter({"jude": 1, "julia": 2}))["characters"] == 2


def test_line_markers():
    m = line_markers(["where do you go?", "come back to me", "the kettle hums", "please stay", ""])
    assert m["questions"] == 0.25 and m["orders"] == 0.5
    empty = line_markers([])
    assert empty["questions"] != empty["questions"]
