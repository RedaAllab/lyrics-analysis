"""The Beatles next to other artists, offline: vocabulary richness, length, repetition and choruses,
mood, distinctive words, closeness between catalogues and change over the first nine years of each career.
Each artist's songs go through the app's own pipeline (beatles_viz.corpus.build_corpus), originals only, songs of
at least MIN_TOKENS words. Tables and figures go to analysis/artists/; they hold numbers and single words only.
Usage: compare_artists.py <beatles.parquet> <artist.parquet> [<artist.parquet> ...]
  (files from scripts/build_artist.py, plus the Beatles file the app reads, data/beatles/beatles.parquet;
  the order of the files is the order of the tables and charts)"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from artist_helpers import career_stage, chorus_share, distinctive, proper_nouns
from beatles_viz.corpus import analysable, build_corpus, doc_frequencies
from beatles_viz.text.similarity import similarity_matrix
from beatles_viz.text.tokenize import content_counter, merge

OUT = ROOT / "analysis/artists"
# First record of the career compared: Love Me Do (Oct 1962), Come On (June 1963), the album Bob Dylan (March 1962),
# McCartney (1970), Give Peace a Chance (1969), Songs of Leonard Cohen (1967), Song to a Seagull (1968) and, for
# Paul Simon, the album Paul Simon (1972): his solo career after Simon & Garfunkel (the 1965 Songbook, songs he
# re-recorded with Garfunkel, falls before the window).
DEBUT = {"The Beatles": 1962, "The Rolling Stones": 1963, "Bob Dylan": 1962, "Paul McCartney": 1970,
         "John Lennon": 1969, "Leonard Cohen": 1967, "Joni Mitchell": 1968, "Paul Simon": 1972}
WINDOW = 9  # the Beatles' whole recording career, 1962-1970
COLORS = {"The Beatles": "#2a6f97", "The Rolling Stones": "#d1495b", "Bob Dylan": "#e09f3e",
          "Paul McCartney": "#7fb3d5", "John Lennon": "#b07bac", "Leonard Cohen": "#8a97a6",
          "Joni Mitchell": "#2a9d8f", "Paul Simon": "#a9844f"}
# Tokenizer leftovers, not words: "café" cut at the accent, "'em" without its apostrophe.
ARTEFACTS = {"caf", "em"}
SHORT = {"The Beatles": "Beatles", "The Rolling Stones": "Stones", "Bob Dylan": "Dylan", "Paul McCartney": "McCartney",
         "John Lennon": "Lennon", "Leonard Cohen": "Cohen", "Joni Mitchell": "Mitchell", "Paul Simon": "Simon"}
METRICS = {"tokens": "Words per song", "types": "Distinct words per song", "mattr": "Vocabulary richness (MATTR-50)",
           "repetition_score": "Repetition (share of matching word pairs)", "repeat_ratio": "Repeated lines (share of words)",
           "chorus_share": "Words sung in choruses (share)", "valence": "Mood (VADER valence, -1..1)",
           "positive": "Positive words (share)", "negative": "Negative words (share)",
           "first_singular": "I / me / my (share)", "second": "you / your (share)"}


def load(path):
    df = pd.read_parquet(path)
    names = proper_nouns(df.lyrics_raw)
    d = analysable(build_corpus(df))  # originals, >= MIN_TOKENS words, no Beatles jams or sound collage
    d = d.assign(chorus_share=[chorus_share(k, w) for k, w in zip(d.sec_kinds, d.sec_words)],
                 has_chorus=d.sec_kinds.map(lambda k: "chorus" in k),
                 career_year=d.year - DEBUT[d.artist.iloc[0]] + 1,
                 stage=d.year.map(lambda y: career_stage(y, DEBUT[d.artist.iloc[0]], WINDOW)))
    return d, names


def summary(d):
    row = {"songs": len(d), "years": f"{d.year.min()}-{d.year.max()}", "total_words": int(d.tokens.sum()),
           "vocabulary": len(merge(d.bow)), "songs_with_chorus": d.has_chorus.mean(),
           "detected_sections": np.mean([any(a) for a in d.sec_auto])}
    for m in METRICS:
        row[f"{m}_median"] = d[m].median()
    return row


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150)
    plt.close(fig)


def main(paths):
    OUT.mkdir(parents=True, exist_ok=True)
    loaded = [load(p) for p in paths]
    corpora = {d.artist.iloc[0]: d for d, _ in loaded}
    names = set().union(*(n for _, n in loaded)) | ARTEFACTS
    artists = list(corpora)
    allsongs = pd.concat(corpora.values(), ignore_index=True)

    # 1. Overall profile, medians per song
    summ = pd.DataFrame({a: summary(d) for a, d in corpora.items()})
    summ.to_csv(OUT / "summary.csv")
    allsongs[["artist", "title", "year", "career_year", "stage", *METRICS, "has_chorus"]].round(4).to_csv(
        OUT / "song_metrics.csv", index=False)

    # 2. Pairwise tests: are the differences in medians more than noise? (Mann-Whitney, two-sided)
    tests = []
    for m in METRICS:
        for i, a in enumerate(artists):
            for b in artists[i + 1:]:
                x, y = corpora[a][m].dropna(), corpora[b][m].dropna()
                tests.append({"metric": m, "a": a, "b": b, "median_a": x.median(), "median_b": y.median(),
                              "p_value": mannwhitneyu(x, y).pvalue})
    pd.DataFrame(tests).round({"median_a": 4, "median_b": 4}).to_csv(OUT / "pairwise_tests.csv", index=False, float_format="%.3g")

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, m in zip(axes.flat, ["mattr", "tokens", "repetition_score", "chorus_share", "valence", "first_singular"]):
        data = [corpora[a][m].dropna() for a in artists]
        parts = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.6,
                           medianprops={"color": "black"})
        for patch, a in zip(parts["boxes"], artists):
            patch.set_facecolor(COLORS[a]); patch.set_alpha(0.75)
        ax.set_xticks(range(1, len(artists) + 1), [SHORT.get(a, a) for a in artists], rotation=45, ha="right")
        ax.set_title(METRICS[m], fontsize=10)
    fig.suptitle("Per-song profile, original songs (boxes: middle half of the songs, line: median)")
    save(fig, "fig1_profile.png")

    # 3. Distinctive words: each artist against all the others together (single words only)
    rows = []
    for a, d in corpora.items():
        counts = content_counter(merge(d.bow))
        others = content_counter(merge(c for b, o in corpora.items() if b != a for c in o.bow))
        top = distinctive(counts, doc_frequencies(d), others, exclude=names)
        rows.append(top.assign(artist=a))
    words = pd.concat(rows)[["artist", "word", "z", "in_group", "in_rest", "songs"]]
    words.round(2).to_csv(OUT / "distinctive_words.csv", index=False)
    cols = min(4, len(artists))
    rows_n = -(-len(artists) // cols)
    fig, axes = plt.subplots(rows_n, cols, figsize=(4.2 * cols, 5.5 * rows_n), squeeze=False)
    for ax in axes.flat[len(artists):]:
        ax.axis("off")
    for ax, a in zip(axes.flat, artists):
        w = words[words.artist == a].head(15)
        ax.barh(w.word[::-1], w.z[::-1], color=COLORS[a])
        ax.set_title(a); ax.set_xlabel("z-score vs all the others")
    fig.suptitle("Most distinctive words (Monroe log-odds, in at least 5 songs, names left out)")
    save(fig, "fig2_distinctive_words.png")

    # 4. How close are the catalogues? Mean TF-IDF cosine between songs of each pair of artists
    sim = similarity_matrix(allsongs)
    labels = allsongs.artist.to_numpy()
    block = pd.DataFrame(index=artists, columns=artists, dtype=float)
    for a in artists:
        for b in artists:
            s = sim[np.ix_(labels == a, labels == b)]
            block.loc[a, b] = (s.sum() - np.trace(s)) / (s.size - len(s)) if a == b else s.mean()
    block.round(4).to_csv(OUT / "similarity_between_artists.csv")

    # 5. First nine years of each career, in three stages
    win = allsongs.dropna(subset=["stage"])
    stages = win.groupby(["artist", "stage"]).agg(songs=("title", "count"), **{
        f"{m}_median": (m, "median") for m in ["tokens", "mattr", "repetition_score", "chorus_share", "valence",
                                               "first_singular", "second"]}).round(4)
    stages.to_csv(OUT / "career_stages.csv")
    yearly = win.groupby(["artist", "career_year"]).agg(songs=("title", "count"), **{
        m: (m, "median") for m in ["tokens", "mattr", "repetition_score", "valence"]}).round(4)
    yearly.to_csv(OUT / "career_years.csv")
    fig, axes = plt.subplots(2, 2, figsize=(15, 9))
    for ax, m in zip(axes.flat, ["mattr", "tokens", "repetition_score", "valence"]):
        for a in artists:
            y = yearly.loc[a]
            ax.plot(y.index, y[m], marker="o", color=COLORS[a], label=a)
            few = y[y.songs < 5]
            ax.plot(few.index, few[m], "o", color="white", markeredgecolor=COLORS[a])  # hollow: fewer than 5 songs
        ax.set_title(METRICS[m], fontsize=10); ax.set_xlabel("year of career (1 = debut year)")
        ax.set_xticks(range(1, WINDOW + 1))
    axes[0, 0].legend(fontsize=8, ncol=2)
    fig.suptitle("First nine years of each career, median per year (hollow dot: fewer than 5 songs)")
    save(fig, "fig3_first_nine_years.png")

    # 6. Whole careers by decade
    decades = allsongs.assign(decade=allsongs.year // 10 * 10).groupby(["artist", "decade"]).agg(
        songs=("title", "count"), **{f"{m}_median": (m, "median") for m in ["tokens", "mattr", "repetition_score",
                                                                            "valence"]}).round(4)
    decades.to_csv(OUT / "decades.csv")

    # 7. Pronouns and mood words in a bar chart
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, m in zip(axes, ["first_singular", "second", "chorus_share"]):
        ax.bar([SHORT.get(a, a) for a in artists], [corpora[a][m].mean() for a in artists],
               color=[COLORS[a] for a in artists])
        ax.tick_params(axis="x", rotation=45)
        ax.set_title(METRICS[m].replace("(share)", "(mean share)"), fontsize=10)
    save(fig, "fig4_pronouns_choruses.png")

    pd.set_option("display.width", 200)
    print(summ.to_string(), "\n", block.round(3).to_string(), "\n", stages.to_string(), sep="\n")
    print(words.groupby("artist").word.apply(lambda w: ", ".join(w.head(12))).to_string())


if __name__ == "__main__":
    main(sys.argv[1:])
