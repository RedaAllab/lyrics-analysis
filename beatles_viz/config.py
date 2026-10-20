import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LYRICS_PATH = ROOT / "data/beatles/beatles.parquet"
PUBLIC_PATH = ROOT / "data/public/beatles_bow.parquet"
YOUTUBE_PATH = ROOT / "data/beatles/youtube.csv"
SECTION_TIMES_PATH = ROOT / "data/beatles/section_times.csv"

PHASES = [("1962-63", 1962, 1963), ("1964-65", 1964, 1965), ("1966-67", 1966, 1967), ("1968-70", 1968, 1970)]
MIN_TOKENS = 30
# Get Back session jams: real recordings, but improvised talk-singing that would skew catalogue statistics
IMPROVISATIONS = {"Can You Dig It?", "Commonwealth"}
MATTR_WINDOW = 50

MEMBERS = ["Lennon", "McCartney", "Harrison", "Starr"]
# First names only count when followed by the surname or used alone ("George Martin" is the producer).
MEMBER_PATTERNS = {
    "Lennon": re.compile(r"\bLennon\b|\bJohn\b(?!\s+(?!Lennon)[A-Z])"),
    "McCartney": re.compile(r"\bMcCartney\b|\bPaul\b(?!\s+(?!McCartney)[A-Z])"),
    "Harrison": re.compile(r"\bHarrison\b|\bGeorge\b(?!\s+(?!Harrison)[A-Z])"),
    "Starr": re.compile(r"\bStarr\b|\bStarkey\b|\bRingo\b"),
}
SHARED, NEUTRAL = "Shared", "Neutral"

SECTION_KINDS = ["intro", "verse", "pre_chorus", "chorus", "bridge", "instrumental", "outro", "other"]
# Checked in order: the first matching rule wins ("Instrumental Bridge" is instrumental, not bridge).
SECTION_RULES = [
    ("instrumental", re.compile(r"instrumental|solo|break|interlude|segue|transition|jam", re.I)),
    ("pre_chorus", re.compile(r"pre-?chorus", re.I)),
    ("chorus", re.compile(r"chou?ru?s?|refrain|hook", re.I)),
    ("verse", re.compile(r"verse", re.I)),
    ("bridge", re.compile(r"bridge", re.I)),
    ("intro", re.compile(r"intro", re.I)),
    ("outro", re.compile(r"outro|coda", re.I)),
]
REPEAT_MARK = re.compile(r"^\s*(?:x\s*(\d+)|repeat\s*(\d+)\s*x)\s*$", re.I)

VOICE_COLORS = {"Lennon": "#3a6ea5", "McCartney": "#d1495b", "Harrison": "#e09f3e", "Starr": "#2a9d8f",
                "Shared": "#7b6d8d", "Neutral": "#9a9a9a"}
SECTION_COLORS = {"intro": "#c9d6df", "verse": "#6a8398", "pre_chorus": "#8fa9b8", "chorus": "#e07a5f",
                  "bridge": "#81b29a", "instrumental": "#f2cc8f", "outro": "#a7b1b8", "other": "#d8d8d8",
                  "song": "#6a8398"}
ACCENT = "#e07a5f"
VOICE_ORDER = ["Lennon", "McCartney", "Harrison", "Starr", "Shared", "Neutral"]
