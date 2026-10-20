"""Vocabulary analysis of the Beatles' original compositions (data/beatles/beatles.parquet).
Covers: global vocabulary, evolution over time (year / phase), comparison by lead singer.
Outputs: tables (CSV) and figures (PNG) in analysis/beatles/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter

from beatles_viz.config import MATTR_WINDOW, PHASES, ROOT
from beatles_viz.corpus import analysable, load_corpus
from beatles_viz.text.keyness import monroe
from beatles_viz.text.metrics import mattr
from beatles_viz.text.sections import all_lines
from beatles_viz.text.tokenize import content, tokenize

OUT = ROOT / "analysis/beatles"
OUT.mkdir(parents=True, exist_ok=True)

df = analysable(load_corpus("local")).rename(columns={"voice": "singer"})
# MATTR with repeated lines counted once: richness of the writing rather than of the performance
df["mattr_dedup"] = df.sections.map(lambda s: mattr([w for l in dict.fromkeys(x.lower() for x in all_lines(s))
                                                    for w in tokenize(l)]))
df[["title", "year", "phase", "release_core", "singer", "tokens", "types", "mattr", "mattr_dedup", "repeat_ratio"]].to_csv(OUT / "song_metrics.csv", index=False)
print(f"corpus: {len(df)} songs")

# ---------- 1. global vocabulary ----------
allw = [w for ws in df.words for w in ws]
cw = Counter(content(allw))
hapax = sum(1 for n in Counter(allw).values() if n == 1)
glob = dict(songs=len(df), tokens=len(allw), vocabulary=len(set(allw)), hapax=hapax,
            hapax_share=round(hapax / len(set(allw)), 3), mean_tokens=round(df.tokens.mean(), 1),
            mean_types=round(df.types.mean(), 1), mean_mattr50=round(df.mattr.mean(), 3),
            mean_repeat_ratio=round(df.repeat_ratio.mean(), 3))
pd.Series(glob).to_csv(OUT / "global_summary.csv", header=["value"])
top = pd.DataFrame(cw.most_common(40), columns=["word", "count"])
top.to_csv(OUT / "top_words_content.csv", index=False)
fig, ax = plt.subplots(figsize=(7, 8))
ax.barh(top.word[::-1][:30], top["count"][::-1][:30], color="#2a6f97")
ax.set_title("30 most frequent content words (originals)"); ax.set_xlabel("occurrences")
fig.tight_layout(); fig.savefig(OUT / "fig1_top_words.png", dpi=150); plt.close(fig)

# vocabulary growth (songs in chronological order)
ordered = df.sort_values(["year", "title"])
seen, growth = set(), []
for ws in ordered.words:
    seen |= set(ws); growth.append(len(seen))
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(range(1, len(growth) + 1), growth, color="#2a6f97")
ax.set_xlabel("songs (chronological order)"); ax.set_ylabel("cumulative distinct words")
ax.set_title("Vocabulary growth"); fig.tight_layout(); fig.savefig(OUT / "fig2_vocab_growth.png", dpi=150); plt.close(fig)

# ---------- 2. evolution ----------
tm = df[df.year <= 1970]
yr = tm.groupby("year").agg(songs=("title", "count"), tokens=("tokens", "mean"), types=("types", "mean"),
                            mattr=("mattr", "mean"), mattr_dedup=("mattr_dedup", "mean"),
                            repeat_ratio=("repeat_ratio", "mean")).round(3)
yr.to_csv(OUT / "year_summary.csv")
ph = tm.groupby("phase").agg(songs=("title", "count"), tokens=("tokens", "mean"), types=("types", "mean"),
                             mattr=("mattr", "mean"), mattr_dedup=("mattr_dedup", "mean"),
                             repeat_ratio=("repeat_ratio", "mean")).round(3).loc[[p for p, _, _ in PHASES]]
ph.to_csv(OUT / "phase_summary.csv")
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, col, ttl in zip(axes, ["tokens", "mattr", "repeat_ratio"], ["words per song", f"lexical richness (MATTR-{MATTR_WINDOW})", "share of repeated lines"]):
    ax.plot(yr.index, yr[col], marker="o", color="#2a6f97")
    for y, v, n in zip(yr.index, yr[col], yr.songs):
        if n < 5: ax.plot(y, v, "o", color="#bbbbbb")  # grey = fewer than 5 songs
    ax.set_title(ttl); ax.set_xlabel("year")
fig.suptitle("Beatles originals by year (grey dot = fewer than 5 songs)"); fig.tight_layout()
fig.savefig(OUT / "fig3_year_trends.png", dpi=150); plt.close(fig)

total_c = sum(cw.values()); prior = {w: n / total_c for w, n in cw.items()}
def distinctive(col, groups, fname, fig_name, title):
    res = []
    fig, axes = plt.subplots(1, len(groups), figsize=(3.6 * len(groups), 5), sharex=False)
    for ax, g in zip(np.atleast_1d(axes), groups):
        a = Counter(content([w for ws in tm[tm[col] == g].words for w in ws]))
        b = Counter(content([w for ws in tm[tm[col] != g].words for w in ws]))
        r = monroe(a, b, prior).head(10); r.insert(0, col, g); res.append(r)
        ax.barh(r.word[::-1], r.z[::-1], color="#e07a5f"); ax.set_title(f"{g}"); ax.set_xlabel("z-score")
    pd.concat(res).to_csv(OUT / fname, index=False)
    fig.suptitle(title); fig.tight_layout(); fig.savefig(OUT / fig_name, dpi=150); plt.close(fig)

distinctive("phase", [p for p, _, _ in PHASES], "distinctive_words_by_phase.csv", "fig4_phase_words.png", "Words most characteristic of each period")

# word trends per 1000 tokens, by phase
WATCH = ["love", "i", "you", "we", "me", "yeah", "oh", "baby"]
trend = {}
for p, _, _ in PHASES:
    c = Counter(w for ws in tm[tm.phase == p].words for w in ws); n = sum(c.values())
    trend[p] = {w: round(1000 * c[w] / n, 1) for w in WATCH}
trend = pd.DataFrame(trend).T; trend.to_csv(OUT / "word_trends_per_1000_tokens.csv")
fig, ax = plt.subplots(figsize=(8, 4.5))
for w in WATCH: ax.plot(trend.index, trend[w], marker="o", label=w)
ax.set_ylabel("occurrences per 1000 words"); ax.set_title("Selected words by period"); ax.legend(ncol=4, fontsize=8)
fig.tight_layout(); fig.savefig(OUT / "fig5_word_trends.png", dpi=150); plt.close(fig)

# ---------- 3. by lead singer ----------
order = ["Lennon", "McCartney", "Harrison", "Starr", "Shared"]
sg = df.groupby("singer").agg(songs=("title", "count"), tokens=("tokens", "mean"), types=("types", "mean"),
                              mattr=("mattr", "mean"), repeat_ratio=("repeat_ratio", "mean")).round(3).reindex(order)
sg.to_csv(OUT / "singer_summary.csv")
main = [s for s in ["Lennon", "McCartney", "Harrison"] if s in df.singer.values]
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
for ax, col, ttl in zip(axes, ["tokens", "mattr", "repeat_ratio"], ["words per song", f"lexical richness (MATTR-{MATTR_WINDOW})", "share of repeated lines"]):
    ax.boxplot([df[df.singer == s][col].dropna() for s in main], tick_labels=[f"{s}\n(n={int((df.singer == s).sum())})" for s in main])
    ax.set_title(ttl)
fig.suptitle("Lead singer comparison (originals)"); fig.tight_layout(); fig.savefig(OUT / "fig6_singers.png", dpi=150); plt.close(fig)
tm_s = tm.copy()
distinctive("singer", main, "distinctive_words_by_singer.csv", "fig7_singer_words.png", "Words most characteristic of each lead singer")

print(pd.Series(glob)); print(ph); print(sg); print(trend)
