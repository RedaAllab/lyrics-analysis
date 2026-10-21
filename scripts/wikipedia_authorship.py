"""Sentences of the Wikipedia articles (cached by scripts/fetch_wikipedia_credits.py) that say who wrote what: a
member's name next to a writing word (wrote, lyrics, middle eight, contributed...), with the works cited after each
sentence. The output is a reading list, local only (data/credits/wp_cache/authorship_sentences.csv, git-ignored:
it is article prose). The claims read from it go, as facts with their cited work, to
data/credits/wikipedia_claims.csv (columns of manual_claims.csv), then scripts/build_credits.py.
Run: python scripts/wikipedia_authorship.py"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.config import ROOT  # noqa: E402
from beatles_viz.wiki import cited_sentences  # noqa: E402

CREDITS = ROOT / "data/credits"
CACHE = CREDITS / "wp_cache"


def main():
    pages = pd.read_csv(CREDITS / "wp_pages.csv", keep_default_na=False)
    cached = {json.loads(p.read_text()).get("parse", {}).get("title"): p for p in CACHE.glob("*.json")}
    rows = []
    for pg in pages.itertuples():
        path = cached.get(pg.page)
        if path is None:
            continue
        wikitext = json.loads(path.read_text())["parse"]["wikitext"]
        for r in cited_sentences(wikitext):
            rows.append({"level": pg.level, "page": pg.page, "revid": pg.revid, "titles": pg.titles, **r})
    out = pd.DataFrame(rows)
    out.to_csv(CACHE / "authorship_sentences.csv", index=False)
    print(f"{len(out)} sentences from {out.page.nunique()} pages ({(out.cited == '').sum()} without a citation) "
          f"-> {CACHE / 'authorship_sentences.csv'}", file=sys.stderr)


if __name__ == "__main__":
    main()
