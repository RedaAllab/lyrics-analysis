"""Entry point: streamlit run app/beatles_app.py"""
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

st.set_page_config(page_title="Beatles lyrics explorer", page_icon=":material/music_note:", layout="wide")
st.navigation([
    st.Page(HERE / "corpus_page.py", title="Corpus", icon=":material/bar_chart:", url_path="corpus", default=True),
    st.Page(HERE / "song_page.py", title="Song", icon=":material/lyrics:", url_path="song"),
]).run()
