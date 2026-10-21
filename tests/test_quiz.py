# Synthetic songs only.
import random
from collections import Counter

import pandas as pd

from beatles_viz.config import MEMBERS
from beatles_viz.quiz import MIN_WORDS, pool, question

SIGNATURE = ["rain", "kiss", "mountain", "silver", "garden", "window", "river", "candle"]


def corpus(n=8):
    rows = []
    for i in range(n):
        own = {w + str(i): 6 for w in SIGNATURE}  # words only this song uses
        bow = Counter({**own, "common": 20, "plain": 15})
        rows.append(dict(title=f"Song {i}", year=1960 + i, voice=MEMBERS[i % 4] if i < 7 else "Shared", bow=bow))
    return pd.DataFrame(rows)


def test_pool_keeps_only_the_four_voices():
    assert set(pool(corpus()).voice) <= set(MEMBERS) and len(pool(corpus())) == 7


def test_question_gives_the_voice_and_words_from_that_song_only():
    c = corpus()
    q = question(c, random.Random(1))
    song = c[c.title == q.title].iloc[0]
    assert q.voice == song.voice and q.year == song.year
    assert MIN_WORDS <= len(q.words) <= 6 and all(w in song.bow for w in q.words)


def test_title_words_are_never_shown():
    c = corpus()
    c.loc[1, "title"] = "Lantern"  # a title that is also one of the song's own words
    c.at[1, "bow"] = Counter({**c.bow[1], "lantern": 9})
    shown = [question(c, random.Random(seed)) for seed in range(30)]
    assert any(q.title == "Lantern" for q in shown)
    assert all("lantern" not in q.words for q in shown if q.title == "Lantern")


def test_questions_do_not_repeat_until_the_pool_is_used_up():
    c, rng, asked = corpus(), random.Random(3), []
    for _ in range(7):
        q = question(c, rng, asked)
        assert q is not None and q.title not in asked
        asked.append(q.title)
    assert question(c, rng, asked) is None


def test_songs_without_telling_words_are_skipped():
    c = corpus()
    c["bow"] = [Counter({"common": 20, "plain": 15}) for _ in range(len(c))]
    assert question(c, random.Random(0)) is None
