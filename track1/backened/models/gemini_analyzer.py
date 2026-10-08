"""
Gemini Analyzer — 4 accuracy-boosting analyses for Track 1 models
===================================================================

Gemini adds qualitative signals that pure ML cannot extract from numbers:

  1. expand_brand_brief()     → richer semantic text for brand match embedding
  2. analyze_comment_quality()→ spam / bot / authentic ratios from real comment text
  3. analyze_bio_authority()  → niche credibility from profile bio + posting style
  4. predict_campaign_roi()   → estimated ROI + reasoning for a brand × influencer pair

All functions:
  - Fall back to sensible defaults if Gemini is unavailable / rate-limited
  - Cache results in memory (TTL 1 hour) to avoid redundant API calls
  - Log what they used (Gemini live vs cached vs fallback)
"""
from __future__ import annotations
import os, json, time, hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent"
CACHE_TTL  = 3600   # 1 hour

_cache: dict[str, tuple[dict, float]] = {}


def _cache_key(*args) -> str:
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cache(key: str):
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None


def _set_cache(key: str, val: dict) -> None:
    _cache[key] = (val, time.time())


def _call_gemini(prompt: str) -> str | None:
    if not GEMINI_KEY:
        return None
    try:
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 512,
                    "response_mime_type": "application/json",
                },
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"[GeminiAnalyzer] HTTP {r.status_code}")
    except Exception as e:
        print(f"[GeminiAnalyzer] Error: {e}")
    return None


def _parse_json(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list) and parsed:
            return parsed[0]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# 1. Brand Brief Expansion
# ---------------------------------------------------------------------------
def expand_brand_brief(brief: dict) -> str:
    """
    Expand a brand brief into a richer semantic description for better embedding.

    Without Gemini: "fitness app" → only fitness keywords match
    With Gemini:    "fitness app" → health, wellness, workout, nutrition, body goals,
                    gym motivation, healthy lifestyle, weight loss, muscle gain...

    Returns: expanded text string (100-150 words)
    Falls back to: concatenated brief fields
    """
    key = _cache_key("expand_brief", brief)
    cached = _get_cache(key)
    if cached:
        return cached.get("expanded_text", "")

    prompt = f"""You are a marketing expert. Expand this brand brief into a rich semantic description
for finding the best influencer match.

Brand Brief:
{json.dumps(brief, indent=2)}

Return ONLY valid JSON:
{{
  "expanded_text": "100-150 word semantic description covering: target audience psychology, content themes that would resonate, lifestyle signals, related topics, pain points addressed, aspirational language the brand uses",
  "key_themes": ["theme1", "theme2", "theme3", "theme4", "theme5"],
  "ideal_creator_traits": ["trait1", "trait2", "trait3"]
}}"""

    raw    = _call_gemini(prompt)
    result = _parse_json(raw)

    if result and result.get("expanded_text"):
        _set_cache(key, result)
        print(f"[GeminiAnalyzer] Brief expanded ({len(result['expanded_text'])} chars)")
        return result["expanded_text"]

    # Fallback: concatenate brief fields
    fallback = " ".join(str(v) for v in brief.values() if isinstance(v, str))
    print("[GeminiAnalyzer] Brief expansion fallback (Gemini unavailable)")
    return fallback


# ---------------------------------------------------------------------------
# 2. Comment Quality Analysis
# ---------------------------------------------------------------------------
def analyze_comment_quality(comments: list[str], niche: str = "") -> dict:
    """
    Analyze a sample of comments to detect spam, bots, and authentic engagement.

    Replaces the synthetic `avg_comment_length` proxy with real NLP analysis.

    Returns:
        {
          "spam_ratio":          0.0-1.0  (generic/emoji-only/template comments)
          "bot_confidence":      0.0-1.0  (how likely comments are automated)
          "sentiment_diversity": 0.0-1.0  (varied opinions vs all positive)
          "authentic_ratio":     0.0-1.0  (genuine personal responses)
          "quality_score":       0-100    (overall comment quality)
        }
    """
    if not comments:
        return _default_comment_quality()

    key = _cache_key("comment_quality", comments[:10], niche)
    cached = _get_cache(key)
    if cached:
        return cached

    sample = comments[:15]
    prompt = f"""Analyze these Instagram comments for authenticity. Niche: {niche or 'general'}

Comments:
{json.dumps(sample)}

Evaluate:
- spam_ratio: % that are generic/emoji-only/template ("Nice!", "🔥🔥", "Follow me!")
- bot_confidence: likelihood comments are from automated accounts (0=human, 1=bot)
- sentiment_diversity: are opinions varied (0=all same, 1=diverse perspectives)
- authentic_ratio: % showing genuine personal engagement

Return ONLY valid JSON:
{{
  "spam_ratio": 0.0,
  "bot_confidence": 0.0,
  "sentiment_diversity": 0.5,
  "authentic_ratio": 0.8,
  "quality_score": 75,
  "reasoning": "one sentence"
}}"""

    raw    = _call_gemini(prompt)
    result = _parse_json(raw)

    if result and "quality_score" in result:
        # Clamp all values
        result = {
            "spam_ratio":          float(min(max(result.get("spam_ratio", 0.1), 0), 1)),
            "bot_confidence":      float(min(max(result.get("bot_confidence", 0.1), 0), 1)),
            "sentiment_diversity": float(min(max(result.get("sentiment_diversity", 0.5), 0), 1)),
            "authentic_ratio":     float(min(max(result.get("authentic_ratio", 0.7), 0), 1)),
            "quality_score":       float(min(max(result.get("quality_score", 60), 0), 100)),
        }
        _set_cache(key, result)
        print(f"[GeminiAnalyzer] Comment quality: score={result['quality_score']}")
        return result

    return _default_comment_quality()


def _default_comment_quality() -> dict:
    return {"spam_ratio": 0.15, "bot_confidence": 0.10,
            "sentiment_diversity": 0.60, "authentic_ratio": 0.70, "quality_score": 65}


# ---------------------------------------------------------------------------
# 3. Bio / Profile Authority Analysis
# ---------------------------------------------------------------------------
def analyze_bio_authority(bio: str, niche: str, sample_captions: list[str] = None) -> dict:
    """
    Score how credible and authoritative this influencer is within their niche.

    Gemini reads the bio + caption samples and assesses:
    - Does the bio show real expertise (certifications, years, specific accomplishments)?
    - Are captions educational/insightful or generic/promotional?
    - Does the creator have a clear, authentic point of view?

    Returns:
        {
          "authority_score":     0-100
          "expertise_signals":   ["signal1", "signal2"]
          "content_quality":     0-100
          "brand_safety":        0-100  (no controversial content)
          "niche_fit":           0-100
        }
    """
    key = _cache_key("bio_authority", bio, niche, (sample_captions or [])[:3])
    cached = _get_cache(key)
    if cached:
        return cached

    captions_text = ""
    if sample_captions:
        captions_text = f"\n\nSample captions:\n" + "\n".join(f"- {c}" for c in sample_captions[:3])

    prompt = f"""You are a talent agency evaluating an influencer's niche authority.

Niche: {niche}
Bio: {bio or "(no bio provided)"}
{captions_text}

Score this influencer:
- authority_score: 0-100 (expertise, credentials, specific knowledge vs generic content)
- content_quality: 0-100 (depth, originality, value to audience)
- brand_safety: 0-100 (100=safe for all brands, lower=controversial/risky)
- niche_fit: 0-100 (how well they actually fit this niche vs just posting about it)

Return ONLY valid JSON:
{{
  "authority_score": 70,
  "expertise_signals": ["specific signal 1", "signal 2"],
  "content_quality": 65,
  "brand_safety": 90,
  "niche_fit": 80
}}"""

    raw    = _call_gemini(prompt)
    result = _parse_json(raw)

    if result and "authority_score" in result:
        result = {
            "authority_score":  float(min(max(result.get("authority_score", 60), 0), 100)),
            "expertise_signals":result.get("expertise_signals", []),
            "content_quality":  float(min(max(result.get("content_quality", 60), 0), 100)),
            "brand_safety":     float(min(max(result.get("brand_safety", 80), 0), 100)),
            "niche_fit":        float(min(max(result.get("niche_fit", 70), 0), 100)),
        }
        _set_cache(key, result)
        print(f"[GeminiAnalyzer] Authority: {result['authority_score']}/100  safety: {result['brand_safety']}/100")
        return result

    return {"authority_score": 60, "expertise_signals": [],
            "content_quality": 60, "brand_safety": 80, "niche_fit": 65}


# ---------------------------------------------------------------------------
# 4. Campaign ROI Prediction
# ---------------------------------------------------------------------------
def predict_campaign_roi(influencer: dict, brief: dict) -> dict:
    """
    Predict the likely ROI and outcomes of a brand × influencer campaign.

    Gemini reasons about the match quality, audience fit, and expected outcomes
    beyond what cosine similarity can capture.

    Returns:
        {
          "roi_score":          0-100  (expected campaign ROI)
          "conversion_fit":     0-100  (likelihood to drive conversions)
          "audience_alignment": 0-100  (how well audience matches target)
          "risk_factors":       ["risk1", "risk2"]
          "why_good_match":     "one-sentence explanation"
          "expected_outcome":   "Awareness" | "Engagement" | "Conversions"
        }
    """
    key = _cache_key("campaign_roi",
                     influencer.get("influencer_id", ""),
                     brief.get("category", ""),
                     brief.get("campaign_goal", ""))
    cached = _get_cache(key)
    if cached:
        return cached

    inf_summary = {
        "niche":              influencer.get("niche", ""),
        "tier":               influencer.get("tier", ""),
        "followers":          influencer.get("followers_count", 0),
        "engagement_rate":    influencer.get("engagement_rate", 0),
        "authenticity_score": influencer.get("authenticity_score", 70),
        "audience_country":   influencer.get("audience_country_top1", "India"),
        "content_tone":       influencer.get("content_tone", ""),
        "past_brands":        influencer.get("past_brand_categories", []),
    }

    prompt = f"""You are a brand partnership strategist. Predict campaign ROI.

Influencer Profile:
{json.dumps(inf_summary, indent=2)}

Brand Brief:
{json.dumps({k: brief.get(k) for k in ['category','product_description','campaign_goal','target_audience','target_country']}, indent=2)}

Assess:
- roi_score: 0-100 expected return (100=exceptional ROI)
- conversion_fit: how likely to drive the campaign goal
- audience_alignment: does influencer's audience match brand's target customer
- risk_factors: list any red flags (over-commercialized, wrong audience, etc.)
- expected_outcome: the most realistic outcome of this collab

Return ONLY valid JSON:
{{
  "roi_score": 72,
  "conversion_fit": 68,
  "audience_alignment": 80,
  "risk_factors": [],
  "why_good_match": "one sentence",
  "expected_outcome": "Engagement"
}}"""

    raw    = _call_gemini(prompt)
    result = _parse_json(raw)

    if result and "roi_score" in result:
        result = {
            "roi_score":          float(min(max(result.get("roi_score", 60), 0), 100)),
            "conversion_fit":     float(min(max(result.get("conversion_fit", 60), 0), 100)),
            "audience_alignment": float(min(max(result.get("audience_alignment", 65), 0), 100)),
            "risk_factors":       result.get("risk_factors", []),
            "why_good_match":     result.get("why_good_match", ""),
            "expected_outcome":   result.get("expected_outcome", "Engagement"),
        }
        _set_cache(key, result)
        print(f"[GeminiAnalyzer] ROI: {result['roi_score']}/100  alignment: {result['audience_alignment']}/100")
        return result

    return {"roi_score": 60, "conversion_fit": 55, "audience_alignment": 65,
            "risk_factors": [], "why_good_match": "", "expected_outcome": "Engagement"}
