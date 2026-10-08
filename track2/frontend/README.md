# AI Generator — Viral Content Intelligence

A self-contained React dashboard that runs a content pipeline:
**Trend Discovery → Script Generation → Virality Prediction → Content Package**,
powered by the Google Gemini API.

## Files
- `index.html` — entry point (loads React, Babel, and the scripts below)
- `styles.css` — dark dashboard styling
- `logic.js` — Gemini API calls, prompts, virality scoring, sample data
- `components.jsx` — icons, top bar, pipeline bar, empty state, shared UI
- `sections.jsx` — Trends, Scripts (tabbed), Virality sections
- `app.jsx` — app state, pipeline orchestration, JSON export

## How to run in Visual Studio Code

The app loads the `.jsx` files in the browser, so it must be served by a local
web server — **opening `index.html` directly (double-click / file://) will NOT work.**

1. Open this folder in VS Code (`File → Open Folder`).
2. Install the **Live Server** extension (by Ritwick Dey) from the Extensions panel.
3. Right-click `index.html` → **"Open with Live Server"**.
4. Your browser opens at `http://127.0.0.1:5500` and the app runs.

### Alternative (no extension) — any static server
From a terminal inside this folder:

```bash
# Python 3
python -m http.server 5500

# or Node
npx serve .
```

Then open the URL it prints.

## Using the app
- **Sample run (no key):** click **"View sample run"** to populate the full
  dashboard with demo data — no API call.
- **Live run:** pick a niche, paste your **Gemini API key**, click **Generate**.
  Then **Export** downloads the full content package as JSON.

## Notes
- The Gemini model is set at the top of `logic.js`
  (`window.GEMINI_URL`, model `gemini-3.1-flash-lite-preview`). If a live run
  errors in the pipeline bar, confirm that model is available on your key, or
  change the model name there.
- An internet connection is required (React/Babel load from a CDN, and live
  runs call the Gemini API).
