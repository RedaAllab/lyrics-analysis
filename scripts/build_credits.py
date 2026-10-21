"""Credit tables with a source and a confidence on every row (schema in docs/ROADMAP.md, v2, part D):

  data/credits/source.csv              where each claim comes from
  data/credits/person.csv              people named in any credit
  data/credits/recording.csv           the recording each song is matched to in MusicBrainz
  data/credits/work_credit.csv         who wrote the song: official credits, documented contributions, interpretations
  data/credits/performance_credit.csv  who sings, plays, produces or engineers each recording
  analysis/credits/lead_vocal_conflicts.csv  songs where the sources disagree on the lead singer
  analysis/credits/source_disagreements.csv  MusicBrainz against the Wikipedia articles, person by person
  analysis/credits/source_agreement.csv      the same, counted per aspect (lead vocal, guitar, keyboards...)

Inputs: the official song list (columns songwriters, lead_vocal of the corpus), MusicBrainz (scripts/fetch_credits.py),
the Personnel sections of the Wikipedia articles (scripts/fetch_wikipedia_credits.py), data/credits/wikipedia_claims.csv
(who wrote what, read from the articles with the work they cite) and data/credits/manual_claims.csv, typed by hand from books and interviews, each row with its source_id. Nothing is
merged away: two sources that disagree give two rows. Run: python scripts/build_credits.py"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.config import MEMBERS, ROOT  # noqa: E402
from beatles_viz.corpus import load_corpus  # noqa: E402
from beatles_viz.credits import (CREDITS_DIR, agreement_summary, compare_sources, lead_vocal_conflicts,  # noqa: E402
                                 person_id)

MANUAL = CREDITS_DIR / "manual_claims.csv"
WP_CLAIMS = CREDITS_DIR / "wikipedia_claims.csv"
LIST_SOURCE = "wikipedia_song_list"
MB_SOURCE = "musicbrainz"
WP_SONG, WP_ALBUM = "wikipedia_song_page", "wikipedia_album_page"
WP_ROLES = {"lead_vocal", "backing_vocal", "vocal", "instrument", "producer", "engineer", "arranger"}
VOCAL_ROLES = {"lead vocals": "lead_vocal", "background vocals": "backing_vocal", "harmony vocals": "backing_vocal",
               "choir vocals": "backing_vocal"}


def vocal_roles(detail):
    """'background vocals; lead vocals' -> ['backing_vocal', 'lead_vocal']: a part sung both ways gives two rows."""
    roles = list(dict.fromkeys(VOCAL_ROLES[a] for a in str(detail or "").split("; ") if a in VOCAL_ROLES))
    return roles or ["vocal"]


def main():
    corpus = load_corpus("auto")
    mb_rec = pd.read_csv(CREDITS_DIR / "mb_recording.csv")
    mb = pd.read_csv(CREDITS_DIR / "mb_credit.csv", keep_default_na=False)
    accessed = mb.accessed.iloc[0] if len(mb) else ""

    sources = [
        {"source_id": LIST_SOURCE, "type": "secondary",
         "citation": "Wikipedia, List of songs recorded by the Beatles (writer and lead vocal columns, which reproduce "
                     "the official credits of the releases)",
         "url": "https://en.wikipedia.org/wiki/List_of_songs_recorded_by_the_Beatles", "accessed": ""},
        {"source_id": MB_SOURCE, "type": "database",
         "citation": "MusicBrainz, recording and work relationships (CC0), original editions",
         "url": "https://musicbrainz.org/", "accessed": accessed},
    ]
    wp_path = CREDITS_DIR / "wp_credit.csv"
    wp = pd.read_csv(wp_path, keep_default_na=False) if wp_path.exists() else pd.DataFrame()
    if len(wp):
        wp_accessed = wp.accessed.iloc[0]
        sources += [
            {"source_id": WP_SONG, "type": "secondary",
             "citation": "English Wikipedia, Personnel section of the song's article; each row names the works the "
                         "article cites (revision in the note)",
             "url": "https://en.wikipedia.org/", "accessed": wp_accessed},
            {"source_id": WP_ALBUM, "type": "secondary",
             "citation": "English Wikipedia, Personnel section of the album's article, roles limited to named songs "
                         "only; works cited in the note",
             "url": "https://en.wikipedia.org/", "accessed": wp_accessed}]
    claims = [pd.read_csv(p, keep_default_na=False) for p in (WP_CLAIMS, MANUAL) if p.exists()]
    manual = pd.concat(claims, ignore_index=True) if claims else pd.DataFrame()
    manual_sources = CREDITS_DIR / "manual_sources.csv"
    if manual_sources.exists():
        sources += pd.read_csv(manual_sources, keep_default_na=False).to_dict("records")

    recording_of = dict(zip(mb_rec.title, mb_rec.recording_mbid))
    work_rows, perf_rows = [], []
    for row in corpus.itertuples():
        for name in row.writers + row.other_writers:
            work_rows.append({"title": row.title, "person_id": person_id(name), "role": "credited_writer",
                              "kind": "official", "source_id": LIST_SOURCE, "confidence": "high", "note": ""})
        rec = recording_of.get(row.title, "")
        for name in row.lead_singers:
            perf_rows.append({"title": row.title, "recording_id": rec, "person_id": person_id(name),
                              "role": "lead_vocal", "detail": "", "source_id": LIST_SOURCE, "confidence": "medium",
                              "note": "song-level column, version not stated"})
        for name in row.backing_singers + [n for n in row.other_singers if n not in row.lead_singers]:
            perf_rows.append({"title": row.title, "recording_id": rec, "person_id": person_id(name),
                              "role": "backing_vocal" if name in row.backing_singers else "vocal", "detail": "",
                              "source_id": LIST_SOURCE, "confidence": "medium",
                              "note": "song-level column, version not stated"})
    for c in mb.itertuples():
        pid = person_id(c.person)
        if c.level == "work":
            work_rows.append({"title": c.title, "person_id": pid, "role": c.role, "kind": "official",
                              "source_id": MB_SOURCE, "confidence": "medium", "note": f"work {c.target_mbid}"})
        else:
            for role in vocal_roles(c.detail) if c.role == "vocal" else [c.role]:
                perf_rows.append({"title": c.title, "recording_id": c.target_mbid, "person_id": pid, "role": role,
                                  "detail": c.detail, "source_id": MB_SOURCE, "confidence": "medium", "note": ""})
    for c in wp[wp.title.ne("") & wp.kind.isin(WP_ROLES)].itertuples() if len(wp) else []:
        cited = c.line_cited or c.cited
        perf_rows.append({"title": c.title, "recording_id": recording_of.get(c.title, ""), "person_id": person_id(c.person),
                          "role": c.kind, "detail": c.role_text if c.kind == "instrument" else "",
                          "source_id": WP_SONG if c.level == "song" else WP_ALBUM, "confidence": "medium",
                          "note": f"{c.page} (revision {c.revid})" + (f"; cites {cited}" if cited else "; no citation")})
    if len(manual):
        for c in manual.itertuples():
            target = work_rows if c.level == "work" else perf_rows
            row = {"title": c.title, "person_id": c.person_id, "role": c.role, "detail": c.detail,
                   "source_id": c.source_id, "confidence": c.confidence, "note": c.note}
            if c.level == "work":
                row["kind"] = c.kind
            else:
                row["recording_id"] = recording_of.get(c.title, "")
            target.append(row)

    work = pd.DataFrame(work_rows).fillna("").drop_duplicates()
    perf = pd.DataFrame(perf_rows).drop_duplicates()
    names = {**{person_id(n): n for n in corpus.writers.sum() + corpus.other_writers.sum() + corpus.other_singers.sum()},
             **({person_id(n): n for n in wp.person} if len(wp) else {}), **{person_id(n): n for n in mb.person}}
    people = pd.DataFrame([{"person_id": p, "name": n, "is_member": p in {person_id(m) for m in MEMBERS},
                            "mbid": ""} for p, n in sorted(names.items())])
    mbids = dict(zip(mb.person.map(person_id), mb.person_mbid))
    people["mbid"] = people.person_id.map(mbids).fillna("")

    pd.DataFrame(sources).to_csv(CREDITS_DIR / "source.csv", index=False)
    people.to_csv(CREDITS_DIR / "person.csv", index=False)
    mb_rec.rename(columns={"recording_mbid": "recording_id"}).to_csv(CREDITS_DIR / "recording.csv", index=False)
    work.to_csv(CREDITS_DIR / "work_credit.csv", index=False)
    perf.to_csv(CREDITS_DIR / "performance_credit.csv", index=False)

    out = ROOT / "analysis/credits"
    out.mkdir(parents=True, exist_ok=True)
    conflicts = lead_vocal_conflicts(perf)
    conflicts.to_csv(out / "lead_vocal_conflicts.csv", index=False)
    if len(wp):
        archival = dict(zip(corpus.title, corpus.is_archival))
        parts = [compare_sources(perf, MB_SOURCE, WP_SONG).assign(wikipedia=WP_SONG),
                 compare_sources(perf, MB_SOURCE, WP_ALBUM, partial_b=True).assign(wikipedia=WP_ALBUM)]
        cmp = pd.concat(parts, ignore_index=True).rename(columns={"in_a": "musicbrainz", "in_b": "in_wikipedia"})
        cmp["archival"] = cmp.title.map(archival).fillna(False)
        notes = perf[perf.source_id.isin([WP_SONG, WP_ALBUM])].groupby(["title", "person_id", "source_id"]).note.first()
        cmp["wikipedia_note"] = [notes.get((t, p, s), "") for t, p, s in zip(cmp.title, cmp.person_id, cmp.wikipedia)]
        cmp[cmp.musicbrainz != cmp.in_wikipedia].to_csv(out / "source_disagreements.csv", index=False)
        summary = pd.concat([agreement_summary(cmp[(cmp.wikipedia == w) & ~cmp.archival].rename(
            columns={"musicbrainz": "in_a", "in_wikipedia": "in_b"})).assign(wikipedia=w) for w in (WP_SONG, WP_ALBUM)])
        summary.rename(columns={"only_a": "only_musicbrainz", "only_b": "only_wikipedia"}).to_csv(
            out / "source_agreement.csv", index=False)
    print(f"{len(work)} work credits, {len(perf)} performance credits, {len(people)} people, "
          f"{len(conflicts)} lead vocal disagreements", file=sys.stderr)


if __name__ == "__main__":
    main()
