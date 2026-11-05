#!/usr/bin/env python3
"""Brand a weekday Instagram video: prominent FoundHer logo badge over the footage,
then a cream closing card with a CTA that ends on the logo
("Want to find your next best friend?" + foundher logo). 720x1280, 30 fps, H.264 + AAC.

    python3 tools/reels/brand_weekday.py IN.mp4 OUT.mp4 "CTA text" [--end 3]

The CTA reads into the logo, so end it with "?" or "at". Second person, no em dashes.
Any on-screen credit already in the footage is left visible (never cropped or covered).
"""
import argparse, json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = Path(__file__).resolve().parent
W, H, FPS = 720, 1280, 30
CREAM = (252, 242, 232); CHARCOAL = (26, 26, 26); TERRACOTTA = (201, 101, 50)
LOGO_SVG = S / "brand/FoundHer-Primary-Logo.svg"


def font(name, size, var):
    f = ImageFont.truetype(str(S / "fonts" / {"serif": "Playfair.ttf", "sans": "Montserrat.ttf"}[name]), size)
    try: f.set_variation_by_name(var)
    except Exception: pass
    return f


def logo(width, out):
    subprocess.run(["rsvg-convert", "-w", str(width), "-o", str(out), str(LOGO_SVG)], check=True)
    return Image.open(out).convert("RGBA")


def badge(path, tmp):
    lg = logo(300, tmp / "lg_badge.png")
    px, py = 26, 16
    w, h = lg.width + 2 * px, lg.height + 2 * py
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=22, fill=CREAM + (240,))
    im.alpha_composite(lg, (px, py))
    im.save(path)
    return w, h


def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines


def end_card(path, cta, tmp):
    im = Image.new("RGBA", (W, H), CREAM + (255,))
    d = ImageDraw.Draw(im)
    f = font("serif", 46, "Regular")
    lines = wrap(d, cta, f, 560)
    mw = 560
    while mw > 200 and len(wrap(d, cta, f, mw - 10)) == len(lines):
        mw -= 10
    lines = wrap(d, cta, f, mw)
    lh = 62
    lg = logo(470, tmp / "lg_end.png")
    block = len(lines) * lh + 40 + lg.height
    y = (H - block) // 2 - 60
    for ln in lines:
        d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=CHARCOAL); y += lh
    y += 40
    im.alpha_composite(lg, ((W - lg.width) // 2, y)); y += lg.height + 56
    fs = font("sans", 20, "SemiBold")
    for txt, col in (("@FOUNDHER.TRIBE", TERRACOTTA), ("LINK IN BIO", CHARCOAL)):
        tr = 20 * 0.18; ws = [d.textlength(c, font=fs) for c in txt]; tot = sum(ws) + tr * (len(txt) - 1)
        x = (W - tot) / 2
        for c, w in zip(txt, ws): d.text((x, y), c, font=fs, fill=col); x += w + tr
        y += 40
    im.convert("RGB").save(path)


def probe(src):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,duration:format=duration",
                                   "-of", "json", str(src)], capture_output=True, text=True, check=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    return float(v.get("duration") or j["format"]["duration"]), v["width"], v["height"], any(s["codec_type"] == "audio" for s in j["streams"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("cta")
    ap.add_argument("--end", type=float, default=3.0)
    ap.add_argument("--badge-y", type=int, default=64)
    a = ap.parse_args()
    dur, w, h, has_audio = probe(a.src)
    tmp = Path(tempfile.mkdtemp())
    bw, bh = badge(tmp / "badge.png", tmp)
    end_card(tmp / "end.png", a.cta, tmp)
    fade = 0.35
    if h > w and abs(w / h - 9 / 16) < 0.06:
        base = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    else:
        base = (f"[0:v]split[a][b];[b]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,"
                f"eq=brightness=-0.1[bg];[a]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")
    fc = (f"{base},fps={FPS},tpad=stop_mode=clone:stop_duration=2,trim=duration={dur:.3f},setsar=1,format=yuv420p[v0];[v0][2:v]overlay=(W-w)/2:{a.badge_y},format=yuv420p[vb];"
          f"[1:v]loop=-1:1,fps={FPS},scale={W}:{H},setsar=1,format=yuv420p,trim=duration={a.end + fade}[ec];"
          f"[vb][ec]xfade=transition=fade:duration={fade}:offset={dur - fade:.3f}[v]")
    total = dur + a.end
    fc += (f";[0:a]aresample=48000,afade=t=out:st={max(dur - 0.8, 0):.3f}:d=0.8,apad,atrim=duration={total:.3f}[aout]"
           if has_audio else f";anullsrc=r=48000:cl=stereo,atrim=duration={total:.3f}[aout]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-loop", "1", "-i", str(tmp / "end.png"), "-i", str(tmp / "badge.png"),
                    "-filter_complex", fc, "-map", "[v]", "-map", "[aout]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", f"{total:.3f}", a.out], check=True)
    print(f"{a.out}: {total:.1f}s")


if __name__ == "__main__":
    main()
