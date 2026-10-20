import os
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from beatles_viz.data.loader import has_lyrics

APP = Path(__file__).resolve().parent.parent / "app"
SONG_PAGE = str(APP / "song_page.py")
needs_lyrics = pytest.mark.skipif(not has_lyrics(), reason="local lyrics file not available")


@pytest.mark.parametrize("entry", ["beatles_app.py", "corpus_page.py", "compare_page.py", "stories_page.py",
                                   "album_page.py", "voice_page.py", "mood_page.py", "trends_page.py"])
def test_pages_run(entry):
    assert not AppTest.from_file(str(APP / entry), default_timeout=180).run().exception


def test_home_shows_search_and_featured_songs():
    at = AppTest.from_file(str(APP / "beatles_app.py"), default_timeout=180).run()
    assert not at.exception
    assert at.selectbox[0].placeholder.startswith("Type a title")
    assert len([b for b in at.button if b.label == "Open"]) >= 4


def test_compare_page_rejects_same_song():
    at = AppTest.from_file(str(APP / "compare_page.py"), default_timeout=180).run()
    at.selectbox(key="cmp_1").set_value(at.selectbox(key="cmp_0").value).run()
    assert not at.exception and at.info


@needs_lyrics
def test_song_page_reads_by_default_and_navigates():
    at = AppTest.from_file(SONG_PAGE, default_timeout=180).run()
    assert not at.exception and len(at.get("html")) == 1
    first = at.session_state["song_title"]
    at.button(key="song_next").click().run()
    assert not at.exception and at.session_state["song_title"] != first


@needs_lyrics
def test_song_page_analyse_view_shows_charts_without_lyrics():
    at = AppTest.from_file(SONG_PAGE, default_timeout=180)
    at.query_params["view"] = "Analyse"
    at.run()
    assert not at.exception and len(at.get("html")) == 0 and len(at.get("plotly_chart")) >= 5


def test_public_mode_has_no_lyrics():
    # Separate process: the env switch must be set before the app imports the loader.
    code = ("from streamlit.testing.v1 import AppTest; "
            f"at = AppTest.from_file({SONG_PAGE!r}, default_timeout=120); "
            "at.query_params['view'] = 'Read'; at.run(); "
            "assert not at.exception and len(at.get('html')) == 0 and at.info")
    env = {**os.environ, "BEATLES_PUBLIC_ONLY": "1"}
    assert subprocess.run([sys.executable, "-c", code], env=env, cwd=APP.parent).returncode == 0


@needs_lyrics
def test_open_song_lands_on_requested_title():
    at = AppTest.from_file(SONG_PAGE, default_timeout=180)
    at.session_state["goto_song"] = "Something"
    at.run()
    assert not at.exception and at.session_state["song_title"] == "Something"
    assert "goto_song" not in at.session_state


def test_word_page_runs_and_follows_url():
    at = AppTest.from_file(str(APP / "word_page.py"), default_timeout=180)
    at.query_params["w"] = "love"
    at.run()
    assert not at.exception and at.session_state["word_pick"] == "love"


def test_stories_step_through_and_stop_at_the_end():
    at = AppTest.from_file(str(APP / "stories_page.py"), default_timeout=180).run()
    assert not at.exception and at.button(key="story_prev").disabled
    for _ in range(4):
        at.button(key="story_next").click().run()
    assert not at.exception and at.query_params["story"] == "5"
    assert not [b for b in at.button if b.key == "story_next"]


def test_album_page_follows_url():
    at = AppTest.from_file(str(APP / "album_page.py"), default_timeout=180)
    at.query_params["album"] = "Revolver"
    at.run()
    assert not at.exception and at.selectbox(key="album_pick").value == "Revolver"


def test_voice_page_single_voice():
    at = AppTest.from_file(str(APP / "voice_page.py"), default_timeout=180).run()
    at.selectbox(key="voice_b").set_value("Lennon").run()
    assert not at.exception


def test_voice_pills_filter_the_corpus_and_persist():
    at = AppTest.from_file(str(APP / "corpus_page.py"), default_timeout=180).run()
    pills = at.button_group(key="w_voices")
    assert set(pills.value) == {"Lennon", "McCartney", "Harrison", "Starr", "Shared", "Neutral"}
    pills.set_value(["Harrison"]).run()
    assert not at.exception and at.session_state["flt_voices"] == ["Harrison"]
