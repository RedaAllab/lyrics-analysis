# Synthetic tables only; the page test reads analysis/artists/ (numbers and single words, no lyrics).
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from beatles_viz.viz import artist_charts as ac

APP = Path(__file__).resolve().parent.parent / "app"


@pytest.fixture
def songs():
    rows = [(a, f"{a} song {i}", 1962 + i, 0.6 + 0.01 * i + j * 0.05, 150 + 10 * i, 0.1 * j)
            for j, a in enumerate(ac.ARTISTS) for i in range(5)]
    d = pd.DataFrame(rows, columns=["artist", "title", "year", "mattr", "tokens", "valence"])
    for m in ac.MEASURES:
        if m not in d:
            d[m] = 0.2
    return d


def test_medians_keep_artist_order(songs):
    med = ac.medians(songs.iloc[::-1])
    assert med.index.tolist() == ac.ARTISTS
    assert med.loc["Bob Dylan", "mattr"] == pytest.approx(0.72)


def test_profile_box_has_one_trace_per_artist(songs):
    fig = ac.profile_box(songs, "mattr")
    assert {t.name for t in fig.data} == set(ac.ARTISTS)


def test_distinctive_bars_sorted_by_z():
    words = pd.DataFrame({"artist": ["Bob Dylan"] * 3 + ["The Beatles"], "word": ["kettle", "lamp", "door", "rain"],
                          "z": [3.0, 9.0, 5.0, 7.0], "songs": [5, 6, 7, 8]})
    fig = ac.distinctive_bars(words, "Bob Dylan")
    assert list(fig.data[0].y) == ["lamp", "door", "kettle"]


def test_career_lines_hollow_for_thin_years():
    years = pd.DataFrame({"artist": ["The Beatles"] * 2, "career_year": [2, 1], "songs": [3, 12],
                          "mattr": [0.6, 0.7], "tokens": [1, 2], "repetition_score": [0, 0], "valence": [0, 0]})
    (line,) = ac.career_lines(years, "mattr").data
    assert list(line.x) == [1, 2] and list(line.marker.color) == [ac.ARTIST_COLORS["The Beatles"], "white"]


def test_p_value_either_order():
    tests = pd.DataFrame({"metric": ["mattr"], "a": ["The Beatles"], "b": ["Bob Dylan"], "p_value": [0.003]})
    assert ac.p_value(tests, "mattr", "Bob Dylan", "The Beatles") == 0.003


def test_artists_page_runs():
    at = AppTest.from_file(str(APP / "artists_page.py"), default_timeout=120).run()
    assert not at.exception and len(at.get("plotly_chart")) == 5
