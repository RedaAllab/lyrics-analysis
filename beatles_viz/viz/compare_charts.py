"""Figures comparing two songs. No lyric text in any figure."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.text.keyness import contrast
from beatles_viz.text.tokenize import content_counter
from beatles_viz.viz.song_charts import HIGHLIGHT_COLORS, PRONOUN_LABELS, _layout

PROFILE = {"tokens": "Words", "types": "Distinct words", "mattr": "Lexical richness", "repeat_ratio": "Repeated lines",
           "repetition_score": "Repetition score"}


def percentile_profile(a, b, corpus):
    """Each metric as a percentile of the corpus, so scales with different units sit on one axis."""
    rows = []
    for col, label in PROFILE.items():
        if col not in corpus:
            continue
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


def contrast_words(ca, cb, top=8, min_count=2):
    """The words most typical of A (z > 0) and of B (z < 0), strongest last."""
    r = contrast(ca, cb, min_count=min_count)
    if r.empty:
        return r
    side = pd.concat([r.head(top), r.tail(top)]).drop_duplicates("word")
    return side[side.z != 0].sort_values("z")


def contrast_figure(ca, cb, label_a, label_b, colors=HIGHLIGHT_COLORS, top=8, min_count=2,
                    title="Words that tell the two songs apart"):
    """A diverging bar chart: words of A to the right, words of B to the left."""
    side = contrast_words(ca, cb, top, min_count)
    if side.empty:
        return None
    fig = go.Figure(go.Bar(x=side.z, y=side.word, orientation="h",
                           marker_color=[colors[0] if z > 0 else colors[1] for z in side.z],
                           customdata=side[["in_group", "in_rest"]],
                           hovertemplate=f"%{{y}}<br>%{{customdata[0]}} in {label_a}, "
                                         f"%{{customdata[1]}} in {label_b}<extra></extra>"))
    fig.update_xaxes(title=f"← more in {label_b}   ·   more in {label_a} →")
    return _layout(fig, title, height=max(300, 26 * len(side)))


def word_contrast(a, b, top=8):
    """Words most typical of one song against the other: A to the right, B to the left."""
    return contrast_figure(a.bow, b.bow, a.title, b.title, top=top)


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
