import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from beatles_viz.config import VOICE_COLORS  # noqa: E402
from beatles_viz.data.loader import has_lyrics  # noqa: E402
from beatles_viz.render.components import apply_filters, cached_corpus, corpus_filters, open_song, plot  # noqa: E402
from beatles_viz.viz import compare_charts as cmp  # noqa: E402
from beatles_viz.viz import song_charts as charts  # noqa: E402
from beatles_viz.viz.song_charts import HIGHLIGHT_COLORS  # noqa: E402

local = has_lyrics()
corpus = cached_corpus("local" if local else "public")
d = apply_filters(corpus, *corpus_filters(int(corpus.year.min()), int(corpus.year.max())))
st.title("Compare two songs")
if len(d) < 2:
    st.warning("Fewer than two songs match the filters.")
    st.stop()

titles = d.title.tolist()
defaults = [t for t in ["Something", "Hey Jude"] if t in titles] or titles[:2]
picks = []
for i, (col, label) in enumerate(zip(st.columns(2), ["Song A", "Song B"])):
    default = defaults[i] if i < len(defaults) else titles[i]
    title = col.selectbox(label, titles, index=titles.index(default), key=f"cmp_{i}")
    song = d[d.title == title].iloc[0]
    picks.append(song)
    color = VOICE_COLORS.get(song.voice, "#999")
    col.markdown(f'<span class="lx-dot" style="background:{HIGHLIGHT_COLORS[i]}"></span>'
                 f'**{song.title}** · {int(song.year)} · <span style="color:{color}">{song.voice}</span>',
                 unsafe_allow_html=True)
    if col.button("Open this song", key=f"cmp_open_{i}", icon=":material/arrow_forward:"):
        open_song(song.title)
a, b = picks
if a.title == b.title:
    st.info("Pick two different songs.")
    st.stop()

plot(cmp.percentile_profile(a, b, corpus[corpus.is_original]))

if local:
    for song in (a, b):
        fig = charts.structure_timeline(song.sections)
        fig.update_layout(title=f"How {song.title} is built")
        plot(fig)

left, right = st.columns([3, 2])
with left:
    fig = cmp.word_contrast(a, b)
    if fig is None:
        st.info("Not enough words to tell these songs apart.")
    else:
        plot(fig)
with right:
    v = cmp.shared_vocabulary(a, b)
    st.metric("Shared words", v["shared"], help="Content words used in both songs (stop words removed).")
    st.metric(f"Only in {a.title}", v["only_a"])
    st.metric(f"Only in {b.title}", v["only_b"])
    st.caption(f"{v['overlap']:.0%} of their combined vocabulary is shared.")

plot(cmp.pronoun_pair(a, b))
plot(charts.corpus_position(a, corpus, None, others=[b]))
