# Synthetic lyrics only.
import re
from types import SimpleNamespace

import pandas as pd

from beatles_viz.corpus import neighbors
from beatles_viz.render.song_view import render_song
from beatles_viz.text.sections import split_sections

RAW = """[Verse 1: George Harrison]
a quiet lamp <b>glows</b>
[Chorus: John Lennon & Paul McCartney]
round the table
[x2]
[Guitar Solo]
[Verse 2]
the kettle hums"""
SONG = SimpleNamespace(title="Test", lead_vocal="McCartney", sections=split_sections(RAW))


def classes(h):
    return re.findall(r'class="fx fx-(\w+)', h)


def test_one_block_per_section_with_voice_effects():
    h = render_song(SONG)
    # Untagged sections (the solo, verse 2) fall back to the song's lead vocal.
    assert classes(h) == ["harrison", "shared", "mccartney", "mccartney"]
    assert "x2" in h and "instrumental" in h
    assert "&lt;b&gt;glows&lt;/b&gt;" in h and "<b>glows" not in h


def test_effects_off_is_all_neutral():
    assert set(classes(render_song(SONG, effects_on=False))) == {"neutral"}


def test_params_override_reaches_css():
    h = render_song(SONG, params={"harrison": {"period": 9.5}})
    assert "fx-harrison-pulse 9.5s" in h


def test_neighbors():
    corpus = pd.DataFrame({"title": ["A", "B", "C"], "year": [1963, 1964, 1964], "release_core": ["X", "Y", "Y"]})
    assert neighbors(corpus, "B") == ("A", "C")
    assert neighbors(corpus, "A") == (None, "B")
    assert neighbors(corpus, "B", "album") == (None, "C")
