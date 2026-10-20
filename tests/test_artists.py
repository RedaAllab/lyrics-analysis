# Synthetic titles, pages and lyrics only.
from collections import Counter

import pytest

from scripts.artist_helpers import (career_stage, chorus_share, distinctive, match_title, norm, pick_versions,
                                    proper_nouns, slug, wiki_tables)

OFFICIAL = {norm("Paper Kettle"): {"title": "Paper Kettle"}, norm("Slow Lamp (Morning Mix)"): {"title": "Slow Lamp (Morning Mix)"},
            norm("Slow Lamp (Morning Mix)", False): {"title": "Slow Lamp (Morning Mix)"}}


def test_slug():
    assert slug("The Rolling Stones") == "rolling_stones"
    assert slug("Bob Dylan") == "bob_dylan"


def test_norm_ignores_punctuation_and_number_commas():
    assert norm("Don't Stop, Kettle!") == norm("Dont Stop Kettle")
    assert norm("10,000 Kettles") == norm("10000 Kettles")


@pytest.mark.parametrize("title, expected", [
    ("Paper Kettle", ("paper kettle", False)),
    ("Paper Kettle Live 1975", ("paper kettle", True)),
    ("Paper Kettle (Demo)", ("paper kettle", True)),
    ("Paper Kettle (For Lamp)", ("paper kettle", False)),
    ("Paper Kettle Take 2", ("paper kettle", True)),
    ("Paper Kettle Blues", (None, False)),  # another song, not a version
    ("Slow Lamp", ("slow lamp", False)),
])
def test_match_title(title, expected):
    assert match_title(title, OFFICIAL) == expected


def test_pick_versions_prefers_studio_then_longest():
    words = lambda n: " ".join(["kettle"] * n)
    rows = [{"title": "Paper Kettle Live 1975", "lyrics": words(300)},
            {"title": "Paper Kettle", "lyrics": words(40)},
            {"title": "Paper Kettle", "lyrics": words(10)},  # too short
            {"title": "Slow Lamp Demo", "lyrics": words(25)},
            {"title": "Slow Lamp Demo 2", "lyrics": words(50)},
            {"title": "Unknown Song", "lyrics": words(80)}]
    best = {r["official"]: r for r in pick_versions(rows, OFFICIAL)}
    assert set(best) == {"Paper Kettle", "Slow Lamp (Morning Mix)"}
    assert best["Paper Kettle"]["n_words"] == 40 and not best["Paper Kettle"]["is_version"]
    assert best["Slow Lamp (Morning Mix)"]["n_words"] == 50 and best["Slow Lamp (Morning Mix)"]["is_version"]


def test_wiki_tables_expands_spans_and_skips_other_tables():
    html = """<table class="navbox"><tr><td>menu</td></tr></table>
    <table class="wikitable sortable"><tr><th>Title</th><th>Year released</th><th>Album</th></tr>
    <tr><th>"Paper Kettle"<sup>[1]</sup></th><td rowspan="2">1964</td><td>First<br>Second</td></tr>
    <tr><th>"Slow Lamp"</th><td colspan="1">Third</td></tr></table>"""
    (table,) = wiki_tables(html)
    assert table[0] == ["Title", "Year released", "Album"]
    assert table[1] == ['"Paper Kettle"', "1964", "First; Second"]
    assert table[2] == ['"Slow Lamp"', "1964", "Third"]


def test_proper_nouns_are_capitalised_mid_line():
    lyrics = ["I walked to Tallow town\nwe sang in Tallow again\nthe Kettle went to Tallow", "Kettle songs\nthe kettle hums"]
    names = proper_nouns(lyrics, min_count=2)
    assert "tallow" in names and "kettle" not in names and "i" not in names


@pytest.mark.parametrize("year, stage", [(1962, "years 1-3"), (1966, "years 4-6"), (1970, "years 7-9"),
                                         (1971, None), (1961, None)])
def test_career_stage(year, stage):
    assert career_stage(year, 1962) == stage


def test_chorus_share():
    assert chorus_share(["verse", "chorus", "verse", "chorus"], [30, 20, 30, 20]) == pytest.approx(0.4)
    assert chorus_share([], []) != chorus_share([], [])  # nan


def test_distinctive_needs_several_songs():
    mine = Counter({"kettle": 60, "lamp": 40, "door": 30})
    others = Counter({"kettle": 5, "lamp": 5, "door": 30})
    docs = Counter({"kettle": 9, "lamp": 1, "door": 9})
    words = distinctive(mine, docs, others).word.tolist()
    assert words[0] == "kettle" and "lamp" not in words


ALBUM = """{{Infobox album
| name = Paper Kettle
| released = {{Start date|1971|3|2}}<ref>{{cite web|date=1999}}</ref>
}}
==Track listing==
{{Track listing
| headline = Side one
| all_writing = [[Ann Writer]]
| title1 = [[Morning Lamp (song)|Morning Lamp]]
| length1 = 3:00
| title2 = Slow Kettle{{efn|a note}}
| writer2 = Ann Writer, [[Bo Helper]]
}}
{{Track listing
| headline = 2007 reissue bonus tracks
| title3 = Outtake Song
}}
"""

NUMBERED = """==Track listing==
All tracks written by Ann Writer.
;Side one
# "[[Morning Lamp (song)|Morning Lamp]]" – 3:00
# "Old Door" (Cy Other) – 2:10
;Bonus tracks
# "Spare Song" – 1:00

==Personnel==
# "Not a track" – 9:99
"""


def test_album_template_tracks_and_year():
    from scripts.artist_helpers import album_tracks, infobox_year
    assert infobox_year(ALBUM) == 1971
    assert album_tracks(ALBUM) == [("Morning Lamp", "Ann Writer"), ("Slow Kettle", "Ann Writer, Bo Helper")]


def test_album_numbered_tracks_stop_at_bonus_and_next_section():
    from scripts.artist_helpers import album_tracks
    assert album_tracks(NUMBERED) == [("Morning Lamp", ""), ("Old Door", "Cy Other")]


def test_song_list_html_reads_back_as_a_wikitable():
    from scripts.artist_helpers import song_list_html
    html = song_list_html([{"title": "Kettle & Lamp", "year": 1971, "release": "Paper", "writers": "Ann Writer"}])
    (table,) = wiki_tables(html)
    assert table == [["Title", "Year released", "Original release", "Songwriter(s)"],
                     ['"Kettle & Lamp"', "1971", "Paper", "Ann Writer"]]


def test_official_songs_prefer_exact_titles_and_year_released():
    import re
    from scripts.build_artist import official_songs
    html = """<table class="wikitable"><tr><th>Song</th><th>Year recorded</th><th>Year released</th><th>Writer(s)</th></tr>
    <tr><td>"Paper Kettle (Reprise)"</td><td>1980</td><td>1984</td><td>Ann Writer</td></tr>
    <tr><td>"Paper Kettle"</td><td>1975</td><td>1976</td><td>Ann Writer</td></tr></table>"""
    official = official_songs(html, "Ann Writer")
    assert official["paper kettle"]["title"] == "Paper Kettle" and official["paper kettle"]["year"] == 1976
    assert official["paper kettle reprise"]["year"] == 1984
