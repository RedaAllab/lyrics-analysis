import os
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from beatles_viz.data.loader import has_lyrics

APP = Path(__file__).resolve().parent.parent / "app"
needs_lyrics = pytest.mark.skipif(not has_lyrics(), reason="local lyrics file not available")


@pytest.mark.parametrize("page", ["beatles_app.py", "pages/1_Song.py"])
def test_public_pages_run(page):
    at = AppTest.from_file(str(APP / page), default_timeout=180).run()
    assert not at.exception


@needs_lyrics
def test_read_page_renders_song_and_navigates():
    at = AppTest.from_file(str(APP / "pages/2_Read.py"), default_timeout=180).run()
    assert not at.exception and len(at.get("html")) == 1
    first = at.session_state["read_title"]
    at.button[1].click().run()
    assert not at.exception and at.session_state["read_title"] != first


def test_read_page_hides_lyrics_without_local_file():
    # Separate process: the env switch must be set before the app imports the loader.
    code = ("from streamlit.testing.v1 import AppTest; "
            f"at = AppTest.from_file({str(APP / 'pages/2_Read.py')!r}, default_timeout=120).run(); "
            "assert not at.exception and len(at.get('html')) == 0 and at.info")
    env = {**os.environ, "BEATLES_PUBLIC_ONLY": "1"}
    assert subprocess.run([sys.executable, "-c", code], env=env, cwd=APP.parent).returncode == 0
