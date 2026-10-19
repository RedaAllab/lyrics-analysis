# Synthetic songs only.
import pandas as pd
import pytest

from beatles_viz.corpus import build_corpus, featured_songs
from beatles_viz.viz import compare_charts as cmp

def lyrics(words, n):
    return "\n".join(f"{words} {i}" for i in range(n))


@pytest.fixture(scope="module")
def corpus():
    rows = [("Kettle", 1964, "McCartney", lyrics("the kettle hums the morning tune", 20)),
            ("Lamp", 1967, "Lennon", lyrics("a lamp burns in the empty hallway", 14)),
            ("Rain", 1969, "Harrison", lyrics("slow rain over the quiet garden wall", 16))]
    df = pd.DataFrame([dict(title=t, year=y, lead_vocal=v, lyrics_raw=l, is_original=True,
                            songwriters="Lennon–McCartney", release_core="Test") for t, y, v, l in rows])
    return build_corpus(df)


def pick(corpus, title):
    return corpus[corpus.title == title].iloc[0]


def test_percentiles_are_bounded(corpus):
    fig = cmp.percentile_profile(pick(corpus, "Kettle"), pick(corpus, "Lamp"), corpus)
    values = [v for t in fig.data for v in t.x if v is not None]
    assert values and all(0 <= v <= 100 for v in values)


def test_word_contrast_sides(corpus):
    a, b = pick(corpus, "Kettle"), pick(corpus, "Lamp")
    fig = cmp.word_contrast(a, b)
    words = dict(zip(fig.data[0].y, fig.data[0].x))
    assert words["kettle"] > 0 and words["lamp"] < 0


def test_shared_vocabulary(corpus):
    v = cmp.shared_vocabulary(pick(corpus, "Kettle"), pick(corpus, "Lamp"))
    assert v["shared"] == 0 and v["only_a"] > 0 and v["only_b"] > 0


def test_pronoun_pair_builds(corpus):
    assert cmp.pronoun_pair(pick(corpus, "Kettle"), pick(corpus, "Rain")) is not None


def test_featured_songs_are_distinct(corpus):
    picks = featured_songs(corpus, min_tokens=60)
    titles = [t for _, t, _ in picks]
    assert len(titles) == len(set(titles)) and set(titles) <= set(corpus.title)
