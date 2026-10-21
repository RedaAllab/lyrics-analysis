"""A game: the words that set a song apart, and the lead voice to guess. Lyrics are never shown, only single words."""
import html
import random

import streamlit as st

from beatles_viz.config import MEMBERS, VOICE_COLORS
from beatles_viz.corpus import analysable
from beatles_viz.data.loader import data_source
from beatles_viz.quiz import pool, question
from beatles_viz.render.components import cached_corpus, open_song
from beatles_viz.render.identity import kicker

corpus = analysable(cached_corpus(data_source()))
s = st.session_state
s.setdefault("guess_asked", [])
s.setdefault("guess_score", [0, 0])  # right, played
s.setdefault("guess_pick", None)


def draw():
    if len(s.guess_asked) >= len(pool(corpus)):
        s.guess_asked = []  # every song has been asked: start over
    s.guess_q = question(corpus, random.Random(), s.guess_asked)
    s.guess_pick = None
    if s.guess_q:
        s.guess_asked.append(s.guess_q.title)


def answer(voice):
    s.guess_pick = voice
    s.guess_score = [s.guess_score[0] + (voice == s.guess_q.voice), s.guess_score[1] + 1]


if s.get("guess_q") is None:
    draw()
q = s.guess_q

kicker("A game · lead voices")
st.title("Who sings this?")
st.markdown('<p class="lx-lead">The words that set one Beatles song apart from all the others. '
            "No lyrics here, only single words: which of the four sings it?</p>", unsafe_allow_html=True)

right, played = s.guess_score
st.metric("Score", f"{right} / {played}" if played else "0 / 0")

if q is None:
    st.info("Not enough songs with a telling vocabulary to ask a question.")
    st.stop()

st.markdown('<div class="lx-chips">' + "".join(f'<span class="lx-chip">{html.escape(w)}</span>' for w in q.words)
            + "</div>", unsafe_allow_html=True)

if s.guess_pick is None:
    for col, voice in zip(st.columns(len(MEMBERS)), MEMBERS):
        col.button(voice, key=f"guess_{voice}", on_click=answer, args=(voice,), width="stretch")
else:
    color = VOICE_COLORS[q.voice]
    if s.guess_pick == q.voice:
        st.success(f"Yes, {q.voice} sings the lead.")
    else:
        st.error(f"Not quite: you said {s.guess_pick}, it is {q.voice}.")
    st.markdown(f"<h3><span class='lx-dot' style='background:{color}'></span>{html.escape(q.title)} "
                f"<span style='font-weight:400'>({q.year})</span></h3>", unsafe_allow_html=True)
    again, show = st.columns(2)
    again.button("Next song", key="guess_next", on_click=draw, icon=":material/arrow_forward:", type="primary",
                 width="stretch")
    if show.button("Open the song", key="guess_open", icon=":material/lyrics:", width="stretch"):
        open_song(q.title)
