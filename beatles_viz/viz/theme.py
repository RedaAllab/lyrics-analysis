"""One look for every chart: fonts, colours, axes, legend and hover. Applied by render.components.plot.
Monochrome frame (ink axis lines, light horizontal rules), colour only in the data."""
import plotly.graph_objects as go
import plotly.io as pio

from beatles_viz.config import ACCENT, CARD, INK, MUTED, PAPER, RULE, SECTION_COLORS, SOFT, VOICE_COLORS

BODY_FONT = "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif"
TITLE_FONT = "'Space Grotesk', 'Helvetica Neue', Arial, sans-serif"
MONO_FONT = "'IBM Plex Mono', ui-monospace, Menlo, monospace"  # fonts loaded by .streamlit/config.toml
COLORWAY = [VOICE_COLORS[v] for v in ("Lennon", "McCartney", "Harrison", "Starr", "Shared")] + \
           [ACCENT, SECTION_COLORS["verse"], VOICE_COLORS["Neutral"]]
SEQUENTIAL = [[0, SOFT], [0.5, "#7d95d0"], [0.85, VOICE_COLORS["Lennon"]], [1, INK]]
DIVERGING = [[0, VOICE_COLORS["Lennon"]], [0.5, PAPER], [1, ACCENT]]
NAME = "lyrics"

AXIS = dict(showline=True, linecolor=INK, linewidth=1, ticks="outside", tickcolor=INK, ticklen=4,
            tickfont=dict(family=MONO_FONT, size=11, color=INK), zeroline=False,
            title=dict(font=dict(family=BODY_FONT, size=12, color=MUTED)))

pio.templates[NAME] = go.layout.Template(
    layout=dict(
        font=dict(family=BODY_FONT, size=13, color=INK),
        title=dict(font=dict(family=TITLE_FONT, size=20, color=INK), x=0, xanchor="left"),
        colorway=COLORWAY,
        colorscale=dict(sequential=SEQUENTIAL, diverging=DIVERGING),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor=CARD, bordercolor=INK, font=dict(family=BODY_FONT, size=13, color=INK)),
        legend=dict(font=dict(size=12), title=dict(font=dict(family=MONO_FONT, size=11, color=MUTED))),
        bargap=0.25,
        xaxis=dict(**AXIS, showgrid=False),
        yaxis=dict(**{**AXIS, "tickfont": dict(family=BODY_FONT, size=12, color=INK)}, showgrid=True, gridcolor=RULE),
    ),
    data=dict(bar=[go.Bar(marker_line_width=0)], heatmap=[go.Heatmap(colorscale=SEQUENTIAL)]),
)


def titled(fig, title, height=320):
    fig.update_layout(title=title, height=height, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def style(fig):
    """Layered over Streamlit's own chart theme: explicit layout values win over it."""
    t = pio.templates[NAME].layout
    fig.update_layout(font=t.font, colorway=t.colorway, colorscale=t.colorscale, paper_bgcolor=t.paper_bgcolor,
                      plot_bgcolor=t.plot_bgcolor, hoverlabel=t.hoverlabel, title_font=t.title.font, title_x=0,
                      title_xanchor="left", bargap=fig.layout.bargap or t.bargap, legend_font=t.legend.font,
                      legend_title_font=t.legend.title.font)
    if fig.layout.legend.orientation is None:  # below the chart: a side legend squeezes it on a phone
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0))
    fig.update_xaxes(t.xaxis.to_plotly_json())
    fig.update_yaxes(t.yaxis.to_plotly_json())
    return fig


def solid_boxes(fig, colors):
    """Box plots with a solid fill in each group's colour and an ink outline and median, not Plotly's translucent fill."""
    fig.for_each_trace(lambda t: t.update(fillcolor=colors.get(t.name, t.marker.color), line=dict(color=INK, width=1.2),
                                          marker=dict(color=colors.get(t.name, t.marker.color), size=4)))
    return fig
