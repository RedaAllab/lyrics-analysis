import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from beatles_viz.config import PHASES  # noqa: E402
from beatles_viz.data.loader import has_lyrics  # noqa: E402
from beatles_viz.render.components import cached_corpus, metrics_panel, song_header, song_selector  # noqa: E402
from beatles_viz.viz import song_charts as charts  # noqa: E402

st.set_page_config(page_title="Song - Beatles explorer", layout="wide")
local = has_lyrics()
corpus = cached_corpus("local" if local else "public")
song, scope = song_selector(corpus)
if song is None:
    st.warning("No song matches the filters.")
    st.stop()

song_header(song)
metrics_panel(song, corpus)


def show(fig, question, missing="Not enough data for this chart."):
    st.caption(question)
    if fig is None:
        st.info(missing)
    else:
        st.plotly_chart(fig, use_container_width=True)


if local:
    show(charts.structure_timeline(song.sections), "How is the song built?")
    left, right = st.columns(2)
    with left:
        show(charts.self_similarity(song.sections), "Where are the repetitions and returning motifs?")
    with right:
        show(charts.rolling_richness(song.sections), "Where is the text dense, where is it repetitive?",
             "The song is shorter than the 30-word window.")
        show(charts.voice_split(song.sections, song.lead_vocal), "Who sings what?",
             "The lyrics source names no singer per section for this song.")
else:
    st.info("Structure, repetition, density and voice charts need the local lyrics file; "
            "this deployment only has word counts.")

left, right = st.columns(2)
with left:
    show(charts.keyness(song.bow, corpus[corpus.title != song.title].bow), "Which vocabulary sets it apart?",
         "Too few words for a reliable comparison.")
with right:
    show(charts.pronoun_profile(song, corpus), "From whose point of view does the song speak?")
period = st.radio("Compare with", ["same period", "all songs"], horizontal=True)
show(charts.corpus_position(song, corpus, song.phase if period == "same period" else None),
     "Is the song typical of its time?")
