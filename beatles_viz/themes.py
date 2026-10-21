"""Themes annotated by hand with a codebook (data/themes/codebook.csv), several per song, and the tools to check
them: agreement between annotators (Cohen's kappa per theme) and between a person and the model's suggestions.
The annotations are the reference; the model only proposes (see docs/ROADMAP.md, v2)."""
from datetime import date

import numpy as np
import pandas as pd

from beatles_viz.config import ROOT

THEMES_DIR = ROOT / "data/themes"
CODEBOOK_PATH = THEMES_DIR / "codebook.csv"
ANNOTATIONS_PATH = THEMES_DIR / "annotations.csv"
SUGGESTIONS_PATH = THEMES_DIR / "suggestions.csv"
ANNOTATION_COLS = ["title", "annotator", "themes", "main_theme", "implicit", "note", "annotated_on"]
SEP = ";"


def load_codebook(path=CODEBOOK_PATH):
    return pd.read_csv(path)


def load_annotations(path=ANNOTATIONS_PATH):
    if not path.exists():
        return pd.DataFrame(columns=ANNOTATION_COLS)
    d = pd.read_csv(path, dtype={"note": str, "themes": str, "main_theme": str}, keep_default_na=False)
    d["implicit"] = d.implicit.astype(str).str.lower().isin({"true", "1", "yes"})
    return d


def theme_list(cell):
    return [t for t in str(cell or "").split(SEP) if t]


def save_annotation(title, annotator, themes, main_theme="", implicit=False, note="", path=ANNOTATIONS_PATH,
                    codebook=None):
    """Adds or replaces the annotator's row for the song. Themes must come from the codebook."""
    known = set((codebook if codebook is not None else load_codebook()).theme)
    unknown = set(themes) - known
    if unknown:
        raise ValueError(f"themes not in the codebook: {sorted(unknown)}")
    if main_theme and main_theme not in themes:
        raise ValueError("the main theme must be one of the themes")
    d = load_annotations(path)
    d = d[~((d.title == title) & (d.annotator == annotator))]
    row = {"title": title, "annotator": annotator, "themes": SEP.join(themes), "main_theme": main_theme,
           "implicit": bool(implicit), "note": note, "annotated_on": date.today().isoformat()}
    d = pd.concat([d, pd.DataFrame([row])], ignore_index=True).sort_values(["annotator", "title"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    d.to_csv(tmp, index=False)
    tmp.replace(path)
    return d


def theme_matrix(annotations, annotator, themes):
    """Songs annotated by one person x themes, True when the theme was given."""
    d = annotations[annotations.annotator == annotator]
    return pd.DataFrame([{t: t in theme_list(row.themes) for t in themes} for row in d.itertuples()],
                        index=d.title.to_numpy(), columns=list(themes), dtype=bool)


def kappa(a, b):
    """Cohen's kappa of two yes/no codings of the same items; nan when chance agreement is total."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if not len(a):
        return float("nan")
    observed = (a == b).mean()
    expected = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float("nan") if expected == 1 else float((observed - expected) / (1 - expected))


def agreement(m1, m2):
    """Per theme, over the songs both have coded: songs, times each gave it, raw agreement and kappa."""
    songs = m1.index.intersection(m2.index)
    rows = []
    for t in m1.columns:
        a, b = m1.loc[songs, t], m2.loc[songs, t]
        rows.append({"theme": t, "songs": len(songs), "first": int(a.sum()), "second": int(b.sum()),
                     "agreement": float((a == b).mean()) if len(songs) else float("nan"), "kappa": kappa(a, b)})
    return pd.DataFrame(rows)


def suggestion_matrix(suggestions, themes, top=2, min_score=None):
    """The model's themes per song: its top ones (and, if given, only those above min_score)."""
    d = suggestions[suggestions["rank"] <= top]
    if min_score is not None:
        d = d[d.score >= min_score]
    titles = suggestions.title.unique()
    m = pd.DataFrame(False, index=titles, columns=list(themes))
    for row in d.itertuples():
        if row.theme in m:
            m.loc[row.title, row.theme] = True
    return m


def theme_shares(matrix, groups):
    """Share of songs carrying each theme, per group (period, album, voice...); groups: Series indexed by title."""
    g = groups.reindex(matrix.index)
    return matrix.groupby(g.to_numpy()).mean().assign(songs=matrix.groupby(g.to_numpy()).size())
