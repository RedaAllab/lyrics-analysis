import re
from collections import Counter

import numpy as np
import pandas as pd

from beatles_viz.attribution import lead_voice
from beatles_viz.config import IMPROVISATIONS, MIN_TOKENS, PHASES
from beatles_viz.data.loader import load_songs
from beatles_viz.text.metrics import pronoun_shares, text_metrics
from beatles_viz.text.mood import mood, themes
from beatles_viz.text.repetition import fingerprint, repetition_score
from beatles_viz.text.sections import all_lines, section_name
from beatles_viz.text.segment import AUTO, song_sections
from beatles_viz.text.tokenize import tokenize

EXCLUDED_TITLES = {"Revolution 9"}  # a sound collage: its few words are not lyrics
THEME_PREFIX = "theme: "
STRUCTURE_COLS = ["sec_names", "sec_kinds", "sec_words", "sec_repeats", "sec_auto"]


def phase_of(year):
    return next((p for p, a, b in PHASES if a <= year <= b), None)


def album_of(release):
    """'Past Masters; (B-side of " Help!")' -> 'Past Masters': the first release named, without notes."""
    first = str(release or "").split(";")[0]
    return re.sub(r"\s*\(.*?\)\s*", " ", first).strip() or "Unknown"


def structure_of(sections):
    """Section names, kinds, word counts and repeats: the shape of the song without its words."""
    return {"sec_names": [section_name(s) for s in sections], "sec_kinds": [s.kind for s in sections],
            "sec_words": [len(tokenize(" ".join(s.lines))) for s in sections],
            "sec_repeats": [s.repeat for s in sections], "sec_auto": [s.label == AUTO for s in sections]}


def build_corpus(df):
    """Adds sections, tokens and metrics. Rows without lyrics (public file) keep only word counts."""
    df = df.copy()
    if "lyrics_raw" in df:
        df["sections"] = df.lyrics_raw.map(song_sections)
        df["words"] = df.sections.map(lambda s: tokenize("\n".join(all_lines(s))))
        df["bow"] = df.words.map(Counter)
        metrics = pd.DataFrame(df.sections.map(lambda s: text_metrics(all_lines(s))).tolist(), index=df.index)
        df = df.drop(columns=[c for c in metrics if c in df]).join(metrics)
        df["repetition_score"] = df.words.map(repetition_score)
        df["fingerprint"] = df.words.map(fingerprint)
        structure = pd.DataFrame(df.sections.map(structure_of).tolist(), index=df.index)
        df = df.drop(columns=[c for c in structure if c in df]).join(structure)
    else:
        df = df.join(pd.DataFrame(df.bow.map(pronoun_shares).tolist(), index=df.index))
        if "fingerprint" in df:  # stored flat in the public file
            df["fingerprint"] = df.fingerprint.map(lambda f: np.asarray(f, dtype=np.uint8).reshape(
                int(np.sqrt(len(f))), -1) if f is not None and len(f) else np.zeros((1, 1), dtype=np.uint8))
        for col in STRUCTURE_COLS:
            if col in df:
                df[col] = df[col].map(list)
    df = df.join(pd.DataFrame(df.bow.map(mood).tolist(), index=df.index))
    df = df.join(pd.DataFrame(df.bow.map(themes).tolist(), index=df.index).add_prefix(THEME_PREFIX))
    df["voice"] = df.lead_vocal.map(lead_voice)
    df["phase"] = df.year.map(phase_of)
    df["album"] = df.release_core.map(album_of)
    return df.sort_values(["year", "title"]).reset_index(drop=True)


def load_corpus(source="auto", originals_only=False):
    return build_corpus(load_songs(source, originals_only))


def analysable(corpus, originals_only=True, improvisations=False):
    """Songs long enough for vocabulary statistics: the same set whether the lyrics are local or not.
    Studio improvisations stay in the public file (improvisations=True) but out of the statistics."""
    d = corpus[~corpus.title.isin(EXCLUDED_TITLES) & (corpus.tokens >= MIN_TOKENS)]
    if not improvisations:
        d = d[~d.title.isin(IMPROVISATIONS)]
    return d[d.is_original] if originals_only else d


def albums(corpus, min_tracks=3):
    """One row per release with at least min_tracks songs, in release order."""
    g = corpus.groupby("album").agg(year=("year", "min"), tracks=("title", "count"), originals=("is_original", "sum"),
                                    words=("tokens", "sum"), mattr=("mattr", "mean"),
                                    repetition=("repetition_score", "mean"),
                                    voice=("voice", lambda v: v.value_counts().index[0]))
    return g[g.tracks >= min_tracks].sort_values(["year", "album"]).reset_index()


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


def featured_songs(corpus, min_tokens=60):
    """A few songs worth opening, each with the reason it stands out: [(label, title, reason)]."""
    d = analysable(corpus)
    d = d[d.tokens >= min_tokens].dropna(subset=["mattr"])
    if d.empty:
        return []
    med_t, med_m = d.tokens.median(), d.mattr.median()
    typical = ((d.tokens - med_t).abs() / med_t + (d.mattr - med_m).abs() / med_m).idxmin()
    picks = [
        ("Richest vocabulary", d.mattr.idxmax(), lambda r: f"richness {r.mattr:.2f}"),
        ("Most repetitive", d.repeat_ratio.idxmax(), lambda r: f"{r.repeat_ratio:.0%} repeated lines"),
        ("Longest", d.tokens.idxmax(), lambda r: f"{int(r.tokens)} words"),
        ("Shortest", d.tokens.idxmin(), lambda r: f"{int(r.tokens)} words"),
        ("Most typical", typical, lambda r: f"{int(r.tokens)} words, richness {r.mattr:.2f}"),
        ("Earliest", d.year.idxmin(), lambda r: f"released {int(r.year)}"),
    ]
    out, seen = [], set()
    for label, idx, reason in picks:
        row = d.loc[idx]
        if row.title not in seen:
            seen.add(row.title)
            out.append((label, row.title, reason(row)))
    return out
