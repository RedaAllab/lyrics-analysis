"""One Plotly figure per question about a song. No Streamlit here, and no lyric text in any figure."""
from collections import Counter

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.attribution import resolve_voice
from beatles_viz.config import SECTION_COLORS, VOICE_COLORS
from beatles_viz.text.keyness import monroe, prior
from beatles_viz.text.sections import section_name
from beatles_viz.text.tokenize import content_counter, merge, tokenize

MIN_INSTRUMENTAL_WIDTH = 4  # word-equivalents, so wordless sections stay visible on the timeline
MAX_LINES_FOR_LINE_MATRIX = 80
MIN_LABEL_GAP = 0.08  # share of the song length between two section labels


def _layout(fig, title, height=320):
    fig.update_layout(title=title, height=height, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def structure_timeline(sections):
    rows, start = [], 0
    for i, s in enumerate(sections):
        words = len(tokenize(" ".join(s.lines)))
        width = max(words, MIN_INSTRUMENTAL_WIDTH)
        rows.append(dict(order=i, name=section_name(s), kind=s.kind, start=start, width=width, words=words,
                         repeat=f"x{s.repeat}" if s.repeat > 1 else ""))
        start += width
    df = pd.DataFrame(rows)
    fig = go.Figure()
    for kind, g in df.groupby("kind", sort=False):
        fig.add_bar(y=["structure"] * len(g), x=g.width, base=g.start, orientation="h", name=kind,
                    marker_color=SECTION_COLORS.get(kind, "#cccccc"), marker_line=dict(color="white", width=2),
                    text=(g.name + " " + g.repeat).str.strip(), textposition="inside", insidetextanchor="middle",
                    customdata=g[["name", "words", "repeat"]],
                    hovertemplate="%{customdata[0]} %{customdata[2]}<br>%{customdata[1]} words<extra></extra>")
    fig.update_yaxes(visible=False)
    fig.update_xaxes(title="position in the song (words)")
    fig.update_layout(barmode="overlay", legend=dict(orientation="h", y=-0.4))
    return _layout(fig, "Structure", height=230)


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
    fig = go.Figure(go.Heatmap(z=m, x=labels, y=labels, colorscale="Blues", zmin=0, zmax=1,
                               hovertemplate="%{y}<br>%{x}<br>shared words: %{z:.2f}<extra></extra>"))
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(autorange="reversed", showticklabels=by_section)
    unit = "sections" if by_section else "lines"
    return _layout(fig, f"Repetition map ({unit}: similarity of word sets)", height=460)


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
    fig = go.Figure(go.Scatter(x=x, y=vals, mode="lines", line=dict(color="#3a6ea5"),
                               hovertemplate="word %{x}<br>%{y:.0%} distinct<extra></extra>"))
    last_label = -len(words)
    for pos, name in bounds:
        fig.add_vline(x=pos, line=dict(color="#bbbbbb", dash="dot", width=1))
        if pos - last_label >= MIN_LABEL_GAP * len(words):  # skip labels that would overlap
            fig.add_annotation(x=pos, y=1.04, yref="paper", text=name, showarrow=False, font=dict(size=9),
                               xanchor="left")
            last_label = pos
    fig.update_yaxes(title=f"distinct words in a {window}-word window", tickformat=".0%", range=[0, 1.05])
    fig.update_xaxes(title="position in the song (words)")
    return _layout(fig, "Lexical density along the song", height=320)


def keyness(song_bow, corpus_bows, top=10):
    song = content_counter(song_bow)
    rest = content_counter(merge(corpus_bows)) - song
    r = monroe(song, rest, prior(song + rest), min_count=3)
    r = r[r.in_group > 0].head(top)
    if r.empty:
        return None
    fig = px.bar(r[::-1], x="z", y="word", orientation="h", hover_data={"in_group": True, "in_rest": True},
                 labels={"z": "over-representation (z-score)", "in_group": "in this song", "in_rest": "in other songs"},
                 color_discrete_sequence=["#e07a5f"])
    return _layout(fig, "Words that set this song apart from the corpus", height=360)


def corpus_position(song, corpus, period=None):
    d = corpus.dropna(subset=["mattr"])
    if period:
        d = d[d.phase == period]
    fig = px.scatter(d, x="tokens", y="mattr", color="voice", color_discrete_map=VOICE_COLORS, opacity=0.55,
                     hover_name="title", hover_data={"year": True, "voice": True, "tokens": True, "mattr": ":.2f"},
                     labels={"tokens": "words in the song", "mattr": "lexical richness (MATTR-50)"})
    if not np.isnan(song.mattr):
        fig.add_scatter(x=[song.tokens], y=[song.mattr], mode="markers", name=song.title,
                        # Gold fill with a dark outline stays visible on both light and dark themes.
                        marker=dict(symbol="star", size=20, color="#f5b700", line=dict(color="#1a1a1a", width=1.5)),
                        hovertemplate=f"{song.title}<extra></extra>")
    scope = f"songs of {period}" if period else "all songs"
    return _layout(fig, f"Length and richness compared with {scope}", height=420)


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
    return _layout(fig, "Who sings each section", height=max(260, 28 * len(df)))


PRONOUN_LABELS = {"first_singular": "I / me / my", "second": "you / your", "first_plural": "we / us / our"}


def pronoun_profile(song, corpus):
    ref = corpus[corpus.phase == song.phase] if song.phase else corpus
    rows = []
    for key, label in PRONOUN_LABELS.items():
        rows.append(dict(pronoun=label, group="this song", share=100 * song[key]))
        rows.append(dict(pronoun=label, group=f"average {song.phase or 'corpus'}", share=100 * ref[key].mean()))
    fig = px.bar(pd.DataFrame(rows), x="pronoun", y="share", color="group", barmode="group",
                 labels={"share": "per 100 words", "pronoun": ""},
                 color_discrete_sequence=["#3a6ea5", "#c9d6df"])
    return _layout(fig, "Point of view: personal pronouns", height=320)
