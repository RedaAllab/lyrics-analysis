"""Shared drawing pieces for the PNG cards: fonts, colours, the logo mark, the tape strip and text fitting.
Cards are laid out in design units and drawn at any size with a scale `u` (final pixels per design unit), so
the same layout can be rendered small for a test or at 2x for a sharp upload."""
import re
import textwrap
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

from beatles_viz.config import ACCENT, CARD, INK, PAPER

FONTS = {"title": "SpaceGrotesk-Bold.ttf", "label": "IBMPlexMono-Medium.ttf", "body": "IBMPlexSans-Regular.ttf",
         "strong": "IBMPlexSans-SemiBold.ttf"}


@lru_cache(maxsize=None)
def font(size, family="body"):
    return ImageFont.truetype(str(Path(__file__).parent / "fonts" / FONTS[family]), max(int(round(size)), 8))


def rgb(color, default=INK):
    """(r, g, b, alpha 0-1) from '#rrggbb', 'rgb()' or 'rgba()'; the default for anything else."""
    if isinstance(color, (tuple, list)):
        return tuple(color[:3]) + (1.0,)
    if not isinstance(color, str):
        color = default
    color = color.strip()
    if color.startswith("#") and len(color) == 7:
        return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) + (1.0,)
    m = re.match(r"rgba?\(([^)]+)\)", color)
    if m:
        p = [float(x) for x in m.group(1).split(",")]
        return int(p[0]), int(p[1]), int(p[2]), (p[3] if len(p) > 3 else 1.0)
    return rgb(default) if color != default else (0, 0, 0, 1.0)


def mix(color, over=PAPER, alpha=1.0):
    """The opaque colour of `color` at `alpha` over `over` (PIL does not blend in an RGB draw)."""
    c, o = rgb(color)[:3], rgb(over)[:3]
    return tuple(int(round(a * alpha + b * (1 - alpha))) for a, b in zip(c, o))


def text_width(draw, text, size, family="body", u=1):
    return draw.textlength(text, font=font(size * u, family)) / u


def fit_size(draw, text, family, size, width, minimum=14, u=1):
    """The largest size, at most `size`, at which the text is `width` wide or less (design units)."""
    while size > minimum and text_width(draw, text, size, family, u) > width:
        size -= 1
    return size


def wrap(draw, text, family, size, width, max_lines, u=1):
    """Greedy word wrap to `width`; the last line ends with an ellipsis when the text does not fit."""
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if text_width(draw, trial, size, family, u) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = w
    lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and text_width(draw, lines[-1] + "…", size, family, u) > width:
            lines[-1] = lines[-1].rsplit(" ", 1)[0] if " " in lines[-1] else lines[-1][:-1]
        lines[-1] += "…"
    return lines


def sentences_fitting(draw, text, family, size, width, max_lines, u=1):
    """Whole sentences from the start of `text` that fit in `max_lines`; the first one at least."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = parts[0]
    for p in parts[1:]:
        trial = f"{kept} {p}"
        if len(wrap(draw, trial, family, size, width, max_lines + 1, u)) > max_lines:
            break
        kept = trial
    return wrap(draw, kept, family, size, width, max_lines, u)


def logo_mark(draw, x, y, size):
    """The app's icon (static/icon.svg: a framed 3x3 grid with a diagonal and two orange squares)."""
    k = size / 48
    draw.rectangle([x + 2 * k, y + 2 * k, x + 46 * k, y + 46 * k], fill=CARD, outline=INK, width=max(int(3 * k), 2))
    for gx, gy, color in [(9, 9, INK), (20, 20, INK), (31, 31, INK), (31, 9, ACCENT), (9, 31, ACCENT)]:
        draw.rectangle([x + gx * k, y + gy * k, x + (gx + 8) * k - 1, y + (gy + 8) * k - 1], fill=color)


def tape(draw, width, top, bottom, u=1, tooth=60):
    """The ink strip with paper teeth that closes every card."""
    draw.rectangle([0, top, width, bottom], fill=INK)
    step = tooth * u
    x = -step * 0.67
    while x < width + step:
        draw.polygon([(x, top), (x + 0.57 * step, top), (x + 0.37 * step, bottom), (x - 0.2 * step, bottom)], fill=PAPER)
        x += step


def title_lines(draw, title, width, sizes=(68, 58, 48, 40), max_lines=2, u=1):
    """The first size at which the title wraps to `max_lines` lines or fewer, each within `width`."""
    for size in sizes:
        lines = textwrap.wrap(title, width=max(8, int(width / (size * 0.55))))
        if len(lines) <= max_lines and all(text_width(draw, l, size, "title", u) <= width for l in lines):
            return lines, size
    size = sizes[-1]
    return wrap(draw, title, "title", size, width, max_lines, u), size
