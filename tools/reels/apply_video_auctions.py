"""Upgrade the auction Reels and Stories to the footage style approved on the Oct 17 Reel:
Motion Array footage behind the text (theme-colour wash), music, larger shadowed text,
and a 5.5 s end card. Run after build_auctions_2026_q4.py (which writes the base specs).

Usage: python3 tools/reels/apply_video_auctions.py [--render]
Media (git-ignored, from FoundHer's Motion Array account) lives in tools/reels/media/.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/reels"))
import render_reel as rr  # noqa: E402

MEDIA = "tools/reels/media/"
CLIPS = {  # donor -> (file, crop [x, y, w, h] on 1920x1080, speed, credit)
    "beaumont": ("motionarray-173995-coffee-croissant.mp4", [760, 0, 608, 1080], 0.7, "Coffee And Croissant by DCStudio (173995)"),
    "lehi": ("motionarray-478019-kneading-dough.mp4", [800, 0, 608, 1080], 1.0, "Kneading Dough by Avi Meshulam (478019)"),
    "tates": ("motionarray-421044-chocolate-truffles.mp4", [656, 0, 608, 1080], 0.82, "Chocolate Truffles by Heinz Baumann Photography (421044)"),
    "stonehaven": ("motionarray-2607565-brushing-teeth.mp4", [480, 0, 608, 1080], 1.0, "Woman Brushing Teeth In Bathroom by mediame.pro (2607565)"),
}
AUDIO = {"src": MEDIA + "motionarray-12713-ukulele-whistle-40s.wav", "volume": 0.85, "fade_out": 1.8,
         "source": "Ukulele Whistle by SixideBeats (12713), 40 s version, not Content ID registered"}
THEMES = {  # alternate the three brand colours across the run
    "2026-10-21": "terracotta", "2026-10-25": "sage", "2026-10-28": "rose", "2026-11-01": "terracotta",
    "2026-11-04": "sage", "2026-11-08": "rose", "2026-11-11": "terracotta",
}
TINT = {"terracotta": 0.64, "sage": 0.74, "rose": 0.74}  # lighter washes need more cover for dark text
POSTS = {  # date -> donor whose clip leads the video
    "2026-10-21": "beaumont", "2026-10-25": "lehi", "2026-10-28": "beaumont", "2026-11-01": "tates",
    "2026-11-04": "lehi", "2026-11-08": "stonehaven", "2026-11-11": "tates",
}
TEXT_W = rr.TEXT_W


def fit_headline(lines, want):
    """Largest size <= want at which every headline line fits the text width."""
    size = want
    while size > 60:
        ok = True
        for text, italic in lines:
            f = rr.font("serif-i" if italic else "serif", size, "Medium Italic" if italic else "Regular")
            if rr.ImageDraw.Draw(rr.layer(10)).textlength(text, font=f) > TEXT_W:
                ok = False
                break
        if ok:
            return size
        size -= 2
    return size


def bg(donor, theme):
    f, crop, speed, credit = CLIPS[donor]
    return {"src": MEDIA + f, "crop": crop, "speed": speed, "tint_alpha": TINT[theme], "source": "Motion Array: " + credit}


def upgrade_reel(spec, donor, theme):
    spec["theme"] = theme
    spec["duration"] = 19.5
    spec["still_times"] = [0, 5.4, 9.4, 12.8, 15.0, 19.2]
    spec["text_shadow"] = True
    spec["background_video"] = bg(donor, theme)
    spec["audio"] = dict(AUDIO)
    spec["photo_source"] = "Background footage: " + spec["background_video"]["source"]
    for i, sc in enumerate(spec["scenes"]):
        sc["items"] = [it for it in sc["items"] if it["kind"] != "image"]
        sc["top"] = 560 if i in (0, 3) else 520
        for it in sc["items"]:
            k = it["kind"]
            if k == "headline":
                it["size"] = fit_headline(it["lines"], int(it.get("size", 80) * 1.28))
                it["gap"] = 56
            elif k == "body":
                it.update(size=46, weight="SemiBold")
            elif k == "bullet":
                it["size"] = 48
            elif k == "eyebrow":
                it.update(size=34, gap=52)
            elif k == "pills":
                it["size"] = 44
    return spec


def upgrade_story(spec, donor, theme):
    spec["theme"] = theme
    spec["text_shadow"] = True
    spec["background_video"] = bg(donor, theme)
    spec["audio"] = dict(AUDIO, fade_out=1.2)
    spec["decoration"] = False
    for sc in spec["scenes"]:
        sc["items"] = [it for it in sc["items"] if it["kind"] != "image"]
        sc["top"] = 420
        for it in sc["items"]:
            if it["kind"] == "headline":
                it["size"] = fit_headline(it["lines"], 100)
                it["gap"] = 50
            elif it["kind"] == "body":
                it.update(size=42, weight="SemiBold", gap=16)
            elif it["kind"] == "eyebrow":
                it.update(size=30, gap=40)
    return spec


def main(render):
    data = json.loads((ROOT / "data/posts.json").read_text())
    posts = {p["id"]: p for p in data["posts"]}
    for date, donor in POSTS.items():
        pid = f"{date}-auction"
        for suffix, fn in (("", upgrade_reel), ("-story", upgrade_story)):
            path = ROOT / f"tools/reels/specs/{pid}{suffix}.json"
            spec = fn(json.loads(path.read_text()), donor, THEMES[date])
            path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
            if render:
                subprocess.run([sys.executable, str(ROOT / "tools/reels/render_reel.py"), str(path),
                                str(ROOT / f"assets/{pid}{suffix}.mp4"), "--stills",
                                f"/home/claude/stage/render/{pid}{suffix}-v-stills"], check=True, stdout=subprocess.DEVNULL)
                print("rendered", pid + suffix)
        p = posts[pid]
        p["notes"] = (p["notes"].split("PLACEHOLDER PHOTO")[0]
                      + "Video: Motion Array footage (" + CLIPS[donor][3] + ") and music (Ukulele Whistle by SixideBeats, "
                      "not Content ID registered). It already has sound; do not add Instagram music.")
    (ROOT / "data/posts.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main("--render" in sys.argv)
