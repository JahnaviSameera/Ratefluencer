"""
Brand Match Model v2 — Semantic Embedding Similarity
======================================================

UPGRADE from TF-IDF cosine sim → sentence-transformers.

Why this matters:
  TF-IDF: "fitness" ≠ "health"  (word overlap only)
  Embeddings: "fitness" ≈ "health" ≈ "wellness" ≈ "workout"
              (384-dim semantic space, trained on 1B+ sentences)

Pipeline:
  1. Build rich influencer profile text (niche + tone + hashtags + interests + past brands)
  2. Build brand brief text (category + product + audience + keywords + goal)
  3. Embed both with all-MiniLM-L6-v2
  4. Cosine similarity in 384-dim space
  5. Apply structured bonuses: niche match, age group, country, collab fatigue
  6. Output 0-100 score + human-readable match reasons
"""
from __future__ import annotations
import pickle, os, json
import numpy as np
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "brand_match_embedder.pkl")

# ── Semantic niche descriptors (richer than keywords alone) ──────────────────
NICHE_DESCRIPTIONS = {
    "Fitness":               "gym workout exercise weights training bodybuilding cardio strength muscle performance",
    "Health & Wellness":     "health healing wellness supplements vitamins immunity holistic natural remedies wellbeing",
    "Yoga & Meditation":     "yoga meditation mindfulness breathwork flexibility pose asana calm stress relief",
    "Nutrition & Diet":      "nutrition diet meal prep protein calories healthy eating weight loss macros food",
    "Fashion":               "outfit OOTD style fashion clothes wardrobe aesthetic streetwear trends designer",
    "Beauty & Skincare":     "skincare makeup foundation serum moisturizer beauty routine cosmetics GRWM glow",
    "Lifestyle Vlogging":    "vlog daily life morning routine productivity self improvement habits lifestyle",
    "Parenting & Family":    "parenting kids toddler mom dad baby family children motherhood",
    "Travel":                "travel adventure destinations hiking trekking mountains outdoor backpacking explore tourism",
    "Food & Cooking":        "cooking recipe food restaurant chef baking cuisine homemade delicious",
    "Home Decor & Interior": "home decor interior design room apartment renovation aesthetic furniture",
    "DIY & Crafts":          "DIY craft handmade build project woodworking tutorial how to make",
    "Technology":            "tech gadget smartphone app software coding developer review programming",
    "Gaming":                "gaming stream gameplay console PC game esports tournament twitch",
    "Finance & Investing":   "investing money savings portfolio stocks mutual fund wealth financial planning",
    "Entrepreneurship":      "startup founder entrepreneur hustle business revenue growth saas build",
    "Sports & Athletics":    "sports athlete training outdoor running hiking marathon conditioning performance gear",
    "Mental Health":         "mental health anxiety therapy self care healing mindfulness boundaries",
    "Music & Dance":         "music dance song performance choreography lyrics artist beat cover",
    "Comedy & Entertainment":"comedy funny meme relatable humor entertainment viral sketch joke",
}

CAMPAIGN_GOALS = {
    "Awareness":   "brand awareness reach impressions visibility recognition discovery",
    "Conversions": "sales purchase conversion ROI clicks leads revenue e-commerce",
    "Engagement":  "engagement community interaction comments shares saves viral content",
}

# Dynamic score adjustments per campaign goal — applied on top of semantic similarity
# These reward influencers whose STATS match what the campaign needs
GOAL_STAT_BOOST = {
    "Conversions": [("save_rate",              0.12, 0.03),   # (column, weight, normaliser)
                    ("true_engagement_rate",    0.05, 0.10)],
    "Awareness":   [("followers_count",         0.08, 1_000_000),
                    ("video_view_rate",          0.05, 0.40)],
    "Engagement":  [("unique_commenters_ratio",  0.10, 1.0),
                    ("engagement_trend_30d",     0.05, 2.0)],
    "Reach":       [("followers_count",          0.10, 1_000_000),
                    ("avg_likes",                0.05, 100_000)],
}

_embedder  = None
_df_embs   = None   # cached DataFrame embeddings


def _load_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _influencer_text(row: dict) -> str:
    """
    Build influencer profile text for embedding.
    Includes captions + bio so two influencers in the SAME niche
    (e.g. Fitness) but different content angles score differently
    against different campaigns.
    """
    niche    = row.get("niche", "")
    bio      = row.get("bio", "")
    captions = " ".join(_parse_list(row.get("sample_captions", "[]")))
    niche_desc = NICHE_DESCRIPTIONS.get(niche, "")
    parts = [
        bio,            bio,            # bio 2× — distinctive signal
        captions,       captions,       # captions 2× — actual content
        niche_desc,                     # niche keywords so Travel/Sports match correctly
        niche,
        row.get("content_tone", ""),
        " ".join(_parse_list(row.get("top_5_hashtags",       "[]"))),
        " ".join(_parse_list(row.get("audience_interests",   "[]"))),
        " ".join(_parse_list(row.get("past_brand_categories","[]"))),
    ]
    return " ".join(str(p) for p in parts if p).strip()


def _brand_text(brief: dict) -> str:
    """
    Build brand brief text for embedding.
    Product description is repeated so it drives the semantic direction,
    not the niche label which would just pull results toward one category.
    """
    goal = brief.get("campaign_goal", "Awareness")
    prod = brief.get("product_description", "").strip()
    kw   = brief.get("keywords", "")
    if isinstance(kw, list): kw = " ".join(kw)
    parts = [
        prod, prod, prod,               # repeat 3× — this is the core campaign signal
        brief.get("category", ""),
        brief.get("target_audience", ""),
        CAMPAIGN_GOALS.get(goal, goal),
        kw,
        # deliberately NOT including NICHE_DESCRIPTIONS — let product text decide
    ]
    return " ".join(str(p) for p in parts if p).strip()


def _parse_list(val) -> list:
    if isinstance(val, list): return val
    try: return json.loads(val) if isinstance(val, str) else []
    except: return []


def train(df: pd.DataFrame):
    """Pre-compute and cache embeddings for all influencer profiles."""
    model = _load_embedder()
    texts = [_influencer_text(row) for _, row in df.iterrows()]
    print(f"[BrandMatch] Computing semantic embeddings for {len(texts)} profiles...")
    embs = model.encode(texts, batch_size=64, show_progress_bar=False,
                        normalize_embeddings=True)
    ids  = df["influencer_id"].tolist()
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"embeddings": embs, "ids": ids}, f)
    print(f"[BrandMatch] Embeddings saved (shape: {embs.shape})")
    return model


def load():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Run train_models.py first")
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict(row: dict, brief: dict, cache: dict = None) -> dict:
    model = _load_embedder()
    inf_text   = _influencer_text(row)
    brand_text = _brand_text(brief)   # pure semantic — no Gemini in hot path

    inf_emb   = model.encode([inf_text],   normalize_embeddings=True)
    brand_emb = model.encode([brand_text], normalize_embeddings=True)
    semantic  = float((inf_emb @ brand_emb.T)[0][0])

    # Structured bonuses — kept small so semantic content dominates ranking
    brief_niche   = brief.get("niche", "").strip().lower()
    niche_bonus   = 0.05 if (brief_niche and row.get("niche","").lower() == brief_niche) else 0.0
    country_bonus = 0.05 if brief.get("target_country") == row.get("audience_country_top1") else 0.0
    collab_penalty= min(float(row.get("collab_frequency", 0)) / 6, 1.0) * 0.10

    # Age-group bonus using audience breakdown
    age_bonus = 0.0
    target_age = brief.get("target_age_group", "")
    if target_age:
        audience = row.get("audience", {})
        age_map  = {"18_24":"18-24","25_34":"25-34","35_44":"35-44","45_plus":"45+",
                    "18-24":"18-24","25-34":"25-34","35-44":"35-44","45+":"45+"}
        age_key  = age_map.get(target_age, target_age)
        if isinstance(audience, dict) and "age" in audience:
            age_pct = audience["age"].get(age_key, 0)
        else:
            age_pct = float(row.get(f"audience_age_{target_age}", 0))
        age_bonus = min(float(age_pct) / 100 * 0.30, 0.15)

    raw   = semantic + niche_bonus + age_bonus + country_bonus - collab_penalty
    score = float(np.clip(raw * 115, 0, 100))

    # Match reasons
    reasons = []
    if semantic > 0.45:
        reasons.append(f"✓ Strong semantic fit ({int(semantic*100)}% content alignment)")
    elif semantic > 0.25:
        reasons.append(f"✓ Moderate content alignment ({int(semantic*100)}%)")
    if niche_bonus > 0:
        reasons.append(f"✓ Exact niche match: {row.get('niche','').title()}")
    if age_bonus > 0.05:
        reasons.append(f"✓ Audience age aligns with target group")
    if country_bonus > 0:
        reasons.append(f"✓ Primary audience: {row.get('audience_country_top1','')}")
    if collab_penalty > 0.05:
        reasons.append(f"⚠ High collab frequency ({row.get('collab_frequency',0):.1f}/month)")
    if not reasons:
        reasons.append("Low semantic alignment with brand brief")

    verdict = "🎯 Excellent" if score >= 75 else "👍 Good" if score >= 50 else "⚠️ Weak"

    return {
        "brand_match_score": round(score, 1),
        "verdict":           verdict,
        "match_reasons":     reasons,
        "semantic_score":    round(semantic, 3),
    }


def rank_influencers(df: pd.DataFrame, brief: dict,
                     cache: dict = None, top_n: int = 20) -> pd.DataFrame:
    """Rank using pre-computed embeddings — fast pure semantic search."""
    model      = _load_embedder()
    brand_text = _brand_text(brief)   # no Gemini — instant, deterministic
    brand_emb  = model.encode([brand_text], normalize_embeddings=True)

    if cache:
        embs = cache["embeddings"]
        ids  = cache["ids"]
        # Filter to rows in df
        idx_map = {iid: i for i, iid in enumerate(ids)}
        df_ids  = df["influencer_id"].tolist()
        idxs    = [idx_map[i] for i in df_ids if i in idx_map]
        if idxs:
            sub_embs = embs[idxs]
            sims     = (brand_emb @ sub_embs.T)[0]
            df = df.copy()
            df["_sem"] = list(sims) + [0] * (len(df) - len(sims))
        else:
            df = df.copy(); df["_sem"] = 0.0
    else:
        # Fallback: encode on the fly
        texts     = [_influencer_text(r) for _, r in df.iterrows()]
        inf_embs  = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        sims      = (brand_emb @ inf_embs.T)[0]
        df        = df.copy()
        df["_sem"] = list(sims)

    # Apply bonuses — small so semantic content drives ranking, not niche filter
    niche = brief.get("niche", "").strip().lower()
    ctry  = brief.get("target_country", "")
    # Semantic + structural match score (0-100)
    df["brand_match_score"] = np.clip(
        (df["_sem"]
         + (df["niche"].str.lower() == niche).astype(float) * (0.05 if niche else 0)
         + (df["audience_country_top1"] == ctry).astype(float) * 0.05
         - df["collab_frequency"].clip(0, 6) / 6 * 0.05
        ) * 115, 0, 100
    )

    # Quality-weighted final ranking score
    # A suspicious low-quality influencer should never rank above
    # a genuine high-quality one even if their niche match is slightly better.
    #
    # Formula: brand_match × (0.35 + 0.65 × quality_index)
    #   quality_index = average of normalised authenticity + ratefluencer score
    #   → a WEAK influencer (auth=42, rf=30) gets multiplier 0.35 + 0.65×0.36 = 0.58
    #   → a STRONG influencer (auth=85, rf=82) gets multiplier 0.35 + 0.65×0.84 = 0.90
    auth_n = df["authenticity_score"].clip(0, 100) / 100
    rf_n   = df["ratefluencer_score"].clip(0, 100) / 100
    quality_index = (auth_n * 0.55 + rf_n * 0.45)   # authenticity weighted higher
    df["_rank_score"] = df["brand_match_score"] * (0.35 + 0.65 * quality_index)

    df.drop(columns=["_sem"], inplace=True)
    result = df.nlargest(top_n, "_rank_score").reset_index(drop=True)
    result.drop(columns=["_rank_score"], inplace=True)
    return result
