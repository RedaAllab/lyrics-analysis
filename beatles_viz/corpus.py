from collections import Counter

import pandas as pd

from beatles_viz.attribution import lead_voice
from beatles_viz.config import PHASES
from beatles_viz.data.loader import load_songs
from beatles_viz.text.metrics import pronoun_shares, text_metrics
from beatles_viz.text.sections import all_lines, split_sections
from beatles_viz.text.tokenize import tokenize


def phase_of(year):
    return next((p for p, a, b in PHASES if a <= year <= b), None)


def build_corpus(df):
    """Adds sections, tokens and metrics. Rows without lyrics (public file) keep only word counts."""
    df = df.copy()
    if "lyrics_raw" in df:
        df["sections"] = df.lyrics_raw.map(split_sections)
        df["words"] = df.sections.map(lambda s: tokenize("\n".join(all_lines(s))))
        df["bow"] = df.words.map(Counter)
        metrics = pd.DataFrame(df.sections.map(lambda s: text_metrics(all_lines(s))).tolist(), index=df.index)
        df = df.drop(columns=[c for c in metrics if c in df]).join(metrics)
    else:
        df = df.join(pd.DataFrame(df.bow.map(pronoun_shares).tolist(), index=df.index))
    df["voice"] = df.lead_vocal.map(lead_voice)
    df["phase"] = df.year.map(phase_of)
    return df.sort_values(["year", "title"]).reset_index(drop=True)


def load_corpus(source="auto", originals_only=False):
    return build_corpus(load_songs(source, originals_only))


def neighbors(corpus, title, order="chronological"):
    """(previous, next) titles. 'album' stays within the song's release; the data has no track numbers,
    so songs of a release follow year then title."""
    d = corpus
    if order == "album":
        release = d.loc[d.title == title, "release_core"].iloc[0]
        d = d[d.release_core == release]
    titles = d.sort_values(["year", "title"]).title.tolist()
    i = titles.index(title)
    return (titles[i - 1] if i > 0 else None, titles[i + 1] if i < len(titles) - 1 else None)


def doc_frequencies(corpus):
    return Counter(w for bow in corpus.bow for w in bow)
