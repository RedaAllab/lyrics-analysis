import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from beatles_viz.attribution import resolve_voice  # noqa: E402
from beatles_viz.corpus import doc_frequencies, neighbors  # noqa: E402
from beatles_viz.data.loader import has_lyrics  # noqa: E402
from beatles_viz.effects import get_effect  # noqa: E402
from beatles_viz.render.components import cached_corpus, metrics_panel, song_header, song_selector  # noqa: E402
from beatles_viz.render.song_view import render_song  # noqa: E402

KEY = "read"
st.set_page_config(page_title="Read - Beatles explorer", layout="wide")
if not has_lyrics():
    st.info("Full-song reading needs the local lyrics file (data/beatles/beatles.parquet). "
            "Lyrics are copyrighted, so they are not part of the deployed app.")
    st.stop()

corpus = cached_corpus("local")
song, scope = song_selector(corpus, key=KEY)
if song is None:
    st.warning("No song matches the filters.")
    st.stop()


@st.cache_data(show_spinner=False)
def cached_doc_freq():
    return doc_frequencies(corpus)


def go_to(title):
    st.session_state[f"{KEY}_title"] = title
    st.query_params["song"] = title


# ---------- display settings ----------
st.sidebar.header("Display")
effects_on = st.sidebar.toggle("Voice effects", value=True)
font_size = st.sidebar.slider("Text size", 0.8, 1.6, 1.05, 0.05)
voices = {resolve_voice(s, song.lead_vocal) for s in song.sections}
params = {}
with st.sidebar.expander("Effect settings", expanded=False):
    for voice in sorted(voices):
        effect = get_effect(voice)
        if not (set(effect.ranges) or any(str(v).startswith("#") for v in effect.defaults.values())):
            continue
        st.markdown(f"**{voice}**")
        p = {}
        for name, value in effect.defaults.items():
            wkey = f"{KEY}_{effect.name}_{name}"
            if name in effect.ranges:
                lo, hi, step = effect.ranges[name]
                p[name] = st.slider(name, lo, hi, value, step, key=wkey)
            elif str(value).startswith("#"):
                p[name] = st.color_picker(name, value, key=wkey)
        params[effect.name] = p

# ---------- header and navigation ----------
order = st.radio("Browse", ["chronological", "album"], horizontal=True,
                 format_func=lambda o: "by year" if o == "chronological" else "within the release")
prev_title, next_title = neighbors(scope, song.title, order)
nav = st.columns([1, 1, 4])
nav[0].button("← Previous", disabled=prev_title is None, on_click=go_to, args=(prev_title,), use_container_width=True)
nav[1].button("Next →", disabled=next_title is None, on_click=go_to, args=(next_title,), use_container_width=True)
nav[2].markdown(f"[Charts for this song](Song?song={quote(song.title)})")

song_header(song)
with st.expander("Metrics"):
    metrics_panel(song, corpus)

frozen = {e: tuple(sorted(p.items())) for e, p in params.items()}


@st.cache_data(show_spinner=False, max_entries=64)
def cached_html(title, effects_on, frozen, font_size):
    row = corpus[corpus.title == title].iloc[0]
    return render_song(row, effects_on, {e: dict(p) for e, p in frozen.items()}, cached_doc_freq(), font_size)


st.html(cached_html(song.title, effects_on, frozen, font_size))
st.caption("Lyrics: Genius dataset, not proofread. Voice per section: Genius tag when present, otherwise the "
           "song's lead vocal (Wikipedia). Animations stop when the system asks for reduced motion.")
