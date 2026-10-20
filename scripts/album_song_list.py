"""A song list for an artist that has no 'List of songs recorded by ...' page on Wikipedia: the track listings of
their studio albums, each song dated by its album's release year (first album wins for a re-recorded song).
Writes an HTML wikitable that scripts/build_artist.py reads like a Wikipedia song list.
Usage: album_song_list.py "<artist>" <out.html>   (albums below, in release order)"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from artist_helpers import album_tracks, infobox_year, norm, song_list_html

# Studio albums of original songs (cover albums and re-recordings left out: Both Sides Now, Travelogue,
# In the Blue Light). Page titles are tried as "<album> (<artist> album)", "<album> (album)", "<album>".
STUDIO_ALBUMS = {
    "Leonard Cohen": ["Songs of Leonard Cohen", "Songs from a Room", "Songs of Love and Hate",
                      "New Skin for the Old Ceremony", "Death of a Ladies' Man", "Recent Songs", "Various Positions",
                      "I'm Your Man", "The Future", "Ten New Songs", "Dear Heather", "Old Ideas", "Popular Problems",
                      "You Want It Darker", "Thanks for the Dance"],
    "Joni Mitchell": ["Song to a Seagull", "Clouds", "Ladies of the Canyon", "Blue", "For the Roses", "Court and Spark",
                      "The Hissing of Summer Lawns", "Hejira", "Don Juan's Reckless Daughter", "Mingus",
                      "Wild Things Run Fast", "Dog Eat Dog", "Chalk Mark in a Rain Storm", "Night Ride Home",
                      "Turbulent Indigo", "Taming the Tiger", "Shine"],
    "Paul Simon": ["The Paul Simon Songbook", "Paul Simon", "There Goes Rhymin' Simon",
                   "Still Crazy After All These Years", "One-Trick Pony", "Hearts and Bones", "Graceland",
                   "The Rhythm of the Saints", "Songs from The Capeman", "You're the One", "Surprise",
                   "So Beautiful or So What", "Stranger to Stranger", "Seven Psalms"],
}
API = "https://en.wikipedia.org/w/api.php"


def wikitexts(titles, tries=5):
    """{requested title: wikitext} in one API call (redirects followed); waits and retries when rate-limited."""
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
                                "redirects": 1, "titles": "|".join(titles), "format": "json", "formatversion": 2})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "lyrics-analysis/1.0 (offline study)"})
    for attempt in range(tries):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=30))["query"]
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == tries - 1:
                raise
            time.sleep(10 * (attempt + 1))
    time.sleep(1)  # be polite to the API
    alias = {r["from"]: r["to"] for key in ("normalized", "redirects") for r in data.get(key, [])}
    pages = {p["title"]: p["revisions"][0]["slots"]["main"]["content"] for p in data["pages"] if not p.get("missing")}
    resolve = lambda t: alias.get(alias.get(t, t), alias.get(t, t))
    return {t: pages.get(resolve(t), "") for t in titles}


def album_page(album, artist):
    candidates = [f"{album} ({artist} album)", f"{album} (album)", album]
    texts = wikitexts(candidates)
    for title in candidates:
        text = texts[title]
        if "nfobox album" in text and artist.split()[-1] in text[:3000] and album_tracks(text):
            return title, text
    return None, ""


def main(artist, out):
    rows, seen = [], set()
    for album in STUDIO_ALBUMS[artist]:
        title, text = album_page(album, artist)
        if not title:
            print(f"  no track listing found for {album}", file=sys.stderr)
            continue
        year, tracks = infobox_year(text), album_tracks(text)
        print(f"  {album} ({year}): {len(tracks)} tracks", file=sys.stderr)
        for song, writers in tracks:
            if norm(song) not in seen:
                seen.add(norm(song))
                rows.append({"title": song, "year": year, "release": album, "writers": writers or artist})
    Path(out).write_text(song_list_html(rows), encoding="utf-8")
    print(f"{artist}: {len(rows)} songs from {len(STUDIO_ALBUMS[artist])} albums -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
