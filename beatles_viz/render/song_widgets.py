"""Widgets of the song page: picker, header, similar songs and metrics."""
import re

import streamlit as st

from beatles_viz.config import IMPROVISATIONS, VOICE_COLORS
from beatles_viz.render.components import HELP, apply_filters, chip_row, corpus_filters, open_song, plot
from beatles_viz.text.similarity import similar_songs
from beatles_viz.viz.song_charts import fingerprint_figure


def song_selector(corpus, key="song"):
    """Shared filters + title picker. Keeps the choice in the URL (?song=...) so a song can be linked."""
    d = apply_filters(corpus, *corpus_filters(int(corpus.year.min()), int(corpus.year.max())))
    if d.empty:
        return None, d
    titles = d.title.tolist()
    # The choice lives in session state only: a widget given both a default and a session value warns.
    state = f"{key}_title"
    goto = st.session_state.pop("goto_song", None)
    if goto in titles:
        st.session_state[state] = goto
    if st.session_state.get(state) not in titles:
        wanted = st.query_params.get("song")
        st.session_state[state] = wanted if wanted in titles else titles[0]
    title = st.sidebar.selectbox("Song", titles, key=state,
                                 format_func=lambda t: f"{t} ({int(d.loc[d.title == t, 'year'].iloc[0])})")
    st.query_params["song"] = title
    return d[d.title == title].iloc[0], d


def song_header(song):
    color = VOICE_COLORS.get(song.voice, "#999999")
    text, thumb = st.columns([5, 1], vertical_alignment="center")
    text.markdown(f"## {song.title}")
    release = re.sub(r'"\s+', '"', song.release_core)  # Wikipedia export leaves '" Title' quotes
    text.markdown(f"{int(song.year)} · *{release}* · written by {song.songwriters} · "
                  f"lead voice <span style='color:{color};font-weight:600'>{song.voice}</span> ({song.lead_vocal})",
                  unsafe_allow_html=True)
    if song.title in IMPROVISATIONS:
        text.caption("Studio improvisation from the Get Back sessions: left out of the catalogue statistics.")
    if "fingerprint" in song and song.fingerprint.size > 1:
        with thumb:
            plot(fingerprint_figure(song.fingerprint, color, height=120), static=True)
            st.caption("Repetition fingerprint", help=HELP["repetition"])


def similar_picker(song, corpus, matrix, key):
    """Closest songs by shared words and, when scripts/embed_songs.py has run, by meaning."""
    sims = similar_songs(corpus, song.title, k=5, matrix=matrix)
    rows = [("similar", "Similar words", {f"{r.title} · {r.similarity:.0%}": r.title for r in sims.itertuples()},
             "Closest vocabulary (TF-IDF weighted word counts, cosine similarity).")]
    meaning = song.get("sem_neighbors")
    if meaning is not None and not isinstance(meaning, float) and len(meaning):
        rows.append(("meaning", "Similar meaning", {t: t for t in meaning},
                     "Closest in meaning: each stanza turned into a vector by a sentence transformer (all-MiniLM-L6-v2), "
                     "averaged per song, cosine similarity. Trained on everyday text, not lyrics: irony and metaphor "
                     "escape it."))
    for suffix, label, options, help in rows:
        pick = chip_row(label, list(options), f"{key}_{suffix}", help=help)
        if pick:
            open_song(options[pick])


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
