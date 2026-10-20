"""Figures about one release and the releases over time. No lyric text in any figure."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.config import ACCENT, PAPER, REFERENCE, SECTION_COLORS, VOICE_COLORS
from beatles_viz.viz.song_charts import has_structure, structure_frame
from beatles_viz.viz.theme import titled


def album_timeline(albums, selected=None):
    """Each release as a bubble: year, average richness, size = number of songs."""
    d = albums.dropna(subset=["mattr"]).assign(selected=lambda a: a.album == selected)
    fig = px.scatter(d, x="year", y="mattr", size="tracks", hover_name="album", size_max=28,
                     color="selected", color_discrete_map={True: ACCENT, False: REFERENCE},
                     hover_data={"tracks": True, "year": True, "mattr": ":.2f", "selected": False},
                     labels={"mattr": "average lexical richness", "year": ""})
    fig.update_layout(showlegend=False)
    return titled(fig, "Releases over time", height=320)


def album_structures(tracks):
    """One bar per track, cut into its sections: where the choruses fall, how long each song runs."""
    rows = [structure_frame(t).assign(title=t.title) for _, t in tracks.iterrows() if has_structure(t)]
    if not rows:
        return None
    df = pd.concat(rows)
    order = tracks.title.tolist()
    fig = go.Figure()
    for kind, g in df.groupby("kind", sort=False):
        fig.add_bar(y=g.title, x=g.width, base=g.start, orientation="h", name=kind,
                    marker_color=SECTION_COLORS.get(kind, SECTION_COLORS["other"]), marker_line=dict(color=PAPER, width=1),
                    customdata=g[["name", "words"]],
                    hovertemplate="%{y}<br>%{customdata[0]}: %{customdata[1]} words<extra></extra>")
    fig.update_yaxes(categoryorder="array", categoryarray=order[::-1], title=None)
    fig.update_xaxes(title="position in the song (words)")
    fig.update_layout(barmode="overlay", legend=dict(orientation="h", y=-0.15))
    return titled(fig, "How each track is built", height=max(280, 30 * len(order) + 120))


def album_tracks(tracks, metric, label):
    d = tracks.dropna(subset=[metric])
    if d.empty:
        return None
    fig = px.bar(d, x=metric, y="title", color="voice", orientation="h", color_discrete_map=VOICE_COLORS,
                 hover_data={"year": True, "tokens": True}, labels={metric: label, "title": "", "voice": "lead voice"})
    fig.update_yaxes(categoryorder="array", categoryarray=tracks.title.tolist()[::-1])
    return titled(fig, f"{label}, track by track", height=max(280, 28 * len(d) + 100))
