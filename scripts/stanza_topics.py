"""Recurring subjects of the stanzas, found without a codebook: the core of BERTopic without its heavy dependencies.

1. Each distinct stanza of the original compositions (a chorus sung four times counts once per song) becomes a
   vector (the sentence transformer of scripts/embed_songs.py).
2. k-means groups them; k is chosen between K_MIN and K_MAX by the silhouette (cosine).
3. Stability: the clustering is rerun with other seeds; the adjusted Rand index between runs says how much of the
   grouping is the data and how much is chance (1: identical, 0: chance level).
4. Each group is named by its most specific content words (class-based TF-IDF, as in BERTopic).

Writes data/themes/stanza_topics.csv (one row per topic: words, size, share of each period), stanza_topics_songs.csv
(title, topic, stanzas) and analysis/themes/stanza_topics_quality.csv. Titles, numbers and single words only.
Exploratory: the groups depend on the model and on k. Needs the local lyrics and the nlp extra.
Run: python scripts/stanza_topics.py"""
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.config import PHASE_ORDER, ROOT  # noqa: E402
from beatles_viz.corpus import analysable, load_corpus  # noqa: E402
from beatles_viz.text.semantic import MODEL  # noqa: E402
from beatles_viz.text.tokenize import content, tokenize  # noqa: E402
from beatles_viz.themes import THEMES_DIR  # noqa: E402

K_MIN, K_MAX, SEEDS, TOP_WORDS = 8, 20, 10, 8


def stanzas(songs):
    rows = []
    for title, phase, sections in zip(songs.title, songs.phase, songs.sections):
        seen = set()
        for s in sections:
            text = "\n".join(s.lines).strip()
            if text and text.lower() not in seen and len(content(tokenize(text))) >= 3:
                seen.add(text.lower())
                rows.append({"title": title, "phase": phase, "text": text})
    return pd.DataFrame(rows)


def class_tfidf(texts, labels, top=TOP_WORDS):
    """BERTopic's c-TF-IDF: a word's frequency in the class times log(1 + mean class size / its total frequency)."""
    counts = {k: Counter() for k in sorted(set(labels))}
    for text, k in zip(texts, labels):
        counts[k].update(content(tokenize(text)))
    total = Counter()
    for c in counts.values():
        total.update(c)
    mean_size = np.mean([sum(c.values()) for c in counts.values()])
    out = {}
    for k, c in counts.items():
        size = sum(c.values()) or 1
        score = {w: n / size * np.log(1 + mean_size / total[w]) for w, n in c.items() if total[w] >= 2}
        out[k] = [w for w, _ in sorted(score.items(), key=lambda x: -x[1])[:top]]
    return out


def main():
    from sentence_transformers import SentenceTransformer
    songs = analysable(load_corpus("local"))
    d = stanzas(songs)
    x = SentenceTransformer(MODEL).encode(d.text.tolist(), normalize_embeddings=True)

    quality = []
    for k in range(K_MIN, K_MAX + 1):
        labels = KMeans(k, n_init=10, random_state=0).fit_predict(x)
        quality.append({"k": k, "silhouette": silhouette_score(x, labels, metric="cosine")})
    quality = pd.DataFrame(quality)
    k = int(quality.loc[quality.silhouette.idxmax(), "k"])
    runs = [KMeans(k, n_init=10, random_state=s).fit_predict(x) for s in range(SEEDS)]
    stability = np.mean([adjusted_rand_score(a, b) for a, b in combinations(runs, 2)])
    quality["chosen"] = quality.k == k
    quality["stability_ari"] = np.where(quality.chosen, round(stability, 3), np.nan)

    d["topic"] = runs[0]
    words = class_tfidf(d.text, d.topic)
    topics = []
    for t, g in d.groupby("topic"):
        row = {"topic": t, "words": " ".join(words[t]), "stanzas": len(g), "songs": g.title.nunique(),
               "top_songs": "; ".join(g.title.value_counts().head(5).index)}
        share = g.phase.value_counts(normalize=True)
        row.update({p: round(float(share.get(p, 0)), 3) for p in PHASE_ORDER})
        topics.append(row)
    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(topics).sort_values("stanzas", ascending=False).to_csv(THEMES_DIR / "stanza_topics.csv", index=False)
    d.groupby(["title", "topic"]).size().rename("stanzas").reset_index().to_csv(
        THEMES_DIR / "stanza_topics_songs.csv", index=False)
    out = ROOT / "analysis/themes"
    out.mkdir(parents=True, exist_ok=True)
    quality.round(4).to_csv(out / "stanza_topics_quality.csv", index=False)
    print(f"{len(d)} stanzas, k={k}, silhouette {quality.silhouette.max():.3f}, stability (ARI) {stability:.2f}",
          file=sys.stderr)
    print(pd.DataFrame(topics)[["topic", "stanzas", "songs", "words"]].to_string(index=False), file=sys.stderr)


if __name__ == "__main__":
    main()
