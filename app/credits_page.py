"""Who wrote, sang and played: the sourced credit tables (data/credits), no lyrics."""
import streamlit as st

from beatles_viz.config import MEMBERS, PHASE_ORDER, ROOT
from beatles_viz.credits import (authorship_summary, instruments, lead_vocal_conflicts, load_table,
                                 outside_musicians)
from beatles_viz.data.loader import data_source
from beatles_viz.render.components import cached_corpus, evidence, plot, song_table
from beatles_viz.render.identity import kicker
from beatles_viz.viz import credit_charts as cc


@st.cache_data(show_spinner="Reading the credits...")
def tables():
    tables = ("performance_credit", "person", "work_credit", "source", "recording")
    out = {name: load_table(name) for name in tables}
    out["agreement"] = load_table("", ROOT / "analysis/credits/source_agreement.csv")
    out["disagreements"] = load_table("", ROOT / "analysis/credits/source_disagreements.csv")
    return out


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
c[2].metric("Lead vocal disagreements", len(conflicts), help="Songs where two sources (official list, MusicBrainz, "
            "Wikipedia song and album articles) name different lead singers.")

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
    cols = {"musicbrainz": "MusicBrainz", "wikipedia_song_list": "Official list",
            "wikipedia_song_page": "Song article", "wikipedia_album_page": "Album article"}
    show = conflicts.rename(columns=cols)
    for col in cols.values():
        if col in show:
            show[col] = show[col].map(lambda s: ", ".join(names.get(p, p) for p in str(s).split("; ")))
    song_table(show, "credits_conflicts", {"title": "Title"})
evidence("descriptive")
st.caption("All are kept: the list gives one lead per song without saying which version; MusicBrainz credits the "
           "original recording part by part (a verse sung by another member counts as a lead vocal); the Wikipedia "
           "articles follow the books they cite. An empty cell: that source says nothing about the song.")

st.subheader("Wikipedia against MusicBrainz, part by part")
agree, dis = t["agreement"], t["disagreements"]
if agree.empty:
    st.info("Not compared yet: run scripts/fetch_wikipedia_credits.py, then scripts/build_credits.py.")
else:
    song_level = agree[agree.wikipedia == "wikipedia_song_page"].drop(columns="wikipedia")
    st.dataframe(song_level, hide_index=True, width="stretch", column_config={
        "aspect": "Part", "both": "Both sources", "only_musicbrainz": "Only MusicBrainz",
        "only_wikipedia": "Only Wikipedia", "agreed": st.column_config.ProgressColumn("Agreement", format="%.2f")})
    evidence("descriptive")
    st.caption("For each song both credit, every (person, part) pair one source names: a part is the lead or backing "
               "vocal, or an instrument family. Wikipedia here is the Personnel section of the song's own article, "
               "which cites its books (Lewisohn, MacDonald, Everett...); archival recordings are left out, since the "
               "article and MusicBrainz may not describe the same take.")
    d = dis[~dis.archival.astype(str).eq("True")]
    part = st.selectbox("Disagreements on", ["All", *song_level.aspect], key="credits_part")
    d = d if part == "All" else d[d.aspect == part]
    names = dict(zip(people.person_id, people.name))
    d = d.assign(person=d.person_id.map(lambda p: names.get(p, p)),
                 says=d.musicbrainz.astype(str).map({"True": "MusicBrainz only", "False": "Wikipedia only"}),
                 article=d.wikipedia.map({"wikipedia_song_page": "song", "wikipedia_album_page": "album"}))
    song_table(d[["title", "person", "aspect", "says", "article", "wikipedia_note"]], "credits_disagreements",
               {"title": "Title", "person": "Person", "aspect": "Part", "says": "Named by", "article": "Article",
                "wikipedia_note": "Wikipedia page and works cited"})
    st.caption("A credit only one source gives is not wrong for that: MusicBrainz often lists every orchestral player "
               "by name, Wikipedia often says “uncredited”; two singers sharing the lead count as two leads in "
               "MusicBrainz, as lead and harmony in many articles. Check the cited book before correcting either.")

claims = t["work_credit"][t["work_credit"].kind != "official"]
st.subheader("Who wrote what, according to the sources")
if claims.empty:
    st.info("None entered yet.")
else:
    summary = authorship_summary(t["work_credit"], people)
    c = st.columns(3)
    c[0].metric("Songs with documented claims", len(summary))
    c[1].metric("Claims", len(claims))
    c[2].metric("Songs where accounts differ", int(summary.accounts_differ.sum()))
    only_differ = st.toggle("Only songs where the accounts differ", key="credits_differ")
    song_table(summary[summary.accounts_differ] if only_differ else summary, "credits_authorship",
               {"title": "Title", "main": "Main writer", "co": "Co-writer", "parts": "Also contributed",
                "claims": "Claims", "accounts_differ": "Accounts differ"})
    title = st.selectbox("Claims for one song", summary.title, key="credits_claims_song")
    one = claims[claims.title == title]
    names = dict(zip(people.person_id, people.name))
    st.dataframe(one.assign(person=one.person_id.map(lambda p: names.get(p, p.replace("_", " ").title())),
                            role=one.role.str.replace("_", " "))[
                     ["person", "role", "detail", "kind", "confidence", "source_id", "note"]],
                 hide_index=True, width="stretch",
                 column_config={"person": "Person", "role": "Role", "detail": "Detail", "kind": "Kind",
                                "confidence": "Confidence", "source_id": "Source",
                                "note": st.column_config.TextColumn("Page, revision and works cited", width="large")})
evidence("exploratory")
st.caption("Sentences of the Wikipedia song and album articles that say who wrote what were read by a model "
           "(claude-opus-5.5) and turned into one row per claim, with the article's revision and the works it cites "
           "(data/credits/wikipedia_claims.csv); claims typed by hand from books are in manual_claims.csv. Testimony "
           "is documented, an author's reading is an interpretation; a claim with no citation on its sentence, or "
           "contradicted elsewhere, has low confidence. “Lennon–McCartney” stays the official credit of both: these "
           "rows are to be checked against the cited books before any analysis leans on them.")
