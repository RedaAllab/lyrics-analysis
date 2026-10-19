"""Entry point: streamlit run app/beatles_app.py"""
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from beatles_viz.render.identity import apply_identity  # noqa: E402

st.set_page_config(page_title="Beatles lyrics explorer", page_icon=str(HERE / "static/icon.svg"), layout="wide")
apply_identity(HERE / "static/logo.svg", HERE / "static/icon.svg")
st.navigation([
    st.Page(HERE / "home_page.py", title="Home", icon=":material/home:", url_path="home", default=True),
    st.Page(HERE / "song_page.py", title="Song", icon=":material/lyrics:", url_path="song"),
    st.Page(HERE / "compare_page.py", title="Compare", icon=":material/compare_arrows:", url_path="compare"),
    st.Page(HERE / "corpus_page.py", title="Corpus", icon=":material/bar_chart:", url_path="corpus"),
]).run()
