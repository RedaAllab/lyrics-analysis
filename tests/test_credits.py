# Strings copied from the official song list (metadata, not lyrics).
import pandas as pd
import pytest

from beatles_viz.attribution import lead_members
from beatles_viz.credits import (is_archival, lead_vocal_conflicts, person_id, release_note, song_performers,
                                 vocal_credit, writer_credit)

VOCALS = ["Harrison", "Harrison; McCartney", "Lennon; (with Harrison)", "Lennon; (with McCartney; and Harrison)",
          "Lennon; (with Yoko Ono)", "Lennon; McCartney; Harrison; Eric Morecambe; Ernie Wise", "Lennon; and McCartney",
          "McCartney; (with Lennon,; Harrison,; and Starr)", "McCartney; and Lennon", "Sound Collage", "Starr",
          "Tony Sheridan", "–"]


@pytest.mark.parametrize("raw, members, others, label", [
    ("Lennon–McCartney", ["Lennon", "McCartney"], [], "Lennon–McCartney"),
    ("Lennon; McCartney", ["Lennon", "McCartney"], [], "Lennon–McCartney"),
    ("Starkey", ["Starr"], [], "Starr"),
    ("Lennon; McCartney; Harrison; Starr", ["Lennon", "McCartney", "Harrison", "Starr"], [],
     "Lennon–McCartney–Harrison–Starr"),
    (r"Jerry Leiber\; \; Mike Stoller",[], ["Jerry Leiber", "Mike Stoller"], "Outside writers"),
    ("Cy Coben, Mel Foree", [], ["Cy Coben", "Mel Foree"], "Outside writers"),
    ("Trad. arr. Tony Sheridan", [], ["Traditional", "Tony Sheridan"], "Outside writers"),
    ("Traditional, arr.; Lennon; McCartney; Harrison; Starkey", ["Lennon", "McCartney", "Harrison", "Starr"],
     ["Traditional"], "Members with outside writers"),
    ("Rudolph Isley; Ronald Isley; O'Kelly Isley Jr.", [], ["Rudolph Isley", "Ronald Isley", "O'Kelly Isley Jr."],
     "Outside writers"),
])
def test_writer_credit(raw, members, others, label):
    c = writer_credit(raw)
    assert (c["writers"], c["other_writers"], c["writer_credit"]) == (members, others, label)


def test_medley_credits_are_merged_and_flagged():
    c = writer_credit("Lennon; McCartney /; Lennon; McCartney; Harrison; Starkey")
    assert c["writers"] == ["Lennon", "McCartney", "Harrison", "Starr"] and c["medley"]
    assert not writer_credit("Harrison")["medley"]


def test_vocal_credit_separates_lead_backing_and_guests():
    c = vocal_credit("McCartney; (with Lennon,; Harrison,; and Starr)")
    assert c["lead_singers"] == ["McCartney"] and c["backing_singers"] == ["Lennon", "Harrison", "Starr"]
    assert vocal_credit("Lennon; (with Yoko Ono)")["other_singers"] == ["Yoko Ono"]
    assert vocal_credit("McCartney; and Lennon")["lead_singers"] == ["McCartney", "Lennon"]
    for raw in ("–", "Sound Collage"):
        assert vocal_credit(raw) == {"lead_singers": [], "backing_singers": [], "other_singers": [],
                                     "vocal_known": False}


@pytest.mark.parametrize("raw", VOCALS)
def test_lead_singers_agree_with_the_voice_rule(raw):
    assert set(vocal_credit(raw)["lead_singers"]) == set(lead_members(raw))


def test_release_note_and_archives():
    assert release_note('Past Masters; (B-side of " Help!")') == 'B-side of "Help!"'
    assert release_note("Revolver") == ""
    assert is_archival("Anthology 1") and is_archival("The Beatles: Get Back")
    assert is_archival("The Beatles", "2018 Deluxe Edition") and not is_archival("Abbey Road")


def test_person_id_keeps_the_producer_apart():
    assert [person_id(n) for n in ["John Lennon", "Starkey", "Ringo Starr", "George Harrison", "George Martin",
                                   "Billy Preston"]] == ["lennon", "starr", "starr", "harrison", "george_martin",
                                                         "billy_preston"]


def test_conflicts_and_performers():
    perf = pd.DataFrame([
        ("A", "lennon", "lead_vocal", "", "list"), ("A", "mccartney", "lead_vocal", "", "mb"),
        ("A", "mccartney", "instrument", "bass guitar", "mb"), ("A", "george_martin", "producer", "", "mb"),
        ("B", "harrison", "lead_vocal", "", "list"), ("B", "harrison", "lead_vocal", "", "mb"),
        ("C", "starr", "lead_vocal", "", "list")],
        columns=["title", "person_id", "role", "detail", "source_id"])
    conflicts = lead_vocal_conflicts(perf)
    assert conflicts.title.tolist() == ["A"] and conflicts.iloc[0]["mb"] == "mccartney"
    people = pd.DataFrame({"person_id": ["lennon", "mccartney"], "name": ["John Lennon", "Paul McCartney"]})
    table = song_performers(perf, people, "A")
    assert table.person.tolist() == ["John Lennon", "Paul McCartney"]
    assert table.what.iloc[1] == "lead vocal, bass guitar" and table.sources.iloc[1] == "mb"


def test_instrument_families():
    from beatles_viz.credits import instrument_family
    assert [instrument_family(n) for n in ["electric bass guitar", "bass", "bass drum", "12 string guitar",
                                           "Hammond organ", "sitar", "French horn", "cello", "tape"]] == [
        "Bass", "Bass", "Percussion", "Guitar", "Keyboards", "Indian instruments", "Winds and brass", "Strings",
        "Other"]


def test_instruments_outside_musicians_and_charts():
    from beatles_viz.credits import instruments, outside_musicians
    from beatles_viz.viz import credit_charts as cc
    perf = pd.DataFrame([("A", "lennon", "instrument", "piano; electric guitar", "mb"),
                         ("B", "lennon", "instrument", "guest", "mb"),
                         ("B", "billy_preston", "instrument", "Hammond organ", "mb"),
                         ("B", "george_martin", "producer", "", "mb")],
                        columns=["title", "person_id", "role", "detail", "source_id"])
    inst = instruments(perf)
    assert sorted(inst.instrument) == ["Hammond organ", "electric guitar", "piano"]
    people = pd.DataFrame({"person_id": ["billy_preston"], "name": ["Billy Preston"]})
    assert outside_musicians(perf, people).person.tolist() == ["Billy Preston"]
    songs = pd.DataFrame({"title": ["A", "B"], "phase": ["1962-63", "1962-63"]})
    shares, per_phase = cc.family_shares(inst, songs)
    s = shares.set_index(["person_id", "family"]).share
    assert s[("lennon", "Keyboards")] == 0.5 and per_phase["1962-63"] == 2
    assert cc.member_instruments(shares, per_phase, "Lennon") is not None
    assert cc.member_instruments(shares, per_phase, "Starr") is None


def test_person_id_of_a_name_in_another_script_is_not_empty():
    assert person_id("Μίκης Θεοδωράκης") == "μίκης_θεοδωράκης"
    assert person_id("José Feliciano") == "jos_feliciano"  # Latin names unchanged
