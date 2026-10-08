"""
Ratefluencer — Caption Trainer
================================

Two jobs:

A) FEW-SHOT SELECTOR
   Loads real Instagram captions from instagram_corpus.pkl,
   finds the ones most semantically similar to the current
   trend/niche, and returns them as few-shot examples for
   the Gemini prompt → Gemini writes in the style of real
   viral posts instead of generic AI content.

B) CAPTION RANKER
   Takes 3 generated script variants, scores each with the
   XGBoost virality model, and returns the highest-scoring
   one along with scores for all variants.
"""
from __future__ import annotations
import pickle, os, re
import numpy as np

CORPUS_PATH = "instagram_corpus.pkl"

# ---------------------------------------------------------------------------
# Shared sentence-transformer (loaded once)
# ---------------------------------------------------------------------------
_st_model     = None
_corpus_texts = None
_corpus_embs  = None


def _load_st():
    global _st_model, _corpus_texts, _corpus_embs
    if _st_model is not None:
        return _st_model

    from sentence_transformers import SentenceTransformer
    _st_model = SentenceTransformer("all-MiniLM-L6-v2")

    if os.path.exists(CORPUS_PATH):
        with open(CORPUS_PATH, "rb") as f:
            _corpus_texts = pickle.load(f)
        # Only keep captions of useful length (10-200 chars)
        _corpus_texts = [c for c in _corpus_texts
                         if isinstance(c, str) and 10 < len(c) < 200]
        _corpus_embs = _st_model.encode(
            _corpus_texts, show_progress_bar=False, normalize_embeddings=True
        )
        print(f"[CaptionTrainer] Corpus loaded: {len(_corpus_texts)} IG captions")
    else:
        _corpus_texts = []
        _corpus_embs  = None
        print("[CaptionTrainer] instagram_corpus.pkl not found — run train_from_instagram.py first")

    return _st_model


# ---------------------------------------------------------------------------
# A: Few-shot example selector
# ---------------------------------------------------------------------------
def get_relevant_examples(
    trend_phrase: str,
    niche: str = "",
    n: int = 5,
    min_words: int = 6,
    max_words: int = 60,
) -> list[str]:
    """
    Find n real Instagram captions most semantically similar to the
    current trend phrase. These become few-shot examples in the Gemini prompt.

    Returns list of caption strings, ordered by relevance.
    Falls back to keyword search if sentence-transformer unavailable.
    """
    _load_st()

    if not _corpus_texts:
        return []

    # Filter by word count first (too short = useless, too long = noise)
    candidates = [
        (i, t) for i, t in enumerate(_corpus_texts)
        if min_words <= len(t.split()) <= max_words
    ]
    if not candidates:
        return []

    idxs, texts = zip(*candidates)
    cand_embs   = _corpus_embs[list(idxs)]

    # Query = trend_phrase + niche for richer matching
    query     = f"{trend_phrase} {niche}".strip()
    query_emb = _st_model.encode([query], normalize_embeddings=True)
    sims      = (query_emb @ cand_embs.T)[0]

    top_n_idx = np.argsort(sims)[-n:][::-1]
    results   = [texts[i] for i in top_n_idx if sims[i] > 0.15]

    # Clean: strip excess hashtags so they don't pollute the prompt
    clean = []
    for cap in results:
        # Remove hashtag blocks (keep caption body only)
        body = re.sub(r"(#\w+\s*){3,}", "", cap).strip()
        if body and len(body) > 20:
            clean.append(body)

    return clean[:n]


def format_few_shot_block(examples: list[str], label: str = "Instagram captions") -> str:
    """Format examples as a readable block for the Gemini prompt."""
    if not examples:
        return ""
    lines = "\n".join(f'  {i+1}. "{ex}"' for i, ex in enumerate(examples))
    return f"\nHigh-performing real {label} from this niche:\n{lines}\n"


# ---------------------------------------------------------------------------
# B: Caption / script ranker
# ---------------------------------------------------------------------------
def rank_variants(
    variants: list[dict],
    trend: dict | None = None,
) -> dict:
    """
    Score each script variant with the XGBoost virality model and return
    the highest-scoring one.

    Args:
        variants: list of script dicts (same shape as GeneratedContent.to_dict())
        trend:    trend dict (for urgency/score context), optional

    Returns:
        {
          "winner":  <best variant dict>,
          "scores":  [{"variant": i, "score": float, "verdict": str}, ...],
          "winner_idx": int,
        }
    """
    from virality_model import predict, load_model, _verdict

    if not variants:
        return {"winner": {}, "scores": [], "winner_idx": 0}

    model  = load_model()
    scores = []

    for i, v in enumerate(variants):
        # Merge trend context if provided
        if trend:
            v.setdefault("trend_score",  trend.get("score", 50))
            v.setdefault("urgency",      trend.get("urgency", "rising"))
            v.setdefault("acceleration", trend.get("acceleration", 0))
            v.setdefault("niche",        trend.get("niche", ""))

        result = predict(v, model=model, use_semantic=True)
        scores.append({
            "variant":    i + 1,
            "score":      result.virality_score,
            "verdict":    result.verdict,
            "confidence": result.confidence,
        })

    best_idx = max(range(len(scores)), key=lambda i: scores[i]["score"])

    print(f"[CaptionTrainer] Ranked {len(variants)} variants:")
    for s in scores:
        marker = " ← WINNER" if s["variant"] - 1 == best_idx else ""
        print(f"  Variant {s['variant']}: {s['score']:.1f}/100  {s['verdict']}{marker}")

    return {
        "winner":      variants[best_idx],
        "scores":      scores,
        "winner_idx":  best_idx,
    }
