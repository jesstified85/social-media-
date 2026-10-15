# Article Reel maker

Renders FoundHer article Reels in the approved reference style: 1080x1920, 30 fps,
16.5 s, silent MP4, headline on the first frame, all text inside the 4:5 centre crop,
cream end card with the logo, "READ IT IN THE APP" and "Where you find your people."

```
python3 tools/reels/render_reel.py tools/reels/specs/2026-10-20-article.json assets/2026-10-20-article.mp4
```

- `specs/`: one JSON per Reel (theme, category label, scenes, end card). Copy one to start a new Reel.
  Themes: `terracotta` (cream text) and `sage` (charcoal text).
- `plates/`: background colour + pin-heart watermark, label pin and logo, taken from the team's own
  reference Reels. Do not redraw these. A rose or coral plate needs a reference frame on that colour.
- `fonts/`: Playfair Display and Montserrat (SIL Open Font License). Above the Sky is not included;
  the script accent uses Playfair Display Italic, as the reference Reels do.

Text rules: only words that come from the article, second person, no em dashes.
