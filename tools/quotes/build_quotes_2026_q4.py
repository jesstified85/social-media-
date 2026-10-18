"""Render FoundHer quote posts (Oct 20 to Dec 13, 2026) and add them to data/posts.json.

Usage: python3 tools/quotes/build_quotes_2026_q4.py

Format: 1080x1350 (4:5) feed image, solid brand colour, charcoal Playfair Display quote,
small @foundher.tribe handle at the bottom. No logo, tagline or call to action in the image.
Colours alternate post by post between Rose Blush #D79AA0 and Sage #A6B99C.
Weekly rhythm: Tuesday = female friendship, Friday = womanhood, Sunday = strength.
Re-running replaces the existing quote posts (ids ending in -quote) and their images.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "tools" / "reels" / "fonts"
W, H = 1080, 1350
CHARCOAL = (26, 26, 26)
COLOURS = {"rose": ((0xD7, 0x9A, 0xA0), "Rose Blush"), "sage": ((0xA6, 0xB9, 0x9C), "Sage")}

CTA = "Tag a friend to share this message with."
TAGS = {
    "Friendship": "#FemaleFriendship #FriendshipQuotes #GirlFriends #WomenSupportingWomen #FoundHerTribe",
    "Womanhood": "#Womanhood #WomenEmpowerment #QuotesForWomen #WomenSupportingWomen #FoundHerTribe",
    "Strength": "#StrongWomen #InnerStrength #QuotesForWomen #WomenSupportingWomen #FoundHerTribe",
}

# date, category, quote (as it appears on the image), caption lead-in
POSTS = [
    ("2026-10-20", "Friendship", "She didn’t fix it. She just sat with me in it.", "For the friend who doesn't need to say anything to make it better."),
    ("2026-10-23", "Womanhood", "Be the woman you needed when you were younger.", "A note to your younger self, and to the woman you are now."),
    ("2026-10-25", "Strength", "She cried, then she handled it.", "Both things can be true."),
    ("2026-10-27", "Friendship", "The friend who says “I’m on my way” without asking why.", "Every woman deserves an \"I'm on my way\" friend."),
    ("2026-10-30", "Womanhood", "She is still becoming. So are you.", "Growth doesn't have a finish line."),
    ("2026-11-01", "Strength", "Doing it scared still counts.", "Shaky hands still count. Showing up still counts."),
    ("2026-11-03", "Friendship", "Find the friend who remembers the little things.", "The little things are the big things."),
    ("2026-11-06", "Womanhood", "Soft and strong can live in the same woman.", "You don't have to choose one."),
    ("2026-11-08", "Strength", "Brave doesn’t always look loud.", "Courage comes in a lot of volumes."),
    ("2026-11-10", "Friendship", "A good friend knows your coffee order and your heart.", "The friend who knows exactly what you need before you ask."),
    ("2026-11-13", "Womanhood", "You don’t have to have it all together to be worthy.", "Messy, in progress and still enough."),
    ("2026-11-15", "Strength", "You’ve survived every hard day so far.", "Your track record for getting through hard days is 100%."),
    ("2026-11-17", "Friendship", "Some friendships don’t need daily texts. They just pick up where they left off.", "The best kind of friendship never runs out of time."),
    ("2026-11-20", "Womanhood", "There is no wrong age to begin again.", "It's never too late to start something new."),
    ("2026-11-22", "Strength", "Quiet strength is still strength.", "Not all strength makes noise."),
    ("2026-11-24", "Friendship", "Thank you to the women who stayed.", "This Thanksgiving week, a little gratitude for the women who showed up and kept showing up."),
    ("2026-11-27", "Womanhood", "You’re allowed to change your mind about who you want to be.", "Change is allowed. Growth requires it."),
    ("2026-11-29", "Strength", "Rest is not a reward. It’s a requirement.", "Permission to slow down this weekend."),
    ("2026-12-01", "Friendship", "Grown women still need a best friend.", "No matter your age, everyone needs their person."),
    ("2026-12-04", "Womanhood", "You can be a work in progress and a masterpiece at the same time.", "Both at once. Always."),
    ("2026-12-06", "Strength", "Strong women lift each other up.", "When one of us rises, we all do."),
    ("2026-12-08", "Friendship", "Friends who hype you up are a form of self-care.", "Surround yourself with women who cheer the loudest."),
    ("2026-12-11", "Womanhood", "Not every season is a blooming one. That’s okay.", "Every season has its purpose. This one too."),
    ("2026-12-13", "Strength", "Some days strength is just getting out of bed.", "If today was hard, you still showed up. That counts."),
]


def font(name, size, variation):
    f = ImageFont.truetype(str(FONTS / name), size)
    f.set_variation_by_name(variation)
    return f


def wrap(draw, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def render(quote, bg, out):
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    max_w = 760  # 160px side margins: lots of breathing room
    size = 68
    while True:
        f = font("Playfair.ttf", size, b"Regular")
        lines = wrap(d, quote, f, max_w)
        if len(lines) <= 4 or size <= 52:
            break
        size -= 4
    # balance: narrow the measure as far as possible without adding a line, so no orphaned last word
    n, w_try = len(lines), max_w
    while w_try > 300:
        trial = wrap(d, quote, f, w_try - 10)
        if len(trial) > n:
            break
        lines, w_try = trial, w_try - 10
    lh = round(size * 1.32)
    block = lh * len(lines)
    top = (H - block) / 2 - 40  # sit slightly above optical centre
    for i, line in enumerate(lines):
        w = d.textlength(line, font=f)
        d.text(((W - w) / 2, top + i * lh), line, font=f, fill=CHARCOAL)
    # small handle, letter-spaced
    hf = font("Montserrat.ttf", 22, b"Medium")
    handle = "@foundher.tribe"
    spacing = 3
    total = sum(d.textlength(c, font=hf) for c in handle) + spacing * (len(handle) - 1)
    x = (W - total) / 2
    for c in handle:
        d.text((x, H - 120), c, font=hf, fill=CHARCOAL)
        x += d.textlength(c, font=hf) + spacing
    img.save(out, optimize=True)


def main():
    data_path = ROOT / "data" / "posts.json"
    data = json.loads(data_path.read_text())
    posts = [p for p in data["posts"] if not p["id"].endswith("-quote")]
    for i, (date, cat, quote, lead) in enumerate(POSTS):
        key = "rose" if i % 2 == 0 else "sage"
        rgb, cname = COLOURS[key]
        asset = f"assets/{date}-quote.png"
        render(quote, rgb, ROOT / asset)
        posts.append({
            "id": f"{date}-quote",
            "date": date,
            "type": "quote",
            "order": 9,
            "platform": "Instagram + Facebook",
            "status": "review",
            "title": "Quote: " + quote.replace("’", "'").replace("“", '"').replace("”", '"'),
            "caption": lead + "\n\n" + CTA,
            "hashtags": TAGS[cat],
            "asset": asset,
            "assetName": f"FoundHer-quote-{date}.png",
            "notes": f"{cat} quote. {cname} background, 1080x1350 feed post. Original wording (not attributed to anyone). No music needed; can also be shared to Stories.",
        })
    posts.sort(key=lambda p: (p.get("date", ""), p.get("order", 0)))
    data["posts"] = posts
    data["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data_path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"Rendered {len(POSTS)} quote posts; posts.json now has {len(posts)} posts")


if __name__ == "__main__":
    main()
