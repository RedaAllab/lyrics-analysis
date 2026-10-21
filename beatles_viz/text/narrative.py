"""How a song tells: who speaks to whom (persons), whether it asks or orders, whether it looks back or ahead, and
whether it names characters. Word lists and line rules, no parser: transparent, but blind to grammar ("love" is
counted as a verb or a noun alike). Read the values as rough markers to compare songs, not as an analysis.

From word counts (work in the public app): third person, past and future markers, named characters.
From lines (local, then exported): questions and orders."""
import re

from beatles_viz.text.tokenize import NAMES, tokenize

THIRD = {"he", "him", "his", "himself", "he's", "she", "her", "hers", "herself", "she's", "they", "them", "their",
         "theirs", "themselves", "they're"}
PAST = {"was", "were", "had", "did", "didn't", "wasn't", "weren't", "said", "went", "came", "saw", "knew", "thought",
        "told", "got", "gave", "made", "took", "felt", "left", "found", "heard", "met", "ran", "sat", "stood", "fell",
        "kept", "lost", "met", "sang", "spoke", "wrote", "woke", "began", "brought", "bought", "caught", "taught",
        "held", "led", "meant", "became", "yesterday", "ago", "used"}
NOT_PAST = {"need", "feed", "indeed", "speed", "bed", "red", "wed", "seed", "bleed", "breed", "shed", "weed",
            "greed", "deed", "proceed", "succeed", "exceed", "tweed", "sled", "fled", "bred"}
FUTURE = {"will", "won't", "gonna", "i'll", "you'll", "we'll", "she'll", "he'll", "they'll", "it'll", "tomorrow",
          "someday", "shall"}
REGULAR_PAST = re.compile(r"^[a-z]{2,}ed$")
# A line that opens on one of these gives an order or a plea ("help", "come", "don't", "let's"...).
IMPERATIVE_OPENERS = {"come", "go", "get", "give", "help", "hold", "take", "let", "let's", "look", "listen", "tell",
                      "say", "please", "don't", "try", "think", "turn", "stop", "wait", "remember", "believe",
                      "close", "open", "show", "send", "bring", "keep", "leave", "put", "call", "write", "sing",
                      "dance", "shake", "twist", "move", "stay", "run", "carry", "imagine"}
# Two name words, one character: counted once.
SAME_CHARACTER = {"rigby": "eleanor", "raccoon": "rocky", "shears": "billy", "bungalow": "bill", "pepper": "sgt",
                  "peppers": "sgt"}
NARRATIVE_COLS = ["third_person", "past", "future", "characters", "questions", "orders"]


def is_past(word):
    return word in PAST or (REGULAR_PAST.match(word) is not None and word not in NOT_PAST)


def word_markers(bow):
    """Shares of the song's words (like the pronoun shares): third person, past markers, future markers;
    characters: named characters (the proper names of tokenize.NAMES, a full name counted once)."""
    total = sum(bow.values()) or 1
    return {"third_person": sum(n for w, n in bow.items() if w in THIRD) / total,
            "past": sum(n for w, n in bow.items() if is_past(w)) / total,
            "future": sum(n for w, n in bow.items() if w in FUTURE) / total,
            "characters": len({SAME_CHARACTER.get(w, w) for w in bow if w in NAMES})}


def line_markers(lines):
    """Shares of sung lines that ask a question (ending in '?') and that open on an order or a plea."""
    lines = [l.strip() for l in lines if tokenize(l)]
    if not lines:
        return {"questions": float("nan"), "orders": float("nan")}
    return {"questions": sum(l.endswith("?") for l in lines) / len(lines),
            "orders": sum(tokenize(l)[0] in IMPERATIVE_OPENERS for l in lines) / len(lines)}
