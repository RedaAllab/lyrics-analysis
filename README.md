# Lyrics : analyse des paroles des Beatles

Explorateur Streamlit du vocabulaire, de la structure et des voix dans les paroles des Beatles (compositions
originales par défaut), avec une comparaison à huit catalogues d'artistes.

**App publique** : <https://redaallab-lyrics-analysis-appbeatles-app-lzrxuu.streamlit.app/>
(point d'entrée : `app/beatles_app.py`).

> Projet de fans non officiel, sans lien avec les Beatles, Apple Corps ou leurs maisons de disques.

## Fonctionnement

Chaque chanson passe par `beatles_viz.corpus.build_corpus` :

1. **Sections** : balises Genius (`[Verse 1]`, `[Chorus: Paul McCartney]`…) normalisées ; à défaut, couplets et
   refrains détectés par les strophes qui reviennent (`text/sections.py`, `text/segment.py`).
2. **Mesures** : tokenisation, richesse lexicale (MATTR), répétition et « empreinte » 48×48 des répétitions,
   pronoms, humeur (lexique VADER) et thèmes (`text/`).
3. **Voix** : la voix principale suit le chanteur nommé dans la section, sinon `lead_vocal` de la chanson,
   sinon « Neutral » ; plusieurs voix donnent « Shared » (`attribution.py`). Ce n'est pas le crédit d'écriture.
4. **Rendu** : graphiques Plotly (`viz/`), page « Read » avec un effet visuel par voix (`effects/`), carte de
   partage (`render/share_card.py`).

## Deux modes de données

| Mode | Source | Contenu |
|---|---|---|
| `local` | `data/beatles/beatles.parquet` (git-ignoré) | paroles complètes ; active la page Read, « My songs » et les similarités sémantiques |
| `public` | `data/public/beatles_bow.parquet` (versionné) | métriques, comptes de mots, empreinte de répétition, forme des sections : **aucune parole** |

Les paroles sont protégées par le droit d'auteur et ne sont pas dans le dépôt. Sans fichier local, l'app se
lance en mode `public`. `BEATLES_PUBLIC_ONLY=1` force ce mode sur une machine qui a les paroles.

## Arborescence

```
app/                  Streamlit : beatles_app.py (navigation) + une page par fichier *_page.py ; static/ (logos)
beatles_viz/          paquet Python
  config.py           chemins, phases, seuils, couleurs
  corpus.py           build_corpus / load_corpus / analysable
  attribution.py      règle voix -> effet
  stories.py          les constats des « Stories »
  data/               loader.py (local/public), export.py (export sans paroles)
  text/               tokenisation, sections, métriques, humeur, répétition, sémantique
  viz/                graphiques Plotly
  effects/            un effet visuel par voix
  render/             vues, carte de partage, polices (licences OFL incluses)
scripts/              construction des données et analyses hors ligne
tests/                pytest, paroles synthétiques uniquement
analysis/             tables et figures produites (sans paroles) ; artists/README.md décrit la méthode
data/                 beatles_songs.csv, youtube.csv, section_times.csv, public/ (le reste est git-ignoré)
docs/                 ROADMAP.md, AUDIT_UX.md, PRODUCT_IDEAS.md : notes de travail (en français)
```

## Installation et exécution

Python ≥ 3.11. Les versions sont épinglées comme sur Streamlit Cloud (`requirements.txt`, `pyproject.toml`).

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/streamlit run app/beatles_app.py
```

Extras : `dev` (pytest, duckdb, matplotlib, pour les tests et les scripts) ; `nlp` (sentence-transformers, local
uniquement, pour `scripts/embed_songs.py`).

## Tests

```bash
BEATLES_PUBLIC_ONLY=1 .venv/bin/pytest   # comme la CI GitHub Actions : les tests qui exigent les paroles sont ignorés
.venv/bin/pytest                         # avec le fichier de paroles local : tous les tests
```

## Reconstruire les données (local)

| Étape | Script |
|---|---|
| Liste officielle (Wikipédia) × paroles Genius (datasets Hugging Face `theelderemo/genius-lyrics-cleaned`, `Dr3dre/Genius-song-lyrics-cleaned`) | `scripts/build_beatles.py` (voir son docstring) |
| Autres artistes | `scripts/build_artist.py`, `scripts/album_song_list.py` |
| Vecteurs sémantiques (facultatif) | `scripts/embed_songs.py` |
| Fichier public sans paroles | `scripts/export_public.py` |
| Identifiants YouTube officiels | `scripts/youtube_ids.py` |
| Tables et figures | `scripts/analyse_beatles.py`, `scripts/compare_artists.py`, `scripts/audit_dataset.py` |

## Limites connues

- `build_beatles.py` écrit `beatles_lyrics.csv` ; aucun script versionné ne produit `beatles.parquet` (colonnes
  `title`, `release_core`, `is_original`, `lyrics_raw`…) que l'app lit. Ce fichier local n'est donc pas
  reproductible depuis le dépôt seul.
- Les années Genius sont peu fiables ; l'année retenue est celle de la liste officielle.
- Les horodatages de sections (`section_times.csv`) sont mesurés à l'oreille sur quelques chansons, estimés ailleurs.
- Usage de recherche personnel.
