"""Article Reels v2 (16 Oct 2026): same copy, new look.

Jess's direction for all calendar videos:
- Footage background (Motion Array) instead of still plates or photos.
- Slower pages (about 5 s each) and text on a solid brand-colour panel.
- Bigger, bolder type.
- Colours rotate terracotta, green (sage), pink (rose) by date.
- Music: FoundHer's own OpenArt tracks, mixed into the video.

The words in each Reel are unchanged from the approved specs; this script only restyles them.

Usage: python3 tools/reels/build_articles_v2.py [--render] [--only 2026-10-20 ...]
Media (git-ignored) lives in tools/reels/media/.
"""
import json
from datetime import datetime, timezone
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/reels"))
import render_reel as rr  # noqa: E402

MEDIA = "tools/reels/media/"
SPECS = ROOT / "tools/reels/specs"
THEMES = ["terracotta", "sage", "rose"]
TINT = {"terracotta": 0.45, "sage": 0.5, "rose": 0.5}
SCENE = 5.0
END = 6.0

MUSIC = {
    "fall-winter": "FoundHer fall and winter background music (made in OpenArt for FoundHer)",
    "gentle": "FoundHer gentle background music (made in OpenArt for FoundHer)",
    "mellow": "FoundHer mellow background music (made in OpenArt for FoundHer)",
    "openart-1": "FoundHer upbeat background music (made in OpenArt for FoundHer)",
}

# date: (music, clip file, crop [x, y, w, h] on 1920x1080, speed, loop, credit)
C = {
    "2026-10-17": ("fall-winter", "motionarray-2732492-autumn-picnic.mp4", [1040, 0, 608, 1080], 0.8, False, "Young Friends Enjoying Picnic In Autumn Forest (2732492)"),
    "2026-10-20": ("openart-1", "motionarray-3648780.mp4", [656, 0, 608, 1080], 0.8, True, "Middle Aged Women Clinking Glasses And Dancing (3648780)"),
    "2026-10-24": ("gentle", "motionarray-756638.mp4", [656, 0, 608, 1080], 0.55, "bounce", "Women Laughing On Terrace Party (756638)"),
    "2026-10-27": ("mellow", "motionarray-896032.mp4", [656, 0, 608, 1080], 0.8, True, "Women Talking In Coffee Shop (896032)"),
    "2026-10-31": ("openart-1", "motionarray-4096518.mp4", [656, 0, 608, 1080], 0.8, True, "Group Of Women Having Fun Outdoor (4096518)"),
    "2026-11-03": ("mellow", "motionarray-2405844.mp4", [656, 0, 608, 1080], 0.8, True, "Women Laughing Talking In Street Cafe (2405844)"),
    "2026-11-07": ("openart-1", "motionarray-2539584.mp4", [656, 0, 608, 1080], 0.8, True, "Group Of Healthy Mature Women Running Together Outdoors (2539584)"),
    "2026-11-10": ("fall-winter", "motionarray-3230357.mp4", [656, 0, 608, 1080], 0.8, True, "Friends Gathering For Dinner (3230357)"),
    "2026-11-14": ("mellow", "motionarray-4256316.mp4", [656, 0, 608, 1080], 0.8, True, "Friends Brunch (4256316)"),
    "2026-11-17": ("openart-1", "motionarray-1944961.mp4", [656, 0, 608, 1080], 0.8, True, "Women's Book Club Gathering (1944961)"),
    "2026-11-21": ("fall-winter", "motionarray-1659422.mp4", [656, 0, 608, 1080], 0.8, True, "Friends Playing In Snow (1659422)"),
    "2026-11-24": ("openart-1", "motionarray-1904902.mp4", [656, 0, 608, 1080], 0.8, True, "Women Volunteer At Non-Profit Food Drive (1904902)"),
    "2026-11-28": ("fall-winter", "motionarray-682587.mp4", [656, 0, 608, 1080], 0.8, True, "Women In The Christmas Market (682587)"),
    "2026-12-01": ("fall-winter", "motionarray-2082278.mp4", [656, 0, 608, 1080], 0.8, True, "Friends Christmas Lights Decoration (2082278)"),
    "2026-12-05": ("fall-winter", "motionarray-3797189.mp4", [656, 0, 608, 1080], 0.8, True, "Woman Skiing In Snow Mountains (3797189)"),
    "2026-12-08": ("mellow", "motionarray-1421055.mp4", [656, 0, 608, 1080], 0.8, True, "Women On A Video Call (1421055)"),
    "2026-12-12": ("gentle", "motionarray-3038164.mp4", [656, 0, 608, 1080], 0.8, True, "Woman At Winter Window (3038164)"),
    "2026-12-15": ("fall-winter", "motionarray-1109814.mp4", [656, 0, 608, 1080], 0.8, True, "Woman On Hot Springs (1109814)"),
    "2026-12-19": ("gentle", "motionarray-1637311.mp4", [656, 0, 608, 1080], 0.8, True, "Woman Comforting Distraught Friend (1637311)"),
    "2026-12-22": ("gentle", "motionarray-2616181.mp4", [656, 0, 608, 1080], 0.8, True, "Woman Reading Book In Cafe (2616181)"),
    "2026-12-26": ("fall-winter", "motionarray-834531.mp4", [656, 0, 608, 1080], 0.8, True, "Women On Road Trip Looking At Map (834531)"),
    "2026-12-29": ("gentle", "motionarray-1427133.mp4", [656, 0, 608, 1080], 0.8, True, "Woman Walks In Winter Mountain Forest (1427133)"),
}


def fit(lines, want):
    d = rr.ImageDraw.Draw(rr.layer(10))
    size = want
    while size > 60:
        if all(d.textlength(t, font=rr.font("serif-i" if i else "serif", size, "Medium Italic" if i else "Regular")) <= rr.TEXT_W
               for t, i in lines):
            return size
        size -= 2
    return size


def restyle_item(it, first):
    it = dict(it)
    k = it["kind"]
    if k == "headline":
        want = round(it.get("size", 90) * (1.22 if first else 1.18))
        it["size"] = fit(it["lines"], min(want, 120))
    elif k == "body":
        it["size"] = min(54, max(46, round(it.get("size", 38) * 1.3)))
        it["weight"] = "SemiBold"
    elif k == "bullet":
        it["size"] = 50
    elif k == "pills":
        it["size"] = 46
    elif k == "eyebrow":
        it["size"] = 34
    return it


def restyle(spec, date, theme):
    music, clip, crop, speed, loop, credit = C[date]
    scenes, t = [], 0.0
    for i, sc in enumerate(s for s in spec["scenes"]):
        items = [restyle_item(it, i == 0) for it in sc["items"] if it["kind"] != "image"]
        if not items:
            continue
        new = {"start": round(t, 2), "end": round(t + SCENE, 2), "top": sc.get("top", 600), "stagger": 0.6, "items": items}
        if not scenes:
            new["instant"] = True
        scenes.append(new)
        t += SCENE
    out = {
        "theme": theme, "category": spec.get("category", "Lifestyle"), "duration": round(t + END, 2),
        "still_times": [0.2] + [round(sc["start"] + 2.5, 2) for sc in scenes[1:]] + [round(t + 5.5, 2)],
        "text_panel": {"alpha": 0.9, "pad": 52},
        "background_video": {"src": MEDIA + clip, "crop": crop, "speed": speed, "loop": loop,
                             "tint_alpha": TINT[theme], "source": "Motion Array: " + credit},
        "audio": {"src": MEDIA + f"foundher-music-{music}.wav", "volume": 0.6, "fade_out": 2.5, "source": MUSIC[music]},
        "photo_source": "Background footage: Motion Array, " + credit,
        "scenes": scenes,
        "end_card": dict(spec["end_card"], start=t),
    }
    return out


def main():
    args = sys.argv[1:]
    only = set(a for a in args if a[:2] == "20")
    data = json.loads((ROOT / "data/posts.json").read_text())
    arts = sorted((p for p in data["posts"] if p["type"] == "article"), key=lambda p: p["date"])
    for n, p in enumerate(arts):
        d = p["date"]
        theme = THEMES[n % 3]
        path = SPECS / f"{d}-article.json"
        orig = json.loads(path.read_text())
        # Keep the original copy if this spec was already restyled.
        src = orig.get("_v1") or {k: orig[k] for k in ("scenes", "end_card", "category") if k in orig}
        spec = restyle(src, d, theme)
        spec["_v1"] = src
        if only and d not in only:
            continue
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
        music = C[d][0]
        p["notes"] = (f"Video v2 (16 Oct 2026): {C[d][5]} footage from Motion Array, {theme} panel, "
                      f"FoundHer '{music}' music already mixed in, so don't add Instagram music. "
                      "Copy unchanged from the approved version.")
        print(d, theme, music, C[d][1])
        if "--render" in args:
            out = ROOT / f"assets/{d}-article.mp4"
            stills = Path("/home/claude/stage/render") / f"{d}-article-v2"
            subprocess.run([sys.executable, str(ROOT / "tools/reels/render_reel.py"), str(path), str(out), "--stills", str(stills)],
                           check=True, cwd=ROOT)
    data["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (ROOT / "data/posts.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
