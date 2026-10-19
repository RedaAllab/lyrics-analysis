"""Rebuild the Beatles rows from the official song list (Wikipedia export).
Genius tags many Beatles songs as 'pop', so candidates are taken from all genres, matched on
normalised title (exact), the year is replaced by the original release year, genre is set to rock.
Writes data/beatles_official.csv and data/genius_songs_clean.csv (all rock/hiphop rows with the
Beatles replaced by the cleaned set)."""
import glob, json, re, sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
md = json.loads(Path(sys.argv[1]).read_text())["markdown"]
TAGS = re.compile(r"\[[^\]]*\]")
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
def norm(s, keep_parens=False):
    s = str(s).lower() if keep_parens else re.sub(r"\(.*?\)", "", str(s).lower())
    s = s.replace("&", "and")
    s = re.sub(r"['’‎]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

official = {}
for line in md.split("\n"):
    cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
    if len(cells) < 6 or not re.fullmatch(r"\d{4}", cells[4]):
        continue
    m = re.search(r"\[([^\]]+)\]\(", cells[0]) or re.search(r'"\s*([^"]+?)\s*"', cells[0])
    title = (m.group(1) if m else cells[0]).strip(' "')
    official.setdefault(norm(title), (title, int(cells[4])))
    official.setdefault(norm(title, True), (title, int(cells[4])))  # title with its parenthetical kept
pd.DataFrame(sorted(set(official.values())), columns=["title", "year"]).to_csv(ROOT / "data/beatles_official.csv", index=False)

rows = []
for f in sorted(glob.glob(str(ROOT / "raw/genius/*.parquet"))):
    d = pd.read_parquet(f, columns=["title", "artist", "year", "lyrics"])
    d = d[d.artist == "The Beatles"]
    for t, lyr in zip(d.title, d.lyrics):
        k = norm(t)
        if k not in official:
            continue
        w = WORD.findall(TAGS.sub(" ", str(lyr)).lower())
        if len(w) >= 20:
            rows.append((k, len(w), len(set(w)), len(set(w[:100])) if len(w) >= 100 else None))
c = pd.DataFrame(rows, columns=["k", "tokens", "types", "types_first100"])
c = c.sort_values("tokens", ascending=False).drop_duplicates("k")
c["title"] = c.k.map(lambda k: official[k][0]); c["year"] = c.k.map(lambda k: official[k][1])
c = c.drop_duplicates("title")
c["artist"], c["genre"] = "The Beatles", "rock"
c = c[["artist", "title", "year", "genre", "tokens", "types", "types_first100"]]
missing = sorted({v[0] for v in official.values()} - set(c.title))
print(len({v[0] for v in official.values()}), "official;", len(c), "matched;", len(missing), "missing", file=sys.stderr)
print(missing, file=sys.stderr)

s = pd.read_csv(ROOT / "data/genius_songs.csv")
pd.concat([s[s.artist != "The Beatles"], c]).to_csv(ROOT / "data/genius_songs_clean.csv", index=False)
c.to_csv(ROOT / "data/beatles_clean.csv", index=False)
