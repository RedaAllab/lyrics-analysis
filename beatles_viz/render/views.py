"""The two views of the song page. Streamlit calls live here; computations stay in viz/ and render/song_view."""
import streamlit as st

from beatles_viz.attribution import resolve_voice
from beatles_viz.corpus import doc_frequencies, neighbors
from beatles_viz.effects import get_effect
from beatles_viz.render.components import chip_row, open_word, plot
from beatles_viz.text.keyness import monroe, prior
from beatles_viz.text.tokenize import content_counter, merge
from beatles_viz.render.song_view import render_song
from beatles_viz.viz import song_charts as charts

READ, ANALYSE = "Read", "Analyse"
DETECTED_NOTE = ("This song has no section tags: verses and choruses were detected from the stanzas that "
                 "come back. On tagged songs this guess matches the tags for 70% of lines.")


def navigation(song, scope, key):
    def go_to(title):
        st.session_state[f"{key}_title"] = title
        st.query_params["song"] = title

    order = st.radio("Browse", ["chronological", "album"], horizontal=True, key=f"{key}_order",
                     format_func=lambda o: "by year" if o == "chronological" else "within the release")
    prev_title, next_title = neighbors(scope, song.title, order)
    cols = st.columns([1, 1, 4])
    cols[0].button("← Previous", disabled=prev_title is None, on_click=go_to, args=(prev_title,),
                   width="stretch", key=f"{key}_prev")
    cols[1].button("Next →", disabled=next_title is None, on_click=go_to, args=(next_title,),
                   width="stretch", key=f"{key}_next")


def effect_settings(song, key):
    st.sidebar.header("Reading")
    effects_on = st.sidebar.toggle("Voice effects", value=True, key=f"{key}_effects")
    motion = st.sidebar.radio("Motion", ["calm", "loop", "off"], key=f"{key}_motion", horizontal=True,
                              format_func={"calm": "Play once", "loop": "Loop", "off": "Off"}.get,
                              help="Play once keeps the effects but lets the text rest after a few seconds.")
    font_size = st.sidebar.slider("Text size", 0.8, 1.6, 1.05, 0.05, key=f"{key}_font")
    params = {}
    with st.sidebar.expander("Effect settings", expanded=False):
        for voice in sorted({resolve_voice(s, song.lead_vocal) for s in song.sections}):
            effect = get_effect(voice)
            if not (effect.ranges or any(str(v).startswith("#") for v in effect.defaults.values())):
                continue
            st.markdown(f"**{voice}**")
            p = {}
            for name, value in effect.defaults.items():
                wkey = f"{key}_{effect.name}_{name}"
                if name in effect.ranges:
                    lo, hi, step = effect.ranges[name]
                    p[name] = st.slider(name, lo, hi, value, step, key=wkey)
                elif str(value).startswith("#"):
                    p[name] = st.color_picker(name, value, key=wkey)
            params[effect.name] = p
    return effects_on, motion, font_size, params


@st.cache_data(show_spinner=False)
def _doc_freq(_corpus):
    return doc_frequencies(_corpus)


@st.cache_data(show_spinner=False, max_entries=64)
def _song_html(_corpus, title, effects_on, frozen, font_size, motion):
    row = _corpus[_corpus.title == title].iloc[0]
    return render_song(row, effects_on, {e: dict(p) for e, p in frozen}, _doc_freq(_corpus), font_size, motion)


def read_view(song, corpus, local, key):
    if not local:
        st.info("Reading the full song needs the local lyrics file (data/beatles/beatles.parquet). "
                "Lyrics are copyrighted, so they are not part of the deployed app: use the Analyse view.")
        return
    effects_on, motion, font_size, params = effect_settings(song, key)
    frozen = tuple(sorted((e, tuple(sorted(p.items()))) for e, p in params.items()))
    st.html(_song_html(corpus, song.title, effects_on, frozen, font_size, motion))
    st.caption("Lyrics: Genius dataset, not proofread. Voice per section: Genius tag when present, otherwise the "
               "song's lead vocal (Wikipedia). Animations are off when the system asks for reduced motion.")


def _show(fig, question, missing="Not enough data for this chart."):
    if fig is None:
        st.markdown(f"**{question}**")
        st.info(missing)
    else:
        fig.update_layout(title=question)  # one title per chart, phrased as the question it answers
        plot(fig)


def analyse_view(song, corpus, local, key):
    _show(charts.structure_timeline(song), "How is the song built?", "No section information for this song.")
    if charts.has_structure(song) and any(song.sec_auto):
        st.caption(DETECTED_NOTE)
    if local:
        left, right = st.columns(2)
        with left:
            _show(charts.self_similarity(song.sections), "Where are the repetitions and returning motifs?")
        with right:
            _show(charts.rolling_richness(song.sections), "Where is the text dense, where is it repetitive?",
                  "The song is shorter than the 30-word window.")
            _show(charts.voice_split(song.sections, song.lead_vocal), "Who sings what?",
                  "The lyrics source names no singer per section for this song.")
    else:
        st.info("Repetition, density and voice charts need the local lyrics file; "
                "this deployment only has word counts and section shapes.")
    left, right = st.columns(2)
    with left:
        _show(charts.keyness(song.bow, corpus[corpus.title != song.title].bow), "Which vocabulary sets it apart?",
              "Too few words for a reliable comparison.")
        a = content_counter(song.bow)
        rest = content_counter(merge(corpus[corpus.title != song.title].bow)) - a
        top = monroe(a, rest, prior(a + rest), min_count=3).query("in_group > 0").word.head(6).tolist()
        if top:
            pick = chip_row("Explore a word", top, f"{key}_word")
            if pick:
                open_word(pick)
    with right:
        _show(charts.pronoun_profile(song, corpus), "From whose point of view does the song speak?")
    period = st.radio("Compare with", ["same period", "all songs"], horizontal=True, key=f"{key}_period")
    _show(charts.corpus_position(song, corpus, song.phase if period == "same period" else None),
          "Is the song typical of its time?")
