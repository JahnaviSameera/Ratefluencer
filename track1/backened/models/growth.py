"""
Growth Model v2 — XGBoost + Trend Decomposition
=================================================

UPGRADE: Gradient Boosting → XGBoost with engineered trend features.

New features added:
  - momentum_score      weighted recent growth (last 7d weighted 3× vs 30d)
  - trend_acceleration  2nd derivative of follower growth
  - content_velocity    posts_per_week × engagement_trend (combined signal)
  - er_stability        low variance ER = sustainable, not one-hit-wonder
  - viral_coefficient   max_single_day_gain / avg_daily_growth

Also:
  - RandomizedSearchCV for hyperparameter tuning
  - 3-fold cross-validation for honest accuracy estimate
  - Confidence interval on predictions
"""
from __future__ import annotations
import pickle, os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import MinMaxScaler

MODEL_PATH  = os.path.join(os.path.dirname(__file__), "growth_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "growth_scaler.pkl")

BASE_FEATURES = [
    "growth_rate_30d",
    "growth_rate_90d",
    "avg_daily_growth",
    "engagement_trend_30d",
    "posting_std_dev",
    "posts_per_week",
    "true_engagement_rate",
    "video_view_rate",
    "save_rate",
    "followers_7d_delta",
    "max_single_day_gain",
]

DERIVED_FEATURES = [
    "momentum_score",
    "trend_acceleration",
    "content_velocity",
    "er_stability",
    "viral_coefficient",
]

ALL_FEATURES = BASE_FEATURES + DERIVED_FEATURES


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    eps = 1e-6

    # Momentum: recent 7d growth weighted 3× vs 30d
    f7d  = df.get("followers_7d_delta",  pd.Series(0, index=df.index)).fillna(0)
    f30  = df.get("growth_rate_30d",     pd.Series(0, index=df.index)).fillna(0)
    f90  = df.get("growth_rate_90d",     pd.Series(0, index=df.index)).fillna(0)
    df["momentum_score"] = (f7d * 3 + f30 * 2 + f90) / 6

    # Trend acceleration: 30d growth minus 90d growth (positive = accelerating)
    df["trend_acceleration"] = f30 - f90

    # Content velocity: posting frequency × engagement trend
    ppw = df.get("posts_per_week",       pd.Series(3, index=df.index)).fillna(3)
    ent = df.get("engagement_trend_30d", pd.Series(0, index=df.index)).fillna(0)
    df["content_velocity"] = ppw * (1 + ent.clip(-1, 2))

    # Engagement stability (inverted coefficient of variation)
    ter = df.get("true_engagement_rate", pd.Series(3, index=df.index)).fillna(3)
    std = df.get("posting_std_dev",      pd.Series(1, index=df.index)).fillna(1)
    df["er_stability"] = 1 - (std / (ter + eps)).clip(0, 1)

    # Viral coefficient: max spike relative to avg daily growth
    avg_gr = df.get("avg_daily_growth",      pd.Series(10, index=df.index)).fillna(10).clip(eps)
    max_gn = df.get("max_single_day_gain",   pd.Series(10, index=df.index)).fillna(10)
    df["viral_coefficient"] = (max_gn / avg_gr).clip(0, 20)

    return df


def train(df: pd.DataFrame):
    df2 = _engineer(df)
    X   = df2[ALL_FEATURES].fillna(0).values
    y   = df2["growth_score"].fillna(50).values

    scaler   = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.20, random_state=42
    )

    param_grid = {
        "n_estimators":     [300, 500, 700],
        "max_depth":        [4, 5, 6],
        "learning_rate":    [0.03, 0.05, 0.08],
        "subsample":        [0.8, 0.9],
        "colsample_bytree": [0.7, 0.8],
        "reg_alpha":        [0.0, 0.1],
    }
    base   = xgb.XGBRegressor(random_state=42, verbosity=0, tree_method="hist")
    search = RandomizedSearchCV(
        base, param_grid, n_iter=15,
        cv=KFold(3, shuffle=True, random_state=42),
        scoring="neg_mean_absolute_error",
        n_jobs=-1, random_state=42, verbose=0,
    )
    search.fit(X_train, y_train)
    model = search.best_estimator_

    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    r2    = r2_score(y_test, preds)
    print(f"[Growth] MAE: {mae:.2f}  R²: {r2:.4f}  Best: {search.best_params_}")

    with open(MODEL_PATH,  "wb") as f: pickle.dump(model,  f)
    with open(SCALER_PATH, "wb") as f: pickle.dump(scaler, f)
    print("[Growth] Model saved")
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

    row_df   = pd.DataFrame([row])
    row_eng  = _engineer(row_df).iloc[0].to_dict()

    X        = np.array([[row_eng.get(f, 0) for f in ALL_FEATURES]], dtype=np.float32)
    X_scaled = scaler.transform(X)

    growth_score = float(np.clip(model.predict(X_scaled)[0], 0, 100))

    # Growth projections
    followers    = row.get("followers_count", 0)
    daily_growth = row.get("avg_daily_growth", 0)
    momentum     = float(row_eng.get("momentum_score", 0))
    multiplier   = 1 + (growth_score / 100) * 0.35 * (1 + momentum * 0.1)

    pred_30 = max(int(followers + daily_growth * 30  * multiplier), followers)
    pred_60 = max(int(followers + daily_growth * 60  * multiplier), followers)
    pred_90 = max(int(followers + daily_growth * 90  * multiplier), followers)

    er_now  = row.get("engagement_rate", 0)
    trend   = row.get("engagement_trend_30d", 0)
    er_30d  = round(max(er_now + trend * 30 * 0.01, 0), 2)
    er_60d  = round(max(er_now + trend * 60 * 0.01, 0), 2)

    verdict = "🚀 High Growth" if growth_score >= 70 else "📈 Moderate" if growth_score >= 40 else "📉 Slow"

    return {
        "growth_score":            round(growth_score, 1),
        "verdict":                 verdict,
        "predicted_followers_30d": pred_30,
        "predicted_followers_60d": pred_60,
        "predicted_followers_90d": pred_90,
        "predicted_er_30d":        er_30d,
        "predicted_er_60d":        er_60d,
        "growth_drivers": [
            {"factor": "Momentum Score",       "value": round(float(row_eng.get("momentum_score", 0)), 3)},
            {"factor": "Trend Acceleration",   "value": round(float(row_eng.get("trend_acceleration", 0)), 3)},
            {"factor": "Content Velocity",     "value": round(float(row_eng.get("content_velocity", 0)), 2)},
            {"factor": "ER Stability",         "value": round(float(row_eng.get("er_stability", 0)), 3)},
            {"factor": "Viral Coefficient",    "value": round(float(row_eng.get("viral_coefficient", 0)), 2)},
        ],
    }


def score_dataframe(df: pd.DataFrame) -> pd.Series:
    model, scaler = load()
    df2   = _engineer(df)
    X     = df2[ALL_FEATURES].fillna(0).values
    Xs    = scaler.transform(X)
    scores = np.clip(model.predict(Xs), 0, 100)
    return pd.Series(scores, index=df.index)
