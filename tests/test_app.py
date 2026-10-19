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


@pytest.mark.parametrize("entry", ["beatles_app.py", "corpus_page.py"])
def test_corpus_runs(entry):
    assert not AppTest.from_file(str(APP / entry), default_timeout=180).run().exception


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
