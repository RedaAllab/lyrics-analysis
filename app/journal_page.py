"""Your journal: favourites, ratings, notes and listening history. Local only (data/personal/journal.json)."""
import plotly.express as px
import streamlit as st

from beatles_viz import personal
from beatles_viz.config import ACCENT
from beatles_viz.data.loader import data_source
from beatles_viz.render.components import cached_corpus, open_song, plot
from beatles_viz.render.identity import kicker

kicker("Only on this computer")
st.markdown("## My songs")
if not personal.enabled():
    st.info("The journal lives on your own computer, next to the lyrics file: it is not part of the deployed app.")
    st.stop()

journal = personal.load()
table = personal.journal_frame(journal, cached_corpus(data_source()))
if table.empty:
    st.info("Nothing yet. On a song page, star it, rate it, write a note or press “I listened”.")
    st.stop()

c = st.columns(4)
c[0].metric("Favourites", int(table.favourite.sum()))
c[1].metric("Songs listened", int((table.listens > 0).sum()))
c[2].metric("Listens", int(table.listens.sum()))
c[3].metric("Notes", int((table.note.str.len() > 0).sum()))

show = st.radio("Show", ["Everything", "Favourites", "With notes", "Most listened"], horizontal=True,
                key="journal_show")
t = table
if show == "Favourites":
    t = t[t.favourite]
elif show == "With notes":
    t = t[t.note.str.len() > 0]
elif show == "Most listened":
    t = t[t.listens > 0].sort_values("listens", ascending=False)
else:
    t = t.sort_values(["last_listen", "title"], ascending=[False, True], na_position="last")
t = t.reset_index(drop=True)
st.caption("Select a row to open the song.")
picked = st.dataframe(
    t[["title", "year", "voice", "favourite", "rating", "listens", "last_listen", "note"]], hide_index=True,
    width="stretch", on_select="rerun", selection_mode="single-row", key="journal_table",
    column_config={"title": "Title", "year": st.column_config.NumberColumn("Year", format="%d"),
                   "voice": "Lead voice", "favourite": st.column_config.CheckboxColumn("★"),
                   "rating": st.column_config.NumberColumn("Rating", format="%d / 5"),
                   "listens": st.column_config.NumberColumn("Listens", format="%d"),
                   "last_listen": "Last listened", "note": st.column_config.TextColumn("Note", width="large")})
if picked.selection.rows:
    open_song(t.iloc[picked.selection.rows[0]]["title"])

months = personal.listens_by_month(journal)
if not months.empty:
    plot(px.bar(months, x="month", y="listens", color_discrete_sequence=[ACCENT], title="Listens by month",
                labels={"month": "", "listens": "listens"}))
