import pandas as pd

from beatles_viz.render.components import apply_filters

DF = pd.DataFrame({"title": list("ABCD"), "year": [1963, 1966, 1969, 1977],
                   "voice": ["Lennon", "Harrison", "Lennon", "Starr"], "is_original": [True, True, False, True]})


def test_apply_filters():
    assert apply_filters(DF, True, (1960, 1970), ["Lennon", "Harrison"]).title.tolist() == ["A", "B"]
    assert apply_filters(DF, False, (1960, 1970), ["Lennon"]).title.tolist() == ["A", "C"]
    assert apply_filters(DF, False, (1960, 1980), ["Starr"], voice_col="voice").title.tolist() == ["D"]
