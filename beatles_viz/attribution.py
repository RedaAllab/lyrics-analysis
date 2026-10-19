import re

from beatles_viz.config import MEMBERS, NEUTRAL, SHARED
from beatles_viz.text.sections import parse_members


def voice_from_members(members):
    if not members:
        return NEUTRAL
    return next(iter(members)) if len(members) == 1 else SHARED


def lead_members(lead_vocal):
    # Wikipedia uses surnames only and puts backing vocals in parentheses ("Lennon; (with McCartney)").
    lead = re.sub(r"\(.*?\)", "", str(lead_vocal or ""))
    return frozenset(m for m in MEMBERS if re.search(rf"\b{m}\b", lead))


def lead_voice(lead_vocal):
    return voice_from_members(lead_members(lead_vocal))


def section_members(section, song_lead_vocal):
    return section.singers or lead_members(song_lead_vocal)


def resolve_voice(section, song_lead_vocal):
    if section.singers:
        return voice_from_members(section.singers)
    return lead_voice(song_lead_vocal)
