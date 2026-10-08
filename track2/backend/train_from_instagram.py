"""
Ratefluencer — Instagram Dataset Trainer
=========================================

Trains/updates the virality model using real Instagram captions from
the kkcosmos/instagram-images-with-captions HuggingFace dataset.

What this does:
  1. Loads the dataset and inspects columns
  2. Builds a LIVE semantic corpus (replaces 20 hardcoded headlines
     with up to 2000 real IG captions → much better hook similarity)
  3. Extracts real caption features (length, hashtags, sentiment, etc.)
  4. Assigns virality pseudo-labels:
       - If dataset has likes/comments → real engagement label
       - Otherwise → quality-based pseudo-label from feature scores
  5. Trains XGBoost blending: real IG data (10×) + synthetic (1×)
  6. Saves updated model + corpus to disk

Run:
    python train_from_instagram.py
    python train_from_instagram.py --sample 5000   # faster, fewer records
    python train_from_instagram.py --inspect        # just print schema
"""
from __future__ import annotations
import sys, re, math, json, pickle, os, argparse
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from datasets import load_dataset

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
HASHTAG_RE = re.compile(r"#\w+")
EMOJI_RE   = re.compile(
    "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+"
)

CORPUS_PATH = "instagram_corpus.pkl"   # saved semantic corpus
MODEL_PATH  = "virality_model.pkl"


def clean(text: str) -> str:
    return (text or "").strip()


def extract_hashtags(text: str) -> list[str]:
    return HASHTAG_RE.findall(text or "")


def count_words(text: str) -> int:
    return len((text or "").split())


def has_emoji(text: str) -> bool:
    return bool(EMOJI_RE.search(text or ""))


def has_number(text: str) -> bool:
    return bool(re.search(r"\d", text or ""))


def has_question(text: str) -> bool:
    return (text or "").strip().endswith("?")


def has_power_word(text: str) -> bool:
    POWER = {"secret","hack","revealed","nobody","mistake","truth","dead",
             "shocking","warning","trick","free","best","worst","only","first"}
    t = (text or "").lower()
    return any(w in t for w in POWER)


def count_sentences(text: str) -> int:
    return max(len(re.findall(r"[.!?]+", text or "")), 1)


def bell(x: float, ideal: float, spread: float) -> float:
    return math.exp(-0.5 * ((x - ideal) / spread) ** 2)


# ---------------------------------------------------------------------------
# Pseudo-label when no engagement data available
# Based on caption quality features — better caption = higher baseline
# ---------------------------------------------------------------------------
def pseudo_label(caption: str, hashtags: list[str]) -> float:
    """
    Estimate a virality label (0-100) purely from caption quality signals.
    This is NOT a ground truth — it teaches the model what 'good' looks like.
    When real engagement data is available, this is replaced by the real label.
    """
    wc      = count_words(caption)
    htags   = len(hashtags)
    emoji   = float(has_emoji(caption))
    num     = float(has_number(caption))
    quest   = float(has_question(caption))
    pw      = float(has_power_word(caption))
    sents   = count_sentences(caption)

    # Feature scores (all 0-1)
    len_sc  = bell(wc,   50.0, 20.0)    # sweet spot 40-60 words
    htag_sc = bell(htags, 11.0,  4.0)   # sweet spot 10-12 tags
    sent_sc = bell(sents,  5.0,  3.0)   # ~5 sentences

    quality = (
        0.25 * len_sc  +
        0.20 * htag_sc +
        0.15 * emoji   +
        0.15 * num     +
        0.10 * quest   +
        0.10 * pw      +
        0.05 * sent_sc
    )
    # Map 0-1 quality to 35-75 range (real IG captions are not extreme)
    return round(35.0 + quality * 40.0, 1)


def real_label(likes: int, comments: int) -> float:
    """Convert real engagement to 0-100 virality score."""
    if likes <= 0 and comments <= 0:
        return None
    # weighted engagement: comments worth 5× likes (intent signal)
    eng = likes + comments * 5
    # log-scale: 100 eng=40, 1K=55, 10K=70, 100K=85, 1M=100
    score = min(math.log1p(eng) / math.log1p(1_000_000) * 100, 100.0)
    return round(score, 1)


# ---------------------------------------------------------------------------
# Build training record from one dataset row
# ---------------------------------------------------------------------------
def row_to_training_record(row: dict, label: float) -> dict:
    """
    Convert a raw dataset row into a script-like dict compatible with
    virality_model.extract_features().
    The caption is used as hook + instagram_caption.
    """
    caption   = clean(row.get("caption") or row.get("text") or
                      row.get("post_text") or row.get("description") or "")
    hashtags  = extract_hashtags(caption)
    # Remove hashtags from caption body for cleaner feature extraction
    body      = HASHTAG_RE.sub("", caption).strip()
    sentences = body.split(".")
    hook      = sentences[0].strip() if sentences else body[:100]

    return {
        "hook":               hook,
        "story":              body[:300],
        "insights":           [],
        "cta":                sentences[-1].strip() if len(sentences) > 1 else "",
        "instagram_caption":  caption,
        "instagram_hashtags": hashtags,
        "linkedin_post":      body,
        "thumbnail_title":    hook[:30],
        "content_angle":      hook,
        "trend_score":        55.0,          # neutral — dataset doesn't have trend data
        "trend_urgency":      "rising",
        "acceleration":       0.0,
        "niche":              "creator economy",
        "_label":             label,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample",  type=int, default=3000,
                        help="Number of dataset records to use (default 3000)")
    parser.add_argument("--inspect", action="store_true",
                        help="Just print dataset schema and exit")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("Ratefluencer — Instagram Dataset Trainer")
    print(f"{'='*60}\n")

    # --- Load dataset ---
    split = f"train[:{args.sample}]"
    print(f"Loading kkcosmos/instagram-images-with-captions ({split})...")
    ds = load_dataset("kkcosmos/instagram-images-with-captions", split=split)
    print(f"Loaded {len(ds)} records")
    print(f"Columns: {ds.column_names}")

    if args.inspect:
        print("\nSample record:")
        for k, v in ds[0].items():
            if isinstance(v, str):
                print(f"  {k}: {repr(v[:150])}")
            else:
                print(f"  {k}: {type(v).__name__}")
        return

    # --- Detect engagement columns ---
    cols        = set(ds.column_names)
    has_likes   = any(c in cols for c in ["likes","like_count","num_likes","likes_count"])
    has_comments= any(c in cols for c in ["comments","comment_count","num_comments"])
    likes_col   = next((c for c in ["likes","like_count","num_likes","likes_count"] if c in cols), None)
    comment_col = next((c for c in ["comments","comment_count","num_comments"] if c in cols), None)

    caption_col = next((c for c in ["caption","text","post_text","description"] if c in cols), None)
    if not caption_col:
        print("ERROR: no caption column found in dataset")
        return

    print(f"\nCaption column : {caption_col}")
    print(f"Likes column   : {likes_col or 'NOT FOUND (using pseudo-labels)'}")
    print(f"Comments column: {comment_col or 'NOT FOUND'}")

    # --- Build corpus (for semantic similarity) ---
    print(f"\nBuilding semantic corpus from {min(len(ds),2000)} captions...")
    corpus = []
    for row in ds.select(range(min(len(ds), 2000))):
        cap = clean(row.get(caption_col, ""))
        if not cap or len(cap) < 20:
            continue
        # Extract first sentence as headline-like phrase
        first = cap.split(".")[0].strip()
        if 10 < len(first) < 200:
            corpus.append(first)
        # Also add caption without hashtags
        body = HASHTAG_RE.sub("", cap).strip()
        if 20 < len(body) < 300:
            corpus.append(body[:200])

    corpus = list(dict.fromkeys(corpus))[:2000]   # dedup, cap at 2000
    print(f"Corpus built: {len(corpus)} unique phrases")

    with open(CORPUS_PATH, "wb") as f:
        pickle.dump(corpus, f)
    print(f"Corpus saved → {CORPUS_PATH}")

    # --- Build training records ---
    print(f"\nExtracting features from {len(ds)} records...")
    from virality_model import extract_features, ViralityFeatures

    X_list, y_list = [], []
    skipped = 0

    for i, row in enumerate(ds):
        cap  = clean(row.get(caption_col, ""))
        if not cap or len(cap) < 15:
            skipped += 1
            continue

        tags = extract_hashtags(cap)

        # Compute label
        if likes_col:
            lk = int(row.get(likes_col) or 0)
            cm = int(row.get(comment_col) or 0) if comment_col else 0
            label = real_label(lk, cm)
            if label is None:
                label = pseudo_label(cap, tags)
        else:
            label = pseudo_label(cap, tags)

        script = row_to_training_record(row, label)

        try:
            feats = extract_features(script, use_semantic=False)  # skip ST for speed
            X_list.append(feats.to_array())
            y_list.append(label)
        except Exception as e:
            skipped += 1

        if (i + 1) % 500 == 0:
            print(f"  Processed {i+1}/{len(ds)}  (skipped {skipped})")

    print(f"\nExtracted {len(X_list)} training records  ({skipped} skipped)")

    if len(X_list) < 50:
        print("ERROR: too few records to train. Check dataset format.")
        return

    X_real = np.array(X_list, dtype=np.float32)
    y_real = np.array(y_list,  dtype=np.float32)

    label_source = "REAL engagement" if likes_col else "pseudo-labels"
    print(f"Label source: {label_source}")
    print(f"Label range:  {y_real.min():.1f} – {y_real.max():.1f}  "
          f"mean={y_real.mean():.1f}  std={y_real.std():.1f}")

    # --- Train model blending IG data (10×) + synthetic ---
    print("\nTraining virality model with Instagram data...")
    from virality_model import generate_training_data, MODEL_PATH as MP
    from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
    from sklearn.metrics import mean_absolute_error, r2_score
    import xgboost as xgb

    print("Generating 5000 synthetic samples for balance...")
    X_syn, y_syn = generate_training_data(5000)

    # Repeat real records 10× so they dominate the synthetic baseline
    X_real_rep = np.repeat(X_real, 10, axis=0)
    y_real_rep = np.repeat(y_real, 10)

    X_all = np.vstack([X_syn, X_real_rep])
    y_all = np.concatenate([y_syn, y_real_rep])
    print(f"Total training set: {len(X_all)} samples "
          f"({len(X_real_rep)} from Instagram, {len(X_syn)} synthetic)")

    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.15, random_state=42
    )

    param_dist = {
        "n_estimators":     [500, 700, 1000],
        "max_depth":        [4, 5, 6],
        "learning_rate":    [0.03, 0.05, 0.08],
        "subsample":        [0.8, 0.9],
        "colsample_bytree": [0.7, 0.8],
        "reg_alpha":        [0.0, 0.1],
        "reg_lambda":       [1.0, 2.0],
    }
    base = xgb.XGBRegressor(random_state=42, verbosity=0, tree_method="hist")
    search = RandomizedSearchCV(
        base, param_dist, n_iter=20,
        cv=KFold(n_splits=5, shuffle=True, random_state=42),
        scoring="neg_mean_absolute_error",
        n_jobs=-1, random_state=42, verbose=0,
    )
    print("Running hyperparameter search (this takes ~2 min)...")
    search.fit(X_train, y_train)
    model = search.best_estimator_

    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    r2    = r2_score(y_test, preds)
    print(f"\nTest MAE: {mae:.2f}  |  R²: {r2:.4f}")
    print(f"Best params: {search.best_params_}")

    from sklearn.model_selection import cross_val_score
    cv = -cross_val_score(model, X_all, y_all, cv=5,
                          scoring="neg_mean_absolute_error", n_jobs=-1)
    print(f"5-fold CV MAE: {cv.mean():.2f} ± {cv.std():.2f}")

    with open(MP, "wb") as f:
        pickle.dump({"model": model, "cv_mae": cv.mean(), "cv_std": cv.std(),
                     "trained_on": "instagram+synthetic",
                     "n_real": len(X_list), "label_source": label_source}, f)
    print(f"\nModel saved → {MP}")
    print("\nDone. The virality model is now trained on real Instagram data.")
    print("The semantic corpus has also been updated.")
    print("Restart api_server.py to pick up the new model.")


if __name__ == "__main__":
    main()
