import streamlit as st

from beatles_viz.corpus import analysable
from beatles_viz.data.loader import has_lyrics
from beatles_viz.render.components import cached_corpus, metrics_panel, similar_picker, song_header, song_selector
from beatles_viz.render.listen_view import listen_block
from beatles_viz.render.share_card import share_block
from beatles_viz.render.personal_view import personal_strip
from beatles_viz.text.similarity import similarity_matrix
from beatles_viz.render.views import ANALYSE, READ, analyse_view, navigation, read_view

KEY = "song"
local = has_lyrics()
corpus = cached_corpus("local" if local else "public")
song, scope = song_selector(corpus, key=KEY)
if song is None:
    st.warning("No song matches the filters.")
    st.stop()

song_header(song)
listen_block(song)
share_block(song, analysable(corpus))
personal_strip(song)

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


@st.cache_data(show_spinner=False)
def _similarity(source):
    return similarity_matrix(corpus)


similar_picker(song, corpus, _similarity("local" if local else "public"), KEY)

if view == READ:
    read_view(song, corpus, local, KEY)
else:
    analyse_view(song, corpus, local, KEY)
