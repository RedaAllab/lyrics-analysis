"""A 1200x630 PNG card for one song (the usual link-preview size): repetition fingerprint, title, voice and the
song's most unusual measures. Drawn with Pillow and its built-in font: nothing more to install on Streamlit Cloud."""
import io
import re
import textwrap

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from beatles_viz.config import VOICE_COLORS
from beatles_viz.share import song_link, standout_facts, voice_line

W, H = 1200, 630
INK, NAVY, CREAM, GREY = "#12151f", "#1b2440", "#ece6dc", "#9a9aa6"
FAINT = (40, 44, 58)


def _font(size):
    return ImageFont.load_default(size=size)


def _rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def fingerprint_image(fp, color, size=400):
    """Same reading as the on-screen fingerprint: faint repeats lifted, anything above 5% in the voice colour."""
    t = np.sqrt(np.asarray(fp, dtype=float) / 255)
    a = np.clip(t / 0.05, 0, 1)[..., None]
    rgb = (np.array(FAINT) * (1 - a) + np.array(_rgb(color)) * a).astype(np.uint8)
    return Image.fromarray(rgb).resize((size, size), Image.NEAREST)


def _title_lines(draw, title, width):
    for size in (68, 58, 48, 40):
        lines = textwrap.wrap(title, width=max(8, int(width / (size * 0.52))))
        if len(lines) <= 2 and all(draw.textlength(l, font=_font(size)) <= width for l in lines):
            return lines, size
    return textwrap.wrap(title, width=30)[:2], 40


def card_png(song, reference):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=NAVY)
    color = VOICE_COLORS.get(song.voice, "#999999")
    fp = song.get("fingerprint")
    if fp is not None and getattr(fp, "size", 0) > 1:
        img.paste(fingerprint_image(fp, color), (60, 70))

    x, width = 510, W - 510 - 60
    kicker = f"THE BEATLES · {int(song.year)}"
    kw = d.textlength(kicker, font=_font(22))
    d.rectangle([x, 70, x + kw + 24, 106], fill=CREAM)
    d.text((x + 12, 76), kicker, fill=INK, font=_font(22))

    lines, size = _title_lines(d, song.title, width)
    y = 128
    for line in lines:
        d.text((x, y), line, fill=CREAM, font=_font(size))
        y += int(size * 1.15)
    d.ellipse([x, y + 14, x + 18, y + 32], fill=color)
    d.text((x + 28, y + 10), voice_line(song.voice), fill=GREY, font=_font(24))

    y += 64
    for headline, detail in standout_facts(song, reference):
        d.text((x, y), headline, fill=CREAM, font=_font(30))
        d.text((x, y + 36), detail, fill=GREY, font=_font(20))
        y += 78

    d.text((60, 500), "Beatles lyrics explorer · unofficial fan project", fill=GREY, font=_font(20))
    d.rectangle([0, 560, W, H], fill="#0d0f16")
    for sx in range(-40, W + 40, 60):
        d.polygon([(sx, 560), (sx + 34, 560), (sx + 22, H), (sx - 12, H)], fill=CREAM)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def share_block(song, reference):
    with st.expander("Share this song", icon=":material/share:"):
        png = card_png(song, reference)
        st.image(png, width="stretch")
        name = re.sub(r"[^a-z0-9]+", "-", song.title.lower()).strip("-")
        st.download_button("Download the card", png, file_name=f"beatles-{name}.png", mime="image/png",
                           icon=":material/download:")
        st.caption("Post the image with the link below: link previews from this app show no picture.")
        st.code(song_link(song.title), language=None)
