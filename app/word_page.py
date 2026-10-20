import streamlit as st

from beatles_viz.data.loader import data_source
from beatles_viz.render.components import (apply_filters, cached_corpus, chip_row, corpus_filters,
                                           open_song, open_word, plot)
from beatles_viz.render.identity import kicker
from beatles_viz.text import words as W
from beatles_viz.viz import word_charts as charts

corpus = cached_corpus(data_source())
d = apply_filters(corpus, *corpus_filters(int(corpus.year.min()), int(corpus.year.max())))
vocab, counts = W.vocabulary(d)
if not vocab:
    st.warning("No song matches the filters.")
    st.stop()

goto = st.session_state.pop("goto_word", None)
wanted = W.normalize_word(goto or st.query_params.get("w", "love"))
if wanted in vocab:
    st.session_state["word_pick"] = wanted
elif st.session_state.get("word_pick") not in vocab:
    st.session_state["word_pick"] = vocab[0]
word = st.selectbox("Word", vocab, key="word_pick", help="Content words used at least 3 times in the selection.")
st.query_params["w"] = word

kicker("Word")
st.title(f"“{word}”")
n = W.occurrences(d, word)
cols = st.columns(4)
cols[0].metric("Times sung", int(n.sum()))
cols[1].metric("Songs", f"{int((n > 0).sum())} of {len(d)}")
cols[2].metric("First used", int(d[n > 0].year.min()))
by_voice = W.usage_by(d, word, "voice")
cols[3].metric("Sung most by", by_voice.sort_values("per_1000", ascending=False).voice.iloc[0],
               help="Highest rate per 1000 words sung by that voice.")

plot(charts.usage_over_time(W.usage_by(d, word, "year"), word))
left, right = st.columns(2)
with left:
    plot(charts.usage_by_voice(by_voice, word))
with right:
    comp = W.companions(d, word)
    fig = charts.companion_words(comp, word)
    if fig is None:
        st.info("Every or no song uses this word: nothing to compare with.")
    else:
        plot(fig)
        pick = chip_row("Explore a companion word", comp.word.head(6).tolist(), "comp")
        if pick:
            open_word(pick)

st.subheader("Songs where it matters most")
top = W.top_songs(d, word)
top["share"] *= 100
st.caption("Select a row to open the song.")
sel = st.dataframe(top, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
                   key=f"word_songs_{word}",
                   column_config={"title": "Title", "year": st.column_config.NumberColumn("Year", format="%d"),
                                  "voice": "Lead voice",
                                  "occurrences": st.column_config.NumberColumn("Times", format="%d"),
                                  "share": st.column_config.NumberColumn("Share of the song's words", format="%.1f%%")})
if sel.selection.rows:
    open_song(top.iloc[sel.selection.rows[0]]["title"])
