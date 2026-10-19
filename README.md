# Lyrics analysis

Vocabulary analysis of Beatles lyrics (originals first), built from public datasets.

## Streamlit app
[![Deploy on Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=RedaAllab/lyrics-analysis&branch=main&mainModule=app/beatles_app.py)

Interactive explorer (vocabulary, evolution over time, lead singers). Deploy it from the badge above
(Streamlit Community Cloud, main file `app/beatles_app.py`). Run locally: `streamlit run app/beatles_app.py`.
The app reads `data/public/beatles_bow.parquet`: per-song metrics and word counts only, no lyrics text.

## Layout
- `scripts/build_beatles.py` builds `data/beatles/beatles.parquet` from the official song list (Wikipedia) and Genius lyric datasets.
- `scripts/beatles_lib.py` shared corpus loading and metrics.
- `scripts/analyse_beatles.py` tables and figures in `analysis/beatles/`.
- `app/beatles_app.py` Streamlit explorer (corpus view), `app/pages/1_Song.py` per-song charts,
  `app/pages/2_Read.py` full-song reading with one visual effect per voice (local only, needs the lyrics file).
- `beatles_viz/` package: data loading, sections, metrics, voice attribution, charts, effects, rendering.
- `tests/` pytest suite (synthetic lyrics only). `scripts/audit_dataset.py` dataset audit (`analysis/audit/`).
- `ROADMAP.md` development plan.
- `scripts/export_public.py` regenerates the lyrics-free `data/public/beatles_bow.parquet` (needs the local lyrics file).
- `scripts/build_dataset.py`, `build_genius.py`, `vocab_by_year.py`: earlier rock / hip-hop experiments (Million Song Dataset, Genius).

## Data
Lyrics are copyrighted and are **not** in this repository (`raw/` and `data/` are git-ignored, except song metadata
without lyrics). To rebuild: download the Genius lyrics datasets from Hugging Face
(`theelderemo/genius-lyrics-cleaned`, `Dr3dre/Genius-song-lyrics-cleaned`) and run `scripts/build_beatles.py`
(arguments: Wikipedia list export, then dataset folders). For personal research use only.
