from beatles_viz.config import VOICE_COLORS
from beatles_viz.effects.base import Effect, register


@register
class Shared(Effect):
    """Several singers: a border split into the colours of the voices present, no animation."""
    name = "shared"
    summary = "border in the colours of the voices present"
    defaults = {"bg": "#f3f1f7", "fg": "#2d2640", "accent": "#7b6d8d", "border": 6}
    ranges = {"border": (2, 12, 1)}

    def section_style(self, section, p, ctx):
        colors = [VOICE_COLORS[m] for m in sorted(ctx.get("members", ())) if m in VOICE_COLORS] or [p["accent"]]
        step = 100 / len(colors)
        stops = ", ".join(f"{c} {i * step:.0f}% {(i + 1) * step:.0f}%" for i, c in enumerate(colors))
        return f"border-left:{p['border']}px solid;border-image:linear-gradient(to bottom, {stops}) 1"
