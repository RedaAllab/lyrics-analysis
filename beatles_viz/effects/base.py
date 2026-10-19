import html
import re

WORD_SPLIT = re.compile(r"([A-Za-z’']+)")
REGISTRY = {}


def register(cls):
    REGISTRY[cls.name] = cls()
    return cls


def get_effect(voice):
    return REGISTRY.get(str(voice).lower(), REGISTRY["neutral"])


def map_words(line, fn):
    """Escapes a line and passes each word through fn(escaped_word, raw_word); separators stay as they are."""
    parts = WORD_SPLIT.split(line)
    return "".join(fn(html.escape(p), p) if i % 2 else html.escape(p) for i, p in enumerate(parts))


class Effect:
    name = "neutral"
    font = "inherit"
    defaults = {"bg": "#f5f5f2", "fg": "#222222", "accent": "#8a8a8a"}
    ranges = {}
    text_keys = ("fg",)  # colour params used for text, checked for contrast against bg

    def params(self, overrides=None):
        return {**self.defaults, **(overrides or {})}

    def css(self, p):
        c = f".fx-{self.name}"
        return (f"{c}{{background:{p['bg']};color:{p['fg']};font-family:{self.font};"
                f"border-left:5px solid {p['accent']};}}\n" + self.extra_css(c, p))

    def extra_css(self, c, p):
        return ""

    def section_style(self, section, p, ctx):
        return ""

    def wrap_section(self, inner, section, p, ctx):
        style = self.section_style(section, p, ctx)
        return (f'<section class="fx fx-{self.name} fx-kind-{section.kind}"'
                f'{f" style={chr(34)}{style}{chr(34)}" if style else ""}>{inner}</section>')

    def wrap_line(self, line, p, ctx):
        return html.escape(line)
