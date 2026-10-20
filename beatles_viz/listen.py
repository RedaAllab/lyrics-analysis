"""Links to listen on the streaming platforms. Search links rather than track ids: they need no API account and
always land on the official Beatles releases first; no audio is hosted here. YouTube uploads of the official channel
(scripts/youtube_ids.py) can be played in the page."""
import csv
from functools import lru_cache
from urllib.parse import quote, quote_plus

from beatles_viz.config import SECTION_TIMES_PATH, YOUTUBE_PATH

PLATFORMS = {
    "Spotify": lambda q: f"https://open.spotify.com/search/{quote(q)}",
    "Apple Music": lambda q: f"https://music.apple.com/us/search?term={quote_plus(q)}",
    "YouTube Music": lambda q: f"https://music.youtube.com/search?q={quote_plus(q)}",
    "Deezer": lambda q: f"https://www.deezer.com/search/{quote(q)}",
}


def listen_links(title, artist="The Beatles"):
    q = f"{artist} {title}"
    return {name: url(q) for name, url in PLATFORMS.items()}


@lru_cache(maxsize=1)
def _youtube_ids():
    if not YOUTUBE_PATH.exists():
        return {}
    with open(YOUTUBE_PATH, newline="") as f:
        return {r["title"]: r["video_id"] for r in csv.DictReader(f)}


def video_id(title):
    return _youtube_ids().get(title)


def youtube_embed(title):
    """Embed URL of the song's official upload, or None. youtube-nocookie: no tracking cookie until play."""
    vid = video_id(title)
    return f"https://www.youtube-nocookie.com/embed/{vid}" if vid else None


def section_spans(song):
    """Each section as a share of the song, 0 to 1: [(name, kind, start, end)]. Words are sung at a fairly steady
    pace, so the share of words is a first estimate of the share of time; wordless sections get a few words' worth."""
    from beatles_viz.viz.song_charts import structure_frame
    f = structure_frame(song)
    total = f.width.sum()
    return [(r.name, r.kind, r.start / total, (r.start + r.width) / total) for r in f.itertuples()]


def parse_time(text):
    """'3:08' or '188' -> seconds."""
    minutes, _, seconds = text.strip().partition(":")
    return int(minutes) * 60 + float(seconds) if seconds else float(minutes)


@lru_cache(maxsize=1)
def _section_times():
    if not SECTION_TIMES_PATH.exists():
        return {}
    out = {}
    with open(SECTION_TIMES_PATH, newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["title"], {})[int(r["section"]) - 1] = parse_time(r["start"])
    return out


def section_times(title):
    """Start times measured by ear, {section index from 0: seconds}; the other sections are estimated."""
    return _section_times().get(title, {})
