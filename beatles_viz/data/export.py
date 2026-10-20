"""The lyrics-free table behind the deployed app: metrics, word counts, repetition fingerprint and section shapes."""
from beatles_viz.config import PUBLIC_PATH
from beatles_viz.corpus import STRUCTURE_COLS, analysable

PUBLIC_COLS = ["title", "year", "release_core", "songwriters", "lead_vocal", "is_original", "tokens", "types",
               "mattr", "repeat_ratio", "hapax", "repetition_score", *STRUCTURE_COLS]


def public_table(corpus):
    """corpus: built from the local lyrics. Keeps every column that cannot give the text back."""
    d = analysable(corpus, originals_only=False, improvisations=True)
    out = d[PUBLIC_COLS].copy()
    out["bow_words"] = d.bow.map(lambda c: list(c.keys()))
    out["bow_counts"] = d.bow.map(lambda c: [int(n) for n in c.values()])
    out["fingerprint"] = d.fingerprint.map(lambda f: f.ravel().tolist())
    return out.reset_index(drop=True)


def export_public(corpus, path=PUBLIC_PATH):
    out = public_table(corpus)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, compression="zstd", index=False)
    return out
