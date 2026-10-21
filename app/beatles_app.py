"""Entry point: streamlit run app/beatles_app.py"""
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:  # Streamlit Cloud does not install the package; locally `pip install -e .` does
    sys.path.insert(0, str(ROOT))


def fresh_package():
    """Streamlit keeps imported modules for the life of the server, and a push to Streamlit Cloud does not restart
    it: a new visitor would run the old beatles_viz. Reload the package, and drop data cached by the old code,
    when one of its files is newer than the loaded copy."""
    stamp = max(p.stat().st_mtime for p in (ROOT / "beatles_viz").rglob("*.py"))
    loaded = sys.modules.get("beatles_viz")
    if loaded is not None and getattr(loaded, "loaded_at", 0) >= stamp:
        return
    if loaded is not None:
        for name in [m for m in sys.modules if m == "beatles_viz" or m.startswith("beatles_viz.")]:
            del sys.modules[name]
        st.cache_data.clear()
    import beatles_viz
    beatles_viz.loaded_at = stamp


fresh_package()
from beatles_viz import personal  # noqa: E402
from beatles_viz.render.identity import apply_identity  # noqa: E402

st.set_page_config(page_title="Beatles lyrics explorer", page_icon=str(HERE / "static/icon.svg"), layout="wide")
apply_identity(HERE / "static/logo.svg", HERE / "static/icon.svg")
st.sidebar.caption("Unofficial fan project, not affiliated with The Beatles, Apple Corps or their record labels.")
st.navigation({
    "Explore": [
        st.Page(HERE / "home_page.py", title="Home", icon=":material/home:", url_path="home", default=True),
        st.Page(HERE / "song_page.py", title="Song", icon=":material/lyrics:", url_path="song"),
        st.Page(HERE / "album_page.py", title="Albums", icon=":material/album:", url_path="albums"),
        st.Page(HERE / "stories_page.py", title="Stories", icon=":material/auto_stories:", url_path="stories"),
        st.Page(HERE / "trends_page.py", title="Trends", icon=":material/trending_up:", url_path="trends"),
        *([st.Page(HERE / "journal_page.py", title="My songs", icon=":material/favorite:", url_path="mine"),
           st.Page(HERE / "annotate_page.py", title="Annotate", icon=":material/label:", url_path="annotate")]
          if personal.enabled() else []),
    ],
    "Go further": [
        st.Page(HERE / "word_page.py", title="Word", icon=":material/text_fields:", url_path="word"),
        st.Page(HERE / "compare_page.py", title="Compare", icon=":material/compare_arrows:", url_path="compare"),
        st.Page(HERE / "artists_page.py", title="Other artists", icon=":material/groups:", url_path="artists"),
        st.Page(HERE / "mood_page.py", title="Mood", icon=":material/sentiment_satisfied:", url_path="mood"),
        st.Page(HERE / "guess_page.py", title="Who sings?", icon=":material/quiz:", url_path="guess"),
        st.Page(HERE / "voice_page.py", title="Voices", icon=":material/record_voice_over:", url_path="voices"),
        st.Page(HERE / "credits_page.py", title="Credits", icon=":material/badge:", url_path="credits"),
        st.Page(HERE / "corpus_page.py", title="Corpus", icon=":material/bar_chart:", url_path="corpus"),
    ],
}, expanded=True).run()
