"""Changes across the discography: words that drift, song architecture and lead voices, period by period."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from beatles_viz.config import PHASES
from beatles_viz.corpus import doc_frequencies
from beatles_viz.text.tokenize import content_counter, is_content, merge

FIRST, LAST = PHASES[0][0], PHASES[-1][0]
SECTION_GROUPS = {"verse": "verse", "chorus": "chorus", "bridge": "bridge", "outro": "outro"}  # anything else: "other"
GROUP_ORDER = ["verse", "chorus", "bridge", "outro", "other"]


def rates(d, words):
    """Rate of each word in each song (share of the song's words), songs in the rows."""
    return pd.DataFrame({w: d.bow.map(lambda b: b.get(w, 0)).to_numpy() / d.tokens.to_numpy() for w in words},
                        index=d.index)


def fdr(p):
    """Benjamini-Hochberg q-values: the false discovery rate at which each test would be kept."""
    p = np.asarray(p, dtype=float)
    if not len(p):
        return p
    order = np.argsort(p)
    q = p[order] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1].clip(max=1)
    out = np.empty_like(q)
    out[order] = q
    return out


def word_trends(d, min_songs=10):
    """One row per content word used in at least min_songs songs: rank correlation between release year and the
    word's rate in each song (rho, p, and q corrected for the number of words tested); the pooled rate per 1,000
    words in the first and last periods (first, last, change); and the mean of the songs' rates (first_song,
    last_song, change_song), where a long song weighs no more than a short one."""
    songs = doc_frequencies(d)
    words = [w for w, n in songs.items() if n >= min_songs and is_content(w)]
    r = rates(d, words)
    per_1000 = {p: content_counter(merge(d[d.phase == p].bow)) for p in (FIRST, LAST)}
    size = {p: d[d.phase == p].tokens.sum() for p in per_1000}
    song_mean = {p: 1000 * r[(d.phase == p).to_numpy()].mean() for p in (FIRST, LAST)}
    rows = []
    for w in words:
        rho, p = spearmanr(d.year, r[w])
        first, last = (1000 * per_1000[ph].get(w, 0) / size[ph] for ph in (FIRST, LAST))
        fs, ls = song_mean[FIRST][w], song_mean[LAST][w]
        rows.append((w, rho, p, songs[w], first, last, last - first, fs, ls, ls - fs))
    out = pd.DataFrame(rows, columns=["word", "rho", "p", "songs", "first", "last", "change", "first_song",
                                      "last_song", "change_song"])
    out["q"] = fdr(out.p)
    return out


def steady_movers(trends, top=8, alpha=0.05, exclude=()):
    """The words that rise and fall most steadily: rank correlation with p < alpha (uncorrected: leads to check)
    that agrees with the change of the songs' mean rate between the first and last period, largest change first.
    Words that still hold once corrected for the number of tests (q < alpha, column held) are always kept."""
    sig = trends[(trends.p < alpha) & (np.sign(trends.rho) == np.sign(trends.change_song))
                 & ~trends.word.isin(exclude)].assign(held=lambda t: t.q < alpha)
    rising, falling = sig[sig.rho > 0], sig[sig.rho < 0]
    picked = pd.concat([rising.nlargest(top, "change_song"), rising[rising.held],
                        falling.nsmallest(top, "change_song"), falling[falling.held]]).drop_duplicates("word")
    picked["direction"] = np.where(picked.rho > 0, "rising", "falling")
    return picked.sort_values("change_song", ascending=False).reset_index(drop=True)


def change_interval(d, words, n_boot=2000, level=0.95, seed=0):
    """Bootstrap interval of change_song (per 1,000 words): songs are resampled within the first and the last
    period. One row per word: ci_low, ci_high."""
    rng = np.random.default_rng(seed)
    a = 1000 * rates(d[d.phase == FIRST], words).to_numpy()
    b = 1000 * rates(d[d.phase == LAST], words).to_numpy()
    if not len(a) or not len(b):
        return pd.DataFrame({"word": list(words), "ci_low": np.nan, "ci_high": np.nan})
    diffs = (b[rng.integers(0, len(b), (n_boot, len(b)))].mean(axis=1)
             - a[rng.integers(0, len(a), (n_boot, len(a)))].mean(axis=1))
    lo, hi = np.quantile(diffs, [(1 - level) / 2, (1 + level) / 2], axis=0)
    return pd.DataFrame({"word": list(words), "ci_low": lo, "ci_high": hi})


def section_shares(d):
    """Share of sung words in verses, choruses, bridges, outros and the rest, per period."""
    rows = [(p, SECTION_GROUPS.get(k, "other"), w)
            for p, kinds, words in zip(d.phase, d.sec_kinds, d.sec_words) for k, w in zip(kinds, words)]
    g = pd.DataFrame(rows, columns=["phase", "kind", "words"]).groupby(["phase", "kind"]).words.sum().unstack(fill_value=0)
    g = g.reindex(columns=[k for k in GROUP_ORDER if k in g])
    return g.div(g.sum(axis=1), axis=0)


def voice_shares(d):
    """Share of songs led by each voice, per period, with the number of songs."""
    counts = pd.crosstab(d.phase, d.voice)
    return counts.div(counts.sum(axis=1), axis=0), counts.sum(axis=1)
