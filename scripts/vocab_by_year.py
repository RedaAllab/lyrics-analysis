"""Vocabulary size and richness per genre and decade from data/*.csv."""
import pandas as pd
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
songs = pd.read_csv(D / "songs.csv")
wc = pd.read_csv(D / "word_counts.csv")
songs["decade"] = songs.year // 10 * 10
per_song = wc.groupby("track_id").agg(tokens=("count", "sum"), types=("word", "nunique")).reset_index()
df = songs.merge(per_song, on="track_id")
df["ttr"] = df.types / df.tokens
out = df.groupby(["genre", "decade"]).agg(songs=("track_id", "count"), mean_tokens=("tokens", "mean"),
                                         mean_types=("types", "mean"), mean_ttr=("ttr", "mean")).round(3)
print(out)
out.to_csv(D / "vocab_by_decade.csv")
