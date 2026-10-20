"""One artist's lyrics dataset, the same way as scripts/build_beatles.py: an official song list from Wikipedia
matched against the Genius parquet files. One row per official title; when Genius only has a Live/Remix/Demo/Take
version, that version stands in for it (longest lyrics with >= 20 words). Year = original release year from
the official list. Writes data/<slug>/<slug>.parquet with the columns of data/beatles/beatles.parquet.

The Wikipedia list is saved first (the page as HTML, parsed with the standard library):
  curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_recorded_by_the_Rolling_Stones&action=render" -o stones.html
  curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_written_by_Bob_Dylan&action=render" -o dylan.html
Usage: build_artist.py "<Genius artist>" <wikipedia.html> <genius_dir1> [<genius_dir2> ...]
  e.g. build_artist.py "The Rolling Stones" stones.html raw/genius"""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from artist_helpers import TAGS, clean_title, first_year, lyric_words, match_title, norm, pick_versions, slug, wiki_tables

# Writers that make a song the artist's own (the Beatles parquet's is_original); the Dylan list only has his songs.
MEMBERS = {"The Rolling Stones": re.compile(r"Jagger|Richards|Nanker Phelge|Wyman|Watts|Jones|Taylor|Wood", re.I),
           "Bob Dylan": re.compile(r"Dylan", re.I)}


def column(header, *names):
    return next((i for i, h in enumerate(header) for n in names if n in h.lower()), None)


def official_songs(html, artist):
    """{normalised title: record} from the page's wikitables (title, release year, release, writers, vocals)."""
    official = {}
    for table in wiki_tables(html):
        header = table[0]
        t, y = column(header, "title"), column(header, "year released", "released")
        if t is None or y is None:
            continue
        rel, w, v = column(header, "original release", "album"), column(header, "writer"), column(header, "vocal")
        for row in table[1:]:
            if len(row) <= max(t, y) or first_year(row[y]) is None:
                continue
            title = clean_title(row[t])
            get = lambda i: row[i] if i is not None and i < len(row) else ""
            writers = get(w) or artist
            rec = dict(title=title, year=first_year(row[y]), release_core=get(rel), songwriters=writers,
                       lead_vocal=get(v) or artist, is_original=bool(MEMBERS.get(artist, re.compile(".")).search(writers)))
            for k in (norm(title), norm(title, False)):
                official.setdefault(k, rec)
    return official


def clean(lyrics):
    lines = [TAGS.sub("", l).strip() for l in str(lyrics).splitlines()]
    return "\n".join(l for l in lines if l)


def main(artist, page, dirs):
    official = official_songs(Path(page).read_text(encoding="utf-8"), artist)
    titles = {r["title"]: r for r in official.values()}
    parts = [f"select title, lyrics from read_parquet('{d}/train-*.parquet') where artist = ?" for d in dirs]
    cand = duckdb.execute(" union all ".join(parts), [artist] * len(dirs)).df()
    matched = cand.title.map(lambda t: match_title(t, official)[0]).notna()
    best = pick_versions(cand.to_dict("records"), official)
    rows = []
    for b in best:
        words = lyric_words(b["lyrics"])
        rows.append({"artist": artist, **titles[b["official"]], "genius_title": b["title"], "n_tokens": len(words),
                     "n_types": len(set(words)), "lyrics_raw": b["lyrics"], "lyrics_clean": clean(b["lyrics"])})
    df = pd.DataFrame(rows).sort_values(["year", "title"]).reset_index(drop=True)
    out = ROOT / "data" / slug(artist)
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / f"{slug(artist)}.parquet", index=False)
    print(f"{artist}: {len(cand)} Genius rows, {len(titles)} official titles, {int(matched.sum())} rows "
          f"matched, {len(df)} songs kept ({int(df.is_original.sum())} originals, "
          f"{sum(b["is_version"] for b in best)} from a Live/Demo/Remix version), years {df.year.min()}-{df.year.max()} "
          f"-> {out / (slug(artist) + '.parquet')}", file=sys.stderr)
    return df


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
