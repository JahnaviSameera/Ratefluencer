"""
Ratefluencer Score™ v2 — XGBoost + Feature Interactions + Calibration
=======================================================================

UPGRADE:
  - 16 raw features → 24 features including cross-product interactions
  - RandomizedSearchCV hyperparameter tuning
  - 5-fold CV for honest accuracy estimate
  - Feature importance for per-influencer explanations

Key interaction features added:
  auth_x_engagement   — high engagement only matters if authentic
  growth_x_er         — growing AND highly engaged = top tier
  campaign_x_auth     — campaign success needs authentic base
  reach_quality       — followers × true_er (absolute impact)
  engagement_depth    — save + share (deep engagement signals)
"""
from __future__ import annotations
import pickle, os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.metrics import mean_absolute_error, r2_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ratefluencer_model.pkl")

BASE_FEATURES = [
    "true_engagement_rate",
    "authenticity_score",
    "growth_score",
    "campaign_success_prob",
    "real_followers_pct",
    "posting_std_dev",
    "save_rate",
    "share_rate",
    "video_view_rate",
    "comment_like_ratio",
    "er_vs_expected",
    "unique_commenters_ratio",
    "sponsored_er_drop",
    "bio_completeness_score",
    "avg_hashtags_per_post",
    "collab_frequency",
]

INTERACTION_FEATURES = [
    "auth_x_engagement",
    "growth_x_er",
    "campaign_x_auth",
    "reach_quality",
    "content_consistency",
    "engagement_depth",
    "comment_quality",
    "niche_authority",
    "gemini_authority",      # Gemini bio/caption credibility score
    "gemini_roi_score",      # Gemini campaign ROI prediction
]

ALL_FEATURES = BASE_FEATURES + INTERACTION_FEATURES


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    ter  = df.get("true_engagement_rate",   pd.Series(3,   index=df.index)).fillna(3)
    auth = df.get("authenticity_score",     pd.Series(70,  index=df.index)).fillna(70)
    grw  = df.get("growth_score",           pd.Series(50,  index=df.index)).fillna(50)
    camp = df.get("campaign_success_prob",  pd.Series(0.5, index=df.index)).fillna(0.5)
    flw  = df.get("followers_count",        pd.Series(10000,index=df.index)).fillna(10000)
    std  = df.get("posting_std_dev",        pd.Series(1,   index=df.index)).fillna(1)
    sv   = df.get("save_rate",              pd.Series(0,   index=df.index)).fillna(0)
    sh   = df.get("share_rate",             pd.Series(0,   index=df.index)).fillna(0)
    ucr  = df.get("unique_commenters_ratio",pd.Series(0.5, index=df.index)).fillna(0.5)
    csr  = df.get("comment_spam_ratio",     pd.Series(0.1, index=df.index)).fillna(0.1)
    bio  = df.get("bio_completeness_score", pd.Series(0.7, index=df.index)).fillna(0.7)
    erd  = df.get("sponsored_er_drop",      pd.Series(0.1, index=df.index)).fillna(0.1)

    df["auth_x_engagement"]   = auth / 100 * ter / 10
    df["growth_x_er"]         = grw  / 100 * ter / 10
    df["campaign_x_auth"]     = camp * auth / 100
    df["reach_quality"]       = (flw * ter / 100 / 1_000_000).clip(0, 100)
    df["content_consistency"] = 1 - std.clip(0, 5) / 5
    df["engagement_depth"]    = (sv + sh).clip(0, 0.2) / 0.2
    df["comment_quality"]     = ucr * (1 - csr)
    df["niche_authority"]     = bio * (1 - erd.clip(0, 0.5) / 0.5)

    # Gemini features — use precomputed column if present, else synthetic proxy
    if "gemini_authority" not in df.columns:
        df["gemini_authority"] = (bio * 0.6 + ucr * 0.4) * 100  # synthetic proxy
    if "gemini_roi_score" not in df.columns:
        df["gemini_roi_score"] = (auth / 100 * camp * 100).clip(0, 100)  # synthetic proxy

    return df


def train(df: pd.DataFrame):
    df2 = _engineer(df)
    X   = df2[ALL_FEATURES].fillna(0).values
    y   = df2["ratefluencer_score"].fillna(50).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42
    )

    param_grid = {
        "n_estimators":     [400, 600, 800, 1000],
        "max_depth":        [4, 5, 6],
        "learning_rate":    [0.03, 0.05, 0.08],
        "subsample":        [0.8, 0.9],
        "colsample_bytree": [0.7, 0.8],
        "reg_alpha":        [0.0, 0.1, 0.3],
        "reg_lambda":       [0.5, 1.0, 2.0],
        "min_child_weight": [1, 3, 5],
    }
    base   = xgb.XGBRegressor(random_state=42, verbosity=0, tree_method="hist")
    search = RandomizedSearchCV(
        base, param_grid, n_iter=20,
        cv=KFold(5, shuffle=True, random_state=42),
        scoring="neg_mean_absolute_error",
        n_jobs=-1, random_state=42, verbose=0,
    )
    search.fit(X_train, y_train)
    model = search.best_estimator_

    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    r2    = r2_score(y_test, preds)
    print(f"[RatefluencerScore] MAE: {mae:.2f}  R²: {r2:.4f}")

    fi   = dict(zip(ALL_FEATURES, model.feature_importances_))
    top5 = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:5]
    print("[RatefluencerScore] Top features:", {k: round(v,3) for k,v in top5})

    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": model, "feature_names": ALL_FEATURES}, f)
    print("[RatefluencerScore] Model saved")
    return model


def load():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Run train_models.py first")
    with open(MODEL_PATH, "rb") as f:
        data = pickle.load(f)
    return data["model"] if isinstance(data, dict) else data


def predict(row: dict, model=None) -> dict:
    if model is None:
        model = load()

    # Live Gemini enrichment — replaces synthetic proxies at inference time
    enriched = dict(row)
    try:
        from models.gemini_analyzer import analyze_bio_authority, predict_campaign_roi
        bio    = row.get("bio", "")
        niche  = row.get("niche", "")
        caps   = row.get("sample_captions", [])
        auth   = analyze_bio_authority(bio, niche, caps)
        enriched["gemini_authority"] = auth.get("authority_score", 60)
        # ROI uses empty brief for standalone profile scoring
        roi    = predict_campaign_roi(row, {"category": niche, "campaign_goal": "Awareness"})
        enriched["gemini_roi_score"] = roi.get("roi_score", 60)
    except Exception:
        enriched.setdefault("gemini_authority", 60)
        enriched.setdefault("gemini_roi_score", 60)

    row_df  = pd.DataFrame([enriched])
    row_eng = _engineer(row_df).iloc[0].to_dict()
    X       = np.array([[row_eng.get(f, 0) for f in ALL_FEATURES]], dtype=np.float32)
    score   = float(np.clip(model.predict(X)[0], 0, 100))

    imps      = model.feature_importances_
    breakdown = sorted(
        [{"feature":    f,
          "importance": round(float(imp), 4),
          "value":      round(float(row_eng.get(f, 0)), 3),
          "impact":     round(float(imp * row_eng.get(f, 0) * 100), 2)}
         for f, imp in zip(ALL_FEATURES, imps)],
        key=lambda x: x["impact"], reverse=True
    )

    return {
        "ratefluencer_score": round(score, 1),
        "top_drivers":        breakdown[:5],
        "weak_points":        breakdown[-3:],
    }


def score_dataframe(df: pd.DataFrame) -> pd.Series:
    model = load()
    df2   = _engineer(df)
    X     = df2[ALL_FEATURES].fillna(0).values
    return pd.Series(np.clip(model.predict(X), 0, 100), index=df.index)
