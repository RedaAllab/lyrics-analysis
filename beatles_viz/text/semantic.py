"""Meaning of the lyrics as sentence-transformer vectors. Computed on this machine (scripts/embed_songs.py): only
neighbour titles and similarity scores are kept, never the vectors or the text."""
import numpy as np
import pandas as pd

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SEMANTIC_COLS = ["sem_neighbors", "sem_scores", "sem_early"]


def song_vectors(sections_per_song, model_name=MODEL):
    """One unit vector per song, the mean of its stanza vectors: the model cuts text past 256 word pieces."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    out = []
    for sections in sections_per_song:
        v = model.encode(["\n".join(s.lines) for s in sections if s.lines], normalize_embeddings=True).mean(axis=0)
        out.append(v / np.linalg.norm(v))
    return np.vstack(out)


def neighbours(vectors, titles, k=5):
    sims = vectors @ vectors.T
    np.fill_diagonal(sims, -np.inf)
    order = np.argsort(-sims, axis=1)[:, :k]
    return [[titles[j] for j in row] for row in order], [sims[i, row].round(3).tolist() for i, row in enumerate(order)]


def closeness_to(vectors, reference):
    """Cosine similarity of each song to the mean of the reference songs, the song itself left out."""
    total = vectors[reference].sum(axis=0)
    centres = np.where(reference[:, None], total - vectors, total)
    return np.einsum("ij,ij->i", vectors, centres) / np.linalg.norm(centres, axis=1)


def semantic_table(corpus, vectors, reference):
    names, scores = neighbours(vectors, corpus.title.tolist())
    return pd.DataFrame({"title": corpus.title.to_numpy(), "sem_neighbors": names, "sem_scores": scores,
                         "sem_early": closeness_to(vectors, np.asarray(reference))})
