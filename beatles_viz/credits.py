"""Credits as the official song list gives them (Wikipedia strings in `songwriters`, `lead_vocal`, `release_core`),
split into members and other people. These are official credits only: "Lennon–McCartney" names both members whoever
wrote the song, and nothing here says who actually wrote what (see docs/ROADMAP.md, v2)."""
import re

import pandas as pd

from beatles_viz.config import MEMBER_PATTERNS, MEMBERS, ROOT

CREDITS_DIR = ROOT / "data/credits"  # tables built by scripts/build_credits.py
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


def person_id(name):
    """'John Lennon', 'Lennon' -> 'lennon'; 'Ringo Starr', 'Starkey' -> 'starr'; anyone else: a slug of the name.
    A member's first name only counts with the surname or alone ('George Martin' is the producer)."""
    name = str(name).strip()
    for m, pattern in MEMBER_PATTERNS.items():
        if pattern.search(name):
            return m.lower()
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_table(name, path=None):
    """One credit table (source, person, recording, work_credit, performance_credit); empty when not built."""
    path = path or CREDITS_DIR / f"{name}.csv"
    return pd.read_csv(path, keep_default_na=False) if path.exists() else pd.DataFrame()


def lead_vocal_conflicts(perf):
    """Songs where two sources name different lead singers. One row per song: each source's singers."""
    lead = perf[perf.role == "lead_vocal"]
    by = lead.groupby(["title", "source_id"]).person_id.agg(lambda p: "; ".join(sorted(set(p)))).unstack()
    if by.shape[1] < 2:
        return pd.DataFrame(columns=["title"])
    by = by.dropna()
    return by[by.nunique(axis=1) > 1].reset_index()


def song_performers(perf, people, title):
    """Who sings and plays on the song's recording, one row per person: roles and instruments, with sources."""
    d = perf[(perf.title == title) & perf.role.isin(["lead_vocal", "backing_vocal", "vocal", "instrument"])]
    if d.empty:
        return d
    names = dict(zip(people.person_id, people.name))
    d = d.assign(what=d.role.str.replace("_", " ").where(d.role != "instrument", d.detail))
    g = d.groupby("person_id").agg(what=("what", lambda w: ", ".join(dict.fromkeys(x for x in w if x))),
                                    sources=("source_id", lambda s: ", ".join(sorted(set(s)))))
    g.insert(0, "person", g.index.map(lambda p: names.get(p, p)))
    order = {m.lower(): i for i, m in enumerate(MEMBERS)}
    return g.reset_index().sort_values("person_id", key=lambda s: s.map(lambda p: order.get(p, 9))).drop(
        columns="person_id").reset_index(drop=True)


# MusicBrainz instrument names -> families, checked in order (the first match wins: "bass drum" is percussion).
FAMILIES = [
    ("Percussion", ("drum", "tambourine", "maracas", "handclap", "percussion", "bongo", "conga", "cowbell", "clave",
                    "cymbal", "hi-hat", "wood block", "anvil", "shaker", "finger snap", "tap dance", "timpani",
                    "tubular bells", "glockenspiel", "vibraphone")),
    ("Indian instruments", ("sitar", "tambura", "tabla", "dilruba", "swarmandal", "sarod", "shehnai", "santoor",
                            "surbahar", "pakhawaj", "dholak")),
    ("Bass", ("bass guitar", "double bass")),
    ("Guitar", ("guitar", "ukulele", "banjo")),
    ("Keyboards", ("piano", "organ", "harmonium", "harpsichord", "mellotron", "moog", "synthesizer", "clavi",
                   "celesta", "keyboard")),
    ("Winds and brass", ("trumpet", "trombone", "horn", "flugelhorn", "tuba", "saxophone", "clarinet", "flute",
                         "flûte", "piccolo", "oboe", "cor anglais", "bassoon", "recorder", "harmonica",
                         "mouth harp", "accordion", "ocarina")),
    ("Strings", ("violin", "viola", "cello", "harp")),
]


def instrument_family(name):
    """'electric bass guitar' -> 'Bass'; 'Hammond organ' -> 'Keyboards'; unknown or vague ('tape') -> 'Other'."""
    name = str(name).lower()
    if name == "bass":
        return "Bass"
    return next((fam for fam, keys in FAMILIES if any(k in name for k in keys)), "Other")


def instruments(perf):
    """One row per (song, person, instrument) from the recording credits, with the instrument's family."""
    d = perf[perf.role == "instrument"].assign(instrument=lambda x: x.detail.str.split("; ")).explode("instrument")
    d = d[~d.instrument.isin({"", "guest", "additional", "other instruments"})]
    return d.assign(family=d.instrument.map(instrument_family))[["title", "person_id", "instrument", "family",
                                                                 "source_id"]]


def outside_musicians(perf, people, roles=("instrument", "vocal", "backing_vocal", "lead_vocal")):
    """People other than the four who sing or play, with the songs they are credited on."""
    members = {m.lower() for m in MEMBERS}
    d = perf[perf.role.isin(roles) & ~perf.person_id.isin(members)]
    names = dict(zip(people.person_id, people.name))
    g = d.groupby("person_id").agg(songs=("title", "nunique"), titles=("title", lambda t: ", ".join(sorted(set(t)))))
    g.insert(0, "person", g.index.map(lambda p: names.get(p, p)))
    return g.sort_values(["songs", "person"], ascending=[False, True]).reset_index(drop=True)
