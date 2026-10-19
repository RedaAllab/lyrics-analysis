"""Beatles-only lyrics dataset: official song list (Wikipedia export) matched against the Genius
parquet sources. One row per official title (exact normalised title, so Take/Live/Remix versions
are excluded), year = original release year from the official list.
Usage: build_beatles.py <wikipedia_scrape.json> <genius_dir1> [<genius_dir2> ...]"""
import json, re, sys
from pathlib import Path
import duckdb, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
md = json.loads(Path(sys.argv[1]).read_text())["markdown"]
dirs = sys.argv[2:]
TAGS = re.compile(r"\[[^\]]*\]")
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")

def norm(s, keep_parens=True):
    s = str(s).lower() if keep_parens else re.sub(r"\(.*?\)", "", str(s).lower())
    s = re.sub(r"['’‎]", "", s.replace("&", "and"))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def cell(c):
    c = re.sub(r"\[\\\[[^\]]*\\\]\]\(\S+(?: \"[^\"]*\")?\)", "", c)  # footnote refs
    c = re.sub(r"\[([^\]]+)\]\(\S+(?: \"[^\"]*\")?\)", r"\1", c)       # links -> text
    c = c.replace("<br>", "; ").replace("†", "").replace("_", "")
    return re.sub(r"\s+", " ", c).strip(' ";')

official = {}
for line in md.split("\n"):
    cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
    if len(cells) < 6 or not re.fullmatch(r"\d{4}", cells[4]):
        continue
    m = re.search(r"\[([^\]]+)\]\(", cells[0]) or re.search(r'"\s*([^"]+?)\s*"', cells[0])
    title = (m.group(1) if m else cell(cells[0])).strip(' "')
    rec = dict(official_title=title, year=int(cells[4]), release=cell(cells[1]),
               songwriters=cell(cells[2]), lead_vocal=re.sub(r"\[.*", "", cell(cells[3])).strip())
    for k in {norm(title), norm(title, False)}:
        official.setdefault(k, rec)

parts = [f"select title, tag, lyrics from read_parquet('{d}/train-*.parquet') where artist = 'The Beatles'" for d in dirs]
cand = duckdb.sql(" union all ".join(parts)).df()
cand["k"] = cand.title.map(norm)
cand = cand[cand.k.isin(official)]

rows = []
for k, g in cand.groupby("k"):
    w = lambda l: WORD.findall(TAGS.sub(" ", str(l)).lower())
    g = g.assign(n=g.lyrics.map(lambda l: len(w(l)))).query("n >= 20")
    if g.empty:
        continue
    best = g.sort_values("n", ascending=False).iloc[0]
    words = w(best.lyrics)
    rows.append({**official[k], "genius_title": best.title, "lyrics": best.lyrics,
                 "tokens": len(words), "types": len(set(words))})
df = pd.DataFrame(rows).drop_duplicates("official_title").sort_values(["year", "official_title"])
(ROOT / "data/beatles").mkdir(exist_ok=True)
df.to_csv(ROOT / "data/beatles/beatles_lyrics.csv", index=False)
df.drop(columns="lyrics").to_csv(ROOT / "data/beatles/beatles_songs.csv", index=False)
allofficial = {v["official_title"] for v in official.values()}
miss = sorted(allofficial - set(df.official_title))
print(len(allofficial), "official;", len(df), "matched;", len(miss), "missing", file=sys.stderr)
print(miss, file=sys.stderr)
