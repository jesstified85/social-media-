"""Render a FoundHer article Reel in the reference style.

1080x1920, 30 fps, silent H.264 MP4. Background plates, the pin icon and the
logo are taken from the team's own reference Reels (see plates/).

Usage: python3 tools/reels/render_reel.py <spec.json> <out.mp4> [--stills DIR]
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = Path(__file__).resolve().parent
FONTS = S / "fonts"
PLATES = S / "plates"
W, H, FPS = 1080, 1920, 30
MARGIN = 96
TEXT_W = W - 2 * MARGIN
SAFE_TOP, SAFE_BOT = 285, 1635  # 4:5 centre crop

CREAM = (252, 242, 232)
CHARCOAL = (26, 26, 26)
TERRACOTTA = (201, 101, 50)
CORAL = (255, 107, 91)
BODY_ON_CREAM = (77, 68, 60)

THEMES = {
    "terracotta": {"plate": "plate_terracotta.png", "pin": "pin_terracotta.png",
                   "fg": CREAM, "soft": (246, 214, 194), "line": (226, 160, 125), "dot": CREAM},
    "sage": {"plate": "plate_sage.png", "pin": "pin_sage.png",
             "fg": CHARCOAL, "soft": (52, 58, 48), "line": (120, 136, 112), "dot": TERRACOTTA},
}

_font_cache = {}


def font(name, size, weight=None):
    key = (name, size, weight)
    if key not in _font_cache:
        path = {"serif": "Playfair.ttf", "serif-i": "PlayfairItalic.ttf", "sans": "Montserrat.ttf"}[name]
        f = ImageFont.truetype(str(FONTS / path), size)
        if weight:
            f.set_variation_by_name(weight)
        _font_cache[key] = f
    return _font_cache[key]


def tracked_width(draw, text, f, tracking):
    return sum(draw.textlength(ch, font=f) for ch in text) + tracking * max(len(text) - 1, 0)


def draw_tracked(draw, xy, text, f, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking
    return x


def balanced(draw, text, f, maxw):
    """Wrap to the fewest lines, then narrow the width so lines come out even."""
    n = len(wrap(draw, text, f, maxw))
    w = maxw
    while w > 200 and len(wrap(draw, text, f, w - 10)) == n:
        w -= 10
    return wrap(draw, text, f, w)


def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


class Element:
    """A pre-rendered RGBA layer with a top position and an appear time."""

    def __init__(self, img, x, y, appear):
        self.img, self.x, self.y, self.appear = img, x, y, appear
        self._cache = {}

    def at_opacity(self, op):
        q = round(op * 24) / 24
        if q not in self._cache:
            im = self.img.copy()
            a = im.getchannel("A").point(lambda v: int(v * q))
            im.putalpha(a)
            self._cache[q] = im
        return self._cache[q]


def layer(h):
    return Image.new("RGBA", (W, h), (0, 0, 0, 0))


def make_headline(lines, size, color, lh=1.16):
    """lines: list of [text, italic] pairs, one per line."""
    step = int(size * lh)
    im = layer(step * len(lines) + int(size * 0.4))
    d = ImageDraw.Draw(im)
    for i, (text, italic) in enumerate(lines):
        f = font("serif-i" if italic else "serif", size, "Medium Italic" if italic else "Regular")
        w = d.textlength(text, font=f)
        assert w <= TEXT_W, f"headline line too wide ({w:.0f}px): {text}"
        d.text((MARGIN, i * step), text, font=f, fill=color)
    return im


def make_body(text, size, color, lh=1.45, weight="Regular"):
    f = font("sans", size, weight)
    tmp = ImageDraw.Draw(layer(10))
    lines = wrap(tmp, text, f, TEXT_W)
    step = int(size * lh)
    im = layer(step * len(lines) + size // 2)
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((MARGIN, i * step), ln, font=f, fill=color)
    return im


def make_eyebrow(text, color, rule_color=None, size=24):
    f = font("sans", size, "SemiBold")
    im = layer(size * 2 + 20)
    d = ImageDraw.Draw(im)
    tw = tracked_width(d, text, f, size * 0.14)
    assert tw <= TEXT_W, f"eyebrow too wide: {text}"
    draw_tracked(d, (MARGIN, 0), text, f, color, size * 0.14)
    if rule_color:
        d.line((MARGIN, size + 22, W - MARGIN, size + 22), fill=rule_color, width=2)
    return im


def make_bullet(text, color, dot, size=36):
    f = font("sans", size, "Medium")
    tmp = ImageDraw.Draw(layer(10))
    indent = 40
    lines = balanced(tmp, text, f, TEXT_W - indent)
    step = int(size * 1.4)
    im = layer(step * len(lines) + size // 2)
    d = ImageDraw.Draw(im)
    cy = int(size * 0.62)
    d.ellipse((MARGIN, cy - 8, MARGIN + 16, cy + 8), fill=dot)
    for i, ln in enumerate(lines):
        d.text((MARGIN + indent, i * step), ln, font=f, fill=color)
    return im


def make_pills(items, color, size=32):
    """Outline pill tags flowing left to right, wrapping to new rows."""
    f = font("sans", size, "Medium")
    tmp = ImageDraw.Draw(layer(10))
    padx, pady, gap = 28, 16, 18
    ph = size + 2 * pady
    rows, cur, curw = [], [], 0
    for it in items:
        w = int(tmp.textlength(it, font=f)) + 2 * padx
        if cur and curw + gap + w > TEXT_W:
            rows.append(cur)
            cur, curw = [], 0
        cur.append((it, w))
        curw += (gap if curw else 0) + w
    rows.append(cur)
    im = layer(len(rows) * (ph + gap))
    d = ImageDraw.Draw(im)
    for r, row in enumerate(rows):
        x = MARGIN
        y = r * (ph + gap)
        for it, w in row:
            d.rounded_rectangle((x, y, x + w, y + ph), radius=ph // 2, outline=color, width=3)
            d.text((x + padx, y + pady - 2), it, font=f, fill=color)
            x += w + gap
    return im


def build_scene(scene, theme):
    """Turn a scene spec into positioned Elements."""
    th = THEMES[theme]
    els = []
    y = scene.get("top", 640)
    t = 0.0
    stagger = scene.get("stagger", 0.35)
    for item in scene["items"]:
        kind = item["kind"]
        if kind == "headline":
            im = make_headline(item["lines"], item.get("size", 96), th["fg"])
        elif kind == "body":
            im = make_body(item["text"], item.get("size", 36), th["fg"])
        elif kind == "eyebrow":
            im = make_eyebrow(item["text"], th["soft"], th["line"] if item.get("rule") else None)
        elif kind == "bullet":
            im = make_bullet(item["text"], th["fg"], th["dot"])
        elif kind == "pills":
            im = make_pills(item["items"], th["fg"])
        else:
            raise ValueError(kind)
        bbox = im.getbbox()
        h = bbox[3] if bbox else im.height
        els.append(Element(im, 0, y, item.get("at", t)))
        y += h + item.get("gap", 34)
        t += stagger
    assert y <= SAFE_BOT, f"scene content runs below the 4:5 crop (y={y})"
    return els


def build_label(theme, category):
    th = THEMES[theme]
    im = layer(80)
    pin = Image.open(PLATES / th["pin"]).convert("RGBA")
    im.paste(pin, (96, 0))
    d = ImageDraw.Draw(im)
    f = font("sans", 25, "SemiBold")
    x = draw_tracked(d, (158, 17), "FROM THE APP", f, th["fg"], 25 * 0.26)
    x = draw_tracked(d, (x + 22, 17), "·", f, th["fg"], 0)
    draw_tracked(d, (x + 22, 17), category.upper(), f, th["fg"], 25 * 0.26)
    return Element(im, 0, 296, 0)


def build_end_card(spec):
    im = Image.new("RGBA", (W, H), CREAM + (255,))
    im.paste(Image.open(PLATES / "logo_on_cream.png").convert("RGBA"), (200, 320))
    d = ImageDraw.Draw(im)

    def centered_tracked(y, text, f, fill, tr):
        w = tracked_width(d, text, f, tr)
        draw_tracked(d, ((W - w) / 2, y), text, f, fill, tr)

    centered_tracked(724, "THE FULL READ, IN THE APP", font("sans", 24, "SemiBold"), TERRACOTTA, 24 * 0.16)
    ft = font("serif", 54, "Regular")
    y = 800
    for ln in balanced(d, spec["title"], ft, 840):
        w = d.textlength(ln, font=ft)
        d.text(((W - w) / 2, y), ln, font=ft, fill=CHARCOAL)
        y += 70
    y += 34
    fs = font("sans", 31, "Regular")
    for ln in balanced(d, spec["summary"], fs, 840):
        w = d.textlength(ln, font=fs)
        d.text(((W - w) / 2, y), ln, font=fs, fill=BODY_ON_CREAM)
        y += 48
    y += 50
    bw, bh = 513, 102
    bx = (W - bw) // 2
    d.rounded_rectangle((bx, y, bx + bw, y + bh), radius=bh // 2, fill=TERRACOTTA)
    fb = font("sans", 28, "Bold")
    tw = tracked_width(d, "READ IT IN THE APP", fb, 28 * 0.1)
    draw_tracked(d, ((W - tw) / 2, y + bh / 2 - 19), "READ IT IN THE APP", fb, (255, 255, 255), 28 * 0.1)
    y += bh + 34
    centered_tracked(y, "LINK IN BIO", font("sans", 23, "SemiBold"), CHARCOAL, 23 * 0.16)
    fi = font("serif-i", 46, "Medium Italic")
    tag = "Where you find your people."
    w = d.textlength(tag, font=fi)
    d.text(((W - w) / 2, 1520), tag, font=fi, fill=TERRACOTTA)
    assert y + 40 < 1520, "end card content collides with the tagline"
    return im


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def render(spec, out, stills=None):
    theme = spec["theme"]
    plate = Image.open(PLATES / THEMES[theme]["plate"]).convert("RGBA")
    label = build_label(theme, spec["category"])
    scenes = []
    for sc in spec["scenes"]:
        scenes.append((sc["start"], sc["end"], build_scene(sc, theme), sc.get("instant", False)))
    end_start = spec["end_card"]["start"]
    end_img = build_end_card(spec["end_card"])
    total = spec["duration"]
    nframes = int(round(total * FPS))
    fade_in, fade_out, rise, xfade = 0.5, 0.35, 26, 0.45

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for n in range(nframes):
        t = n / FPS
        frame = plate.copy()
        frame.alpha_composite(label.img, (0, label.y))
        for start, end, els, instant in scenes:
            if t < start or t >= end:
                continue
            out_k = 1.0 if t < end - fade_out else max(0.0, (end - t) / fade_out)
            for el in els:
                local = t - start - el.appear
                if instant and el.appear == 0:
                    k = 1.0
                else:
                    k = ease(local / fade_in)
                op = k * out_k
                if op <= 0.01:
                    continue
                dy = int((1 - k) * rise)
                frame.alpha_composite(el.at_opacity(op), (0, el.y + dy))
        if t >= end_start:
            a = min(1.0, (t - end_start) / xfade)
            frame = Image.blend(frame, end_img, a) if a < 1 else end_img.copy()
        rgb = frame.convert("RGB")
        if stills is not None and n in stills:
            rgb.save(stills[n])
        proc.stdin.write(rgb.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text())
    out = sys.argv[2]
    stills = None
    if len(sys.argv) > 3 and sys.argv[3] == "--stills":
        d = Path(sys.argv[4])
        d.mkdir(parents=True, exist_ok=True)
        stills = {int(t * FPS): str(d / f"t{t:05.2f}.png") for t in spec.get("still_times", [])}
    render(spec, out, stills)
    print("rendered", out)
