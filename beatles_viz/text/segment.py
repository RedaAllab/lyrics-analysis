"""Guess verses and choruses when the lyrics have no section tags (21 songs).

Stanzas are the blank-line blocks of the text. A stanza that comes back (same words as another stanza, or most of
its lines sung elsewhere in the song) is a chorus, the others are verses: the self-similarity idea used to segment
the WASABI corpus, reduced to what a song of 15 to 50 lines needs. A text without blank lines is cut into runs of
repeated and new lines instead."""
import re

from beatles_viz.text.sections import TAG, Section, header_tags, split_sections
from beatles_viz.text.tokenize import tokenize

AUTO = "auto"  # label of detected sections, so the views can say they are a guess
STANZA_MATCH = 0.5  # word-set overlap between two stanzas that count as the same chorus
LINES_MATCH = 0.6  # share of a stanza's lines sung elsewhere in the song
SAME_STANZA = 0.9  # near-identical stanzas: the chorus of a song where everything else also repeats
BLANK = re.compile(r"\n\s*\n")


def _stanzas(lyrics_raw):
    stanzas = []
    for block in BLANK.split(str(lyrics_raw)):
        lines = [TAG.sub("", l).strip() for l in block.split("\n") if header_tags(l) is None]
        lines = [l for l in lines if l]
        if lines:
            stanzas.append(lines)
    return stanzas


def _key(line):
    return " ".join(tokenize(line))


def _overlap(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def _label(kinds, blocks):
    sections, verse = [], 0
    for kind, lines in zip(kinds, blocks):
        number = None
        if kind == "verse":
            verse += 1
            number = verse
        sections.append(Section(kind, AUTO, number, frozenset(), lines, 1))
    return sections


def _from_stanzas(stanzas):
    keys = [[_key(l) for l in s] for s in stanzas]
    sets = [set(tokenize(" ".join(s))) for s in stanzas]
    kinds, closest = [], []
    for i, s in enumerate(stanzas):
        elsewhere = {k for j, ks in enumerate(keys) if j != i for k in ks}
        lines_back = sum(k in elsewhere for k in keys[i] if k) / max(1, len(keys[i]))
        closest.append(max(_overlap(sets[i], sets[j]) for j in range(len(stanzas)) if j != i))
        kinds.append("chorus" if closest[i] >= STANZA_MATCH or lines_back >= LINES_MATCH else "verse")
    if "verse" not in kinds:
        # every stanza comes back: a strophic song, unless some stanzas are exact returns of each other
        kinds = ["chorus" if c >= SAME_STANZA else "verse" for c in closest]
    return kinds


def _from_lines(lines):
    keys = [_key(l) for l in lines]
    repeated = [bool(k) and keys.count(k) > 1 for k in keys]
    runs = []
    for line, rep in zip(lines, repeated):
        if runs and runs[-1][0] == rep:
            runs[-1][1].append(line)
        else:
            runs.append((rep, [line]))
    # a lone repeated line inside a verse is a hook, not a chorus
    runs = [(rep and len(ls) > 1, ls) for rep, ls in runs]
    merged = []
    for rep, ls in runs:
        if merged and merged[-1][0] == rep:
            merged[-1][1].extend(ls)
        else:
            merged.append((rep, list(ls)))
    return ["chorus" if rep else "verse" for rep, _ in merged], [ls for _, ls in merged]


def detect_sections(lyrics_raw):
    """Verse / chorus sections for untagged lyrics, or None when nothing repeats (no structure to find)."""
    stanzas = _stanzas(lyrics_raw)
    if len(stanzas) > 1:
        kinds, blocks = _from_stanzas(stanzas), stanzas
    elif stanzas:
        kinds, blocks = _from_lines(stanzas[0])
    else:
        return None
    if "chorus" not in kinds or len(blocks) < 2:
        return None
    return _label(kinds, blocks)


def is_untagged(sections):
    return len(sections) == 1 and sections[0].kind == "song"


def song_sections(lyrics_raw):
    """Sections from the Genius tags, or detected ones when the text has no tags."""
    sections = split_sections(lyrics_raw)
    if is_untagged(sections):
        return detect_sections(lyrics_raw) or sections
    return sections


def is_detected(sections):
    return any(s.label == AUTO for s in sections)
