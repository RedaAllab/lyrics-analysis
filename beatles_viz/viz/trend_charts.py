"""Figures about change over the discography. No lyric text in any figure."""
import plotly.express as px

from beatles_viz.config import ACCENT, PHASES, SECTION_COLORS, VOICE_COLORS, VOICE_ORDER
from beatles_viz.viz.song_charts import _layout

PHASE_ORDER = [p for p, _, _ in PHASES]
RISING = "#5fa8d3"
SECTION_LABELS = {"song": "untagged", "pre_chorus": "pre-chorus"}


def _phase_labels(counts):
    return {p: f"{p}<br>{n} songs" for p, n in counts.items()}


def word_movers(movers):
    first, last = PHASE_ORDER[0], PHASE_ORDER[-1]
    fig = px.bar(movers[::-1], x="change", y="word", orientation="h", color="direction",
                 color_discrete_map={"rising": RISING, "falling": ACCENT},
                 hover_data={"first": ":.1f", "last": ":.1f", "songs": True, "direction": False},
                 labels={"change": f"change in rate, {first} to {last} (per 1,000 words)", "word": "",
                         "first": f"per 1,000 words, {first}", "last": f"per 1,000 words, {last}",
                         "songs": "songs using it"})
    fig.update_layout(showlegend=False)
    return _layout(fig, "Words that drift steadily", height=max(320, 26 * len(movers) + 100))


def section_shares(shares, counts):
    d = shares.rename(index=_phase_labels(counts)).rename(columns=SECTION_LABELS)
    colors = {SECTION_LABELS.get(k, k): c for k, c in {**SECTION_COLORS, "song": "#2f3441"}.items()}
    fig = px.bar(d, barmode="stack", color_discrete_map=colors, labels={"value": "share of sung words", "index": "",
                                                                         "kind": "section"})
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend_title_text="")
    fig.update_xaxes(title="")
    return _layout(fig, "Where the words are sung", height=380)


def voice_shares(shares, counts):
    d = shares.rename(index=_phase_labels(counts))
    d = d[[v for v in VOICE_ORDER if v in d and d[v].sum() > 0]]
    fig = px.bar(d, barmode="stack", color_discrete_map=VOICE_COLORS, labels={"value": "share of songs", "index": "",
                                                                              "voice": "lead voice"})
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend_title_text="")
    fig.update_xaxes(title="")
    return _layout(fig, "Who sings lead", height=380)
