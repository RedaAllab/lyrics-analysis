"""Pure helpers for scripts/build_artist.py and scripts/compare_artists.py (no duckdb, no matplotlib, so the
tests run in CI with requirements.txt + pytest only)."""
import re
from collections import Counter
from html.parser import HTMLParser

from beatles_viz.text.keyness import monroe, prior

TAGS = re.compile(r"\[[^\]]*\]")
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
# Genius keeps other recordings of a song under titles like "Angie Live 1975", "Heart of Stone Demo",
# "Blowin in the Wind Witmark Demo - 1962" (this dataset drops most brackets) or "Angie (Live)".
VERSION = re.compile(r"\b(live|remix|remixed|remaster|remastered|demo|take|version|mono|stereo|mix|edit|outtake|"
                     r"alternate|alt|acoustic|rehearsal|session|instrumental|bootleg|unplugged|reprise|remake|"
                     r"unreleased|extended|duet|budokan|flashpoint|bremen|gaslight|brandeis|witmark|19[5-9]\d|"
                     r"20[0-2]\d)\b", re.I)
YEAR = re.compile(r"\b(19[5-9]\d|20[0-2]\d)\b")


def slug(name):
    """'The Rolling Stones' -> 'rolling_stones'."""
    s = re.sub(r"^the\s+", "", str(name).strip().lower())
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def norm(title, keep_parens=True):
    """Same normalisation as scripts/build_beatles.py, so titles match across sources."""
    s = str(title).lower() if keep_parens else re.sub(r"\(.*?\)", "", str(title).lower())
    s = re.sub(r"['’‎]|(?<=\d),(?=\d)", "", s.replace("&", "and"))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def match_title(title, official):
    """(official key, is_version) for a Genius title, or (None, False). Exact normalised title first (with and
    without its parenthetical), else the longest official title it starts with when the rest names a version
    ("Angie Live 1975" -> "angie", True)."""
    if norm(title) in official:
        return norm(title), False
    if norm(title, False) in official:  # "Angie (Live)": a version unless the official title has that note too
        return norm(title, False), any(VERSION.search(n) for n in re.findall(r"\((.*?)\)", str(title)))
    t = norm(title)
    words = t.split()
    for n in range(len(words) - 1, 0, -1):
        k, rest = " ".join(words[:n]), " ".join(words[n:])
        if k in official and VERSION.search(rest):
            return k, True
    return None, False


def lyric_words(lyrics):
    return WORD.findall(TAGS.sub(" ", str(lyrics)).lower().replace("’", "'"))


def pick_versions(rows, official, min_words=20):
    """rows: dicts with 'title' and 'lyrics'. One row per official title: the studio title when Genius has it,
    else a Live/Demo/Take version, keeping the longest lyrics with at least min_words words."""
    best = {}
    for r in rows:
        k, version = match_title(r["title"], official)
        n = len(lyric_words(r["lyrics"]))
        if k is None or n < min_words:
            continue
        key = official[k]["title"]
        rank = (not version, n)
        if key not in best or rank > best[key][0]:
            best[key] = (rank, {**r, "official": key, "is_version": version, "n_words": n})
    return [v for _, v in best.values()]


class _Tables(HTMLParser):
    """Collects every <table class="wikitable ..."> as rows of cell texts (rowspans copied down)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.stack, self.skip = [], [], 0
        self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":  # only top-level wikitables, not navboxes or tables nested in cells
            self.stack.append(not self.stack and "wikitable" in (a.get("class") or ""))
            if self.stack == [True]:
                self.tables.append([])
        if self.stack != [True]:
            return
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = {"text": [], "rowspan": int(re.sub(r"\D", "", a.get("rowspan") or "1") or 1),
                         "colspan": int(re.sub(r"\D", "", a.get("colspan") or "1") or 1)}
        elif tag in ("sup", "style", "script"):
            self.skip += 1
        elif tag == "br" and self.cell is not None:
            self.cell["text"].append("; ")

    def handle_endtag(self, tag):
        if tag == "table" and self.stack:
            self.stack.pop()
        if self.stack != [True]:
            return
        if tag in ("sup", "style", "script"):
            self.skip = max(0, self.skip - 1)
        elif tag in ("td", "th") and self.cell is not None:
            text = re.sub(r"\s+", " ", "".join(self.cell["text"])).strip(' ;')
            self.row.append((text, self.cell["rowspan"], self.cell["colspan"]))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.tables[-1].append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None and not self.skip:
            self.cell["text"].append(data)


def wiki_tables(html):
    """Wikitables of a Wikipedia page as lists of rows (lists of strings), rowspan/colspan expanded."""
    p = _Tables()
    p.feed(html)
    out = []
    for raw in p.tables:
        grid, carry = [], {}  # carry: column -> (text, rows left)
        for cells in raw:
            row, col, it = [], 0, iter(cells)
            while True:
                if col in carry:
                    text, left = carry[col]
                    row.append(text)
                    carry = {**carry, col: (text, left - 1)} if left > 1 else {k: v for k, v in carry.items() if k != col}
                    col += 1
                    continue
                c = next(it, None)
                if c is None:
                    break
                text, rs, cs = c
                for _ in range(cs):
                    row.append(text)
                    if rs > 1:
                        carry[col] = (text, rs - 1)
                    col += 1
            grid.append(row)
        out.append(grid)
    return out


def first_year(text):
    m = YEAR.search(str(text))
    return int(m.group(1)) if m else None


def clean_title(text):
    """'"Angie"' / '“Angie” ‡' -> 'Angie'."""
    t = re.sub(r"[\"“”‡†*§¶#]+", " ", str(text))
    return re.sub(r"\s+", " ", t).strip()


def proper_nouns(lyrics_list, min_count=3, share=0.9):
    """Words written with a capital letter in mid-line at least `share` of the time (names, places):
    left out of the distinctive-word rankings, like the Beatles' NAMES list in beatles_viz.text.tokenize."""
    caps, total = Counter(), Counter()
    for lyrics in lyrics_list:
        for line in TAGS.sub(" ", str(lyrics)).replace("’", "'").splitlines():
            for i, w in enumerate(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*", line)):
                if i == 0 or w == "I" or w.startswith("I'"):
                    continue  # the first word of a line is capitalised anyway
                lw = w.lower()
                total[lw] += 1
                caps[lw] += w[0].isupper()
    return {w for w, n in total.items() if n >= min_count and caps[w] / n >= share}


def career_stage(year, debut, length=9, stages=3):
    """'years 1-3' / 'years 4-6' / 'years 7-9' for a year in the first `length` years after the debut, else None.
    length=9 is the Beatles' whole recording career (1962-1970), so the three artists are compared at the same age."""
    k = int(year) - int(debut)
    if not 0 <= k < length:
        return None
    size = -(-length // stages)
    lo = k // size * size
    return f"years {lo + 1}-{min(lo + size, length)}"


def chorus_share(kinds, words):
    """Share of a song's sung words that sit in chorus sections (tagged or detected)."""
    total = sum(words)
    return sum(w for k, w in zip(kinds, words) if k == "chorus") / total if total else float("nan")


def distinctive(counts, doc_counts, others, min_songs=5, k=20, exclude=()):
    """Words most typical of one artist against the others (Monroe log-odds z), kept only when they appear in at
    least `min_songs` of the artist's songs, so one song repeating a word forty times cannot top the list."""
    z = monroe(counts, others, prior(counts + others))
    z = z[~z.word.isin(exclude) & z.word.map(lambda w: doc_counts.get(w, 0) >= min_songs)]
    return z.head(k).assign(songs=lambda d: d.word.map(doc_counts))
