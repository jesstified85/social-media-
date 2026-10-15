# FoundHer Content Calendar

A month view of FoundHer Tribe's planned social posts. Click a day to download that day's asset and copy its caption, hashtags and tagged links for Instagram and Facebook.

This is a static site (no build step) meant to be hosted on Vercel. Anyone with the link can open it, so keep the link within the team.

## Files

- `index.html`, `styles.css`, `app.js`: the calendar page.
- `data/posts.json`: every post (date, type, status, title, caption, hashtags, links, Linktree title, asset path).
- `assets/`: the videos and images to post, named `YYYY-MM-DD-type.mp4` (or `.png`/`.jpg`).
- `scripts/build_posts.py`: rebuilds `data/posts.json` from exported post records.
- `vercel.json`: keeps the site out of search engines and stops browsers caching the posts list.

## How it gets updated

Claude (in the "Social Media Marketing FoundHer" project) maintains the posts. When a post changes, Claude updates `data/posts.json`, adds any new asset to `assets/`, and pushes to `main`. Vercel republishes automatically.

A post record looks like this:

```json
{
  "id": "2026-10-20-article",
  "date": "2026-10-20",
  "type": "article",
  "status": "draft",
  "title": "Girls' Night Ideas in Salt Lake City and Utah County",
  "caption": "...",
  "hashtags": "#FoundHerTribe #FindYourPeople ...",
  "links": { "instagram": "https://...", "facebook": "https://..." },
  "linktreeTitle": "...",
  "asset": "assets/2026-10-20-article.mp4"
}
```

`type` is `event`, `article`, `auction` or `recap`. `status` is `placeholder`, `draft`, `review` (ready for Jess), `approved` (approved by Jess) or `posted`.

## Deploying on Vercel (one time)

1. In Vercel, choose **Add New → Project** and import `jesstified85/social-media-`.
2. Leave Framework Preset as **Other**, with no build command and no output directory.
3. Click **Deploy**. Every push to `main` then redeploys the site.
