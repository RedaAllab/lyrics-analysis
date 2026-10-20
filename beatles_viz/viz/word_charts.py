"""Figures about one word across the corpus."""
import plotly.express as px

from beatles_viz.config import ACCENT, VOICE_COLORS, VOICE_ORDER
from beatles_viz.viz.theme import titled


def usage_over_time(by_year, word):
    fig = px.bar(by_year, x="year", y="per_1000", color_discrete_sequence=[ACCENT],
                 hover_data={"occurrences": True, "songs": True, "total_songs": True},
                 labels={"per_1000": "per 1000 words", "year": "", "songs": "songs using it",
                         "total_songs": "songs that year"})
    return titled(fig, f"How often “{word}” is sung, year by year", height=320)


def usage_by_voice(by_voice, word):
    d = by_voice[by_voice.occurrences > 0]
    fig = px.bar(d, x="voice", y="per_1000", color="voice", color_discrete_map=VOICE_COLORS,
                 category_orders={"voice": VOICE_ORDER}, hover_data={"occurrences": True, "songs": True},
                 labels={"per_1000": "per 1000 words", "voice": ""})
    fig.update_layout(showlegend=False)
    return titled(fig, f"Who sings “{word}”", height=320)


def companion_words(comp, word):
    if comp.empty:
        return None
    fig = px.bar(comp[::-1], x="z", y="word", orientation="h", color_discrete_sequence=["#5fa8d3"],
                 labels={"z": "over-representation (z-score)", "word": ""})
    return titled(fig, f"Words that come with “{word}”", height=max(300, 24 * len(comp)))
