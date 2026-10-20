"""The Beatles next to the Rolling Stones and Bob Dylan, from the tables in analysis/artists/ (no lyrics)."""
import streamlit as st

from beatles_viz.render.components import HELP, chip_row, open_word, plot
from beatles_viz.render.identity import kicker
from beatles_viz.viz import artist_charts as ac

if not ac.available():
    st.info("The comparison tables are missing: run scripts/compare_artists.py (see analysis/artists/README.md).")
    st.stop()


@st.cache_data
def tables():
    return ac.load_tables()


t = tables()
songs, med = t["songs"], ac.medians(t["songs"])

kicker("Beyond the Beatles · original compositions")
st.markdown("## The Beatles, the Rolling Stones and Bob Dylan")
st.markdown("The same measures, computed the same way, on the three catalogues. A typical song by each artist:")
for col, (artist, row) in zip(st.columns(len(med)), med.iterrows()):
    with col:
        st.markdown(f'<span class="lx-dot" style="background:{ac.ARTIST_COLORS[artist]}"></span>**{artist}**',
                    unsafe_allow_html=True)
        st.metric("Vocabulary richness", f"{row.mattr:.2f}", help=HELP["mattr"])
        st.metric("Words", f"{row.tokens:.0f}")
        st.metric("Mood", f"{row.valence:+.2f}", help=HELP["mood"])

measure = st.segmented_control("Measure", list(ac.MEASURES), format_func=ac.MEASURES.get, default="mattr",
                               key="artists_measure") or "mattr"
plot(ac.profile_box(songs, measure))
p = ac.p_value(t["tests"], measure, "The Beatles", "The Rolling Stones")
q = ac.p_value(t["tests"], measure, "The Beatles", "Bob Dylan")
st.caption(f"Each dot outside the boxes is one song; the box holds the middle half. Difference with the Beatles "
           f"(Mann-Whitney): Rolling Stones p = {p:.2g}, Bob Dylan p = {q:.2g}; below 0.01 it is very unlikely "
           "to be chance.")

st.markdown("#### The words that set each one apart")
st.caption("Words used far more by one artist than by the other two (log-odds z-score), found in at least five "
           "of their songs. Names of people and places are left out.")
for col, artist in zip(st.columns(3), ac.ARTISTS):
    with col:
        plot(ac.distinctive_bars(t["words"], artist), static=True)
beatles_words = t["words"][t["words"].artist == "The Beatles"].nlargest(12, "z").word.tolist()
pick = chip_row("Open a Beatles word", beatles_words, "artists_word")
if pick:
    open_word(pick)

st.markdown("#### Growing up")
trend = st.segmented_control("Over time", ac.TREND_MEASURES, format_func=ac.MEASURES.get, default="mattr",
                             key="artists_trend") or "mattr"
plot(ac.career_lines(t["years"], trend))
st.caption("Nine years is the Beatles' whole recording career (1962-1970); the Rolling Stones are taken from 1963 "
           "and Bob Dylan from 1962, so the three are compared at the same age and in the same decade. Hollow dots: "
           "fewer than five songs that year (the early Stones mostly recorded covers).")

counts = songs.artist.value_counts()
st.caption("Original compositions with at least 30 words: " + ", ".join(f"{counts.get(a, 0)} by {a}" for a in ac.ARTISTS)
           + ". Lyrics from Genius, years from Wikipedia's song lists. Method and limits: analysis/artists/README.md "
           "in the project repository.")
