"""Stories, albums and voices. Synthetic songs for the charts; the stories run on the committed public file,
which holds word counts only."""
import pandas as pd
import pytest

from beatles_viz.corpus import album_of, albums, build_corpus, load_corpus
from beatles_viz.stories import build_stories
from beatles_viz.viz import album_charts, voice_charts


def lyrics(words, n):
    return "\n".join(f"{words} {i}" for i in range(n))


@pytest.fixture(scope="module")
def corpus():
    rows = [("Kettle", 1964, "McCartney", "Album A", lyrics("the kettle hums the morning tune", 20)),
            ("Spoon", 1964, "McCartney", "Album A", lyrics("a silver spoon rings against the cup", 18)),
            ("Lamp", 1964, "Lennon", "Album A", lyrics("a lamp burns in the empty hallway", 14)),
            ("Door", 1967, "Lennon", "Album B; (B-side of \" Lamp\")", lyrics("the door swings open to the yard", 15)),
            ("Rain", 1967, "Harrison", "Album B", lyrics("slow rain over the quiet garden wall", 16)),
            ("Clock", 1967, "Lennon", "Album B", lyrics("the clock ticks in the empty kitchen", 12))]
    df = pd.DataFrame([dict(title=t, year=y, lead_vocal=v, release_core=r, lyrics_raw=l, is_original=True,
                            songwriters="Lennon–McCartney") for t, y, v, r, l in rows])
    return build_corpus(df)


def test_album_of_drops_notes():
    assert album_of('Past Masters; (B-side of " Help!")') == "Past Masters"
    assert album_of('The Beatles ("White Album")') == "The Beatles"


def test_albums_in_release_order(corpus):
    table = albums(corpus)
    assert table.album.tolist() == ["Album A", "Album B"] and table.tracks.tolist() == [3, 3]
    assert table.voice.tolist() == ["McCartney", "Lennon"]


def test_album_charts_build(corpus):
    tracks = corpus[corpus.album == "Album A"]
    assert album_charts.album_timeline(albums(corpus), "Album A") is not None
    fig = album_charts.album_structures(tracks)
    assert fig is not None and "kettle hums" not in fig.to_json()
    assert album_charts.album_tracks(tracks, "tokens", "Words") is not None


def test_voice_charts_build(corpus):
    assert voice_charts.voice_radar(corpus, ["Lennon", "McCartney"]) is not None
    assert voice_charts.voice_trend(corpus, ["Lennon"], "mattr", "Richness") is not None
    assert voice_charts.voice_summary(corpus, "Lennon")["songs"] == 3
    assert set(voice_charts.signature_songs(corpus, "Lennon", k=2)) <= {"Lamp", "Door", "Clock"}


@pytest.fixture(scope="module")
def stories():
    return {s.key: s for s in build_stories(load_corpus("public"))}


def test_stories_are_complete(stories):
    assert list(stories) == ["love", "richness", "pronouns", "words", "mood"]
    for s in stories.values():
        assert s.headline and s.text and s.figure is not None and s.links


def test_stories_match_the_data(stories):
    # The headlines are computed; these are the findings the page was written around.
    assert stories["love"].headline.startswith("“Love” fell")
    assert stories["richness"].headline.endswith("1964-65")
    assert "1966-67" in stories["pronouns"].headline
    assert stories["mood"].headline.startswith("Lennon")
