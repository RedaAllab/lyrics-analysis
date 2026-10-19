"""Shared corpus loading and text metrics for the Beatles analysis and the Streamlit app."""
import math, re
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

ROOT = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
STOP = set(ENGLISH_STOP_WORDS) | {"ll", "ve", "re", "don't", "i'm", "it's", "i'll", "you're", "i've", "that's",
                                  "can't", "didn't", "won't", "isn't", "he's", "she's", "let's", "we're", "they're"}
# Vocables (non-lexical syllables) and proper names are kept in the token counts used for length and
# richness, but removed from word rankings and characteristic-word lists.
VOCABLES = {"na", "la", "da", "doo", "dee", "du", "ba", "bom", "sha", "shoo", "dum", "ob", "di", "ho", "ha",
            "ah", "ahh", "mm", "mmm", "hm", "uh", "oo", "ooh", "ooo", "woo", "wah", "bop", "ha", "tit", "ding", "dong"}
NAMES = {"john", "george", "paul", "ringo", "yoko", "jude", "julia", "sadie", "rita", "lucy", "michelle", "prudence",
         "eleanor", "rigby", "maxwell", "bungalow", "bill", "rocky", "raccoon", "martha", "desmond", "molly", "jojo",
         "loretta", "kite", "mustard", "joe", "jack", "sam", "mary", "maggie", "anna", "sgt", "pepper", "peppers", "billy", "shears"}
EXCLUDED = VOCABLES | NAMES
PHASES = [("1962-63", 1962, 1963), ("1964-65", 1964, 1965), ("1966-67", 1966, 1967), ("1968-70", 1968, 1970)]
MIN_TOKENS, MATTR_WINDOW = 30, 50

def tokenize(text):
    return WORD.findall(text.lower().replace("’", "'"))

def content(words):
    return [w for w in words if w not in STOP and w not in EXCLUDED and len(w) > 1]

def merge(counters):
    total = Counter()
    for c in counters:
        total.update(c)
    return total

def content_counter(c):
    return Counter({w: n for w, n in c.items() if w not in STOP and w not in EXCLUDED and len(w) > 1})

def mattr(words, w=MATTR_WINDOW):
    if len(words) < w:
        return np.nan
    c = Counter(words[:w]); vals = [len(c)]
    for i in range(w, len(words)):
        c[words[i]] += 1
        c[words[i - w]] -= 1
        if c[words[i - w]] == 0:
            del c[words[i - w]]
        vals.append(len(c))
    return float(np.mean(vals)) / w

def singer(lead_vocal):
    names = set(re.findall(r"Lennon|McCartney|Harrison|Starr", re.sub(r"\(.*?\)", "", lead_vocal)))
    return names.pop() if len(names) == 1 else ("Shared" if names else "Other")

def load_corpus(originals_only=True):
    """Songs with per-song metrics. originals_only: compositions by the band members only."""
    df = pd.read_parquet(ROOT / "data/beatles/beatles.parquet")
    df = df[df.title != "Revolution 9"]
    if originals_only:
        df = df[df.is_original]
    df = df.copy()
    df["words"] = df.lyrics_clean.map(tokenize)
    df["words_dedup"] = df.lyrics_clean.map(lambda t: tokenize("\n".join(dict.fromkeys(l.strip() for l in t.lower().split("\n")))))
    df = df[df.words.map(len) >= MIN_TOKENS].reset_index(drop=True)
    df["bow"] = df.words.map(Counter)
    df["tokens"] = df.words.map(len)
    df["types"] = df.words.map(lambda w: len(set(w)))
    df["mattr"] = df.words.map(mattr)
    df["mattr_dedup"] = df.words_dedup.map(mattr)
    df["repeat_ratio"] = 1 - df.words_dedup.map(len) / df.tokens
    df["singer"] = df.lead_vocal.map(singer)
    df["phase"] = df.year.map(lambda y: next((p for p, a, b in PHASES if a <= y <= b), None))
    return df

def monroe(counts_a, counts_b, prior, a0=200, min_count=5):
    """z-scored log-odds with an informative Dirichlet prior (Monroe et al. 2008)."""
    na, nb = sum(counts_a.values()), sum(counts_b.values()); rows = []
    for w, p in prior.items():
        aw = a0 * p; ya, yb = counts_a.get(w, 0), counts_b.get(w, 0)
        if ya + yb < min_count:
            continue
        d = math.log((ya + aw) / (na + a0 - ya - aw)) - math.log((yb + aw) / (nb + a0 - yb - aw))
        rows.append((w, ya, yb, d / math.sqrt(1 / (ya + aw) + 1 / (yb + aw))))
    return pd.DataFrame(rows, columns=["word", "in_group", "in_rest", "z"]).sort_values("z", ascending=False)

def prior_from(df):
    c = content_counter(merge(df.bow)); t = sum(c.values())
    return c, {w: n / t for w, n in c.items()}


PUBLIC = ROOT / "data/public/beatles_bow.parquet"
PUBLIC_COLS = ["title", "year", "release_core", "songwriters", "lead_vocal", "is_original", "singer", "phase",
               "tokens", "types", "mattr", "mattr_dedup", "repeat_ratio"]

def export_public():
    """Lyrics-free dataset: per-song metrics and bag-of-words (word counts), safe to deploy."""
    df = load_corpus(originals_only=False)
    out = df[PUBLIC_COLS].copy()
    out["bow_words"] = df.bow.map(lambda c: list(c.keys()))
    out["bow_counts"] = df.bow.map(lambda c: [int(n) for n in c.values()])
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(PUBLIC, compression="zstd", index=False)
    return out

def load_public(originals_only=True):
    """Same shape as load_corpus (minus lyrics), from the deployable bag-of-words file."""
    df = pd.read_parquet(PUBLIC)
    df["bow"] = [Counter(dict(zip(w, c))) for w, c in zip(df.bow_words, df.bow_counts)]
    df = df.drop(columns=["bow_words", "bow_counts"])
    return df[df.is_original].reset_index(drop=True) if originals_only else df
