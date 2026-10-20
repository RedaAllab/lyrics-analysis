"""Guided stories: a few findings about the catalogue, each with its chart. Every number and every direction in
the text is computed from the data, so a story stays true if the corpus changes."""
from collections import Counter, namedtuple

import plotly.express as px

from beatles_viz.config import ACCENT, MEMBERS, PHASE_ORDER, VOICE_COLORS
from beatles_viz.corpus import analysable
from beatles_viz.text.words import usage_by
from beatles_viz.viz.compare_charts import contrast_figure, contrast_words
from beatles_viz.viz.trend_charts import phase_strip
from beatles_viz.text.tokenize import merge
from beatles_viz.viz.theme import titled

# link: ("word", w), ("song", title) or ("page", file name)
Story = namedtuple("Story", "key headline text figure links")
EARLY, LATE = PHASE_ORDER[0], PHASE_ORDER[-1]


def trend(a, b):
    return "fell" if b < a else "rose"


def story_corpus(corpus):
    """Original compositions of the band years, long enough to count words."""
    d = analysable(corpus)
    return d[d.phase.notna()]


def _phase_axis(fig):
    fig.update_xaxes(title="", categoryorder="array", categoryarray=PHASE_ORDER)
    return fig


def love_fades(d):
    u = usage_by(d, "love", "phase").set_index("phase").reindex(PHASE_ORDER)
    first, last = u.loc[EARLY], u.loc[LATE]
    text = (f"In {EARLY}, “love” comes back {first.per_1000:.0f} times every 1,000 words and "
            f"{first.songs:.0f} of {first.total_songs:.0f} songs use it. By {LATE} the rate {trend(first.per_1000, last.per_1000)} "
            f"to {last.per_1000:.0f} per 1,000 words, in {last.songs:.0f} of {last.total_songs:.0f} songs. "
            "The love song does not disappear, it stops being the default subject.")
    fig = px.bar(u.reset_index(), x="phase", y="per_1000", color_discrete_sequence=[ACCENT], text_auto=".0f",
                 hover_data={"songs": True, "total_songs": True},
                 labels={"per_1000": "“love” per 1,000 words", "songs": "songs using it", "total_songs": "songs"})
    headline = f"“Love” {trend(first.per_1000, last.per_1000)} from {first.per_1000:.0f} to {last.per_1000:.0f} per 1,000 words"
    return Story("love", headline, text, titled(_phase_axis(fig), headline, 360), [("word", "love")])


def richest_years(d):
    g = d.groupby("phase").mattr.mean().reindex(PHASE_ORDER)
    peak, low = g.idxmax(), g.idxmin()
    top = d[d.phase == peak].sort_values("mattr", ascending=False).iloc[0]
    text = (f"Lexical richness measures how many different words a song uses in every 50-word stretch. "
            f"It peaks in {peak} (average {g[peak]:.2f}) and is lowest in {low} ({g[low]:.2f}). "
            f"The richest song of {peak} is {top.title} ({top.mattr:.2f}). Each dot is a song.")
    headline = f"The richest vocabulary comes in {peak}"
    fig = phase_strip(d, "mattr", "lexical richness (MATTR-50)", headline, 420)
    return Story("richness", headline, text, fig, [("song", top.title)])


def i_to_we(d):
    cols = {"first_singular": "I / me / my", "first_plural": "we / us / our", "second": "you / your"}
    g = (d.groupby("phase")[list(cols)].mean() * 100).reindex(PHASE_ORDER)
    low_i = g.first_singular.idxmin()
    text = (f"Early songs speak in the first person: “I, me, my” make {g.first_singular[EARLY]:.1f} of every "
            f"100 words in {EARLY}. The share drops to {g.first_singular[low_i]:.1f} in {low_i}, while “we, us, our” "
            f"{trend(g.first_plural[EARLY], g.first_plural[low_i])} from {g.first_plural[EARLY]:.1f} to "
            f"{g.first_plural[low_i]:.1f}. The songs talk less about the singer and more about a group, or the world.")
    long = g.rename(columns=cols).reset_index().melt("phase", var_name="pronoun", value_name="per 100 words")
    fig = px.line(long, x="phase", y="per 100 words", color="pronoun", markers=True,
                  color_discrete_sequence=[ACCENT, "#5fa8d3", "#9a9a9a"])
    headline = f"“I” is halved by {low_i}" if g.first_singular[low_i] <= g.first_singular[EARLY] / 2 \
        else f"“I” recedes in {low_i}"
    return Story("pronouns", headline, text, titled(_phase_axis(fig), headline, 380), [("word", "we")])


def song_presence(bows):
    """Each word counted once per song, so one very repetitive song cannot tip the balance."""
    return merge(Counter(dict.fromkeys(b, 1)) for b in bows)


def new_words(d, top=8):
    early, late = d[d.year <= 1965], d[d.year >= 1966]
    a, b = song_presence(late.bow), song_presence(early.bow)
    side = contrast_words(a, b, top=top, min_count=5)
    gained = side[side.z > 0].sort_values("z", ascending=False).word.head(3).tolist()
    lost = side[side.z < 0].sort_values("z").word.head(3).tolist()
    text = (f"Compare the songs released up to 1965 ({len(early)}) with those from 1966 on ({len(late)}). "
            f"The early catalogue leans on {', '.join(f'“{w}”' for w in lost)}; the later one brings "
            f"{', '.join(f'“{w}”' for w in gained)}. Each word is counted once per song: these are words that more "
            "songs use, not words one song repeats.")
    fig = contrast_figure(a, b, "1966-70", "1962-65", colors=["#5fa8d3", ACCENT], top=top, min_count=5,
                          title="Words that changed")
    headline = "From “" + lost[0] + "” to “" + gained[0] + "”" if lost and gained else "Words that changed"
    return Story("words", headline, text, fig, [("word", w) for w in lost[:2] + gained[:2]])


def darkest_voice(d, min_songs=5):
    s = d.dropna(subset=["valence"])
    g = s[s.voice.isin(MEMBERS)].groupby("voice").valence.agg(["mean", "count"])
    g = g[g["count"] >= min_songs].sort_values("mean")
    dark, bright = g.index[0], g.index[-1]
    darkest = s[s.voice == dark].nsmallest(1, "valence").iloc[0]
    text = (f"Score each song by the mood of its words, from −1 (dark) to +1 (bright). Among the voices with at "
            f"least {min_songs} songs, {dark}'s average {g.loc[dark, 'mean']:+.2f} is the lowest and {bright}'s "
            f"{g.loc[bright, 'mean']:+.2f} the highest. {dark}'s darkest is {darkest.title} "
            f"({darkest.valence:+.2f}). Words only: negation and irony are missed.")
    order = g.index.tolist()
    fig = px.box(s[s.voice.isin(order)], x="voice", y="valence", color="voice", points="all", hover_name="title",
                 color_discrete_map=VOICE_COLORS, category_orders={"voice": order},
                 labels={"valence": "mood (−1 dark · +1 bright)", "voice": ""})
    fig.update_layout(showlegend=False)
    headline = f"{dark} sings the darkest songs"
    return Story("mood", headline, text, titled(fig, headline, 400), [("song", darkest.title), ("page", "mood")])


STORIES = [love_fades, richest_years, i_to_we, new_words, darkest_voice]


def build_stories(corpus):
    d = story_corpus(corpus)
    return [s(d) for s in STORIES]
