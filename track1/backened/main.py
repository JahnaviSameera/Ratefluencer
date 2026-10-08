"""
Ratefluencer — FastAPI Backend
================================
Routes:
  GET  /                          health check
  GET  /stats                     dataset summary
  GET  /influencers               list with filters + sort
  GET  /influencers/{id}          single profile deep dive
  POST /search                    brand brief → ranked influencers
  GET  /influencers/{id}/growth   growth prediction
  GET  /influencers/{id}/auth     authenticity breakdown

Start: uvicorn main:app --reload --port 8000
Docs:  http://localhost:8000/docs
"""
from __future__ import annotations
import os, json, sys, time, uuid
sys.path.insert(0, os.path.dirname(__file__))

ALERTS_FILE = os.path.join(os.path.dirname(__file__), "alerts.json")

def _load_alerts() -> list:
    try:
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _save_alerts(alerts: list) -> None:
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=2)

def run_trend_scan():
    """Runs every hour — finds breaking trends and saves alerts."""
    try:
        print("[TrendScanner] Running scheduled scan...")
        # Import here to avoid circular deps
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "track2", "backend"))
        from trend_agent import discover_trends

        alerts = _load_alerts()
        existing_phrases = {a["phrase"] for a in alerts if not a.get("dismissed")}

        for niche in ["artificial intelligence", "creator economy", "technology", "finance"]:
            try:
                trends = discover_trends(niche=niche, window_hours=24, top_n=5, use_gemini=False)
                for t in trends:
                    if t.score >= 82 and t.phrase not in existing_phrases:
                        alert = {
                            "id":          str(uuid.uuid4())[:8],
                            "phrase":      t.phrase,
                            "score":       round(t.score, 1),
                            "urgency":     "breaking" if t.score >= 90 else "rising",
                            "niche":       niche,
                            "why":         t.why_trending or f"Trending in {niche}",
                            "acceleration":round(t.acceleration, 1),
                            "timestamp":   time.time(),
                            "dismissed":   False,
                        }
                        alerts.append(alert)
                        existing_phrases.add(t.phrase)
                        print(f"[TrendScanner] 🔥 Alert: {t.phrase} ({t.score:.0f})")
            except Exception as e:
                print(f"[TrendScanner] {niche} failed: {e}")

        # Keep only last 20 undismissed alerts
        alerts = sorted(alerts, key=lambda x: x["timestamp"], reverse=True)[:20]
        _save_alerts(alerts)
        print(f"[TrendScanner] Done. {len([a for a in alerts if not a['dismissed']])} active alerts")
    except Exception as e:
        print(f"[TrendScanner] Scan error: {e}")

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from models.authenticity      import predict as auth_predict,    load as auth_load,    score_dataframe as auth_score_df
from models.growth            import predict as growth_predict,  load as growth_load,  score_dataframe as growth_score_df
from models.brand_match       import predict as brand_predict,   load as brand_load,   rank_influencers
from models.ratefluencer_score import predict as rf_predict,     load as rf_load,      score_dataframe as rf_score_df

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Ratefluencer AI API",
    description="AI-powered influencer intelligence engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Load dataset + models at startup
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(os.path.dirname(__file__), "influencer_dataset.csv")
df_global: pd.DataFrame = None
auth_model = auth_scaler = growth_model = growth_scaler = brand_vectorizer = rf_model = None

@app.on_event("startup")
async def startup():
    global df_global, auth_model, auth_scaler, growth_model, growth_scaler, brand_vectorizer, rf_model
    print("[Startup] Loading dataset...")
    df_global = pd.read_csv(DATA_PATH)
    print(f"[Startup] {len(df_global)} profiles loaded")

    print("[Startup] Loading ML models...")
    try:
        auth_model, auth_scaler = auth_load()
        growth_model, growth_scaler = growth_load()
        brand_vectorizer = brand_load()
        rf_model = rf_load()
        from models.brand_match import _load_embedder
        _load_embedder()
        print("[Startup] All models loaded ✓")
    except FileNotFoundError as e:
        print(f"[Startup] Models not found: {e}")
        print("[Startup] Run: python train_models.py")

    # Start trend scanner — runs immediately once, then every 60 minutes
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_trend_scan, "interval", minutes=60, id="trend_scan")
        scheduler.start()
        print("[Startup] Trend scanner started (every 60 min) ✓")
    except Exception as e:
        print(f"[Startup] Scheduler failed: {e}")


def _safe_val(v):
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating,)): return float(v)
    if isinstance(v, (np.bool_,)): return bool(v)
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)): return None
    return v

def _row_to_dict(row: pd.Series) -> dict:
    return {k: _safe_val(v) for k, v in row.items()}

def _parse_json_col(val):
    """Parse JSON string columns → list."""
    if isinstance(val, list): return val
    try: return json.loads(val) if isinstance(val, str) else []
    except: return []

def _audience_breakdown(row: dict) -> dict:
    """Generate audience age + country breakdown from available fields."""
    age_grp = row.get("audience_age_group", "25_34")
    country = row.get("audience_country_top1", "India")
    age_map = {
        "13_17": {"13-17":55,"18-24":25,"25-34":12,"35-44":6,"45+":2},
        "18_24": {"13-17":8,"18-24":52,"25-34":28,"35-44":8,"45+":4},
        "25_34": {"13-17":3,"18-24":22,"25-34":55,"35-44":15,"45+":5},
        "35_44": {"13-17":2,"18-24":10,"25-34":30,"35-44":45,"45+":13},
        "45_54": {"13-17":1,"18-24":5,"25-34":18,"35-44":32,"45+":44},
    }
    country_map = {
        "India":     {"India":65,"USA":12,"UAE":10,"UK":8,"Other":5},
        "USA":       {"USA":68,"India":10,"UK":10,"Canada":8,"Other":4},
        "UAE":       {"UAE":55,"India":20,"UK":10,"USA":10,"Other":5},
        "UK":        {"UK":60,"USA":18,"India":10,"Canada":8,"Other":4},
        "Singapore": {"Singapore":50,"India":20,"USA":15,"UK":10,"Other":5},
        "Canada":    {"Canada":62,"USA":18,"UK":10,"India":6,"Other":4},
        "Australia": {"Australia":60,"UK":15,"USA":12,"India":8,"Other":5},
    }
    return {
        "age":     age_map.get(age_grp, age_map["25_34"]),
        "country": country_map.get(country, country_map["India"]),
    }

def _shape_influencer(row: dict, include_ml: bool = False) -> dict:
    """Transform backend row → frontend expected shape."""
    f = row.get("followers_count", 0)
    return {
        "id":                    row.get("influencer_id", ""),
        "username":              row.get("username", ""),
        "full_name":             row.get("full_name", ""),
        "niche":                 row.get("niche", ""),
        "tier":                  row.get("tier", ""),
        "platform":              row.get("platform", "Instagram"),
        "followers_count":       f,
        "engagement_rate":       row.get("engagement_rate", 0),
        "true_engagement_rate":  row.get("true_engagement_rate", 0),
        "is_verified":           bool(row.get("is_verified", False)),
        "is_fake_account":       bool(row.get("is_fake_account", False)),
        "ratefluencer_score":    row.get("ratefluencer_score", 0),
        "authenticity_score":    row.get("authenticity_score", 0),
        "growth_score":          row.get("growth_score", 0),
        "campaign_success_score": round(float(row.get("campaign_success_prob", 0)) * 100, 1),
        "benchmark":             round(float(row.get("engagement_rate", 0)) * 0.8, 2),
        "avg_likes":             row.get("avg_likes", 0),
        "avg_comments":          row.get("avg_comments", 0),
        "avg_video_views":       int(f * float(row.get("video_view_rate", 0.1))),
        "posts_per_week":        row.get("posts_per_week", 0),
        "save_rate":             row.get("save_rate", 0),
        "share_rate":            row.get("share_rate", 0),
        "followers_30d_delta":   int(row.get("followers_7d_delta", 0)) * 4,
        "engagement_trend_30d":  row.get("engagement_trend_30d", 0),
        "content_tone":          row.get("content_tone", ""),
        "top_hashtags":          _parse_json_col(row.get("top_5_hashtags", "[]")),
        "past_brand_categories": _parse_json_col(row.get("past_brand_categories", "[]")),
        "audience":              _audience_breakdown(row),
        "bio":                   row.get("bio", ""),
        "sample_comments":       _parse_json_col(row.get("sample_comments", "[]")),
        "sample_captions":       _parse_json_col(row.get("sample_captions", "[]")),
        # ML detail (only on full profile)
        **({"auth":   row.get("authenticity_detail")} if include_ml and "authenticity_detail" in row else {}),
        **({"growth": row.get("growth_detail")}       if include_ml and "growth_detail" in row else {}),
    }


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
from typing import Union

class BrandBrief(BaseModel):
    category:            str   = ""
    product_description: str   = ""
    target_audience:     str   = ""
    campaign_goal:       str   = "Awareness"
    keywords:            Union[str, list] = ""   # frontend sends array, backend accepts both
    niche:               str   = ""
    target_age_group:    str   = "25_34"
    target_country:      str   = "India"
    min_followers:       int   = 1000
    max_followers:       int   = 25000000
    min_authenticity:    float = 0.0
    top_n:               int   = 20

    def keywords_str(self) -> str:
        if isinstance(self.keywords, list):
            return " ".join(str(k) for k in self.keywords if k)
        return str(self.keywords or "")


def _shape_auth(raw: dict) -> dict:
    """Map authenticity.predict() output → frontend auth shape."""
    factors = []
    for item in raw.get("breakdown", []):
        feat = item["feature"]
        val  = item["value"]
        good = item["impact"] == "positive"
        # Determine unit and display hint
        if "pct" in feat.lower() or "ratio" in feat.lower() or "%" in feat.lower():
            unit, higher = "%", "Real Followers %" in feat
        elif "score" in feat.lower() or "completeness" in feat.lower():
            unit, higher = "/1.0", True
        elif "ratio" in feat.lower() or "spike" in feat.lower():
            unit, higher = "x", False
        else:
            unit, higher = "", True
        factors.append({"key": feat, "value": round(float(val), 3),
                        "unit": unit, "good": good, "higherBetter": higher})
    return {"verdict": raw.get("verdict", ""), "factors": factors}


def _shape_growth(raw: dict) -> dict:
    """Map growth.predict() output → frontend growth shape."""
    return {
        "growth_score": raw.get("growth_score", 0),
        "verdict":      raw.get("verdict", ""),
        "followers": {
            "30d": raw.get("predicted_followers_30d", 0),
            "60d": raw.get("predicted_followers_60d", 0),
            "90d": raw.get("predicted_followers_90d", 0),
        },
        "er": {
            "30d": raw.get("predicted_er_30d", 0),
            "60d": raw.get("predicted_er_60d", 0),
        },
        "drivers": [{"factor": d["factor"], "value": d["value"]}
                    for d in raw.get("growth_drivers", [])],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
FRONTEND_DIR  = os.path.join(os.path.dirname(__file__), "..", "FRONTEND")
FRONTEND_JS   = os.path.join(FRONTEND_DIR, "js")
FRONTEND_HTML = os.path.join(FRONTEND_DIR, "Ratefluencer AI.html")

if os.path.exists(FRONTEND_JS):
    app.mount("/js", StaticFiles(directory=FRONTEND_JS), name="js")

@app.get("/")
def root():
    if os.path.exists(FRONTEND_HTML):
        return FileResponse(FRONTEND_HTML, media_type="text/html")
    return {"status": "ok", "service": "Ratefluencer AI API", "version": "1.0.0"}

class FullCampaignRequest(BaseModel):
    category:            str = ""
    product_description: str = ""
    campaign_goal:       str = "Awareness"
    target_audience:     str = ""
    budget_inr:          int = 100000
    niche:               str = ""
    top_n:               int = 3

@app.post("/api/run-campaign")
def api_run_campaign(req: FullCampaignRequest):
    """Full autonomous campaign pipeline — fast ML core + Gemini enrichment with timeouts."""
    import concurrent.futures as cf
    from agents import brief_optimizer, compare_influencers, budget_roi_estimator, outreach_generator
    from models.brand_match import rank_influencers as bm_rank

    def _gemini_safe(fn, *args, timeout=5, default=None):
        try:
            with cf.ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(fn, *args).result(timeout=timeout)
        except Exception:
            return default or {}

    result = {}

    # ── Step 1: Optimize brief (Gemini, 5s) ────────────────────────────
    raw_brief = {"category": req.category, "product_description": req.product_description,
                 "campaign_goal": req.campaign_goal, "niche": req.niche}
    optimized  = _gemini_safe(brief_optimizer, raw_brief, timeout=5,
                               default={"target_niches":[req.niche or "Lifestyle Vlogging"],
                                        "keywords":[], "ideal_persona":"", "refined_brief":raw_brief})
    refined    = optimized.get("refined_brief", raw_brief)
    best_niche = (optimized.get("target_niches") or [req.niche or ""])[0]
    result["step1_optimized_brief"] = optimized

    # ── Step 2: Search influencers (ML only — fast) ─────────────────────
    search_brief = {**raw_brief, "niche": best_niche,
                    "keywords": optimized.get("keywords", []),
                    "product_description": refined.get("product_description", req.product_description)}
    ranked_df = bm_rank(df_global.copy(), search_brief, cache=brand_vectorizer, top_n=req.top_n)
    top_influencers = [_shape_influencer(r.to_dict()) for _, r in ranked_df.iterrows()]

    if not top_influencers:
        raise HTTPException(404, "No influencers found")

    result["step2_top_influencers"] = [
        {"id": i.get("id"), "username": i.get("username"), "niche": i.get("niche"),
         "ratefluencer_score": i.get("ratefluencer_score"),
         "authenticity_score": i.get("authenticity_score"),
         "brand_match": round(float(row.get("brand_match_score", 0)), 1)}
        for i, (_, row) in zip(top_influencers, ranked_df.iterrows())
    ]

    # ── Step 3: Compare top 3 (Gemini, 5s) — ML fallback = highest score ─
    comparison = _gemini_safe(compare_influencers, top_influencers[:3], search_brief, timeout=5,
                               default={"winner": {"id": top_influencers[0].get("id"),
                                                   "username": top_influencers[0].get("username"),
                                                   "reason": "Highest Ratefluencer score"},
                                        "ranking": [], "comparison": {}, "recommendation": ""})
    winner_id  = comparison.get("winner", {}).get("id", top_influencers[0].get("id"))
    winner     = next((i for i in top_influencers if i.get("id") == winner_id), top_influencers[0])
    result["step3_comparison"] = comparison
    result["step3_winner"]     = {
        "id": winner.get("id"), "username": winner.get("username"),
        "niche": winner.get("niche"), "followers": winner.get("followers_count"),
        "authenticity": winner.get("authenticity_score"),
        "ratefluencer": winner.get("ratefluencer_score"),
        "why": comparison.get("winner", {}).get("reason", "Top ML score"),
    }

    # ── Step 4: Budget & ROI (ML fast + Gemini 4s for strategy) ─────────
    budget_result = budget_roi_estimator(req.budget_inr, search_brief, top_influencers)
    result["step4_budget"] = {
        "total_reach":           budget_result.get("total_reach", 0),
        "estimated_impressions": budget_result.get("estimated_impressions", 0),
        "estimated_conversions": budget_result.get("estimated_conversions", 0),
        "roi_multiplier":        budget_result.get("roi_multiplier", 0),
        "avg_cpm_inr":           budget_result.get("avg_cpm_inr", 0),
        "recommended_mix":       budget_result.get("recommended_mix", [])[:3],
        "strategy":              budget_result.get("gemini_strategy", ""),
        "tip":                   budget_result.get("gemini_tip", ""),
    }

    # ── Step 5: Outreach email (Gemini, 5s) ─────────────────────────────
    budget_ctx = {**raw_brief,
                  "product_description": refined.get("product_description", req.product_description),
                  "budget_note": f"Budget ₹{req.budget_inr:,} | Est. {budget_result.get('estimated_impressions',0):,} impressions | ROI {budget_result.get('roi_multiplier',0)}x"}
    email = _gemini_safe(outreach_generator, winner, budget_ctx, timeout=5,
                          default={"subject": f"Collaboration — {req.category}",
                                   "body": f"Hi @{winner.get('username','')},\n\nWe'd love to collaborate on our {req.category} campaign. Our budget is ₹{req.budget_inr:,} and we think your audience is a great fit.\n\nLet's connect!",
                                   "cta": "Reply to discuss terms", "hook": "", "tone": "professional"})
    result["step5_outreach_email"] = email

    return result


class OptimizeBriefRequest(BaseModel):
    category:            str = ""
    product_description: str = ""
    target_audience:     str = ""
    campaign_goal:       str = "Awareness"
    niche:               str = ""
    keywords:            Union[str, list] = ""

@app.post("/api/optimize-brief")
def api_optimize_brief(req: OptimizeBriefRequest):
    """Agent 1 — Gemini refines a rough brief into a precise targeting strategy."""
    from agents import brief_optimizer
    brief = {
        "category":            req.category,
        "product_description": req.product_description,
        "target_audience":     req.target_audience,
        "campaign_goal":       req.campaign_goal,
        "niche":               req.niche,
        "keywords":            req.keywords if isinstance(req.keywords, list) else [k.strip() for k in req.keywords.split(",") if k.strip()],
    }
    result = brief_optimizer(brief)
    return result


class OutreachRequest(BaseModel):
    influencer_id:       str
    category:            str = ""
    product_description: str = ""
    campaign_goal:       str = "Awareness"
    target_audience:     str = ""

class CompareRequest(BaseModel):
    influencer_ids: list[str]
    category:            str = ""
    product_description: str = ""
    campaign_goal:       str = "Awareness"

@app.post("/api/compare")
def api_compare(req: CompareRequest):
    """Agent 6 — Compare 2-3 influencers side-by-side for a campaign."""
    from agents import compare_influencers
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")
    influencers = []
    for iid in req.influencer_ids[:3]:
        m = df_global[df_global["influencer_id"] == iid]
        if not m.empty:
            influencers.append(_shape_influencer(m.iloc[0].to_dict()))
    if len(influencers) < 2:
        raise HTTPException(400, "Need at least 2 valid influencer IDs")
    brief = {"category": req.category, "product_description": req.product_description,
             "campaign_goal": req.campaign_goal}
    return compare_influencers(influencers, brief)


class BudgetRequest(BaseModel):
    budget_inr:          int
    category:            str = ""
    product_description: str = ""
    campaign_goal:       str = "Awareness"
    niche:               str = ""
    min_followers:       int = 1000
    top_n:               int = 20

@app.post("/api/budget-estimate")
def api_budget_estimate(req: BudgetRequest):
    """Agent 8 — Budget allocation + ROI estimation across candidate influencers."""
    from agents import budget_roi_estimator
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")
    filtered = df_global[df_global["followers_count"] >= req.min_followers]
    if req.niche:
        niche_filtered = filtered[filtered["niche"].str.lower() == req.niche.lower()]
        filtered = niche_filtered if len(niche_filtered) >= 5 else filtered
    top = filtered.nlargest(req.top_n, "ratefluencer_score")
    influencers = [_shape_influencer(r.to_dict()) for _, r in top.iterrows()]
    brief = {"category": req.category, "product_description": req.product_description,
             "campaign_goal": req.campaign_goal}
    return budget_roi_estimator(req.budget_inr, brief, influencers)


@app.post("/api/outreach")
def api_outreach(req: OutreachRequest):
    """Agent 3 — Gemini drafts a personalised outreach email for a specific influencer."""
    from agents import outreach_generator
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")
    match = df_global[df_global["influencer_id"] == req.influencer_id]
    if match.empty:
        raise HTTPException(404, "Influencer not found")
    inf_row = _shape_influencer(match.iloc[0].to_dict())
    brief   = {
        "category":            req.category,
        "product_description": req.product_description,
        "campaign_goal":       req.campaign_goal,
        "target_audience":     req.target_audience,
    }
    result = outreach_generator(inf_row, brief)
    return result


@app.post("/api/alerts/scan")
def trigger_scan():
    """Manually trigger a trend scan right now (for testing)."""
    import threading
    threading.Thread(target=run_trend_scan, daemon=True).start()
    return {"ok": True, "message": "Scan started — check /api/alerts in ~60 seconds"}


@app.get("/api/alerts")
def get_alerts():
    """Return active (non-dismissed) trend alerts."""
    alerts = [a for a in _load_alerts() if not a.get("dismissed")]
    return {"alerts": alerts, "count": len(alerts)}

@app.delete("/api/alerts/{alert_id}")
def dismiss_alert(alert_id: str):
    """Dismiss a single alert."""
    alerts = _load_alerts()
    for a in alerts:
        if a["id"] == alert_id:
            a["dismissed"] = True
    _save_alerts(alerts)
    return {"ok": True}

@app.delete("/api/alerts")
def dismiss_all_alerts():
    """Dismiss all alerts."""
    alerts = _load_alerts()
    for a in alerts:
        a["dismissed"] = True
    _save_alerts(alerts)
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Ratefluencer AI API", "version": "1.0.0"}


@app.get("/stats")
def stats():
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")
    niche_counts = df_global["niche"].value_counts()
    return {
        "total_influencers":    len(df_global),
        "total_reach":          int(df_global["followers_count"].sum()),
        "avg_engagement_rate":  round(float(df_global["engagement_rate"].mean()), 2),
        "avg_authenticity":     round(float(df_global["authenticity_score"].mean()), 1),
        "avg_ratefluencer_score": round(float(df_global["ratefluencer_score"].mean()), 1),
        "fake_accounts_pct":    round(float(df_global["is_fake_account"].mean()) * 100, 1),
        "niche_breakdown":      [{"niche": n, "count": int(c)} for n, c in niche_counts.items()],
        "tiers":                df_global["tier"].value_counts().to_dict(),
    }


@app.get("/influencers")
def list_influencers(
    niche:          Optional[str]  = Query(None),
    tier:           Optional[str]  = Query(None),
    min_followers:  int            = Query(0),
    max_followers:  int            = Query(25_000_000),
    min_score:      float          = Query(0),
    sort_by:        str            = Query("ratefluencer_score"),
    limit:          int            = Query(50),
    offset:         int            = Query(0),
):
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")

    filtered = df_global.copy()
    if niche:
        filtered = filtered[filtered["niche"].str.lower() == niche.lower()]
    if tier:
        filtered = filtered[filtered["tier"].str.lower() == tier.lower()]
    filtered = filtered[
        (filtered["followers_count"] >= min_followers) &
        (filtered["followers_count"] <= max_followers) &
        (filtered["ratefluencer_score"] >= min_score)
    ]

    sort_map = {"followers": "followers_count", "engagement_rate": "engagement_rate",
                "authenticity": "authenticity_score", "growth": "growth_score",
                "ratefluencer_score": "ratefluencer_score"}
    sort_col = sort_map.get(sort_by, "ratefluencer_score")
    filtered = filtered.sort_values(sort_col, ascending=False)

    total = len(filtered)
    page  = filtered.iloc[offset: offset + limit]
    records = [_shape_influencer(row.to_dict()) for _, row in page.iterrows()]

    return {"total": total, "offset": offset, "limit": limit, "items": records}


@app.get("/influencers/{influencer_id}")
def get_influencer(influencer_id: str):
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")

    match = df_global[df_global["influencer_id"] == influencer_id]
    if match.empty:
        raise HTTPException(404, f"Influencer {influencer_id} not found")

    row      = match.iloc[0]
    row_dict = row.to_dict()

    # Attach live ML predictions before shaping
    if auth_model:
        row_dict["authenticity_detail"] = _shape_auth(auth_predict(row_dict, auth_model, auth_scaler))
    if growth_model:
        row_dict["growth_detail"] = _shape_growth(growth_predict(row_dict, growth_model, growth_scaler))

    return _shape_influencer(row_dict, include_ml=True)


@app.get("/influencers/{influencer_id}/growth")
def get_growth(influencer_id: str):
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")

    match = df_global[df_global["influencer_id"] == influencer_id]
    if match.empty:
        raise HTTPException(404, "Not found")

    row = match.iloc[0].to_dict()
    if not growth_model:
        raise HTTPException(503, "Growth model not loaded")

    return _shape_growth(growth_predict(row, growth_model, growth_scaler))


@app.get("/influencers/{influencer_id}/auth")
def get_auth(influencer_id: str):
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")

    match = df_global[df_global["influencer_id"] == influencer_id]
    if match.empty:
        raise HTTPException(404, "Not found")

    row = match.iloc[0].to_dict()
    if not auth_model:
        raise HTTPException(503, "Auth model not loaded")

    return _shape_auth(auth_predict(row, auth_model, auth_scaler))


@app.post("/search")
def search_influencers(brief: BrandBrief):
    if df_global is None:
        raise HTTPException(503, "Dataset not loaded")
    if not brand_vectorizer:
        raise HTTPException(503, "Brand match model not loaded")

    # Pre-filter by hard constraints
    filtered = df_global[
        (df_global["followers_count"] >= brief.min_followers) &
        (df_global["followers_count"] <= brief.max_followers) &
        (df_global["authenticity_score"] >= brief.min_authenticity)
    ].copy()

    if filtered.empty:
        return {"total": 0, "items": []}

    brief_dict = brief.dict()
    brief_dict["keywords"] = brief.keywords_str()   # normalize array→string
    ranked     = rank_influencers(filtered, brief_dict, brand_vectorizer, top_n=brief.top_n)

    records = []
    brief_niche = brief_dict.get("niche", "").lower()
    for _, row in ranked.iterrows():
        row_dict  = row.to_dict()
        rec       = _shape_influencer(row_dict)

        # Use score already computed by rank_influencers — no re-encoding
        bm_score  = round(float(row_dict.get("brand_match_score", 0)), 1)
        rec["brand_match"] = bm_score

        # Build match reasons explaining WHY this influencer was recommended
        reasons = []
        auth  = float(row_dict.get("authenticity_score", 0))
        rf_sc = float(row_dict.get("ratefluencer_score", 0))

        if bm_score >= 70:
            reasons.append(f"✓ Strong content alignment with campaign ({bm_score:.0f}% match)")
        elif bm_score >= 50:
            reasons.append(f"✓ Good content alignment with campaign ({bm_score:.0f}% match)")
        else:
            reasons.append(f"Content relevance: {bm_score:.0f}%")

        if auth >= 80:
            reasons.append(f"✓ Highly authentic audience ({auth:.0f}/100 authenticity)")
        elif auth >= 60:
            reasons.append(f"✓ Verified authentic audience ({auth:.0f}/100)")
        else:
            reasons.append(f"⚠ Authenticity below threshold ({auth:.0f}/100)")

        if rf_sc >= 75:
            reasons.append(f"✓ Elite Ratefluencer score ({rf_sc:.0f}/100)")
        elif rf_sc >= 55:
            reasons.append(f"✓ Strong Ratefluencer score ({rf_sc:.0f}/100)")
        else:
            reasons.append(f"⚠ Ratefluencer score low ({rf_sc:.0f}/100)")

        if brief_niche and row_dict.get("niche","").lower() == brief_niche:
            reasons.append(f"✓ Exact niche match: {row_dict.get('niche','').title()}")
        if brief_dict.get("target_country") == row_dict.get("audience_country_top1"):
            reasons.append(f"✓ Primary audience: {row_dict.get('audience_country_top1','')}")

        rec["match_reasons"]  = reasons
        rec["match_warnings"] = []
        rec["gemini_roi"]     = 0
        rec["audience_alignment"] = 0
        rec["why_good_match"] = ""
        rec["expected_outcome"] = ""
        records.append(rec)

    return {"total": len(records), "brief": brief_dict, "items": records}
