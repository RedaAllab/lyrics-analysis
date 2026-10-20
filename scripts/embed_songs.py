"""Write data/beatles/semantic.parquet: for each song of the public file, its five closest songs in meaning and its
closeness to the first period's songs (sentence-transformer vectors of the stanzas, see beatles_viz/text/semantic.py).
Needs the local lyrics and the nlp extra (pip install -e ".[nlp]"). Then run scripts/export_public.py.
Run: python scripts/embed_songs.py"""
from beatles_viz.config import PHASES, SEMANTIC_PATH
from beatles_viz.corpus import analysable, load_corpus
from beatles_viz.text.semantic import semantic_table, song_vectors

songs = analysable(load_corpus("local"), originals_only=False, improvisations=True)  # the rows of the public file
reference = songs.index.isin(analysable(songs).index) & (songs.phase == PHASES[0][0])
table = semantic_table(songs, song_vectors(songs.sections), reference)
table.to_parquet(SEMANTIC_PATH, index=False)
print(len(table), "songs ->", SEMANTIC_PATH)
