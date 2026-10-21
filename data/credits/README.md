# Credits

Who wrote, sang and played each song, every row with its source and a confidence level. No lyrics here.

| File | Content | Made by |
|---|---|---|
| `source.csv` | where each claim comes from (type: primary, reference, database, secondary, interpretation) | `scripts/build_credits.py` |
| `person.csv` | people named in any credit (`is_member`, MusicBrainz id) | idem |
| `recording.csv` | the MusicBrainz recording each song is matched to (original edition) | idem |
| `work_credit.csv` | who wrote the song: `kind` = official (credit), documented (attested contribution), interpretation (analysis) | idem |
| `performance_credit.csv` | who sings, plays, produces or engineers the recording | idem |
| `mb_recording.csv`, `mb_credit.csv`, `mb_missing.csv` | raw MusicBrainz extract (CC0) | `scripts/fetch_credits.py` |
| `manual_sources.csv`, `manual_claims.csv` | claims typed by hand from books, interviews and studies | by hand |

Rules:

- Never merge: two sources that disagree give two rows; `analysis/credits/lead_vocal_conflicts.csv` lists them.
- "Lennon–McCartney" is the official credit of both, whoever wrote the song. Who actually wrote what goes in
  `manual_claims.csv` as `documented` (testimony, sessions) or `interpretation` (analysis), with its source.
- No source, no row. Unknown stays unknown.
- Confidence: `high` (official credit, primary document), `medium` (reference book, curated database), `low`
  (single testimony contradicted elsewhere, statistical inference).

Adding a claim from a book: add the book once to `manual_sources.csv` (with the edition), then one row per claim to
`manual_claims.csv` (`level` work or recording, `person_id` lennon / mccartney / harrison / starr or a slug, `role`
lyrics, music, middle_eight, lead_vocal, instrument…, the page in `note`), then run `python scripts/build_credits.py`.
