import streamlit as st

from beatles_viz.config import VOICE_ORDER

PLOT_CONFIG = {"displayModeBar": False}
HELP = {
    "mattr": "Moving-average type-token ratio: share of distinct words in every 50-word window, averaged. "
             "Higher means a more varied vocabulary, independent of song length.",
    "repeats": "Share of lines that repeat an earlier line of the same song.",
    "used_once": "Share of the vocabulary that appears only once in the selection.",
    "repetition": "Share of word pairs in the song that are the same word (SongSim). 0 means every word is new; higher means more repetition, whatever the length.",
    "mood": "Average valence of the song's words in the VADER sentiment lexicon, from −1 (dark) to +1 (bright). "
            "Word counts only: negation and irony are missed.",
    "z": "How strongly the word is over-represented compared with the rest (log-odds z-score). "
         "Above 2 is a clear difference.",
}


def plot(fig, static=False):
    """Plotly titles do not wrap and get cut on a phone: the title becomes a Streamlit heading above the chart."""
    from beatles_viz.viz.theme import style
    title = fig.layout.title.text
    if title:
        st.markdown(f"##### {title}")
        fig.update_layout(title=None, margin_t=10)
    config = {**PLOT_CONFIG, "staticPlot": True} if static else PLOT_CONFIG
    st.plotly_chart(style(fig), width="stretch", config=config)


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


# Markdown colours closest to VOICE_COLORS (pills cannot take arbitrary colours)
CHIP_COLORS = {"Lennon": "blue", "McCartney": "red", "Harrison": "orange", "Starr": "green", "Shared": "violet",
               "Neutral": "gray"}


def voice_chip(voice):
    return f":{CHIP_COLORS.get(voice, 'gray')}[●] {voice}"


def corpus_filters(y0, y1):
    """Sidebar filters shared by every page: (originals_only, (year_from, year_to), voices)."""
    s = st.session_state
    st.sidebar.header("Filters")
    widget, store, sync = _persistent("originals", True)
    st.sidebar.toggle("Original compositions only", key=widget, **sync)
    widget, store, sync = _persistent("years", (y0, min(y1, 1970)))
    st.sidebar.slider("Release year", y0, y1, key=widget, **sync)
    widget, store, sync = _persistent("voices", list(VOICE_ORDER))
    st.sidebar.pills("Lead voice", VOICE_ORDER, selection_mode="multi", key=widget, format_func=voice_chip, wrap=True,
                     **sync)
    return s.flt_originals, s.flt_years, s.flt_voices


def apply_filters(df, originals, years, voices, voice_col="voice"):
    d = df[df.year.between(*years) & df[voice_col].isin(voices)]
    return d[d.is_original] if originals else d


def song_table(table, key, column_config):
    """A table of songs where selecting a row opens that song."""
    st.caption("Select a row to open the song.")
    picked = st.dataframe(table, hide_index=True, width="stretch", column_config=column_config,
                          on_select="rerun", selection_mode="single-row", key=key)
    if picked.selection.rows:
        open_song(table.iloc[picked.selection.rows[0]]["title"])


def open_song(title, page="song_page.py"):
    st.session_state["goto_song"] = title
    st.switch_page(page)


def open_word(word, page="word_page.py"):
    st.session_state["goto_word"] = word
    st.switch_page(page)


def listen_row(title, label="Listen on", player=False):
    """One line of links that wraps on a phone, rather than a row of buttons; with player, the song's official
    YouTube upload above it when there is one."""
    from beatles_viz.listen import listen_links, youtube_embed
    embed = youtube_embed(title) if player else None
    if embed:
        left, _ = st.columns([2, 3])
        with left:
            st.iframe(embed, height=200)
    links = " · ".join(f"[{name}]({url})" for name, url in listen_links(title).items())
    st.markdown(f":material/headphones: {label} {links}")


def chip_row(label, options, key, help=None):
    """Clickable chips that wrap on narrow screens; returns the clicked option or None. Every caller navigates
    away on a click, so no selection is left behind."""
    return st.pills(label, options, selection_mode="single", key=key, help=help, width="stretch",
                    wrap=True) if options else None


EVIDENCE = {
    "descriptive": (":material/bar_chart:", "Descriptive",
                    "counts read from the data: true of these sources, nothing more"),
    "exploratory": (":material/explore:", "Exploratory",
                    "a pattern found by a method that could have found another: a lead to check"),
    "validate": (":material/rule:", "To validate",
                 "a claim that needs annotated data, sources or a test before it can be stated"),
}


def evidence(level):
    """One line saying how far a result can be trusted (docs/ROADMAP.md, v2, part D)."""
    icon, name, meaning = EVIDENCE[level]
    st.caption(f"{icon} **{name}**: {meaning}.")
