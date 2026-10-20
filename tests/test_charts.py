# Synthetic mini-corpus only: real lyrics never go into the test suite.
import pandas as pd
import pytest

from beatles_viz.corpus import build_corpus
from beatles_viz.viz import song_charts as charts

TAGGED = "\n".join(["[Verse 1: Paul McCartney]"] + [f"the kettle hums at seven number {i}" for i in range(8)]
                   + ["[Chorus: John Lennon & Paul McCartney]", "round the table again", "round the table again",
                      "[Guitar Solo]", "[Verse 2]"] + [f"a lamp in the hallway stays on {i}" for i in range(8)])
UNTAGGED = "\n".join(f"walking down the quiet morning street {i}" for i in range(10))
SHORT = "tiny song\nvery small"


@pytest.fixture(scope="module")
def corpus():
    rows = [("Kettle", 1964, "McCartney", TAGGED), ("Street", 1967, "Lennon", UNTAGGED),
            ("Tiny", 1969, "Starr", SHORT)]
    df = pd.DataFrame([dict(title=t, year=y, lead_vocal=v, lyrics_raw=l, is_original=True,
                            songwriters="Lennon–McCartney", release_core="Test album") for t, y, v, l in rows])
    return build_corpus(df)


def test_corpus_columns(corpus):
    for col in ["sections", "bow", "tokens", "types", "mattr", "repeat_ratio", "voice", "phase", "second"]:
        assert col in corpus
    assert corpus.set_index("title").loc["Kettle", "voice"] == "McCartney"


def test_every_chart_builds_or_returns_none(corpus):
    for song in corpus.itertuples():
        row = corpus.loc[song.Index]
        charts.structure_timeline(row)
        charts.self_similarity(song.sections)
        charts.rolling_richness(song.sections)
        charts.keyness(song.bow, corpus[corpus.title != song.title].bow)
        charts.corpus_position(row, corpus, song.phase)
        charts.pronoun_profile(row, corpus)
        charts.voice_split(song.sections, song.lead_vocal)


def test_untagged_song_still_has_structure_and_density(corpus):
    street = corpus.set_index("title").loc["Street"]
    assert charts.structure_timeline(street) is not None
    assert charts.rolling_richness(street.sections) is not None
    assert charts.voice_split(street.sections, street.lead_vocal) is None


def test_short_song_has_no_density_curve(corpus):
    assert charts.rolling_richness(corpus.set_index("title").loc["Tiny"].sections) is None


def test_voice_split_only_with_tagged_singers(corpus):
    kettle = corpus.set_index("title").loc["Kettle"]
    fig = charts.voice_split(kettle.sections, kettle.lead_vocal)
    assert {t.name for t in fig.data} == {"McCartney", "Shared"}


def test_figures_never_contain_lyric_lines(corpus):
    kettle = corpus.set_index("title").loc["Kettle"]
    for fig in [charts.structure_timeline(kettle), charts.self_similarity(kettle.sections),
                charts.voice_split(kettle.sections, kettle.lead_vocal)]:
        assert "kettle hums" not in fig.to_json()
