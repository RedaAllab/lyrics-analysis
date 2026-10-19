import math

from beatles_viz.text.metrics import mattr, repeat_ratio, text_metrics
from beatles_viz.text.tokenize import content, tokenize


def test_tokenize_keeps_contractions():
    assert tokenize("Don’t STOP, it's fine") == ["don't", "stop", "it's", "fine"]


def test_content_filters_stopwords_vocables_names():
    assert content(["the", "na", "john", "kettle", "a"]) == ["kettle"]


def test_mattr():
    assert math.isnan(mattr(["a"] * 10, window=50))
    assert mattr(["a", "b"] * 30, window=50) == 2 / 50
    assert mattr([str(i) for i in range(60)], window=50) == 1.0


def test_repeat_ratio():
    assert repeat_ratio(["one two", "one two", "three four"]) == 1 - 4 / 6
    assert repeat_ratio(["one", "two"]) == 0


def test_text_metrics_pronouns():
    m = text_metrics(["I see you", "we go"])
    assert m["tokens"] == 5 and m["types"] == 5 and m["hapax"] == 5
    assert m["first_singular"] == 1 / 5 and m["second"] == 1 / 5 and m["first_plural"] == 1 / 5
