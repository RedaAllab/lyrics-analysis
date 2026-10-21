"""Figures about who plays what (recording credits, beatles_viz/credits.py). No lyric text in any figure."""
import plotly.express as px
import plotly.graph_objects as go

from beatles_viz.config import MEMBERS, PHASE_ORDER, VOICE_COLORS, VOICE_ORDER
from beatles_viz.credits import FAMILIES
from beatles_viz.viz.theme import titled

FAMILY_ORDER = [f for f, _ in FAMILIES] + ["Other"]


def family_shares(inst, songs):
    """Per member, period and instrument family: share of the period's credited songs where the member plays it.
    inst: instruments(); songs: title, phase of the songs to count (those with recording credits)."""
    songs = songs.dropna(subset=["phase"])
    per_phase = songs.groupby("phase").title.nunique()
    d = inst.merge(songs[["title", "phase"]], on="title")
    d = d[d.person_id.isin([m.lower() for m in MEMBERS])]
    g = d.groupby(["person_id", "phase", "family"]).title.nunique().rename("songs").reset_index()
    g["share"] = g.songs / g.phase.map(per_phase)
    return g, per_phase


def member_instruments(shares, per_phase, member):
    d = shares[shares.person_id == member.lower()]
    z = d.pivot(index="family", columns="phase", values="share").reindex(
        index=[f for f in FAMILY_ORDER if f in set(d.family)], columns=[p for p in PHASE_ORDER if p in per_phase])
    if z.empty:
        return None
    fig = go.Figure(go.Heatmap(z=z.fillna(0).values, x=[f"{p} ({per_phase[p]})" for p in z.columns],
                               y=z.index.tolist(), colorscale=[[0, "#ffffff"], [1, VOICE_COLORS[member]]], zmin=0,
                               zmax=1, text=[[f"{v:.0%}" if v == v else "" for v in row] for row in z.values],
                               texttemplate="%{text}", colorbar=dict(title="songs", tickformat=".0%"),
                               hovertemplate="%{y} · %{x}<br>on %{z:.0%} of the songs<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    return titled(fig, f"What {member} plays, period by period", height=380)


def credit_voice_figure(corpus, phase=None):
    """Original compositions: songs per official writing credit, split by lead voice (one period or all)."""
    d = corpus[corpus.is_original].dropna(subset=["phase"])
    if phase:
        d = d[d.phase == phase]
    g = d.groupby(["writer_credit", "voice"]).size().rename("songs").reset_index()
    order = d.writer_credit.value_counts().index.tolist()
    fig = px.bar(g, x="songs", y="writer_credit", color="voice", orientation="h", color_discrete_map=VOICE_COLORS,
                 category_orders={"writer_credit": order, "voice": VOICE_ORDER},
                 labels={"songs": "songs", "writer_credit": "", "voice": "lead voice"})
    return titled(fig, f"Official credit and lead voice, {phase or 'all periods'}", height=120 + 34 * len(order))
