import re
from collections import namedtuple

from beatles_viz.config import MEMBER_PATTERNS, MEMBERS, REPEAT_MARK, SECTION_RULES

Section = namedtuple("Section", "kind label number singers lines repeat")

# Header line = only bracketed tags ("[Chorus]", "[Chorus] [x2]"). An unclosed "[Chorus" line is also a
# header: one Genius text has it, and a naive [^]]* regex would swallow the lyrics that follow.
TAG_LINE = re.compile(r"^\s*(?:\[[^\]\n]*\]\s*)+$")
UNCLOSED = re.compile(r"^\s*\[([^\]\n]*)$")
TAG = re.compile(r"\[([^\]\n]*)\]")
ZERO_WIDTH = re.compile(r"[\u200b\u200e\u200f\ufeff]")


def normalize_label(raw_label):
    label = ZERO_WIDTH.sub("", raw_label).strip()
    kind = next((k for k, rx in SECTION_RULES if rx.search(label)), "other")
    m = re.search(r"\d+", label)
    return kind, int(m.group()) if m else None


def parse_members(raw):
    if not raw:
        return frozenset()
    lead = re.sub(r"\(.*?\)", "", raw)
    found = {m for m in MEMBERS if MEMBER_PATTERNS[m].search(lead)}
    if not found:
        found = {m for m in MEMBERS if MEMBER_PATTERNS[m].search(raw)}
    return frozenset(found)


def header_tags(line):
    """Tags of a header line as [(label, singers)], or None for a lyric line."""
    if TAG_LINE.match(line):
        bodies = TAG.findall(line)
    elif UNCLOSED.match(line):
        bodies = [UNCLOSED.match(line).group(1)]
    else:
        return None
    return [(b.partition(":")[0].strip(), b.partition(":")[2].strip()) for b in bodies]


def repeat_count(label, singers):
    m = REPEAT_MARK.match(label) or REPEAT_MARK.match(singers)
    return int(m.group(1) or m.group(2)) if m else None


def split_sections(lyrics_raw):
    sections, label, singers, lines, repeat = [], None, "", [], 1

    def close():
        if label is None and not lines:
            return
        kind, number = normalize_label(label) if label is not None else ("other", None)
        sections.append(Section(kind, label or "", number, parse_members(singers), lines, repeat))

    for line in str(lyrics_raw).split("\n"):
        tags = header_tags(line)
        if tags is None:
            text = TAG.sub("", line).strip()  # inline annotations such as "[?]"
            if text:
                lines.append(text)
            continue
        heads = [t for t in tags if repeat_count(*t) is None]
        reps = [repeat_count(*t) for t in tags if repeat_count(*t) is not None]
        if not heads:
            # "[x2]" closes the block it follows and marks it as repeated.
            if lines:
                close()
                label, singers, lines, repeat = None, "", [], 1
            if sections and reps:
                sections[-1] = sections[-1]._replace(repeat=reps[0])
            continue
        close()
        label, singers, lines, repeat = heads[0][0], heads[0][1], [], reps[0] if reps else 1
    close()
    if len(sections) == 1 and not sections[0].label:
        sections[0] = sections[0]._replace(kind="song")
    return sections


def all_lines(sections):
    return [l for s in sections for l in s.lines]


def section_name(section):
    base = section.kind.replace("_", "-").capitalize()
    return f"{base} {section.number}" if section.number else base
