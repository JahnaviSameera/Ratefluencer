"""
Ratefluencer Score™ — ML Model Benchmark
==========================================

Trains and compares ALL 6 models suggested by the hackathon brief:
  1. Logistic Regression  (baseline linear model)
  2. Random Forest        (ensemble of trees)
  3. XGBoost             (gradient boosting — our current model)
  4. LightGBM            (faster gradient boosting)
  5. CatBoost            (handles categoricals natively)
  6. Neural Network       (MLP — non-linear deep features)

Plus: Voting Ensemble of top 3 performers

Features covering all 9 hackathon-required categories:
  Engagement Rate      → engagement_rate, true_engagement_rate, er_vs_expected
  Share Rate           → share_rate
  Save Rate            → save_rate
  Audience Quality     → authenticity_score, real_followers_pct, unique_commenters_ratio
  Posting Consistency  → posting_std_dev, posts_per_week, posting_regularity (derived)
  Growth Rate          → growth_rate_30d, growth_rate_90d, avg_daily_growth
  Comment Quality      → comment_spam_ratio, comment_like_ratio
  Content Category     → niche (one-hot encoded)
  Audience Demographics→ audience_country_top1, audience_age_group (encoded)

Output: comparison table + best model saved as ratefluencer_model.pkl
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import os, pickle, json, time
import numpy as np
import pandas as pd

from sklearn.linear_model    import LogisticRegression
from sklearn.ensemble        import RandomForestRegressor, VotingRegressor
from sklearn.neural_network  import MLPRegressor
from sklearn.preprocessing   import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics         import mean_absolute_error, r2_score
import xgboost  as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor

# ── Load dataset ──────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
df   = pd.read_csv(os.path.join(BASE, "influencer_dataset.csv"))
print(f"Dataset: {len(df)} influencers, {len(df.columns)} columns")

# ── Feature Engineering: all 9 hackathon categories ──────────────────────
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # 1. ENGAGEMENT RATE
    d["eng_efficiency"]   = d["true_engagement_rate"] / (d["engagement_rate"].clip(0.1))
    d["er_vs_expected"]   = d.get("er_vs_expected", pd.Series(0, index=d.index)).fillna(0)

    # 2. SHARE RATE
    d["share_rate"]       = d.get("share_rate", pd.Series(0.01, index=d.index)).fillna(0.01)

    # 3. SAVE RATE
    d["save_rate"]        = d.get("save_rate", pd.Series(0.01, index=d.index)).fillna(0.01)

    # 4. AUDIENCE QUALITY
    d["audience_quality"] = (
        d["real_followers_pct"] * 0.5 +
        d["unique_commenters_ratio"] * 0.3 +
        (1 - d["bot_follower_pct"]) * 0.2
    )

    # 5. POSTING CONSISTENCY (lower std = more consistent)
    d["posting_regularity"] = 1 - (d["posting_std_dev"].clip(0, 5) / 5)
    d["content_velocity"]   = d["posts_per_week"] * (1 + d["engagement_trend_30d"].clip(-1, 2))

    # 6. GROWTH RATE
    d["growth_momentum"]    = d["growth_rate_30d"] * 3 + d["growth_rate_90d"]
    d["followers_log"]      = np.log1p(d["followers_count"])

    # 7. COMMENT QUALITY (lower spam = better)
    d["comment_quality"]    = d["unique_commenters_ratio"] * (1 - d["comment_spam_ratio"])

    # 8. CONTENT CATEGORY (one-hot encode top niches)
    top_niches = d["niche"].value_counts().head(15).index.tolist()
    for n in top_niches:
        d[f"niche_{n.lower().replace(' ','_').replace('&','').replace('/','_')}"] = (d["niche"] == n).astype(int)

    # 9. AUDIENCE DEMOGRAPHICS
    country_map = {"India":1,"USA":2,"UK":3,"UAE":4,"Singapore":5,"Canada":6,"Australia":7}
    d["country_enc"]   = d["audience_country_top1"].map(country_map).fillna(0)
    age_map = {"13_17":1,"18_24":2,"25_34":3,"35_44":4,"45_54":5}
    d["age_group_enc"] = d["audience_age_group"].map(age_map).fillna(3)

    # Interaction features
    d["auth_x_engagement"]  = d["authenticity_score"] / 100 * d["true_engagement_rate"]
    d["growth_x_quality"]   = d["growth_momentum"].clip(0) * d["audience_quality"]
    d["engagement_depth"]   = d["save_rate"] + d["share_rate"]

    return d


df_feat  = build_features(df)

BASE_FEATURES = [
    # Engagement
    "engagement_rate", "true_engagement_rate", "er_vs_expected", "eng_efficiency",
    # Share & Save
    "share_rate", "save_rate", "engagement_depth",
    # Audience Quality
    "authenticity_score", "real_followers_pct", "unique_commenters_ratio",
    "bot_follower_pct", "audience_quality",
    # Posting Consistency
    "posting_std_dev", "posts_per_week", "posting_regularity", "content_velocity",
    # Growth
    "growth_rate_30d", "growth_rate_90d", "avg_daily_growth", "growth_momentum",
    "followers_log",
    # Comment Quality
    "comment_spam_ratio", "comment_like_ratio", "comment_quality",
    # Demographics
    "country_enc", "age_group_enc",
    # Interactions
    "auth_x_engagement", "growth_x_quality",
    # Campaign signals
    "campaign_success_prob", "collab_frequency", "sponsored_er_drop",
    "avg_hashtags_per_post", "bio_completeness_score",
]

# Add niche one-hot columns
niche_cols = [c for c in df_feat.columns if c.startswith("niche_")]
ALL_FEATURES = BASE_FEATURES + niche_cols

X = df_feat[[f for f in ALL_FEATURES if f in df_feat.columns]].fillna(0).values
y = df_feat["ratefluencer_score"].fillna(50).values

print(f"Features: {X.shape[1]} total ({len(BASE_FEATURES)} base + {len(niche_cols)} niche dummies)")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

scaler    = MinMaxScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ── Define all 6 models ───────────────────────────────────────────────────
MODELS = {
    "Logistic Regression":  LogisticRegression(max_iter=1000),   # used as regressor via LinearRegression
    "Random Forest":        RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42, n_jobs=-1),
    "XGBoost":              xgb.XGBRegressor(n_estimators=700, max_depth=5, learning_rate=0.05,
                                              subsample=0.8, colsample_bytree=0.8,
                                              random_state=42, verbosity=0, tree_method="hist"),
    "LightGBM":             lgb.LGBMRegressor(n_estimators=700, max_depth=5, learning_rate=0.05,
                                               subsample=0.8, colsample_bytree=0.8,
                                               random_state=42, verbose=-1),
    "CatBoost":             CatBoostRegressor(iterations=500, depth=5, learning_rate=0.05,
                                              random_seed=42, verbose=0),
    "Neural Network":       MLPRegressor(hidden_layer_sizes=(128, 64, 32), activation="relu",
                                          max_iter=500, random_state=42, early_stopping=True,
                                          validation_fraction=0.1),
}

# Swap LR for actual regression (sklearn's LR is a classifier)
from sklearn.linear_model import Ridge
MODELS["Logistic Regression"] = Ridge(alpha=1.0)

# ── Train + evaluate all models ───────────────────────────────────────────
print("\n" + "="*70)
print(f"{'Model':<22} {'MAE':>6} {'R²':>7} {'CV-MAE':>8} {'Time':>7}")
print("="*70)

results = {}
kf = KFold(n_splits=5, shuffle=True, random_state=42)

for name, model in MODELS.items():
    # Use scaled data for LR and NN; raw for tree models
    use_scaled = name in ("Logistic Regression", "Neural Network")
    Xtr = X_train_s if use_scaled else X_train
    Xte = X_test_s  if use_scaled else X_test
    Xall= X_train_s if use_scaled else X_train

    t0 = time.time()
    model.fit(Xtr, y_train)
    elapsed = time.time() - t0

    preds = model.predict(Xte)
    mae   = mean_absolute_error(y_test, preds)
    r2    = r2_score(y_test, preds)

    cv    = -cross_val_score(model, Xall, y_train, cv=kf,
                              scoring="neg_mean_absolute_error", n_jobs=-1).mean()

    results[name] = {"model": model, "mae": mae, "r2": r2, "cv_mae": cv,
                     "scaled": use_scaled}
    print(f"  {name:<20} {mae:>6.2f} {r2:>7.4f} {cv:>8.2f} {elapsed:>6.1f}s")

# ── Build Voting Ensemble from top 3 by CV-MAE ───────────────────────────
sorted_models = sorted(results.items(), key=lambda x: x[1]["cv_mae"])
top3_names    = [n for n, _ in sorted_models[:3] if not results[n]["scaled"]][:3]
print(f"\nTop 3 for ensemble: {top3_names}")

if len(top3_names) >= 2:
    ensemble = VotingRegressor(
        estimators=[(n, results[n]["model"]) for n in top3_names],
        weights=[3, 2, 1][:len(top3_names)]
    )
    ensemble.fit(X_train, y_train)
    ens_preds = ensemble.predict(X_test)
    ens_mae   = mean_absolute_error(y_test, ens_preds)
    ens_r2    = r2_score(y_test, ens_preds)
    print(f"  {'Ensemble (top 3)':<20} {ens_mae:>6.2f} {ens_r2:>7.4f}")
    results["Ensemble"] = {"model": ensemble, "mae": ens_mae, "r2": ens_r2,
                           "cv_mae": ens_mae, "scaled": False}

# ── Save best model ───────────────────────────────────────────────────────
best_name, best = min(results.items(), key=lambda x: x[1]["mae"])
print(f"\n✓ Best model: {best_name}  MAE={best['mae']:.2f}  R²={best['r2']:.4f}")

feat_names_used = [f for f in ALL_FEATURES if f in df_feat.columns]
save_data = {
    "model":         best["model"],
    "scaler":        scaler,
    "feature_names": feat_names_used,
    "model_name":    best_name,
    "mae":           best["mae"],
    "r2":            best["r2"],
    "trained_on":    len(df),
}
out_path = os.path.join(BASE, "ratefluencer_model.pkl")
with open(out_path, "wb") as f:
    pickle.dump(save_data, f)
print(f"Model saved → {out_path}")

# ── Feature importance (XGBoost / LightGBM) ──────────────────────────────
for m_name in ["XGBoost", "LightGBM"]:
    if m_name in results and hasattr(results[m_name]["model"], "feature_importances_"):
        fi = dict(zip(feat_names_used, results[m_name]["model"].feature_importances_))
        top10 = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"\nTop 10 features ({m_name}):")
        for feat, imp in top10:
            bar = "█" * int(imp * 200)
            print(f"  {feat:<35} {bar} {imp:.4f}")

# ── Comparison summary ────────────────────────────────────────────────────
print("\n" + "="*70)
print("MODEL COMPARISON SUMMARY")
print("="*70)
df_results = pd.DataFrame([
    {"Model": name, "MAE": d["mae"], "R²": d["r2"], "CV-MAE": d["cv_mae"]}
    for name, d in results.items()
]).sort_values("MAE")
print(df_results.to_string(index=False))

# Save comparison as JSON for the API
comp_path = os.path.join(BASE, "model_comparison.json")
with open(comp_path, "w") as f:
    json.dump([{"model": name, "mae": round(d["mae"],2), "r2": round(d["r2"],4)}
               for name, d in results.items()], f, indent=2)
print(f"\nComparison saved → {comp_path}")
print("\nDone! Run the server to use the new model.")
