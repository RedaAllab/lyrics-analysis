"""Global look: display font for titles, card style, section rhythm. Colours come from .streamlit/config.toml."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&display=swap');
h1, h2, h3 { font-family: 'DM Serif Display', Georgia, serif !important; font-weight: 400 !important;
             letter-spacing: .01em; }
h1 { font-size: 2.6rem !important; }
.lx-kicker { text-transform: uppercase; letter-spacing: .18em; font-size: .75rem; color: #e07a5f; margin: 0; }
.lx-lead { font-size: 1.1rem; opacity: .8; max-width: 40rem; }
.lx-dot { display: inline-block; width: .7em; height: .7em; border-radius: 50%; margin-right: .35em; }
.lx-stat { font-size: .85rem; opacity: .75; }
</style>
"""


def apply_identity(logo, icon):
    st.html(CSS)
    st.logo(str(logo), icon_image=str(icon))


def kicker(text):
    st.markdown(f'<p class="lx-kicker">{text}</p>', unsafe_allow_html=True)
