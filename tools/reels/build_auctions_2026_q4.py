"""Auction Reels, Stories and posts, 21 Oct to 8 Nov 2026 (v2, 16 Oct 2026).

Jess's rules for auction posts:
- Advertise the prize only. No end dates, countdowns or "last call" posts.
- Credit line: "Shared with love from our sponsors at <name>." (never "Donated by").
- Slow pages (about 5 s each) and text on a solid brand-colour panel over the footage.
- Colours alternate terracotta, green (sage), pink (rose).
- Music: FoundHer's own auction track (OpenArt), footage from Motion Array.

Facts come from the live listings on foundhertribe.app (16 Oct 2026): prize, value, starting
bid and sponsor. Rules quoted from the app's auction pages: bid with coins, outbid coins come
straight back, members can win 1 auction a month and 4 a year, bidders stay anonymous.

Usage: python3 tools/reels/build_auctions_2026_q4.py [--render]
Media (git-ignored) lives in tools/reels/media/.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/reels"))
import render_reel as rr  # noqa: E402

APP = "https://foundhertribe.app/auctions"
MEDIA = "tools/reels/media/"
MUSIC = {"src": MEDIA + "foundher-music-auctions.wav", "volume": 0.6, "fade_out": 2.5,
         "source": "FoundHer auction background music (made in OpenArt for FoundHer)"}
TINT = {"terracotta": 0.45, "sage": 0.5, "rose": 0.5}

A = {
    "beaumont": dict(id="01a13d9e-bf2f-71b5-a081-dbe43c6952a7", prize="$50 Beaumont Bakery & Café Gift Card",
                     head=["A $50 gift card", "*to Beaumont", "*Bakery & Café."], sponsor="Beaumont Café",
                     value="$50", start=200, about="The Millcreek favorite for fresh croissants, brunch and coffee.",
                     clip=("motionarray-173995-coffee-croissant.mp4", [760, 0, 608, 1080], 0.6,
                           "Coffee And Croissant by DCStudio (173995)"),
                     tags="#SaltLakeCity #Millcreek #ShopLocalUtah"),
    "lehi": dict(id="01a13d9f-35d2-728e-9ddf-ae11a5572c05", prize="$50 Lehi Roller Mills Gift Certificate",
                 head=["A $50 gift", "certificate to", "*Lehi Roller Mills."], sponsor="Lehi Roller Mills",
                 value="$50", start=200, about="The historic Lehi flour mill and country store, famous for its baking mixes, flour and gifts.",
                 clip=("motionarray-478019-kneading-dough.mp4", [800, 0, 608, 1080], 0.8,
                       "Kneading Dough by Avi Meshulam (478019)"),
                 tags="#Lehi #UtahCounty #ShopLocalUtah"),
    "tates": dict(id="01a13d9f-5844-7306-b00e-52034c7249a1", prize="$100 Tate's Chocolate Gift Card",
                  head=["A $100 gift card", "*to Tate's", "*Chocolate."], sponsor="Tate's Chocolate",
                  value="$100", start=400, about="A $100 gift card to Tate's Chocolate.",
                  clip=("motionarray-421044-chocolate-truffles.mp4", [656, 0, 608, 1080], 0.6,
                        "Chocolate Truffles by Heinz Baumann Photography (421044)"),
                  tags="#ShopLocalUtah"),
    "stonehaven": dict(id="01a13d9f-4709-7290-b700-f1612be83d14", prize="Electric Toothbrush from Stonehaven Dental",
                       head=["A new electric", "toothbrush from", "*Stonehaven Dental."], sponsor="Stonehaven Dental",
                       value=None, start=200, about="A new electric toothbrush from Stonehaven Dental in Lehi.",
                       clip=("motionarray-2607565-brushing-teeth.mp4", [480, 0, 608, 1080], 0.8,
                             "Woman Brushing Teeth In Bathroom by mediame.pro (2607565)"),
                       tags="#Lehi #UtahCounty #ShopLocalUtah"),
}


def H(*lines):
    return [[l[1:], True] if l.startswith("*") else [l, False] for l in lines]


def nb(t):
    head, _, last = t.rpartition(" ")
    return f"{head} {last}" if head else t


def love(keys):
    names = [A[k]["sponsor"] for k in keys]
    joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    return f"Shared with love from our sponsors at {joined}."


def fit(lines, want):
    size = want
    d = rr.ImageDraw.Draw(rr.layer(10))
    while size > 60:
        if all(d.textlength(t, font=rr.font("serif-i" if i else "serif", size, "Medium Italic" if i else "Regular")) <= rr.TEXT_W
               for t, i in lines):
            return size
        size -= 2
    return size


def headline(*lines, want=110, gap=48):
    L = H(*lines)
    return {"kind": "headline", "size": fit(L, want), "lines": L, "gap": gap}


def body(text, size=48, at=None, gap=30):
    it = {"kind": "body", "text": text, "size": size, "weight": "SemiBold", "gap": gap}
    if at is not None:
        it["at"] = at
    return it


def eyebrow(text):
    return {"kind": "eyebrow", "text": text, "rule": True, "gap": 44, "size": 34}


def bullet(text):
    return {"kind": "bullet", "text": text, "size": 50}


def scenes_at(*blocks, length=5.0):
    """Lay scenes back to back, each `length` seconds (first one instant)."""
    out, t = [], 0.0
    for i, (top, items) in enumerate(blocks):
        sc = {"start": round(t, 2), "end": round(t + length, 2), "top": top, "stagger": 0.6, "items": items}
        if i == 0:
            sc["instant"] = True
        out.append(sc)
        t += length
    return out, t


def video(key, theme):
    f, crop, speed, credit = A[key]["clip"]
    return {"src": MEDIA + f, "crop": crop, "speed": speed, "tint_alpha": TINT[theme], "source": "Motion Array: " + credit}


def reel(theme, clip_key, blocks, title, summary, eyebrow_text="LIVE NOW, IN THE APP"):
    scenes, t = scenes_at(*blocks)
    return {
        "theme": theme, "category": "Auctions", "duration": round(t + 6.0, 2),
        "still_times": [0.2] + [round(sc["start"] + 2.5, 2) for sc in scenes[1:]] + [round(t + 5.5, 2)],
        "text_panel": {"alpha": 0.9, "pad": 52},
        "background_video": video(clip_key, theme), "audio": dict(MUSIC),
        "photo_source": "Background footage: Motion Array, " + A[clip_key]["clip"][3],
        "scenes": scenes,
        "end_card": {"start": t, "title": nb(title), "summary": summary, "eyebrow": eyebrow_text, "button": "BID IN THE APP"},
    }


HOW_TO_BID = (520, [eyebrow("HOW TO BID"), bullet("Bid with your coins, not cash."),
                    bullet("Outbid? Your coins come straight back."), bullet("Bidders stay anonymous.")])


def feature(key, theme, hook):
    a = A[key]
    prize_items = [eyebrow("UP FOR AUCTION"), headline(*a["head"], want=100)]
    prize_items.append(body((f"Worth {a['value']}. " if a["value"] else "") + f"Bidding starts at {a['start']} coins.", at=1.2))
    blocks = [
        (600, [headline(*hook, want=118)]),
        (520, prize_items),
        (600, [headline("Shared with love", "*from our sponsors", want=104), body(f"at {a['sponsor']}.", size=54, at=1.0)]),
        HOW_TO_BID,
        (600, [headline("Open the app.", "*Place your bid.", want=118), body("Link in bio.", at=1.0)]),
    ]
    return reel(theme, key, blocks, a["prize"], love([key]))


def roundup(keys, theme):
    blocks = [
        (600, [headline("Live in the app", "*right now.", want=118)]),
        (520, [eyebrow("UP FOR AUCTION")] + [bullet(A[k]["prize"].replace(" Gift Card", " gift card").replace(" Gift Certificate", " gift certificate")) for k in keys]),
        (560, [headline("Shared with love", "*from our sponsors.", want=104), body(", ".join(A[k]["sponsor"] for k in keys[:-1]) + " and " + A[keys[-1]]["sponsor"] + ".", size=46, at=1.0)]),
        HOW_TO_BID,
        (600, [headline("Open the app.", "*Place your bid.", want=118), body("Link in bio.", at=1.0)]),
    ]
    return reel(theme, keys[-1], blocks, "Live Auctions in the App", love(keys))


def how_it_works(theme, clip_key):
    blocks = [
        (600, [headline("Your coins can", "*win you prizes.", want=118)]),
        (520, [eyebrow("HOW AUCTIONS WORK"), bullet("Local sponsors share prizes."), bullet("You bid with coins, not cash."), bullet("Outbid? Your coins come straight back.")]),
        (520, [eyebrow("GOOD TO KNOW"), bullet("Bidders stay anonymous."), bullet("Members can win 1 auction a month and 4 a year.")]),
        (600, [headline("Shared with love", "*from our sponsors.", want=104), body("Thank you for making it possible.", at=1.0)]),
        (600, [headline("Open the app.", "*Take a look.", want=118), body("Link in bio.", at=1.0)]),
    ]
    return reel(theme, clip_key, blocks, "How FoundHer Auctions Work", "Bid with coins on prizes shared by our local sponsors.",
                eyebrow_text="AUCTIONS, IN THE APP")


def cap(*paras):
    return "\n\n".join(paras + ("Where you find your people.",))


RULES = "Bid with your coins, not cash. If someone outbids you, your coins come straight back."
BASE_TAGS = "#FoundHerTribe #FindYourPeople #FoundHerAuctions"

POSTS = [
    ("2026-10-21", ["beaumont"], "terracotta", "Auction: $50 Beaumont Bakery & Café gift card", "Bid: $50 Beaumont Bakery & Café",
     lambda: feature("beaumont", "terracotta", ["Your next brunch", "*could be on", "*your coins."]),
     cap("Croissants, brunch and coffee, on your coins.",
         "A $50 gift card to Beaumont Bakery & Café, the Millcreek favorite for fresh croissants, brunch and coffee, is up for auction in the app. Bidding starts at 200 coins.",
         RULES,
         love(["beaumont"]) + " Bid in the app, link in bio.")),
    ("2026-10-25", ["lehi"], "sage", "Auction: $50 Lehi Roller Mills gift certificate", "Bid: $50 Lehi Roller Mills",
     lambda: feature("lehi", "sage", ["Baking season", "*just got a", "*little sweeter."]),
     cap("Baking season is here, and so is this one.",
         "A $50 gift certificate to Lehi Roller Mills, the historic Lehi flour mill and country store famous for its baking mixes, flour and gifts, is up for auction in the app. Bidding starts at 200 coins.",
         RULES,
         love(["lehi"]) + " Bid in the app, link in bio.")),
    ("2026-10-28", ["tates"], "rose", "Auction: $100 Tate's Chocolate gift card", "Bid: $100 Tate's Chocolate",
     lambda: feature("tates", "rose", ["A $100", "*chocolate fund.", "Need we say more?"]),
     cap("A $100 chocolate fund. Need we say more?",
         "A $100 gift card to Tate's Chocolate is up for auction in the app. Bidding starts at 400 coins.",
         RULES,
         love(["tates"]) + " Bid in the app, link in bio.")),
    ("2026-11-01", ["stonehaven"], "terracotta", "Auction: electric toothbrush from Stonehaven Dental", "Bid: Stonehaven Dental toothbrush",
     lambda: feature("stonehaven", "terracotta", ["Upgrade your", "*morning routine", "*with your coins."]),
     cap("Treat yourself to the smallest luxury in your morning routine.",
         "A new electric toothbrush from Stonehaven Dental in Lehi is up for auction in the app. Bidding starts at 200 coins.",
         RULES,
         love(["stonehaven"]) + " Bid in the app, link in bio.")),
    ("2026-11-04", ["lehi", "tates", "stonehaven"], "sage", "Live auctions: Lehi Roller Mills, Tate's Chocolate and Stonehaven Dental", "Bid on live auctions",
     lambda: roundup(["lehi", "tates", "stonehaven"], "sage"),
     cap("Three prizes, live in the app right now.",
         "A $50 Lehi Roller Mills gift certificate, a $100 Tate's Chocolate gift card and a new electric toothbrush from Stonehaven Dental.",
         RULES,
         love(["lehi", "tates", "stonehaven"]) + " Bid in the app, link in bio.")),
    ("2026-11-08", ["tates", "stonehaven"], "rose", "How FoundHer auctions work", "How auctions work",
     lambda: how_it_works("rose", "tates"),
     cap("Did you know your coins can win you prizes?",
         "Local sponsors share prizes, and you bid on them with your coins, not cash. If someone outbids you, your coins come straight back. Bidders stay anonymous, and members can win 1 auction a month and 4 a year.",
         "Thank you to our sponsors for sharing them with love. Take a look in the app, link in bio.")),
]


def story_spec(theme, clip_key, title_lines, lines, eyebrow_text):
    items = [headline(*title_lines, want=104, gap=40), eyebrow(eyebrow_text)]
    items += [body(t, size=44, gap=14, at=1.0 + 0.5 * i) for i, t in enumerate(lines)]
    for it in items:
        it.setdefault("at", 0)
    return {
        "theme": theme, "category": "Auctions", "duration": 14.0, "decoration": False, "click": False,
        "still_times": [0.2, 4.0, 13.5], "text_panel": {"alpha": 0.9, "pad": 48},
        "background_video": video(clip_key, theme), "audio": dict(MUSIC, fade_out=1.5),
        "scenes": [{"start": 0, "end": 99, "top": 400, "instant": True, "stagger": 0.6, "items": items}],
        "end_card": {"start": 99, "title": "unused", "summary": "unused"},
    }


def link(aid, medium):
    return f"{APP}/{aid}?utm_source=instagram&utm_medium={medium}&utm_campaign=auctions"


STORY_HOW = ("In Instagram: upload this as a Story, then add the stickers below in the empty lower half "
             "(Link sticker first, poll under it). Tap Copy to paste each value.")


def main(render):
    data = json.loads((ROOT / "data/posts.json").read_text())
    posts = {p["id"]: p for p in data["posts"]}
    for date, keys, theme, title, linktree, build, caption in POSTS:
        pid = f"{date}-auction"
        spec = build()
        (ROOT / f"tools/reels/specs/{pid}.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
        a = A[keys[0]]
        if len(keys) == 1:
            st = story_spec(theme, keys[0], ["Up for", "*auction."],
                            [a["prize"], f"Bidding starts at {a['start']} coins.", love(keys)], "LIVE NOW, IN THE APP")
            url = link(a["id"], "social")
        elif date == "2026-11-04":
            st = story_spec(theme, keys[-1], ["Live in", "*the app."],
                            [A[k]["prize"] for k in keys] + ["Shared with love from our sponsors."], "UP FOR AUCTION")
            url = APP + "?utm_source=instagram&utm_medium=social&utm_campaign=auctions"
        else:
            st = story_spec(theme, keys[0], ["Your coins can", "*win you prizes."],
                            ["Bid with coins, not cash.", "Outbid? Your coins come straight back.", "Shared with love from our sponsors."],
                            "HOW AUCTIONS WORK")
            url = APP + "?utm_source=instagram&utm_medium=social&utm_campaign=auctions"
        (ROOT / f"tools/reels/specs/{pid}-story.json").write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n")
        story_url = url.replace("utm_medium=social", "utm_medium=story")
        tags = " ".join([BASE_TAGS] + list(dict.fromkeys(" ".join(A[k]["tags"] for k in keys).split())) + ["#UtahWomen"])
        p = posts[pid]
        p.update({
            "status": "draft", "title": title, "caption": caption, "hashtags": tags,
            "links": {"instagram": url, "facebook": url.replace("utm_source=instagram", "utm_source=facebook")},
            "linktreeTitle": linktree,
            "notes": ("Prize facts from the live auction listing, checked 16 Oct 2026. No end dates on purpose (Jess, 16 Oct). "
                      "Footage: Motion Array, " + A[keys[-1] if date == "2026-11-04" else keys[0]]["clip"][3] + ". "
                      "Music: FoundHer's own auction track, already in the video; do not add Instagram music."),
            "asset": f"assets/{pid}.mp4", "assetType": "video/mp4",
            "assetName": f"FHT_{date}_auction_{'-'.join(keys)}.mp4",
            "story": {"asset": f"assets/{pid}-story.mp4", "assetName": f"FHT_{date}_auction-story_{'-'.join(keys)}.mp4",
                      "how": STORY_HOW,
                      "stickers": [{"label": "Link sticker URL", "value": story_url},
                                   {"label": "Link sticker text", "value": "Bid now" if date != "2026-11-08" else "See the auctions"},
                                   {"label": "Poll question", "value": "Would you bid on this?" if len(keys) == 1 else "Which would you bid on?"},
                                   {"label": "Poll answers", "value": "Obviously / Tell me more" if len(keys) == 1 else "All of them / Still deciding"}]},
        })
        p.pop("assetNote", None)
        if render:
            for suffix in ("", "-story"):
                subprocess.run([sys.executable, str(ROOT / "tools/reels/render_reel.py"), str(ROOT / f"tools/reels/specs/{pid}{suffix}.json"),
                                str(ROOT / f"assets/{pid}{suffix}.mp4"), "--stills", f"/home/claude/stage/render/{pid}{suffix}-v2"],
                               check=True, stdout=subprocess.DEVNULL)
                print("rendered", pid + suffix, flush=True)
    # 11 Nov: both remaining auctions close that night, so it goes back to a placeholder for the next prizes.
    p = posts["2026-11-11-auction"]
    for k in ("caption", "hashtags", "links", "linktreeTitle", "asset", "assetName", "assetType", "story"):
        p.pop(k, None)
    p.update({"status": "placeholder", "title": "Auction feature (next prizes to confirm)",
              "notes": "Tate's and Stonehaven close tonight, so this slot waits for the next auction prizes."})
    data["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (ROOT / "data/posts.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main("--render" in sys.argv)
