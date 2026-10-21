"""Hand annotation of themes with the codebook. Local only: it shows the lyrics and writes data/themes/annotations.csv.
The model's suggestions stay hidden until the song is annotated, so they cannot steer the choice."""
import pandas as pd
import streamlit as st

from beatles_viz import themes as T
from beatles_viz.corpus import analysable
from beatles_viz.data.loader import data_source, has_lyrics
from beatles_viz.render.components import cached_corpus
from beatles_viz.render.identity import kicker
from beatles_viz.text.sections import section_name

kicker("Only on this computer")
st.markdown("## Annotate themes")
if not has_lyrics():
    st.info("Annotating needs the lyrics, which stay on your own computer: this page is not part of the deployed app.")
    st.stop()

codebook = T.load_codebook()
labels = dict(zip(codebook.theme, codebook.label))
songs = analysable(cached_corpus(data_source())).sort_values(["year", "title"])
annotator = st.text_input("Annotator", key="annotator", help="Your name or initials: each person's annotations are "
                          "kept apart, so agreement between people can be measured.").strip()
if not annotator:
    st.info("Type a name or initials to start.")
    st.stop()

done = set(T.load_annotations().query("annotator == @annotator").title)
st.progress(len(done & set(songs.title)) / len(songs),
            text=f"{len(done & set(songs.title))} of {len(songs)} original compositions annotated by {annotator}")
todo = [t for t in songs.title if t not in done]
only_todo = st.toggle("Only songs not annotated yet", value=bool(todo), key="annotate_todo")
choices = todo if only_todo and todo else songs.title.tolist()
title = st.selectbox("Song", choices, key="annotate_song")
song = songs[songs.title == title].iloc[0]

with st.expander("Codebook", expanded=not done):
    st.dataframe(codebook.drop(columns="theme"), hide_index=True, width="stretch")

left, right = st.columns([3, 2])
with left:
    st.markdown(f"#### {title}")
    st.caption(f"{int(song.year)} · {song.album} · credited to {song.writer_credit} · lead {song.lead_vocal}")
    for s in song.sections:
        if s.lines:
            st.markdown(f"**{section_name(s)}**" + (f" ×{s.repeat}" if s.repeat > 1 else ""))
            st.text("\n".join(s.lines))

with right:
    previous = T.load_annotations().query("annotator == @annotator and title == @title")
    prev = previous.iloc[0] if len(previous) else None
    with st.form(f"annotate_{title}"):
        picked = st.multiselect("Themes", list(labels), format_func=labels.get,
                                default=T.theme_list(prev.themes) if prev is not None else [],
                                help="Every theme the song really develops, not one passing word.")
        main = st.selectbox("Main theme", [""] + list(labels), format_func=lambda t: labels.get(t, "—"),
                            index=([""] + list(labels)).index(prev.main_theme) if prev is not None else 0)
        implicit = st.checkbox("The literal meaning differs from the implied one (irony, double meaning, metaphor)",
                               value=bool(prev.implicit) if prev is not None else False)
        note = st.text_area("Note", value=prev.note if prev is not None else "",
                            help="Why, doubts, the line that decided it (no need to copy it).")
        if st.form_submit_button("Save", type="primary"):
            try:
                T.save_annotation(title, annotator, picked, main if main in picked else "", implicit, note,
                                  codebook=codebook)
                st.success("Saved.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    if title in done and T.SUGGESTIONS_PATH.exists():
        with st.expander("Model suggestions (after your choice)"):
            sug = pd.read_csv(T.SUGGESTIONS_PATH).query("title == @title").sort_values("rank").head(4)
            st.dataframe(sug.assign(theme=sug.theme.map(labels))[["theme", "score"]], hide_index=True,
                         width="stretch")
            st.caption("Closeness of the song's two nearest stanzas to each theme's description (sentence "
                       "transformer). A hint, often wrong on irony and metaphor: your annotation is the reference.")
