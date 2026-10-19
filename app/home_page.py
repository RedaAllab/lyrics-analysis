import random
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from beatles_viz.config import VOICE_COLORS  # noqa: E402
from beatles_viz.corpus import featured_songs  # noqa: E402
from beatles_viz.data.loader import has_lyrics  # noqa: E402
from beatles_viz.render.components import cached_corpus, open_song, plot  # noqa: E402
from beatles_viz.viz.song_charts import fingerprint_figure  # noqa: E402
from beatles_viz.render.identity import kicker  # noqa: E402

corpus = cached_corpus("local" if has_lyrics() else "public")
originals = corpus[corpus.is_original]

kicker(f"The Beatles · {int(originals.year.min())}–1970")
st.title("Pick a song, see how it is written")
st.markdown('<p class="lx-lead">Structure, repetitions, vocabulary and voices of '
            f'{len(originals)} original compositions, song by song or across the whole catalogue.</p>',
            unsafe_allow_html=True)

search, surprise = st.columns([4, 1], vertical_alignment="bottom")
titles = originals.sort_values("title").title.tolist()
choice = search.selectbox("Search a song", titles, index=None, placeholder="Type a title…",
                          label_visibility="collapsed")
if choice:
    open_song(choice)
if surprise.button("Surprise me", icon=":material/shuffle:", use_container_width=True):
    open_song(random.choice(titles))

st.subheader("Songs to discover")
cards = featured_songs(corpus)
for row_start in range(0, len(cards), 3):
    for col, (label, title, reason) in zip(st.columns(3), cards[row_start:row_start + 3]):
        song = corpus[corpus.title == title].iloc[0]
        with col.container(border=True):
            kicker(label)
            st.markdown(f"### {title}")
            if "fingerprint" in song and song.fingerprint.size > 1:
                plot(fingerprint_figure(song.fingerprint, VOICE_COLORS.get(song.voice, "#e07a5f"), height=110),
                     static=True)
            st.markdown(f'<span class="lx-dot" style="background:{VOICE_COLORS.get(song.voice, "#999")}"></span>'
                        f'{song.voice} · {int(song.year)}<br><span class="lx-stat">{reason}</span>',
                        unsafe_allow_html=True)
            if st.button("Open", key=f"open_{title}", icon=":material/arrow_forward:"):
                open_song(title)

st.subheader("Or explore")
left, right = st.columns(2)
left.page_link("corpus_page.py", label="The whole catalogue: vocabulary over time and by voice",
               icon=":material/bar_chart:")
right.page_link("compare_page.py", label="Two songs side by side", icon=":material/compare_arrows:")
