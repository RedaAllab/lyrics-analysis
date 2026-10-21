"""Recording credits from MusicBrainz (data under CC0): who sings and plays what on each song's recording, the
producer and engineers, and the writers MusicBrainz attaches to the work. Writes data/credits/mb_recording.csv and
data/credits/mb_credit.csv; scripts/build_credits.py merges them into the credit tables.

For each release of the corpus (column album), the official edition whose tracks match the most corpus titles (then
carry the most relationships) is read among the earliest ones; songs are matched by normalised title. Songs not
found there (singles, Past Masters, archives) are looked up one by one: among the Beatles recordings with that title,
the one with the most relationships. Remasters carry no relationships in MusicBrainz, original editions do. Responses are cached in data/credits/mb_cache/ (git-ignored), so a second run
makes no request. MusicBrainz asks for at most one request per second and a descriptive User-Agent.
Run: python scripts/fetch_credits.py"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from beatles_viz.config import ROOT  # noqa: E402
from beatles_viz.corpus import load_corpus  # noqa: E402

API = "https://musicbrainz.org/ws/2/"
USER_AGENT = "beatles-lyrics-analysis/0.2 (personal research script, non-commercial)"
BEATLES = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
OUT = ROOT / "data/credits"
CACHE = OUT / "mb_cache"
# Corpus album -> MusicBrainz release group titles, when they differ (None: look songs up one by one)
RG_TITLES = {"Past Masters": ["Past Masters, Volume One", "Past Masters, Volume Two"], "Non-album single": None,
             "My Bonnie": None, "Ya Ya": None, "The Beatles' First": None, "The Beatles: Get Back": None,
             "Let It Be: Special Edition": None}
KEEP = {"instrument", "vocal", "performer", "producer", "engineer", "arranger", "orchestrator", "conductor",
        "mix", "recording", "instrument arranger", "vocal arranger", "writer", "composer", "lyricist"}


def get(path, **params):
    params["fmt"] = "json"
    url = API + path + "?" + urllib.parse.urlencode(sorted(params.items()))
    key = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", path + "_" + urllib.parse.urlencode(sorted(params.items())))[:200]
                   + ".json")
    if key.exists():
        return json.loads(key.read_text())
    for attempt in range(6):
        time.sleep(1.5 * (attempt + 1))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            data = json.load(urllib.request.urlopen(req, timeout=30))
            key.write_text(json.dumps(data))
            return data
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503):
                raise
    raise RuntimeError(f"MusicBrainz kept refusing {url}")


def norm(title):
    t = str(title).lower().replace("’", "'").replace("&", "and")
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def release_groups(album):
    titles = RG_TITLES.get(album, [album])
    out = []
    for title in titles or []:
        found = get("release-group", query=f'releasegroup:"{title}" AND arid:{BEATLES}', limit=10)["release-groups"]
        out += [r["id"] for r in found if norm(r["title"]) == norm(title) and r.get("primary-type") == "Album"]
    return out


def best_release(rg_ids, wanted, tries=8):
    """Among the earliest official editions, the one whose tracks match the most wanted titles, then carry the
    most relationships (original pressings do, remasters do not)."""
    best, best_key = None, (-1, -1)
    for rg in rg_ids:
        releases = get("release", **{"release-group": rg, "status": "official", "limit": 100})["releases"]
        for r in sorted(releases, key=lambda r: (r.get("date") or "9999"))[:tries]:
            d = get(f"release/{r['id']}", inc="recordings+recording-level-rels+artist-rels+work-rels+work-level-rels")
            tracks = [t for m in d["media"] for t in m["tracks"]]
            key = (sum(norm(t["title"]) in wanted for t in tracks),
                   sum(len(t["recording"].get("relations", [])) for t in tracks))
            if key > best_key:
                best, best_key = d, key
    return best


def lookup_recording(title, candidates=5):
    """A song outside the album releases: among the Beatles recordings with that title, the one with the most
    relationships, with a release to name it by."""
    found = get("recording", query=f'recording:"{title}" AND arid:{BEATLES} AND status:official', limit=25)
    found = [r for r in found["recordings"] if norm(r["title"]) == norm(title)][:candidates]
    best, best_n = None, -1
    for r in found:
        d = get(f"recording/{r['id']}", inc="artist-rels+work-rels+work-level-rels+releases")
        if len(d.get("relations", [])) > best_n:
            best, best_n = d, len(d.get("relations", []))
    return best


def rows_for(title, album, release, track):
    rec = track["recording"]
    out_rec = {"title": title, "album": album, "recording_mbid": rec["id"], "track_title": track["title"],
               "release_mbid": release["id"], "release_date": release.get("date", ""),
               "release_country": release.get("country", "")}
    credits = []
    for rel in rec.get("relations", []):
        if rel.get("target-type") == "artist" and rel["type"] in KEEP:
            credits.append({"title": title, "level": "recording", "target_mbid": rec["id"],
                            "person": rel["artist"]["name"], "person_mbid": rel["artist"]["id"],
                            "role": rel["type"], "detail": "; ".join(rel.get("attributes", [])),
                            "credited_as": rel.get("target-credit", "")})
        if rel.get("target-type") == "work" and rel["type"] == "performance":
            work = rel["work"]
            for w in work.get("relations", []):
                if w.get("target-type") == "artist" and w["type"] in KEEP:
                    credits.append({"title": title, "level": "work", "target_mbid": work["id"],
                                    "person": w["artist"]["name"], "person_mbid": w["artist"]["id"],
                                    "role": w["type"], "detail": "; ".join(w.get("attributes", [])),
                                    "credited_as": w.get("target-credit", "")})
    return out_rec, credits


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    corpus = load_corpus("auto")
    recordings, credits, missing = [], [], []
    for album, songs in corpus.groupby("album"):
        wanted = {norm(t) for t in songs.title}
        rgs = release_groups(album)
        release = best_release(rgs, wanted) if rgs else None
        tracks = {norm(t["title"]): t for m in (release or {}).get("media", []) for t in m["tracks"]}
        for title in songs.title:
            track = tracks.get(norm(title))
            source = release
            if track is None:  # not on the album release: the song's own recordings
                rec = lookup_recording(title)
                if rec is None:
                    missing.append({"title": title, "album": album, "reason": "no matching recording"})
                    continue
                first = (rec.get("releases") or [{}])[0]
                track, source = {"title": rec["title"], "recording": rec}, {"id": first.get("id", ""),
                                                                            "date": first.get("date", ""),
                                                                            "country": first.get("country", "")}
            rec, cr = rows_for(title, album, source, track)
            recordings.append(rec)
            credits += cr
        print(f"{album}: {len(songs)} songs, release {release['id'] if release else '-'}", file=sys.stderr)
    accessed = date.today().isoformat()
    pd.DataFrame(recordings).assign(accessed=accessed).to_csv(OUT / "mb_recording.csv", index=False)
    pd.DataFrame(credits).drop_duplicates().assign(accessed=accessed).to_csv(OUT / "mb_credit.csv", index=False)
    pd.DataFrame(missing).to_csv(OUT / "mb_missing.csv", index=False)
    print(f"{len(recordings)} recordings matched, {len(missing)} songs missing, {len(credits)} credits",
          file=sys.stderr)


if __name__ == "__main__":
    main()
