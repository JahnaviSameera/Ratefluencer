# Ratefluencer — User Manual

AI-powered viral content generation pipeline. Discovers real trending topics, generates reel scripts, predicts virality, and produces ready-to-post MP4 reels.

---

## Quick Start (3 steps)

### 1. Install dependencies

```bash
pip install requests fastapi uvicorn python-dotenv scikit-learn xgboost sentence-transformers textblob numpy pillow moviepy==1.0.3 edge-tts gtts imageio-ffmpeg
```

### 2. Set your API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your free key at: https://aistudio.google.com/app/apikey

### 3. Run the server

```bash
python api_server.py
```

Open **http://localhost:8000** in your browser.

---

## What Each File Does

| File | Purpose |
|------|---------|
| `trend_agent.py` | Scrapes HN + Google News, ranks trends using 5 ML signals |
| `script_generator.py` | Generates reel scripts, LinkedIn posts, Instagram captions |
| `scorer.py` | TF-IDF + sentence-transformers script quality scoring |
| `virality_model.py` | XGBoost virality prediction with engagement estimates |
| `REEL_GENERATOR.py` | Produces MP4 reels with TTS voiceover and visuals |
| `api_server.py` | FastAPI backend — runs the full pipeline |
| `app/ai-generator-app/` | React frontend — the dashboard UI |

---

## Running Individual Scripts

### Discover Trends
```bash
python trend_agent.py "artificial intelligence"
# Output: trends_output.json
```

### Generate Scripts
```bash
python script_generator.py 3
# Reads trends_output.json, outputs scripts_output.json
```

### Predict Virality
```bash
python virality_model.py
# Reads scripts_output.json, outputs virality_output.json
```

### Produce Reels
```bash
python REEL_GENERATOR.py
# Reads scripts_output.json, outputs reels_output/*.mp4
```

### Score Scripts
```bash
python scorer.py
# Runs all 4 scoring tests
```

---

## Frontend Pipeline

The UI runs a 4-stage pipeline automatically:

1. **Trend Discovery** — Fetches real trending topics for your selected niche
2. **Script Generation** — Generates full content packages via Gemini
3. **Virality Prediction** — XGBoost scores each script (0–100)
4. **Content Package** — All assets ready to download/export

Click **Generate** — no API key needed in the UI (it reads from `.env`).

Click **View sample run** to see a demo without making any API calls.

---

## Supported Niches

- Artificial Intelligence
- Creator Economy
- Startups
- Finance
- Technology
- Business

---

## Output Files

| File | Contents |
|------|---------|
| `trends_output.json` | Top 10 trends with scores, signals, Gemini enrichment |
| `scripts_output.json` | Reel scripts, LinkedIn posts, Instagram captions, thumbnails |
| `virality_output.json` | Virality scores, predicted views/likes/shares/saves |
| `reels_output/reel_*.mp4` | Ready-to-post vertical MP4 reels |
| `reels_output/thumbnail_*.jpg` | Thumbnail images for each reel |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/trends` | Discover trends for a niche |
| POST | `/api/scripts` | Generate content packages |
| POST | `/api/virality` | Score scripts with XGBoost |
| POST | `/api/generate-image` | Generate Instagram post image |
| GET | `/health` | Server health check |

---

## Requirements

- Python 3.10+
- Gemini API key (free tier works — 500 RPD on gemini-3.1-flash-lite)
- Internet connection (for HN + Google News scraping)
- ffmpeg (auto-installed via `imageio-ffmpeg`)

---

## Troubleshooting

**Rate limit errors (429):** The script will auto-retry with 60s wait. You can also run `python trend_agent.py --no-gemini` to skip Gemini enrichment.

**`moviepy.editor` not found:** Run `pip install moviepy==1.0.3` (must be 1.x not 2.x).

**Encoding errors on Windows:** Set `PYTHONUTF8=1` before running, or the scripts handle it automatically.

**Port 8000 in use:** Kill the existing process or change the port in `api_server.py`.
