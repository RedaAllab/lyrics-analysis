"""Agreement on the hand-annotated themes (data/themes/annotations.csv): between every pair of annotators, and between
each annotator and the model's suggestions (its top 2 themes per song, scripts/suggest_themes.py). Cohen's kappa per
theme, over the songs both have coded. Writes analysis/themes/agreement.csv.
Run: python scripts/theme_agreement.py"""
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz import themes as T  # noqa: E402
from beatles_viz.config import ROOT  # noqa: E402

OUT = ROOT / "analysis/themes"
MODEL = "model (top 2)"

codebook = T.load_codebook()
annotations = T.load_annotations()
matrices = {a: T.theme_matrix(annotations, a, codebook.theme) for a in sorted(annotations.annotator.unique())}
if T.SUGGESTIONS_PATH.exists():
    matrices[MODEL] = T.suggestion_matrix(pd.read_csv(T.SUGGESTIONS_PATH), codebook.theme, top=2)
pairs = [(a, b) for a, b in combinations(matrices, 2)]
if not pairs:
    sys.exit("Nothing to compare yet: annotate songs on the Annotate page (one annotator is enough against the model).")
rows = [T.agreement(matrices[a], matrices[b]).assign(first_coder=a, second_coder=b) for a, b in pairs]
table = pd.concat(rows, ignore_index=True)[["first_coder", "second_coder", "theme", "songs", "first", "second",
                                             "agreement", "kappa"]]
OUT.mkdir(parents=True, exist_ok=True)
table.round(3).to_csv(OUT / "agreement.csv", index=False)
print(table.groupby(["first_coder", "second_coder"]).agg(songs=("songs", "max"), mean_kappa=("kappa", "mean"))
      .round(2).to_string())
