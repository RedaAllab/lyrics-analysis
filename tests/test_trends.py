# Synthetic songs only.
from collections import Counter

import pandas as pd

from beatles_viz.text import trends as T


def corpus():
    rows = []
    for i in range(40):
        phase, year = ("1962-63", 1963) if i < 20 else ("1968-70", 1969)
        bow = Counter({"rain": 6 if year == 1969 else 0, "kiss": 0 if year == 1969 else 6, "plain": 10 + i % 3})
        rows.append(dict(title=f"s{i}", year=year, phase=phase, bow=bow, tokens=sum(bow.values()),
                         voice="Lennon" if i % 2 else "Shared", sec_kinds=["verse", "chorus"],
                         sec_words=[10, 6] if year == 1963 else [8, 12]))
    return pd.DataFrame(rows)


def test_word_trends_find_rising_and_falling_words():
    movers = T.steady_movers(T.word_trends(corpus(), min_songs=5), top=3)
    direction = movers.set_index("word").direction
    assert direction["rain"] == "rising" and direction["kiss"] == "falling"
    assert "plain" not in direction.index


def test_section_and_voice_shares_sum_to_one():
    d = corpus()
    assert T.section_shares(d).sum(axis=1).round(6).eq(1).all()
    shares, counts = T.voice_shares(d)
    assert shares.sum(axis=1).round(6).eq(1).all() and counts.tolist() == [20, 20]
    assert T.section_shares(d).loc["1968-70", "chorus"] > T.section_shares(d).loc["1962-63", "chorus"]
