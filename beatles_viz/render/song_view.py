import html

from beatles_viz.attribution import resolve_voice, section_members
from beatles_viz.config import NEUTRAL, SHARED, VOICE_COLORS, VOICE_ORDER
from beatles_viz.effects import get_effect
from beatles_viz.text.sections import section_name
from beatles_viz.text.segment import AUTO

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Courier+Prime&family=Nunito:wght@400;700&display=swap');"


MOTION = {
    "calm": ".fx,.fx *{animation-iteration-count:1 !important;}\n",  # each effect plays once, then the text rests
    "loop": "",
    "off": ".fx,.fx *{animation:none !important;opacity:1 !important;}\n",
}


def base_css(font_size, motion="calm"):
    return (f"{FONTS}\n"
            f".fx-song{{font-size:{font_size}rem;max-width:46rem;margin:0 auto;}}\n"
            ".fx{padding:.9rem 1.2rem;margin:.7rem 0;border-radius:6px;}\n"
            ".fx-head{font-family:system-ui,sans-serif;font-size:.8em;text-transform:uppercase;letter-spacing:.08em;"
            "opacity:.85;margin-bottom:.4rem;display:flex;gap:.6rem;align-items:center;}\n"
            ".fx-legend{display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;font-family:system-ui,sans-serif;font-size:.8em;"
            "margin:.2rem 0 .6rem;}\n"
            ".fx-dot{display:inline-block;width:.75em;height:.75em;border-radius:50%;margin-right:.35em;"
            "vertical-align:-.05em;}\n"
            ".fx-badge{border:1px solid currentColor;border-radius:999px;padding:0 .5em;}\n"
            ".fx-voice{margin-left:auto;font-weight:600;}\n"
            ".fx-l{margin:.1rem 0;}\n"
            ".fx-instr{font-style:italic;opacity:.7;}\n"
            "@media (prefers-reduced-motion: reduce){.fx,.fx *{animation:none !important;opacity:1 !important;}}\n"
            + MOTION[motion])


def voice_label(voice, members):
    return " & ".join(sorted(members)) if voice == SHARED and members else voice


def render_section(section, lead_vocal, effects_on, params, doc_freq):
    members = section_members(section, lead_vocal)
    voice = resolve_voice(section, lead_vocal) if effects_on else NEUTRAL
    effect = get_effect(voice)
    p = effect.params(params.get(effect.name))
    ctx = {"members": members, "doc_freq": doc_freq}
    lines = "".join(f'<div class="fx-l">{effect.wrap_line(l, p, {**ctx, "line_in_section": i})}</div>'
                    for i, l in enumerate(section.lines))
    repeat = f'<span class="fx-badge">x{section.repeat}</span>' if section.repeat > 1 else ""
    shown_voice = voice_label(resolve_voice(section, lead_vocal), members)
    guess = '<span class="fx-badge" title="No tag in the source: section detected">detected</span>' \
        if section.label == AUTO else ""
    head = (f'<div class="fx-head"><span>{html.escape(section_name(section))}</span>{repeat}{guess}'
            f'<span class="fx-voice">{html.escape(shown_voice)}</span></div>')
    body = lines or '<div class="fx-instr">instrumental</div>'
    return effect, p, effect.wrap_section(head + body, section, p, ctx)


def legend(voices):
    items = []
    for voice in sorted(voices, key=lambda v: VOICE_ORDER.index(v) if v in VOICE_ORDER else 99):
        color = VOICE_COLORS.get(voice, "#999999")
        items.append(f'<span><span class="fx-dot" style="background:{color}"></span><b>{html.escape(voice)}</b>: '
                     f'{html.escape(get_effect(voice).summary)}</span>')
    return f'<div class="fx-legend">{"".join(items)}</div>'


def render_song(song, effects_on=True, params=None, doc_freq=None, font_size=1.05, motion="calm"):
    """HTML for a whole song: a legend of the voices, then one block per section styled by its voice."""
    used, blocks, voices = {}, [], set()
    for s in song.sections:
        effect, p, block = render_section(s, song.lead_vocal, effects_on, params or {}, doc_freq or {})
        used[effect.name] = effect.css(p)
        voices.add(resolve_voice(s, song.lead_vocal))
        blocks.append(block)
    css = base_css(font_size, motion) + "".join(used.values())
    head = legend(voices) if effects_on else ""
    return f"<style>{css}</style><div class=\"fx-song\">{head}{''.join(blocks)}</div>"
