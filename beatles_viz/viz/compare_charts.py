"""Figures comparing two songs. No lyric text in any figure."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.text.keyness import monroe, prior
from beatles_viz.text.tokenize import content_counter
from beatles_viz.viz.song_charts import HIGHLIGHT_COLORS, PRONOUN_LABELS, _layout

PROFILE = {"tokens": "Words", "types": "Distinct words", "mattr": "Lexical richness", "repeat_ratio": "Repeated lines"}


def percentile_profile(a, b, corpus):
    """Each metric as a percentile of the corpus, so scales with different units sit on one axis."""
    rows = []
    for col, label in PROFILE.items():
        ref = corpus[col].dropna()
        for song in (a, b):
            value = song[col]
            pct = None if pd.isna(value) else 100 * (ref < value).mean()
            rows.append(dict(metric=label, song=song.title, percentile=pct))
    fig = px.bar(pd.DataFrame(rows), x="percentile", y="metric", color="song", barmode="group", orientation="h",
                 color_discrete_sequence=HIGHLIGHT_COLORS, range_x=[0, 100],
                 labels={"percentile": "percentile among all songs", "metric": ""},
                 category_orders={"metric": list(PROFILE.values())})
    fig.add_vline(x=50, line=dict(color="#888888", dash="dot", width=1))
    return _layout(fig, "Where each song stands in the corpus", height=330)


def word_contrast(a, b, top=8):
    """Words most typical of one song against the other: A to the right, B to the left."""
    ca, cb = content_counter(a.bow), content_counter(b.bow)
    r = monroe(ca, cb, prior(ca + cb), min_count=2)
    if r.empty:
        return None
    side = pd.concat([r.head(top).assign(song=a.title), r.tail(top).assign(song=b.title)])
    side = side[(side.song == a.title) & (side.z > 0) | (side.song == b.title) & (side.z < 0)]
    if side.empty:
        return None
    side = side.drop_duplicates("word").sort_values("z")
    fig = go.Figure(go.Bar(x=side.z, y=side.word, orientation="h",
                           marker_color=[HIGHLIGHT_COLORS[0] if s == a.title else HIGHLIGHT_COLORS[1] for s in side.song],
                           customdata=side[["song", "in_group", "in_rest"]],
                           hovertemplate="%{y}<br>%{customdata[1]} in A, %{customdata[2]} in B<extra></extra>"))
    fig.update_xaxes(title=f"← more in {b.title}   ·   more in {a.title} →")
    return _layout(fig, "Words that tell the two songs apart", height=max(300, 26 * len(side)))


def pronoun_pair(a, b):
    rows = [dict(pronoun=label, song=s.title, share=100 * s[key]) for key, label in PRONOUN_LABELS.items()
            for s in (a, b)]
    fig = px.bar(pd.DataFrame(rows), x="pronoun", y="share", color="song", barmode="group",
                 color_discrete_sequence=HIGHLIGHT_COLORS, labels={"share": "per 100 words", "pronoun": ""})
    return _layout(fig, "Point of view: personal pronouns", height=320)


def shared_vocabulary(a, b):
    ca, cb = set(content_counter(a.bow)), set(content_counter(b.bow))
    union = ca | cb
    return {"shared": len(ca & cb), "only_a": len(ca - cb), "only_b": len(cb - ca),
            "overlap": len(ca & cb) / len(union) if union else 0.0}
