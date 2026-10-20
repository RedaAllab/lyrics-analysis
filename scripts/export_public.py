"""Write data/public/beatles_bow.parquet (per-song metrics, word counts, repetition score, a downsampled
repetition fingerprint and section shapes, no lyrics) used by the deployed app.
Needs data/beatles/beatles.parquet (local only). Run: python scripts/export_public.py"""
from beatles_viz.config import PUBLIC_PATH
from beatles_viz.corpus import load_corpus
from beatles_viz.data.export import export_public

out = export_public(load_corpus("local"))
print(out.shape, f"{PUBLIC_PATH.stat().st_size / 1024:.0f} KB")
