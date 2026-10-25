# Synthetic songs only.
import io

import numpy as np
import pandas as pd
from PIL import Image

from beatles_viz.render.share_card import card_png
from beatles_viz.share import song_link, standout_facts


def reference():
    return pd.DataFrame({"title": [f"s{i}" for i in range(10)], "tokens": range(100, 200, 10),
                         "mattr": np.linspace(0.4, 0.8, 10), "repetition_score": np.linspace(0.01, 0.05, 10),
                         "valence": np.linspace(-0.5, 0.5, 10)})


def song(**values):
    base = dict(title="x", year=1965, voice="Lennon", tokens=150, mattr=0.6, repetition_score=0.03, valence=0.0,
                fingerprint=np.zeros((48, 48), dtype=np.uint8))
    return pd.Series({**base, **values})


def test_the_most_unusual_measure_comes_first_and_100_percent_is_worded():
    facts = standout_facts(song(tokens=500), reference())
    assert facts[0] == ("Longer than every other Beatles original", "500 words")
    assert len(facts) == 3


def test_percentages_never_round_up_to_every_song():
    ref = pd.concat([reference()] * 30, ignore_index=True).assign(title=lambda d: [f"s{i}" for i in range(len(d))])
    ref.loc[0, "tokens"] = 1000
    headline = standout_facts(song(tokens=500), ref)[0][0]
    assert headline == "Longer than 99% of Beatles originals"


def test_card_is_a_1200_by_630_png():
    png = card_png(song(title="A rather long title that needs two lines on the card"), reference())
    assert Image.open(io.BytesIO(png)).size == (1200, 630)


def test_song_link_escapes_the_title():
    assert song_link("Sgt. Pepper's").endswith("/song?song=Sgt.%20Pepper%27s")


def test_card_scales_for_a_sharp_upload():
    assert Image.open(io.BytesIO(card_png(song(), reference(), scale=2))).size == (2400, 1260)


def test_story_cards_have_the_x_feed_sizes_and_draw_every_chart_kind():
    import plotly.express as px
    import plotly.graph_objects as go
    from collections import namedtuple

    from beatles_viz.render.share_card import story_card_png

    Story = namedtuple("Story", "key headline text figure links")
    long_text = "First sentence of the story. " + "A second, much longer sentence that goes on. " * 30
    d = pd.DataFrame({"phase": ["a", "a", "b", "b"], "v": [1.0, -2.0, 3.0, 0.5], "g": list("xyxy")})
    figures = [px.bar(d, x="phase", y="v"), px.line(d, x="phase", y="v", color="g"), px.box(d, x="phase", y="v", points="all"),
               px.strip(d, x="phase", y="v", color="g"),
               go.Figure(go.Bar(x=[3.0, -2.0], y=["up", "down"], orientation="h"))]
    for fig in figures:
        story = Story("k", "A headline long enough to wrap on a few lines of the card, and then some more", long_text, fig, [])
        for fmt, size in (("wide", (1600, 900)), ("portrait", (1080, 1350))):
            assert Image.open(io.BytesIO(story_card_png(story, 1, 5, fmt))).size == size
