"""Links to listen on the streaming platforms. Search links rather than track ids: they need no API account and
always land on the official Beatles releases first; no audio is hosted here."""
from urllib.parse import quote, quote_plus

PLATFORMS = {
    "Spotify": lambda q: f"https://open.spotify.com/search/{quote(q)}",
    "Apple Music": lambda q: f"https://music.apple.com/us/search?term={quote_plus(q)}",
    "YouTube Music": lambda q: f"https://music.youtube.com/search?q={quote_plus(q)}",
    "Deezer": lambda q: f"https://www.deezer.com/search/{quote(q)}",
}


def listen_links(title, artist="The Beatles"):
    q = f"{artist} {title}"
    return {name: url(q) for name, url in PLATFORMS.items()}
