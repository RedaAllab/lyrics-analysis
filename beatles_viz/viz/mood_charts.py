"""Figures about mood (word valence) and themes. No lyric text in any figure."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.config import ACCENT
from beatles_viz.corpus import THEME_PREFIX
from beatles_viz.viz.trend_charts import phase_strip
from beatles_viz.viz.theme import titled

LABELS = {"phase": "period", "voice": "voice"}


def theme_columns(corpus):
    return [c for c in corpus if c.startswith(THEME_PREFIX)]


def mood_over_time(corpus):
    return phase_strip(corpus.dropna(subset=["valence"]), "valence", "mood (−1 dark · +1 bright)",
                       "Mood of each song, period by period", zero_line=True)


def theme_heatmap(corpus, key, order):
    cols = theme_columns(corpus)
    g = corpus.groupby(key)[cols].mean().reindex([o for o in order if o in set(corpus[key])])
    z = g.T.values
    fig = go.Figure(go.Heatmap(z=z, x=g.index.tolist(), y=[c.removeprefix(THEME_PREFIX) for c in cols],
                               colorscale="Oranges", text=[[f"{v:.0f}" for v in row] for row in z],
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
                 color_discrete_sequence=[ACCENT, "#7a8794"], labels={"rate": "theme words per 1,000", "theme": ""})
    fig.update_yaxes(autorange="reversed")
    return titled(fig, "Themes", height=400)


def mood_words_figure(positive, negative):
    rows = [dict(word=w, weight=v) for w, v in positive + negative]
    if not rows:
        return None
    d = pd.DataFrame(rows).sort_values("weight")
    fig = go.Figure(go.Bar(x=d.weight, y=d.word, orientation="h",
                           marker_color=[ACCENT if v > 0 else "#3a6ea5" for v in d.weight],
                           hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
    fig.update_xaxes(title="← darker · brighter → (occurrences × word valence)")
    return titled(fig, "Words that set the mood", height=max(260, 26 * len(d)))
