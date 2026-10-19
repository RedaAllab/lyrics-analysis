import re

import streamlit as st

from beatles_viz.config import VOICE_COLORS, VOICE_ORDER

PLOT_CONFIG = {"displayModeBar": False}
HELP = {
    "mattr": "Moving-average type-token ratio: share of distinct words in every 50-word window, averaged. "
             "Higher means a more varied vocabulary, independent of song length.",
    "repeats": "Share of lines that repeat an earlier line of the same song.",
    "used_once": "Share of the vocabulary that appears only once in the selection.",
    "repetition": "Share of word pairs in the song that are the same word (SongSim). 0 means every word is new; higher means more repetition, whatever the length.",
    "z": "How strongly the word is over-represented compared with the rest (log-odds z-score). "
         "Above 2 is a clear difference.",
}


def plot(fig, static=False):
    config = {**PLOT_CONFIG, "staticPlot": True} if static else PLOT_CONFIG
    st.plotly_chart(fig, use_container_width=True, config=config)


@st.cache_data(show_spinner="Loading songs...")
def cached_corpus(source):
    from beatles_viz.corpus import load_corpus
    return load_corpus(source)


def _persistent(name, default):
    # Streamlit drops widget state when the page changes: the value lives in a plain key, is copied into the
    # widget key before each render, and copied back on change (pattern from the Streamlit multipage docs).
    s = st.session_state
    store, widget = f"flt_{name}", f"w_{name}"
    s.setdefault(store, default)
    s[widget] = s[store]
    return widget, store, {"on_change": _save, "args": (widget, store)}


def _save(widget, store):
    st.session_state[store] = st.session_state[widget]


def corpus_filters(y0, y1):
    """Sidebar filters shared by every page: (originals_only, (year_from, year_to), voices)."""
    s = st.session_state
    st.sidebar.header("Filters")
    widget, store, sync = _persistent("originals", True)
    st.sidebar.toggle("Original compositions only", key=widget, **sync)
    widget, store, sync = _persistent("years", (y0, min(y1, 1970)))
    st.sidebar.slider("Release year", y0, y1, key=widget, **sync)
    widget, store, sync = _persistent("voices", list(VOICE_ORDER))
    st.sidebar.multiselect("Lead voice", VOICE_ORDER, key=widget, **sync)
    return s.flt_originals, s.flt_years, s.flt_voices


def apply_filters(df, originals, years, voices, voice_col="voice"):
    d = df[df.year.between(*years) & df[voice_col].isin(voices)]
    return d[d.is_original] if originals else d


def open_song(title, page="song_page.py"):
    st.session_state["goto_song"] = title
    st.switch_page(page)


def open_word(word, page="word_page.py"):
    st.session_state["goto_word"] = word
    st.switch_page(page)


def song_selector(corpus, key="song"):
    """Shared filters + title picker. Keeps the choice in the URL (?song=...) so a song can be linked."""
    d = apply_filters(corpus, *corpus_filters(int(corpus.year.min()), int(corpus.year.max())))
    if d.empty:
        return None, d
    titles = d.title.tolist()
    goto = st.session_state.pop("goto_song", None)
    if goto in titles:
        st.session_state[f"{key}_title"] = goto
    wanted = goto or st.query_params.get("song")
    index = titles.index(wanted) if wanted in titles else 0
    if st.session_state.get(f"{key}_title") not in titles:
        st.session_state.pop(f"{key}_title", None)
    title = st.sidebar.selectbox("Song", titles, index=index, key=f"{key}_title",
                                 format_func=lambda t: f"{t} ({int(d.loc[d.title == t, 'year'].iloc[0])})")
    st.query_params["song"] = title
    return d[d.title == title].iloc[0], d


def song_header(song):
    from beatles_viz.viz.song_charts import fingerprint_figure
    color = VOICE_COLORS.get(song.voice, "#999999")
    text, thumb = st.columns([5, 1], vertical_alignment="center")
    text.markdown(f"## {song.title}")
    release = re.sub(r'"\s+', '"', song.release_core)  # Wikipedia export leaves '" Title' quotes
    text.markdown(f"{int(song.year)} · *{release}* · written by {song.songwriters} · "
                  f"lead voice <span style='color:{color};font-weight:600'>{song.voice}</span> ({song.lead_vocal})",
                  unsafe_allow_html=True)
    if "fingerprint" in song and song.fingerprint.size > 1:
        with thumb:
            plot(fingerprint_figure(song.fingerprint, color, height=120), static=True)
            st.caption("Repetition fingerprint", help=HELP["repetition"])


def chip_row(label, options, key, help=None):
    """A row of small buttons; returns the clicked option or None. Plain buttons rather than st.pills,
    which AppTest cannot rerun."""
    st.markdown(f"**{label}**", help=help)
    cols = st.columns(len(options)) if options else []
    for i, (col, option) in enumerate(zip(cols, options)):
        if col.button(option, key=f"{key}_{i}", type="tertiary", use_container_width=True):
            return option
    return None


def similar_picker(song, corpus, matrix, key):
    from beatles_viz.text.similarity import similar_songs
    sims = similar_songs(corpus, song.title, k=5, matrix=matrix)
    labels = {f"{r.title} · {r.similarity:.0%}": r.title for r in sims.itertuples()}
    pick = chip_row("Songs like this one", list(labels), f"{key}_similar",
                    help="Closest vocabulary (TF-IDF weighted word counts, cosine similarity).")
    if pick:
        open_song(labels[pick])


def metrics_panel(song, corpus):
    ref = corpus[corpus.is_original]
    cols = st.columns(5)
    # Neutral deltas: a shorter song is not a worse one.
    cols[0].metric("Words", int(song.tokens), f"{song.tokens - ref.tokens.median():+.0f} vs median", delta_color="off")
    cols[1].metric("Distinct words", int(song.types), f"{song.types - ref.types.median():+.0f} vs median",
                   delta_color="off")
    mattr = "n/a" if song.mattr != song.mattr else f"{song.mattr:.2f}"
    cols[2].metric("Lexical richness", mattr, help=HELP["mattr"])
    cols[3].metric("Repeated lines", f"{song.repeat_ratio:.0%}", help=HELP["repeats"])
    if "repetition_score" in song and song.repetition_score == song.repetition_score:
        pct = (ref.repetition_score < song.repetition_score).mean()
        cols[4].metric("Repetition score", f"{song.repetition_score:.3f}", f"more than {pct:.0%} of songs",
                       delta_color="off", help=HELP["repetition"])
