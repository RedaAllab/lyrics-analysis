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


def word_trends(d, min_songs=10):
    """One row per content word used in at least min_songs songs: rank correlation between release year and the
    word's rate in each song (rho, p), and the change of its pooled rate per 1,000 words from the first to the
    last period."""
    songs = doc_frequencies(d)
    words = [w for w, n in songs.items() if n >= min_songs and is_content(w)]
    rates = pd.DataFrame({w: d.bow.map(lambda b: b.get(w, 0)).to_numpy() / d.tokens.to_numpy() for w in words})
    per_1000 = {p: content_counter(merge(d[d.phase == p].bow)) for p in (FIRST, LAST)}
    size = {p: d[d.phase == p].tokens.sum() for p in per_1000}
    rows = []
    for w in words:
        rho, p = spearmanr(d.year, rates[w])
        first, last = (1000 * per_1000[ph].get(w, 0) / size[ph] for ph in (FIRST, LAST))
        rows.append((w, rho, p, songs[w], first, last, last - first))
    return pd.DataFrame(rows, columns=["word", "rho", "p", "songs", "first", "last", "change"])


def steady_movers(trends, top=8, alpha=0.05, exclude=()):
    """The words that rise and fall most steadily: significant rank correlation that agrees with the change of
    rate between the first and last period, largest change first."""
    sig = trends[(trends.p < alpha) & (np.sign(trends.rho) == np.sign(trends.change)) & ~trends.word.isin(exclude)]
    rising = sig[sig.rho > 0].nlargest(top, "change").assign(direction="rising")
    falling = sig[sig.rho < 0].nsmallest(top, "change").assign(direction="falling")
    return pd.concat([rising, falling]).sort_values("change", ascending=False).reset_index(drop=True)


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
