import re
from collections import Counter

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
STOP = set(ENGLISH_STOP_WORDS) | {"ll", "ve", "re", "don't", "i'm", "it's", "i'll", "you're", "i've", "that's",
                                  "can't", "didn't", "won't", "isn't", "he's", "she's", "let's", "we're", "they're"}
# Vocables and proper names stay in length/richness counts but are left out of word rankings.
VOCABLES = {"na", "la", "da", "doo", "dee", "du", "ba", "bom", "sha", "shoo", "dum", "ob", "di", "ho", "ha",
            "naa", "nah", "ah", "ahh", "mm", "mmm", "hm", "uh", "oo", "ooh", "ooo", "woo", "wah", "bop", "tit", "ding", "dong"}
NAMES = {"john", "george", "paul", "ringo", "yoko", "jude", "julia", "sadie", "rita", "lucy", "michelle", "prudence",
         "eleanor", "rigby", "maxwell", "bungalow", "bill", "rocky", "raccoon", "martha", "desmond", "molly", "jojo",
         "loretta", "kite", "mustard", "joe", "jack", "sam", "mary", "maggie", "anna", "sgt", "pepper", "peppers",
         "billy", "shears"}
EXCLUDED = VOCABLES | NAMES


def tokenize(text):
    return WORD.findall(str(text).lower().replace("’", "'"))


def is_content(word):
    return word not in STOP and word not in EXCLUDED and len(word) > 1


def content(words):
    return [w for w in words if is_content(w)]


def content_counter(counter):
    return Counter({w: n for w, n in counter.items() if is_content(w)})


def merge(counters):
    total = Counter()
    for c in counters:
        total.update(c)
    return total
