from collections import Counter

import numpy as np

from beatles_viz.config import MATTR_WINDOW
from beatles_viz.text.sections import all_lines
from beatles_viz.text.tokenize import tokenize

PRONOUNS = {"first_singular": {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"},
            "second": {"you", "your", "yours", "yourself", "you're", "you've", "you'll", "you'd"},
            "first_plural": {"we", "us", "our", "ours", "ourselves", "we're", "we've", "we'll", "we'd"}}


def mattr(words, window=MATTR_WINDOW):
    if len(words) < window:
        return np.nan
    c = Counter(words[:window])
    vals = [len(c)]
    for i in range(window, len(words)):
        c[words[i]] += 1
        c[words[i - window]] -= 1
        if c[words[i - window]] == 0:
            del c[words[i - window]]
        vals.append(len(c))
    return float(np.mean(vals)) / window


def repeat_ratio(lines):
    words = tokenize("\n".join(lines))
    if not words:
        return np.nan
    unique = tokenize("\n".join(dict.fromkeys(l.strip().lower() for l in lines)))
    return 1 - len(unique) / len(words)


def pronoun_shares(counter):
    total = sum(counter.values()) or 1
    return {k: sum(n for w, n in counter.items() if w in v) / total for k, v in PRONOUNS.items()}


def pronoun_profile(words):
    return pronoun_shares(Counter(words))


def text_metrics(lines):
    words = tokenize("\n".join(lines))
    counts = Counter(words)
    return {"tokens": len(words), "types": len(counts), "mattr": mattr(words),
            "repeat_ratio": repeat_ratio(lines), "hapax": sum(n == 1 for n in counts.values()),
            **pronoun_profile(words)}


def song_metrics(sections):
    return text_metrics(all_lines(sections))


def section_metrics(section):
    return text_metrics(section.lines)
