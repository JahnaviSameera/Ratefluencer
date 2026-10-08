# RATEFLUENCER AI — PPT Content Guide
### AI Hackathon Submission — Track 1 + Track 2 (Unified)

---

---

# SLIDE 1 — TITLE SLIDE

**RATEFLUENCER AI**
*The Autonomous Influencer-Marketing Brain*

- Two tracks. One product. One server.
- Built for the AI Hackathon
- Team: Sourabh Kumar

**Tagline:** From trend signal → right creator → viral content → in one platform.

---

# SLIDE 2 — THE PROBLEM

### Why Influencer Marketing Is Broken

| Pain Point | Reality |
|---|---|
| Who is real? | 30–50% of "influence" is bots and bought followers |
| Who fits my brand? | Niche tags are too coarse — same niche, wrong voice |
| Will this content go viral? | Creators guess and burn effort on content that never lands |
| How do I run the campaign? | Brief → shortlist → compare → budget → outreach is all manual |

**Brands waste billions because none of these questions have fast, data-driven answers.**

---

# SLIDE 3 — OUR SOLUTION (ONE LINE PER POINT)

### Ratefluencer AI answers all of them — automatically

- **Track 1 — Influencer Intelligence Engine**
  Scores 5,364 influencers, detects fake followers, predicts growth, matches brands by voice, runs full campaigns autonomously

- **Track 2 — Viral Content Creator Agent**
  Detects real trending topics before they peak, writes multi-platform scripts, predicts virality score before you post

- **One unified server** — `python app.py` → both tracks live at port 8000

---

# SLIDE 4 — SYSTEM ARCHITECTURE

```
DATA SOURCES
├── YouTube Data API v3     → 364 real influencer profiles
├── HuggingFace IG Dataset  → 5,000 real Instagram captions
├── HN Algolia API          → real-time trending articles
├── Google News RSS         → real-time news articles
└── Pexels API              → visual content fallback

ML LAYER
├── Track 1: 4 ML models (XGBoost ensemble, Auth, Growth, Brand Match)
└── Track 2: Trend engine (5-signal) + Virality model (25 features)

AI AGENT LAYER
└── 8 Gemini Agents (gemini-3.1-flash-lite-preview)

UNIFIED SERVER
└── FastAPI + uvicorn on port 8000
    ├── APScheduler → trend scan every 60 minutes (autonomous)
    ├── http://localhost:8000       → Track 1 frontend
    └── http://localhost:8000/creator → Track 2 frontend
```

---

# SLIDE 5 — TECH STACK

### AI / ML
| Technology | What We Use It For |
|---|---|
| XGBoost | Ratefluencer score, virality, authenticity, growth |
| LightGBM + CatBoost | Ensemble members for Ratefluencer score |
| Sentence-Transformers (all-MiniLM-L6-v2, 384-dim) | Semantic brand matching + hook similarity |
| Random Forest + Ridge + MLP | Benchmark comparison models |
| TextBlob | Sentiment scoring |
| Scikit-learn | Pipeline, hyperparameter search, cross-validation |

### AI APIs
| API | What We Use It For |
|---|---|
| Gemini 3.1 Flash Lite Preview | All 8 AI agents + script generation |
| Imagen 4 Fast | AI post image generation |
| edge-tts (Microsoft) | Free neural TTS voiceover for reels |
| YouTube Data API v3 | Scraping real channel data |
| Pexels API | Stock images fallback |

### Platform
- **Backend:** FastAPI, APScheduler, python-dotenv, uvicorn
- **Frontend:** React 18.3.1 (CDN, no build step), Babel in-browser transpilation

---

# SLIDE 6 — TRACK 1 OVERVIEW

## Track 1: Influencer Intelligence Engine

**What it does:**
- Takes a brand's campaign brief (rough text)
- Finds the most suitable influencers from 5,364 profiles
- Detects fake followers, predicts future growth
- Compares candidates, estimates budget & ROI
- Writes personalized outreach emails
- All in one click via `/api/run-campaign`

**Dataset:** 5,364 influencer profiles across 20 niches
(364 real YouTube channels + 5,000 synthetic profiles)

**20 Niches covered:**
Fitness, Health & Wellness, Yoga, Nutrition, Fashion, Beauty, Lifestyle,
Parenting, Travel, Food, Home Decor, DIY, Technology, Gaming, Finance,
Entrepreneurship, Sports, Mental Health, Music, Comedy

---

# SLIDE 7 — TRACK 1 WORKFLOW (8 STEPS)

```
Brand enters rough campaign brief
        ↓
Step 1: Brief Optimizer Agent (Gemini)
        Raw brief → refined brief, ranked niches, ideal persona, content angle
        ↓
Step 2: Semantic Search (Sentence-Transformers, 384-dim)
        Finds influencers whose actual content matches brand voice
        ↓
Step 3: ML Ranking (XGBoost Ensemble)
        Scores all candidates → brand_match × quality_index
        ↓
Step 4: Results
        Ranked influencer list + Ratefluencer scores + match reasons
        ↓
Step 5: Deep Profile Analysis
        Live authenticity score + growth trajectory for selected influencer
        ↓
Step 6: Compare Agent (Gemini)
        Side-by-side comparison of 2–3 finalists → picks winner
        ↓
Step 7: Budget & ROI Agent (ML + Gemini)
        Allocates spend, projects reach/conversions/ROI
        ↓
Step 8: Outreach Email Agent (Gemini)
        Personalized email referencing creator's actual content
```

---

# SLIDE 8 — THE RATEFLUENCER SCORE (MASTER ML MODEL)

### 6 Models Benchmarked — Ensemble Ships

| Model | MAE ↓ | R² ↑ |
|---|---|---|
| Ridge (linear baseline) | 2.40 | 0.815 |
| Random Forest | 2.54 | 0.860 |
| XGBoost | 1.54 | 0.872 |
| LightGBM | 1.62 | 0.870 |
| CatBoost | 1.57 | 0.889 |
| Neural Net (MLP 128-64-32) | 1.94 | 0.852 |
| **Voting Ensemble (3:2:1)** | **1.51** | **0.878** |

**Ensemble blends XGBoost + LightGBM + CatBoost at weights 3:2:1**
Only ships if it beats every standalone model — it does.

### 24 Features (16 base + 8 interaction cross-terms)
- Engagement: `true_engagement_rate`, `er_vs_expected`, `engagement_depth`
- Audience quality: `authenticity_score`, `real_followers_pct`, `bot_follower_pct`
- Growth: `growth_score`, `growth_rate_30d/90d`, `momentum_score`
- Interaction terms: `auth × engagement`, `growth × er`, `campaign × auth` (multiplicative)
- Campaign signals: `campaign_success_prob`, `sponsored_er_drop`, `collab_frequency`

---

# SLIDE 9 — FAKE DETECTION (AUTHENTICITY MODEL)

### XGBoost Binary Classifier with Platt Scaling

**The problem it solves:** Is this influencer's audience real or bought?

**13 input features:**
- `real_followers_pct` — % genuine human followers
- `bot_follower_pct` — % confirmed bots
- `comment_spam_ratio` — % "Nice! 🔥" / generic comments
- `unique_commenters_ratio` — unique commenters ÷ total comments
- `spike_ratio` — max single-day gain ÷ avg daily gain
- `avg_comment_length` — bots leave very short comments
- `follower_following_ratio` — bots follow everyone
- `posting_regularity` — erratic schedule = suspicious
- `gemini_comment_quality` — Gemini reads real comments → quality score

**Output:**
- `fake_probability` → `authenticity_score = (1 - fake_prob) × 100`
- ≥75 = ✅ Authentic | 45–74 = ⚠️ Suspicious | <45 = 🚨 Fake

**Why XGBoost over Isolation Forest:**
Isolation Forest is unsupervised — it flags any outlier.
XGBoost is trained on labeled fake/real profiles — it learns the specific patterns of bot farms, engagement pods, and bought followers.

---

# SLIDE 10 — GROWTH PREDICTOR MODEL

### XGBoost Regressor — 5 Engineered Features

**The problem it solves:** Is this creator growing or plateauing?

**5 key engineered signals (derived, not raw counts):**

| Feature | Formula | Meaning |
|---|---|---|
| `momentum_score` | `(7d×3 + 30d×2 + 90d×1) / 6` | Recent growth weighted 3× more |
| `trend_acceleration` | `growth_30d − growth_90d` | Positive = accelerating |
| `content_velocity` | `posts_per_week × (1 + eng_trend)` | Posting more + more engaged |
| `er_stability` | `1 − (posting_std / engagement_rate)` | Consistent = sustainable |
| `viral_coefficient` | `max_day_gain / avg_daily_growth` | How big was their biggest spike |

**Output:** Growth score 0–100 + follower projections at 30 / 60 / 90 days

---

# SLIDE 11 — SEMANTIC BRAND MATCHING

### Sentence-Transformers — Beyond Keywords

**Old way (TF-IDF):** "fitness" ≠ "health" — word overlap only
**New way (Embeddings):** "fitness" ≈ "health" ≈ "wellness" ≈ "workout" — semantic meaning in 384-dim space

**How it works:**

1. Build influencer profile text:
   - bio (2×), actual captions (2×), niche description, hashtags, past brands

2. Build brand brief text:
   - product description (3×), campaign goal keywords, target audience

3. Cosine similarity in 384 dimensions → semantic match score (0–1)

4. Add structured bonuses:
   - +0.05 exact niche match
   - +0.15 audience age group alignment
   - +0.05 country match
   - −0.10 penalty for high collab frequency (overexposed creator)

5. Final ranking:
   - `rank_score = brand_match × (0.35 + 0.65 × quality_index)`
   - quality_index = auth × 0.55 + ratefluencer × 0.45
   - **A fake influencer with perfect niche match still loses to a genuine one**

---

# SLIDE 12 — THE 8 GEMINI AI AGENTS

| # | Agent | What It Does |
|---|---|---|
| 1 | **Brief Optimizer** | Turns vague brief into targeted strategy with ranked niches & ideal persona |
| 2 | **Outreach Generator** | Personalized email referencing creator's actual content |
| 3 | **Content-Fit Analyzer** | Scores voice & values alignment beyond just niche tags |
| 4 | **Brand-Safety Checker** | Flags controversy, competitor ties, fake signals before contract |
| 5 | **Competitor Intel** | Reverse-engineers rival strategies, finds untapped niches |
| 6 | **Compare Influencers** | Side-by-side winner declaration with axis-by-axis reasoning |
| 7 | **Budget/ROI Estimator** | ML allocates spend by cost-efficiency; Gemini adds strategy + tips |
| 8 | **Script Generator** | Full content kit: reel + LinkedIn + Instagram + Thumbnail |

All agents: **Gemini 3.1 Flash Lite Preview** via REST API
Temperature: 0.3 for data, 0.7 for creative content
Response format: JSON mode for structured output

---

# SLIDE 13 — TRACK 2 OVERVIEW

## Track 2: AI Viral Content Creator Agent

**What it does:**
- Discovers what's trending RIGHT NOW from live internet data
- Ranks trends by mathematical signals (not guessing)
- Generates complete multi-platform content kit (Reel + LinkedIn + Instagram)
- Predicts virality score BEFORE you post
- Produces actual MP4 video with voiceover

**Two inputs, full output:**
1. User selects a niche (AI, finance, creator economy, etc.)
2. Clicks Generate
3. Gets: trending topic + script + social copy + virality prediction + post image

---

# SLIDE 14 — TRACK 2 WORKFLOW (7 STEPS)

```
User selects niche
        ↓
Step 1: Trend Discovery
        Scrapes HN Algolia + Google News RSS
        12 queries per niche × 2 sources = ~200 articles per run
        ↓
Step 2: 5-Signal ML Ranking
        Counts mentions in 3 time windows (t0=48-72h, t1=24-48h, t2=0-24h)
        Derives: velocity, acceleration, novelty, volume, sustained
        Score = weighted tanh combination → 0 to 100
        ↓
Step 3: Gemini Enrichment
        Adds why_trending, content_angle, target_audience, urgency
        NEVER touches the numeric score — pure annotation
        ↓
Step 4: Script Generation (Gemini)
        Hook + Story + Insights + CTA
        + LinkedIn post + Instagram caption + Thumbnail text
        ↓
Step 5: Best-of-3 Ranker
        Generates 3 script variants → XGBoost scores each → returns winner
        ↓
Step 6: Virality Prediction (XGBoost, 25 features)
        Score 0–100 + confidence band + top driving factors
        + Predicted views, likes, shares, saves
        ↓
Step 7: Reel Production
        edge-tts voiceover + Pexels/Imagen images + MoviePy → MP4
```

---

# SLIDE 15 — TREND SCORING MATH

### 5 Signals, 3 Time Windows, 1 Score

**Time windows from scraped articles:**
- `t0` = mentions 48–72 hours ago (oldest)
- `t1` = mentions 24–48 hours ago (middle)
- `t2` = mentions 0–24 hours ago (newest)

**5 computed signals:**

| Signal | Formula | What it captures |
|---|---|---|
| Velocity | `(t2 − t0) / 2` | Speed of growth |
| Acceleration | `t2 − 2×t1 + t0` | 2nd derivative — is growth speeding UP? |
| Volume | `t0 + t1 + t2` | Total buzz size |
| Novelty | `t2 / volume` | How recent-heavy the buzz is |
| Sustained | `0 / 0.4 / 0.8 / 1.0` | Active in 0/1/2/3 windows |

**Final score formula:**
```
raw = 0.35×tanh(accel/5) + 0.25×tanh(vel/5) + 0.20×novelty
    + 0.10×tanh(log(1+vol)/5) + 0.10×sustained

score = (raw + 1) × 50     →    maps to [0, 100]
```

**Why tanh?** Compresses outliers — 3 mentions vs 300 shouldn't score 100× differently.
**Why additive?** Earlier multiplicative formula zeroed out single-window breakouts. Now a viral spike that appears in only 1 window still gets scored.

**Acceleration is weighted highest (35%)** because a trend speeding up NOW is more valuable than one that peaked 3 days ago.

---

# SLIDE 16 — VIRALITY PREDICTION MODEL

### XGBoost + 25 Features + Platt Calibration

**Training:** 15,000 synthetic samples with non-linear ground truth
**Tuning:** RandomizedSearchCV over 8 hyperparameters, 5-fold CV
**Calibration:** Platt scaling — scores map to real engagement probability

**25 features across 4 groups:**

**Text Quality (11 features)**
- Hook length: ideal = 12 words, bell curve scoring
- Hook power words: "secret", "revealed", "nobody", "shocking" etc.
- Hook semantic similarity: cosine similarity to corpus of 2,000 proven viral headlines
- Story specificity: numbers / $ amounts / proper names in body
- CTA strength: contains follow/comment/share/save
- Sentiment, question flag, number flag

**Trend Signals (4 features)**
- `trend_score` (0–100), `trend_urgency` (breaking=1.0, rising=0.67, established=0.33)
- `trend_acceleration`, `niche_virality_baseline`

**Platform Signals (4 features)**
- Caption length: ideal = 50 words (Gaussian bell)
- Hashtag count: ideal = 11 tags
- LinkedIn length: ideal = 175 words
- Thumbnail title length: ideal = 5 words

**Linguistic (6 features)**
- Sentiment compound, exclamation count, content angle power words
- Sentence count, avg word length (shorter = better), emoji presence

**Output:**
- Virality score 0–100
- Predicted views / likes / shares / saves
- Top 5 driving factors with importances
- Confidence level (high/medium/low)

---

# SLIDE 17 — HOOK SEMANTIC SIMILARITY (KEY INNOVATION)

### Measuring How "Viral" a Hook Sounds

**The idea:** Compare the hook to a corpus of 2,000 proven viral headlines using sentence embeddings

**The corpus (3 layers, priority order):**
1. Real Instagram captions from HuggingFace dataset (most valuable)
2. Today's live scraped trend headlines
3. 20 hardcoded proven viral hooks as fallback

**The math:**
```
hook_embedding    = SentenceTransformer.encode(hook)         # 384-dim vector
corpus_embeddings = encode(all 2000 viral headlines)         # 2000 × 384 matrix

similarity = max(hook_embedding · corpus_embeddings.T)       # cosine sim
```

**Example:**
- Hook: "AI agents just made chatbots obsolete. Here's why." → similarity = 0.71 (high)
- Hook: "Here is my video about artificial intelligence" → similarity = 0.31 (low)

**Why this matters:** It's the only feature that measures whether the hook SOUNDS like content that already went viral — not just whether it has the right keywords.

---

# SLIDE 18 — DATA SOURCES (HONEST BREAKDOWN)

### What's Real vs Estimated

**Truly Real Data (from YouTube Data API v3):**
- Subscriber count, total views, video count
- Per-video: likes, comments, view count
- Channel description (bio), video titles, tags
- Engagement rate calculated from actual video stats

**Computed from Real Data:**
- `posting_std_dev` = std(days between video publish dates)
- `spike_ratio` = max(video views) / mean(video views)
- `comment_spam_ratio` = fraction of "Nice! / Great post! / 🔥🔥🔥" comments
- `unique_commenters_ratio` = unique author IDs / total comments
- `bio_completeness_score` = min(len(description) / 300, 1.0)

**Intelligently Estimated (no public API gives this):**
- `bot_follower_pct` — derived as proxy from spam ratio + spike ratio + ER anomaly
- `growth_rate_30d` — YouTube doesn't give subscriber history → estimated from view trend
- `audience_age_group` — requires creator OAuth → not available publicly

**Real Instagram Captions:**
- HuggingFace dataset `kkcosmos/instagram-images-with-captions`
- 5,000 real captions embedded and clustered to 20 niches
- Used for brand match embeddings — actual posted content, not fake text

---

# SLIDE 19 — THE AUTONOMOUS LOOP (GRAND CHALLENGE)

### Both Tracks Connected Into One Self-Driving Engine

```
Every 60 minutes (APScheduler, no human trigger):
        ↓
Trend scan fires automatically across 4 niches
(AI, creator economy, technology, finance)
        ↓
Score ≥ 82 → "Breaking" alert saved to alerts.json
        ↓
Alert bell 🔔 lights up in Track 1 dashboard
        ↓
Brand clicks: "Find influencers for this trend"
        ↓
Track 1 auto-searches → ranked creators returned
        ↓
Brand picks top creator → "Generate Content" button
        ↓
Track 2 generates content for exactly that niche
        ↓
Virality predicted → content approved → reel produced
        ↓
✅ COMPLETE: trend signal → right creator → viral content
```

**This loop runs without any human input after initial setup.**

---

# SLIDE 20 — API ENDPOINTS (17 TOTAL)

### Key Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /search` | Brand brief → ML-ranked influencers |
| `POST /api/run-campaign` | **Full autonomous pipeline in one call** |
| `GET /influencers/{id}` | Deep profile with live auth + growth |
| `POST /api/optimize-brief` | Gemini refines rough brief |
| `POST /api/compare` | Side-by-side comparison of candidates |
| `POST /api/budget-estimate` | Budget allocation + ROI projection |
| `POST /api/outreach` | Personalized outreach email |
| `GET /api/alerts` | Real-time trend alert feed |
| `POST /api/trends` | Discover live trending topics |
| `POST /api/scripts` | Generate full content kit |
| `POST /api/virality` | Predict virality before posting |
| `POST /api/generate-image` | AI image for Instagram post |
| `GET /docs` | Full Swagger API documentation |

---

# SLIDE 21 — FRONTEND (TWO DASHBOARDS)

### Track 1 Frontend — Influencer Intelligence Dashboard
- Built in React 18.3.1 (CDN, no build step required)
- Dark theme with custom CSS properties
- **Search panel:** niche filter + campaign brief input
- **Results cards:** Ratefluencer score, tier badge, ER, match reasons, DiceBear avatar
- **Profile modal:** Auth breakdown, growth chart (Recharts), 13-feature breakdown
- **Compare modal:** Side-by-side table + Gemini winner declaration
- **Budget panel:** Spend allocation + ROI + conversion projections
- **Alert bell 🔔:** Real-time breaking trend notifications
- **"Real Creator Agent" button:** Direct link to Track 2

### Track 2 Frontend — Content Creator Studio
- Niche dropdown (6 options) + API key input
- Pipeline status bar: Trend Discovery → Script Generation → Virality → Package
- **Trend cards:** Score bar, urgency badge, velocity/acceleration stats
- **Script cards:** Tabbed view (Reel / LinkedIn / Instagram / Thumbnail)
- **Virality dial:** Circular SVG gauge + predicted engagement metrics
- **Generate Image button:** Imagen 4 → Gemini → Pexels fallback chain
- **LinkedIn preview:** Mock LinkedIn post UI
- **Instagram preview:** Mock Instagram post UI with image

---

# SLIDE 22 — NUMBERS THAT MATTER

| Metric | Number |
|---|---|
| Influencer profiles in dataset | 5,364 |
| Real YouTube channels scraped | 364 |
| Real Instagram captions used | 5,000 |
| ML models trained & benchmarked | 6 + 1 ensemble |
| Ratefluencer Score MAE | 1.51 (out of 100) |
| Ratefluencer Score R² | 0.878 |
| Features in Ratefluencer model | 24 (16 base + 8 interactions) |
| Virality model features | 25 |
| Virality training samples | 15,000 |
| Gemini AI agents | 8 |
| Trend scoring signals | 5 |
| Niche query sets per trend scan | 6 niches × 12 queries |
| API endpoints | 17 |
| Niches covered | 20 |
| Script variants generated per trend | 3 (Best-of-3 ranker picks winner) |
| Autonomous scan frequency | Every 60 minutes |
| Server ports needed to run | 1 (port 8000) |

---

# SLIDE 23 — BUSINESS IMPACT

### What This Saves / Creates

**Cost savings:**
- Authenticity model stops budget flowing to fake accounts BEFORE signing
- Brand-Safety agent flags risks before contracts are signed
- Budget/ROI estimator quantifies spend efficiency before committing

**Time savings:**
- `/api/run-campaign` collapses days of manual work into one API call
- Brief → shortlist → compare → budget → outreach: ~60 seconds vs 2–3 days

**Revenue improvement:**
- Semantic brand match finds the right voice, not just the right niche
- Virality prediction + Best-of-3 means better content, scored before money is spent
- Trend alerts surface opportunities before competitors react

**Quantification:**
Every budget recommendation includes:
- Projected reach (views/impressions)
- Projected conversions (at ₹500 AOV assumption)
- ROI multiplier
- Strategic rationale from Gemini

---

# SLIDE 24 — HACKATHON JUDGING CRITERIA

| Criteria | Points | How We Earn It |
|---|---|---|
| AI/ML Innovation | 20 | Sentence-transformer brand match, 5-signal trend ML, 8 Gemini agents, real-data training, hook semantic similarity to viral corpus |
| Influencer Scoring Accuracy | 20 | 6 models benchmarked, ensemble winner MAE 1.51 / R² 0.878, 24 features, real YouTube + HuggingFace data |
| Viral Prediction | 15 | XGBoost virality model (25 features, Platt-calibrated, confidence band), hook semantic similarity, Best-of-3 ranker |
| Automation & Agent Design | 15 | 8 Gemini agents, autonomous APScheduler scan every 60 min, full `/api/run-campaign` pipeline |
| Product Design & UX | 10 | Dark dashboard, alert bell, compare modal, budget panel, DiceBear avatars, Instagram/LinkedIn preview |
| Business Impact | 10 | Budget/ROI estimator, brand-safety gate, personalized outreach, real engagement metrics |
| Technical Complexity | 5 | Unified dual-track server, real scraping pipeline, model ensemble, semantic embeddings |
| Demo & Presentation | 5 | One clean flow: alert → search → compare → budget → outreach → generate content → score |

---

# SLIDE 25 — DEMO FLOW (FOR LIVE DEMO)

### The Story: Signal → Signed → Scored (7 steps)

1. **🔔 Alert fires** — APScheduler's hourly scan surfaces "AI agents" accelerating. Alert bell lights up in dashboard.

2. **🔍 Search** — Brand drops rough brief: *"launching AI productivity tool for Gen Z professionals"*. Brief Optimizer refines it. Semantic Brand Match + Ratefluencer Ensemble return ranked shortlist with match reasons.

3. **👤 Deep dive** — Open top influencer profile. See live authenticity score (92/100 ✅) + growth projection (↑ 47K followers in 90 days).

4. **⚖️ Compare** — Pick 3 finalists → Compare Agent declares winner + axis-by-axis breakdown. Brand-Safety clears all three.

5. **💰 Budget** — Budget/ROI Estimator allocates ₹2L spend, projects 4.2M reach, 8,400 conversions, 2.1× ROI.

6. **✉️ Outreach** — Outreach Generator drafts personalized email referencing creator's actual last 3 videos.

7. **🎬 Content (Track 2)** — Switch to /creator. Pick "artificial intelligence" niche. Generate → trend "AI agents" surfaces at 87/100. Script generated → Best-of-3 picks winner → Virality predicted at 74/100 🔥 High. LinkedIn + Instagram + Thumbnail ready.

**One platform: signal → signed creator → scored content.**

---

# SLIDE 26 — WHAT MAKES THIS DIFFERENT

### Key Differentiators vs Existing Tools

| Feature | Traditional Tools | Ratefluencer AI |
|---|---|---|
| Brand matching | Keyword/niche filter | 384-dim semantic embedding on actual content |
| Fake detection | Follower count thresholds | XGBoost on 13 signals including Gemini comment analysis |
| Trend discovery | Manual browsing | Live 5-signal ML scoring on 200+ real articles |
| Virality prediction | Gut feel / past data | XGBoost + hook cosine similarity to viral corpus |
| Campaign execution | Manual steps | One API call: brief → outreach |
| Content creation | Separate tool | Built-in, virality-scored before posting |
| Autonomy | Zero | Hourly trend scan, alert push, no human trigger needed |

---

# SLIDE 27 — TECHNICAL CHALLENGES SOLVED

1. **Unified server** — Two completely separate FastAPI apps merged into one uvicorn process. Track 1's catch-all `/{path}` route had to be filtered to prevent it intercepting `/creator`. Solved with route inspection at import time.

2. **Real-time trend detection** — Google News and HN APIs give noisy data. tanh normalization + 3-window time-series prevents viral outliers from dominating the score.

3. **Fake detection without private data** — Real `bot_follower_pct` requires third-party APIs. Built proxy from: spam comment ratio + spike ratio + ER vs benchmark + comment uniqueness.

4. **Semantic brand matching** — Plain niche matching gives wrong results. Two influencers in "Fitness" can have completely different voices. Product description repeated 3× in brand text + bio/captions repeated 2× in influencer text ensures direction is driven by actual content.

5. **Virality ground truth** — No labeled dataset of viral vs non-viral posts. Built non-linear synthetic ground truth with multiplicative interactions (hook_similarity × trend_score) to teach XGBoost that both signals must be simultaneously strong.

---

# SLIDE 28 — FUTURE ROADMAP

### What's Next (Already Architected)

- **Feedback loop:** `/api/feedback` endpoint already built — log real post performance, retrain virality model on actual outcomes. Self-improving.
- **Agent 7 (Missing):** Auto-negotiation agent — handles rate proposals and contract back-and-forth.
- **Real fraud data:** Replace synthetic authenticity training data with labeled fraud dataset from HypeAuditor or Modash.
- **Multi-platform:** TikTok Creator Marketplace API + X (Twitter) trending data.
- **Growth rate history:** Social Blade API integration for real 30/90-day growth curves instead of estimates.
- **Campaign close loop:** After outreach sent, track open rates → retrain outreach template model.

---

# SLIDE 29 — QUICK START (FOR JUDGES)

```bash
# 1. Install
pip install -r track1/backened/requirements.txt

# 2. Add Gemini key
# Create track2/backend/.env:
GEMINI_API_KEY=your_key_here
PEXELS_API_KEY=your_key_here

# 3. Run (one command, both tracks)
python app.py
```

**Open in browser:**
- `http://localhost:8000` — Track 1: Influencer Intelligence
- `http://localhost:8000/creator/` — Track 2: Content Creator
- `http://localhost:8000/docs` — API Documentation

**GitHub:** https://github.com/sourabh-03/news_generator

---

# SLIDE 30 — CLOSING SLIDE

## Ratefluencer AI

**The Autonomous Influencer-Marketing Brain**

From:  *"I need a creator for my AI tool launch"*
To:    *Signed creator + viral content + predicted ROI*
In:    *One platform, one command, one port*

---

**Built with:**
XGBoost · LightGBM · CatBoost · Sentence-Transformers · Gemini AI
FastAPI · React · YouTube API · Real Instagram Data · APScheduler

**Key numbers:**
- 5,364 influencer profiles · 6 ML models benchmarked · MAE 1.51
- 8 Gemini agents · 25-feature virality model · Hourly autonomous scan

---
*Thank you*

---

---

# APPENDIX — SLIDE-BY-SLIDE SUMMARY FOR PPT BUILDER

| Slide # | Title | Type |
|---|---|---|
| 1 | Title Slide | Title |
| 2 | The Problem | Problem |
| 3 | Our Solution | Solution overview |
| 4 | System Architecture | Architecture diagram |
| 5 | Tech Stack | Technology table |
| 6 | Track 1 Overview | Feature overview |
| 7 | Track 1 Workflow | Flow diagram |
| 8 | Ratefluencer Score | ML model table |
| 9 | Fake Detection | ML model detail |
| 10 | Growth Predictor | ML model detail |
| 11 | Semantic Brand Matching | Algorithm detail |
| 12 | 8 Gemini Agents | Agent table |
| 13 | Track 2 Overview | Feature overview |
| 14 | Track 2 Workflow | Flow diagram |
| 15 | Trend Scoring Math | Formula/math |
| 16 | Virality Prediction | ML model detail |
| 17 | Hook Semantic Similarity | Key innovation |
| 18 | Data Sources | Honest breakdown |
| 19 | Autonomous Loop | Grand challenge |
| 20 | API Endpoints | Technical reference |
| 21 | Frontend | UI description |
| 22 | Numbers That Matter | Key metrics |
| 23 | Business Impact | Business value |
| 24 | Judging Criteria | Scoring breakdown |
| 25 | Demo Flow | Live demo script |
| 26 | Differentiators | Competitive analysis |
| 27 | Technical Challenges | Engineering depth |
| 28 | Future Roadmap | Extensibility |
| 29 | Quick Start | For judges |
| 30 | Closing Slide | Thank you |
