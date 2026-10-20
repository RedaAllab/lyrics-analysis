"""Change over the discography: three questions, each with its chart and its main limit. Statistics only."""
import streamlit as st

from beatles_viz.config import PHASES
from beatles_viz.corpus import analysable
from beatles_viz.data.loader import has_lyrics
from beatles_viz.render.components import cached_corpus, chip_row, open_word, plot
from beatles_viz.render.identity import kicker
from beatles_viz.text import trends as T
from beatles_viz.viz import trend_charts as charts


@st.cache_data(show_spinner="Looking for trends...")
def cached_trends(source):
    d = analysable(cached_corpus(source))
    d = d[d.phase.notna()]
    shares, counts = T.voice_shares(d)
    return T.steady_movers(T.word_trends(d), exclude=("love",)), T.section_shares(d), shares, counts


movers, sections, voices, counts = cached_trends("local" if has_lyrics() else "public")

kicker("Trends · original compositions, period by period")
st.markdown("## What changed between 1962 and 1970")
st.markdown('<p class="lx-lead">Beyond “love” (see Stories): which words, which song shapes and which voices rise or fade.</p>',
            unsafe_allow_html=True)

st.subheader("Which words rise or fall, besides “love”?")
plot(charts.word_movers(movers))
pick = chip_row("Open a word", movers.word.tolist(), "trend_words")
if pick:
    open_word(pick)
st.caption("Words used in at least 10 songs whose rate follows the release year (rank correlation, p < 0.05), "
           "ranked by the change between the first and the last period. Over a hundred words are tested, so a few "
           "of these drifts are chance: read them as leads, then check the word's own page. Few words rise because "
           "the later vocabulary spreads over many words, none of which dominates.")

st.subheader("Are songs built differently over time?")
plot(charts.section_shares(sections, counts))
st.caption("Sections come from Genius tags (verses and choruses detected from returning stanzas when a song has none), "
           "and count sung words only: instrumental passages are invisible. Tagging habits may vary with the era "
           "of the transcription, not only with the songs.")

st.subheader("Who sings lead, and when?")
plot(charts.voice_shares(voices, counts))
st.caption("Lead voice is read from the credits; “Shared” means several lead singers. "
           f"{PHASES[0][0]} has {counts.iloc[0]} songs, so a single song moves it by several points.")
