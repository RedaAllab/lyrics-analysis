import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LYRICS_PATH = ROOT / "data/beatles/beatles.parquet"
PUBLIC_PATH = ROOT / "data/public/beatles_bow.parquet"
YOUTUBE_PATH = ROOT / "data/beatles/youtube.csv"
SECTION_TIMES_PATH = ROOT / "data/beatles/section_times.csv"
SEMANTIC_PATH = ROOT / "data/beatles/semantic.parquet"  # local, from scripts/embed_songs.py

PHASES = [("1962-63", 1962, 1963), ("1964-65", 1964, 1965), ("1966-67", 1966, 1967), ("1968-70", 1968, 1970)]
PHASE_ORDER = [p for p, _, _ in PHASES]
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

# "Session sheet" palette: monochrome interface, colour reserved for data. Mirrored in .streamlit/config.toml.
INK, PAPER, CARD = "#16161a", "#f4f4f1", "#ffffff"
MUTED, RULE, SOFT = "#5c5c66", "#dadad4", "#ecece7"  # MUTED passes 4.5:1 on PAPER
REFERENCE = "#a9a9a2"  # medians, zero lines, "everything else" in a comparison
VOICE_COLORS = {"Lennon": "#2b59c3", "McCartney": "#c8283f", "Harrison": "#a86a00", "Starr": "#00796b",
                "Shared": "#6a4fa3", "Neutral": "#6e6e73"}
SECTION_COLORS = {"intro": "#a9b4be", "verse": "#4f6d8a", "pre_chorus": "#7f98ae", "chorus": "#e4572e",
                  "bridge": "#5e9c76", "instrumental": "#e9c46a", "outro": "#a9b4be", "other": "#cfcfc8",
                  "song": "#4f6d8a"}
ACCENT = SECTION_COLORS["chorus"]
SECONDARY = VOICE_COLORS["Lennon"]  # second series when a chart compares two things that are not voices
APP_URL = "https://redaallab-lyrics-analysis-appbeatles-app-lzrxuu.streamlit.app"
VOICE_ORDER = ["Lennon", "McCartney", "Harrison", "Starr", "Shared", "Neutral"]
