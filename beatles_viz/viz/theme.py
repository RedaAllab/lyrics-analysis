"""One look for every chart: fonts, colours, margins, legend and hover. Applied by render.components.plot."""
import plotly.graph_objects as go
import plotly.io as pio

from beatles_viz.config import ACCENT

BODY_FONT = "'Source Sans Pro', 'Source Sans 3', system-ui, sans-serif"
TITLE_FONT = "'DM Serif Display', Georgia, serif"  # loaded by render.identity
COLORWAY = [ACCENT, "#5fa8d3", "#81b29a", "#f2cc8f", "#b07bac", "#9a9a9a", "#d1495b", "#3a6ea5"]
NAME = "lyrics"

pio.templates[NAME] = go.layout.Template(layout=dict(
    font=dict(family=BODY_FONT, size=13),
    title=dict(font=dict(family=TITLE_FONT, size=19), x=0, xanchor="left"),
    colorway=COLORWAY,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(font=dict(family=BODY_FONT, size=13)),
    legend=dict(font=dict(size=12), title=dict(font=dict(size=12))),
    xaxis=dict(gridcolor="rgba(128,128,128,0.18)", zeroline=False, title=dict(font=dict(size=12))),
    yaxis=dict(gridcolor="rgba(128,128,128,0.18)", zeroline=False, title=dict(font=dict(size=12))),
))


def titled(fig, title, height=320):
    fig.update_layout(title=title, height=height, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def style(fig):
    """Layered over Streamlit's own chart theme: explicit layout values win over it."""
    t = pio.templates[NAME].layout
    fig.update_layout(font=t.font, colorway=t.colorway, paper_bgcolor=t.paper_bgcolor, plot_bgcolor=t.plot_bgcolor,
                      hoverlabel=t.hoverlabel, title_font=t.title.font, title_x=0, title_xanchor="left")
    if fig.layout.legend.orientation is None:  # below the chart: a side legend squeezes it on a phone
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0))
    fig.update_xaxes(gridcolor=t.xaxis.gridcolor, zeroline=False, title_font_size=12)
    fig.update_yaxes(gridcolor=t.yaxis.gridcolor, zeroline=False, title_font_size=12)
    return fig
