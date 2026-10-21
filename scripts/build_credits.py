"""Credit tables with a source and a confidence on every row (schema in docs/ROADMAP.md, v2, part D):

  data/credits/source.csv              where each claim comes from
  data/credits/person.csv              people named in any credit
  data/credits/recording.csv           the recording each song is matched to in MusicBrainz
  data/credits/work_credit.csv         who wrote the song: official credits, documented contributions, interpretations
  data/credits/performance_credit.csv  who sings, plays, produces or engineers each recording
  analysis/credits/lead_vocal_conflicts.csv  songs where the sources disagree on the lead singer

Inputs: the official song list (columns songwriters, lead_vocal of the corpus), MusicBrainz (scripts/fetch_credits.py)
and data/credits/manual_claims.csv, typed by hand from books and interviews, each row with its source_id. Nothing is
merged away: two sources that disagree give two rows. Run: python scripts/build_credits.py"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.config import MEMBERS, ROOT  # noqa: E402
from beatles_viz.corpus import load_corpus  # noqa: E402
from beatles_viz.credits import CREDITS_DIR, lead_vocal_conflicts, person_id  # noqa: E402

MANUAL = CREDITS_DIR / "manual_claims.csv"
LIST_SOURCE = "wikipedia_song_list"
MB_SOURCE = "musicbrainz"
VOCAL_ROLES = {"lead vocals": "lead_vocal", "background vocals": "backing_vocal", "harmony vocals": "backing_vocal",
               "choir vocals": "backing_vocal"}


def vocal_role(detail):
    for attr in str(detail or "").split("; "):
        if attr in VOCAL_ROLES:
            return VOCAL_ROLES[attr]
    return "vocal"


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
    manual = pd.read_csv(MANUAL, keep_default_na=False) if MANUAL.exists() else pd.DataFrame()
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
            role = vocal_role(c.detail) if c.role == "vocal" else c.role
            perf_rows.append({"title": c.title, "recording_id": c.target_mbid, "person_id": pid, "role": role,
                              "detail": c.detail, "source_id": MB_SOURCE, "confidence": "medium", "note": ""})
    if len(manual):
        for c in manual.itertuples():
            target = work_rows if c.level == "work" else perf_rows
            row = {"title": c.title, "person_id": c.person_id, "role": c.role, "source_id": c.source_id,
                   "confidence": c.confidence, "note": c.note}
            if c.level == "work":
                row["kind"] = c.kind
            else:
                row.update(recording_id=recording_of.get(c.title, ""), detail=c.detail)
            target.append(row)

    work = pd.DataFrame(work_rows).drop_duplicates()
    perf = pd.DataFrame(perf_rows).drop_duplicates()
    names = {**{person_id(n): n for n in corpus.writers.sum() + corpus.other_writers.sum() + corpus.other_singers.sum()},
             **{person_id(n): n for n in mb.person}}
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
    print(f"{len(work)} work credits, {len(perf)} performance credits, {len(people)} people, "
          f"{len(conflicts)} lead vocal disagreements", file=sys.stderr)


if __name__ == "__main__":
    main()
