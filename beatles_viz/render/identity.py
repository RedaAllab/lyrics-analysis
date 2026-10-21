"""Global look on top of .streamlit/config.toml (fonts, colours, radius): metrics, tabs, kickers, cards."""
import base64

import streamlit as st

from beatles_viz.config import CARD, INK, MUTED, PAPER, RULE

CSS = f"""
<style>
:root {{ --lx-ink: {INK}; --lx-paper: {PAPER}; --lx-card: {CARD}; --lx-muted: {MUTED}; --lx-rule: {RULE};
         --lx-mono: 'IBM Plex Mono', ui-monospace, Menlo, monospace; }}
h1, h2, h3, h4 {{ letter-spacing: -.02em; }}
h1 {{ line-height: .95 !important; text-wrap: balance; }}
.lx-kicker {{ font-family: var(--lx-mono); text-transform: uppercase; letter-spacing: .06em; font-size: .75rem !important;
             color: var(--lx-muted); margin: 0 0 .5rem; }}
.lx-kicker.lx-plain {{ white-space: nowrap; }}
.lx-banner {{ display: block; width: 100%; height: auto; margin-bottom: .75rem; }}
.lx-lead {{ font-size: 1.2rem; line-height: 1.5; max-width: 36rem; }}
.lx-dot {{ display: inline-block; width: .7em; height: .7em; margin-right: .4em; }}
.lx-stat {{ font-family: var(--lx-mono); font-size: .75rem !important; text-transform: uppercase; letter-spacing: .06em; }}
[data-testid="stMetric"] {{ border-top: 1px solid var(--lx-ink); padding-top: .75rem; }}
[data-testid="stMetricLabel"] p {{ font-family: var(--lx-mono); font-size: .66rem !important; text-transform: uppercase;
                                  letter-spacing: .02em; color: var(--lx-muted); overflow-wrap: normal; word-break: normal; }}
[data-testid="stMetricDelta"] {{ color: var(--lx-muted) !important; }}
[data-testid="stMetricDelta"] svg {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {{ background: var(--lx-card); }}
[role="tablist"] {{ border-bottom: 2px solid var(--lx-ink); gap: 0; }}
[data-testid="stTab"] {{ padding: .6rem 1.1rem; font-weight: 600; }}
[data-testid="stTab"][aria-selected="true"] {{ background: var(--lx-ink); }}
[data-testid="stTab"][aria-selected="true"], [data-testid="stTab"][aria-selected="true"] * {{ color: var(--lx-paper) !important; }}
[role="tablist"]::after, [data-testid="stTab"]::after {{ display: none !important; }}
/* Notices: card with an ink frame instead of Streamlit's tinted box */
[data-testid="stAlert"] > div {{ background: var(--lx-card) !important; border: 1px solid var(--lx-ink) !important;
  border-left-width: 6px !important; border-radius: 0 !important; }}
[data-testid="stAlert"], [data-testid="stAlert"] * {{ color: var(--lx-ink) !important; }}
[data-testid="stCaptionContainer"] {{ color: var(--lx-muted); }}
hr {{ border-color: var(--lx-ink) !important; }}
/* Nothing is cut with an ellipsis: labels, values, deltas and button texts wrap instead */
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *, [data-testid="stMetricValue"], [data-testid="stMetricValue"] *,
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] *, [data-testid^="stBaseButton"] p {{
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] {{ font-size: clamp(1.5rem, 2.4vw, 2.25rem) !important; line-height: 1.1; overflow-wrap: anywhere; }}
[data-testid="stMetricDelta"] {{ height: auto !important; }}
[data-testid^="stBaseButton"] {{ height: auto; min-height: 2.5rem; }}
/* Segmented controls select like tabs: solid ink */
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][data-selected="true"] {{
  background: var(--lx-ink) !important; color: var(--lx-paper) !important; }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][data-selected="true"] * {{ color: var(--lx-paper) !important; }}
/* Phones: rows of metrics stay two by two instead of one per line */
@media (max-width: 640px) {{
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] > [data-testid="stMetric"]) {{
    flex-direction: row !important; flex-wrap: wrap !important; gap: .5rem 1rem !important; }}
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] > [data-testid="stMetric"]) > [data-testid="stColumn"] {{
    flex: 1 1 calc(50% - 1rem) !important; min-width: calc(50% - 1rem) !important; }}
  h1 {{ font-size: 2.75rem !important; }}
  [data-testid="stMainBlockContainer"] {{ padding-top: 4.5rem !important; }}
}}
</style>
"""


def apply_identity(logo, icon):
    st.html(CSS)
    st.logo(str(logo), icon_image=str(icon), size="large")


def kicker(text, plain=False):
    st.markdown(f'<p class="lx-kicker{" lx-plain" if plain else ""}">{text}</p>', unsafe_allow_html=True)


def banner(path, alt):
    """An <img> rather than st.image, which cannot take a text alternative."""
    data = base64.b64encode(path.read_bytes()).decode()
    st.markdown(f'<img class="lx-banner" src="data:image/svg+xml;base64,{data}" alt="{alt}">', unsafe_allow_html=True)
