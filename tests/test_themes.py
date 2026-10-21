# Synthetic annotations only.
import pandas as pd
import pytest

from beatles_viz import themes as T

CODEBOOK = pd.DataFrame({"theme": ["love_devotion", "heartbreak", "society"], "label": ["Love", "Hurt", "World"],
                         "definition": "", "include": "", "exclude": ""})


def test_save_replaces_the_annotators_row_and_checks_the_codebook(tmp_path):
    path = tmp_path / "a.csv"
    T.save_annotation("Song A", "rb", ["love_devotion"], path=path, codebook=CODEBOOK)
    T.save_annotation("Song A", "rb", ["heartbreak", "society"], "society", True, "irony", path=path,
                      codebook=CODEBOOK)
    T.save_annotation("Song A", "xy", ["love_devotion"], path=path, codebook=CODEBOOK)
    d = T.load_annotations(path)
    assert len(d) == 2
    row = d[d.annotator == "rb"].iloc[0]
    assert T.theme_list(row.themes) == ["heartbreak", "society"] and row.main_theme == "society" and row.implicit
    with pytest.raises(ValueError):
        T.save_annotation("Song B", "rb", ["unknown"], path=path, codebook=CODEBOOK)
    with pytest.raises(ValueError):
        T.save_annotation("Song B", "rb", ["heartbreak"], "society", path=path, codebook=CODEBOOK)


def test_kappa():
    assert T.kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1
    assert T.kappa([1, 1, 0, 0], [0, 0, 1, 1]) == -1
    assert T.kappa([1, 1, 1], [1, 1, 1]) != T.kappa([1, 1, 1], [1, 1, 1])  # nan: no variation


def test_agreement_and_suggestions():
    ann = pd.DataFrame({"title": ["A", "B", "A", "B"], "annotator": ["p", "p", "q", "q"],
                        "themes": ["love_devotion", "society", "love_devotion", "heartbreak;society"]})
    m_p, m_q = (T.theme_matrix(ann, a, CODEBOOK.theme) for a in "pq")
    agr = T.agreement(m_p, m_q).set_index("theme")
    assert agr.loc["love_devotion", "kappa"] == 1 and agr.loc["heartbreak", "agreement"] == 0.5
    sug = pd.DataFrame({"title": ["A", "A", "B", "B"], "theme": ["love_devotion", "society", "society", "heartbreak"],
                        "score": [0.5, 0.2, 0.4, 0.1], "rank": [1, 2, 1, 2]})
    m = T.suggestion_matrix(sug, CODEBOOK.theme, top=1)
    assert m.loc["A", "love_devotion"] and not m.loc["A", "society"] and m.loc["B", "society"]


def test_theme_shares():
    m = pd.DataFrame({"love_devotion": [True, False, True]}, index=["A", "B", "C"])
    s = T.theme_shares(m, pd.Series({"A": "early", "B": "early", "C": "late"}))
    assert s.loc["early", "love_devotion"] == 0.5 and s.loc["late", "songs"] == 1


def test_annotated_heatmap_builds():
    from beatles_viz.viz.mood_charts import annotated_theme_heatmap
    corpus = pd.DataFrame({"title": ["A", "B", "C"], "phase": ["1962-63", "1962-63", "1968-70"]})
    m = pd.DataFrame({"love_devotion": [True, False, True], "society": [False, False, True]}, index=["A", "B", "C"])
    fig = annotated_theme_heatmap(m, corpus, {"love_devotion": "Love"})
    assert list(fig.data[0].x) == ["1962-63 (2)", "1968-70 (1)"] and fig.data[0].z[0][0] == 0.5


def test_stanza_topic_shares_and_heatmap():
    from beatles_viz.viz.mood_charts import stanza_topic_heatmap
    corpus = pd.DataFrame({"title": ["A", "B"], "phase": ["1962-63", "1968-70"]})
    songs = pd.DataFrame({"title": ["A", "A", "B"], "topic": [0, 1, 1], "stanzas": [3, 1, 2]})
    s = T.stanza_topic_shares(songs, corpus)
    assert s.loc["1962-63", 0] == 0.75 and s.loc["1968-70", 1] == 1
    topics = pd.DataFrame({"topic": [1, 0], "words": ["sun sky blue day rain", "love need"]})
    fig = stanza_topic_heatmap(s, topics)
    assert list(fig.data[0].y) == ["sun sky blue day", "love need"]
