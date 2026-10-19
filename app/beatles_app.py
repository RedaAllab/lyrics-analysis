"""Interactive explorer for the Beatles lyrics vocabulary analysis.
Run:  streamlit run app/beatles_app.py
Shows statistics and word lists only (no lyrics text)."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from beatles_lib import PHASES, content_counter, load_public, merge, monroe, prior_from  # noqa: E402

st.set_page_config(page_title="Beatles lyrics explorer", layout="wide")

METRICS = {"Words per song": "tokens", "Distinct words per song": "types",
           "Lexical richness (MATTR-50)": "mattr", "Share of repeated lines": "repeat_ratio"}
SINGERS = ["Lennon", "McCartney", "Harrison", "Starr", "Shared"]


@st.cache_data(show_spinner="Loading corpus...")
def get_corpus(originals_only: bool) -> pd.DataFrame:
    return load_public(originals_only)


# ---------------- sidebar filters ----------------
st.sidebar.header("Corpus")
originals_only = st.sidebar.radio("Songs", ["Original compositions", "All (incl. covers)"]) == "Original compositions"
full = get_corpus(originals_only)
y0, y1 = int(full.year.min()), int(full.year.max())
years = st.sidebar.slider("Release year", y0, y1, (y0, min(y1, 1970)))
singers = st.sidebar.multiselect("Lead singer", sorted(full.singer.unique()), default=sorted(full.singer.unique()))
df = full[full.year.between(*years) & full.singer.isin(singers)].copy()
st.sidebar.caption(f"{len(df)} songs selected out of {len(full)}")
st.sidebar.caption("Lyrics: Genius dataset, not proofread. Years: original release year (Wikipedia list).")

st.title("The Beatles - lyrics vocabulary")
if df.empty:
    st.warning("No song matches the filters.")
    st.stop()

tab_over, tab_time, tab_words, tab_singer, tab_songs = st.tabs(
    ["Overview", "Evolution", "Characteristic words", "Lead singers", "Songs"])

# ---------------- overview ----------------
with tab_over:
    counts = merge(df.bow)
    hapax = sum(1 for n in counts.values() if n == 1)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Songs", len(df)); c2.metric("Words", f"{sum(counts.values()):,}")
    c3.metric("Distinct words", f"{len(counts):,}"); c4.metric("Used once", f"{hapax / len(counts):.0%}")
    c5.metric("Repeated lines", f"{df.repeat_ratio.mean():.0%}")
    n = st.slider("Number of words shown", 10, 60, 25)
    top = pd.DataFrame(content_counter(counts).most_common(n), columns=["word", "count"])
    st.plotly_chart(px.bar(top[::-1], x="count", y="word", orientation="h", height=max(350, 18 * n),
                           title="Most frequent words (stop words, syllables and names removed)"), use_container_width=True)
    ordered = df.sort_values(["year", "title"]); seen, growth = set(), []
    for ws in ordered.bow:
        seen |= set(ws); growth.append(len(seen))
    g = pd.DataFrame({"song #": range(1, len(growth) + 1), "distinct words": growth, "title": ordered.title.values, "year": ordered.year.values})
    st.plotly_chart(px.line(g, x="song #", y="distinct words", hover_data=["title", "year"], title="Vocabulary growth (chronological order)"), use_container_width=True)

# ---------------- evolution ----------------
with tab_time:
    by = st.radio("Group by", ["Year", "Period"], horizontal=True)
    key = "year" if by == "Year" else "phase"
    d = df if by == "Year" else df[df.phase.notna()]
    order = None if by == "Year" else [p for p, _, _ in PHASES]
    metric_label = st.selectbox("Metric", list(METRICS))
    col = METRICS[metric_label]
    agg = d.groupby(key).agg(value=(col, "mean"), songs=("title", "count")).reset_index()
    if order:
        agg[key] = pd.Categorical(agg[key], order, ordered=True); agg = agg.sort_values(key)
    fig = px.line(agg, x=key, y="value", markers=True, hover_data=["songs"], title=f"{metric_label} by {by.lower()}")
    fig.update_yaxes(title=metric_label)
    st.plotly_chart(fig, use_container_width=True)
    if (agg.songs < 5).any():
        st.caption("Some groups have fewer than 5 songs: read those points with caution.")
    st.subheader("Word frequency over time")
    default = ["love", "i", "you", "we", "yeah"]
    raw = st.text_input("Words (comma separated)", ", ".join(default))
    watch = [w.strip().lower() for w in raw.split(",") if w.strip()]
    rows = []
    for k, grp in d.groupby(key):
        c = merge(grp.bow); tot = sum(c.values())
        for w in watch:
            rows.append({key: k, "word": w, "per 1000 words": 1000 * c[w] / tot, "occurrences": c[w]})
    if rows:
        tr = pd.DataFrame(rows)
        if order:
            tr[key] = pd.Categorical(tr[key], order, ordered=True); tr = tr.sort_values(key)
        st.plotly_chart(px.line(tr, x=key, y="per 1000 words", color="word", markers=True, hover_data=["occurrences"]), use_container_width=True)

# ---------------- characteristic words ----------------
with tab_words:
    st.caption("Words over-represented in a group compared with the rest of the selection "
               "(log-odds z-score with informative prior, Monroe et al. 2008). Words seen fewer than 5 times are ignored.")
    n_words = st.slider("Words per group", 5, 25, 10, key="n_dist")
    d = df[df.phase.notna()]
    _, prior = prior_from(d)
    cols = st.columns(len(PHASES))
    for colw, (p, _, _) in zip(cols, PHASES):
        grp = d[d.phase == p]
        if grp.empty or len(grp) == len(d):
            colw.caption(f"{p}: no data"); continue
        a = content_counter(merge(grp.bow)); b = content_counter(merge(d[d.phase != p].bow))
        r = monroe(a, b, prior).head(n_words)
        colw.markdown(f"**{p}** ({len(grp)} songs)")
        colw.dataframe(r[["word", "in_group", "z"]].round(1).reset_index(drop=True), hide_index=True, use_container_width=True)

# ---------------- singers ----------------
with tab_singer:
    sg = df.groupby("singer").agg(songs=("title", "count"), words=("tokens", "mean"), distinct=("types", "mean"),
                                  mattr=("mattr", "mean"), repeats=("repeat_ratio", "mean")).round(3)
    st.dataframe(sg.reindex([s for s in SINGERS if s in sg.index]), use_container_width=True)
    m = st.selectbox("Metric", list(METRICS), key="sing_metric")
    st.plotly_chart(px.box(df, x="singer", y=METRICS[m], points="all", hover_data=["title", "year"],
                           category_orders={"singer": SINGERS}), use_container_width=True)
    st.caption("Songs credited to Lennon-McCartney: the lead singer is used as a proxy, not the actual writer.")
    main = [s for s in ["Lennon", "McCartney", "Harrison"] if (df.singer == s).sum() >= 5]
    if len(main) >= 2:
        _, prior_s = prior_from(df)
        cols = st.columns(len(main))
        for colw, s in zip(cols, main):
            a = content_counter(merge(df[df.singer == s].bow)); b = content_counter(merge(df[df.singer != s].bow))
            colw.markdown(f"**{s}**")
            colw.dataframe(monroe(a, b, prior_s).head(10)[["word", "in_group", "z"]].round(1).reset_index(drop=True), hide_index=True, use_container_width=True)

# ---------------- songs ----------------
with tab_songs:
    q = st.text_input("Find songs containing the word", "").strip().lower()
    t = df[["title", "year", "release_core", "singer", "tokens", "types", "mattr", "repeat_ratio"]].copy()
    if q:
        t["occurrences"] = df.bow.map(lambda c: c.get(q, 0))
        t = t[t.occurrences > 0].sort_values("occurrences", ascending=False)
        st.caption(f"{len(t)} songs contain '{q}' ({int(t.occurrences.sum())} occurrences).")
    else:
        t = t.sort_values(["year", "title"])
    st.dataframe(t.round(3), hide_index=True, use_container_width=True)
