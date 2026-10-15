"""Specs and captions for the Nov to Dec 2026 article Reels.

Writes tools/reels/specs/<id>.json for each Reel and updates the matching posts in
data/posts.json (caption, hashtags, links, Linktree title). All wording comes from
the live articles on foundhertribe.app, read on 14 Oct 2026.
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://foundhertribe.app/article/"


def H(*lines):
    """Headline lines; a leading '*' marks an italic line."""
    return [[l[1:], True] if l.startswith("*") else [l, False] for l in lines]


def links(slug):
    return {
        "instagram": f"{BASE}{slug}?utm_source=instagram&utm_medium=social&utm_campaign=articles",
        "facebook": f"{BASE}{slug}?utm_source=facebook&utm_medium=social&utm_campaign=articles",
    }


def reel(theme, category, photo_id, hook, s2_head, s2_body, s3, s4_head, s4_body, title, summary, hook_size=90):
    pid = None
    return {
        "theme": theme,
        "category": category,
        "duration": 16.5,
        "still_times": [0, 5.4, 9.4, 12.8, 16.0],
        "photo_source": f"Article hero image: https://images.unsplash.com/{photo_id} (Unsplash), as used on the article page",
        "scenes": [
            {"start": 0, "end": 3.6, "top": 640, "instant": True,
             "items": [{"kind": "headline", "size": hook_size, "lines": H(*hook)}]},
            {"start": 3.6, "end": 7.4, "top": 470, "stagger": 0.4, "items": [
                {"kind": "image", "src": "PHOTO", "height": 560, "focus": 0.45, "gap": 48},
                {"kind": "headline", "size": 70, "lines": H(*s2_head), "gap": 36},
                {"kind": "body", "text": s2_body, "size": 36}]},
            dict({"start": 7.4, "end": 11.2, "top": 560, "stagger": 0.45}, **s3),
            {"start": 11.2, "end": 14.4, "top": 640, "items": [
                {"kind": "headline", "size": 80, "lines": H(*s4_head), "gap": 56},
                {"kind": "body", "text": s4_body, "size": 38, "at": 1.0}]},
        ],
        "end_card": {"start": 14.0, "title": title, "summary": summary},
    }


def bullets(eyebrow, *items):
    return {"items": [{"kind": "eyebrow", "text": eyebrow, "rule": True, "gap": 46}]
            + [{"kind": "bullet", "text": t} for t in items]}


def pills(eyebrow, items, body):
    return {"stagger": 0.4, "items": [
        {"kind": "eyebrow", "text": eyebrow, "rule": True, "gap": 46},
        {"kind": "pills", "items": items, "gap": 40},
        {"kind": "body", "text": body, "size": 36, "at": 1.0}]}


POSTS = {
    "2026-11-03-article": dict(
        slug="make-friends-in-your-40s",
        title="How to Make Friends in Your 40s (When It Feels Like Everyone Is Already Settled)",
        linktree="How to Make Friends in Your 40s",
        hashtags="#FoundHerTribe #FindYourPeople #FriendsInYour40s #MidlifeFriendship #UtahWomen #SaltLakeCity #UtahCounty",
        caption=("The kids need you less. The work friends scattered. And there's no one to call for tacos on a Friday night.\n\n"
                 "If you're trying to make friends in your 40s, you're not behind and you're not broken. It's one of the most common friendship gaps, and nobody talks about it.\n\n"
                 "Our guide covers why midlife friendship feels harder, and what actually works: recurring plans, going alone, following up and reconnecting.\n\n"
                 "Send one text to an old friend this week. Then read the guide, link in bio.\n\n"
                 "Where you find your people."),
        spec=reel("terracotta", "Relationships", "photo-1761055924354-244f0ca66af2",
                  ["Somewhere around 43,", "you realized there", "*was no one to call", "*for tacos."],
                  ["You are not behind.", "*You are not broken."],
                  "It's the most common friendship gap nobody talks about.",
                  bullets("WHAT ACTUALLY WORKS",
                          "Choose recurring over one-off: meet six people ten times.",
                          "Go alone. It makes you more approachable.",
                          "Be the one who follows up.",
                          "Reconnect with a friend you drifted from."),
                  ["One awkward coffee", "is not a verdict.", "*It is a deposit."],
                  "Your next friend is probably looking for you too.",
                  "How to Make Friends in Your 40s (When It Feels Like Everyone Is Already Settled)",
                  "Why midlife friendship is harder, and exactly how to make friends anyway.", hook_size=84)),
    "2026-11-07-article": dict(
        slug="run-clubs-utah",
        title="Run Clubs and Walking Clubs in Utah: The Easiest Way to Make Friends Right Now",
        linktree="Run Clubs and Walking Clubs in Utah",
        hashtags="#FoundHerTribe #FindYourPeople #RunClub #WalkingClub #SaltLakeCity #UtahCounty #UtahWomen",
        caption=("You don't need to be fast. You barely need to be a runner.\n\n"
                 "Run clubs and walking clubs have quietly become one of the easiest places to meet people. You show up alone, fall into step with someone, and leave with a few new names in your phone.\n\n"
                 "Our guide lists clubs to try in Salt Lake County and Utah County, what to expect the first time, and the one habit that turns a group run into real friendships.\n\n"
                 "Pick one run and make it your run. Find a club, link in bio.\n\n"
                 "Where you find your people."),
        spec=reel("sage", "Wellness", "photo-1719299246410-df8d0f0845ee",
                  ["You don't need", "to be fast.", "*You barely need", "*to be a runner."],
                  ["Show up alone.", "*Leave with new names."],
                  "Run clubs are quietly the best place to meet people.",
                  bullets("YOUR FIRST GROUP RUN",
                          "Pick the easy or social run, not the speed workout.",
                          "Arrive ten minutes early and say it's your first time.",
                          "Walk breaks are normal."),
                  ["Stay for the", "after part.", "*That's where names", "*turn into plans."],
                  "Plenty of clubs welcome walkers too.",
                  "Run Clubs and Walking Clubs in Utah: The Easiest Way to Make Friends Right Now",
                  "Where to find a club in Salt Lake and Utah County, and how to turn a group run into friends.", hook_size=96)),
    "2026-11-10-article": dict(
        slug="host-a-friendsgiving",
        title="How to Host a Friendsgiving (Even If You've Never Hosted Anything)",
        linktree="How to Host a Friendsgiving",
        hashtags="#FoundHerTribe #FindYourPeople #Friendsgiving #HostingMadeEasy #UtahWomen #SaltLakeCity #UtahCounty",
        caption=("The first rule of hosting a Friendsgiving: nobody is grading the turkey.\n\n"
                 "You don't need a big table, matching plates or a long friend list. Everyone pitches in, which makes it the friendliest possible first party.\n\n"
                 "Our guide has a simple planning timeline, a potluck sign-up system that actually works, budget tips, themes and conversation starters for when the table goes quiet.\n\n"
                 "Pick a date, invite someone newer to your life, and read the guide, link in bio.\n\n"
                 "Where you find your people."),
        spec=reel("rose", "Lifestyle", "photo-1613109040830-ffdd96756f5e",
                  ["The first rule", "of Friendsgiving:", "*nobody is grading", "*the turkey."],
                  ["Everyone pitches in.", "*That's the point."],
                  "The friendliest possible first party.",
                  bullets("KEEP THE POTLUCK SIMPLE",
                          "You make the main. Everyone signs up for the rest.",
                          "Set categories with limited spots, so you don't get seven trays of rolls.",
                          "A dry or alcohol-optional table is completely normal."),
                  ["Invite the coworker", "you always chat with.", "*Most people", "*are flattered."],
                  "Give her a dish to bring. It's oddly comforting.",
                  "How to Host a Friendsgiving (Even If You've Never Hosted Anything)",
                  "A simple timeline, a potluck system that works, and what to say when the table goes quiet.", hook_size=96)),
    "2026-11-21-article": dict(
        slug="winter-things-to-do-utah-county",
        title="Winter Things to Do in Utah County With Friends",
        linktree="Winter Things to Do in Utah County With Friends",
        hashtags="#FoundHerTribe #FindYourPeople #UtahCounty #UtahWinter #ProvoUtah #LehiUtah #UtahWomen",
        caption=("The fix for a long Utah County winter isn't a new candle. It's a plan with other people on the calendar.\n\n"
                 "Our guide rounds up the best things to do with friends this winter: snowshoe trails at Sundance, skating at Peaks Ice Arena, bouldering in Lehi, the Thanksgiving Point museums, and one very warm crater in Midway.\n\n"
                 "It includes honest notes on drive times, safety and what to book ahead.\n\n"
                 "Pick one outing a month and put a date on it. Read the guide, link in bio.\n\n"
                 "Where you find your people."),
        spec=reel("terracotta", "Lifestyle", "photo-1485101015172-b439ab658bb7",
                  ["The fix for a long", "Utah County winter", "*isn't a new candle."],
                  ["It's a plan with", "*people on the calendar."],
                  "Snowshoe trails, skating rinks, museums and one very warm cave.",
                  pills("WINTER, INDOORS AND OUT",
                        ["Snowshoe at Sundance", "Skate at Peaks", "Boulder at Momentum", "Thanksgiving Point", "Utah Lake sunset", "Homestead Crater"],
                        "Check each venue for hours before you go."),
                  ["Make it a series.", "*One outing a month", "*through March."],
                  "\"We should go sometime\" never happens. \"Saturday at 2\" does.",
                  "Winter Things to Do in Utah County With Friends",
                  "Indoors and out, with honest notes on drive times, safety and what to book ahead.", hook_size=88)),
    "2026-12-01-article": dict(
        slug="utah-holiday-lights",
        title="Utah Christmas Lights 2026: The Best Holiday Light Displays for a Girls' Night",
        linktree="Utah Christmas Lights 2026 for a Girls' Night",
        hashtags="#FoundHerTribe #FindYourPeople #UtahChristmasLights #Luminaria #GirlsNightOut #SaltLakeCity #UtahCounty",
        caption=("Christmas lights hit different when you see them with friends.\n\n"
                 "Our guide covers the holiday light displays along the Wasatch Front worth bundling up for, from Luminaria in Lehi and Temple Square to Christmas in Color, Spanish Fork's Festival of Lights and Ogden's Christmas Village.\n\n"
                 "Plus how to turn it into a girls' night: buy timed tickets early, book a fire pit if there are four or more of you, and plan dinner before, not after.\n\n"
                 "Pick your night and text the group chat. Read the guide, link in bio.\n\n"
                 "Where you find your people."),
        spec=reel("sage", "Lifestyle", "photo-1668454367715-b92fee293fe6",
                  ["Christmas lights", "hit different", "*with friends."],
                  ["Hot cocoa in one hand.", "*A friend in a snowbank."],
                  "The lights are the excuse. The people are the point.",
                  pills("WORTH BUNDLING UP FOR",
                        ["Luminaria, Lehi", "Temple Square", "ZooLights", "Candlelight Christmas", "Christmas in Color", "Spanish Fork Festival of Lights", "Ogden's Christmas Village"],
                        "Some sell timed tickets, so book weekends early."),
                  ["Plan dinner before,", "*not after."],
                  "Everyone is more patient at 5 p.m. than at 9 p.m. in the cold.",
                  "Utah Christmas Lights 2026: The Best Holiday Light Displays for a Girls' Night",
                  "Dates, tickets and how to turn the lights into a night out with friends.", hook_size=100)),
    "2026-12-12-article": dict(
        slug="lonely-during-the-holidays",
        title="Feeling Lonely During the Holidays? You're Not the Only One",
        linktree="Feeling Lonely During the Holidays?",
        hashtags="#FoundHerTribe #FindYourPeople #HolidayLoneliness #YouAreNotAlone #UtahWomen #SaltLakeCity #UtahCounty",
        caption=("If you feel lonely during the holidays, nothing is wrong with you. You're in very good company.\n\n"
                 "The season turns the volume up: new to Utah, grieving, newly divorced, friendships that drifted, family that's complicated. None of it makes you less lovable.\n\n"
                 "Our guide shares small, kind things to try this week: say yes to one invitation, send three texts, host an orphans' dinner, or volunteer somewhere.\n\n"
                 "Read the guide, link in bio. And if you're in crisis, call or text 988, any time.\n\n"
                 "This is general information, not medical advice.\n\n"
                 "Where you find your people."),
        spec=reel("rose", "Mental Health", "photo-1658279366796-e0c28623cd27",
                  ["If you feel lonely", "this season,", "*nothing is wrong", "*with you."],
                  ["You're in very", "*good company."],
                  "In a 2025 poll, 48% of adults were worried about missing someone or grief.",
                  bullets("SMALL THINGS FOR THIS WEEK",
                          "Say yes to one invitation. You can stay 45 minutes.",
                          "Send three texts.",
                          "Host an orphans' dinner.",
                          "Volunteer somewhere."),
                  ["Feeling lonely", "is not a verdict.", "*It's a signal you", "*need connection."],
                  "In crisis? Call or text 988, any time.",
                  "Feeling Lonely During the Holidays? You're Not the Only One",
                  "Why the season stings, and small, kind things you can do about it this week.", hook_size=88)),
}


def main():
    posts_path = ROOT / "data" / "posts.json"
    data = json.loads(posts_path.read_text())
    by_id = {p["id"]: p for p in data["posts"]}
    for pid, info in POSTS.items():
        spec = info["spec"]
        for sc in spec["scenes"]:
            for it in sc["items"]:
                if it.get("src") == "PHOTO":
                    it["src"] = f"tools/reels/photos/{pid}.jpg"
        (ROOT / "tools" / "reels" / "specs" / f"{pid}.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False))
        all_text = json.dumps(spec, ensure_ascii=False) + info["caption"]
        assert "—" not in all_text, f"em dash in {pid}"
        p = by_id[pid]
        p.update({
            "status": "draft",
            "title": info["title"],
            "caption": info["caption"],
            "hashtags": info["hashtags"],
            "links": links(info["slug"]),
            "linktreeTitle": info["linktree"],
            "notes": "Article checked live on 14 Oct 2026. Photo: the article's own Unsplash hero image. Reel is silent; add music in Instagram.",
        })
        if not p.get("asset"):
            p["assetNote"] = "Reel written. Rendering once the photo is downloaded."
        assert 5 <= len(info["hashtags"].split()) <= 7
    data["updatedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    posts_path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print("updated", len(POSTS), "posts and specs")


if __name__ == "__main__":
    main()
