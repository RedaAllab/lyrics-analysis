import os
from collections import Counter

import pandas as pd

from beatles_viz.config import LYRICS_PATH, PUBLIC_PATH, SEMANTIC_PATH


def has_lyrics():
    # BEATLES_PUBLIC_ONLY=1 reproduces the deployed app (no lyrics) on a machine that has them.
    return LYRICS_PATH.exists() and os.environ.get("BEATLES_PUBLIC_ONLY") != "1"


def data_source():
    return "local" if has_lyrics() else "public"


def load_songs(source="auto", originals_only=True):
    """source: "local" (with lyrics), "public" (word counts only) or "auto" (local when available)."""
    if source == "auto":
        source = data_source()
    if source == "local":
        df = pd.read_parquet(LYRICS_PATH)
        if SEMANTIC_PATH.exists():
            df = df.merge(pd.read_parquet(SEMANTIC_PATH), on="title", how="left")
    else:
        df = pd.read_parquet(PUBLIC_PATH)
        df["bow"] = [Counter(dict(zip(w, c))) for w, c in zip(df.bow_words, df.bow_counts)]
        df = df.drop(columns=["bow_words", "bow_counts"])
    if originals_only:
        df = df[df.is_original]
    return df.reset_index(drop=True)
