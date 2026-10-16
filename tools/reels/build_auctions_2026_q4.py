"""Auction Reels and posts, 21 Oct to 11 Nov 2026.

Every fact comes from the live auction listings on foundhertribe.app (read 16 Oct 2026):
prize, value, starting bid, end time (stored as UTC, shown here in Denver time) and donor.
Rules quoted from the app's auction pages: bid with coins, outbid coins come straight back,
members can win 1 auction a month and 4 a year.

Photos: none yet (the listing photos are not the donors' own). Add
{"kind": "image", "src": "tools/reels/photos/<file>.jpg", "height": 560, "focus": 0.5, "gap": 48}
as the first item of scene 2 once a donor photo arrives, then re-run this script.

Usage: python3 tools/reels/build_auctions_2026_q4.py [--render]
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = "https://foundhertribe.app/auctions/"

A = {
    "beaumont": dict(photo=("auction-coffee-croissant.jpg", 0.45, "photo-1664139694630-c9eaccd84765"), head=["A $50 gift card to", "*Beaumont Bakery", "*& Café."], id="01a13d9e-bf2f-71b5-a081-dbe43c6952a7", prize="$50 Beaumont Bakery & Café Gift Card",
                     short="$50 Beaumont Bakery & Café", donor="Beaumont Café", value="$50", start=200,
                     ends="Wednesday, October 28 at 10 p.m.", ends_short=["Wednesday, Oct. 28", "*at 10 p.m."],
                     about="The Millcreek favorite for fresh croissants, brunch and coffee.",
                     tags="#SaltLakeCity #Millcreek #ShopLocalUtah"),
    "lehi": dict(photo=("auction-kneading-dough.jpg", 0.5, "photo-1543157840-e6aaa4dccac5"), head=["A $50 gift certificate", "*to Lehi Roller Mills."], id="01a13d9f-35d2-728e-9ddf-ae11a5572c05", prize="$50 Lehi Roller Mills Gift Certificate",
                 short="$50 Lehi Roller Mills", donor="Lehi Roller Mills", value="$50", start=200,
                 ends="Wednesday, November 4 at 10 p.m.", ends_short=["Wednesday, Nov. 4", "*at 10 p.m."],
                 about="The historic Lehi flour mill and country store, famous for its baking mixes, flour and gifts.",
                 tags="#Lehi #UtahCounty #ShopLocalUtah"),
    "tates": dict(photo=("auction-truffles.jpg", 0.5, "photo-1566565286951-f81c7ba5619d"), head=["A $100 gift card", "*to Tate's Chocolate."], id="01a13d9f-5844-7306-b00e-52034c7249a1", prize="$100 Tate's Chocolate Gift Card",
                  short="$100 Tate's Chocolate", donor="Tate's Chocolate", value="$100", start=400,
                  ends="Wednesday, November 11 at 10 p.m.", ends_short=["Wednesday, Nov. 11", "*at 10 p.m."],
                  about="A $100 gift card to Tate's Chocolate.", tags="#ShopLocalUtah"),
    "stonehaven": dict(story_name="Electric toothbrush, Stonehaven Dental", photo=("auction-toothbrush.jpg", 0.55, "photo-1559592892-19db4235d786"), head=["A new electric", "toothbrush from", "*Stonehaven Dental."], id="01a13d9f-4709-7290-b700-f1612be83d14", prize="Electric Toothbrush from Stonehaven Dental",
                       short="Electric toothbrush", donor="Stonehaven Dental", value=None, start=200,
                       ends="Wednesday, November 11 at 10 p.m.", ends_short=["Wednesday, Nov. 11", "*at 10 p.m."],
                       about="A new electric toothbrush, donated by Stonehaven Dental in Lehi.",
                       tags="#Lehi #UtahCounty #ShopLocalUtah"),
}
BASE_TAGS = "#FoundHerTribe #FindYourPeople"
RULES = "Bid with your coins, not cash. If someone outbids you, your coins come straight back."


def photo_item(a, height=520):
    f, focus, _ = a["photo"]
    return {"kind": "image", "src": f"tools/reels/photos/{f}", "height": height, "focus": focus, "gap": 44}


def H(*lines):
    return [[l[1:], True] if l.startswith("*") else [l, False] for l in lines]


def links(aid):
    return {k: f"{APP}{aid}?utm_source={k}&utm_medium=social&utm_campaign=auctions" for k in ("instagram", "facebook")}


def nb(t):
    """Non-breaking space before the last word, so titles never end on an orphan."""
    head, _, last = t.rpartition(" ")
    return f"{head} {last}" if head else t


def spec(theme, category, scenes, title, summary, eyebrow="LIVE NOW, IN THE APP"):
    return {
        "theme": theme, "category": category, "duration": 16.5,
        "still_times": [0, 5.4, 9.4, 12.8, 16.0],
        "photo_source": "PLACEHOLDER: free-license Unsplash photo (unsplash.com/license), not the donor's own. Swap for a donor photo when supplied.",
        "scenes": scenes,
        "end_card": {"start": 14.0, "title": nb(title), "summary": summary, "eyebrow": eyebrow, "button": "BID IN THE APP"},
    }


def feature(key, theme, hook):
    a = A[key]
    value = [{"kind": "body", "text": f"Value {a['value']}. Donated by {a['donor']}.", "size": 36, "at": 1.0}] if a["value"] \
        else [{"kind": "body", "text": f"Donated by {a['donor']}.", "size": 36, "at": 1.0}]
    scenes = [
        {"start": 0, "end": 3.6, "top": 640, "instant": True,
         "items": [{"kind": "headline", "size": 90, "lines": H(*hook)}]},
        {"start": 3.6, "end": 7.4, "top": 400, "stagger": 0.4, "items": [
            photo_item(a),
            {"kind": "eyebrow", "text": "UP FOR AUCTION", "rule": True, "gap": 40},
            {"kind": "headline", "size": 76, "lines": H(*a["head"]), "gap": 40},
        ] + value},
        {"start": 7.4, "end": 11.2, "top": 600, "stagger": 0.45, "items": [
            {"kind": "eyebrow", "text": "HOW TO BID", "rule": True, "gap": 46},
            {"kind": "bullet", "text": "Bid with coins, not cash."},
            {"kind": "bullet", "text": f"Bidding starts at {a['start']} coins."},
            {"kind": "bullet", "text": "Outbid? Your coins come straight back."}]},
        {"start": 11.2, "end": 14.4, "top": 640, "items": [
            {"kind": "headline", "size": 80, "lines": H("Bidding ends", *a["ends_short"]), "gap": 56},
            {"kind": "body", "text": f"Thank you, {a['donor']}.", "size": 38, "at": 1.0}]},
    ]
    return spec(theme, "Auctions", scenes, a["prize"], f"Donated by {a['donor']}. Bidding ends {a['ends']}")


def last_call(keys, theme, hook, title, summary):
    names = [A[k]["short"] if A[k]["value"] else A[k]["short"] + " from " + A[k]["donor"] for k in keys]
    scenes = [
        {"start": 0, "end": 3.6, "top": 640, "instant": True,
         "items": [{"kind": "headline", "size": 90, "lines": H(*hook)}]},
        {"start": 3.6, "end": 7.4, "top": 470, "stagger": 0.4, "items": [
            photo_item(A[keys[0]]),
            {"kind": "eyebrow", "text": "CLOSING TONIGHT AT 10 P.M.", "rule": True, "gap": 46}]
            + [{"kind": "bullet", "text": n} for n in names]
            + [{"kind": "body", "text": "Donated by " + " and ".join(A[k]["donor"] for k in keys) + ".", "size": 36, "at": 1.2}]},
        {"start": 7.4, "end": 11.2, "top": 640, "items": [
            {"kind": "headline", "size": 80, "lines": H("Outbid?", "*Your coins come", "*straight back."), "gap": 56},
            {"kind": "body", "text": "So a bid costs you nothing unless you win.", "size": 38, "at": 1.0}]},
        {"start": 11.2, "end": 14.4, "top": 640, "items": [
            {"kind": "headline", "size": 80, "lines": H("Open the app.", "*Place your bid."), "gap": 56},
            {"kind": "body", "text": "Bidding closes at 10 p.m. tonight.", "size": 38, "at": 1.0}]},
    ]
    return spec(theme, "Auctions", scenes, title, summary, eyebrow="LAST CALL, IN THE APP")


def cap(*paras):
    return "\n\n".join(paras + ("Where you find your people.",))


POSTS = [
    ("2026-10-21", "beaumont", "Auction: $50 Beaumont Bakery & Café gift card", "Bid: $50 Beaumont Bakery & Café",
     cap("Croissants, brunch and coffee, on us (well, on your coins).",
         "A $50 gift card to Beaumont Bakery & Café, the Millcreek favorite for fresh croissants, brunch and coffee, is up for auction in the app now. Bidding starts at 200 coins.",
         RULES,
         "Bidding ends Wednesday, October 28 at 10 p.m. Thank you, Beaumont Café, for donating. Bid in the app, link in bio."),
     feature("beaumont", "terracotta", ["Your next brunch", "*could be on", "*your coins."])),
    ("2026-10-25", "lehi", "Auction: $50 Lehi Roller Mills gift certificate", "Bid: $50 Lehi Roller Mills",
     cap("Baking season is here, and so is this one.",
         "A $50 gift certificate to Lehi Roller Mills, the historic Lehi flour mill and country store famous for its baking mixes, flour and gifts, is up for auction in the app. Bidding starts at 200 coins.",
         RULES,
         "Bidding ends Wednesday, November 4 at 10 p.m. Thank you, Lehi Roller Mills, for donating. Bid in the app, link in bio."),
     feature("lehi", "sage", ["Baking season", "*just got a", "*little sweeter."])),
    ("2026-10-28", ["beaumont"], "Last call: Beaumont Bakery & Café auction ends tonight", "Last call: Beaumont auction",
     cap("Last call! The $50 Beaumont Bakery & Café gift card auction closes tonight at 10 p.m.",
         RULES + " So a bid costs you nothing unless you win.",
         "Thank you, Beaumont Café, for donating. Open the app and place your bid, link in bio."),
     None),
    ("2026-11-01", "tates", "Auction: $100 Tate's Chocolate gift card", "Bid: $100 Tate's Chocolate",
     cap("A $100 chocolate fund. Need we say more?",
         "A $100 gift card to Tate's Chocolate is up for auction in the app now. Bidding starts at 400 coins.",
         RULES,
         "Bidding ends Wednesday, November 11 at 10 p.m. Thank you, Tate's Chocolate, for donating. Bid in the app, link in bio."),
     feature("tates", "rose", ["A $100", "*chocolate fund.", "Need we say more?"])),
    ("2026-11-04", ["lehi"], "Last call: Lehi Roller Mills auction ends tonight", "Last call: Lehi Roller Mills",
     cap("Last call! The $50 Lehi Roller Mills gift certificate auction closes tonight at 10 p.m.",
         RULES + " So a bid costs you nothing unless you win.",
         "Thank you, Lehi Roller Mills, for donating. Open the app and place your bid, link in bio."),
     None),
    ("2026-11-08", "stonehaven", "Auction: electric toothbrush from Stonehaven Dental", "Bid: Stonehaven Dental toothbrush",
     cap("Treat yourself to the smallest luxury in your morning routine.",
         "A new electric toothbrush, donated by Stonehaven Dental in Lehi, is up for auction in the app now. Bidding starts at 200 coins.",
         RULES,
         "Bidding ends Wednesday, November 11 at 10 p.m. Thank you, Stonehaven Dental, for donating. Bid in the app, link in bio."),
     feature("stonehaven", "terracotta", ["Upgrade your", "*morning routine", "*with your coins."])),
    ("2026-11-11", ["tates", "stonehaven"], "Last call: two auctions end tonight", "Last call: 2 auctions tonight",
     cap("Last call! Two auctions close tonight at 10 p.m.",
         "A $100 Tate's Chocolate gift card, and a new electric toothbrush from Stonehaven Dental.",
         RULES + " So a bid costs you nothing unless you win.",
         "Thank you, Tate's Chocolate and Stonehaven Dental, for donating. Open the app and place your bid, link in bio."),
     None),
]

LAST_CALL = {
    "2026-10-28": dict(theme="rose", hook=["Last call.", "*Bidding ends", "*tonight."],
                       title="$50 Beaumont Bakery & Café Gift Card",
                       summary="Bidding closes tonight at 10 p.m. Donated by Beaumont Café."),
    "2026-11-04": dict(theme="terracotta", hook=["Last call.", "*Bidding ends", "*tonight."],
                       title="$50 Lehi Roller Mills Gift Certificate",
                       summary="Bidding closes tonight at 10 p.m. Donated by Lehi Roller Mills."),
    "2026-11-11": dict(theme="sage", hook=["Two auctions.", "*One night left."],
                       title="Two Auctions Close Tonight",
                       summary="A $100 Tate's Chocolate gift card and a Stonehaven Dental electric toothbrush. Bidding closes at 10 p.m."),
}


def main(render):
    data = json.loads((ROOT / "data/posts.json").read_text())
    posts = {p["id"]: p for p in data["posts"]}
    for date, key, title, linktree, caption, sp in POSTS:
        pid = f"{date}-auction"
        keys = key if isinstance(key, list) else [key]
        if sp is None:
            lc = LAST_CALL[date]
            sp = last_call(keys, lc["theme"], lc["hook"], lc["title"], lc["summary"])
        (ROOT / f"tools/reels/specs/{pid}.json").write_text(json.dumps(sp, indent=2, ensure_ascii=False) + "\n")
        tags = " ".join([BASE_TAGS, "#FoundHerAuctions"] + sorted(set(" ".join(A[k]["tags"] for k in keys).split()), key=lambda t: " ".join(A[k]["tags"] for k in keys).index(t)) + ["#UtahWomen"])
        p = posts[pid]
        p.update({
            "status": "draft", "title": title, "caption": caption, "hashtags": tags,
            "links": links(A[keys[0]]["id"]), "linktreeTitle": linktree,
            "notes": ("Facts from the live auction listing, checked 16 Oct 2026. "
                      + ("Two auctions: link goes to the Tate's listing; Stonehaven is " + APP + A["stonehaven"]["id"] + ". " if len(keys) > 1 else "")
                      + "PLACEHOLDER PHOTO (free Unsplash license): " + ", ".join("https://images.unsplash.com/" + A[k]["photo"][2] for k in keys)
                      + ". Not the donor's own; swap in a donor photo when one arrives. Reel is silent; add music in Instagram."),
            "asset": f"assets/{pid}.mp4", "assetName": f"FHT_{date}_auction_{A[keys[0]]['donor'].lower().replace(' ', '-').replace(chr(39), '').replace('é', 'e')}.mp4",
            "assetType": "video/mp4",
        })
        p.pop("assetNote", None)
        if render:
            subprocess.run([sys.executable, str(ROOT / "tools/reels/render_reel.py"), str(ROOT / f"tools/reels/specs/{pid}.json"),
                            str(ROOT / f"assets/{pid}.mp4"), "--stills", f"/home/claude/stage/render/{pid}-stills"],
                           check=True, stdout=subprocess.DEVNULL)
            print("rendered", pid)
    data["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (ROOT / "data/posts.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__" and "--stories" not in sys.argv:
    main("--render" in sys.argv)


# ---------------------------------------------------------------------------
# Instagram Story versions (9:16) with room for interactive stickers.
# Text sits in the top half; the lower half (y 1120 to 1620) stays empty so the
# countdown, link and poll stickers can be placed there in Instagram.
# ---------------------------------------------------------------------------
STORY_END = {  # Denver local end time, for the countdown sticker
    "beaumont": "Wed, Oct 28, 10:00 PM", "lehi": "Wed, Nov 4, 10:00 PM",
    "tates": "Wed, Nov 11, 10:00 PM", "stonehaven": "Wed, Nov 11, 10:00 PM",
}
STORY_HOW = ("In Instagram: upload this as a Story, then add the stickers below in the empty lower half "
             "(Countdown first, Link sticker under it). Tap Copy to paste each value.")


def story_link(aid):
    return f"{APP}{aid}?utm_source=instagram&utm_medium=story&utm_campaign=auctions"


def story_spec(theme, hook, lines, eyebrow, photo=None):
    if photo:
        items = [dict(photo_item(photo, height=300), at=0, gap=36),
                 {"kind": "headline", "size": 60, "lines": H(*hook), "gap": 28, "at": 0.4}]
    else:
        items = [{"kind": "headline", "size": 88, "lines": H(*hook), "gap": 54, "at": 0}]
    items += [{"kind": "eyebrow", "text": eyebrow, "rule": True, "gap": 34, "at": 0.9}]
    items += [{"kind": "body", "text": t, "size": 36, "gap": 14, "at": 1.3 + 0.35 * i} for i, t in enumerate(lines)]
    return {
        "theme": theme, "category": "Auctions", "duration": 10.0, "decoration": False, "click": False,
        "still_times": [0, 3.0, 9.5],
        "scenes": [{"start": 0, "end": 99, "top": 400, "instant": True, "items": items}],
        "end_card": {"start": 99, "title": "unused", "summary": "unused"},
    }


def stories(render):
    data = json.loads((ROOT / "data/posts.json").read_text())
    posts = {p["id"]: p for p in data["posts"]}
    for date, key, title, linktree, caption, sp in POSTS:
        pid = f"{date}-auction"
        keys = key if isinstance(key, list) else [key]
        last = isinstance(key, list)
        a = A[keys[0]]
        theme = json.loads((ROOT / f"tools/reels/specs/{pid}.json").read_text())["theme"]
        if last and len(keys) == 2:
            st = story_spec(theme, ["Two auctions.", "*Closing tonight."], ["$100 Tate's Chocolate gift card", "Electric toothbrush, Stonehaven Dental", "Bidding closes at 10 p.m."], "LAST CALL", A[keys[0]])
        elif last:
            st = story_spec(theme, ["Last call.", "*Ends tonight."], [a.get("story_name", a["prize"]), f"Donated by {a['donor']}.", "Bidding closes at 10 p.m."], "LAST CALL", a)
        else:
            st = story_spec(theme, ["Up for", "*auction."], [a.get("story_name", a["prize"]), f"Starts at {a['start']} coins.", f"Ends {a['ends'].replace(' at ', ', ')}"], "LIVE NOW, IN THE APP", a)
        (ROOT / f"tools/reels/specs/{pid}-story.json").write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n")
        stickers = [
            {"label": "Countdown name", "value": ("Auctions close tonight" if len(keys) == 2 else f"{a['donor']} auction ends")},
            {"label": "Countdown ends", "value": STORY_END[keys[0]]},
            {"label": "Link sticker URL", "value": story_link(a["id"])},
            {"label": "Link sticker text", "value": "Bid now"},
        ]
        if len(keys) == 2:
            stickers.append({"label": "2nd link sticker URL", "value": story_link(A[keys[1]]["id"])})
        if not last:
            stickers += [{"label": "Poll question", "value": "Would you bid on this?"},
                         {"label": "Poll answers", "value": "Obviously / Tell me more"}]
        posts[pid]["story"] = {
            "asset": f"assets/{pid}-story.mp4",
            "assetName": f"FHT_{date}_auction-story_{a['donor'].lower().replace(' ', '-').replace(chr(39), '').replace('é', 'e')}.mp4",
            "how": STORY_HOW, "stickers": stickers,
        }
        if render:
            subprocess.run([sys.executable, str(ROOT / "tools/reels/render_reel.py"), str(ROOT / f"tools/reels/specs/{pid}-story.json"),
                            str(ROOT / f"assets/{pid}-story.mp4"), "--stills", f"/home/claude/stage/render/{pid}-story-stills"],
                           check=True, stdout=subprocess.DEVNULL)
            print("rendered story", pid)
    (ROOT / "data/posts.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__" and "--stories" in sys.argv:
    stories("--render" in sys.argv)
