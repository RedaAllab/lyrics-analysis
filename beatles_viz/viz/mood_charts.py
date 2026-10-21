"""Figures about mood (word valence) and themes. No lyric text in any figure."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.config import ACCENT, PHASE_ORDER, REFERENCE, SECONDARY
from beatles_viz.corpus import THEME_PREFIX
from beatles_viz.viz.trend_charts import phase_strip
from beatles_viz.viz.theme import titled

LABELS = {"phase": "period", "voice": "voice"}


def theme_columns(corpus):
    return [c for c in corpus if c.startswith(THEME_PREFIX)]


def mood_over_time(corpus):
    return phase_strip(corpus.dropna(subset=["valence"]), "valence", "mood (−1 dark · +1 bright)",
                       "Mood of each song, period by period", zero_line=True)


def mood_methods(corpus):
    """Word-by-word mood against line-by-line mood: songs far from the diagonal are where negation or phrasing
    changes the reading."""
    d = corpus.dropna(subset=["valence", "valence_ctx"])
    fig = px.scatter(d, x="valence", y="valence_ctx", hover_name="title", color_discrete_sequence=[SECONDARY],
                     labels={"valence": "mood from single words", "valence_ctx": "mood line by line"})
    fig.add_shape(type="line", x0=-1, y0=-1, x1=1, y1=1, line=dict(color=REFERENCE, dash="dot"))
    fig.update_xaxes(range=[-1, 1], zeroline=False)
    fig.update_yaxes(range=[-1, 1], zeroline=False)
    return titled(fig, "Two readings of the mood", height=420)


def annotated_theme_heatmap(matrix, corpus, labels):
    """Share of annotated songs carrying each theme, per period. matrix: songs x themes (bool), by title."""
    phase = corpus.set_index("title").phase.reindex(matrix.index)
    g = matrix.groupby(phase.to_numpy()).mean().reindex([p for p in PHASE_ORDER if p in set(phase.dropna())])
    n = phase.value_counts()
    z = g.T.values
    fig = go.Figure(go.Heatmap(z=z, x=[f"{p} ({n.get(p, 0)})" for p in g.index], y=[labels.get(c, c) for c in g],
                               text=[[f"{v:.0%}" for v in row] for row in z], texttemplate="%{text}",
                               colorbar=dict(title="songs", tickformat=".0%"),
                               hovertemplate="%{y} · %{x}<br>%{z:.0%} of annotated songs<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    return titled(fig, "Annotated themes by period (annotated songs)", height=460)


def stanza_topic_heatmap(shares, topics):
    """shares: periods x topics (stanza_topic_shares); topics: topic, words. Topics named by their first words."""
    names = dict(zip(topics.topic, topics.words.str.split().str[:4].str.join(" ")))
    order = topics.topic.tolist()
    g = shares.reindex(index=[p for p in PHASE_ORDER if p in shares.index], columns=order).fillna(0)
    z = g.T.values
    fig = go.Figure(go.Heatmap(z=z, x=g.index.tolist(), y=[names.get(t, t) for t in g.columns],
                               text=[[f"{v:.0%}" for v in row] for row in z], texttemplate="%{text}",
                               colorbar=dict(title="stanzas", tickformat=".0%"),
                               hovertemplate="%{y} · %{x}<br>%{z:.0%} of the period's stanzas<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    return titled(fig, "Automatic stanza groups by period", height=140 + 28 * len(order))


def theme_heatmap(corpus, key, order):
    cols = theme_columns(corpus)
    g = corpus.groupby(key)[cols].mean().reindex([o for o in order if o in set(corpus[key])])
    z = g.T.values
    fig = go.Figure(go.Heatmap(z=z, x=g.index.tolist(), y=[c.removeprefix(THEME_PREFIX) for c in cols],
                               text=[[f"{v:.0f}" for v in row] for row in z],
                               texttemplate="%{text}", colorbar=dict(title="per 1,000"),
                               hovertemplate="%{y} · %{x}<br>%{z:.1f} theme words per 1,000<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    return titled(fig, f"Themes by {LABELS.get(key, key)}", height=420)


def song_themes(song, corpus):
    cols = theme_columns(corpus)
    ref = corpus[corpus.phase == song.phase] if song.phase else corpus
    rows = []
    for c in cols:
        label = c.removeprefix(THEME_PREFIX)
        rows.append(dict(theme=label, group="this song", rate=song[c]))
        rows.append(dict(theme=label, group=f"average {song.phase or 'corpus'}", rate=ref[c].mean()))
    fig = px.bar(pd.DataFrame(rows), x="rate", y="theme", color="group", barmode="group", orientation="h",
                 color_discrete_sequence=[ACCENT, REFERENCE], labels={"rate": "theme words per 1,000", "theme": ""})
    fig.update_yaxes(autorange="reversed")
    return titled(fig, "Themes", height=400)


def mood_words_figure(positive, negative):
    rows = [dict(word=w, weight=v) for w, v in positive + negative]
    if not rows:
        return None
    d = pd.DataFrame(rows).sort_values("weight")
    fig = go.Figure(go.Bar(x=d.weight, y=d.word, orientation="h",
                           marker_color=[ACCENT if v > 0 else SECONDARY for v in d.weight],
                           hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
    fig.update_xaxes(title="← darker · brighter → (occurrences × word valence)")
    return titled(fig, "Words that set the mood", height=max(260, 26 * len(d)))
