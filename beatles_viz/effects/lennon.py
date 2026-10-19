from beatles_viz.effects.base import Effect, map_words, register
from beatles_viz.text.tokenize import is_content


@register
class Lennon(Effect):
    """Typewriter font, cold high-contrast palette, rare words drift and blur slightly."""
    name = "lennon"
    summary = "typewriter font, rare words drift and blur"
    font = '"Courier Prime", "Courier New", Courier, monospace'
    defaults = {"bg": "#eaf0f6", "fg": "#0b2545", "accent": "#1f4e79", "wave": 0.5, "rare_max_songs": 2}
    ranges = {"wave": (0.0, 1.0, 0.05), "rare_max_songs": (1, 10, 1)}
    text_keys = ("fg", "accent")

    def extra_css(self, c, p):
        w = p["wave"]
        return (f"{c} .fx-rare{{display:inline-block;color:{p['accent']};font-weight:700;"
                f"animation:fx-lennon-wave 3.2s ease-in-out infinite;}}\n"
                f"@keyframes fx-lennon-wave{{0%,100%{{transform:translateY(0);filter:blur(0)}}"
                f"50%{{transform:translateY({-3 * w:.2f}px) skewX({-4 * w:.1f}deg);filter:blur({0.7 * w:.2f}px)}}}}\n")

    def wrap_line(self, line, p, ctx):
        doc_freq = ctx.get("doc_freq", {})

        def word(esc, raw):
            w = raw.lower().replace("’", "'")
            rare = is_content(w) and doc_freq.get(w, 0) <= p["rare_max_songs"]
            return f'<span class="fx-rare">{esc}</span>' if rare else esc

        return map_words(line, word)
