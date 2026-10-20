"""Figures about the lead voices (Lennon, McCartney, Harrison, Starr). No lyric text in any figure."""
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.config import PHASE_ORDER, VOICE_COLORS
from beatles_viz.text.keyness import monroe, prior
from beatles_viz.text.tokenize import content_counter, merge
from beatles_viz.viz.compare_charts import contrast_figure
from beatles_viz.viz.song_charts import _layout

PROFILE = {"tokens": "Words", "types": "Distinct words", "mattr": "Richness", "repetition_score": "Repetition",
           "first_singular": "“I”", "second": "“you”", "first_plural": "“we”"}
TRENDS = {"Lexical richness": "mattr", "Words per song": "tokens", "Repetition score": "repetition_score",
          "“I / me / my” share": "first_singular"}


def voice_summary(corpus, voice):
    d = corpus[corpus.voice == voice]
    return {"songs": len(d), "first": int(d.year.min()), "last": int(d.year.max()),
            "words": float(d.tokens.median()), "mattr": float(d.mattr.mean())}


def voice_radar(corpus, voices):
    """Median song of each voice, placed as a percentile among all songs, so every axis reads 0 to 100."""
    fig = go.Figure()
    labels = [l for c, l in PROFILE.items() if c in corpus]
    for v in voices:
        d = corpus[corpus.voice == v]
        values = [100 * (corpus[c].dropna() < d[c].median()).mean() for c in PROFILE if c in corpus]
        fig.add_trace(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1], name=v, fill="toself",
                                      opacity=0.6, line=dict(color=VOICE_COLORS.get(v))))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="%", angle=90, tickfont_size=9),
                                 angularaxis=dict(tickfont_size=11)))
    fig = _layout(fig, "Typical song of each voice (percentile among all songs)", height=420)
    fig.update_layout(margin=dict(l=60, r=60))  # room for the axis labels on a phone
    return fig


def voice_trend(corpus, voices, metric, label):
    g = (corpus[corpus.voice.isin(voices)].groupby(["phase", "voice"])
         .agg(value=(metric, "mean"), songs=("title", "count")).reset_index())
    g = g[g.songs >= 2]
    fig = px.line(g, x="phase", y="value", color="voice", markers=True, color_discrete_map=VOICE_COLORS,
                  hover_data={"songs": True}, labels={"value": label, "phase": ""},
                  category_orders={"phase": PHASE_ORDER})
    return _layout(fig, f"{label} over time (periods with at least 2 songs)", height=340)


def voice_words(corpus, voice, top=10):
    """Words a voice sings much more than the other voices."""
    a = content_counter(merge(corpus[corpus.voice == voice].bow))
    b = content_counter(merge(corpus[corpus.voice != voice].bow))
    return monroe(a, b, prior(a + b)).query("z > 0").head(top).reset_index(drop=True)


def voice_duel(corpus, a, b, top=10):
    ca, cb = merge(corpus[corpus.voice == a].bow), merge(corpus[corpus.voice == b].bow)
    return contrast_figure(ca, cb, a, b, colors=[VOICE_COLORS[a], VOICE_COLORS[b]], top=top, min_count=5,
                           title=f"{a} or {b}: the words that tell them apart")


def signature_songs(corpus, voice, k=5, top=30):
    """Songs of the voice that use most of its characteristic words, per word sung."""
    words = voice_words(corpus, voice, top)
    weights = dict(zip(words.word, words.z))
    d = corpus[corpus.voice == voice]
    score = d.bow.map(lambda c: sum(n * weights.get(w, 0) for w, n in c.items())) / d.tokens
    return d.assign(score=score).sort_values("score", ascending=False).head(k).title.tolist()
