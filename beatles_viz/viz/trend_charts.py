"""Figures about change over the discography. No lyric text in any figure."""
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.config import ACCENT, PHASE_ORDER, REFERENCE, SECONDARY, SECTION_COLORS, VOICE_COLORS, VOICE_ORDER
from beatles_viz.viz.theme import titled

RISING = SECONDARY
GROUP_COLORS = SECTION_COLORS


def _phase_labels(counts):
    return {p: f"{p}<br>{n} songs" for p, n in counts.items()}


def word_movers(movers):
    """movers: steady_movers rows, with ci_low and ci_high (change_interval) when available: drawn as error bars."""
    first, last = PHASE_ORDER[0], PHASE_ORDER[-1]
    d = movers[::-1]
    extra = {}
    if {"ci_low", "ci_high"} <= set(d):
        extra = dict(error_x=d.ci_high - d.change_song, error_x_minus=d.change_song - d.ci_low)
    held = d.held if "held" in d else False  # survives the correction for multiple tests: starred
    d = d.assign(label=d.word + np.where(held, " *", ""))
    fig = px.bar(d, x="change_song", y="label", orientation="h", color="direction",
                 color_discrete_map={"rising": RISING, "falling": ACCENT}, **extra,
                 hover_data={"first_song": ":.1f", "last_song": ":.1f", "songs": True, "q": ":.2f",
                             "direction": False},
                 labels={"change_song": f"change in rate, {first} to {last} (per 1,000 words, mean of songs)",
                         "label": "", "first_song": f"per 1,000 words, {first}", "last_song": f"per 1,000 words, {last}",
                         "songs": "songs using it", "q": "q (corrected for the words tested)"})
    fig.update_layout(showlegend=False)
    return titled(fig, "Words that drift steadily", height=max(320, 26 * len(movers) + 100))


def section_shares(shares, counts):
    d = shares.rename(index=_phase_labels(counts))
    fig = px.bar(d, barmode="stack", color_discrete_map=GROUP_COLORS, labels={"value": "share of sung words", "index": "",
                                                                         "kind": "section"})
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend_title_text="")
    fig.update_xaxes(title="")
    return titled(fig, "Where the words are sung", height=380)


def voice_shares(shares, counts):
    d = shares.rename(index=_phase_labels(counts))
    d = d[[v for v in VOICE_ORDER if v in d and d[v].sum() > 0]]
    fig = px.bar(d, barmode="stack", color_discrete_map=VOICE_COLORS, labels={"value": "share of songs", "index": "",
                                                                              "voice": "lead voice"})
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend_title_text="")
    fig.update_xaxes(title="")
    return titled(fig, "Who sings lead", height=380)


def phase_strip(d, col, label, title, height=400, zero_line=False):
    """Each song as a dot in its period, coloured by lead voice, with the period average as a line."""
    d = d.dropna(subset=[col, "phase"])
    g = d.groupby("phase")[col].mean().reindex(PHASE_ORDER)
    fig = px.strip(d, x="phase", y=col, color="voice", color_discrete_map=VOICE_COLORS, hover_name="title",
                   category_orders={"phase": PHASE_ORDER, "voice": VOICE_ORDER},
                   labels={col: label, "phase": "", "voice": "lead voice"})
    fig.add_trace(go.Scatter(x=g.index, y=g.values, mode="lines+markers", name="average",
                             line=dict(color=ACCENT, width=3)))
    if zero_line:
        fig.add_hline(y=0, line=dict(color=REFERENCE, dash="dot", width=1))
    return titled(fig, title, height)
