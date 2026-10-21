"""Mood and themes across the catalogue, from word counts only (works without the lyrics)."""
import streamlit as st

from beatles_viz import themes as T
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

if "valence_ctx" in corpus and corpus.valence_ctx.notna().any():
    st.subheader("Does reading line by line change the mood?")
    plot(mc.mood_methods(corpus))
    gap = (scored.valence_ctx - scored.valence).abs().dropna()
    pick = chip_row("Biggest changes", scored.loc[gap.nlargest(6).index].title.tolist(), "mood_gap")
    if pick:
        open_song(pick)
    st.caption("Line by line, VADER's sentence rules apply: negation (“don't cry” is no longer sad), intensifiers and "
               "“but”. The score is the mean of the lines that carry a mood, from −1 to +1; songs with fewer than 3 such "
               "lines have none. Both readings use the same lexicon, and neither sees irony.")

by = st.radio("Themes by", ["period", "voice"], horizontal=True, key="mood_by")
if by == "period":
    plot(mc.theme_heatmap(corpus, "phase", PHASE_ORDER))
else:
    plot(mc.theme_heatmap(corpus, "voice", VOICE_ORDER))

st.caption(f"Mood: average valence of the song's words in the VADER lexicon (Hutto & Gilbert 2014), from −1 to +1. "
           f"Word counts only, so negation and irony are missed (“don't cry” counts as sad); interjections such as "
           f"“yeah” or “no” are ignored. {len(corpus) - len(scored)} songs with fewer than 5 mood words have no score. "
           "Themes: short hand-made word lists (see beatles_viz/text/mood.py).")

st.subheader("Themes annotated by hand")
annotations = T.load_annotations()
if annotations.empty:
    st.info("No song annotated yet. The themes above come from word lists; hand annotations with the codebook "
            "(data/themes/codebook.csv, Annotate page on a computer with the lyrics) will replace them here.")
else:
    codebook = T.load_codebook()
    annotator = st.selectbox("Annotator", sorted(annotations.annotator.unique()), key="mood_annotator")
    matrix = T.theme_matrix(annotations, annotator, codebook.theme)
    matrix = matrix[matrix.index.isin(corpus.title)]
    plot(mc.annotated_theme_heatmap(matrix, corpus, dict(zip(codebook.theme, codebook.label))))
    st.caption(f"{len(matrix)} of {len(corpus)} songs annotated by {annotator}. Share of the annotated songs of each "
               "period that carry the theme; a song can carry several. A period with few annotated songs moves a "
               "lot with each one.")
