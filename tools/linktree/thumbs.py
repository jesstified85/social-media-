"""Linktree thumbnails for FoundHer (800x800 PNG, safe inside Linktree's circle crop).

Kinds
  icon   brand-colour tile with a Lucide icon       ("icon", name, theme, lucide_icon)
  pin    the FoundHer heart pin                      ("pin", name, theme)
  date   event date tile, e.g. NOV / 10              ("date", name, theme, "NOV", "10")
  photo  frame from a clip or image, centre-cropped  ("photo", name, src, seconds, x_center 0..1, y_center 0..1, zoom)

Add a row to THUMBS for each new article or event, run the script and upload the PNG from
assets/linktree/ as the link's thumbnail in Linktree (Link > Thumbnail > Upload).

Usage: python3 tools/linktree/thumbs.py
Needs: pip install cairosvg; Lucide icons (npm pack lucide-static) at LUCIDE below.
"""
import io
import re
import subprocess
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/linktree"
FONTS = ROOT / "tools/reels/fonts"
MEDIA = ROOT / "tools/reels/media"
LUCIDE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/lucide/package/icons")
S = 800

CREAM = "#FCF2E8"
CHARCOAL = "#1A1A1A"
TERRACOTTA = "#C86532"
THEMES = {  # background, foreground, accent
    "terracotta": ("#C86332", CREAM, CREAM),
    "sage": ("#A6B69A", CHARCOAL, TERRACOTTA),
    "rose": ("#D6999F", CHARCOAL, TERRACOTTA),
    "cream": (CREAM, TERRACOTTA, TERRACOTTA),
}

PIN = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
       '<path d="M12 23s-8-7-8-13.5a8 8 0 0 1 16 0C20 16 12 23 12 23z" fill="{fg}"/>'
       '<path d="M12 13.6 9.1 10.8a1.9 1.9 0 0 1 2.9-2.5 1.9 1.9 0 0 1 2.9 2.5z" fill="{bg}"/></svg>')

THUMBS = [
    ("pin", "join", "terracotta"),
    ("icon", "articles", "sage", "book-open"),
    ("icon", "auctions", "rose", "gavel"),
    ("icon", "events", "terracotta", "calendar-heart"),
    ("date", "event-2026-11-10", "sage", "NOV", "10"),
    ("photo", "article-2026-10-17", MEDIA / "motionarray-2732492-autumn-picnic.mp4", 4.0, 0.67, 0.42, 1.55),
]


def svg_png(svg, size):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size))).convert("RGBA")


def tile(theme):
    return Image.new("RGBA", (S, S), THEMES[theme][0])


def icon(theme, name):
    bg, fg, _ = THEMES[theme]
    svg = (LUCIDE / f"{name}.svg").read_text()
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).replace("currentColor", fg).replace('stroke-width="2"', 'stroke-width="1.75"')
    im = tile(theme)
    ic = svg_png(svg, 400)
    im.alpha_composite(ic, ((S - 400) // 2, (S - 400) // 2))
    return im


def pin(theme):
    bg, fg, _ = THEMES[theme]
    im = tile(theme)
    ic = svg_png(PIN.format(fg=fg, bg=bg), 460)
    im.alpha_composite(ic, ((S - 460) // 2, (S - 460) // 2 - 6))
    return im


def date(theme, month, day):
    bg, fg, accent = THEMES[theme]
    im = tile(theme)
    d = ImageDraw.Draw(im)
    fm = ImageFont.truetype(str(FONTS / "Montserrat.ttf"), 104)
    fm.set_variation_by_name("Bold")
    fd = ImageFont.truetype(str(FONTS / "Playfair.ttf"), 330)
    d.text((S / 2, 230), " ".join(month), font=fm, fill=fg, anchor="mm")
    d.line((S / 2 - 70, 310, S / 2 + 70, 310), fill=accent, width=6)
    d.text((S / 2, 480), day, font=fd, fill=fg, anchor="mm")
    return im


def photo(src, t, xc, yc=0.5, zoom=1.0):
    src = Path(src)
    if src.suffix.lower() in (".mp4", ".mov", ".bin"):
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", str(src), "-frames:v", "1",
                              "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
        im = Image.open(io.BytesIO(raw))
    else:
        im = Image.open(src)
    im = im.convert("RGBA")
    w, h = im.size
    side = int(min(w, h) / zoom)
    x = int(min(max(xc * w - side / 2, 0), w - side))
    y = int(min(max(yc * h - side / 2, 0), h - side))
    return im.crop((x, y, x + side, y + side)).resize((S, S), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for row in THUMBS:
        kind, name = row[0], row[1]
        im = {"icon": lambda: icon(row[2], row[3]), "pin": lambda: pin(row[2]),
              "date": lambda: date(row[2], row[3], row[4]), "photo": lambda: photo(*row[2:])}[kind]()
        im.convert("RGB").save(OUT / f"{name}.png", optimize=True)
        print("wrote", OUT / f"{name}.png")


if __name__ == "__main__":
    main()
