# Lyrics analysis

Vocabulary analysis of Beatles lyrics (originals first), built from public datasets.

## Layout
- `scripts/build_beatles.py` builds `data/beatles/beatles.parquet` from the official song list (Wikipedia) and Genius lyric datasets.
- `scripts/beatles_lib.py` shared corpus loading and metrics.
- `scripts/analyse_beatles.py` tables and figures in `analysis/beatles/`.
- `app/beatles_app.py` Streamlit explorer: `streamlit run app/beatles_app.py`.
- `scripts/build_dataset.py`, `build_genius.py`, `vocab_by_year.py`: earlier rock / hip-hop experiments (Million Song Dataset, Genius).

## Data
Lyrics are copyrighted and are **not** in this repository (`raw/` and `data/` are git-ignored, except song metadata
without lyrics). To rebuild: download the Genius lyrics datasets from Hugging Face
(`theelderemo/genius-lyrics-cleaned`, `Dr3dre/Genius-song-lyrics-cleaned`) and run `scripts/build_beatles.py`
(arguments: Wikipedia list export, then dataset folders). For personal research use only.
