"""Model suggestions to help, and to check, the hand annotation of themes. Two independent proposals:

1. data/themes/suggestions.csv: each theme of the codebook is described in plain words (label, definition, what to
   include) and turned into a vector by the same sentence transformer as scripts/embed_songs.py; a song's score for
   a theme is the mean of its two closest stanzas. One row per song and theme: score and rank within the song.
2. data/themes/nmf_topics.csv and nmf_songs.csv: NMF on TF-IDF content words (12 topics), to spot groups of words
   the codebook may have missed. Topics are lists of single words; their names are left to the reader.

Only titles, theme names, scores and single words are written, never lyrics. Needs the local lyrics and the nlp
extra (pip install -e ".[nlp]"). Run: python scripts/suggest_themes.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.corpus import analysable, load_corpus  # noqa: E402
from beatles_viz.text.semantic import MODEL  # noqa: E402
from beatles_viz.text.tokenize import content_counter  # noqa: E402
from beatles_viz.themes import SUGGESTIONS_PATH, THEMES_DIR, load_codebook  # noqa: E402

N_TOPICS, TOP_STANZAS, SEED = 12, 2, 0


def theme_scores(songs, codebook):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL)
    descriptions = (codebook.label + ". " + codebook.definition + " " + codebook.include).tolist()
    themes = model.encode(descriptions, normalize_embeddings=True)
    rows = []
    for title, sections in zip(songs.title, songs.sections):
        stanzas = ["\n".join(s.lines) for s in sections if s.lines]
        sims = model.encode(stanzas, normalize_embeddings=True) @ themes.T  # stanzas x themes
        k = min(TOP_STANZAS, len(stanzas))
        score = np.sort(sims, axis=0)[-k:].mean(axis=0)
        for rank, j in enumerate(np.argsort(-score), start=1):
            rows.append({"title": title, "theme": codebook.theme.iloc[j], "score": round(float(score[j]), 4),
                         "rank": rank})
    return pd.DataFrame(rows)


def nmf_topics(songs):
    counts = DictVectorizer()
    x = TfidfTransformer(sublinear_tf=True).fit_transform(counts.fit_transform(
        [dict(content_counter(b)) for b in songs.bow]))
    model = NMF(n_components=N_TOPICS, init="nndsvda", random_state=SEED, max_iter=1000)
    weights = model.fit_transform(x)
    vocab = np.array(counts.get_feature_names_out())
    topics = pd.DataFrame({"topic": range(N_TOPICS),
                           "top_words": [" ".join(vocab[np.argsort(-c)[:10]]) for c in model.components_]})
    per_song = pd.DataFrame(weights.round(4), columns=[f"topic_{i}" for i in range(N_TOPICS)])
    per_song.insert(0, "title", songs.title.to_numpy())
    return topics, per_song


def main():
    songs = analysable(load_corpus("local"))
    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    theme_scores(songs, load_codebook()).to_csv(SUGGESTIONS_PATH, index=False)
    topics, per_song = nmf_topics(songs)
    topics.to_csv(THEMES_DIR / "nmf_topics.csv", index=False)
    per_song.to_csv(THEMES_DIR / "nmf_songs.csv", index=False)
    print(len(songs), "songs ->", SUGGESTIONS_PATH, "and NMF topics:", file=sys.stderr)
    print(topics.to_string(index=False), file=sys.stderr)


if __name__ == "__main__":
    main()
