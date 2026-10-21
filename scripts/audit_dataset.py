"""Phase 0 audit of data/beatles/beatles.parquet. Writes label/singer/song tables to analysis/audit/
(metadata and section labels only, never lyrics)."""
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.attribution import lead_voice, resolve_voice  # noqa: E402
from beatles_viz.config import ROOT  # noqa: E402
from beatles_viz.credits import vocal_credit, writer_credit  # noqa: E402
from beatles_viz.data.loader import load_songs  # noqa: E402
from beatles_viz.text.sections import header_tags, normalize_label, parse_members, split_sections  # noqa: E402
from beatles_viz.text.semantic import SEMANTIC_COLS  # noqa: E402

OUT = ROOT / "analysis/audit"
OUT.mkdir(parents=True, exist_ok=True)
# The raw lyrics file only: load_songs also joins the semantic neighbours, which are not part of it.
df = load_songs("local", originals_only=False).drop(columns=SEMANTIC_COLS, errors="ignore")

labels, singers, songs, voices = Counter(), Counter(), [], Counter()
for row in df.itertuples():
    raw_lines = row.lyrics_raw.split("\n")
    for line in raw_lines:
        for label, who in header_tags(line) or []:
            labels[label] += 1
            if who:
                singers[who] += 1
    sections = split_sections(row.lyrics_raw)
    first_header = next((i for i, l in enumerate(raw_lines) if header_tags(l)), None)
    for s in sections:
        voices[(resolve_voice(s, row.lead_vocal), s.kind)] += 1
    songs.append({
        "title": row.title, "year": row.year, "is_original": row.is_original,
        "songwriters": row.songwriters, "lead_vocal": row.lead_vocal, "song_voice": lead_voice(row.lead_vocal),
        "co_written": len(re.findall(r"Lennon|McCartney|Harrison|Starkey|Starr", row.songwriters)) > 1,
        "has_tags": first_header is not None,
        "text_before_first_tag": first_header is not None and any(l.strip() for l in raw_lines[:first_header]),
        "n_sections": len(sections), "sections_with_singer": sum(bool(s.singers) for s in sections),
        "repeat_marks": sum(s.repeat > 1 for s in sections),
        "non_ascii_chars": "".join(sorted({c for c in row.lyrics_raw if ord(c) > 127})),
        "unclosed_tag": any(l.lstrip().startswith("[") and "]" not in l for l in raw_lines),
        "inline_annotations": sum(len(re.findall(r"\[[^\]\n]*\]", l)) for l in raw_lines if header_tags(l) is None),
    })

pd.DataFrame([{"raw_label": k, "kind": normalize_label(k)[0], "number": normalize_label(k)[1], "count": n}
              for k, n in labels.most_common()]).to_csv(OUT / "section_labels.csv", index=False)
pd.DataFrame([{"raw_singers": k, "members": "; ".join(sorted(parse_members(k))) or "(none)", "count": n}
              for k, n in singers.most_common()]).to_csv(OUT / "section_singers.csv", index=False)
songs = pd.DataFrame(songs)
songs.to_csv(OUT / "songs.csv", index=False)
cov = pd.Series(voices).rename("sections").rename_axis(["voice", "kind"]).reset_index()
cov.to_csv(OUT / "voice_coverage_sections.csv", index=False)

# Every credit string must resolve to members and named outsiders, or be marked unknown: nothing is guessed.
credit_rows = []
for raw, n in df.songwriters.value_counts().items():
    c = writer_credit(raw)
    credit_rows.append({"field": "songwriters", "raw": raw, "songs": n, "members": "; ".join(c["writers"]),
                        "others": "; ".join(c["other_writers"]), "label": c["writer_credit"],
                        "resolved": bool(c["writers"] or c["other_writers"])})
for raw, n in df.lead_vocal.value_counts().items():
    c = vocal_credit(raw)
    credit_rows.append({"field": "lead_vocal", "raw": raw, "songs": n, "members": "; ".join(c["lead_singers"]),
                        "others": "; ".join(c["backing_singers"] + c["other_singers"]),
                        "label": "known" if c["vocal_known"] else "unknown",
                        "resolved": bool(c["lead_singers"] or c["other_singers"]) or not c["vocal_known"]})
credits = pd.DataFrame(credit_rows)
credits.to_csv(OUT / "credits.csv", index=False)

orig = songs[songs.is_original]
summary = {
    "songs": len(songs), "originals": len(orig), "columns": ", ".join(df.columns),
    "missing_values": int(df.drop(columns=["lyrics_raw", "lyrics_clean"]).isna().sum().sum()),
    "lead_vocal_dash": int((df.lead_vocal.str.strip() == "–").sum()),
    "songs_without_tags": int((~songs.has_tags).sum()),
    "songs_with_text_before_first_tag": int(songs.text_before_first_tag.sum()),
    "songs_with_unclosed_tag": int(songs.unclosed_tag.sum()),
    "songs_with_inline_annotations": int((songs.inline_annotations > 0).sum()),
    "songs_with_non_ascii": int((songs.non_ascii_chars != "").sum()),
    "distinct_raw_labels": len(labels), "distinct_singer_strings": len(singers),
    "sections": int(songs.n_sections.sum()), "sections_with_named_singer": int(songs.sections_with_singer.sum()),
    "originals_co_written": int(orig.co_written.sum()),
    "credit_strings": len(credits), "credit_strings_unresolved": int((~credits.resolved).sum()),
    "lead_vocal_unknown": int((credits[credits.field == "lead_vocal"].label == "unknown").mul(
        credits[credits.field == "lead_vocal"].songs).sum()),
}
summary.update({f"originals_voice_{v}": int(n) for v, n in orig.song_voice.value_counts().items()})
pd.Series(summary).to_csv(OUT / "summary.csv", header=["value"])
print(pd.Series(summary).to_string())
