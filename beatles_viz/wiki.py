"""Personnel sections of Wikipedia articles (wikitext) turned into credit rows, each with the work the article cites
for it ("According to Walter Everett" -> Everett 2001 p. 320). Pure text functions: the download is in
scripts/fetch_wikipedia_credits.py. Only facts are kept (who sings or plays what, on which song), never prose."""
import re

from beatles_viz.credits import instrument_family

SECTION = re.compile(r"^(={2,4})\s*(Personnel|Credits|Personnel and credits|Credits and personnel)\s*\1\s*$",
                     re.M | re.I)
HEADING = re.compile(r"^(={2,6})[^=].*?\1\s*$", re.M)
# {{sfn|Everett|2001|p=320}}, {{harvnb|Lewisohn|1988|pp=18–28}}, {{sfnm|1a1=...}} is rare enough to skip
SFN = re.compile(r"\{\{\s*(?:sfn|harvnb|harvtxt|harv|sfnp)\s*\|([^{}]*)\}\}", re.I)
# a self-closing <ref name="a/b" /> first: its name may hold a slash; then a full <ref ...>...</ref>
REF = re.compile(r"<ref[^>]*/\s*>|<ref(?:\s[^>]*?)?(?<!/)>.*?</ref>", re.S | re.I)
COMMENT = re.compile(r"<!--.*?-->", re.S)
QUOTED = r'"[^"]+"'
# 'on "A", "B" and "C"', '("A" and "B")', '(on "A")', with the titles kept as a group
TRACKS = re.compile(r'\s*\(?\s*(?:on\s+|for\s+)?(' + QUOTED + r'(?:\s*(?:,|and|&)\s*(?:and\s+)?' + QUOTED + r')*)\s*\)?',
                    re.I)
HEADS = {"vocals": "vocal", "vocal": "vocal", "guitars": "guitar", "guitar": "guitar", "pianos": "piano",
         "piano": "piano", "organs": "organ", "organ": "organ", "synthesisers": "synthesiser", "keyboards": "keyboard",
         "basses": "bass"}
NAME = re.compile(r"(?!Uncredited|Unknown|Unidentified|Various)(?:[A-Z][\w.'’-]*|de|van|von|la|da)"
                  r"(?:\s+(?:[A-Z][\w.'’-]*|de|van|von|la|da)){0,4}")
NOT_MUSIC = ("photograph", "illustrat", "design", "artwork", "sleeve", "liner", "cover", "art direction", "notes")


def citation(args):
    """'Everett|2001|p=320' -> 'Everett 2001, p. 320'; 'Guesdon|Margotin|2013|pp=277' -> 'Guesdon, Margotin 2013, pp. 277'."""
    parts = [a.strip() for a in args.split("|")]
    names = [p for p in parts if "=" not in p and not re.fullmatch(r"\d{4}[a-z]?", p)]
    year = next((p for p in parts if re.fullmatch(r"\d{4}[a-z]?", p)), "")
    page = next((p.split("=", 1) for p in parts if re.match(r"(p|pp|loc)\s*=", p)), None)
    out = ", ".join(names) + (f" {year}" if year else "")
    if page:
        out += f", {page[0].strip()}. {page[1].strip()}"
    return out


def citations(text):
    """Every short citation in a piece of wikitext, in order, without duplicates."""
    return list(dict.fromkeys(citation(m.group(1)) for m in SFN.finditer(text)))


def plain(text):
    """Wikitext -> plain text: links to their label, templates such as {{small|...}} to their content."""
    text = COMMENT.sub("", REF.sub("", SFN.sub("", text)))
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    for _ in range(3):
        text = re.sub(r"\{\{\s*sort\s*\|[^|{}]*\|([^{}]*)\}\}", r"\1", text, flags=re.I)
        text = re.sub(r"\{\{\s*(?:small|nowrap|abbr|lang\|[a-z]+)\s*\|([^{}]*?)\}\}", r"\1", text, flags=re.I)
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = text.replace("&nbsp;", " ").replace("''", "").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


MEMBER_IN_TEXT = re.compile(r"Lennon|McCartney|Harrison|Ringo|Starr|the Beatles", re.I)
DASHES = re.compile(r"\{\{\s*(?:snd|ndash|spaced ndash|spnd|mdash|spaced en dash)\s*\}\}|&[nm]dash;", re.I)


def _sections(wikitext):
    out = []
    for m in SECTION.finditer(wikitext):
        level = len(m.group(1))
        end = next((h.start() for h in HEADING.finditer(wikitext, m.end()) if len(h.group(1)) <= level),
                   len(wikitext))
        parent = next((h.group(0) for h in reversed(list(HEADING.finditer(wikitext, 0, m.start())))
                       if len(h.group(1)) < level), "")
        out.append((parent, wikitext[m.end():end]))
    return out


def personnel_section(wikitext):
    """The text of the Personnel (or Credits) section about the Beatles' recording, without its heading; '' when
    there is none. A cover's article can list the original artist's personnel first: the section kept is the first
    under a heading naming the Beatles, else the first that names a member."""
    found = _sections(COMMENT.sub("", wikitext))
    for parent, text in found:
        if re.search(r"Beatles", parent) and MEMBER_IN_TEXT.search(text):
            return text
    return next((text for _, text in found if MEMBER_IN_TEXT.search(text)), "")


# which modifiers can take which shared head noun: 'bass, backing vocals' is a bass and a backing vocal
MODIFIERS = {
    "vocal": {"lead", "harmony", "backing", "background", "double-tracked", "falsetto", "spoken", "additional", "solo"},
    "guitar": {"lead", "rhythm", "acoustic", "electric", "bass", "slide", "12-string", "twelve-string", "classical",
               "steel", "fuzz", "jazz", "electric rhythm", "additional", "solo"},
    "piano": {"grand", "upright", "acoustic", "electric", "tack", "honky-tonk", "additional"},
    "organ": {"hammond", "lowrey", "pipe", "electric", "additional"},
}


def _with_head(items):
    """'lead', 'harmony', 'backing vocals' -> 'lead vocal', 'harmony vocal', 'backing vocal': an item that is only a
    modifier takes the head noun of the nearest following item ('rhythm and acoustic guitars')."""
    out, head = [], None
    for item in reversed(items):
        words = item.split()
        h = HEADS.get(words[-1].lower()) if words else None
        if h:
            head = h
            out.append(" ".join(words[:-1] + [h]))
        elif head and item.lower() in MODIFIERS.get(head, ()):
            out.append(f"{item} {head}")
        else:
            out.append(item)
            head = None
    return out[::-1]


def split_roles(text):
    """'lead, harmony and backing vocals; rhythm guitar' -> roles in order, each with the songs it is limited to.
    Returns [(role, [song, ...])]; an empty song list means the role holds for the whole page (song or album)."""
    tracks = []

    def keep(m):
        tracks.append(re.findall(r'"([^"]+)"', m.group(1)))
        return f" @{len(tracks) - 1} "

    text = TRACKS.sub(keep, plain(text))
    out = []
    for clause in re.split(r";", text):
        items = [i.strip(" .:") for i in re.split(r",|\band\b|&|/", clause)]
        merged = []  # a bare '@n' item (titles after a comma) belongs to the item before it
        for i in items:
            if re.fullmatch(r"@\d+", i) and merged:
                merged[-1] += " " + i
            elif i:
                merged.append(i)
        roles = []
        for i in merged:
            ids = [int(n) for n in re.findall(r"@(\d+)", i)]
            name = re.sub(r"\(.*?(\)|$)", "", re.sub(r"@\d+", "", i)).strip(" ,.:()")
            if name:
                roles.append((name, [t for n in ids for t in tracks[n]]))
        names = _with_head([r for r, _ in roles])
        out += [(n, songs) for n, (_, songs) in zip(names, roles)]
    return out


def classify(role):
    """A free-text role -> (kind, family): lead_vocal, backing_vocal, vocal, vocal_effect (spoken words, vocal
    percussion), instrument, producer, engineer, arranger or other; family is the instrument family for instruments."""
    r = role.lower().replace("hand clap", "handclap")
    if any(k in r for k in NOT_MUSIC):
        return "other", ""
    if "vocal" in r or "singing" in r or r in {"vocals", "voice"}:
        if any(k in r for k in ("percussion", "spoken", "grunt", "shout", "vocalis", "vocaliz", "effect", "noise")):
            return "vocal_effect", ""
        if "lead" in r:
            return "lead_vocal", ""
        if any(k in r for k in ("harmony", "backing", "background", "chorus", "choir", "bass vocal", "falsetto")):
            return "backing_vocal", ""
        if "double-tracked" in r or "double tracked" in r or "solo" in r:
            return "lead_vocal", ""
        return "vocal", ""
    if "produc" in r:
        return "producer", ""
    if "engineer" in r or "mix" in r or "recorded" in r or "tape op" in r:
        return "engineer", ""
    if "arrange" in r or "orchestra" in r or "conduct" in r or "score" in r:
        return "arranger", ""
    if any(k in r for k in ("brushes", "chime", "claps")):
        return "instrument", "Percussion"
    family = instrument_family(r)
    if family != "Other" or any(k in r for k in ("bass", "guitar", "sound effect", "tape loop", "synth", "bell")):
        return "instrument", family if family != "Other" else ("Bass" if "bass" in r else "Other")
    return "other", ""


def personnel(section):
    """Rows from a Personnel section: person, role text, kind, family, songs (album pages), the citations of the
    section's opening sentence ('According to ... except where noted') and those found on the line itself."""
    section = REF.sub(lambda m: m.group(0).replace("\n", " "), DASHES.sub(" – ", COMMENT.sub("", section)))
    intro = section.split("\n*", 1)[0]
    page_cited = citations(intro) or citations(re.sub(r"\n\*.*", "", section))
    rows = []
    group = ""
    for line in section.split("\n"):
        s = line.strip()
        if re.match(r"^('''|;|={3,})", s):
            group = plain(s.strip(";=")).strip(":")
            continue
        if not s.startswith("*"):
            continue
        body = s.lstrip("*").strip()
        line_cited = citations(body)
        # 'Name – roles' (en dash, em dash, hyphen surrounded by spaces, or colon)
        parts = re.split(r"\s*(?:&nbsp;|\s)[–—-]\s+|\s*[–—]\s*|:\s+", body, maxsplit=1)
        if len(parts) < 2:
            continue
        people = [n.strip(" ,.") for n in re.split(r",|\band\b", plain(parts[0]))]
        if not all(NAME.fullmatch(n) for n in people):
            continue  # a sentence, 'Uncredited', 'Unknown': no one identified
        for person in people:
            for role, songs in split_roles(parts[1]):
                kind, family = classify(role)
                rows.append({"group": group, "person": person, "role_text": role, "kind": kind, "family": family,
                             "songs": songs, "cited": "; ".join(page_cited), "line_cited": "; ".join(line_cited)})
    return rows


CITE = re.compile(r"\{\{\s*cite\s+\w+([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}", re.I)
NAMED_REF = re.compile(r"<ref\s+name\s*=\s*(?:\"([^\"]+)\"|([^\s>/]+))\s*(/\s*>|>(.*?)</ref>)", re.S | re.I)
WRITING = re.compile(r"\b(wr[io]te|written|writing|compos\w*|lyric\w*|middle[ -]eight|bridge|melod\w*|credit\w*|"
                     r"contribut\w*|came up with|co-wr\w*|authorship|finish\w*|per ?cent|50[–-]50|verse)\b", re.I)
MEMBER_NAME = re.compile(r"\b(Lennon|McCartney|Harrison|Starr|Ringo|John|Paul|George)\b")
SKIP_SECTIONS = re.compile(r"personnel|credits|chart|certification|release history|cover|track listing|"
                           r"references|notes|sources|bibliography|external links|see also|reception|legacy|"
                           r"accolades|live performance|other versions", re.I)


def cite_template(body):
    """'{{cite book |last=Everett |year=2001 |page=320 ...}}' -> 'Everett 2001, p. 320'."""
    field = lambda *names: next((m.group(1).strip() for n in names
                                 for m in [re.search(rf"\|\s*{n}\s*=\s*([^|]*)", body)] if m and m.group(1).strip()),
                                "")
    who = field("last1", "last", "author1", "author", "editor-last", "work", "publisher", "website", "magazine",
                "newspaper")
    year = re.search(r"\d{4}", field("year", "date") or "")
    page = field("page", "pages", "at")
    out = plain(who) + (f" {year.group(0)}" if year else "")
    title = plain(field("title"))[:80]
    if title:
        out += f", {title}"
    return out + (f", p. {page}" if page else "")


def reference_map(wikitext):
    """Named references defined anywhere in the article: name -> short citation (reused with <ref name=x />)."""
    out = {}
    for m in NAMED_REF.finditer(wikitext):
        if m.group(4):
            body = m.group(4)
            found = citations(body) or [cite_template(c.group(1)) for c in CITE.finditer(body)]
            out[(m.group(1) or m.group(2)).strip()] = "; ".join(found) or plain(body)[:100]
    return out


def _mark_citations(text, refs):
    def ref(m):
        named = re.match(r"<ref\s+name\s*=\s*(?:\"([^\"]+)\"|([^\s>/]+))\s*/\s*>", m.group(0), re.I)
        if named:
            c = refs.get((named.group(1) or named.group(2)).strip(), "")
        else:
            body = re.sub(r"^<ref[^>]*>|</ref>$", "", m.group(0))
            c = "; ".join(citations(body) or [cite_template(x.group(1)) for x in CITE.finditer(body)])
        return f" ⟦{c}⟧" if c else ""
    text = REF.sub(ref, text)
    return SFN.sub(lambda m: f" ⟦{citation(m.group(1))}⟧", text)


def cited_sentences(wikitext, pattern=WRITING, names=MEMBER_NAME):
    """Sentences of an article that mention a member and match pattern (writing, composing...), each with the
    citations that follow it and its section. For reading by a person or a model, not for publication."""
    refs = reference_map(wikitext)
    sections = re.split(r"\n(={2,6}[^=\n].*?={2,6})\s*\n", "\n== Lead ==\n" + wikitext)
    rows, name = [], "Lead"
    for part in sections[1:]:
        if re.fullmatch(r"={2,6}[^=\n].*?={2,6}", part.strip()):
            name = part.strip("= ").strip()
            continue
        if SKIP_SECTIONS.search(name):
            continue
        body = re.sub(r"\{\{\s*(?:Infobox|quote|blockquote|cquote|poem)[^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*\}\}", " ",
                      part, flags=re.I | re.S)
        body = "\n".join(l for l in body.split("\n") if not l.startswith(("{|", "|", "!", "*", "[[File", "[[Image")))
        text = plain(_mark_citations(body, refs).replace("⟦", "\x00").replace("⟧", "\x01"))
        text = text.replace("\x00", "⟦").replace("\x01", "⟧")
        start = 0
        for m in re.finditer(r"[.!?][\"”']?((?:\s*⟦[^⟧]*⟧)*)(?:\s+(?=[A-Z\"“(])|\s*$)", text):
            sentence = text[start:m.end()].strip()
            start = m.end()
            cited = re.findall(r"⟦([^⟧]*)⟧", sentence)
            words = re.sub(r"\s*⟦[^⟧]*⟧", "", sentence).strip()
            if pattern.search(words) and names.search(words):
                rows.append({"section": name, "sentence": words, "cited": "; ".join(dict.fromkeys(cited))})
    return rows
