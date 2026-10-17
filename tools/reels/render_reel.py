"""Render a FoundHer article Reel in the reference style.

1080x1920, 30 fps, silent H.264 MP4. Background plates, the pin icon and the
logo are taken from the team's own reference Reels (see plates/).

Usage: python3 tools/reels/render_reel.py <spec.json> <out.mp4> [--stills DIR]
"""
import json
import math
import random
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
    "terracotta": {"plate": "plate_terracotta.png", "pin": "pin_terracotta.png", "deco": (252, 242, 232),
                   "fg": CREAM, "soft": (246, 214, 194), "line": (226, 160, 125), "dot": CREAM},
    "rose": {"plate": "plate_rose.png", "pin": "pin_rose.png", "deco": (255, 246, 247),
             "fg": CHARCOAL, "soft": (62, 40, 44), "line": (176, 112, 120), "dot": TERRACOTTA},
    "sage": {"plate": "plate_sage.png", "pin": "pin_sage.png", "deco": (255, 255, 252),
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
    for w in text.split(" "):
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
        self.reveal = False
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


def make_image(src, height=620, radius=28, focus=0.5):
    """A real photo, cover-cropped into a rounded card the width of the text column."""
    path = Path(src)
    if not path.is_absolute():
        path = S.parent.parent / src  # relative to the repo root
    photo = Image.open(path).convert("RGB")
    tw, th = TEXT_W, height
    scale = max(tw / photo.width, th / photo.height)
    photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
    left = (photo.width - tw) // 2
    top = int((photo.height - th) * focus)
    photo = photo.crop((left, top, left + tw, top + th))
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, tw - 1, th - 1), radius=radius, fill=255)
    im = layer(th)
    im.paste(photo, (MARGIN, 0), mask)
    return im


# ---------- Decoration: hearts and swirls (simple shapes, never the logo or pin) ----------

def heart_points(cx, cy, size, n=90):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((cx + x * size / 34, cy + y * size / 34))
    return pts


_heart_cache = {}


def heart_sprite(size, color, outline):
    key = (size, color, outline)
    if key not in _heart_cache:
        k = 4
        big = Image.new("RGBA", (size * k, size * k), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        pts = heart_points(size * k / 2, size * k / 2 + size * k * 0.04, size * k * 0.92)
        if outline:
            d.line(pts + [pts[0]], fill=color + (255,), width=max(2, int(size * k * 0.07)), joint="curve")
        else:
            d.polygon(pts, fill=color + (255,))
        _heart_cache[key] = big.resize((size, size), Image.LANCZOS)
    return _heart_cache[key]


def with_alpha(im, a):
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return out


class Floaters:
    """Small hearts drifting upward with a gentle sway, in a band away from the text."""

    def __init__(self, color, seed, count=10, x_range=(620, 1010), y_range=(1330, 1890), max_alpha=0.68):
        rnd = random.Random(seed)
        self.color, self.y_range, self.max_alpha = color, y_range, max_alpha
        self.items = []
        for i in range(count):
            self.items.append({
                "x": rnd.uniform(*x_range),
                "phase": rnd.uniform(0, 1),
                "speed": rnd.uniform(38, 70),
                "sway": rnd.uniform(8, 20),
                "period": rnd.uniform(2.6, 4.2),
                "size": rnd.choice([30, 38, 46, 54, 64]),
                "outline": rnd.random() < 0.45,
                "spin": rnd.uniform(-10, 10),
            })

    def draw(self, frame, t, fade=1.0):
        lo, hi = self.y_range
        span = hi - lo
        for it in self.items:
            travel = (t * it["speed"] + it["phase"] * span) % span
            y = hi - travel
            x = it["x"] + it["sway"] * math.sin(2 * math.pi * t / it["period"] + it["phase"] * 6)
            pos = travel / span  # 0 at the bottom, 1 at the top of the band
            a = min(1.0, pos / 0.15) * min(1.0, (1 - pos) / 0.3) * self.max_alpha * fade
            if a <= 0.02:
                continue
            spr = heart_sprite(it["size"], self.color, it["outline"])
            spr = spr.rotate(it["spin"] * math.sin(t + it["phase"] * 5), resample=Image.BICUBIC, expand=True)
            frame.alpha_composite(with_alpha(spr, a), (int(x - spr.width / 2), int(y - spr.height / 2)))


def make_swirl(color, width=420, height=90, stroke=5):
    """A hand-drawn style flourish: a soft wave with one loop and a small heart at the end."""
    k = 3
    big = Image.new("RGBA", (W * k, height * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    pts = []
    for i in range(400):
        t = i / 399
        x = MARGIN + t * width
        y = height * 0.55 + 12 * math.sin(2 * math.pi * 1.2 * t)
        if 0.48 < t < 0.68:
            ph = (t - 0.48) / 0.2 * 2 * math.pi
            x -= 30 * math.sin(ph)
            y -= 26 * (1 - math.cos(ph)) / 2 * 1.6
        pts.append((x * k, y * k))
    d.line(pts, fill=color + (255,), width=stroke * k, joint="curve")
    ex, ey = pts[-1]
    hp = heart_points(ex + 22 * k, ey - 4 * k, 26 * k)
    d.polygon(hp, fill=color + (255,))
    small = big.resize((W, height), Image.LANCZOS)
    im = layer(height)
    im.alpha_composite(small)
    return im


def add_shadow(im, strength=0.55, blur=10, dy=4, color=(20, 12, 8)):
    """Soft halo behind text so it holds up over moving footage (dark for light text, light for dark text)."""
    from PIL import ImageFilter
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda v: int(v * strength))
    sh = Image.new("RGBA", im.size, tuple(color) + (0,))
    sh.putalpha(a)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, dy))
    out.alpha_composite(im)
    return out


def build_scene(scene, theme, shadow=False, panel=None):
    """Turn a scene spec into positioned Elements.

    panel: optional {"alpha": 0.9, "pad": 52} draws a solid rounded panel in the theme colour
    behind the scene's text, so it reads cleanly over footage.
    """
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
            im = make_body(item["text"], item.get("size", 36), th["fg"], weight=item.get("weight", "Regular"))
        elif kind == "eyebrow":
            im = make_eyebrow(item["text"], th["fg"] if shadow else th["soft"], th["line"] if item.get("rule") else None,
                              size=item.get("size", 24))
        elif kind == "bullet":
            im = make_bullet(item["text"], th["fg"], th["dot"], size=item.get("size", 36))
        elif kind == "pills":
            im = make_pills(item["items"], th["fg"], size=item.get("size", 32))
        elif kind == "swirl":
            im = make_swirl(th["dot"], item.get("width", 420))
        elif kind == "image":
            im = make_image(item["src"], item.get("height", 620), item.get("radius", 28), item.get("focus", 0.5))
        else:
            raise ValueError(kind)
        if shadow and kind != "image":
            light_text = sum(th["fg"]) > 382
            im = add_shadow(im) if light_text else add_shadow(im, strength=0.85, blur=12, dy=0, color=(255, 248, 240))
        bbox = im.getbbox()
        h = bbox[3] if bbox else im.height
        el = Element(im, 0, y, item.get("at", t))
        el.reveal = kind == "swirl"
        els.append(el)
        y += h + item.get("gap", 34)
        t += stagger
    assert y <= SAFE_BOT, f"scene content runs below the 4:5 crop (y={y})"
    if panel and els:
        pad = panel.get("pad", 52)
        top = scene.get("top", 640) - pad
        bottom = max(e.y + (e.img.getbbox() or (0, 0, 0, e.img.height))[3] for e in els) + pad
        colour = Image.open(PLATES / th["plate"]).convert("RGB").getpixel((40, 40))
        im = Image.new("RGBA", (W, bottom - top), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((MARGIN - pad, 0, W - MARGIN + pad, bottom - top - 1), radius=44,
                                             fill=colour + (int(255 * panel.get("alpha", 0.9)),))
        bg = Element(im, 0, top, 0)
        els.insert(0, bg)
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

    centered_tracked(724, spec.get("eyebrow", "THE FULL READ, IN THE APP"), font("sans", 24, "SemiBold"), TERRACOTTA, 24 * 0.16)
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
    button = (bx, y, bx + bw, y + bh)
    d.rounded_rectangle((bx, y, bx + bw, y + bh), radius=bh // 2, fill=TERRACOTTA)
    fb = font("sans", 28, "Bold")
    label = spec.get("button", "READ IT IN THE APP")
    tw = tracked_width(d, label, fb, 28 * 0.1)
    draw_tracked(d, ((W - tw) / 2, y + bh / 2 - 19), label, fb, (255, 255, 255), 28 * 0.1)
    y += bh + 34
    centered_tracked(y, "LINK IN BIO", font("sans", 23, "SemiBold"), CHARCOAL, 23 * 0.16)
    fi = font("serif-i", 46, "Medium Italic")
    tag = "Where you find your people."
    w = d.textlength(tag, font=fi)
    d.text(((W - w) / 2, 1520), tag, font=fi, fill=TERRACOTTA)
    assert y + 40 < 1520, "end card content collides with the tagline"
    return im, button


def cursor_sprite(height=64):
    """A plain arrow pointer: white fill, charcoal outline."""
    k = 4
    hgt = height * k
    pts = [(0, 0), (0, 0.80), (0.21, 0.62), (0.36, 0.95), (0.49, 0.89), (0.34, 0.57), (0.60, 0.57)]
    pts = [(x * hgt + 6 * k, y * hgt + 6 * k) for x, y in pts]
    big = Image.new("RGBA", (int(hgt * 0.7) + 12 * k, hgt + 12 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.line(pts + [pts[0]], fill=CHARCOAL + (255,), width=3 * k, joint="curve")
    return big.resize((big.width // k, big.height // k), Image.LANCZOS)


CURSOR = None


def draw_click(frame, tr, button):
    """Cursor glides onto the button, presses it, and a ripple pulses out. tr = seconds into the end card."""
    global CURSOR
    if CURSOR is None:
        CURSOR = cursor_sprite()
    x0, y0, x1, y1 = button
    tx, ty = x0 + (x1 - x0) * 0.64, y0 + (y1 - y0) * 0.58
    sx, sy = 960, 1760
    if tr < 0.75:
        return
    m = ease((tr - 0.75) / 0.8)
    cx, cy = sx + (tx - sx) * m, sy + (ty - sy) * m
    click = 1.7
    if click <= tr < click + 0.6:
        r_k = (tr - click) / 0.6
        ring = layer(H)
        rd = ImageDraw.Draw(ring)
        rad = 14 + 70 * r_k
        a = int(200 * (1 - r_k))
        rd.ellipse((tx - rad, ty - rad, tx + rad, ty + rad), outline=(255, 255, 255, a), width=5)
        frame.alpha_composite(ring)
    pressed = click <= tr < click + 0.18
    if pressed:
        shade = layer(H)
        ImageDraw.Draw(shade).rounded_rectangle(button, radius=(y1 - y0) // 2, fill=(0, 0, 0, 46))
        frame.alpha_composite(shade)
    spr = CURSOR
    if pressed:
        spr = spr.resize((int(spr.width * 0.88), int(spr.height * 0.88)), Image.LANCZOS)
    frame.alpha_composite(spr, (int(cx), int(cy)))


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3



class VideoBackground:
    """Optional moving background: a stock clip cropped to 9:16, scaled to 1080x1920 and
    washed with the theme colour so the brand text stays legible.

    spec["background_video"] = {"src": "path.mp4", "crop": [x, y, w, h], "start": 0,
                                "tint": [r, g, b], "tint_alpha": 0.5, "speed": 1.0}
    speed < 1 slows the clip down (e.g. 0.7 stretches a 14 s clip to 20 s).
    """

    def __init__(self, bg, theme_plate):
        x, y, w, h = bg["crop"]
        speed = bg.get("speed", 1.0)
        slow = f"setpts=PTS/{speed}," if speed != 1.0 else ""
        vf = f"{slow}crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos,fps={FPS}"
        # "loop": true repeats a short clip instead of holding its last frame;
        # "loop": "bounce" plays it forward then backward (no visible jump), doubling its length.
        loop = ["-stream_loop", "-1"] if bg.get("loop") is True else []
        if bg.get("loop") == "bounce":
            vf = (f"crop={w}:{h}:{x}:{y},split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1,"
                  f"{slow}scale={W}:{H}:flags=lanczos,fps={FPS}")
        self.proc = subprocess.Popen(
            ["ffmpeg", "-loglevel", "error", *loop, "-ss", str(bg.get("start", 0)), "-i", str(bg["src"]),
             "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        tint = tuple(bg.get("tint") or theme_plate.convert("RGB").getpixel((40, 40)))
        a = int(255 * bg.get("tint_alpha", 0.5))
        # Even wash plus a heavier band behind the text zone (top two thirds).
        self.wash = Image.new("RGBA", (W, H), tint + (a,))
        grad = Image.new("L", (1, H))
        for yy in range(H):
            k = max(0.0, 1 - yy / (H * 0.8))
            grad.putpixel((0, yy), int(70 * k))
        band = Image.new("RGBA", (W, H), tint + (0,))
        band.putalpha(grad.resize((W, H)))
        self.wash.alpha_composite(band)
        self.last = None

    def frame(self):
        raw = self.proc.stdout.read(W * H * 3)
        if len(raw) == W * H * 3:
            self.last = Image.frombytes("RGB", (W, H), raw).convert("RGBA")
            self.last.alpha_composite(self.wash)
        return self.last.copy()

    def close(self):
        # The clip may run longer than the Reel; stop the decoder quietly.
        self.proc.terminate()
        self.proc.stdout.close()
        self.proc.wait()


def add_audio(video, audio, out, duration):
    """Mux a music track under the silent render, faded out at the end."""
    src = audio["src"]
    vol = audio.get("volume", 1.0)
    fade = audio.get("fade_out", 1.2)
    start = audio.get("start", 0)
    af = f"volume={vol},afade=t=in:d=0.15,afade=t=out:st={max(0, duration - fade):.2f}:d={fade:.2f}"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-ss", str(start), "-i", str(src),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{duration:.3f}", "-movflags", "+faststart", out], check=True)


def render(spec, out, stills=None):
    theme = spec["theme"]
    plate = Image.open(PLATES / THEMES[theme]["plate"]).convert("RGBA")
    label = build_label(theme, spec["category"])
    scenes = []
    for sc in spec["scenes"]:
        scenes.append((sc["start"], sc["end"], build_scene(sc, theme, spec.get("text_shadow", False), spec.get("text_panel")),
                       sc.get("instant", False)))
    end_start = spec["end_card"]["start"]
    end_img, button = build_end_card(spec["end_card"])
    total = spec["duration"]
    nframes = int(round(total * FPS))
    fade_in, fade_out, rise, xfade = 0.5, 0.35, 26, 0.45
    deco_on = spec.get("decoration", True)
    seed = spec.get("seed", spec["end_card"]["title"])
    floaters = Floaters(THEMES[theme]["deco"], seed)
    end_floaters = Floaters((215, 154, 160), seed + "-end", count=7, x_range=(90, 990), y_range=(1590, 1900), max_alpha=0.45)

    bgv = spec.get("background_video")
    video_bg = VideoBackground(bgv, plate) if bgv else None
    audio = spec.get("audio")
    silent_out = out + ".silent.mp4" if audio else out
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent_out],
        stdin=subprocess.PIPE)
    for n in range(nframes):
        t = n / FPS
        frame = video_bg.frame() if video_bg else plate.copy()
        if deco_on:
            floaters.draw(frame, t)
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
                if el.reveal:
                    p = ease(local / 1.1) if not (instant and el.appear == 0) else 1.0
                    if p <= 0:
                        continue
                    img = el.at_opacity(out_k)
                    cut = int(MARGIN + p * (img.width - MARGIN))
                    frame.alpha_composite(img.crop((0, 0, cut, img.height)), (0, el.y))
                    continue
                dy = int((1 - k) * rise)
                frame.alpha_composite(el.at_opacity(op), (0, el.y + dy))
        if t >= end_start:
            a = min(1.0, (t - end_start) / xfade)
            end_frame = end_img.copy()
            if deco_on:
                end_floaters.draw(end_frame, t - end_start)
            if spec.get("click", True):
                draw_click(end_frame, t - end_start, button)
            frame = Image.blend(frame, end_frame, a) if a < 1 else end_frame
        rgb = frame.convert("RGB")
        if stills is not None and n in stills:
            rgb.save(stills[n])
        proc.stdin.write(rgb.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")
    if video_bg:
        video_bg.close()
    if audio:
        add_audio(silent_out, audio, out, total)
        Path(silent_out).unlink()


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
