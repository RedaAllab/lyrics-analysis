"""Join MSD metadata + tagtraum genres + musiXmatch bags-of-words into
data/songs.csv and data/word_counts.csv, keeping Rock and Rap tracks with a known year."""
import csv, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "raw", ROOT / "data"
GENRES = {"Rock": "rock", "Rap": "hiphop"}

genre_of = {}
with open(RAW / "msd_tagtraum_cd2.cls", encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        tid, *g = line.rstrip("\n").split("\t")
        if g and g[0] in GENRES:  # primary genre only
            genre_of[tid] = GENRES[g[0]]

meta = sqlite3.connect(RAW / "track_metadata.db")
songs = {}
for tid, title, artist, year in meta.execute(
        "SELECT track_id, title, artist_name, year FROM songs WHERE year > 0"):
    if tid in genre_of:
        songs[tid] = (artist, title, year, genre_of[tid])

with open(OUT / "songs.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["track_id", "artist", "title", "year", "genre"])
    for tid, row in songs.items():
        w.writerow([tid, *row])

mxm = sqlite3.connect(RAW / "mxm_dataset.db")
n = 0
with open(OUT / "word_counts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["track_id", "word", "count"])
    for tid, word, cnt in mxm.execute("SELECT track_id, word, count FROM lyrics"):
        if tid in songs:
            w.writerow([tid, word, cnt]); n += 1
print(f"{len(songs)} songs with metadata+genre+year, {n} word rows written", file=sys.stderr)
