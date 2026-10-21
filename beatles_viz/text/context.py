"""Words that stand near a word in the sung text, not just in the same song: a window of a few words around each
occurrence tells the senses of a word apart better than the whole song does.

Only pairs of content words and their counts are kept (no order, no grammatical words), so the public file can carry
them without giving the lyrics back."""
from collections import Counter

from beatles_viz.text.keyness import contrast
from beatles_viz.text.tokenize import content_counter, is_content, merge

SPAN = 5  # words on each side


def window_pairs(words, span=SPAN):
    """Counter {(word, neighbour): n} over content words at most span positions apart, both directions."""
    pairs = Counter()
    for i, a in enumerate(words):
        if not is_content(a):
            continue
        for b in words[i + 1:i + 1 + span]:
            if b != a and is_content(b):
                pairs[(a, b)] += 1
                pairs[(b, a)] += 1
    return pairs


def neighbours_of(pair_counters, word):
    """Counter {neighbour: n} of the word over all the given songs."""
    out = Counter()
    for pairs in pair_counters:
        out.update({b: n for (a, b), n in pairs.items() if a == word})
    return out


def collocates(corpus, word, k=15, min_count=3):
    """Words over-represented within the window around the word, against every other content word of the same songs
    (log-odds, Monroe et al. 2008). Empty when the corpus has no window counts (column ctx)."""
    if "ctx" not in corpus:
        return contrast(Counter(), Counter())
    near = neighbours_of(corpus.ctx, word)
    rest = content_counter(merge(corpus.bow)) - near
    rest.pop(word, None)
    out = contrast(near, rest, min_count=min_count)
    return out[out.in_group > 0].head(k).reset_index(drop=True)


def to_lists(pairs):
    """Counter -> (["a b", ...], [n, ...]) for the parquet file, one direction only (a < b): half the size."""
    kept = [(a, b, n) for (a, b), n in pairs.items() if a < b]
    return [f"{a} {b}" for a, b, _ in kept], [int(n) for *_, n in kept]


def from_lists(keys, counts):
    out = Counter()
    for k, n in zip(keys, counts):
        a, b = k.split(" ", 1)
        out[(a, b)] = out[(b, a)] = int(n)
    return out
