"""Shared corpus loading and text metrics for the Beatles analysis and the Streamlit app."""
import math, re, sys
from collections import Counter
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.config import MATTR_WINDOW, MIN_TOKENS, PHASES, ROOT  # noqa: E402,F401
from beatles_viz.text.keyness import monroe  # noqa: E402,F401
from beatles_viz.text.metrics import mattr  # noqa: E402,F401
from beatles_viz.text.tokenize import (EXCLUDED, NAMES, STOP, VOCABLES, content, content_counter,  # noqa: E402,F401
                                       merge, tokenize)

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
