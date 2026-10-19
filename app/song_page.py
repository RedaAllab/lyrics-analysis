import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from beatles_viz.data.loader import has_lyrics  # noqa: E402
from beatles_viz.render.components import cached_corpus, metrics_panel, song_header, song_selector  # noqa: E402
from beatles_viz.render.views import ANALYSE, READ, analyse_view, navigation, read_view  # noqa: E402

KEY = "song"
local = has_lyrics()
corpus = cached_corpus("local" if local else "public")
song, scope = song_selector(corpus, key=KEY)
if song is None:
    st.warning("No song matches the filters.")
    st.stop()

song_header(song)

# The view is kept in the URL (?view=Read) so a link opens the song in the right mode.
views = [READ, ANALYSE] if local else [ANALYSE, READ]
wanted = st.query_params.get("view")
if f"{KEY}_view" not in st.session_state:
    st.session_state[f"{KEY}_view"] = wanted if wanted in views else views[0]
view = st.radio("View", views, key=f"{KEY}_view", horizontal=True, label_visibility="collapsed")
st.query_params["view"] = view

navigation(song, scope, KEY)
with st.expander("Metrics", expanded=view == ANALYSE):
    metrics_panel(song, corpus)

if view == READ:
    read_view(song, corpus, local, KEY)
else:
    analyse_view(song, corpus, local, KEY)
