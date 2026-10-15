"""Build data/posts.json from a folder of exported post records.

Usage: python3 scripts/build_posts.py <export_dir>

<export_dir> holds one JSON file per post (as exported from the Claude content
calendar), named <YYYY-MM-DD>-<type>.json. Records are sorted by date.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED = {
    "date", "order", "type", "platform", "status", "title", "caption", "hashtags",
    "links", "linktreeTitle", "notes", "assetNote", "asset", "assetName", "assetType",
}


def main(export_dir: str) -> None:
    posts = []
    for f in sorted(Path(export_dir).glob("*.json")):
        rec = json.loads(f.read_text())
        rec = {k: v for k, v in rec.items() if k in ALLOWED}
        rec["id"] = f.stem
        posts.append(rec)
    posts.sort(key=lambda p: (p.get("date", ""), p.get("order", 0)))
    out = {"updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "posts": posts}
    dest = Path(__file__).resolve().parent.parent / "data" / "posts.json"
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"Wrote {len(posts)} posts to {dest}")


if __name__ == "__main__":
    main(sys.argv[1])
