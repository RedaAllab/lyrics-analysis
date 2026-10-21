"""'Who sings?': the words that set one song apart from the others (never its lyrics) and the lead voice to guess."""
from collections import namedtuple

from beatles_viz.config import MEMBERS
from beatles_viz.text.keyness import song_keyness
from beatles_viz.text.tokenize import tokenize

Question = namedtuple("Question", "title year voice words")
MIN_WORDS = 4  # fewer telling words than this makes a poor question
ATTEMPTS = 40


def pool(corpus):
    """Songs with one of the four lead voices; shared and uncredited songs have no single answer."""
    return corpus[corpus.voice.isin(MEMBERS)]


def question(corpus, rng, asked=(), k=6):
    """A random song not yet asked, with its k most telling words, or None when every song has been asked.
    Words from the title are left out: they would give the song away."""
    songs = pool(corpus)
    songs = songs[~songs.title.isin(asked)]
    for _ in range(ATTEMPTS):
        if songs.empty:
            return None
        song = songs.iloc[rng.randrange(len(songs))]
        rest = corpus[corpus.title != song.title].bow.tolist()
        in_title = set(tokenize(song.title))
        keyness = song_keyness(song.bow, rest).sort_values("z", ascending=False)
        words = [w for w in keyness[keyness.z > 0].word if w not in in_title][:k]
        if len(words) >= MIN_WORDS:
            return Question(song.title, int(song.year), song.voice, words)
        songs = songs[songs.title != song.title]
    return None
