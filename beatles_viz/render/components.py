import re

import streamlit as st

from beatles_viz.config import VOICE_COLORS

PLOT_CONFIG = {"displayModeBar": False}
HELP = {
    "mattr": "Moving-average type-token ratio: share of distinct words in every 50-word window, averaged. "
             "Higher means a more varied vocabulary, independent of song length.",
    "repeats": "Share of lines that repeat an earlier line of the same song.",
    "used_once": "Share of the vocabulary that appears only once in the selection.",
    "z": "How strongly the word is over-represented compared with the rest (log-odds z-score). "
         "Above 2 is a clear difference.",
}


def plot(fig):
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)


@st.cache_data(show_spinner="Loading songs...")
def cached_corpus(source):
    from beatles_viz.corpus import load_corpus
    return load_corpus(source)


def song_selector(corpus, key="song"):
    """Sidebar filters + title picker. Keeps the choice in the URL (?song=...) so a song can be linked."""
    originals = st.sidebar.toggle("Original compositions only", value=True, key=f"{key}_orig")
    voices = sorted(corpus.voice.unique())
    chosen_voices = st.sidebar.multiselect("Lead voice", voices, default=voices, key=f"{key}_voices")
    d = corpus[corpus.voice.isin(chosen_voices)]
    if originals:
        d = d[d.is_original]
    if d.empty:
        return None, d
    titles = d.title.tolist()
    wanted = st.query_params.get("song")
    index = titles.index(wanted) if wanted in titles else 0
    title = st.sidebar.selectbox("Song", titles, index=index, key=f"{key}_title",
                                 format_func=lambda t: f"{t} ({int(d.loc[d.title == t, 'year'].iloc[0])})")
    st.query_params["song"] = title
    return d[d.title == title].iloc[0], d


def song_header(song):
    color = VOICE_COLORS.get(song.voice, "#999999")
    st.markdown(f"## {song.title}")
    release = re.sub(r'"\s+', '"', song.release_core)  # Wikipedia export leaves '" Title' quotes
    st.markdown(f"{int(song.year)} · *{release}* · written by {song.songwriters} · "
                f"lead voice <span style='color:{color};font-weight:600'>{song.voice}</span> ({song.lead_vocal})",
                unsafe_allow_html=True)


def metrics_panel(song, corpus):
    ref = corpus[corpus.is_original]
    cols = st.columns(4)
    # Neutral deltas: a shorter song is not a worse one.
    cols[0].metric("Words", int(song.tokens), f"{song.tokens - ref.tokens.median():+.0f} vs median", delta_color="off")
    cols[1].metric("Distinct words", int(song.types), f"{song.types - ref.types.median():+.0f} vs median",
                   delta_color="off")
    mattr = "n/a" if song.mattr != song.mattr else f"{song.mattr:.2f}"
    cols[2].metric("Lexical richness", mattr, help=HELP["mattr"])
    cols[3].metric("Repeated lines", f"{song.repeat_ratio:.0%}", help=HELP["repeats"])
