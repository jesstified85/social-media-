#!/usr/bin/env python3
"""Brand a FoundHer ORIGINAL video for Instagram/Facebook Reels and TikTok.

Matches the approved look of the Nov 3 reel: coral pin-heart bug in the top-left corner over
the footage, then a cream end card with the master logo, "Where you find your people." and
@FOUNDHER.TRIBE. Output is 1080x1920, 30 fps, H.264 + AAC.

Only for footage FoundHer owns or has permission to use. Third-party clips use the
"FoundHer Take" format instead (credit kept, original account tagged).

    python3 tools/reels/brand_original.py IN.mp4 OUT.mp4 [--end 2.5]
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = Path(__file__).resolve().parent
ROOT = S.parent.parent
W, H, FPS = 1080, 1920, 30
CREAM = (252, 242, 232)
TERRACOTTA = (201, 101, 50)
CORAL_SVG = ROOT / "tools/quotes/brand/FoundHer-Pin-Coral.svg"


def font(name, size):
    path = {"serif-i": "PlayfairItalic.ttf", "sans": "Montserrat.ttf"}[name]
    f = ImageFont.truetype(str(S / "fonts" / path), size)
    try:
        f.set_variation_by_name({"sans": "SemiBold", "serif-i": "Italic"}[name])
    except Exception:
        pass
    return f


def tracked(d, y, text, f, fill, tr):
    widths = [d.textlength(c, font=f) for c in text]
    total = sum(widths) + tr * (len(text) - 1)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill)
        x += w + tr


def end_card(path):
    # The approved end card, taken from the Nov 3 reel (terracotta master logo). Do not redraw.
    Image.open(S / "plates/endcard_original_720.png").convert("RGB").resize((W, H), Image.LANCZOS).save(path)


def end_card_drawn(path):
    """Unused fallback (coral logo plate). Kept for reference only."""
    im = Image.new("RGB", (W, H), CREAM)
    logo = Image.open(S / "plates/logo_on_cream.png").convert("RGB")
    im.paste(logo, ((W - logo.width) // 2, 640))
    d = ImageDraw.Draw(im)
    fi = font("serif-i", 58)
    tag = "Where you find your people."
    d.text(((W - d.textlength(tag, font=fi)) / 2, 1000), tag, font=fi, fill=(60, 52, 46))
    tracked(d, 1120, "@FOUNDHER.TRIBE", font("sans", 28), TERRACOTTA, 28 * 0.18)
    im.save(path)


def pin_bug(path, width=64):
    subprocess.run(["rsvg-convert", "-w", str(width), "-o", str(path), str(CORAL_SVG)], check=True)


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height:stream_side_data=rotation:format=duration",
                          "-of", "json", str(src)], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in j["streams"])
    return float(j["format"]["duration"]), v["width"], v["height"], has_audio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--end", type=float, default=2.5, help="end card seconds")
    a = ap.parse_args()
    dur, w, h, has_audio = probe(a.src)
    tmp = Path(tempfile.mkdtemp())
    end_card(tmp / "end.png"); pin_bug(tmp / "pin.png")
    fade = 0.35
    # Footage: fill 9:16. Near-9:16 sources are cover-cropped; others sit on a blurred fill.
    fill = (f"[0:v]split[a][b];[b]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=40:2,eq=brightness=-0.08[bg];[a]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2")
    portrait = h > w and abs((w / h) - 9 / 16) < 0.06
    base = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}" if portrait else fill)
    fc = (f"{base},fps={FPS},setsar=1,format=yuv420p[v0];"
          f"[v0][2:v]overlay=86:250,format=yuv420p[vb];"
          f"[1:v]loop=-1:1,fps={FPS},scale={W}:{H},setsar=1,format=yuv420p,trim=duration={a.end + fade}[ec];"
          f"[vb][ec]xfade=transition=fade:duration={fade}:offset={dur - fade:.3f}[v]")
    total = dur + a.end
    if has_audio:
        fc += (f";[0:a]aresample=48000,afade=t=out:st={max(dur - 0.8, 0):.3f}:d=0.8,"
               f"apad,atrim=duration={total:.3f}[aout]")
    else:
        fc += f";anullsrc=r=48000:cl=stereo,atrim=duration={total:.3f}[aout]"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", a.src, "-loop", "1", "-i", str(tmp / "end.png"),
           "-i", str(tmp / "pin.png"), "-filter_complex", fc, "-map", "[v]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", f"{total:.3f}", a.out]
    subprocess.run(cmd, check=True)
    print(f"{a.out}: {total:.1f}s ({dur:.1f}s footage + {a.end}s end card)")


if __name__ == "__main__":
    sys.exit(main())
