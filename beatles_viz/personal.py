"""Your own journal of the songs: favourites, a rating, notes and the days you listened.
One JSON file on this machine (data/personal/, git-ignored), never part of the deployed app."""
import json
import os
from datetime import date
from pathlib import Path

import pandas as pd

from beatles_viz.config import ROOT
from beatles_viz.data.loader import has_lyrics

PATH = ROOT / "data/personal/journal.json"
ENV_PATH = "BEATLES_JOURNAL"  # another file, e.g. for tests
EMPTY = {"favourite": False, "rating": None, "note": "", "listens": []}


def enabled():
    # Same switch as the lyrics: on Streamlit Cloud every visitor would share one throwaway file.
    return has_lyrics()


def journal_path():
    return Path(os.environ[ENV_PATH]) if os.environ.get(ENV_PATH) else PATH


def load(path=None):
    path = path or journal_path()
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save(journal, path=None):
    path = path or journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(journal, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)  # never leave a half-written journal


def entry(journal, title):
    return {**EMPTY, **journal.get(title, {})}


def update(title, path=None, **changes):
    journal = load(path)
    journal[title] = {**entry(journal, title), **changes}
    save(journal, path)
    return journal[title]


def log_listen(title, day=None, path=None):
    listens = entry(load(path), title)["listens"]
    return update(title, path, listens=listens + [(day or date.today()).isoformat()])


def undo_listen(title, path=None):
    listens = entry(load(path), title)["listens"]
    return update(title, path, listens=listens[:-1])


def journal_frame(journal, corpus=None):
    """One row per song you touched, with listen counts; joined to year and voice when a corpus is given."""
    rows = []
    for title, e in journal.items():
        e = {**EMPTY, **e}
        listens = sorted(e["listens"])
        rows.append(dict(title=title, favourite=e["favourite"], rating=e["rating"], note=e["note"],
                         listens=len(listens), last_listen=listens[-1] if listens else None))
    df = pd.DataFrame(rows, columns=["title", "favourite", "rating", "note", "listens", "last_listen"])
    if corpus is not None and not df.empty:
        df = df.merge(corpus[["title", "year", "voice"]], on="title", how="left")
    return df


def listens_by_month(journal):
    days = [d for e in journal.values() for d in e.get("listens", [])]
    if not days:
        return pd.DataFrame(columns=["month", "listens"])
    s = pd.Series(pd.to_datetime(days)).dt.to_period("M").astype(str)
    return s.value_counts().sort_index().rename_axis("month").reset_index(name="listens")
