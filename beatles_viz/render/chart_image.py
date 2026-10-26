"""A Plotly figure drawn with Pillow into a box of a card: bars, lines and dots (strip and box plots).
No browser or Kaleido needed, so it runs on Streamlit Cloud. Built for a phone-sized preview: values are written
on the marks, there is no grid clutter, legends are one row of chips. Only the trace types the app's figures use
are drawn (bar, scatter, box); the rest is ignored. Layout in design units, scaled by `u`."""
import base64
import math

import numpy as np

from beatles_viz.config import ACCENT, INK, MUTED, PAPER, RULE
from beatles_viz.render.card_kit import font, mix, rgb, text_width
from beatles_viz.viz.theme import COLORWAY


def nice_ticks(lo, hi, n=5):
    n = max(int(n), 2)
    span = (hi - lo) or 1.0
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    ticks, v = [], math.floor(lo / step) * step
    while v <= hi + step * 1e-9:
        ticks.append(round(v, 10))
        v += step
    return ticks


def number(v, ref):
    """A value as written on a mark: no decimals from 10 up, one from 1, two below."""
    ref = abs(ref)
    return f"{v:.0f}" if ref >= 10 else f"{v:.1f}" if ref >= 1 else f"{v:.2f}"


def _tick_text(v, step, percent=False):
    if percent:
        return f"{v * 100:.0f}%"
    text = f"{v:.0f}" if step >= 1 else f"{v:.1f}" if step >= .1 else f"{v:.2f}"
    return text[1:] if text.strip("-0.") == "" and text.startswith("-") else text


def _arr(v):
    """Trace data as a list: Plotly 6 (and Streamlit, on a figure it has sent) may hold arrays as {dtype, bdata}."""
    if v is None:
        return None
    if isinstance(v, dict) and "bdata" in v:
        return np.frombuffer(base64.b64decode(v["bdata"]), dtype=v["dtype"]).tolist()
    return list(v)


def _color(trace, i, n):
    for c in (getattr(trace.marker, "color", None), getattr(getattr(trace, "line", None), "color", None)):
        if isinstance(c, str):
            return c
    return COLORWAY[i % len(COLORWAY)]


def _points(trace):
    """(categories, values) of a trace, whichever way it points."""
    x, y = _arr(trace.x), _arr(trace.y)
    if trace.orientation == "h":
        return [str(c) for c in y], x
    return [str(c) for c in (x if x is not None else range(len(y)))], y


def _categories(fig, traces, axis):
    order = getattr(fig.layout, axis).categoryarray
    seen = []
    for t in traces:
        for c in _points(t)[0]:
            if c not in seen:
                seen.append(c)
    return [c for c in order if c in seen] if order else seen


def _legend(d, traces, x, y, w, u):
    """One row of chips; returns the height used (0 when a legend would add nothing)."""
    items, names = [], set()
    for i, t in enumerate(traces):
        if t.showlegend is False or not t.name or t.name in names:
            continue
        if t.type == "bar" and not isinstance(t.marker.color, str):
            continue
        names.add(t.name)
        line = t.type == "scatter" and "lines" in (t.mode or "")
        items.append((t.name, _color(t, i, len(traces)), line))
    if len(items) < 2:
        return 0
    fs, cx, cy = 24 * u, x, y
    for name, color, line in items:
        tw = d.textlength(name, font=font(fs, "label"))
        if cx + 36 * u + tw > x + w and cx > x:
            cx, cy = x, cy + 36 * u
        if line:
            d.rectangle([cx, cy + 10 * u, cx + 26 * u, cy + 17 * u], fill=rgb(color)[:3])
        else:
            d.ellipse([cx + 3 * u, cy + 3 * u, cx + 21 * u, cy + 21 * u], fill=rgb(color)[:3])
        d.text((cx + 34 * u, cy - 2 * u), name, fill=INK, font=font(fs, "label"))
        cx += 34 * u + tw + 28 * u
    return cy + 36 * u - y


def draw_figure(d, fig, box, u=1.0):
    """Draw `fig` inside box = (x0, y0, x1, y1) in pixels; `u` scales the design units of the type and marks."""
    traces = [t for t in fig.data if t.type in ("bar", "scatter", "box") and t.visible is not False]
    if not traces:
        return
    x0, y0, x1, y1 = box
    horizontal = any(t.type == "bar" and t.orientation == "h" for t in traces)
    cats = _categories(fig, traces, "yaxis" if horizontal else "xaxis")
    if not cats:
        return
    all_values = [float(v) for t in traces for v in (_points(t)[1] if t.type != "box" else _arr(t.y)) if v is not None and v == v]
    if not all_values:
        return
    has_bars = any(t.type == "bar" for t in traces)
    stacked = not horizontal and fig.layout.barmode in ("stack", "relative")
    lo, hi = min(all_values), max(all_values)
    if stacked:
        totals = {}
        for t in traces:
            if t.type == "bar":
                for c_, v_ in zip(*_points(t)):
                    totals[c_] = totals.get(c_, 0) + float(v_ or 0)
        hi = max(totals.values())
    percent = (fig.layout.yaxis.tickformat or "").endswith("%") and not horizontal
    if has_bars:
        lo, hi = min(lo, 0), max(hi, 0)
    else:
        pad = (hi - lo) * .06 or 1
        lo, hi = (max(lo - 2 * pad, 0) if lo >= 0 else lo - 2 * pad), hi + pad
    diverging = horizontal and lo < 0 < hi
    ticks = nice_ticks(lo, hi, (y1 - y0) / (70 * u) if not horizontal else 5)
    lo, hi = (min(lo, ticks[0]), max(hi, ticks[-1])) if not diverging else (lo * 1.1, hi * 1.1)
    step = ticks[1] - ticks[0] if len(ticks) > 1 else 1

    value_title = (fig.layout.xaxis.title.text if horizontal else fig.layout.yaxis.title.text) or ""
    cat_title = (fig.layout.yaxis.title.text if horizontal else fig.layout.xaxis.title.text) or ""
    value_title = value_title.replace("<br>", " ")

    # Header row: the value-axis title, then the legend
    top = y0
    if value_title and not horizontal:
        d.text((x0, top), value_title, fill=MUTED, font=font(26 * u, "label"))
        top += 40 * u
    top += _legend(d, traces, x0, top, x1 - x0, u) + (8 * u if len(traces) > 1 else 0)

    tick_fs = 26 * u
    label_fs = 28 * u
    n = len(cats)

    if horizontal:
        bottom = y1 - (44 * u if value_title else 0) - (0 if diverging else 40 * u)
        row = (bottom - top) / n
        cat_fs = max(min(label_fs, row * .62), 14 * u)
        label_w = 0 if diverging else max(d.textlength(c, font=font(cat_fs)) for c in cats) + 18 * u
        left, right = x0 + label_w, x1 - (0 if diverging else 64 * u)
        scale = lambda v: left + (v - lo) / (hi - lo) * (right - left)
        zero = scale(0)
        for tk in ([] if diverging else ticks):
            tx = scale(tk)
            d.line([tx, top, tx, bottom], fill=RULE, width=max(int(u), 1))
            d.text((tx, bottom + 8 * u), _tick_text(tk, step), fill=INK, font=font(tick_fs * .9, "label"), anchor="ma")
        d.line([zero, top, zero, bottom], fill=INK, width=max(int(2.5 * u), 2))
        for i, c in enumerate(cats):
            cy = bottom - (i + .5) * row
            for ti, t in enumerate(traces):
                if t.type != "bar":
                    continue
                tc, tv = _points(t)
                if c not in tc:
                    continue
                v = float(tv[tc.index(c)])
                colors = t.marker.color
                col = colors[tc.index(c)] if isinstance(colors, (list, tuple, np.ndarray)) else _color(t, ti, len(traces))
                half = row * .31
                xa, xb = sorted((zero, scale(v)))
                d.rectangle([xa, cy - half, xb, cy + half], fill=rgb(col)[:3])
                if diverging:
                    tw = d.textlength(c, font=font(cat_fs))
                    d.text((xb + 12 * u, cy) if v > 0 else (xa - 12 * u, cy), c, fill=INK, font=font(cat_fs, "strong"),
                           anchor="lm" if v > 0 else "rm")
                else:
                    d.text((xb + 10 * u, cy), number(v, hi), fill=INK, font=font(cat_fs * .9, "label"), anchor="lm")
        if not diverging:
            for i, c in enumerate(cats):
                d.text((x0, bottom - (i + .5) * row), c, fill=INK, font=font(cat_fs), anchor="lm")
        if value_title:
            d.text(((x0 + x1) / 2, y1), value_title, fill=MUTED, font=font(24 * u, "label"), anchor="ms")
        return

    # Vertical: categories along the bottom
    cat_fs = label_fs
    slot_guess = (x1 - x0) / n
    cat_lines = {c: c.replace("<br>", "\n").split("\n") for c in cats}
    longest = lambda: max(d.textlength(l, font=font(cat_fs)) for ls in cat_lines.values() for l in ls)
    while cat_fs > 16 * u and longest() > slot_guess * .94:
        cat_fs -= u
    rows = max(len(ls) for ls in cat_lines.values())
    bottom = y1 - (rows * cat_fs * 1.15 + 26 * u) - (36 * u if cat_title else 0)
    label_w = max(d.textlength(_tick_text(tk, step, percent), font=font(tick_fs * .9, "label")) for tk in ticks) + 14 * u
    left, right = x0 + label_w, x1
    scale = lambda v: bottom - (v - lo) / (hi - lo) * (bottom - top - 28 * u)
    slot = (right - left) / n
    for tk in ticks:
        ty = scale(tk)
        d.line([left, ty, right, ty], fill=RULE, width=max(int(u), 1))
        d.text((left - 10 * u, ty), _tick_text(tk, step, percent), fill=INK, font=font(tick_fs * .9, "label"), anchor="rm")
    d.line([left, scale(lo if not has_bars else 0), right, scale(lo if not has_bars else 0)], fill=INK, width=max(int(2.5 * u), 2))
    d.line([left, top, left, bottom], fill=INK, width=max(int(2.5 * u), 2))
    if lo < 0 < hi:
        d.line([left, scale(0), right, scale(0)], fill=INK, width=max(int(1.5 * u), 1))
    for i, c in enumerate(cats):
        for j, line in enumerate(cat_lines[c]):
            d.text((left + (i + .5) * slot, bottom + 10 * u + j * cat_fs * 1.15), line, fill=INK if j == 0 else MUTED,
                   font=font(cat_fs, "strong" if j == 0 else "body"), anchor="ma")
    if cat_title:
        d.text(((left + right) / 2, y1), cat_title, fill=MUTED, font=font(24 * u, "label"), anchor="ms")

    bars = [(i, t) for i, t in enumerate(traces) if t.type == "bar"]
    rng = np.random.default_rng(7)
    base = {}
    for i, t in bars:
        k = 0 if stacked else bars.index((i, t))
        width = slot * (.7 if stacked else .62) / (1 if stacked else len(bars))
        tc, tv = _points(t)
        for c, v in zip(tc, tv):
            if c not in cats or v is None:
                continue
            colors = t.marker.color
            col = colors[tc.index(c)] if isinstance(colors, (list, tuple, np.ndarray)) else _color(t, i, len(traces))
            cx = left + (cats.index(c) + .5) * slot + (k - (len(bars) - 1) / 2) * width * (0 if stacked else 1)
            if stacked:
                b0 = base.get(c, 0)
                base[c] = b1 = b0 + float(v)
                ya, yb = sorted((scale(b0), scale(b1)))
                d.rectangle([cx - width / 2, ya, cx + width / 2, yb], fill=rgb(col)[:3], outline=PAPER, width=int(2 * u))
                if yb - ya > 44 * u and float(v) >= .04 * hi:
                    dark = sum(rgb(col)[:3]) < 480
                    txt = f"{float(v) * 100:.0f}%" if percent else number(float(v), hi)
                    d.text((cx, (ya + yb) / 2), txt, fill=PAPER if dark else INK, font=font(26 * u, "label"), anchor="mm")
                continue
            ya, yb = sorted((scale(0), scale(float(v))))
            d.rectangle([cx - width / 2, ya, cx + width / 2, yb], fill=rgb(col)[:3])
            if n * len(bars) <= 12:
                d.text((cx, ya - 8 * u), number(float(v), hi), fill=INK, font=font(34 * u, "title"), anchor="mb")
    for i, t in enumerate(traces):
        if t.type == "box":
            _boxes(d, t, _color(t, i, len(traces)), cats, left, slot, scale, u, rng)
    for i, t in enumerate(traces):
        if t.type != "scatter":
            continue
        tc, tv = _points(t)
        col = rgb(_color(t, i, len(traces)))[:3]
        pts = [(left + (cats.index(c) + .5) * slot, scale(float(v))) for c, v in zip(tc, tv) if c in cats]
        if "lines" in (t.mode or "") and len(pts) > 1:
            d.line(pts, fill=col, width=int(7 * u), joint="curve")
        if "markers" in (t.mode or "markers"):
            for px_, py_ in pts:
                d.ellipse([px_ - 9 * u, py_ - 9 * u, px_ + 9 * u, py_ + 9 * u], fill=col, outline=PAPER, width=int(2 * u))
        if "lines" in (t.mode or "") and len(pts) > 1:
            ref = max(abs(float(v)) for v in tv)
            for j in (0, len(pts) - 1):
                px_, py_ = pts[j]
                above = all(py_ <= _y(o, cats, scale, tc[j]) for o in traces if o is not t and o.type == "scatter") \
                    or py_ + 60 * u > bottom
                d.text((px_, py_ - 18 * u if above else py_ + 18 * u), number(float(tv[j]), ref), fill=col,
                       font=font(30 * u, "title"), anchor="mb" if above else "mt", stroke_width=int(4 * u), stroke_fill=PAPER)


def _y(trace, cats, scale, cat):
    tc, tv = _points(trace)
    return scale(float(tv[tc.index(cat)])) if cat in tc else float("inf")


def _boxes(d, t, color, cats, left, slot, scale, u, rng):
    ys = [float(v) for v in _arr(t.y) if v is not None and v == v]
    xs = [str(c) for c in _arr(t.x)] if t.x is not None else [cats[0]] * len(ys)
    invisible = rgb(getattr(t.line, "color", None), "#000000")[3] == 0
    fill = t.fillcolor if isinstance(t.fillcolor, str) else color
    solid = rgb(fill)[:3] if rgb(fill)[3] > 0 else rgb(color)[:3]
    for c in dict.fromkeys(xs):
        vals = np.array([y for y, x in zip(ys, xs) if x == c])
        if c not in cats or not len(vals):
            continue
        cx = left + (cats.index(c) + .5) * slot
        half = slot * .26
        if not invisible and len(vals) >= 4:
            q1, med, q3 = np.percentile(vals, [25, 50, 75])
            d.rectangle([cx - half, scale(q3), cx + half, scale(q1)], fill=mix(solid, PAPER, .22), outline=INK, width=int(2 * u))
            d.line([cx - half, scale(med), cx + half, scale(med)], fill=INK, width=int(5 * u))
        if t.boxpoints in ("all", "outliers", None) and invisible or t.boxpoints == "all":
            jit = rng.uniform(-half * .9, half * .9, len(vals))
            for j, v in zip(jit, vals):
                px_, py_ = cx + j, scale(float(v))
                d.ellipse([px_ - 7.5 * u, py_ - 7.5 * u, px_ + 7.5 * u, py_ + 7.5 * u], fill=solid, outline=PAPER, width=int(1.5 * u))
