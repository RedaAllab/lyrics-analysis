"""Finds the official YouTube upload of each song (channel "The Beatles") and writes data/beatles/youtube.csv.
Studio audio first ("Remastered", plain title), then music videos, then anything else on the channel; a song with no
official upload gets no row and keeps its search links. Usage: python scripts/youtube_ids.py"""
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from beatles_viz.config import YOUTUBE_PATH  # noqa: E402
from beatles_viz.data.loader import load_songs  # noqa: E402

CHANNEL = "The Beatles"
LESSER = re.compile(r"demo|take \d|live|outtake|rehearsal|anthology|session|instrumental|karaoke", re.I)


def search(query):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
    for wait in (2, 10, 30, None):  # YouTube sometimes answers with a page without results: wait and retry
        page = urllib.request.urlopen(req, timeout=20).read().decode()
        found = re.search(r"var ytInitialData = (\{.*?\});</script>", page)
        if found or wait is None:
            break
        time.sleep(wait)
    if not found:
        return []
    data = json.loads(found.group(1))
    found = []

    def walk(o):
        if isinstance(o, dict):
            if "videoRenderer" in o:
                v = o["videoRenderer"]
                owner = v.get("ownerText", {}).get("runs", [{}])[0].get("text")
                found.append((v["videoId"], v["title"]["runs"][0]["text"], owner))
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(data)
    return found


def simple(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def matches(title, name):
    """The upload's name, before any bracket or dash, is the title ("Shout" is neither "Twist And Shout" nor
    "Shout It Out"); medleys may name it anywhere."""
    name = re.sub(r"^(the beatles\s*-\s*)+", "", name, flags=re.I)
    return simple(core(name)) == simple(core(title)) or ("medley" in name.lower() and simple(title) in simple(name))


def core(text):
    """The part before any bracket or dash: "Anna (Go To Him)" and "Anna - Remastered" are both "Anna"."""
    return re.split(r"\s[-/–]\s|\(|\[", text)[0]


def best(title, results):
    official = [(vid, name) for vid, name, owner in results if owner == CHANNEL and matches(title, name)]

    def rank(item):
        name = item[1]
        return (bool(LESSER.search(name)) and not LESSER.search(title), "video" in name.lower())
    return min(official, key=rank) if official else None


def main():
    titles = load_songs("public", originals_only=False).title.tolist()
    rows = []
    for t in titles:
        pick = best(t, search(f"The Beatles {t}"))
        if pick:
            rows.append({"title": t, "video_id": pick[0], "video_title": pick[1]})
        print(f"{t}: {pick[1] if pick else '-'}", flush=True)
        time.sleep(0.5)
    with open(YOUTUBE_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["title", "video_id", "video_title"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} of {len(titles)} songs matched")


if __name__ == "__main__":
    main()
