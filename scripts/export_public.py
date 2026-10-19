"""Write data/public/beatles_bow.parquet (per-song metrics + word counts, no lyrics) used by the deployed app.
Needs data/beatles/beatles.parquet (local only)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from beatles_lib import export_public

print(export_public().shape)
