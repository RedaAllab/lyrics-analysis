"""The whole catalogue: vocabulary, evolution over time, voices and the song table. Statistics only, no lyrics."""
import pandas as pd
import plotly.express as px
import streamlit as st

from beatles_viz.config import ACCENT, PHASES, PHASE_ORDER, VOICE_COLORS, VOICE_ORDER
from beatles_viz.corpus import analysable
from beatles_viz.data.loader import data_source
from beatles_viz.render.components import (HELP, apply_filters, cached_corpus, corpus_filters, open_song, open_word,
                                           plot)
from beatles_viz.text.keyness import monroe, prior
from beatles_viz.text.tokenize import content_counter, merge

METRICS = {"Words per song": "tokens", "Distinct words per song": "types",
           "Lexical richness (MATTR-50)": "mattr", "Share of repeated lines": "repeat_ratio"}
SINGERS = VOICE_ORDER
LOG_METRICS = {"tokens", "types"}  # a few very long songs would squash every other box
WORD_TABLE = {"word": st.column_config.TextColumn("Word"),
              "in_group": st.column_config.NumberColumn("Occurrences", format="%d"),
              "z": st.column_config.ProgressColumn("Distinctiveness", format="%.1f", min_value=0, max_value=15,
                                                   help=HELP["z"])}
SONG_TABLE = {"title": "Title", "year": st.column_config.NumberColumn("Year", format="%d"),
              "release_core": "Release", "voice": "Lead voice",
              "tokens": st.column_config.NumberColumn("Words", format="%d"),
              "types": st.column_config.NumberColumn("Distinct words", format="%d"),
              "mattr": st.column_config.NumberColumn("Lexical richness", format="%.2f", help=HELP["mattr"]),
              "repeats": st.column_config.NumberColumn("Repeated lines", format="%.0f%%", help=HELP["repeats"]),
              "occurrences": st.column_config.NumberColumn("Occurrences", format="%d"),
              "repetition_score": st.column_config.NumberColumn("Repetition score", format="%.3f",
                                                                help=HELP["repetition"])}


def word_table(container, table, key):
    """Characteristic words; selecting one opens its Word page."""
    sel = container.dataframe(table, hide_index=True, width="stretch", column_config=WORD_TABLE,
                              on_select="rerun", selection_mode="single-row", key=key)
    if sel.selection.rows:
        open_word(table.iloc[sel.selection.rows[0]]["word"])


def prior_from(d):
    return prior(content_counter(merge(d.bow)))


# ---------------- sidebar filters ----------------
corpus = analysable(cached_corpus(data_source()), originals_only=False)
originals_only, years, voices = corpus_filters(int(corpus.year.min()), int(corpus.year.max()))
full = corpus[corpus.is_original] if originals_only else corpus
df = apply_filters(full, False, years, voices).copy()
st.sidebar.caption(f"{len(df)} songs selected out of {len(full)}")
st.sidebar.caption("Lyrics: Genius dataset, not proofread. Years: original release year (Wikipedia list).")

st.title("The Beatles: lyrics vocabulary")
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
    c3.metric("Distinct words", f"{len(counts):,}")
    c4.metric("Words used once", f"{hapax / len(counts):.0%}", help=HELP["used_once"])
    c5.metric("Repeated lines", f"{df.repeat_ratio.mean():.0%}", help=HELP["repeats"])
    n = st.slider("Number of words shown", 10, 60, 25)
    top = pd.DataFrame(content_counter(counts).most_common(n), columns=["word", "count"])
    plot(px.bar(top[::-1], x="count", y="word", orientation="h", height=max(350, 18 * n),
                color_discrete_sequence=[ACCENT], labels={"count": "occurrences", "word": ""},
                title="Most frequent words (stop words, syllables and names removed)"))
    ordered = df.sort_values(["year", "title"]); seen, growth = set(), []
    for ws in ordered.bow:
        seen |= set(ws); growth.append(len(seen))
    g = pd.DataFrame({"song #": range(1, len(growth) + 1), "distinct words": growth, "title": ordered.title.values, "year": ordered.year.values})
    plot(px.line(g, x="song #", y="distinct words", hover_data=["title", "year"], color_discrete_sequence=[ACCENT],
                 title="How the vocabulary grows, song after song"))

# ---------------- evolution ----------------
with tab_time:
    by = st.radio("Group by", ["Year", "Period"], horizontal=True)
    key = "year" if by == "Year" else "phase"
    d = df if by == "Year" else df[df.phase.notna()]
    order = None if by == "Year" else PHASE_ORDER
    metric_label = st.selectbox("Metric", list(METRICS))
    col = METRICS[metric_label]
    agg = d.groupby(key).agg(value=(col, "mean"), songs=("title", "count")).reset_index()
    if order:
        agg[key] = pd.Categorical(agg[key], order, ordered=True); agg = agg.sort_values(key)
    fig = px.line(agg, x=key, y="value", markers=True, hover_data=["songs"], color_discrete_sequence=[ACCENT],
                  title=f"{metric_label} by {by.lower()}")
    fig.update_yaxes(title=metric_label)
    fig.update_xaxes(title="")
    plot(fig)
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
        fig = px.line(tr, x=key, y="per 1000 words", color="word", markers=True, hover_data=["occurrences"])
        fig.update_xaxes(title="")
        plot(fig)

# ---------------- characteristic words ----------------
with tab_words:
    st.caption("Words used much more in a period than in the rest of the selection (log-odds z-score, "
               "Monroe et al. 2008). Words seen fewer than 5 times are ignored. Select a word to open its page.")
    n_words = st.slider("Words per group", 5, 25, 10, key="n_dist")
    d = df[df.phase.notna()]
    phase_prior = prior_from(d)
    cols = st.columns(len(PHASES))
    for colw, (p, _, _) in zip(cols, PHASES):
        grp = d[d.phase == p]
        if grp.empty or len(grp) == len(d):
            colw.caption(f"{p}: no data"); continue
        a = content_counter(merge(grp.bow)); b = content_counter(merge(d[d.phase != p].bow))
        r = monroe(a, b, phase_prior).head(n_words)
        colw.markdown(f"**{p}** ({len(grp)} songs)")
        word_table(colw, r[["word", "in_group", "z"]].reset_index(drop=True), f"phase_words_{p}")

# ---------------- singers ----------------
with tab_singer:
    sg = df.groupby("voice").agg(songs=("title", "count"), tokens=("tokens", "mean"), types=("types", "mean"),
                                  mattr=("mattr", "mean"), repeats=("repeat_ratio", "mean"))
    sg["repeats"] *= 100
    sg = sg.reindex([s for s in SINGERS if s in sg.index]).rename_axis("voice").reset_index()
    st.dataframe(sg, hide_index=True, width="stretch",
                 column_config={**SONG_TABLE, "songs": st.column_config.NumberColumn("Songs", format="%d"),
                                "tokens": st.column_config.NumberColumn("Words (mean)", format="%.0f"),
                                "types": st.column_config.NumberColumn("Distinct words (mean)", format="%.0f")})
    m = st.selectbox("Metric", list(METRICS), key="sing_metric")
    log = METRICS[m] in LOG_METRICS
    fig = px.box(df, x="voice", y=METRICS[m], points="all", hover_data=["title", "year"], color="voice",
                 color_discrete_map=VOICE_COLORS, category_orders={"voice": SINGERS}, log_y=log,
                 labels={"voice": "", METRICS[m]: m + (" (log scale)" if log else "")})
    fig.update_layout(showlegend=False)
    plot(fig)
    st.caption("Songs credited to Lennon-McCartney: the lead singer is used as a proxy, not the actual writer.")
    main = [s for s in ["Lennon", "McCartney", "Harrison"] if (df.voice == s).sum() >= 5]
    if len(main) >= 2:
        prior_s = prior_from(df)
        cols = st.columns(len(main))
        for colw, s in zip(cols, main):
            a = content_counter(merge(df[df.voice == s].bow)); b = content_counter(merge(df[df.voice != s].bow))
            colw.markdown(f"**{s}**")
            word_table(colw, monroe(a, b, prior_s).head(10)[["word", "in_group", "z"]].reset_index(drop=True),
                       f"singer_words_{s}")

# ---------------- songs ----------------
with tab_songs:
    q = st.text_input("Find songs containing the word", "").strip().lower()
    t = df[["title", "year", "release_core", "voice", "tokens", "types", "mattr", "repetition_score"]].copy()
    t["repeats"] = df.repeat_ratio * 100
    if q:
        t["occurrences"] = df.bow.map(lambda c: c.get(q, 0))
        t = t[t.occurrences > 0].sort_values("occurrences", ascending=False)
        st.caption(f"{len(t)} songs contain '{q}' ({int(t.occurrences.sum())} occurrences).")
    else:
        t = t.sort_values(["year", "title"])
    st.caption("Select a row to open the song.")
    picked = st.dataframe(t, hide_index=True, width="stretch", column_config=SONG_TABLE,
                          on_select="rerun", selection_mode="single-row", key="songs_table")
    if picked.selection.rows:
        open_song(t.iloc[picked.selection.rows[0]]["title"])
