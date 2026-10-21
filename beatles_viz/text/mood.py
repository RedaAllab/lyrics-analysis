"""Mood and themes from word counts alone, so they work in the public app.

Mood: VADER's word valences (Hutto & Gilbert 2014, MIT licence), averaged over the song's words that the lexicon
knows. Without the sentences there is no negation or irony: "don't cry" counts as sad. Interjections and words
that are mostly grammatical in lyrics ("like a", "kind of", "hold your hand") are left out.
Mood in context (valence_ctx, local only, then exported): VADER's sentence rules line by line, so negation,
intensifiers and "but" count ("don't cry" is no longer sad). Same lexicon, same neutral words left out.
Themes: short hand-made word lists, counted per 1,000 words."""
from functools import lru_cache
from importlib.resources import files

NEUTRAL_WORDS = {"yeah", "yes", "no", "like", "well", "please", "woo", "hand", "kind", "help", "ok", "okay", "pretty"}
MIN_MOOD_WORDS = 5  # fewer lexicon words than this: no mood score
MIN_MOOD_LINES = 3  # fewer lines carrying a mood than this: no mood-in-context score

THEMES = {
    "Love": {"love", "loves", "loved", "loving", "lover", "lovers", "kiss", "kissed", "kisses", "kissing", "darling",
             "heart", "hearts", "romance", "sweetheart", "honey"},
    "Time": {"time", "times", "day", "days", "night", "nights", "tomorrow", "yesterday", "today", "tonight",
             "morning", "evening", "year", "years", "forever", "hour", "hours", "minute", "minutes", "older", "young"},
    "Nature": {"sun", "sunshine", "sky", "skies", "rain", "sea", "ocean", "tree", "trees", "flower", "flowers",
               "garden", "field", "fields", "star", "stars", "moon", "wind", "river", "snow", "bird", "birds",
               "blackbird", "water", "mountain", "mountains", "earth", "grass", "octopus", "submarine"},
    "Places and travel": {"road", "roads", "ride", "ticket", "train", "car", "cars", "drive", "driving", "street",
                          "streets", "town", "city", "travel", "place", "places", "lane", "airport", "fly", "flying",
                          "plane", "ship", "boat", "away"},
    "Money and work": {"money", "buy", "bought", "pay", "paid", "rich", "poor", "work", "working", "job", "tax",
                       "taxman", "sell", "sold", "cash", "pounds", "dollars", "diamond", "diamonds", "bank"},
    "Mind and dreams": {"mind", "minds", "dream", "dreams", "dreaming", "dreamer", "think", "thinking", "thought",
                        "sleep", "sleeping", "asleep", "believe", "imagine", "wonder", "wondering", "real",
                        "nowhere", "consciousness", "meditation"},
    "Music and dance": {"dance", "dancing", "danced", "sing", "singing", "sang", "song", "songs", "music", "band",
                        "rock", "roll", "twist", "shout", "guitar", "play", "playing", "tune", "melody", "drum"},
    "World and people": {"world", "people", "peace", "revolution", "everybody", "everyone", "nobody", "change",
                         "war", "free", "freedom", "society", "nation", "man", "men", "brother", "brothers"},
    "Family and friends": {"friend", "friends", "mother", "father", "mama", "mummy", "daddy", "family", "sister",
                           "children", "child", "home", "son", "daughter", "wife", "husband", "aunt", "uncle"},
}


@lru_cache(maxsize=1)
def lexicon():
    text = files("vaderSentiment").joinpath("vader_lexicon.txt").read_text(encoding="utf-8")
    out = {}
    for line in text.splitlines():
        word, value, *_ = line.split("\t")
        if word.isalpha() and word not in NEUTRAL_WORDS:
            out[word] = float(value)
    return out


def mood(bow):
    """valence: mean word valence scaled to -1..1; positive / negative: share of all words; mood_words: count."""
    lex = lexicon()
    total = sum(bow.values()) or 1
    hits = {w: n for w, n in bow.items() if w in lex}
    n = sum(hits.values())
    pos = sum(c for w, c in hits.items() if lex[w] > 0)
    neg = sum(c for w, c in hits.items() if lex[w] < 0)
    value = sum(c * lex[w] for w, c in hits.items()) / n / 4 if n >= MIN_MOOD_WORDS else float("nan")
    return {"valence": value, "positive": pos / total, "negative": neg / total, "mood_words": n}


@lru_cache(maxsize=1)
def analyzer():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    a = SentimentIntensityAnalyzer()
    for w in NEUTRAL_WORDS:
        a.lexicon.pop(w, None)
    return a


def line_mood(lines):
    """valence_ctx: mean VADER compound score (-1..1) of the lines that carry a mood; mood_lines: their count."""
    scores = [analyzer().polarity_scores(line)["compound"] for line in lines if line.strip()]
    scores = [x for x in scores if x != 0]
    value = sum(scores) / len(scores) if len(scores) >= MIN_MOOD_LINES else float("nan")
    return {"valence_ctx": value, "mood_lines": len(scores)}


def mood_words(bow, k=6):
    """The words that push the song's mood most, positive then negative: [(word, count * valence)]."""
    lex = lexicon()
    scored = sorted(((w, n * lex[w]) for w, n in bow.items() if w in lex), key=lambda x: x[1])
    return [x for x in scored[::-1][:k] if x[1] > 0], [x for x in scored[:k] if x[1] < 0]


def themes(bow):
    """Theme words per 1,000 words, one value per theme."""
    total = sum(bow.values()) or 1
    return {t: 1000 * sum(bow.get(w, 0) for w in words) / total for t, words in THEMES.items()}
