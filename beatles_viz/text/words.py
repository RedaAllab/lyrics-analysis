"""Statistics about one word across the corpus: usage over time, by voice, top songs, companion words."""
from collections import Counter

import pandas as pd

from beatles_viz.text.keyness import monroe, prior
from beatles_viz.text.tokenize import content_counter, merge


def normalize_word(raw):
    return str(raw).strip().lower().replace("’", "'")


def occurrences(corpus, word):
    return corpus.bow.map(lambda c: c.get(word, 0))


def usage_by(corpus, word, key):
    d = corpus.assign(n=occurrences(corpus, word))
    g = d.groupby(key).agg(occurrences=("n", "sum"), words=("tokens", "sum"), songs=("n", lambda s: int((s > 0).sum())),
                           total_songs=("title", "count")).reset_index()
    g["per_1000"] = 1000 * g.occurrences / g.words.where(g.words > 0)
    return g


def top_songs(corpus, word, k=10):
    d = corpus.assign(occurrences=occurrences(corpus, word))
    d = d[d.occurrences > 0].copy()
    d["share"] = d.occurrences / d.tokens
    return d.sort_values(["occurrences", "share"], ascending=False).head(k)[
        ["title", "year", "voice", "occurrences", "share"]].reset_index(drop=True)


def companions(corpus, word, k=15):
    """Words over-represented in the songs that use the word, compared with the songs that do not."""
    has = occurrences(corpus, word) > 0
    if not has.any() or has.all():
        return pd.DataFrame(columns=["word", "in_group", "in_rest", "z"])
    a, b = content_counter(merge(corpus[has].bow)), content_counter(merge(corpus[~has].bow))
    a.pop(word, None)
    b.pop(word, None)
    return monroe(a, b, prior(a + b)).head(k).reset_index(drop=True)


def vocabulary(corpus, min_count=3):
    c = content_counter(merge(corpus.bow))
    return sorted((w for w, n in c.items() if n >= min_count), key=lambda w: -c[w]), Counter(c)
