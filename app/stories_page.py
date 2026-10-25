"""Guided stories: one finding per screen. Statistics only, works without the lyrics."""
import streamlit as st

from beatles_viz.data.loader import data_source
from beatles_viz.render.components import cached_corpus, open_song, open_word, plot
from beatles_viz.render.identity import kicker
from beatles_viz.render.share_card import story_share_block
from beatles_viz.stories import DEFAULT_SOURCE, SOURCES, build_stories


@st.cache_data(show_spinner="Reading the catalogue...")
def cached_stories(source):
    return build_stories(cached_corpus(source))


stories = cached_stories(data_source())
n = len(stories)
try:
    step = min(max(int(st.query_params.get("story", 1)), 1), n)
except ValueError:
    step = 1


def go(to):
    st.query_params["story"] = to


story = stories[step - 1]
kicker(f"Story {step} of {n}")
st.markdown(f"## {story.headline}")
st.progress(step / n)
st.markdown(story.text)
if story.figure is not None:
    story.figure.update_layout(title=None)
    plot(story.figure)

links = story.links
if links:
    cols = st.columns(len(links))
    for i, (col, (kind, target)) in enumerate(zip(cols, links)):
        label = {"word": f"Open “{target}”", "song": f"Open {target}", "page": f"Open the {target} page"}[kind]
        if col.button(label, key=f"story_link_{step}_{i}", icon=":material/arrow_outward:", width="stretch"):
            if kind == "page":
                st.switch_page(f"{target}_page.py")
            (open_word if kind == "word" else open_song)(target)

story_share_block(story, step, n, source=SOURCES.get(story.key, "Original compositions, 1962-1970").rstrip("."))

st.divider()
prev, middle, nxt = st.columns([1, 2, 1])
prev.button("Previous", disabled=step == 1, on_click=go, args=(step - 1,), icon=":material/arrow_back:",
            width="stretch", key="story_prev")
if step < n:
    nxt.button("Next", on_click=go, args=(step + 1,), type="primary", icon=":material/arrow_forward:",
               width="stretch", key="story_next")
else:
    middle.markdown("**Keep exploring:** the albums one by one, or the four voices side by side.")
    if nxt.button("Albums", icon=":material/album:", width="stretch", key="story_albums"):
        st.switch_page("album_page.py")
    if nxt.button("Voices", icon=":material/record_voice_over:", width="stretch", key="story_voices"):
        st.switch_page("voice_page.py")
st.caption(f"{SOURCES.get(story.key, DEFAULT_SOURCE)} Lyrics: Genius dataset, not proofread.")
