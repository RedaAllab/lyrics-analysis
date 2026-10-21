"""Who sings and plays what, from the Personnel sections of the English Wikipedia articles, with the reference works
each article cites for it (Lewisohn, MacDonald, Everett...). Two levels, kept apart:

  album  the album's article: roles for the whole album, some limited to named songs ('sitar on "Norwegian Wood"');
         only the latter can be compared song by song
  song   the song's own article, when it has one: the personnel of that recording

The song list (List of songs recorded by the Beatles) gives each song's article and its album's article. Writes
data/credits/wp_pages.csv (each page read, its revision and whether it has a Personnel section) and
data/credits/wp_credit.csv (one row per person, role and song, with the works cited). Facts only, no prose.
Wikipedia text is CC BY-SA; the revision ids let anyone read the exact text used. Responses are cached in
data/credits/wp_cache/ (git-ignored). Run: python scripts/fetch_wikipedia_credits.py"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.config import ROOT  # noqa: E402
from beatles_viz.corpus import load_corpus  # noqa: E402
from beatles_viz.wiki import personnel, personnel_section, plain  # noqa: E402

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "beatles-lyrics-analysis/0.2 (personal research script, non-commercial)"
SONG_LIST = "List of songs recorded by the Beatles"
OUT = ROOT / "data/credits"
CACHE = OUT / "wp_cache"
LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def page(title):
    """(resolved title, revision id, wikitext) of an article, following redirects; None when it does not exist."""
    key = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", title)[:150] + ".json")
    if not key.exists():
        params = {"action": "parse", "page": title, "prop": "wikitext|revid", "redirects": 1, "format": "json",
                  "formatversion": 2}
        req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": USER_AGENT})
        for attempt in range(6):
            time.sleep(2 * 2 ** attempt)
            try:
                key.write_text(json.dumps(json.load(urllib.request.urlopen(req, timeout=30))))
                break
            except urllib.error.HTTPError as e:
                if e.code not in (429, 503):
                    raise
        else:
            raise RuntimeError(f"Wikipedia kept refusing {title}")
    data = json.loads(key.read_text())
    if "parse" not in data:
        return None
    return data["parse"]["title"], data["parse"]["revid"], data["parse"]["wikitext"]


def norm(title):
    t = str(title).lower().replace("’", "'").replace("&", "and")
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"['‘’]", "", t)).strip()


def song_list(wikitext):
    """Rows of the song list: displayed title, the song's article (None when not linked) and the album's article."""
    rows = []
    for block in wikitext.split("\n|-")[1:]:
        lines = [l for l in block.strip().split("\n") if l.strip()]
        if not lines or not lines[0].startswith("!"):
            continue
        head = lines[0].split("|", 1)[-1] if "scope" in lines[0] else lines[0].lstrip("!")
        shown = re.search(r'"(.+?)"', plain(head))
        link = LINK.search(head)
        album = next((LINK.search(l) for l in lines[1:2] if LINK.search(l)), None)
        if shown:
            rows.append({"list_title": shown.group(1).strip(), "song_page": link.group(1).strip() if link else None,
                         "album_page": album.group(1).strip() if album else None})
    return pd.DataFrame(rows)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    corpus = load_corpus("auto")
    listing = song_list(page(SONG_LIST)[2])
    listing["key"] = listing.list_title.map(norm)
    corpus = corpus.assign(key=corpus.title.map(norm)).merge(
        listing.drop_duplicates("key"), on="key", how="left")
    accessed = date.today().isoformat()
    pages, credits = [], []

    # 1. album articles: roles limited to named songs become song rows, the rest stay album-wide
    for album_page, songs in corpus.dropna(subset=["album_page"]).groupby("album_page"):
        got = page(album_page)
        section = personnel_section(got[2]) if got else ""
        own = dict(zip(songs.key, songs.title))
        pages.append({"page": got[0] if got else album_page, "level": "album", "revid": got[1] if got else "",
                      "titles": "; ".join(songs.title), "has_personnel": bool(section.strip()), "accessed": accessed})
        for r in personnel(section) if section else []:
            for song in r["songs"] or [""]:
                title = own.get(norm(song), "") if song else ""
                if song and not title:
                    continue  # outside the corpus, or the corpus takes that song from another release
                credits.append({"title": title, "album": songs.album.iloc[0], "level": "album",
                                "page": got[0], "revid": got[1], **{k: r[k] for k in r if k != "songs"},
                                "accessed": accessed})
        print(f"album {album_page}: {'personnel' if section else 'no personnel section'}", file=sys.stderr)

    # 2. the songs' own articles (a link to the album's article is not one)
    for row in corpus.dropna(subset=["song_page"]).itertuples():
        if row.song_page == row.album_page:
            continue
        got = page(row.song_page)
        if got is None:
            continue
        section = personnel_section(got[2])
        pages.append({"page": got[0], "level": "song", "revid": got[1], "titles": row.title,
                      "has_personnel": bool(section.strip()), "accessed": accessed})
        for r in personnel(section) if section else []:
            credits.append({"title": row.title, "album": row.album, "level": "song", "page": got[0],
                            "revid": got[1], **{k: r[k] for k in r if k != "songs"}, "accessed": accessed})

    pages = pd.DataFrame(pages)
    credits = pd.DataFrame(credits).drop_duplicates()
    pages.to_csv(OUT / "wp_pages.csv", index=False)
    credits.to_csv(OUT / "wp_credit.csv", index=False)
    unlinked = corpus[corpus.song_page.isna() & corpus.album_page.isna()].title.tolist()
    print(f"{len(pages)} pages ({pages.has_personnel.sum()} with personnel), {len(credits)} credit rows; "
          f"not found in the song list: {unlinked}", file=sys.stderr)


if __name__ == "__main__":
    main()
