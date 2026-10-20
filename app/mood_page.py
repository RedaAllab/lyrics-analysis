"""Mood and themes across the catalogue, from word counts only (works without the lyrics)."""
import streamlit as st

from beatles_viz.config import PHASE_ORDER, VOICE_ORDER
from beatles_viz.corpus import analysable
from beatles_viz.data.loader import data_source
from beatles_viz.render.components import HELP, cached_corpus, chip_row, open_song, plot
from beatles_viz.render.identity import kicker
from beatles_viz.viz import mood_charts as mc

corpus = analysable(cached_corpus(data_source()))
scored = corpus.dropna(subset=["valence"])

kicker("Mood and themes · original compositions")
st.markdown("## Bright songs, dark songs")
c = st.columns(3)
c[0].metric("Average mood", f"{scored.valence.mean():+.2f}", help=HELP["mood"])
bright, dark = scored.nlargest(1, "valence").iloc[0], scored.nsmallest(1, "valence").iloc[0]
c[1].metric("Brightest song", f"{bright.valence:+.2f}", bright.title, delta_color="off", delta_arrow="off")
c[2].metric("Darkest song", f"{dark.valence:+.2f}", dark.title, delta_color="off", delta_arrow="off")

plot(mc.mood_over_time(corpus))
left, right = st.columns(2)
with left:
    pick = chip_row("Brightest songs", scored.nlargest(6, "valence").title.tolist(), "mood_bright")
    if pick:
        open_song(pick)
with right:
    pick = chip_row("Darkest songs", scored.nsmallest(6, "valence").title.tolist(), "mood_dark")
    if pick:
        open_song(pick)

by = st.radio("Themes by", ["period", "voice"], horizontal=True, key="mood_by")
if by == "period":
    plot(mc.theme_heatmap(corpus, "phase", PHASE_ORDER))
else:
    plot(mc.theme_heatmap(corpus, "voice", VOICE_ORDER))

st.caption(f"Mood: average valence of the song's words in the VADER lexicon (Hutto & Gilbert 2014), from −1 to +1. "
           f"Word counts only, so negation and irony are missed (“don't cry” counts as sad); interjections such as "
           f"“yeah” or “no” are ignored. {len(corpus) - len(scored)} songs with fewer than 5 mood words have no score. "
           "Themes: short hand-made word lists (see beatles_viz/text/mood.py).")
