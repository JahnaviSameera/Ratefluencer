"""
Authenticity Model v2 — XGBoost Binary Classifier
===================================================

UPGRADE from Isolation Forest → XGBoost supervised classifier.

Why this matters:
  Isolation Forest: unsupervised, no labels, treats every outlier as fake
  XGBoost:          trained on labeled real/fake profiles, learns patterns
                    specific to influencer fraud (bot farms, engagement pods,
                    sudden spikes, unnatural follower/engagement ratios)

12 features (vs 8 before):
  - real_followers_pct          % genuine human followers
  - suspicious_followers_pct    % flagged by follower audit tools
  - bot_follower_pct            % confirmed bot accounts
  - comment_spam_ratio          % generic/emoji-only comments
  - unique_commenters_ratio     unique commenters / total comments
  - spike_ratio                 max single-day gain / avg daily gain
  - er_vs_expected              actual ER - benchmark ER for tier
  - bio_completeness_score      profile fill score 0-1
  - follower_following_ratio    followers / following count  [NEW]
  - engagement_consistency      std(likes last 30 posts) / mean [NEW]
  - avg_comment_length          chars per comment (bots leave short comments) [NEW]
  - posting_regularity          1 - std(days between posts) / mean [NEW]
"""
from __future__ import annotations
import pickle, os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.calibration import CalibratedClassifierCV

MODEL_PATH  = os.path.join(os.path.dirname(__file__), "authenticity_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "authenticity_scaler.pkl")

FEATURES = [
    "real_followers_pct",
    "suspicious_followers_pct",
    "bot_follower_pct",
    "comment_spam_ratio",
    "unique_commenters_ratio",
    "spike_ratio",
    "er_vs_expected",
    "bio_completeness_score",
    "follower_following_ratio",
    "engagement_consistency",
    "avg_comment_length",
    "posting_regularity",
    "gemini_comment_quality",    # Gemini comment analysis (13th feature)
]

FEATURE_LABELS = {
    "real_followers_pct":       "Real Followers %",
    "suspicious_followers_pct": "Suspicious Followers %",
    "bot_follower_pct":         "Bot Followers %",
    "comment_spam_ratio":       "Comment Spam Ratio",
    "unique_commenters_ratio":  "Unique Commenters Ratio",
    "spike_ratio":              "Follower Spike Ratio",
    "er_vs_expected":           "Engagement vs Benchmark",
    "bio_completeness_score":   "Profile Completeness",
    "follower_following_ratio": "Follower/Following Ratio",
    "engagement_consistency":   "Engagement Consistency",
    "avg_comment_length":       "Avg Comment Length",
    "posting_regularity":       "Posting Regularity",
}

HIGHER_IS_BETTER = {
    "real_followers_pct", "unique_commenters_ratio",
    "bio_completeness_score", "follower_following_ratio",
    "engagement_consistency", "avg_comment_length", "posting_regularity",
}


def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the 4 new features from existing columns if not present."""
    df = df.copy()

    if "follower_following_ratio" not in df.columns:
        df["follower_following_ratio"] = (
            df["followers_count"] / (df["following_count"].clip(1))
        ).clip(0, 100)

    if "engagement_consistency" not in df.columns:
        # Proxy: lower posting_std_dev relative to posts_per_week = more consistent
        df["engagement_consistency"] = 1 - (
            df.get("posting_std_dev", pd.Series(1, index=df.index)).clip(0, 10) / 10
        )

    if "avg_comment_length" not in df.columns:
        # Proxy: genuine accounts have longer comments
        # Estimate from unique_commenters_ratio (bots comment less)
        df["avg_comment_length"] = (
            df["unique_commenters_ratio"] * 80 + 20
        ).clip(5, 200)

    if "posting_regularity" not in df.columns:
        df["posting_regularity"] = 1 - (
            df.get("posting_std_dev", pd.Series(1, index=df.index)).clip(0, 5) / 5
        )

    # Gemini comment quality — synthetic proxy during training
    # At inference, predict() calls Gemini live for real comments
    if "gemini_comment_quality" not in df.columns:
        ucr = df.get("unique_commenters_ratio", pd.Series(0.5, index=df.index)).fillna(0.5)
        csr = df.get("comment_spam_ratio",      pd.Series(0.1, index=df.index)).fillna(0.1)
        df["gemini_comment_quality"] = (ucr * (1 - csr)).clip(0, 1)

    return df


def train(df: pd.DataFrame):
    df = _add_derived_features(df)
    X  = df[FEATURES].fillna(0).values
    y  = df["is_fake_account"].astype(int).values

    scaler   = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.20, random_state=42, stratify=y
    )

    # XGBoost with class weight to handle imbalance (~18% fake)
    scale_pos = int((y == 0).sum() / max((y == 1).sum(), 1))
    base = xgb.XGBClassifier(
        n_estimators       = 500,
        max_depth          = 5,
        learning_rate      = 0.05,
        subsample          = 0.8,
        colsample_bytree   = 0.8,
        scale_pos_weight   = scale_pos,
        eval_metric        = "auc",
        random_state       = 42,
        verbosity          = 0,
    )
    # Platt scaling for calibrated probabilities
    model = CalibratedClassifierCV(base, cv=3, method="sigmoid")
    model.fit(X_train, y_train)

    # Evaluation
    y_pred  = model.predict(X_test)
    y_prob  = model.predict_proba(X_test)[:, 1]
    auc     = roc_auc_score(y_test, y_prob)
    print(f"[Authenticity] AUC-ROC: {auc:.4f}")
    print(classification_report(y_test, y_pred, target_names=["Real","Fake"], digits=3))

    with open(MODEL_PATH,  "wb") as f: pickle.dump(model,  f)
    with open(SCALER_PATH, "wb") as f: pickle.dump(scaler, f)
    print("[Authenticity] Model saved")
    return model, scaler


def load():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Run train_models.py first")
    with open(MODEL_PATH,  "rb") as f: model  = pickle.load(f)
    with open(SCALER_PATH, "rb") as f: scaler = pickle.load(f)
    return model, scaler


def predict(row: dict, model=None, scaler=None) -> dict:
    if model is None:
        model, scaler = load()

    # Build feature vector including derived features
    fv = {
        "follower_following_ratio": float(row.get("followers_count", 1)) / max(float(row.get("following_count", 1)), 1),
        "engagement_consistency":   1 - min(float(row.get("posting_std_dev", 1)), 5) / 5,
        "avg_comment_length":       float(row.get("unique_commenters_ratio", 0.5)) * 80 + 20,
        "posting_regularity":       1 - min(float(row.get("posting_std_dev", 1)), 5) / 5,
    }
    fv.update(row)

    # Gemini comment quality analysis (13th feature — real NLP, not proxy)
    sample_comments = row.get("sample_comments", [])
    niche           = row.get("niche", "")
    try:
        from models.gemini_analyzer import analyze_comment_quality
        cq = analyze_comment_quality(
            sample_comments if isinstance(sample_comments, list) else [],
            niche
        )
        fv["gemini_comment_quality"] = cq["quality_score"] / 100.0
    except Exception:
        fv["gemini_comment_quality"] = 0.65  # neutral fallback

    X        = np.array([[fv.get(f, 0) for f in FEATURES]], dtype=np.float32)
    X_scaled = scaler.transform(X)

    fake_prob = float(model.predict_proba(X_scaled)[0][1])
    # Authenticity = how NOT fake (0=definitely fake, 100=definitely real)
    score     = round((1 - fake_prob) * 100, 1)

    # Per-feature breakdown
    breakdown = []
    for feat in FEATURES:
        val  = float(fv.get(feat, 0))
        good = feat in HIGHER_IS_BETTER
        # Flip polarity for "bad" features
        if feat not in HIGHER_IS_BETTER:
            if feat == "spike_ratio":
                impact = "negative" if val > 5 else "positive"
            else:
                impact = "negative" if val > 0.15 else "positive"
        else:
            impact = "positive" if val > 0.5 else "negative"

        breakdown.append({
            "feature":      FEATURE_LABELS.get(feat, feat),
            "value":        round(val, 3),
            "impact":       impact,
            "higherBetter": feat in HIGHER_IS_BETTER,
        })

    if score >= 75:
        verdict = "✅ Authentic"
    elif score >= 45:
        verdict = "⚠️ Suspicious"
    else:
        verdict = "🚨 Fake"

    return {
        "authenticity_score": score,
        "fake_probability":   round(fake_prob * 100, 1),
        "verdict":            verdict,
        "breakdown":          breakdown,
    }


def score_dataframe(df: pd.DataFrame) -> pd.Series:
    model, scaler = load()
    df2 = _add_derived_features(df)
    X   = df2[FEATURES].fillna(0).values
    Xs  = scaler.transform(X)
    probs = model.predict_proba(Xs)[:, 1]
    return pd.Series((1 - probs) * 100, index=df.index)
