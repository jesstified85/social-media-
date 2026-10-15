# Article Reel maker

Renders FoundHer article Reels in the approved reference style: 1080x1920, 30 fps,
16.5 s, silent MP4, headline on the first frame, all text inside the 4:5 centre crop,
cream end card with the logo, "READ IT IN THE APP" and "Where you find your people."

```
python3 tools/reels/render_reel.py tools/reels/specs/2026-10-20-article.json assets/2026-10-20-article.mp4
```

- `specs/`: one JSON per Reel (theme, category label, scenes, end card). Copy one to start a new Reel.
  Themes: `terracotta` (cream text), `sage` (charcoal text) and `rose` (charcoal text).
- `plates/`: background colour + pin-heart watermark, label pin and logo, taken from the team's own
  reference Reels. Do not redraw these. A coral plate needs a reference frame on that colour.
- `fonts/`: Playfair Display and Montserrat (SIL Open Font License). Above the Sky is not included;
  the script accent uses Playfair Display Italic, as the reference Reels do.

Photos: add `{"kind": "image", "src": "tools/reels/photos/<file>.jpg", "height": 620, "focus": 0.4}`
to a scene. It is cover-cropped into a rounded card the width of the text; `focus` moves the crop
up (0) or down (1). Use only photos FoundHer owns or has rights to (event photos, the article's own images).

Decoration (on by default): small hearts drift up through the lower corner, and on the end card a
cursor clicks READ IT IN THE APP. (A `{"kind": "swirl"}` item exists but Jess asked not to use swirls.) Turn off with `"decoration": false` or `"click": false` in the spec.

Text rules: only words that come from the article, second person, no em dashes.
