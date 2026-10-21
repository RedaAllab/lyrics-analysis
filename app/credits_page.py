"""Who wrote, sang and played: the sourced credit tables (data/credits), no lyrics."""
import streamlit as st

from beatles_viz.config import MEMBERS, PHASE_ORDER
from beatles_viz.credits import instruments, lead_vocal_conflicts, load_table, outside_musicians
from beatles_viz.data.loader import data_source
from beatles_viz.render.components import cached_corpus, evidence, plot, song_table
from beatles_viz.render.identity import kicker
from beatles_viz.viz import credit_charts as cc


@st.cache_data(show_spinner="Reading the credits...")
def tables():
    return {name: load_table(name) for name in ("performance_credit", "person", "work_credit", "source", "recording")}


t = tables()
corpus = cached_corpus(data_source())
kicker("Credits · every row with its source")
st.markdown("## Who wrote, sang and played")
if t["performance_credit"].empty:
    st.info("The credit tables are not built: run scripts/fetch_credits.py, then scripts/build_credits.py.")
    st.stop()

perf, people = t["performance_credit"], t["person"]
inst = instruments(perf)
credited = corpus[corpus.title.isin(set(inst.title))]
conflicts = lead_vocal_conflicts(perf)
c = st.columns(3)
c[0].metric("Songs with players credited", f"{credited.title.nunique()} of {len(corpus)}")
c[1].metric("People credited", len(people))
c[2].metric("Lead vocal disagreements", len(conflicts), help="Songs where the official list and MusicBrainz name "
            "different lead singers.")

st.subheader("What does each Beatle play?")
member = st.segmented_control("Member", MEMBERS, default=MEMBERS[0], key="credits_member") or MEMBERS[0]
shares, per_phase = cc.family_shares(inst, credited)
fig = cc.member_instruments(shares, per_phase, member)
if fig is None:
    st.info("No instrument credited to this member.")
else:
    plot(fig)
evidence("descriptive")
st.caption("MusicBrainz recording credits for the original editions (CC0, retrieved "
           f"{t['source'].set_index('source_id').accessed.get('musicbrainz', '')}). Share of the period's credited "
           "songs where the member plays an instrument of the family; the count of songs is in brackets. Original "
           "compositions and covers alike. MusicBrainz is collaborative and cites no source per credit: medium "
           "confidence.")

st.subheader("Who else plays and sings?")
others = outside_musicians(perf, people)
st.dataframe(others.head(30), hide_index=True, width="stretch",
             column_config={"person": "Person", "songs": st.column_config.NumberColumn("Songs", format="%d"),
                            "titles": st.column_config.TextColumn("Songs", width="large")})
evidence("descriptive")
st.caption("Musicians and singers other than the four, from the same credits. Producers and engineers are left out.")

st.subheader("Who is credited, who sings?")
period = st.segmented_control("Period", ["All", *PHASE_ORDER], default="All", key="credits_period") or "All"
plot(cc.credit_voice_figure(corpus, None if period == "All" else period))
evidence("validate")
st.caption("Official credit from the song list; “Lennon–McCartney” names both, whoever wrote the song. The lead voice "
           "is not the writer: reading McCartney-sung songs as McCartney-written is a guess that needs documented "
           "sources (data/credits/manual_claims.csv), song by song.")

st.subheader("Where the sources disagree on the lead singer")
if conflicts.empty:
    st.info("No disagreement.")
else:
    names = dict(zip(people.person_id, people.name))
    show = conflicts.rename(columns={"musicbrainz": "MusicBrainz", "wikipedia_song_list": "Official list"})
    for col in ("MusicBrainz", "Official list"):
        if col in show:
            show[col] = show[col].map(lambda s: ", ".join(names.get(p, p) for p in str(s).split("; ")))
    song_table(show, "credits_conflicts", {"title": "Title"})
evidence("descriptive")
st.caption("Both are kept: the list gives one lead per song without saying which version; MusicBrainz credits the "
           "original recording part by part (a verse sung by another member counts as a lead vocal).")

claims = t["work_credit"][t["work_credit"].kind != "official"]
st.subheader("Documented contributions and interpretations")
if claims.empty:
    st.info("None entered yet.")
else:
    citations = dict(zip(t["source"].source_id, t["source"].citation))
    for row in claims.itertuples():
        st.markdown(f"- **{row.title}**: {row.person_id.capitalize()}, {row.role.replace('_', ' ')} "
                    f"(*{row.kind}*, confidence {row.confidence}). {row.note} — {citations.get(row.source_id, '')}")
st.caption("Typed by hand from books, interviews and studies, one row per source (data/credits/manual_claims.csv). "
           "Few so far: who wrote what in a Lennon–McCartney song is only shown when a source says so.")
