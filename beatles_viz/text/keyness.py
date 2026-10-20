import math

import pandas as pd

from beatles_viz.text.tokenize import content_counter, merge


def monroe(counts_a, counts_b, prior, a0=200, min_count=5):
    """z-scored log-odds with an informative Dirichlet prior (Monroe et al. 2008)."""
    na, nb = sum(counts_a.values()), sum(counts_b.values())
    rows = []
    for w, p in prior.items():
        aw = a0 * p
        ya, yb = counts_a.get(w, 0), counts_b.get(w, 0)
        if ya + yb < min_count:
            continue
        d = math.log((ya + aw) / (na + a0 - ya - aw)) - math.log((yb + aw) / (nb + a0 - yb - aw))
        rows.append((w, ya, yb, d / math.sqrt(1 / (ya + aw) + 1 / (yb + aw))))
    return pd.DataFrame(rows, columns=["word", "in_group", "in_rest", "z"]).sort_values("z", ascending=False)


def prior(counter):
    total = sum(counter.values()) or 1
    return {w: n / total for w, n in counter.items()}


def contrast(counts_a, counts_b, min_count=5):
    """Content words over-represented in A against B, with the pooled vocabulary of both as prior."""
    a, b = content_counter(counts_a), content_counter(counts_b)
    return monroe(a, b, prior(a + b), min_count=min_count)


def song_keyness(song_bow, corpus_bows):
    """Words of one song over-represented against the other songs."""
    song = content_counter(song_bow)
    r = contrast(song, content_counter(merge(corpus_bows)) - song, min_count=3)
    return r[r.in_group > 0]
