<div align="center">

# 🚀 Ratefluencer AI

### *The Autonomous Influencer-Marketing Brain*

**One platform that finds the _right_ creators, predicts what will go viral, and runs the entire campaign — from brief to outreach email — with real ML models and a fleet of Gemini agents.**

</div>

---

> 🧩 **Two tracks. One product. One server.**
>
> | Track | Name | What it does |
> |:---:|:---|:---|
> | **1️⃣** | **Influencer Intelligence** | Scores influencers, detects fake followers, predicts growth, matches brands semantically, and autonomously runs campaigns. |
> | **2️⃣** | **Creator Content Engine** | Detects emerging trends _before_ they peak, generates multi-platform content, and predicts virality before you post. |
>
> ⚡ Both tracks run as **one unified FastAPI server on port `8000`**.

---

## 🎯 The Problem

Brands waste **billions** on influencer marketing because the hard questions have no good answers:

| ❓ Question | 💥 The Painful Reality |
|:---|:---|
| **Who is real?** | Up to **30–50%** of "influence" is bots and bought followers. Vanity metrics lie. |
| **Who fits my brand?** | Niche tags are too coarse — a "tech" creator might have the wrong voice, audience, or values entirely. |
| **What should I post — will it work?** | Creators guess at trends and burn effort on content that never lands. |
| **How do I run the campaign?** | Briefing, shortlisting, comparing, budgeting, and outreach are all manual, slow, and inconsistent. |

> ✅ **Ratefluencer AI answers all of them — automatically.**
> Real ML for the numbers, semantic embeddings for fit, and Gemini agents for the judgment calls a human marketer would normally make.

---

## 🏗️ System Architecture

```
╔════════════════════════════════════════════════════════════════════════════╗
║                            📥  DATA SOURCES                                  ║
║   YouTube Data API v3  ·  HuggingFace IG Captions  ·  HN Algolia            ║
║   Google News RSS      ·  Pexels                                            ║
╚═══════════════════════════════════╦══════════════════════════════════════════╝
                                    ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                            🧮  ML LAYER                                      ║
║  ┌─────────────── TRACK 1 ───────────────┬──────────── TRACK 2 ───────────┐ ║
║  │ • Ratefluencer Score Ensemble         │ • Trend Engine — 5-signal ML   │ ║
║  │   (XGB+LGBM+CatBoost · MAE 1.51)      │   (accel/velocity/novelty/...) │ ║
║  │ • Authenticity (XGBoost + Platt)      │ • Virality Model               │ ║
║  │ • Growth Predictor (XGBoost)          │   (XGBoost · 25 feats · calib.)│ ║
║  │ • Semantic Brand Match                │ • Best-of-3 content ranker     │ ║
║  │   (Sentence-Transformers · 384-dim)   │                                │ ║
║  └───────────────────────────────────────┴────────────────────────────────┘ ║
╚═══════════════════════════════════╦══════════════════════════════════════════╝
                                    ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                  🤖  GEMINI AI AGENT LAYER  (8 agents)                       ║
║  Brief Optimizer · Outreach · Content-Fit · Brand-Safety                    ║
║  Competitor-Intel · Compare · Budget/ROI · Script Generator                 ║
╚═══════════════════════════════════╦══════════════════════════════════════════╝
                                    ▼
╔════════════════════════════════════════════════════════════════════════════╗
║              🌐  UNIFIED FASTAPI SERVER   (uvicorn :8000)                    ║
║  Track 1 routes  +  /api Track 2 routes  +  /docs                           ║
║  ⏰ APScheduler → run_trend_scan() every 60 min  (autonomous)               ║
╚═══════════════════════════════════╦══════════════════════════════════════════╝
                                    ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                        ⚛️  REACT 18 FRONTEND                                 ║
║   /         → Track 1: Search · Discovery · Profile · Compare · Budget      ║
║                        · Outreach · Trend-Alert Bell 🔔                     ║
║   /creator  → Track 2: Niche picker · Script gen · Virality · Best-of-3     ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---
---

# 1️⃣ Track 1 — Influencer Intelligence

## 🔄 Track 1 Workflow — Brief → Signed Creator

```
        ┌──────────────────────────────────────────────┐
        │   🎬  Brand enters campaign brief             │
        │   IN:  rough goal, budget, product, vibe      │
        └───────────────────────┬──────────────────────┘
                                ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 1 · 🤖 Agent 1 — Brief Optimizer  (Gemini)               ║
   ║   IN  ▸ raw brief                                             ║
   ║   OUT ▸ refined brief · ranked niches · ideal persona · angle ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 2 · 🔎 Semantic Search  (Sentence-Transformers, 384-dim) ║
   ║   IN  ▸ refined brief embedding                              ║
   ║   OUT ▸ candidate creators by voice & values cosine match     ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 3 · 🧮 ML Ranking  (Ensemble: XGB + LGBM + CatBoost)     ║
   ║   IN  ▸ candidates + 33 features                             ║
   ║   OUT ▸ scored by  ( brand_match  ×  quality )                ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 4 · 📋 Results                                           ║
   ║   OUT ▸ ranked influencer list  +  Ratefluencer scores        ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 5 · 👤 Deep Profile Analysis  (Auth + Growth models)    ║
   ║   IN  ▸ selected influencer                                  ║
   ║   OUT ▸ live authenticity score  +  growth trajectory         ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 6 · 🤖 Agent 6 — Compare 2–3 Influencers  (Gemini)      ║
   ║   IN  ▸ 2–3 candidates + brief                               ║
   ║   OUT ▸ winner · ranking · axis-by-axis comparison            ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 7 · 🤖 Agent 8 — Budget & ROI Estimation  (ML + Gemini) ║
   ║   IN  ▸ budget + chosen candidates                           ║
   ║   OUT ▸ spend mix · reach · conversions · ROI · strategy      ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 8 · 🤖 Agent 3 — Outreach Email  (Gemini, personalized) ║
   ║   IN  ▸ winning creator + brief                              ║
   ║   OUT ▸ subject · body · hook · tone · CTA                    ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
        ┌──────────────────────────────────────────────┐
        │  ✅ OUTPUT:  Complete campaign package         │
        │     ready to execute                           │
        └──────────────────────────────────────────────┘
```

---

## 🏅 Ratefluencer Score — 6 Models Benchmarked, Ensemble Wins

We don't ship one model and hope. We trained **6 models + a voting ensemble**, benchmarked them on a held-out 20% split (`random_state=42`) with **5-fold CV**, and the best one (lowest test MAE) is saved automatically.

> 📌 **All numbers below are computed at runtime from the dataset — none are hard-coded.**

| Model | MAE ↓ | R² ↑ | Role |
|:---|:---:|:---:|:---|
| Ridge (linear baseline)\* | 2.40 | 0.815 | Sanity floor |
| Random Forest | 2.54 | 0.860 | Tree baseline |
| XGBoost | 1.54 | 0.872 | Ensemble member |
| LightGBM | 1.62 | 0.870 | Ensemble member |
| CatBoost | 1.57 | **0.889** | Ensemble member |
| Neural Net (MLP 128-64-32) | 1.94 | 0.852 | Deep features |
| **🏆 Voting Ensemble (3:2:1)** | **1.51** | 0.878 | **Shipped model** |

<sub>\* Labeled "Logistic Regression" in code; implemented as Ridge (`alpha=1.0`) since the target is continuous. Configs: RF `n_estimators=300, depth=8`; XGB/LGBM `n_estimators=700, depth=5, lr=0.05, subsample=0.8`; CatBoost `iterations=500, depth=5, lr=0.05`.</sub>

The ensemble blends the top 3 tree models (weights **3:2:1**) and is only shipped if it beats every standalone model — here it does, at **MAE `1.51` / R² `0.878`**. Results are written to `model_comparison.json` and the winner to `ratefluencer_model.pkl`.

### 🧬 33+ Engineered Features — Not Raw Counts, But _Signal_

| Category | Example Features |
|:---|:---|
| 💬 **Engagement** | `engagement_rate`, `true_engagement_rate`, `er_vs_expected`, `eng_efficiency` |
| 🛡️ **Audience quality** | `authenticity_score`, `real_followers_pct`, `bot_follower_pct`, `unique_commenters_ratio` |
| 📆 **Consistency** | `posting_std_dev`, `posts_per_week`, `posting_regularity`, `content_velocity` |
| 📈 **Growth** | `growth_rate_30d/90d`, `growth_momentum`, `avg_daily_growth`, `followers_log` |
| 🗨️ **Comment quality** | `comment_spam_ratio`, `comment_like_ratio`, `comment_quality` |
| ✖️ **Interactions** | `auth_x_engagement`, `growth_x_quality` (explicit cross terms) |
| 🎯 **Campaign signals** | `campaign_success_prob`, `collab_frequency`, `sponsored_er_drop`, `bio_completeness_score` |

<sub>Plus up to **15 one-hot niche dummies**. Demographics (`country_enc`, `age_group_enc`) round it out.</sub>

### 🧩 Companion Models

| Model | Engine | What it does |
|:---|:---|:---|
| **Authenticity** | XGBoost + Platt scaling | Upgraded from an unsupervised IsolationForest baseline. Detects bot / bought-follower signatures. |
| **Growth Predictor** | XGBoost | Forward-looking follower trajectory over engagement + momentum features. |
| **Semantic Brand Match** | Sentence-Transformers (`all-MiniLM-L6-v2`, 384-dim) | Matches over **real Instagram captions + YouTube profiles** — beyond niche tags to _voice and values_. TF-IDF + cosine kept as fallback. |

---

## 🔌 API — Selected from 17 Endpoints

| Method | Path | Purpose |
|:---|:---|:---|
| `POST` | `/search` | Brand brief → ML-ranked influencers with match reasons |
| `POST` | `/api/run-campaign` | **🤖 Full autonomous pipeline:** brief → search → compare → budget/ROI → outreach |
| `GET` | `/influencers/{id}` | Deep profile with live auth + growth predictions |
| `POST` | `/api/optimize-brief` | Agent: refine rough brief into targeting strategy |
| `POST` | `/api/compare` | Agent: side-by-side comparison of 2–3 candidates |
| `POST` | `/api/budget-estimate` | Agent: budget allocation + ROI estimate |
| `POST` | `/api/outreach` | Agent: personalized outreach email |
| `GET`/`POST`/`DELETE` | `/api/alerts[...]` | Trend alert feed: list, scan, dismiss |

> 📖 Full list including `/health`, `/stats`, `/influencers` (filter/sort/paginate), `/influencers/{id}/growth`, `/influencers/{id}/auth`, and `/api/alerts/scan` is auto-documented at **`/docs`**.

**⚙️ On startup:**

```
load dataset → load all 4 ML models → load sentence embedder
            → start APScheduler trend scan (every 60 min)
            → alerts scoring ≥ 82 saved to alerts.json
```

---
---

# 🤖 The 8 Gemini AI Agents

> Numbers handle the **what**; agents handle the **why** and **how**.
> All built on **Gemini 3.1 Flash Lite Preview**.

| # | Agent | Input → Output | What it does |
|:---:|:---|:---|:---|
| 1 | **Brief Optimizer** | rough brief → refined brief, ranked niches, ideal persona, angle | Turns a vague ask into a real targeting strategy |
| 2 | **Outreach Generator** | influencer + brief → subject, body, hook, tone, CTA | Personalized emails that reference the creator's _actual_ content |
| 3 | **Content-Fit Analyzer** | bio + captions + brief → fit_score, voice_match, mismatches | Scores voice/values alignment beyond niche tags |
| 4 | **Brand-Safety Checker** | profile signals → safety_score, risk_level, red/green flags | Flags controversy, competitor ties, fake signals **before signing**. Blends ML authenticity **60/40** with Gemini |
| 5 | **Competitor Intel** | category + niche → strategy, untapped niches, recommended tiers | Reverse-engineers what rivals do, recommends differentiation |
| 6 | **Compare Influencers** | 2–3 candidates + brief → winner, ranking, axis comparison | Strategic side-by-side; falls back to Ratefluencer score |
| 8 | **Budget/ROI Estimator** | budget + candidates → mix, reach, conversions, ROI, strategy | **Hybrid:** ML greedily allocates by cost-efficiency × quality; Gemini adds rationale + a tip (₹500 AOV assumption) |

> 🙋 **Honest note:** the codebase numbers agents **1–6 and 8** — there is **no Agent 7**; the file jumps from 6 to 8. We list them as they exist rather than inventing one. The **Script Generator** (Track 2) is the de-facto 8th content agent.

---
---

# 2️⃣ Track 2 — Creator Content Engine

## 🔄 Track 2 Workflow — Niche → Ready-to-Post Reel

```
        ┌──────────────────────────────────────────────┐
        │   🎛️  User selects niche                      │
        │   IN:  AI · creator economy · finance · ...   │
        └───────────────────────┬──────────────────────┘
                                ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 1 · 📡 Trend Discovery  (HN Algolia + Google News RSS)   ║
   ║   IN  ▸ niche query sets                                      ║
   ║   OUT ▸ raw trend candidates + mention counts (t0,t1,t2)      ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 2 · 🧮 5-Signal ML Ranking                              ║
   ║   ▸ Acceleration 35%  ▸ Velocity 25%  ▸ Novelty 20%          ║
   ║   ▸ Volume 10%        ▸ Sustained 10%                        ║
   ║   OUT ▸ trend score  0–100                                    ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 3 · 🤖 Gemini Enrichment  (NEVER touches the score)     ║
   ║   IN  ▸ scored trend                                         ║
   ║   OUT ▸ why_trending · content_angle · urgency               ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 4 · ✍️ Script Generation  (Gemini, 1 call)             ║
   ║   IN  ▸ top trend + angle                                    ║
   ║   OUT ▸ Hook + Story + Insights + CTA                        ║
   ║         + LinkedIn + Instagram + Thumbnail                    ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 5 · 🥇 Best-of-3 Ranker                                 ║
   ║   IN  ▸ generate 3 script variants                           ║
   ║        → XGBoost scores each → return winner                 ║
   ║   OUT ▸ highest predicted-virality variant                   ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 6 · 🔮 Virality Prediction  (XGBoost, 25 features)      ║
   ║   IN  ▸ winning script + trend signals                       ║
   ║   OUT ▸ virality score (Platt-calibrated) + confidence band  ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║ STEP 7 · 🎬 Reel Production                                   ║
   ║   IN  ▸ approved script                                      ║
   ║   ▸ edge-tts voiceover + Pexels/Imagen images + MoviePy      ║
   ║   OUT ▸ rendered MP4                                          ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
        ┌──────────────────────────────────────────────┐
        │  ✅ OUTPUT:  Trend score + Script              │
        │     + Virality score + Ready-to-post MP4       │
        └──────────────────────────────────────────────┘
```

---

## 📡 Trend Engine — Catch the Wave Before It Breaks

Polls **HN Algolia** and **Google News RSS** across **6 niche query sets** (AI, creator economy, finance, startups, business, technology), then derives **5 ML signals** from mention counts in 3 time windows (`t0`, `t1`, `t2`):

| Signal | Formula | Why It Matters |
|:---|:---|:---|
| **velocity** | `(t2 − t0) / 2` | How fast it's moving |
| **acceleration** | `t2 − 2·t1 + t0` | 2nd derivative — _is it speeding up?_ |
| **volume** | `t0 + t1 + t2` | Raw size |
| **novelty** | `t2 / volume` | How recent the spike is |
| **sustained** | `{0:0, 1:.4, 2:.8, 3:1}` | Staying power, not a one-off blip |

Combined into a **0–100 score** (acceleration weighted highest at **35%**):

```python
raw   = 0.35*tanh(accel/5) + 0.25*tanh(vel/5) + 0.20*novelty + 0.10*tanh(log1p(vol)/5) + 0.10*sustained
score = round((raw + 1) * 50, 2)   # map [-1,1] → [0,100]
```

> 🔧 `tanh` compresses outliers, `log1p` dampens raw volume, and **additive** combination (vs. an earlier multiplicative version) ensures single-window breakouts aren't zeroed out.
>
> 🤖 **Gemini annotates only** — it adds `why_trending`, `content_angle`, `target_audience`, and `urgency`, and **never touches the numeric score.**

---

## ✍️ Script Generator

For each top trend, **one Gemini call** produces a complete content kit:

1. 🎥 **30–60s reel script** (hook → story → insights → CTA)
2. 💼 **LinkedIn post** (professional, hashtags)
3. 📸 **Instagram caption** (casual, CTA, hashtags)
4. 🖼️ **Thumbnail text** (title + subtitle)

```
Model: gemini-3.1-flash-lite-preview (v1beta REST)
temp: 0.7  ·  max_tokens: 8192  ·  response: JSON mode
output → scripts_output.json
```

---

## 🔮 Virality Model — Predict Before You Post

**XGBoost regression**, tuned via `RandomizedSearchCV`, **Platt-calibrated** so scores map to real engagement probability, trained on **15,000 synthetic samples** with non-linear ground truth (multiplicative interactions). Reports **MAE + R²** and a **confidence band (±uncertainty)** with every prediction.

### 🧬 25 Features Across 4 Groups

| Group | # | Features |
|:---|:---:|:---|
| 📝 **Text quality** | 11 | hook length (8–15 word bell curve), sentiment, question/number flags, power words, **hook semantic similarity to a viral-headline corpus**, story length & specificity, insight count, CTA strength & urgency |
| 📈 **Trend signals** | 4 | `trend_score`, `trend_urgency`, `trend_acceleration`, `niche_virality` baseline |
| 📱 **Platform signals** | 4 | caption length, hashtag count, LinkedIn length, title length — each with a learned sweet-spot |
| 🗣️ **Linguistic** | 6 | sentiment, exclamations, content-angle power density, sentence count, avg word length, emoji presence |

> 🥇 A **Best-of-3 ranker** generates variants and surfaces the highest predicted-virality option.

---
---

# 🏆 Grand Challenge — The Autonomous Loop

> **Where both tracks connect into one self-driving campaign engine.**

```
   ╔═══════════════════════════════════════════════════════════════╗
   ║  ⏰ APScheduler — every 60 min                                ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  📡 Trend scan fires automatically                            ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  🚨 Breaking trend detected  ( score > 82 )                   ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  🔔 Alert Bell lights up in Track 1 UI                        ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  🖱️  Brand clicks: "Find influencers for this trend"          ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  1️⃣ Track 1 auto-searches → returns ranked creators          ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  🎯 Brand picks top creator → clicks "Generate Content"       ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  2️⃣ Track 2 generates tailored content for that niche        ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
   ╔═══════════════════════════════════════════════════════════════╗
   ║  🔮 Virality predicted → content approved → reel produced     ║
   ╚═══════════════════════════════════╦═══════════════════════════╝
                                       ▼
        ┌──────────────────────────────────────────────┐
        │  ✅ Campaign complete:                         │
        │     influencer  +  content  +  score           │
        └──────────────────────────────────────────────┘
```

---
---

## ▶️ Demo Walkthrough — Signal to Signed to Scored

| Step | Action | What Happens |
|:---:|:---|:---|
| 🔔 | **Alert fires** | APScheduler's hourly trend scan surfaces "AI agents" accelerating; the alert bell lights up. |
| 🔍 | **Search** | A brand drops a rough brief into `/search`. _Brief Optimizer_ refines it; the _Semantic Brand Match_ + _Ratefluencer Ensemble_ return a ranked shortlist with reasons. |
| 👤 | **Deep dive** | Open an influencer: live **authenticity** + **growth** predictions, not stale stats. |
| ⚖️ | **Compare** | Pick 3 candidates → _Compare Agent_ declares a winner with axis-by-axis reasoning; _Brand-Safety_ clears them. |
| 💰 | **Budget** | _Budget/ROI Estimator_ allocates spend, projects reach/conversions/ROI, and adds a strategic tip. |
| ✉️ | **Outreach** | _Outreach Generator_ drafts a personalized email referencing the creator's real content. |
| 🎬 | **Create (Track 2)** | Switch to `/creator`: pick the trending niche → _Script Generator_ writes a reel + LinkedIn + IG kit → _Virality Model_ scores it with a confidence band → Best-of-3 picks the winner. |

> 🎉 **One platform took you from _signal_ → _signed creator_ → _scored content_.**

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r track1/backened/requirements.txt

# 2. Add your key (.env in project root)
echo GEMINI_API_KEY=your_key_here > .env

# 3. Run the unified server (both tracks, one process)
python app.py
```

Then open:

| URL | What |
|:---|:---|
| `http://localhost:8000/` | 1️⃣ Track 1 — Influencer Intelligence dashboard |
| `http://localhost:8000/creator` | 2️⃣ Track 2 — Creator Content Engine |
| `http://localhost:8000/docs` | 📖 Interactive API docs (Swagger) |

> ⚙️ `app.py` merges both backends into a single uvicorn process on `:8000`. Track 1 owns `/` and all unmatched paths; Track 2 is namespaced under `/creator` (frontend) and `/api` (backend).
>
> 🔁 To **(re)train** the influencer model: `python track1/backened/ml_benchmark.py`

---

## 🛠️ Technology Stack

### 🧠 AI / ML

| Tech | Use |
|:---|:---|
| XGBoost · LightGBM · CatBoost | Ratefluencer ensemble, virality, growth, authenticity |
| Random Forest · Ridge · MLP | Benchmark models |
| Sentence-Transformers (`all-MiniLM-L6-v2`) | Brand match + hook similarity (384-dim) |
| IsolationForest → XGBoost + Platt | Authenticity (upgraded from unsupervised) |
| TextBlob | Sentiment features |
| Scikit-learn · Pandas · NumPy | Pipeline, preprocessing, data |

### 🌐 AI APIs

| API | Use |
|:---|:---|
| Gemini 3.1 Flash Lite Preview | All 8 agents + content generation |
| Imagen 4 Fast | Post image generation (billed) |
| edge-tts (Microsoft) | Free neural TTS voiceover |
| YouTube Data API v3 | Real influencer data |
| HuggingFace Datasets | Real IG captions for training |
| Pexels | Visual fallback |

### 🧱 Platform

- **Backend:** FastAPI · APScheduler · Pickle · python-dotenv · uvicorn
- **Frontend:** React 18.3.1 (CDN) · Babel · Lucide Icons · DiceBear avatars · Recharts · CSS custom-property dark theme

---

## 🏆 Judging Criteria Mapping

| Criteria | Pts | How We Earn It |
|:---|:---:|:---|
| **AI/ML Innovation** | **20** | Sentence-transformer brand match, 5-signal trend ML, 8 Gemini agents, real-data training |
| **Influencer Scoring Accuracy** | **20** | 6 models benchmarked, **ensemble winner MAE `1.51` / R² `0.878`**, 33+ features, real data |
| **Viral Prediction** | **15** | XGBoost virality model (25 features, Platt-calibrated, confidence band), hook semantic sim, Best-of-3 |
| **Automation & Agent Design** | **15** | 8 Gemini agents, autonomous APScheduler scan, full `/api/run-campaign` pipeline |
| **Product Design & UX** | **10** | Dark dashboard, alert bell, compare modal, budget panel, DiceBear avatars |
| **Business Impact** | **10** | Budget/ROI estimator, brand-safety gate, personalized outreach, real engagement metrics |
| **Technical Complexity** | **5** | Unified dual-track server, real scraping, model ensemble, semantic embeddings |
| **Demo & Presentation** | **5** | One clean flow: alert → search → compare → budget → outreach → generate → score |

---

## 💼 Business Impact

- 💸 **Cut wasted spend** — authenticity + brand-safety models stop budget flowing to bots and risky accounts _before_ contracts.
- ⚡ **Faster campaigns** — `/api/run-campaign` collapses days of manual shortlisting, comparison, budgeting, and outreach into one call.
- 🎯 **Higher hit rate** — semantic brand match + virality prediction mean better creators _and_ better content, scored before money is spent.
- 📊 **Quantified ROI** — every budget recommendation comes with projected reach, conversions, and an ROI multiplier.

---

## 🔭 Future Enhancements

- 🔁 Close the feedback loop: log real post performance and retrain virality/score models on outcomes (self-improving).
- 📈 Replace synthetic virality ground truth with live engagement data at scale.
- 🌍 Multi-platform expansion (TikTok, X) for trend and creator data.
- 🕵️ Train authenticity on a labeled fraud dataset to move beyond synthetic/heuristic signals.
- 🤝 Auto-negotiation agent (**Agent 7** — the one that's currently missing 😉).

---

<div align="center">

<sub>Built for the AI Hackathon · Metrics in this README are read from `track1/backened/model_comparison.json`, produced by running `ml_benchmark.py` against the dataset — <b>no figures are hand-entered.</b></sub>

</div>
