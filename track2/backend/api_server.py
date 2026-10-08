"""
Ratefluencer — FastAPI Backend
================================
Bridges the React frontend to the Python pipeline.

Run:
    python api_server.py
    → http://localhost:8000  (serves the frontend + API)
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Ratefluencer API", version="1.0")

# Allow the frontend (any origin during dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-load the virality model once at startup
_virality_model = None

def get_model():
    global _virality_model
    if _virality_model is None:
        from virality_model import load_model
        _virality_model = load_model()
    return _virality_model


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class TrendRequest(BaseModel):
    niche: str = "artificial intelligence"
    top_n: int = 5

class ScriptRequest(BaseModel):
    niche: str = "artificial intelligence"
    trends: list[dict]
    top_n: int = 3

class RankedScriptRequest(BaseModel):
    niche: str = "artificial intelligence"
    trends: list[dict]
    top_n: int = 3
    n_variants: int = 3   # generate this many variants per trend

class ViralityRequest(BaseModel):
    scripts: list[dict]


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.post("/api/trends")
def api_trends(req: TrendRequest):
    """Stage 1 — Discover and rank real trending topics."""
    from trend_agent import discover_trends
    try:
        trends = discover_trends(niche=req.niche, window_hours=24, top_n=req.top_n)
        return {"trends": [t.to_dict() for t in trends]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scripts")
def api_scripts(req: ScriptRequest):
    """Stage 2 — Generate reel scripts, LinkedIn, Instagram, thumbnails."""
    from script_generator import generate_scripts
    try:
        scripts = generate_scripts(req.trends, top_n=req.top_n)
        result = []
        for s in scripts:
            d = s.to_dict()
            # Flatten nested structure to match frontend expected shape
            result.append({
                "trend_phrase":    d["trend_phrase"],
                "trend_score":     d["trend_score"],
                "niche":           d["niche"],
                "urgency":         d["urgency"],
                "why_trending":    d["why_trending"],
                "content_angle":   d["content_angle"],
                "target_audience": d["target_audience"],
                "hook":            d["reel_script"]["hook"],
                "story":           d["reel_script"]["story"],
                "insights":        d["reel_script"]["insights"],
                "cta":             d["reel_script"]["cta"],
                "estimated_duration_seconds": d["reel_script"]["estimated_duration_seconds"],
                "linkedin_post":      d["linkedin"]["post"],
                "linkedin_hashtags":  d["linkedin"]["hashtags"],
                "instagram_caption":  d["instagram"]["caption"],
                "instagram_hashtags": d["instagram"]["hashtags"],
                "thumbnail_title":    d["thumbnail"]["title"],
                "thumbnail_subtitle": d["thumbnail"]["subtitle"],
            })
        return {"scripts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scripts-ranked")
def api_scripts_ranked(req: RankedScriptRequest):
    """
    Stage 2 (enhanced) — Generate n_variants per trend, score each with
    XGBoost, return only the winner per trend + all variant scores.
    Uses real Instagram examples as few-shot in the prompt.
    """
    from script_generator import generate_scripts
    try:
        scripts = generate_scripts(
            req.trends, top_n=req.top_n,
            n_variants=req.n_variants, auto_rank=True
        )
        result = []
        for s in scripts:
            d = s.to_dict()
            flat = {
                "trend_phrase":    d["trend_phrase"],
                "trend_score":     d["trend_score"],
                "niche":           d["niche"],
                "urgency":         d["urgency"],
                "why_trending":    d["why_trending"],
                "content_angle":   d["content_angle"],
                "target_audience": d["target_audience"],
                "hook":            d["reel_script"]["hook"],
                "story":           d["reel_script"]["story"],
                "insights":        d["reel_script"]["insights"],
                "cta":             d["reel_script"]["cta"],
                "estimated_duration_seconds": d["reel_script"]["estimated_duration_seconds"],
                "linkedin_post":      d["linkedin"]["post"],
                "linkedin_hashtags":  d["linkedin"]["hashtags"],
                "instagram_caption":  d["instagram"]["caption"],
                "instagram_hashtags": d["instagram"]["hashtags"],
                "thumbnail_title":    d["thumbnail"]["title"],
                "thumbnail_subtitle": d["thumbnail"]["subtitle"],
                # Variant ranking info
                "variant_scores":  getattr(s, "_variant_scores", []),
            }
            result.append(flat)
        return {"scripts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/virality")
def api_virality(req: ViralityRequest):
    """Stage 3 — XGBoost virality scoring with engagement predictions."""
    from virality_model import predict
    try:
        model = get_model()
        output = []
        for script in req.scripts:
            r = predict(script, model=model)
            score = r.virality_score
            if score >= 72:
                verdict = {"label": "High", "emoji": "🔥", "tone": "high"}
            elif score >= 50:
                verdict = {"label": "Medium", "emoji": "📈", "tone": "mid"}
            else:
                verdict = {"label": "Low", "emoji": "📉", "tone": "low"}

            output.append({
                "score":   score,
                "factors": [
                    {"key": f["feature"], "value": f["value"], "weight": f["importance"]}
                    for f in r.top_factors
                ],
                "metrics": {
                    "views":  r.predicted_views,
                    "likes":  r.predicted_likes,
                    "shares": r.predicted_shares,
                    "saves":  r.predicted_saves,
                },
                "verdict": verdict,
            })
        return {"virality": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Feedback loop endpoints
# ---------------------------------------------------------------------------
class FeedbackRequest(BaseModel):
    script:          dict
    predicted_score: float
    actual_views:    int
    actual_likes:    int
    actual_shares:   int
    actual_saves:    int
    platform:        str = "instagram"

@app.post("/api/feedback")
def api_feedback(req: FeedbackRequest):
    """
    Log real post performance after publishing.
    Pass the script dict + actual engagement numbers.
    Automatically triggers model retrain every 25 records.
    """
    from feedback_store import append, stats
    try:
        record = append(
            script          = req.script,
            predicted_score = req.predicted_score,
            actual_views    = req.actual_views,
            actual_likes    = req.actual_likes,
            actual_shares   = req.actual_shares,
            actual_saves    = req.actual_saves,
            platform        = req.platform,
        )
        return {
            "saved":       True,
            "record_id":   record["id"],
            "real_label":  record["real_label"],
            "delta":       record["delta"],
            "feedback_stats": stats(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/retrain")
def api_retrain():
    """Manually trigger model retrain blending all real feedback data."""
    from virality_model import train_model
    try:
        _, mae, r2, cv_mae, cv_std = train_model()
        # Invalidate cached model so next predict() loads fresh weights
        global _virality_model
        _virality_model = None
        return {
            "retrained": True,
            "test_mae":  round(mae, 2),
            "r2":        round(r2, 4),
            "cv_mae":    round(cv_mae, 2),
            "cv_std":    round(cv_std, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feedback/stats")
def api_feedback_stats():
    """Return stats on collected real feedback data."""
    from feedback_store import stats
    return stats()


PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")

class ImageRequest(BaseModel):
    prompt: str
    query: str = ""         # plain keyword for Pexels fallback
    aspect_ratio: str = "1:1"

@app.post("/api/generate-image")
def api_generate_image(req: ImageRequest):
    """
    Get an image for the Instagram post.
    Priority: Imagen 4 → Gemini image models → Pexels photo fallback.
    Returns { image_url, source }.
    """
    import base64, requests as http

    gemini_key = os.getenv("GEMINI_API_KEY", "")

    # --- 1. Try Imagen 4 (predict endpoint) ---
    if gemini_key:
        for imagen_model in ["imagen-4.0-generate-001", "imagen-4.0-fast-generate-001"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{imagen_model}:predict"
                r = http.post(
                    f"{url}?key={gemini_key}",
                    json={
                        "instances":  [{"prompt": req.prompt}],
                        "parameters": {"sampleCount": 1},
                    },
                    timeout=30,
                )
                if r.status_code == 200:
                    predictions = r.json().get("predictions", [])
                    if predictions:
                        img_b64  = predictions[0].get("bytesBase64Encoded", "")
                        mime     = predictions[0].get("mimeType", "image/png")
                        data_url = f"data:{mime};base64,{img_b64}"
                        print(f"[ImageAPI] Imagen 4 success ({imagen_model})")
                        return {"image_url": data_url, "source": "imagen4"}
                else:
                    print(f"[ImageAPI] {imagen_model} → {r.status_code}: {r.text[:100]}")
            except Exception as e:
                print(f"[ImageAPI] {imagen_model} error: {e}")

    # --- 2. Try Gemini image models (generateContent endpoint) ---
    if gemini_key:
        for model in ["gemini-3.1-flash-image", "gemini-2.5-flash-image", "gemini-3.1-flash-image-preview"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                r = http.post(
                    f"{url}?key={gemini_key}",
                    json={
                        "contents": [{"parts": [{"text": req.prompt}]}],
                        "generationConfig": {"responseModalities": ["IMAGE"]},
                    },
                    timeout=30,
                )
                if r.status_code == 200:
                    parts = r.json()["candidates"][0]["content"]["parts"]
                    for p in parts:
                        if "inlineData" in p:
                            mime     = p["inlineData"]["mimeType"]
                            img_b64  = p["inlineData"]["data"]
                            data_url = f"data:{mime};base64,{img_b64}"
                            print(f"[ImageAPI] Gemini image success ({model})")
                            return {"image_url": data_url, "source": "gemini"}
                else:
                    print(f"[ImageAPI] {model} → {r.status_code}")
            except Exception as e:
                print(f"[ImageAPI] {model} error: {e}")

    # --- 3. Fallback: Pexels photo search ---
    print("[ImageAPI] All AI models failed — falling back to Pexels")
    search_q = req.query or req.prompt.split(".")[0][:60]
    try:
        r = http.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": search_q, "per_page": 3, "orientation": "square"},
            timeout=15,
        )
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                photo_url = photos[0]["src"]["large"]
                return {"image_url": photo_url, "source": "pexels"}
    except Exception as e:
        print(f"[ImageAPI] Pexels error: {e}")

    raise HTTPException(status_code=503, detail="Image unavailable — try again shortly")


@app.get("/api/social/status")
def social_status():
    """Check which social platforms are configured."""
    from social_poster import get_config_status
    return get_config_status()


class InstagramPostRequest(BaseModel):
    caption:   str
    hashtags:  list[str] = []
    image_url: str = ""   # data URL or Pexels URL

class LinkedInPostRequest(BaseModel):
    text:      str
    hashtags:  list[str] = []
    image_url: str = ""

@app.post("/api/post/instagram")
def api_post_instagram(req: InstagramPostRequest):
    from social_poster import post_to_instagram
    result = post_to_instagram(
        caption   = req.caption,
        hashtags  = req.hashtags,
        image_url = req.image_url or None,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Post failed"))
    return result

@app.post("/api/post/linkedin")
def api_post_linkedin(req: LinkedInPostRequest):
    from social_poster import post_to_linkedin
    result = post_to_linkedin(
        text      = req.text,
        hashtags  = req.hashtags,
        image_url = req.image_url or None,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Post failed"))
    return result


# Serve saved images (for Instagram image hosting)
from fastapi.staticfiles import StaticFiles as _SF
_files_dir = Path(__file__).parent / "reels_output"
_files_dir.mkdir(exist_ok=True)
app.mount("/files", _SF(directory=str(_files_dir), html=False), name="files")


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve the React frontend (must be registered LAST)
# ---------------------------------------------------------------------------
FRONTEND = Path(__file__).parent.parent / "frontend"

if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Frontend not found. Place it at track2/frontend/"}


if __name__ == "__main__":
    import uvicorn
    print("\n  Ratefluencer API + Frontend")
    print("  → http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
