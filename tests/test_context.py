# Synthetic songs only.
from collections import Counter

import pandas as pd

from beatles_viz.corpus import build_corpus
from beatles_viz.data.export import public_table
from beatles_viz.data import loader
from beatles_viz.text.context import collocates, from_lists, neighbours_of, to_lists, window_pairs


def test_window_pairs_are_symmetric_and_skip_grammar_words():
    pairs = window_pairs("the kettle hums a morning tune".split(), span=2)
    assert pairs[("kettle", "hums")] == pairs[("hums", "kettle")] == 1
    assert ("kettle", "tune") not in pairs and not any("the" in p for p in pairs)


def test_pairs_survive_the_public_file_format():
    pairs = window_pairs("rain falls rain garden falls quiet".split())
    keys, counts = to_lists(pairs)
    assert len(keys) * 2 == len(pairs) and from_lists(keys, counts) == pairs


def test_collocates_read_the_neighbourhood_not_the_song():
    # "rain" sits next to "garden" in both songs; "kettle" is in the same songs but far from it.
    filler = " ".join(f"pad{i}" for i in range(12))
    songs = [f"rain garden {filler} kettle", f"garden rain {filler} kettle", f"kettle {filler} window"]
    d = pd.DataFrame({"bow": [Counter(s.split()) for s in songs], "ctx": [window_pairs(s.split()) for s in songs]})
    near = collocates(d, "rain", min_count=1)
    assert near.word.iloc[0] == "garden" and "kettle" not in near.word.tolist()
    assert neighbours_of(d.ctx, "rain")["garden"] == 2


def test_public_table_carries_pairs_and_line_mood(tmp_path, monkeypatch):
    lyrics = "\n".join(["I cry and I am lonely tonight", "the kettle hums the morning tune",
                        "don't cry little garden", "the rain is sad and slow"] * 3)
    df = pd.DataFrame([dict(title="Kettle", year=1964, lead_vocal="McCartney", lyrics_raw=lyrics, is_original=True,
                            songwriters="Lennon–McCartney", release_core="Test")])
    corpus = build_corpus(df)
    out = public_table(corpus)
    assert {"ctx_pairs", "ctx_counts", "valence_ctx", "mood_lines"} <= set(out)
    path = tmp_path / "bow.parquet"
    out.to_parquet(path, index=False)
    monkeypatch.setattr(loader, "PUBLIC_PATH", path)
    back = build_corpus(loader.load_songs("public", originals_only=False))
    assert back.ctx.iloc[0] == corpus.ctx.iloc[0]
    assert back.valence_ctx.iloc[0] == corpus.valence_ctx.iloc[0]
