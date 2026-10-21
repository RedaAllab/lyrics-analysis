"""A 1200x630 PNG card for one song (the usual link-preview size): repetition fingerprint, title, voice and the
song's most unusual measures. Drawn with Pillow (installed with Streamlit) in the app's session-sheet look: paper
background, ink frame, colour only in the data. Fonts are kept in fonts/ with their SIL Open Font License."""
import io
import re
import textwrap
from functools import lru_cache
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from beatles_viz.config import CARD, INK, MUTED, PAPER, SOFT, VOICE_COLORS
from beatles_viz.share import song_link, standout_facts, voice_line

W, H = 1200, 630
FONTS = {"title": "SpaceGrotesk-Bold.ttf", "label": "IBMPlexMono-Medium.ttf", "body": "IBMPlexSans-Regular.ttf",
         "strong": "IBMPlexSans-SemiBold.ttf"}


@lru_cache(maxsize=None)
def _font(size, family="body"):
    return ImageFont.truetype(Path(__file__).parent / "fonts" / FONTS[family], size)


def _rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def fingerprint_image(fp, color, size=400):
    """Same reading as the on-screen fingerprint: faint repeats lifted, anything above 5% in the voice colour."""
    t = np.sqrt(np.asarray(fp, dtype=float) / 255)
    a = np.clip(t / 0.05, 0, 1)[..., None]
    rgb = (np.array(_rgb(SOFT)) * (1 - a) + np.array(_rgb(color)) * a).astype(np.uint8)
    return Image.fromarray(rgb).resize((size, size), Image.NEAREST)


def _title_lines(draw, title, width):
    for size in (68, 58, 48, 40):
        lines = textwrap.wrap(title, width=max(8, int(width / (size * 0.55))))
        if len(lines) <= 2 and all(draw.textlength(l, font=_font(size, "title")) <= width for l in lines):
            return lines, size
    return textwrap.wrap(title, width=30)[:2], 40


def _fit(draw, text, family, size, width):
    """The largest font size, at most `size`, at which the text fits in `width` pixels."""
    while size > 18 and draw.textlength(text, font=_font(size, family)) > width:
        size -= 1
    return _font(size, family)


def card_png(song, reference):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=INK, width=6)
    color = VOICE_COLORS.get(song.voice, VOICE_COLORS["Neutral"])
    fp = song.get("fingerprint")
    d.rectangle([54, 64, 466, 476], fill=CARD, outline=INK, width=3)
    if fp is not None and getattr(fp, "size", 0) > 1:
        img.paste(fingerprint_image(fp, color), (60, 70))

    x, width = 510, W - 510 - 60
    d.text((x, 70), f"THE BEATLES · {int(song.year)}", fill=MUTED, font=_font(24, "label"))

    lines, size = _title_lines(d, song.title, width)
    y = 112
    for line in lines:
        d.text((x, y), line, fill=INK, font=_font(size, "title"))
        y += int(size * 1.12)
    d.rectangle([x, y + 14, x + 18, y + 32], fill=color)
    d.text((x + 30, y + 8), voice_line(song.voice), fill=MUTED, font=_font(24))

    y += 64
    for headline, detail in standout_facts(song, reference):
        d.text((x, y), headline, fill=INK, font=_fit(d, headline, "strong", 30, width))
        d.text((x, y + 36), detail, fill=MUTED, font=_fit(d, detail, "label", 20, width))
        y += 78

    d.text((60, 500), "Beatles lyrics explorer · unofficial fan project", fill=MUTED, font=_font(20, "label"))
    d.rectangle([0, 560, W, H], fill=INK)
    for sx in range(-40, W + 40, 60):
        d.polygon([(sx, 560), (sx + 34, 560), (sx + 22, H), (sx - 12, H)], fill=PAPER)
    d.rectangle([0, 0, W - 1, H - 1], outline=INK, width=6)

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
