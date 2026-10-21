"""How the eight catalogues tell (beatles_viz/text/narrative.py) and their mood read line by line (valence_ctx),
through the app's own pipeline: originals only, songs of at least MIN_TOKENS words. Mean per song with a 95% bootstrap
interval (songs resampled). Named characters are left out: the list of names is the Beatles'.
Writes analysis/artists/narrative.csv (numbers only).
Usage: compare_narrative.py <beatles.parquet> <artist.parquet> [<artist.parquet> ...] (same files as compare_artists.py)"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from beatles_viz.corpus import analysable, build_corpus  # noqa: E402

OUT = ROOT / "analysis/artists"
MEASURES = {"third_person": "he / she / they (share of words)", "past": "past words (share)",
            "future": "future words (share)", "questions": "lines asking a question (share)",
            "orders": "lines opening on an order or plea (share)", "valence": "mood, single words (-1..1)",
            "valence_ctx": "mood, line by line (-1..1)"}
N_BOOT, SEED = 2000, 0


def interval(values, rng):
    v = np.asarray(values.dropna(), dtype=float)
    if not len(v):
        return np.nan, np.nan, np.nan
    means = v[rng.integers(0, len(v), (N_BOOT, len(v)))].mean(axis=1)
    return v.mean(), *np.quantile(means, [0.025, 0.975])


def main(paths):
    rng = np.random.default_rng(SEED)
    rows = []
    for path in paths:
        d = analysable(build_corpus(pd.read_parquet(path)))
        artist = d.artist.iloc[0]
        for m, label in MEASURES.items():
            mean, lo, hi = interval(d[m], rng)
            rows.append({"artist": artist, "measure": m, "label": label, "songs": int(d[m].notna().sum()),
                         "mean": mean, "ci_low": lo, "ci_high": hi})
        print(artist, len(d), "songs", file=sys.stderr)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).round(4).to_csv(OUT / "narrative.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1:])
