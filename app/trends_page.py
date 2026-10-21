"""Change over the discography: three questions, each with its chart and its main limit. Statistics only."""
import streamlit as st

from beatles_viz.config import PHASES
from beatles_viz.corpus import analysable
from beatles_viz.data.loader import data_source
from beatles_viz.render.components import cached_corpus, chip_row, open_word, plot
from beatles_viz.render.identity import kicker
from beatles_viz.text import trends as T
from beatles_viz.viz import trend_charts as charts


@st.cache_data(show_spinner="Looking for trends...")
def cached_trends(source):
    d = analysable(cached_corpus(source))
    d = d[d.phase.notna()]
    shares, counts = T.voice_shares(d)
    trends = T.word_trends(d)
    movers = T.steady_movers(trends, exclude=("love",))
    movers = movers.merge(T.change_interval(d, movers.word), on="word")
    return d, movers, len(trends), trends[trends.q < 0.05].word.tolist(), T.section_shares(d), shares, counts


d, movers, tested, kept, sections, voices, counts = cached_trends(data_source())

kicker("Trends · original compositions, period by period")
st.markdown("## What changed between 1962 and 1970")
st.markdown('<p class="lx-lead">Beyond “love” (see Stories): which words, which song shapes and which voices rise or fade.</p>',
            unsafe_allow_html=True)

st.subheader("Which words rise or fall, besides “love”?")
plot(charts.word_movers(movers))
pick = chip_row("Open a word", movers.word.head(3).tolist() + movers.word.tail(3).tolist(), "trend_words")
if pick:
    open_word(pick)
st.caption("Words used in at least 10 songs whose rate follows the release year (rank correlation, p < 0.05), "
           "ranked by the change of the songs' mean rate between the first and the last period; bars show a 95% "
           f"bootstrap interval (songs resampled). {tested} words are tested: once corrected for that "
           f"(Benjamini-Hochberg, q < 0.05), only {len(kept)} hold{'s' if len(kept) == 1 else ''}"
           f"{': ' + ', '.join(f'“{w}”' for w in kept) if kept else ''} (starred). Read the others as leads, then check "
           "the word's own page. The correlation uses every year, the interval only the first and last periods, so "
           "they can disagree. An interval that crosses zero is not a change. Few words rise "
           "because the later vocabulary spreads over many words, none of which dominates.")

st.subheader("Are songs built differently over time?")
plot(charts.section_shares(sections, counts))
st.caption("Sections come from Genius tags (verses and choruses detected from returning stanzas when a song has none), "
           "and count sung words only: instrumental passages are invisible. “Other” gathers intros, pre-choruses and untagged songs. Tagging habits may vary with the era "
           "of the transcription, not only with the songs.")

st.subheader("Who sings lead, and when?")
plot(charts.voice_shares(voices, counts))
st.caption("Lead voice is read from the credits; “Shared” means several lead singers. "
           f"{PHASES[0][0]} has {counts.iloc[0]} songs, so a single song moves it by several points.")

TELLING = {"he / she / they": ("third_person", "per 100 words"), "past words": ("past", "per 100 words"),
           "future words": ("future", "per 100 words"), "questions": ("questions", "per 100 lines"),
           "orders and pleas": ("orders", "per 100 lines")}
telling = {k: v for k, v in TELLING.items() if v[0] in d and d[v[0]].notna().any()}
if telling:
    st.subheader("Do the songs tell differently?")
    label = st.radio("Marker", list(telling), horizontal=True, key="trend_telling")
    col, unit = telling[label]
    plot(charts.phase_strip(d.assign(**{col: 100 * d[col]}), col, f"{label}, {unit}",
                            f"{label.capitalize()}, period by period"))
    st.caption("Word lists and line rules (beatles_viz/text/narrative.py), no grammar: past words are “was”, “said”, "
               "regular “-ed” forms…; an order is a line opening on “come”, “help”, “don't”, “let's”…; a question is a "
               "line ending in a question mark in the transcription. Rough markers: a song can tell a story in the "
               "present.")

if "sem_early" in d and d.sem_early.notna().any():
    st.subheader("Do the songs move away from their first subjects?")
    plot(charts.phase_strip(d, "sem_early", f"closeness in meaning to the {PHASES[0][0]} songs",
                            f"How close each song is, in meaning, to the songs of {PHASES[0][0]}"))
    st.caption("Each stanza is turned into a vector by a sentence transformer (all-MiniLM-L6-v2), averaged per song, "
               f"and compared with the average of the {PHASES[0][0]} songs ({PHASES[0][0]} songs are compared without "
               "themselves). Checked against random shuffles of the periods. The model was trained on everyday text, "
               "not lyrics: it reads subjects, not irony or metaphor, and the scale has no natural zero.")
