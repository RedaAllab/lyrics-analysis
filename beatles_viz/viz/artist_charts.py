"""The Beatles next to the Rolling Stones and Bob Dylan, from the tables scripts/compare_artists.py writes to
analysis/artists/ (numbers, titles and single words: no lyrics, so the public app can show them)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.config import ROOT

ARTISTS_DIR = ROOT / "analysis/artists"
ARTISTS = ["The Beatles", "The Rolling Stones", "Bob Dylan"]
ARTIST_COLORS = {"The Beatles": "#2a6f97", "The Rolling Stones": "#d1495b", "Bob Dylan": "#e09f3e"}
MEASURES = {"mattr": "Vocabulary richness (MATTR)", "tokens": "Words per song", "repetition_score": "Repetition",
            "chorus_share": "Share of words in choruses", "valence": "Mood (−1 dark · +1 bright)",
            "first_singular": "Share of “I / me / my”", "second": "Share of “you / your”"}
TREND_MEASURES = ["mattr", "tokens", "repetition_score", "valence"]


def available():
    return (ARTISTS_DIR / "song_metrics.csv").exists()


def load_tables():
    read = lambda name: pd.read_csv(ARTISTS_DIR / name)
    return {"songs": read("song_metrics.csv"), "words": read("distinctive_words.csv"),
            "years": read("career_years.csv"), "tests": read("pairwise_tests.csv")}


def _layout(fig, title, height=380):
    fig.update_layout(title=title, height=height, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def medians(songs):
    """Median of every measure per artist, artists in display order."""
    return songs.groupby("artist")[list(MEASURES)].median().reindex([a for a in ARTISTS if a in set(songs.artist)])


def profile_box(songs, measure):
    d = songs.dropna(subset=[measure])
    fig = px.box(d, x="artist", y=measure, color="artist", points="outliers", hover_name="title",
                 hover_data={"year": True, "artist": False}, color_discrete_map=ARTIST_COLORS,
                 category_orders={"artist": ARTISTS}, labels={measure: MEASURES[measure], "artist": ""})
    fig.update_layout(showlegend=False)
    return _layout(fig, f"{MEASURES[measure]}, song by song")


def distinctive_bars(words, artist, k=12):
    w = words[words.artist == artist].nlargest(k, "z")
    fig = go.Figure(go.Bar(x=w.z, y=w.word, orientation="h", marker_color=ARTIST_COLORS.get(artist, "#999"),
                           customdata=w.songs, hovertemplate="%{y}: z = %{x:.1f}, in %{customdata} songs<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="z-score vs the other two")
    return _layout(fig, artist, height=60 + 26 * len(w))


def career_lines(years, measure, few=5):
    """Median per year of career, one line per artist; hollow markers for years with fewer than `few` songs."""
    fig = go.Figure()
    for a in [a for a in ARTISTS if a in set(years.artist)]:
        y = years[years.artist == a].sort_values("career_year")
        color = ARTIST_COLORS[a]
        fig.add_scatter(x=y.career_year, y=y[measure], name=a, mode="lines+markers", line_color=color,
                        marker=dict(color=[color if n >= few else "white" for n in y.songs],
                                    line=dict(color=color, width=2), size=9),
                        customdata=y.songs, hovertemplate=f"{a}<br>year %{{x}} · %{{y:.3g}} · %{{customdata}} songs"
                                                          "<extra></extra>")
    fig.update_xaxes(title="year of career (1 = first record)", dtick=1)
    fig.update_yaxes(title=MEASURES[measure])
    return _layout(fig, f"{MEASURES[measure]}, first nine years of each career")


def p_value(tests, measure, a, b):
    row = tests[(tests.metric == measure) & (((tests.a == a) & (tests.b == b)) | ((tests.a == b) & (tests.b == a)))]
    return float(row.p_value.iloc[0]) if len(row) else float("nan")
