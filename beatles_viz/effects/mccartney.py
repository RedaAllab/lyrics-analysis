import html

from beatles_viz.config import CARD, INK, VOICE_COLORS
from beatles_viz.effects.base import Effect, register


@register
class McCartney(Effect):
    """Readable serif, lines fade in one after another, choruses slightly larger."""
    name = "mccartney"
    summary = "warm serif, lines fade in, larger choruses"
    font = 'Georgia, "Times New Roman", serif'
    defaults = {"bg": CARD, "fg": INK, "accent": VOICE_COLORS["McCartney"], "speed": 0.25, "chorus_scale": 1.12}
    ranges = {"speed": (0.0, 1.0, 0.05), "chorus_scale": (1.0, 1.4, 0.02)}

    def extra_css(self, c, p):
        return (f"{c} .fx-in{{display:inline-block;opacity:0;animation:fx-mccartney-in .7s ease-out forwards;}}\n"
                f"@keyframes fx-mccartney-in{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:none}}}}\n"
                f"{c}.fx-kind-chorus .fx-l{{font-size:{p['chorus_scale']}em;}}\n")

    def wrap_line(self, line, p, ctx):
        delay = ctx.get("line_in_section", 0) * p["speed"]
        return f'<span class="fx-in" style="animation-delay:{delay:.2f}s">{html.escape(line)}</span>'
