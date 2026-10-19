"""Word-level self-similarity (SongSim, Colin Morris): cell (i, j) is set when word i equals word j."""
import numpy as np

FINGERPRINT_SIZE = 48


def word_matrix(words):
    ids = {w: i for i, w in enumerate(dict.fromkeys(words))}
    codes = np.array([ids[w] for w in words])
    return codes[:, None] == codes[None, :]


def repetition_score(words):
    """Share of word pairs that are the same word: 0 = every word new, close to 1 = one word repeated."""
    n = len(words)
    if n < 2:
        return np.nan
    m = word_matrix(words)
    return float((m.sum() - n) / (n * n - n))


def fingerprint(words, size=FINGERPRINT_SIZE):
    """The matrix shrunk to size x size (share of matching cells per block), as uint8 0-255."""
    n = len(words)
    if n < 2:
        return np.zeros((1, 1), dtype=np.uint8)
    m = word_matrix(words).astype(float)
    k = min(size, n)
    edges = np.linspace(0, n, k + 1).astype(int)
    out = np.array([[m[edges[a]:edges[a + 1], edges[b]:edges[b + 1]].mean() for b in range(k)] for a in range(k)])
    return (out * 255).round().astype(np.uint8)
