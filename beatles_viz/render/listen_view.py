"""The official upload with the song's structure under it: a playhead follows the music and a click on a section
jumps to it. Under test on a few songs (SYNCED) before it replaces the plain player."""
import json

import streamlit.components.v1 as components

from beatles_viz.config import SECTION_COLORS
from beatles_viz.listen import section_spans, video_id
from beatles_viz.render.components import listen_row
from beatles_viz.viz.song_charts import has_structure

SYNCED = {"Hey Jude"}

TEMPLATE = """
<style>
body { margin: 0; font-family: 'Source Sans Pro', system-ui, sans-serif; color: #ece6dc; }
#player { width: 100%; max-width: 560px; aspect-ratio: 16 / 9; }
#bar { position: relative; height: 26px; margin: 10px 0 6px; cursor: pointer; }
.seg { position: absolute; top: 0; bottom: 0; box-shadow: inset -2px 0 #12151f; opacity: .55; }
.seg.on { opacity: 1; }
#head { position: absolute; top: -4px; bottom: -4px; width: 2px; background: #ece6dc; left: 0; }
#now { font-size: 15px; font-weight: 600; }
#note { font-size: 12px; opacity: .65; }
</style>
<div id="player"></div>
<div id="bar"></div>
<div id="now">Press play: the structure follows the song. Click a section to jump to it.</div>
<div id="note">Section times are estimated from word counts, not measured.</div>
<script>
const spans = __SPANS__;
const bar = document.getElementById("bar"), now = document.getElementById("now");
let player, duration = 0;
const segs = spans.map(s => {
  const d = document.createElement("div");
  d.className = "seg"; d.title = s.name; d.style.background = s.color;
  d.style.left = 100 * s.start + "%"; d.style.width = 100 * (s.end - s.start) + "%";
  d.onclick = () => { if (duration) { player.seekTo(s.start * duration, true); player.playVideo(); } };
  bar.appendChild(d);
  return d;
});
const head = document.createElement("div"); head.id = "head"; bar.appendChild(head);
function tick() {
  if (!player || !player.getCurrentTime) return;
  duration = duration || player.getDuration();
  if (!duration) return;
  const f = player.getCurrentTime() / duration;
  head.style.left = 100 * Math.min(f, 1) + "%";
  const i = Math.max(0, spans.findIndex(s => f < s.end));
  segs.forEach((d, j) => d.classList.toggle("on", j === i));
  now.textContent = "Now: " + spans[i].name;
}
function onYouTubeIframeAPIReady() {
  player = new YT.Player("player", { videoId: "__VIDEO__", host: "https://www.youtube-nocookie.com",
                                     width: "100%", height: "100%", playerVars: { rel: 0 } });
  setInterval(tick, 250);
}
</script>
<script src="https://www.youtube.com/iframe_api"></script>
"""


def synced_player(song, vid):
    spans = [dict(name=n, start=a, end=b, color=SECTION_COLORS.get(k, "#999999")) for n, k, a, b in section_spans(song)]
    components.html(TEMPLATE.replace("__SPANS__", json.dumps(spans)).replace("__VIDEO__", vid), height=420)


def listen_block(song):
    vid = video_id(song.title)
    if song.title in SYNCED and vid and has_structure(song):
        synced_player(song, vid)
        listen_row(song.title)
    else:
        listen_row(song.title, player=True)
