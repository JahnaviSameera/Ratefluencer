"""
Enrich influencer dataset with REAL caption content
=====================================================

Pulls real Instagram captions from the HuggingFace dataset,
clusters them by topic using sentence-transformers + K-means,
then assigns 2-3 real captions per influencer profile.

This replaces the fake "gym lover sharing workouts" captions
with real posted content — so brand matching actually reflects
what the influencer talks about.

Run:
    python enrich_from_real_posts.py
    (re-run train_models.py after this to retrain on enriched data)
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import os, json, pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# ── Load real Instagram captions ──────────────────────────────────────────
def load_real_captions(n: int = 5000) -> list[str]:
    """Load real captions from HuggingFace dataset."""
    print(f"Loading {n} real Instagram captions from HuggingFace...")
    from datasets import load_dataset
    ds = load_dataset("kkcosmos/instagram-images-with-captions",
                      split=f"train[:{n}]")
    captions = [r["caption"].strip() for r in ds if r.get("caption","").strip()]
    print(f"Loaded {len(captions)} real captions")
    return captions


# ── Niche keyword clusters for assignment ─────────────────────────────────
NICHE_SEED_PHRASES = {
    "Fitness":              "gym workout exercise weights training squats deadlift cardio reps sets",
    "Health & Wellness":    "health healing natural remedy wellness supplements vitamins gut health",
    "Yoga & Meditation":    "yoga meditation mindfulness breathwork chakra flexibility pose asana",
    "Nutrition & Diet":     "meal prep protein macros calories diet nutrition healthy eating recipe",
    "Fashion":              "outfit OOTD style look fashion clothes wardrobe aesthetic streetwear",
    "Beauty & Skincare":    "skincare makeup foundation blush serum moisturizer SPF GRWM glam",
    "Lifestyle Vlogging":   "day in my life vlog morning routine productivity daily life habits",
    "Parenting & Family":   "parenting kids toddler mom dad baby family children motherhood",
    "Travel":               "travel destination trip adventure explore beach mountain city wanderlust",
    "Food & Cooking":       "recipe cooking food homemade delicious restaurant dinner lunch chef",
    "Home Decor & Interior":"home decor interior design room apartment aesthetic cozy aesthetic",
    "DIY & Crafts":         "DIY craft handmade build project tutorial step by step how to make",
    "Technology":           "tech gadget smartphone app software review unboxing coding developer",
    "Gaming":               "gaming stream twitch gameplay console PC game review esports win",
    "Finance & Investing":  "money invest savings portfolio stocks mutual fund wealth financial",
    "Entrepreneurship":     "startup founder business entrepreneur hustle build revenue growth",
    "Sports & Athletics":   "sports athlete training match game score performance conditioning",
    "Mental Health":        "mental health anxiety depression therapy self care healing boundaries",
    "Music & Dance":        "music dance song cover performance lyrics beat studio choreography",
    "Comedy & Entertainment":"funny comedy meme relatable joke viral entertainment laugh humor",
}


def cluster_captions_to_niches(captions: list[str],
                                 model: SentenceTransformer,
                                 batch_size: int = 128) -> dict[str, list[str]]:
    """
    Assign each real caption to its closest niche using cosine similarity
    against niche seed phrases.
    """
    print("Embedding real captions...")
    cap_embs = model.encode(captions, batch_size=batch_size,
                            show_progress_bar=True, normalize_embeddings=True)

    print("Embedding niche seeds...")
    niches      = list(NICHE_SEED_PHRASES.keys())
    seed_texts  = [NICHE_SEED_PHRASES[n] for n in niches]
    seed_embs   = model.encode(seed_texts, normalize_embeddings=True)

    # Cosine sim: (n_captions × n_niches)
    sims        = cap_embs @ seed_embs.T
    best_niche  = sims.argmax(axis=1)

    niche_captions: dict[str, list[str]] = {n: [] for n in niches}
    for idx, niche_idx in enumerate(best_niche):
        niche_captions[niches[niche_idx]].append(captions[idx])

    for n, caps in niche_captions.items():
        print(f"  {n:<32} {len(caps):>4} real captions assigned")

    return niche_captions


def enrich_dataset(df: pd.DataFrame,
                   niche_captions: dict[str, list[str]],
                   rng: np.random.Generator) -> pd.DataFrame:
    """
    Replace synthetic sample_captions with real ones from the matching niche cluster.
    """
    df = df.copy()
    new_captions = []
    for _, row in df.iterrows():
        niche = row.get("niche", "")
        pool  = niche_captions.get(niche, [])
        if len(pool) >= 2:
            picked = list(rng.choice(pool, size=2, replace=False))
        elif pool:
            picked = pool[:1]
        else:
            picked = [f"Content about {niche.lower()}"]
        new_captions.append(json.dumps(picked))
    df["sample_captions"] = new_captions
    return df


def main():
    rng = np.random.default_rng(42)

    dataset_path = os.path.join(os.path.dirname(__file__), "influencer_dataset.csv")
    if not os.path.exists(dataset_path):
        print("ERROR: Run generate_dataset.py first")
        return

    df = pd.read_csv(dataset_path)
    print(f"Dataset: {len(df)} profiles")

    # Load real captions
    real_captions = load_real_captions(n=5000)

    # Load sentence-transformer
    print("Loading sentence-transformer...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Cluster real captions to niches
    niche_caps = cluster_captions_to_niches(real_captions, model)

    # Enrich dataset
    print("\nEnriching dataset with real captions...")
    df_enriched = enrich_dataset(df, niche_caps, rng)

    # Save enriched dataset
    df_enriched.to_csv(dataset_path, index=False)
    print(f"Enriched dataset saved → {dataset_path}")

    # Also update Excel
    xl_path = dataset_path.replace(".csv", ".xlsx")
    niches  = df_enriched["niche"].unique().tolist()
    with pd.ExcelWriter(xl_path, engine="openpyxl") as writer:
        df_enriched.to_excel(writer, sheet_name="All Influencers", index=False)
        for niche in sorted(niches):
            df_enriched[df_enriched["niche"] == niche].to_excel(
                writer, sheet_name=niche[:31], index=False)
    print(f"Excel updated → {xl_path}")

    # Recompute brand match embeddings (they use captions now)
    print("\nRecomputing influencer embeddings with real caption content...")
    from models.brand_match import train as train_brand
    train_brand(df_enriched)
    print("\nDone. Run train_models.py to retrain all models with enriched data.")
    print("The brand match model is already updated.")


if __name__ == "__main__":
    main()
