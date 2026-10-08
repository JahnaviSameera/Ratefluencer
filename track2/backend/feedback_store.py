"""
Ratefluencer — Feedback Store
==============================

Stores real post performance metrics alongside the script features that
were used to make the prediction. As you post content and observe actual
engagement, this data is fed back into the virality model so it learns
from real outcomes instead of synthetic data.

How it works:
  1. You generate scripts → virality model predicts a score
  2. You post the content on Instagram/TikTok/LinkedIn
  3. After 48-72h, you enter the actual views/likes/shares/saves
  4. feedback_store saves the record
  5. On next --retrain, the model blends real records (5× weight) with
     synthetic data → predictions get progressively more accurate

Storage: feedback_data.json  (plain JSON, easy to inspect/edit)
"""
from __future__ import annotations
import json, math, os
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_FILE   = "feedback_data.json"
RETRAIN_TRIGGER = 25   # auto-retrain after this many new real records


# ---------------------------------------------------------------------------
# Virality label from real engagement metrics
# ---------------------------------------------------------------------------
def compute_real_label(views: int, likes: int, shares: int, saves: int) -> float:
    """
    Convert raw engagement numbers to a 0-100 virality score.

    Formula based on industry benchmarks:
      - Engagement rate = (likes + shares×3 + saves×2) / views
      - 1% ER = average, 3% = good, 6% = viral (these are real IG benchmarks)
      - Also factors in absolute reach via log-scaled views

    Returns float 0-100.
    """
    if views <= 0:
        return 0.0

    # Weighted engagement rate (shares and saves worth more than likes)
    weighted_eng  = likes + shares * 3 + saves * 2
    eng_rate      = weighted_eng / views

    # Map engagement rate to 0-1 (6% ER = 1.0, above 6% capped)
    eng_score = min(eng_rate / 0.06, 1.0)

    # Log-scaled reach: 1K views = 0.25, 100K = 0.5, 1M = 0.75, 10M = 1.0
    reach_score = min(math.log1p(views) / math.log1p(10_000_000), 1.0)

    # Blend: engagement quality matters more than raw reach
    label = (0.65 * eng_score + 0.35 * reach_score) * 100
    return round(label, 1)


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def _load() -> list[dict]:
    if not Path(FEEDBACK_FILE).exists():
        return []
    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save(records: list[dict]) -> None:
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(records, f, indent=2)


def append(
    script: dict,
    predicted_score: float,
    actual_views:  int,
    actual_likes:  int,
    actual_shares: int,
    actual_saves:  int,
    platform: str = "instagram",
) -> dict:
    """
    Save one real-world outcome record.

    Returns the saved record (including computed real_label).
    Triggers auto-retrain if RETRAIN_TRIGGER new records have accumulated.
    """
    real_label = compute_real_label(actual_views, actual_likes, actual_shares, actual_saves)

    record = {
        "id":              len(_load()) + 1,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "platform":        platform,
        "trend_phrase":    script.get("trend_phrase", script.get("phrase", "")),
        "niche":           script.get("niche", ""),
        "urgency":         script.get("urgency", ""),
        "predicted_score": predicted_score,
        "real_label":      real_label,
        "delta":           round(real_label - predicted_score, 1),
        "actual": {
            "views":  actual_views,
            "likes":  actual_likes,
            "shares": actual_shares,
            "saves":  actual_saves,
        },
        # Store script content for feature re-extraction during retrain
        "script": {
            "hook":               _get(script, "hook"),
            "story":              _get(script, "story"),
            "insights":           _get(script, "insights", []),
            "cta":                _get(script, "cta"),
            "instagram_caption":  _get(script, "instagram_caption"),
            "instagram_hashtags": _get(script, "instagram_hashtags", []),
            "linkedin_post":      _get(script, "linkedin_post"),
            "thumbnail_title":    _get(script, "thumbnail_title"),
            "content_angle":      script.get("content_angle", ""),
            "trend_score":        script.get("trend_score", 50),
            "trend_urgency":      script.get("urgency", "rising"),
            "acceleration":       script.get("acceleration", 0),
            "niche":              script.get("niche", ""),
        },
    }

    records = _load()
    records.append(record)
    _save(records)
    print(f"[FeedbackStore] Saved record #{record['id']}  "
          f"predicted={predicted_score:.1f} → real={real_label:.1f}  "
          f"delta={record['delta']:+.1f}")

    # Check if auto-retrain threshold reached
    new_count = sum(1 for r in records if r.get("real_label") is not None)
    if new_count % RETRAIN_TRIGGER == 0 and new_count > 0:
        print(f"[FeedbackStore] {new_count} real records — triggering auto-retrain...")
        _auto_retrain()

    return record


def _get(script: dict, key: str, default=None):
    """Get from flat script or nested reel_script."""
    val = script.get(key)
    if val is None:
        reel = script.get("reel_script", {})
        ig   = script.get("instagram", {})
        li   = script.get("linkedin", {})
        th   = script.get("thumbnail", {})
        val  = reel.get(key) or ig.get(key.replace("instagram_","")) \
               or li.get(key.replace("linkedin_","")) \
               or th.get(key.replace("thumbnail_",""))
    return val if val is not None else default


def _auto_retrain():
    try:
        from virality_model import train_model
        train_model()
        print("[FeedbackStore] Auto-retrain complete.")
    except Exception as e:
        print(f"[FeedbackStore] Auto-retrain failed: {e}")


# ---------------------------------------------------------------------------
# Retrieval for training
# ---------------------------------------------------------------------------
def load_for_training() -> tuple[list[dict], list[float]]:
    """
    Returns (scripts, labels) for all records that have real engagement data.
    Used by virality_model.train_model() to blend with synthetic data.
    """
    records = _load()
    scripts, labels = [], []
    for r in records:
        if r.get("real_label") is not None and r.get("script"):
            scripts.append(r["script"])
            labels.append(r["real_label"])
    return scripts, labels


def stats() -> dict:
    records = _load()
    if not records:
        return {"total": 0, "message": "No feedback yet. Post content and log results to train on real data."}

    labels     = [r["real_label"] for r in records if r.get("real_label") is not None]
    predicted  = [r["predicted_score"] for r in records if r.get("predicted_score") is not None]
    deltas     = [r["delta"] for r in records if r.get("delta") is not None]

    import statistics
    return {
        "total":           len(records),
        "avg_real":        round(statistics.mean(labels), 1) if labels else 0,
        "avg_predicted":   round(statistics.mean(predicted), 1) if predicted else 0,
        "avg_delta":       round(statistics.mean(deltas), 1) if deltas else 0,
        "mae":             round(sum(abs(d) for d in deltas) / len(deltas), 2) if deltas else 0,
        "next_retrain_at": RETRAIN_TRIGGER - (len(records) % RETRAIN_TRIGGER),
        "platforms":       list({r.get("platform","unknown") for r in records}),
    }
