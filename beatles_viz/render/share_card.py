"""PNG cards made to be posted on X: one per song (1200x630, the link-preview ratio) and one per story (16:9 for
the feed, or 4:5 portrait that takes more of a phone screen). Drawn with Pillow (installed with Streamlit) in the
app's session-sheet look: paper background, ink frame, colour only in the data. Layout is in design units and
rendered at `scale` times the design size (the app uploads at 2x so text stays sharp when X recompresses it).
Fonts are kept in fonts/ with their SIL Open Font License."""
import io
import re

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

from beatles_viz.config import ACCENT, APP_URL, CARD, INK, MUTED, PAPER, SOFT, VOICE_COLORS
from beatles_viz.render.card_kit import (fit_size, font, logo_mark, rgb, sentences_fitting, tape, text_width,
                                         title_lines)
from beatles_viz.render.chart_image import draw_figure
from beatles_viz.share import song_link, standout_facts, voice_line

W, H = 1200, 630
STORY_FORMATS = {"wide": ("16:9, for the timeline", 1600, 900, 1600), "portrait": ("4:5, taller in the feed", 1080, 1350, 1280)}


def _rgb(hex_color):
    return rgb(hex_color)[:3]


def fingerprint_image(fp, color, size=400):
    """Same reading as the on-screen fingerprint: faint repeats lifted, anything above 5% in the voice colour."""
    t = np.sqrt(np.asarray(fp, dtype=float) / 255)
    a = np.clip(t / 0.05, 0, 1)[..., None]
    rgb_ = (np.array(_rgb(SOFT)) * (1 - a) + np.array(_rgb(color)) * a).astype(np.uint8)
    return Image.fromarray(rgb_).resize((size, size), Image.NEAREST)


def _png(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def card_png(song, reference, scale=1):
    k = scale
    img = Image.new("RGB", (W * k, H * k), PAPER)
    d = ImageDraw.Draw(img)
    color = VOICE_COLORS.get(song.voice, VOICE_COLORS["Neutral"])
    fp = song.get("fingerprint")
    d.rectangle([54 * k, 64 * k, 466 * k, 476 * k], fill=CARD, outline=INK, width=3 * k)
    if fp is not None and getattr(fp, "size", 0) > 1:
        img.paste(fingerprint_image(fp, color, 400 * k), (60 * k, 70 * k))

    x, width = 510, W - 510 - 60
    d.text((x * k, 70 * k), f"THE BEATLES · {int(song.year)}", fill=MUTED, font=font(24 * k, "label"))

    lines, size = title_lines(d, song.title, width, u=k)
    y = 112
    for line in lines:
        d.text((x * k, y * k), line, fill=INK, font=font(size * k, "title"))
        y += int(size * 1.12)
    d.rectangle([x * k, (y + 14) * k, (x + 18) * k, (y + 32) * k], fill=color)
    d.text(((x + 30) * k, (y + 8) * k), voice_line(song.voice), fill=MUTED, font=font(24 * k))

    y += 64
    for headline, detail in standout_facts(song, reference):
        d.text((x * k, y * k), headline, fill=INK, font=font(fit_size(d, headline, "strong", 30, width, u=k) * k, "strong"))
        d.text((x * k, (y + 36) * k), detail, fill=MUTED, font=font(fit_size(d, detail, "label", 20, width, u=k) * k, "label"))
        y += 78

    logo_mark(d, 60 * k, 494 * k, 40 * k)
    d.text((112 * k, 504 * k), "Beatles lyrics explorer · unofficial fan project", fill=MUTED, font=font(20 * k, "label"))
    tape(d, W * k, 560 * k, H * k, u=k)
    d.rectangle([0, 0, W * k - 1, H * k - 1], outline=INK, width=6 * k)
    return _png(img)


def story_card_png(story, step, total, size="wide", scale=1, source="", kicker=None):
    """One story as an image: the headline, its first sentences, the chart. Layout in design units of
    `design` wide; the card is rendered at (width * scale) pixels."""
    _, width, height, design = STORY_FORMATS[size]
    u = width * scale / design
    w, h = int(width * scale), int(height * scale)
    dw, dh = design, height * design / width
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    m, inner = 76, design - 152
    portrait = size == "portrait"
    foot = 150

    logo_mark(d, m * u, 60 * u, 52 * u)
    d.text(((m + 72) * u, 72 * u), kicker or f"STORY {step} OF {total}", fill=MUTED, font=font(28 * u, "label"))
    y = 150
    col = inner if portrait else 560  # wide: text on the left, the chart gets the rest of the width
    lines, hs = title_lines(d, story.headline, col, sizes=(96, 86, 78, 70) if portrait else (68, 62, 56, 50),
                            max_lines=3 if portrait else 5, u=u)
    for line in lines:
        d.text((m * u, y * u), line, fill=INK, font=font(hs * u, "title"))
        y += hs * 1.08
    y += 18
    d.rectangle([m * u, y * u, (m + 180) * u, (y + 12) * u], fill=ACCENT)
    y += 40
    fs = 38 if portrait else 30
    room = int(((dh - foot) - y - (40 if portrait else 10)) // (fs * 1.4))
    body = sentences_fitting(d, story.text, "body", fs, col, max(min(room, 4 if portrait else 9), 1), u=u)
    for line in body:
        d.text((m * u, y * u), line, fill=INK, font=font(fs * u))
        y += fs * 1.4
    if portrait:
        box = (m * u, (y + 26) * u, (m + inner) * u, (dh - foot) * u)
    else:
        box = ((m + col + 56) * u, 150 * u, (m + inner) * u, (dh - foot) * u)
    draw_figure(d, story.figure, box, u=u)

    d.line([m * u, (dh - foot + 20) * u, (m + inner) * u, (dh - foot + 20) * u], fill=INK, width=max(int(2 * u), 1))
    src = source or "Original compositions, 1962-1970"
    d.text((m * u, (dh - foot + 44) * u), src, fill=MUTED, font=font(fit_size(d, src, "label", 24, inner * .56, u=u) * u, "label"))
    name = "Beatles lyrics explorer"
    d.text(((m + inner) * u, (dh - foot + 36) * u), name, fill=INK, font=font(34 * u, "title"), anchor="ra")
    d.text(((m + inner) * u, (dh - foot + 80) * u), "unofficial fan project", fill=MUTED, font=font(22 * u, "label"), anchor="ra")
    tape(d, w, int((dh - 34) * u), h, u=u * .8)
    d.rectangle([0, 0, w - 1, h - 1], outline=INK, width=max(int(7 * u), 4))
    return _png(img)


def story_link(step):
    return f"{APP_URL}/stories?story={step}"


def story_post(story, step):
    return f"{story.headline}\n\nBeatles lyrics explorer: {story_link(step)}"


@st.cache_data(show_spinner=False, max_entries=24)
def _cached_story_png(key, size, _story, step, total, source):
    return story_card_png(_story, step, total, size, scale=2, source=source)


def story_share_block(story, step, total, source=""):
    with st.expander("Share this story", icon=":material/share:"):
        size = st.radio("Format", list(STORY_FORMATS), horizontal=True, key="story_card_format",
                        format_func=lambda f: STORY_FORMATS[f][0])
        png = _cached_story_png(f"{story.key}-{story.headline}", size, story, step, total, source)
        st.image(png, width="stretch", caption=f"{story.headline}: chart of the story")
        st.download_button("Download the image", png, file_name=f"beatles-story-{story.key}-{size}.png",
                           mime="image/png", icon=":material/download:", key=f"story_dl_{story.key}_{size}")
        st.caption("Post text, ready to paste along with the image:")
        st.code(story_post(story, step), language=None, wrap_lines=True)


@st.cache_data(show_spinner=False, max_entries=24)
def _cached_song_png(title, _song, _reference):
    return card_png(_song, _reference, scale=2)


def share_block(song, reference):
    with st.expander("Share this song", icon=":material/share:"):
        png = _cached_song_png(song.title, song, reference)
        st.image(png, width="stretch", caption=f"{song.title}: card with the repetition fingerprint and standout measures")
        name = re.sub(r"[^a-z0-9]+", "-", song.title.lower()).strip("-")
        st.download_button("Download the card", png, file_name=f"beatles-{name}.png", mime="image/png",
                           icon=":material/download:")
        st.caption("Post the image with the link below: link previews from this app show no picture.")
        st.code(f"{song.title}: {voice_line(song.voice)}\n\n{song_link(song.title)}", language=None, wrap_lines=True)


@st.cache_data(show_spinner=False, max_entries=24)
def _cached_figure_png(key, size, _card, kicker, source):
    return story_card_png(_card, 0, 0, size, scale=2, source=source, kicker=kicker)


def figure_share_block(key, headline, text, fig, kicker, link, source=""):
    """The share block for a chart on any page: the same X cards as the stories, from a headline, a few
    sentences and the Plotly figure that is on screen. `key` identifies the chart and what it shows (it keys the cache)."""
    from types import SimpleNamespace
    with st.expander("Share this chart", icon=":material/share:"):
        size = st.radio("Format", list(STORY_FORMATS), horizontal=True, key=f"card_format_{key}",
                        format_func=lambda f: STORY_FORMATS[f][0])
        card = SimpleNamespace(headline=headline, text=text, figure=fig)
        png = _cached_figure_png(f"{key}-{headline}", size, card, kicker, source)
        st.image(png, width="stretch", caption=f"{headline}: chart card")
        st.download_button("Download the image", png, file_name=f"beatles-{key}-{size}.png", mime="image/png",
                           icon=":material/download:", key=f"card_dl_{key}_{size}")
        st.caption("Post text, ready to paste along with the image:")
        st.code(f"{headline}\n\nBeatles lyrics explorer: {link}", language=None, wrap_lines=True)
