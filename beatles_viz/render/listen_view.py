"""The official upload with the song's structure under it: a playhead follows the music and a click on a section
jumps to it. Under test on a few songs (SYNCED) before it replaces the plain player. Section starts come from
data/beatles/section_times.csv when measured by ear, otherwise from word counts between the measured ones."""
import base64
import json
from functools import lru_cache

import streamlit.components.v1 as components

from beatles_viz.config import INK, PAPER, ROOT, SECTION_COLORS
from beatles_viz.listen import section_spans, section_times, video_id
from beatles_viz.render.components import listen_row
from beatles_viz.viz.song_charts import has_structure

SYNCED = {"Hey Jude", "Let It Be"}

@lru_cache(maxsize=None)
def _font_face():
    """The iframe is a separate document that does not get the page's fonts: carry IBM Plex Sans inside it."""
    data = base64.b64encode((ROOT / "app/static/fonts/IBMPlexSans-latin-var.woff2").read_bytes()).decode()
    return ("@font-face { font-family: 'IBM Plex Sans'; font-weight: 400 700; "
            f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")


TEMPLATE = """
<style>
__FONT__
body { margin: 0; font-family: 'IBM Plex Sans', system-ui, sans-serif; color: __INK__; }
#player { width: 100%; max-width: 560px; aspect-ratio: 16 / 9; }
#bar { position: relative; height: 26px; margin: 10px 0 6px; cursor: pointer; }
.seg { position: absolute; top: 0; bottom: 0; box-shadow: inset -2px 0 __PAPER__; opacity: .8; }
.seg.on { opacity: 1; box-shadow: inset -2px 0 __PAPER__, inset 0 -4px __INK__; }
#head { position: absolute; top: -4px; bottom: -4px; width: 2px; background: __INK__; left: 0; }
#now { font-size: 15px; font-weight: 600; }
#note { font-size: 12px; opacity: .65; }
</style>
<div id="player"></div>
<div id="bar"></div>
<div id="now">Press play: the structure follows the song. Click a section to jump to it.</div>
<div id="note">__NOTE__</div>
<script>
// start / end: estimated share of the song; at: start in seconds measured by ear, or null
const spans = __SPANS__;
const bar = document.getElementById("bar"), now = document.getElementById("now");
let player, duration = 0;
const segs = spans.map((s, i) => {
  const d = document.createElement("div");
  d.className = "seg"; d.title = (i + 1) + " · " + s.name; d.style.background = s.color;
  d.onclick = () => { if (duration) { player.seekTo(s.t0, true); player.playVideo(); } };
  bar.appendChild(d);
  return d;
});
const head = document.createElement("div"); head.id = "head"; bar.appendChild(head);
function place(share) {  // share of the song -> seconds, through the measured starts
  const anchors = [[0, 0], ...spans.filter(s => s.at !== null).map(s => [s.start, s.at]), [1, duration]];
  for (let k = 1; k < anchors.length; k++) {
    const [f0, t0] = anchors[k - 1], [f1, t1] = anchors[k];
    if (share <= f1) return f1 === f0 ? t1 : t0 + (share - f0) / (f1 - f0) * (t1 - t0);
  }
  return duration;
}
function layout() {
  spans.forEach(s => { s.t0 = place(s.start); });
  spans.forEach((s, i) => { s.t1 = i + 1 < spans.length ? spans[i + 1].t0 : duration; });
  spans.forEach((s, i) => { segs[i].style.left = 100 * s.t0 / duration + "%";
                            segs[i].style.width = 100 * (s.t1 - s.t0) / duration + "%"; });
}
spans.forEach((s, i) => { segs[i].style.left = 100 * s.start + "%"; segs[i].style.width = 100 * (s.end - s.start) + "%"; });
function tick() {
  if (!player || !player.getCurrentTime) return;
  if (!duration) { duration = player.getDuration(); if (!duration) return; layout(); }
  const t = player.getCurrentTime();
  head.style.left = 100 * Math.min(t / duration, 1) + "%";
  const i = Math.max(0, spans.findIndex(s => t < s.t1));
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
    measured = section_times(song.title)
    spans = [dict(name=n, start=a, end=b, color=SECTION_COLORS.get(k, SECTION_COLORS["other"]), at=measured.get(i))
             for i, (n, k, a, b) in enumerate(section_spans(song))]
    note = (f"Start of {len(measured)} of {len(spans)} sections measured by ear, the others estimated from word counts."
            if measured else "Section times are estimated from word counts, not measured.")
    html = TEMPLATE.replace("__FONT__", _font_face()).replace("__INK__", INK).replace("__PAPER__", PAPER).replace("__SPANS__", json.dumps(spans)).replace("__VIDEO__", vid).replace("__NOTE__", note)
    components.html(html, height=420)


def listen_block(song):
    vid = video_id(song.title)
    if song.title in SYNCED and vid and has_structure(song):
        synced_player(song, vid)
        listen_row(song.title)
    else:
        listen_row(song.title, player=True)
