from beatles_viz.config import CARD, INK, VOICE_COLORS
from beatles_viz.effects.base import Effect, register


@register
class Harrison(Effect):
    """Airy spacing, a slow pulse like a drone."""
    name = "harrison"
    summary = "airy spacing, slow pulse like a drone"
    font = '"Palatino Linotype", Palatino, "Book Antiqua", serif'
    defaults = {"bg": CARD, "fg": INK, "accent": VOICE_COLORS["Harrison"], "period": 6.0, "line_height": 2.0}
    ranges = {"period": (2.0, 12.0, 0.5), "line_height": (1.4, 2.6, 0.1)}

    def extra_css(self, c, p):
        return (f"{c}{{line-height:{p['line_height']};letter-spacing:.03em;"
                f"animation:fx-harrison-pulse {p['period']}s ease-in-out infinite;}}\n"
                f"@keyframes fx-harrison-pulse{{0%,100%{{opacity:1}}50%{{opacity:.8}}}}\n")
