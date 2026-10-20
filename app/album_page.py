"""One release at a time: its tracks, how they are built, their fingerprints and the words of the album."""
import streamlit as st

from beatles_viz.config import VOICE_COLORS
from beatles_viz.corpus import albums
from beatles_viz.data.loader import has_lyrics
from beatles_viz.render.components import HELP, cached_corpus, chip_row, open_song, open_word, plot
from beatles_viz.render.identity import kicker
from beatles_viz.text.keyness import monroe, prior
from beatles_viz.text.tokenize import content_counter, merge
from beatles_viz.viz import album_charts
from beatles_viz.viz.song_charts import fingerprint_figure

TRACK_METRICS = {"Lexical richness": "mattr", "Words": "tokens", "Repetition score": "repetition_score",
                 "Repeated lines": "repeat_ratio"}
GRID = 4

corpus = cached_corpus("local" if has_lyrics() else "public")
table = albums(corpus)
names = table.album.tolist()
wanted = st.query_params.get("album")
album = st.selectbox("Album", names, index=names.index(wanted) if wanted in names else 0, key="album_pick",
                     format_func=lambda a: f"{a} ({int(table.set_index('album').year[a])})")
st.query_params["album"] = album
info = table.set_index("album").loc[album]
tracks = corpus[corpus.album == album].sort_values(["year", "title"])

kicker(f"{int(info.year)} · {int(info.tracks)} songs in the catalogue")
st.markdown(f"## {album}")
c = st.columns(4)
c[0].metric("Songs", int(info.tracks), f"{int(info.originals)} original", delta_color="off")
c[1].metric("Words", f"{int(info.words):,}")
c[2].metric("Lexical richness", "n/a" if info.mattr != info.mattr else f"{info.mattr:.2f}", help=HELP["mattr"])
c[3].metric("Most heard voice", info.voice)
plot(album_charts.album_timeline(table, album))

fig = album_charts.album_structures(tracks)
if fig is not None:
    plot(fig)
left, right = st.columns([3, 2])
with left:
    label = st.radio("Compare tracks by", list(TRACK_METRICS), horizontal=True, key="album_metric")
    fig = album_charts.album_tracks(tracks, TRACK_METRICS[label], label)
    if fig is None:
        st.info("No value for this measure.")
    else:
        plot(fig)
with right:
    a = content_counter(merge(tracks.bow))
    rest = content_counter(merge(corpus[corpus.album != album].bow))
    words = monroe(a, rest, prior(a + rest), min_count=3).query("z > 0").word.head(8).tolist()
    if words:
        pick = chip_row("Words of this album", words, "album_words",
                        help="Over-represented on this album compared with the rest of the catalogue. " + HELP["z"])
        if pick:
            open_word(pick)

st.markdown("**Repetition fingerprints**", help=HELP["repetition"])
rows = list(tracks.itertuples())
for start in range(0, len(rows), GRID):
    cols = st.columns(GRID)
    for col, t in zip(cols, rows[start:start + GRID]):
        with col:
            if getattr(t, "fingerprint", None) is not None and t.fingerprint.size > 1:
                plot(fingerprint_figure(t.fingerprint, VOICE_COLORS.get(t.voice, "#999999"), height=110), static=True)
            if st.button(t.title, key=f"album_open_{t.Index}", type="tertiary", width="stretch"):
                open_song(t.title)
st.caption("Track order: year, then title (the data has no track numbers). Release: first one listed on Wikipedia.")
