"""What makes a song stand out, in words a fan can share: its most unusual measures against the catalogue."""
import math
from urllib.parse import quote

from beatles_viz.config import APP_URL

# column: (sentence when high, sentence when low, value shown)
MEASURES = {
    "repetition_score": ("More repetitive than", "Less repetitive than", lambda v: f"repetition score {v:.3f}"),
    "mattr": ("Richer vocabulary than", "Simpler vocabulary than", lambda v: f"lexical richness {v:.2f}"),
    "tokens": ("Longer than", "Shorter than", lambda v: f"{v:.0f} words"),
    "valence": ("Brighter words than", "Darker words than", lambda v: f"mood {v:+.2f} on a -1 to +1 scale"),
}


def standout_facts(song, reference, k=3):
    """The k measures where the song is furthest from the middle of the reference songs (itself left out):
    [(headline, detail)], most unusual first."""
    others = reference[reference.title != song.title]
    facts = []
    for col, (high, low, detail) in MEASURES.items():
        value = song.get(col)
        values = others[col].dropna() if col in others else None
        if value is None or value != value or values is None or values.empty:
            continue
        share = (values < value).mean()
        word, pct = (high, share) if share >= 0.5 else (low, (values > value).mean())
        who = "every other Beatles original" if pct == 1 else f"{math.floor(100 * pct)}% of Beatles originals"
        facts.append((abs(share - 0.5), f"{word} {who}", detail(value)))
    return [(h, d) for _, h, d in sorted(facts, reverse=True)[:k]]


def song_link(title):
    return f"{APP_URL}/song?song={quote(title)}"


def voice_line(voice):
    return {"Shared": "Shared lead vocals", "Neutral": "No lead vocal credited"}.get(voice, f"Lead voice {voice}")
