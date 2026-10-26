"""The four voices side by side: a profile, an evolution, their own words and a head-to-head."""
import streamlit as st

from beatles_viz.config import MEMBERS, VOICE_COLORS
from beatles_viz.corpus import analysable
from beatles_viz.data.loader import data_source
from beatles_viz.render.components import HELP, cached_corpus, chip_row, open_song, open_word, plot
from beatles_viz.render.identity import kicker
from beatles_viz.render.share_card import figure_share_block
from beatles_viz.config import APP_URL
from beatles_viz.viz import voice_charts as vc

corpus = analysable(cached_corpus(data_source()))

kicker("Lead voices · original compositions")
st.markdown("## Who sings what")
pick_a, pick_b = st.columns(2)
a = pick_a.selectbox("Voice", MEMBERS, index=0, key="voice_a")
b = pick_b.selectbox("Against", MEMBERS, index=1, key="voice_b")
voices = [a] if a == b else [a, b]

cols = st.columns(len(voices))
for col, v in zip(cols, voices):
    s = vc.voice_summary(corpus, v)
    col.markdown(f"<h3 style='color:{VOICE_COLORS[v]};margin-bottom:0'>{v}</h3>", unsafe_allow_html=True)
    m = col.columns(3)
    m[0].metric("Songs", s["songs"], f"{s['first']}–{s['last']}", delta_color="off")
    m[1].metric("Median words", f"{s['words']:.0f}")
    m[2].metric("Richness", f"{s['mattr']:.2f}", help=HELP["mattr"])

left, right = st.columns(2)
with left:
    plot(vc.voice_radar(corpus, voices))
with right:
    label = st.radio("Over time", list(vc.TRENDS), horizontal=True, key="voice_trend")
    fig_trend = vc.voice_trend(corpus, voices, vc.TRENDS[label], label)
    plot(fig_trend)

lines = [f"{t.name}: {t.y[0]:.2f} in {t.x[0]}, {t.y[-1]:.2f} in {t.x[-1]}." for t in fig_trend.data if len(t.y) > 1]
figure_share_block(f"voices-{'-'.join(voices)}-{label}", f"{' and '.join(voices)}: {label.lower()} over time",
                   " ".join(lines) + " Lead voice is read from the credits; it is not the writer.", fig_trend,
                   "LEAD VOICES", f"{APP_URL}/voices", "Original compositions, 1962-1970")

if len(voices) == 2:
    fig = vc.voice_duel(corpus, a, b)
    if fig is not None:
        plot(fig)

cols = st.columns(len(voices))
for col, v in zip(cols, voices):
    with col:
        words = vc.voice_words(corpus, v, top=8).word.tolist()
        if words:
            pick = chip_row(f"{v}'s words", words, f"voice_words_{v}",
                            help=f"Sung much more by {v} than by the other voices. " + HELP["z"])
            if pick:
                open_word(pick)
        songs = vc.signature_songs(corpus, v, k=4)
        pick = chip_row(f"Most {v} songs", songs, f"voice_songs_{v}",
                        help=f"Songs that use the most of {v}'s characteristic words, per word sung.")
        if pick:
            open_song(pick)

st.caption("Voice = lead singer listed on Wikipedia; most songs are credited Lennon–McCartney, so the lead voice is "
           "a proxy for the writer, not proof. Songs with several lead singers count as Shared and are left out.")
