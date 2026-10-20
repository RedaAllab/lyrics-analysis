import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity

from beatles_viz.text.tokenize import content_counter


def similarity_matrix(corpus):
    """Cosine similarity of TF-IDF weighted content-word counts, songs in corpus order."""
    counts = DictVectorizer().fit_transform([dict(content_counter(b)) for b in corpus.bow])
    return cosine_similarity(TfidfTransformer(sublinear_tf=True).fit_transform(counts))


def similar_songs(corpus, title, k=5, matrix=None):
    matrix = similarity_matrix(corpus) if matrix is None else matrix
    i = int(np.flatnonzero(corpus.title.to_numpy() == title)[0])
    order = [j for j in np.argsort(-matrix[i]) if j != i][:k]
    out = corpus.iloc[order][["title", "year", "voice"]].copy()
    out["similarity"] = matrix[i, order]
    return out.reset_index(drop=True)
