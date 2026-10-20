from collections import Counter

from beatles_viz.text.mood import NEUTRAL_WORDS, lexicon, mood, mood_words, themes


def test_bright_and_dark_words():
    assert mood(Counter({"happy": 3, "love": 2, "sunshine": 2, "the": 10}))["valence"] > 0.3
    assert mood(Counter({"cry": 3, "lonely": 2, "misery": 2, "dead": 1}))["valence"] < -0.3


def test_interjections_do_not_count():
    assert not NEUTRAL_WORDS & set(lexicon())
    assert mood(Counter({"yeah": 50, "no": 20}))["mood_words"] == 0


def test_too_few_mood_words_gives_no_score():
    r = mood(Counter({"happy": 1, "the": 40}))
    assert r["valence"] != r["valence"] and r["positive"] == 1 / 41


def test_mood_words_split_by_sign():
    pos, neg = mood_words(Counter({"happy": 2, "cry": 3, "table": 4}))
    assert [w for w, _ in pos] == ["happy"] and [w for w, _ in neg] == ["cry"]


def test_theme_rates_per_thousand():
    t = themes(Counter({"sun": 5, "rain": 5, "money": 10, "the": 980}))
    assert t["Nature"] == 10 and t["Money and work"] == 10 and t["Love"] == 0
