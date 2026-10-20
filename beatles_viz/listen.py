"""Links to listen on the streaming platforms. Search links rather than track ids: they need no API account and
always land on the official Beatles releases first; no audio is hosted here. YouTube uploads of the official channel
(scripts/youtube_ids.py) can be played in the page."""
import csv
from functools import lru_cache
from urllib.parse import quote, quote_plus

from beatles_viz.config import YOUTUBE_PATH

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


def youtube_embed(title):
    """Embed URL of the song's official upload, or None. youtube-nocookie: no tracking cookie until play."""
    vid = _youtube_ids().get(title)
    return f"https://www.youtube-nocookie.com/embed/{vid}" if vid else None
