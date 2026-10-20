"""The Beatles next to other artists, from the tables in analysis/artists/ (no lyrics)."""
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
everyone = ac.present(t["songs"])

kicker("Beyond the Beatles · original compositions")
st.markdown("## The Beatles and the others")
st.markdown("The same measures, computed the same way, on each catalogue: the Rolling Stones, the solo careers of "
            "Paul McCartney and John Lennon, and four singer-songwriters.")
group = st.segmented_control("Show", ["Everyone", *ac.GROUPS], default="Everyone", key="artists_group") or "Everyone"
chosen = everyone if group == "Everyone" else ["The Beatles", *[a for a in ac.GROUPS[group] if a != "The Beatles"]]
chosen = [a for a in everyone if a in chosen]
songs = t["songs"][t["songs"].artist.isin(chosen)]
years = t["years"][t["years"].artist.isin(chosen)]

st.markdown("#### A typical song (medians)")
st.dataframe(ac.profile_table(songs), width="stretch", column_config={
    "Richness": st.column_config.NumberColumn(help=HELP["mattr"]),
    "Repetition": st.column_config.NumberColumn(help=HELP["repetition"]),
    "Mood": st.column_config.NumberColumn(help=HELP["mood"])})

measure = st.segmented_control("Measure", list(ac.MEASURES), format_func=ac.MEASURES.get, default="mattr",
                               key="artists_measure") or "mattr"
plot(ac.profile_box(songs, measure))
others = [a for a in chosen if a != "The Beatles"]
ps = ", ".join(f"{a} p = {ac.p_value(t['tests'], measure, 'The Beatles', a):.2g}" for a in others)
st.caption(f"Each dot outside the boxes is one song; the box holds the middle half. Difference with the Beatles "
           f"(Mann-Whitney): {ps}. Below 0.01 it is very unlikely to be chance.")

st.markdown("#### The words that set each one apart")
st.caption("Words used far more by one artist than by all the others together (log-odds z-score), found in at least "
           "five of their songs. Names of people and places are left out.")
for start in range(0, len(chosen), 4):
    for col, artist in zip(st.columns(4), chosen[start:start + 4]):
        with col:
            plot(ac.distinctive_bars(t["words"], artist), static=True)
beatles_words = t["words"][t["words"].artist == "The Beatles"].nlargest(12, "z").word.tolist()
pick = chip_row("Open a Beatles word", beatles_words, "artists_word")
if pick:
    open_word(pick)

st.markdown("#### Growing up")
trend = st.segmented_control("Over time", ac.TREND_MEASURES, format_func=ac.MEASURES.get, default="mattr",
                             key="artists_trend") or "mattr"
plot(ac.career_lines(years, trend))
st.caption("Nine years is the Beatles' whole recording career (1962-1970), so every artist is compared over the "
           "nine years from their first record: the Stones from 1963, Dylan from 1962, Cohen from 1967, Mitchell from "
           "1968, Lennon from 1969, McCartney from 1970 and Paul Simon from 1972, his first solo album after Simon & "
           "Garfunkel. Hollow dots: fewer than five songs that year. Click a name in the legend to hide it.")

counts = t["songs"].artist.value_counts()
st.caption("Original compositions with at least 30 words: " + ", ".join(f"{counts.get(a, 0)} by {a}" for a in everyone)
           + ". Lyrics from Genius; years from Wikipedia's song lists, or from the studio albums' track listings for "
           "Cohen, Mitchell and Simon. Method and limits: analysis/artists/README.md in the project repository.")
