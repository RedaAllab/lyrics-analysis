"""Write data/public/beatles_bow.parquet (per-song metrics, word counts, repetition score and a downsampled
repetition fingerprint, no lyrics) used by the deployed app. Needs data/beatles/beatles.parquet (local only)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_lib import PUBLIC, export_public  # noqa: E402
from beatles_viz.corpus import load_corpus  # noqa: E402

out = export_public()
local = load_corpus("local").set_index("title")
out["repetition_score"] = out.title.map(local.repetition_score)
out["fingerprint"] = out.title.map(lambda t: local.fingerprint[t].ravel().tolist())
out.to_parquet(PUBLIC, compression="zstd", index=False)
print(out.shape, f"{PUBLIC.stat().st_size / 1024:.0f} KB")
