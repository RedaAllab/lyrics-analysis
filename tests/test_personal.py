from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from beatles_viz import personal
from beatles_viz.data.loader import has_lyrics
from beatles_viz.listen import listen_links

APP = Path(__file__).resolve().parent.parent / "app"


@pytest.fixture
def journal(tmp_path, monkeypatch):
    path = tmp_path / "journal.json"
    monkeypatch.setenv(personal.ENV_PATH, str(path))  # never touch the real journal, even after a module reload
    return path


def test_update_and_listen_round_trip(journal):
    personal.update("Something", favourite=True, rating=5)
    personal.log_listen("Something", day=date(2026, 10, 1))
    personal.log_listen("Something", day=date(2026, 10, 20))
    e = personal.entry(personal.load(), "Something")
    assert e["favourite"] and e["rating"] == 5 and e["listens"] == ["2026-10-01", "2026-10-20"]
    personal.undo_listen("Something")
    assert personal.entry(personal.load(), "Something")["listens"] == ["2026-10-01"]


def test_journal_frame_and_months(journal):
    personal.update("A", note="first dance")
    personal.log_listen("B", day=date(2026, 9, 3))
    personal.log_listen("B", day=date(2026, 10, 3))
    corpus = pd.DataFrame({"title": ["A", "B"], "year": [1964, 1969], "voice": ["Lennon", "Harrison"]})
    t = personal.journal_frame(personal.load(), corpus).set_index("title")
    assert t.loc["B", "listens"] == 2 and t.loc["B", "last_listen"] == "2026-10-03" and t.loc["A", "year"] == 1964
    assert personal.listens_by_month(personal.load()).listens.tolist() == [1, 1]


def test_empty_journal(journal):
    assert personal.load() == {} and personal.journal_frame({}).empty


def test_listen_links_are_searches():
    links = listen_links("Here Comes the Sun")
    assert set(links) == {"Spotify", "Apple Music", "YouTube Music", "Deezer"}
    assert all("Beatles" in url and "Sun" in url for url in links.values())


@pytest.mark.skipif(not has_lyrics(), reason="local lyrics file not available")
def test_song_page_listen_button_writes_the_journal(journal):
    at = AppTest.from_file(str(APP / "song_page.py"), default_timeout=180)
    at.session_state["goto_song"] = "Something"
    at.run()
    [listen] = [b for b in at.button if b.label == "I listened"]
    listen.click().run()
    assert not at.exception and len(personal.entry(personal.load(), "Something")["listens"]) == 1
    journal_page = AppTest.from_file(str(APP / "journal_page.py"), default_timeout=180).run()
    assert not journal_page.exception and journal_page.metric[2].value == "1"
