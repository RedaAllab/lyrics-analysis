from beatles_viz.effects.base import Effect, map_words, register


@register
class Starr(Effect):
    """Rounded font, primary colours, the first word of each line bounces on a beat."""
    name = "starr"
    summary = "rounded font, first word of each line bounces"
    font = 'Nunito, "Varela Round", "Arial Rounded MT Bold", "Trebuchet MS", sans-serif'
    defaults = {"bg": "#fffbe6", "fg": "#1d3557", "accent": "#c1121f", "bounce": 4, "tempo": 1.2}
    ranges = {"bounce": (0, 10, 1), "tempo": (0.4, 3.0, 0.1)}
    text_keys = ("fg", "accent")

    def extra_css(self, c, p):
        return (f"{c} .fx-bounce{{display:inline-block;color:{p['accent']};font-weight:700;"
                f"animation:fx-starr-bounce {p['tempo']}s ease-in-out infinite;}}\n"
                f"@keyframes fx-starr-bounce{{0%,100%{{transform:translateY(0)}}"
                f"50%{{transform:translateY({-p['bounce']}px)}}}}\n")

    def wrap_line(self, line, p, ctx):
        state = {"done": False}
        delay = ctx.get("line_in_section", 0) * 0.1

        def word(esc, raw):
            if state["done"]:
                return esc
            state["done"] = True
            return f'<span class="fx-bounce" style="animation-delay:{delay:.1f}s">{esc}</span>'

        return map_words(line, word)
