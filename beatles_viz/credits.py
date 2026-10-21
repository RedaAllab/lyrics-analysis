"""Credits as the official song list gives them (Wikipedia strings in `songwriters`, `lead_vocal`, `release_core`),
split into members and other people. These are official credits only: "Lennon–McCartney" names both members whoever
wrote the song, and nothing here says who actually wrote what (see docs/ROADMAP.md, v2)."""
import re

from beatles_viz.config import MEMBERS

ALIASES = {"Starkey": "Starr"}  # Richard Starkey is credited under his real name
NON_SINGERS = {"Sound Collage", "–", "-", ""}
# Releases put out decades after the band years: their `year` is the year of the session or demo, not of release.
ARCHIVE_ALBUMS = {"Anthology 1", "Anthology 2", "Anthology 3", "Live at the BBC", "On Air – Live at the BBC Volume 2",
                  "The Beatles Bootleg Recordings 1963", "The Beatles: Get Back", "Let It Be: Special Edition"}
ARCHIVE_NOTES = ("Deluxe Edition", "Free as a Bird")  # 2018 White Album demos; the 1995 single's B-side
SPLIT = re.compile(r"\s*(?:\\;|;|,|/|\band\b)\s*")
TRADITIONAL = re.compile(r"\bTrad(?:itional)?\b\.?,?\s*(?:arr\.?)?", re.I)


def _names(text):
    text = TRADITIONAL.sub("Traditional;", str(text or "")).replace("\\", "")
    out = []
    for name in SPLIT.split(text):
        name = re.sub(r"^with\s+", "", name.strip(" ;,"))
        name = ALIASES.get(name, name)
        if name and name not in out:
            out.append(name)
    return out


def _split_members(names):
    members = [n for n in names if n in MEMBERS]  # order of the source: the first named leads
    return members, [n for n in names if n not in MEMBERS]


def writer_label(members, others):
    if not members:
        return "Outside writers"
    if others:
        return "Members with outside writers"
    return "–".join(members)  # "Lennon–McCartney", "Harrison", "Lennon–McCartney–Harrison–Starr"


def writer_credit(songwriters):
    """'Lennon–McCartney' -> members ['Lennon', 'McCartney'], others [], label 'Lennon–McCartney', medley False."""
    text = str(songwriters or "").replace("–", ";")
    members, others = _split_members(_names(text))
    return {"writers": members, "other_writers": others, "writer_credit": writer_label(members, others),
            "medley": "/" in text}


def vocal_credit(lead_vocal):
    """'McCartney; (with Lennon; and Harrison)' -> lead ['McCartney'], backing ['Lennon', 'Harrison'].
    Backing voices are only those the list names in parentheses; '–' and 'Sound Collage' give no singer."""
    text = str(lead_vocal or "").strip()
    if text in NON_SINGERS:
        return {"lead_singers": [], "backing_singers": [], "other_singers": [], "vocal_known": False}
    backing = [n for part in re.findall(r"\((.*?)\)", text) for n in _names(part)]
    lead = _names(re.sub(r"\(.*?\)", "", text))
    lead_m, lead_o = _split_members(lead)
    back_m, back_o = _split_members([n for n in backing if n not in lead])
    return {"lead_singers": lead_m, "backing_singers": back_m, "other_singers": lead_o + back_o, "vocal_known": True}


def release_note(release):
    """'Past Masters; (B-side of " Help!")' -> 'B-side of "Help!"'; '' when the release has no note."""
    notes = re.findall(r"\((.*)\)", str(release or ""))
    return re.sub(r'"\s+', '"', notes[0]).strip() if notes else ""


def is_archival(album, note=""):
    return album in ARCHIVE_ALBUMS or any(n in note for n in ARCHIVE_NOTES)


def credit_columns(row):
    """All derived credit columns for one song (needs songwriters, lead_vocal, release_core and album)."""
    note = release_note(row["release_core"])
    archival = is_archival(row["album"], note)
    return {**writer_credit(row["songwriters"]), **vocal_credit(row["lead_vocal"]), "release_note": note,
            "is_archival": archival, "year_basis": "recording" if archival else "release"}
