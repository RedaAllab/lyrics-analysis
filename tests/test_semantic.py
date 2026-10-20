# Synthetic vectors only: the model itself is not loaded in the test suite.
import numpy as np
import pandas as pd

from beatles_viz.text.semantic import closeness_to, neighbours, semantic_table


def unit(*rows):
    v = np.array(rows, dtype=float)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_neighbours_skip_the_song_itself_and_rank_by_similarity():
    v = unit([1, 0], [0.9, 0.1], [0, 1])
    names, scores = neighbours(v, ["a", "b", "c"], k=2)
    assert names[0] == ["b", "c"] and names[2][0] == "b"
    assert scores[0][0] > scores[0][1]


def test_closeness_leaves_the_song_out_of_its_own_reference():
    v = unit([1, 0], [1, 0], [0, 1])
    c = closeness_to(v, np.array([True, True, False]))
    assert np.allclose(c, [1, 1, 0])


def test_semantic_table_has_only_titles_and_scores():
    v = unit([1, 0], [0.9, 0.1], [0, 1])
    t = semantic_table(pd.DataFrame({"title": ["a", "b", "c"]}), v, [True, True, False])
    assert list(t.columns) == ["title", "sem_neighbors", "sem_scores", "sem_early"]
