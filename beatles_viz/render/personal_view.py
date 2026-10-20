"""The song page's personal strip: favourite, rating, 'I listened' and notes. Local only."""
import hashlib

import streamlit as st

from beatles_viz import personal


def _key(title, part):
    return f"me_{part}_{hashlib.md5(title.encode()).hexdigest()[:10]}"


def _save_rating(title, key):
    stars = st.session_state[key]
    personal.update(title, rating=None if stars is None else stars + 1)


def _save_note(title, key):
    personal.update(title, note=st.session_state[key].strip())


def personal_strip(song):
    if not personal.enabled():
        return
    title = song.title
    e = personal.entry(personal.load(), title)
    fav, stars, listen, info = st.columns([1.2, 1.4, 1.2, 3], vertical_alignment="center")
    label = "Favourite" if e["favourite"] else "Add to favourites"
    if fav.button(label, icon=":material/star:" if e["favourite"] else ":material/star_border:",
                  key=_key(title, "fav"), type="tertiary"):
        personal.update(title, favourite=not e["favourite"])
        st.rerun()
    with stars:
        st.feedback("stars", key=_key(title, "rating"),
                    default=None if e["rating"] is None else e["rating"] - 1,
                    on_change=_save_rating, args=(title, _key(title, "rating")))
    if listen.button("I listened", icon=":material/headphones:", key=_key(title, "listen"), type="tertiary"):
        personal.log_listen(title)
        st.rerun()
    n = len(e["listens"])
    if n:
        info.caption(f"Listened {n} time{'s' if n > 1 else ''}, last on {max(e['listens'])}.")
        if info.button("Undo last listen", key=_key(title, "undo"), type="tertiary"):
            personal.undo_listen(title)
            st.rerun()
    note_key = _key(title, "note")
    with st.expander("My notes" + (" ·  saved" if e["note"] else ""), expanded=False):
        st.text_area("Notes", value=e["note"], key=note_key, label_visibility="collapsed",
                     placeholder="What this song means to you, where you heard it, what to listen for…",
                     on_change=_save_note, args=(title, note_key))
        st.caption("Saved on this computer only (data/personal/journal.json).")
