# Lyrics: analysing the Beatles' words

A Streamlit explorer for the vocabulary, structure and voices in Beatles lyrics (original compositions by default),
with a comparison against eight artist catalogues.

**Public app**: <https://redaallab-lyrics-analysis-appbeatles-app-lzrxuu.streamlit.app/>
(entry point: `app/beatles_app.py`).

> Unofficial fan project, not affiliated with The Beatles, Apple Corps or their record labels.

## How it works

Each song goes through `beatles_viz.corpus.build_corpus`:

1. **Sections**: Genius tags (`[Verse 1]`, `[Chorus: Paul McCartney]`…) are normalised; when a song has none,
   verses and choruses are detected from returning stanzas (`text/sections.py`, `text/segment.py`).
2. **Metrics**: tokenisation, lexical richness (MATTR), repetition and a 48×48 repetition "fingerprint",
   pronouns, mood (VADER lexicon) and themes (`text/`).
3. **Voices**: the lead voice is the singer named in the section tag, otherwise the song's `lead_vocal`,
   otherwise "Neutral"; several voices give "Shared" (`attribution.py`). This is not the songwriting credit.
4. **Rendering**: Plotly charts (`viz/`), a Read page with one visual effect per voice (`effects/`), and a
   share card (`render/share_card.py`).

## Two data modes

| Mode | Source | Content |
|---|---|---|
| `local` | `data/beatles/beatles.parquet` (git-ignored) | full lyrics; enables the Read page, "My songs" and semantic similarities |
| `public` | `data/public/beatles_bow.parquet` (versioned) | metrics, word counts, repetition fingerprint, section shapes: **no lyrics** |

Lyrics are copyrighted and are not in the repository. Without the local file the app starts in `public` mode.
`BEATLES_PUBLIC_ONLY=1` forces that mode on a machine that has the lyrics.

## Layout

```
app/                  Streamlit: beatles_app.py (navigation) + one *_page.py per page; static/ (logos)
beatles_viz/          Python package
  config.py           paths, phases, thresholds, colours
  corpus.py           build_corpus / load_corpus / analysable
  attribution.py      voice -> effect rule
  stories.py          the findings shown in "Stories"
  data/               loader.py (local/public), export.py (lyrics-free export)
  text/               tokenisation, sections, metrics, mood, repetition, semantics
  viz/                Plotly charts
  effects/            one visual effect per voice
  render/             views, share card, fonts (OFL licences included)
scripts/              offline data building and analyses
tests/                pytest, synthetic lyrics only
analysis/             generated tables and figures (no lyrics); artists/README.md describes the method
data/                 beatles_songs.csv, youtube.csv, section_times.csv, public/ (the rest is git-ignored)
docs/                 ROADMAP.md, AUDIT_UX.md, PRODUCT_IDEAS.md: working notes (in French)
```

## Install and run

Python ≥ 3.11. Versions are pinned to match Streamlit Cloud (`requirements.txt`, `pyproject.toml`).

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/streamlit run app/beatles_app.py
```

Extras: `dev` (pytest, duckdb, matplotlib, for tests and scripts); `nlp` (sentence-transformers, local only, for
`scripts/embed_songs.py`).

## Tests

```bash
BEATLES_PUBLIC_ONLY=1 .venv/bin/pytest   # as in GitHub Actions CI: tests that need the lyrics are skipped
.venv/bin/pytest                         # with the local lyrics file: all tests
```

## Rebuilding the data (local)

| Step | Script |
|---|---|
| Official song list (Wikipedia) × Genius lyrics (Hugging Face datasets `theelderemo/genius-lyrics-cleaned`, `Dr3dre/Genius-song-lyrics-cleaned`) | `scripts/build_beatles.py` (see its docstring) |
| Other artists | `scripts/build_artist.py`, `scripts/album_song_list.py` |
| Semantic vectors (optional) | `scripts/embed_songs.py` |
| Public lyrics-free file | `scripts/export_public.py` |
| Official YouTube IDs | `scripts/youtube_ids.py` |
| Tables and figures | `scripts/analyse_beatles.py`, `scripts/compare_artists.py`, `scripts/audit_dataset.py` |

## Known limitations

- `build_beatles.py` writes `beatles_lyrics.csv`; no versioned script produces the `beatles.parquet` the app reads
  (columns `title`, `release_core`, `is_original`, `lyrics_raw`…), so that local file cannot be rebuilt from the
  repository alone.
- Genius years are unreliable; the year used is the one from the official list.
- Section timestamps (`section_times.csv`) are measured by ear on a few songs and estimated for the others.
- For personal research use only.
