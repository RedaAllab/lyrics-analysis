# Lyrics analysis

Vocabulary analysis of Beatles lyrics (originals first), built from public datasets.

## Streamlit app
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://redaallab-lyrics-analysis-appbeatles-app-lzrxuu.streamlit.app/)

Deployed app (public): https://redaallab-lyrics-analysis-appbeatles-app-lzrxuu.streamlit.app/

Interactive explorer (vocabulary, evolution over time, lead singers, per-song charts). To deploy another copy, use
[Streamlit Community Cloud](https://share.streamlit.io/deploy?repository=RedaAllab/lyrics-analysis&branch=main&mainModule=app/beatles_app.py)
(main file `app/beatles_app.py`). The app reads `data/public/beatles_bow.parquet`: per-song metrics, word counts,
a repetition score, a 48x48 repetition fingerprint (where words repeat, not which words) and section shapes
(kind and word count of each section), no lyrics text.

Run locally (same versions as Streamlit Cloud, pinned in `requirements.txt` and `pyproject.toml`):
```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/streamlit run app/beatles_app.py
.venv/bin/pytest
```
`BEATLES_PUBLIC_ONLY=1` runs the app as deployed (no lyrics) on a machine that has the lyrics file.

## Layout
- `scripts/build_beatles.py` builds `data/beatles/beatles.parquet` from the official song list (Wikipedia) and Genius lyric datasets.
- `scripts/analyse_beatles.py` tables and figures in `analysis/beatles/`.
- `app/beatles_app.py` entry point (navigation, theme, logo): `app/home_page.py` song search and songs to discover,
  `app/song_page.py` song page with two views, Read (full song with one visual effect per voice, local only, needs the
  lyrics file) and Analyse (per-song charts), `app/word_page.py` one word across the catalogue, `app/compare_page.py` two songs side by side,
  `app/stories_page.py` five guided findings, `app/trends_page.py` drifting words, song architecture and
  lead voices by period, `app/album_page.py` one release at a time, `app/voice_page.py` the lead
  voices side by side (Lennon / McCartney by default), `app/mood_page.py` mood (VADER word valence) and themes,
  `app/corpus_page.py` the whole catalogue, `app/journal_page.py` your favourites, ratings, notes and listening
  history (local only, `data/personal/journal.json`, git-ignored). Song and album pages link to Spotify, Apple Music,
  YouTube Music and Deezer searches (no audio hosted); the song page also plays the official YouTube upload
  (`data/beatles/youtube.csv`, rebuilt by `scripts/youtube_ids.py`), with a section bar that follows the song
  on the songs listed in `beatles_viz/render/listen_view.py` (times estimated from word counts). Theme in `.streamlit/config.toml`, logo in `app/static/`.
- `beatles_viz/` package: data loading and public export, sections (Genius tags, or verses and choruses detected
  from returning stanzas when a song has no tags), metrics, voice attribution, stories, charts, effects, rendering.
- `tests/` pytest suite (synthetic lyrics only). `scripts/audit_dataset.py` dataset audit (`analysis/audit/`).
- `ROADMAP.md` development plan.
- `scripts/export_public.py` regenerates the lyrics-free `data/public/beatles_bow.parquet` (needs the local lyrics file).
- `scripts/build_dataset.py`, `build_genius.py`, `vocab_by_year.py`: earlier rock / hip-hop experiments (Million Song Dataset, Genius).

## Data
Lyrics are copyrighted and are **not** in this repository (`raw/` and `data/` are git-ignored, except song metadata
without lyrics). To rebuild: download the Genius lyrics datasets from Hugging Face
(`theelderemo/genius-lyrics-cleaned`, `Dr3dre/Genius-song-lyrics-cleaned`) and run `scripts/build_beatles.py`
(arguments: Wikipedia list export, then dataset folders). For personal research use only.
