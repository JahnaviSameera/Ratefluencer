# Ratefluencer — Track 2

AI-powered viral content generation pipeline for short-form creators.

## Structure

```
track2/
├── backend/          Python pipeline + FastAPI server
│   ├── api_server.py         Main server — run this
│   ├── trend_agent.py        Real-time trend discovery (HN + Google News)
│   ├── script_generator.py   Gemini-powered reel + LinkedIn + Instagram scripts
│   ├── caption_trainer.py    Few-shot selector + caption ranker
│   ├── virality_model.py     XGBoost virality prediction (25 features)
│   ├── scorer.py             TF-IDF + sentence-transformer quality scoring
│   ├── feedback_store.py     Real engagement feedback loop
│   ├── REEL_GENERATOR.py     MP4 reel production (TTS + images + captions)
│   ├── social_poster.py      Instagram + LinkedIn direct posting
│   ├── train_from_instagram.py  Train model on Instagram dataset
│   └── .env                  API keys (GEMINI_API_KEY etc.)
│
└── frontend/         React dashboard (CDN-based, no build step)
    ├── index.html
    ├── app.jsx       Pipeline orchestration + state
    ├── sections.jsx  Trends / Scripts / Virality sections
    ├── components.jsx Shared UI components
    ├── logic.js      API calls + virality scoring
    └── styles.css    Dark theme design system
```

## Run

```bash
cd backend
python api_server.py
```

Open **http://localhost:8000**
