# Strings copied from the official song list (metadata, not lyrics).
import pytest

from beatles_viz.attribution import lead_members
from beatles_viz.credits import is_archival, release_note, vocal_credit, writer_credit

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
