"""One Plotly figure per question about a song. No Streamlit here, and no lyric text in any figure."""
from collections import Counter

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.attribution import resolve_voice
from beatles_viz.config import ACCENT, INK, PAPER, REFERENCE, SECONDARY, SECTION_COLORS, VOICE_COLORS
from beatles_viz.text.keyness import song_keyness
from beatles_viz.text.sections import section_name
from beatles_viz.text.tokenize import tokenize
from beatles_viz.viz.theme import titled

MIN_INSTRUMENTAL_WIDTH = 4  # word-equivalents, so wordless sections stay visible on the timeline
MAX_LINES_FOR_LINE_MATRIX = 80
MIN_LABEL_GAP = 0.08  # share of the song length between two section labels


def structure_frame(song):
    """One row per section from the song's sec_* columns (names, kinds, word counts): works without the lyrics."""
    rows, start = [], 0
    for i, (name, kind, words, repeat, auto) in enumerate(zip(song.sec_names, song.sec_kinds, song.sec_words,
                                                               song.sec_repeats, song.sec_auto)):
        width = max(int(words), MIN_INSTRUMENTAL_WIDTH)
        rows.append(dict(order=i, name=name, kind=kind, start=start, width=width, words=int(words),
                         repeat=f"x{repeat}" if repeat > 1 else "", auto=bool(auto)))
        start += width
    return pd.DataFrame(rows)


def has_structure(song):
    return "sec_kinds" in song and isinstance(song.sec_kinds, list) and len(song.sec_kinds) > 0


def structure_timeline(song):
    if not has_structure(song):
        return None
    df = structure_frame(song)
    fig = go.Figure()
    for kind, g in df.groupby("kind", sort=False):
        fig.add_bar(y=["structure"] * len(g), x=g.width, base=g.start, orientation="h", name=kind,
                    marker_color=SECTION_COLORS.get(kind, SECTION_COLORS["other"]), marker_line=dict(color=PAPER, width=2),
                    text=(g.name + " " + g.repeat).str.strip(), textposition="inside", insidetextanchor="middle",
                    customdata=g[["name", "words", "repeat"]],
                    hovertemplate="%{customdata[0]} %{customdata[2]}<br>%{customdata[1]} words<extra></extra>")
    fig.update_yaxes(visible=False)
    fig.update_xaxes(title="position in the song (words)")
    fig.update_layout(barmode="overlay", legend=dict(orientation="h", yanchor="top", y=-0.7))
    title = "Structure (sections detected automatically)" if df.auto.any() else "Structure"
    return titled(fig, title, height=270)


def _jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def self_similarity(sections):
    units = [(section_name(s), set(tokenize(l))) for s in sections for l in s.lines]
    by_section = len(units) > MAX_LINES_FOR_LINE_MATRIX
    if by_section:
        units = [(section_name(s), set(tokenize(" ".join(s.lines)))) for s in sections if s.lines]
    if len(units) < 2:
        return None
    m = np.array([[_jaccard(a, b) for _, b in units] for _, a in units])
    labels = [f"{i + 1}. {name}" for i, (name, _) in enumerate(units)]
    fig = go.Figure(go.Heatmap(z=m, x=labels, y=labels, zmin=0, zmax=1,
                               hovertemplate="%{y}<br>%{x}<br>shared words: %{z:.2f}<extra></extra>"))
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(autorange="reversed", showticklabels=by_section)
    unit = "sections" if by_section else "lines"
    return titled(fig, f"Repetition map ({unit}: similarity of word sets)", height=460)


def rolling_richness(sections, window=30):
    words, bounds = [], []
    for s in sections:
        bounds.append((len(words), section_name(s)))
        words += tokenize(" ".join(s.lines))
    if len(words) < window:
        return None
    c = Counter(words[:window])
    vals = [len(c) / window]
    for i in range(window, len(words)):
        c[words[i]] += 1
        c[words[i - window]] -= 1
        if c[words[i - window]] == 0:
            del c[words[i - window]]
        vals.append(len(c) / window)
    x = np.arange(len(vals)) + window // 2
    fig = go.Figure(go.Scatter(x=x, y=vals, mode="lines", line=dict(color=SECONDARY),
                               hovertemplate="word %{x}<br>%{y:.0%} distinct<extra></extra>"))
    last_label = -len(words)
    for pos, name in bounds:
        fig.add_vline(x=pos, line=dict(color=REFERENCE, dash="dot", width=1))
        if pos - last_label >= MIN_LABEL_GAP * len(words):  # skip labels that would overlap
            fig.add_annotation(x=pos, y=1.04, yref="paper", text=name, showarrow=False, font=dict(size=9),
                               xanchor="left")
            last_label = pos
    fig.update_yaxes(title=f"distinct words in a {window}-word window", tickformat=".0%", range=[0, 1.05])
    fig.update_xaxes(title="position in the song (words)")
    return titled(fig, "Lexical density along the song", height=320)


def keyness(song_bow, corpus_bows, top=10):
    r = song_keyness(song_bow, corpus_bows).head(top)
    if r.empty:
        return None
    fig = px.bar(r[::-1], x="z", y="word", orientation="h", hover_data={"in_group": True, "in_rest": True},
                 labels={"z": "over-representation (z-score)", "in_group": "in this song", "in_rest": "in other songs"},
                 color_discrete_sequence=[ACCENT])
    return titled(fig, "Words that set this song apart from the corpus", height=360)


HIGHLIGHT = {"symbol": "star", "size": 20, "line": dict(color=INK, width=1.5)}
HIGHLIGHT_COLORS = [ACCENT, INK]  # song A, song B: neither is a voice colour


def corpus_position(song, corpus, period=None, others=()):
    """Scatter of the corpus with the song (and optional other songs) marked as stars."""
    d = corpus.dropna(subset=["mattr"])
    if period:
        d = d[d.phase == period]
    fig = px.scatter(d, x="tokens", y="mattr", color="voice", color_discrete_map=VOICE_COLORS, opacity=0.55,
                     hover_name="title", hover_data={"year": True, "voice": True, "tokens": True, "mattr": ":.2f"},
                     labels={"tokens": "words in the song", "mattr": "lexical richness (MATTR-50)"})
    for s, color in zip([song, *others], HIGHLIGHT_COLORS):
        if not np.isnan(s.mattr):
            fig.add_scatter(x=[s.tokens], y=[s.mattr], mode="markers", name=s.title,
                            marker={**HIGHLIGHT, "color": color}, hovertemplate=f"{s.title}<extra></extra>")
    scope = f"songs of {period}" if period else "all songs"
    return titled(fig, f"Length and richness compared with {scope}", height=420)


def voice_split(sections, lead_vocal):
    if not any(s.singers for s in sections):
        return None
    rows = [dict(section=f"{i + 1}. {section_name(s)}", voice=resolve_voice(s, lead_vocal),
                 words=len(tokenize(" ".join(s.lines))), source="tag" if s.singers else "song lead")
            for i, s in enumerate(sections) if s.lines]
    df = pd.DataFrame(rows)
    fig = px.bar(df, x="words", y="section", color="voice", orientation="h", color_discrete_map=VOICE_COLORS,
                 hover_data={"source": True}, category_orders={"section": df.section.tolist()})
    fig.update_yaxes(autorange="reversed", title=None)
    return titled(fig, "Who sings each section", height=max(260, 28 * len(df)))


PRONOUN_LABELS = {"first_singular": "I / me / my", "second": "you / your", "first_plural": "we / us / our",
                  "third_person": "he / she / they"}
TELLING_LABELS = {"past": "looks back (past words)", "future": "looks ahead (future words)",
                  "questions": "asks (lines with a question)", "orders": "urges (lines opening on an order)"}


def pronoun_profile(song, corpus):
    ref = corpus[corpus.phase == song.phase] if song.phase else corpus
    rows = []
    for key, label in PRONOUN_LABELS.items():
        rows.append(dict(pronoun=label, group="this song", share=100 * song[key]))
        rows.append(dict(pronoun=label, group=f"average {song.phase or 'corpus'}", share=100 * ref[key].mean()))
    fig = px.bar(pd.DataFrame(rows), x="pronoun", y="share", color="group", barmode="group",
                 labels={"share": "per 100 words", "pronoun": ""},
                 color_discrete_sequence=[SECONDARY, REFERENCE])
    return titled(fig, "Point of view: personal pronouns", height=320)


def telling_profile(song, corpus):
    """Past and future words per 100 words, questions and orders per 100 lines, against the period average.
    None when the song has none of the measures (public file exported before them)."""
    keys = [k for k in TELLING_LABELS if k in corpus and song.get(k) == song.get(k)]
    if not keys:
        return None
    ref = corpus[corpus.phase == song.phase] if song.phase else corpus
    rows = []
    for key in keys:
        rows.append(dict(marker=TELLING_LABELS[key], group="this song", rate=100 * song[key]))
        rows.append(dict(marker=TELLING_LABELS[key], group=f"average {song.phase or 'corpus'}",
                         rate=100 * ref[key].mean()))
    fig = px.bar(pd.DataFrame(rows), x="rate", y="marker", color="group", barmode="group", orientation="h",
                 labels={"rate": "per 100 words (past, future) · per 100 lines (questions, orders)", "marker": ""},
                 color_discrete_sequence=[SECONDARY, REFERENCE])
    fig.update_yaxes(autorange="reversed")
    return titled(fig, "How it tells", height=320)


def fingerprint_figure(fp, color=ACCENT, height=150):
    """SongSim thumbnail: where words repeat along the song (top-left = start). No text involved."""
    z = 255 * np.sqrt(np.asarray(fp, dtype=float) / 255)  # most blocks are sparse: lift faint repeats
    fig = go.Figure(go.Heatmap(z=z, colorscale=[[0, "rgba(22,22,26,0.06)"], [0.05, color], [1, color]],
                               zmin=0, zmax=255, showscale=False, hoverinfo="skip"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)")
    return fig
