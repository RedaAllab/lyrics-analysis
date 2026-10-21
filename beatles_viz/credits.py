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


def lead_vocal_conflicts(perf, sources=None):
    """Songs where two sources name different lead singers. One row per song: each source's singers (empty when a
    source says nothing about the song). sources: the source_ids to compare (default: all)."""
    lead = perf[perf.role == "lead_vocal"]
    if sources is not None:
        lead = lead[lead.source_id.isin(sources)]
    by = lead.groupby(["title", "source_id"]).person_id.agg(lambda p: "; ".join(sorted(set(p)))).unstack()
    if by.shape[1] < 2:
        return pd.DataFrame(columns=["title"])
    by = by[(by.notna().sum(axis=1) >= 2) & (by.nunique(axis=1) > 1)]
    return by.fillna("").reset_index()


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
                    "bell", "glockenspiel", "vibraphone", "brushes", "chime", "claps", "snap", "güiro", "guiro")),
    ("Indian instruments", ("sitar", "tambura", "tabla", "dilruba", "swarmandal", "sarod", "shehnai", "santoor",
                            "surbahar", "pakhawaj", "dholak")),
    ("Winds and brass", ("trumpet", "trombone", "horn", "flugelhorn", "tuba", "saxophone", "clarinet", "flute",
                         "flûte", "piccolo", "oboe", "cor anglais", "bassoon", "recorder", "harmonica", "sax", "whistle",
                         "mouth harp", "mouth organ", "accordion", "ocarina")),
    ("Bass", ("bass",)),  # after percussion and winds: bass drum, bass clarinet
    ("Guitar", ("guitar", "ukulele", "banjo")),
    ("Keyboards", ("piano", "organ", "harmonium", "harpsichord", "mellotron", "moog", "synthesizer", "synthesiser", "clavi",
                   "celesta", "keyboard")),
    ("Strings", ("violin", "viola", "cello", "harp")),
]


def instrument_family(name):
    """'electric bass guitar' -> 'Bass'; 'Hammond organ' -> 'Keyboards'; unknown or vague ('tape') -> 'Other'."""
    name = str(name).lower()
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


MUSICIAN_ROLES = ("lead_vocal", "backing_vocal", "vocal", "instrument")
VAGUE = {"", "guest", "additional", "other instruments", "instrument"}


def musician_claims(perf, source_id):
    """What a source says each person does on each song, as (title, person_id, aspect) rows. Aspects: 'lead vocal',
    'backing vocal', or an instrument family ('Guitar', 'Keyboards'...). An unqualified vocal is the lead when the
    source names no lead singer for the song and no backing part for that person, a backing vocal otherwise."""
    d = perf[(perf.source_id == source_id) & perf.role.isin(MUSICIAN_ROLES)]
    has_lead = set(d[d.role == "lead_vocal"].title)
    backs = set(zip(d[d.role == "backing_vocal"].title, d[d.role == "backing_vocal"].person_id))
    rows = []
    for r in d.itertuples():
        if r.role == "instrument":
            for name in str(r.detail).split("; "):
                family = instrument_family(name)
                if name.strip().lower() not in VAGUE and family != "Other":
                    rows.append((r.title, r.person_id, family))
        elif r.role == "lead_vocal" or (r.role == "vocal" and r.title not in has_lead
                                        and (r.title, r.person_id) not in backs):
            rows.append((r.title, r.person_id, "lead vocal"))
        else:
            rows.append((r.title, r.person_id, "backing vocal"))
    return pd.DataFrame(rows, columns=["title", "person_id", "aspect"]).drop_duplicates()


def compare_sources(perf, a, b, partial_b=False):
    """Song by song, where sources a and b disagree on who sings or plays what. Only songs both sources credit.
    partial_b: b lists only some roles (an album page naming the songs of an exceptional part), so only what b states
    and a lacks is a disagreement. One row per (title, person, aspect) with in_a / in_b."""
    ca, cb = musician_claims(perf, a), musician_claims(perf, b)
    both = set(ca.title) & set(cb.title)
    m = ca[ca.title.isin(both)].assign(in_a=True).merge(cb[cb.title.isin(both)].assign(in_b=True),
                                                        on=["title", "person_id", "aspect"], how="outer")
    m[["in_a", "in_b"]] = m[["in_a", "in_b"]].fillna(False).astype(bool)
    if partial_b:
        m = m[m.in_b]
    return m.sort_values(["title", "person_id", "aspect"]).reset_index(drop=True)


def agreement_summary(compared):
    """Per aspect: claims made by both sources, by a only, by b only, and the share agreed."""
    g = compared.groupby("aspect").agg(both=("in_a", lambda s: int((s & compared.loc[s.index, "in_b"]).sum())),
                                       only_a=("in_b", lambda s: int((~s).sum())),
                                       only_b=("in_a", lambda s: int((~s).sum())))
    g["agreed"] = (g.both / (g.both + g.only_a + g.only_b)).round(3)
    return g.sort_values("both", ascending=False).reset_index()


WRITER_ROLES = {"main_writer", "sole_writer"}
EXCLUSIVE_PARTS = {"middle_eight", "middle_section", "music", "title", "riff"}  # a part only one person can have written
SHARE_ROLES = {"co_writer", "contribution", "lyrics", "verses", "chorus"}


def authorship_summary(work, people=None):
    """Per song, what the documented and interpreted claims say (official credits left out): who is named main or sole
    writer, who co-wrote, who added a part (middle eight, lyrics, riff...), and whether the accounts differ: two people
    named main writer or given the same part (the middle eight, the music), a sole writer while someone else is given
    a share, or a claim noted as disputed by its source."""
    d = work[work.kind != "official"]
    if d.empty:
        return pd.DataFrame(columns=["title", "main", "co", "parts", "claims", "accounts_differ"])
    names = dict(zip(people.person_id, people.name)) if people is not None else {}
    label = lambda ps: ", ".join(names.get(p, p.replace("_", " ").title()) for p in sorted(ps))
    rows = []
    for title, g in d.groupby("title"):
        main = set(g[g.role.isin(WRITER_ROLES)].person_id)
        sole = set(g[g.role == "sole_writer"].person_id)
        co = set(g[g.role == "co_writer"].person_id)
        parts = set(g[~g.role.isin(WRITER_ROLES | {"co_writer"})].person_id)
        same_part = any(g[g.role == r].person_id.nunique() > 1 for r in EXCLUSIVE_PARTS)
        sole_vs_share = bool(sole and set(g[g.role.isin(SHARE_ROLES)].person_id) - sole)
        noted = g.detail.astype(str).str.contains("disput|contradict", case=False).any()
        rows.append({"title": title, "main": label(main), "co": label(co - main), "parts": label(parts - main - co),
                     "claims": len(g), "accounts_differ": len(main) > 1 or same_part or sole_vs_share or noted})
    return pd.DataFrame(rows)
