"""Build rock/rap dataset from the Genius parquet shards: dedup, clean, per-song vocabulary stats,
and word counts per genre and year. Outputs go to data/."""
import glob, re, csv, sys
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted(glob.glob(str(ROOT / "raw/genius/*.parquet")))
OUT = ROOT / "data"
GENRES = {"rock": "rock", "rap": "hiphop"}
TAGS = re.compile(r"\[[^\]]*\]")
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

# Pass 1: earliest plausible year per (artist, title)
min_year = {}
for f in FILES:
    d = pd.read_parquet(f, columns=["title", "artist", "tag", "year"])
    d = d[d.tag.isin(GENRES) & d.year.between(1940, 2024)]
    for t, a, y in zip(d.title, d.artist, d.year):
        k = (norm(a), norm(t))
        if y < min_year.get(k, 9999):
            min_year[k] = y
print(len(min_year), "unique rock/rap songs", file=sys.stderr)

# Pass 2: stats and word counts
seen, wc = set(), defaultdict(Counter)
with open(OUT / "genius_songs.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["artist", "title", "year", "genre", "tokens", "types", "types_first100"])
    for f in FILES:
        d = pd.read_parquet(f, columns=["title", "artist", "tag", "year", "lyrics"])
        d = d[d.tag.isin(GENRES) & d.year.between(1940, 2024)]
        for t, a, g, lyr in zip(d.title, d.artist, d.tag, d.lyrics):
            k = (norm(a), norm(t))
            if k in seen:
                continue
            seen.add(k)
            words = WORD.findall(TAGS.sub(" ", str(lyr)).lower())
            if len(words) < 20:
                continue
            y, gg = min_year[k], GENRES[g]
            w.writerow([a, t, y, gg, len(words), len(set(words)),
                        len(set(words[:100])) if len(words) >= 100 else ""])
            wc[(gg, y)].update(words)
        print(f, len(seen), file=sys.stderr)

with open(OUT / "genius_word_counts.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["genre", "year", "word", "count"])
    for (g, y), c in sorted(wc.items()):
        for word, n in c.items():
            if n >= 3:
                w.writerow([g, y, word, n])
