"""
Ratefluencer — AI Agent Layer (Gemini-powered)
================================================

5 agents that use Gemini to go beyond ML scores and add
genuine intelligence to the influencer discovery pipeline.

Each agent is independent — call any one from anywhere.

Agents:
  1. brief_optimizer     — refines vague campaign briefs
  2. outreach_generator  — personalised pitch emails
  3. content_fit_analyzer— how well influencer voice matches brand
  4. brand_safety_checker— flags risks before you sign
  5. competitor_intel    — what influencer type competitors use
"""
from __future__ import annotations
import os, json, time, hashlib, requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent"

# ── In-memory cache (TTL 1hr) ─────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 3600

def _ck(*args) -> str:
    return hashlib.md5(json.dumps(args, default=str).encode()).hexdigest()

def _get(key):
    if key in _cache:
        v, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return v
    return None

def _set(key, val):
    _cache[key] = (val, time.time())


# ── Core Gemini caller ────────────────────────────────────────────────────
def _gemini(prompt: str, max_tokens: int = 512) -> dict | None:
    """Call Gemini, return parsed JSON dict. Returns None on failure."""
    if not GEMINI_KEY:
        return None
    try:
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": max_tokens,
                    "response_mime_type": "application/json",
                },
            },
            timeout=12,
        )
        if r.status_code == 200:
            raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else (parsed[0] if parsed else None)
    except Exception as e:
        print(f"[Agents] Gemini error: {e}")
    return None


# =============================================================================
# AGENT 1 — Campaign Brief Optimizer
# =============================================================================
def brief_optimizer(brief: dict) -> dict:
    """
    Takes a rough campaign brief and returns an enriched version with:
    - refined target audience description
    - suggested keywords for influencer search
    - recommended niches (ranked)
    - ideal influencer persona
    - campaign angle suggestion

    Example:
        Input:  {"category": "energy drink", "campaign_goal": "Awareness"}
        Output: {
          "refined_brief": {...},
          "target_niches": ["Fitness", "Gaming", "Sports & Athletics"],
          "ideal_persona": "High-energy content creator aged 18-28...",
          "campaign_angle": "Show peak performance moments...",
          "keywords": ["endurance", "performance", "hustle", "training"]
        }
    """
    ck = _ck("brief_optimizer", brief)
    cached = _get(ck)
    if cached:
        return cached

    prompt = f"""You are a campaign strategy expert.

A brand submitted this rough campaign brief:
{json.dumps(brief, indent=2)}

Optimize and expand it for better influencer targeting.

Return ONLY valid JSON:
{{
  "refined_brief": {{
    "product_description": "enriched description (2 sentences)",
    "target_audience": "specific psychographic + demographic description",
    "campaign_angle": "the single strongest creative angle for this campaign"
  }},
  "target_niches": ["top niche", "2nd niche", "3rd niche"],
  "ideal_persona": "description of the ideal influencer for this campaign (3 sentences)",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "why": "one sentence explaining the targeting strategy"
}}"""

    result = _gemini(prompt, max_tokens=600)
    if result:
        _set(ck, result)
        print(f"[Agent:BriefOptimizer] Optimized for {brief.get('category','')}")
        return result

    # Fallback
    return {
        "refined_brief": brief,
        "target_niches": [brief.get("niche", "Lifestyle Vlogging")],
        "ideal_persona": "Creator aligned with the brand values",
        "keywords": brief.get("keywords", []) if isinstance(brief.get("keywords"), list) else [],
        "why": "Based on provided brief parameters",
    }


# =============================================================================
# AGENT 2 — Outreach Email Generator
# =============================================================================
def outreach_generator(influencer: dict, brief: dict) -> dict:
    """
    Generates a personalised outreach email from a brand to an influencer.
    References their actual content, niche, and audience — not a template.

    Returns:
        {
          "subject": "email subject line",
          "body":    "full email body (150-200 words)",
          "tone":    "professional/casual/creator-friendly",
          "hook":    "opening sentence that references their content"
        }
    """
    ck = _ck("outreach", influencer.get("id",""), brief.get("category",""))
    cached = _get(ck)
    if cached:
        return cached

    captions = influencer.get("sample_captions", [])
    cap_text = " | ".join(captions[:2]) if captions else "recent content"

    prompt = f"""You are a brand partnership manager writing a collaboration outreach.

Influencer profile:
- Name: {influencer.get('full_name', '')}
- Niche: {influencer.get('niche', '')}
- Followers: {influencer.get('followers_count', 0):,}
- Engagement: {influencer.get('engagement_rate', 0)}%
- Recent content: {cap_text}
- Audience: primarily {influencer.get('audience', {}).get('country', {}) if influencer.get('audience') else influencer.get('audience_country_top1', 'India')}

Brand campaign:
- Product: {brief.get('category', '')}
- Description: {brief.get('product_description', '')}
- Goal: {brief.get('campaign_goal', 'Awareness')}

Write a personalised outreach email. Reference their actual content. Do NOT use generic templates.

Return ONLY valid JSON:
{{
  "subject": "email subject line (under 60 chars)",
  "body": "full email (150-200 words, warm professional tone)",
  "hook": "first sentence that mentions something specific about their content",
  "tone": "professional/casual/creator-friendly",
  "cta": "specific call to action"
}}"""

    result = _gemini(prompt, max_tokens=700)
    if result:
        _set(ck, result)
        print(f"[Agent:Outreach] Generated email for {influencer.get('username','')}")
        return result

    return {
        "subject": f"Collaboration with {brief.get('category', 'our brand')}",
        "body":    f"Hi {influencer.get('full_name', '')}, we'd love to collaborate with you on our {brief.get('category','')} campaign.",
        "hook":    "We love your content",
        "tone":    "professional",
        "cta":     "Reply to this email to learn more",
    }


# =============================================================================
# AGENT 3 — Content Fit Analyzer
# =============================================================================
def content_fit_analyzer(influencer: dict, brief: dict) -> dict:
    """
    Reads the influencer's actual captions/bio and scores how well
    their VOICE and STYLE matches the brand.

    Goes beyond niche matching — checks tone, vocabulary, values alignment.

    Returns:
        {
          "fit_score":       0-100,
          "voice_match":     "formal/casual/inspirational/educational/humorous",
          "brand_alignment": ["alignment point 1", "alignment point 2"],
          "mismatches":      ["potential mismatch"],
          "recommendation":  "concise recommendation for the brand"
        }
    """
    ck = _ck("content_fit", influencer.get("id",""), brief.get("category",""))
    cached = _get(ck)
    if cached:
        return cached

    captions = influencer.get("sample_captions", [])
    bio = influencer.get("bio", "")

    prompt = f"""You are a brand-influencer fit specialist.

Analyze whether this influencer's content STYLE and VOICE matches the brand.

Influencer content:
Bio: {bio or "Not available"}
Recent captions:
{json.dumps(captions[:4])}

Brand:
Product: {brief.get('category', '')}
Description: {brief.get('product_description', '')}
Goal: {brief.get('campaign_goal', 'Awareness')}
Target audience: {brief.get('target_audience', '')}

Evaluate content style, vocabulary, values, and tone alignment.

Return ONLY valid JSON:
{{
  "fit_score": 75,
  "voice_match": "casual/professional/inspirational/educational/humorous",
  "brand_alignment": ["specific alignment 1", "specific alignment 2"],
  "mismatches": ["potential mismatch if any"],
  "content_themes": ["theme their content covers"],
  "recommendation": "2-sentence recommendation for the brand manager"
}}"""

    result = _gemini(prompt, max_tokens=600)
    if result:
        _set(ck, result)
        print(f"[Agent:ContentFit] Score={result.get('fit_score')} for {influencer.get('username','')}")
        return result

    return {
        "fit_score": 60,
        "voice_match": "neutral",
        "brand_alignment": ["Same niche audience"],
        "mismatches": [],
        "content_themes": [influencer.get("niche", "")],
        "recommendation": "Manual review recommended",
    }


# =============================================================================
# AGENT 4 — Brand Safety Checker
# =============================================================================
def brand_safety_checker(influencer: dict) -> dict:
    """
    Checks for brand safety risks BEFORE signing a contract:
    - Controversial content signals
    - Competitor brand associations
    - Content consistency (posting quality over time)
    - Red flags in bio or captions

    Returns:
        {
          "safety_score":   0-100 (100 = fully brand safe),
          "risk_level":     "LOW / MEDIUM / HIGH",
          "red_flags":      ["flag1"],
          "green_flags":    ["positive signal 1"],
          "recommendation": "safe to proceed / review first / avoid"
        }
    """
    ck = _ck("safety", influencer.get("id",""))
    cached = _get(ck)
    if cached:
        return cached

    captions = influencer.get("sample_captions", [])
    bio = influencer.get("bio", "")
    auth = influencer.get("authenticity_score", 70)
    fake = influencer.get("is_fake_account", False)

    prompt = f"""You are a brand safety analyst reviewing an influencer before a campaign.

Influencer profile:
Bio: {bio or "Not available"}
Niche: {influencer.get('niche', '')}
Recent content samples:
{json.dumps(captions[:5])}
Authenticity score: {auth}/100
Flagged as suspicious: {fake}
Collab frequency: {influencer.get('collab_frequency', 0)}/month

Check for: controversy signals, competitor brand mentions, content quality consistency,
professional vs personal boundary, audience engagement quality.

Return ONLY valid JSON:
{{
  "safety_score": 85,
  "risk_level": "LOW",
  "red_flags": ["specific red flag if found"],
  "green_flags": ["positive brand safety signal"],
  "competitor_mentions": false,
  "content_consistency": "consistent/inconsistent/mixed",
  "recommendation": "safe to proceed / review first / avoid — with one sentence reason"
}}"""

    result = _gemini(prompt, max_tokens=500)
    if result:
        # Boost/reduce based on ML authenticity score
        base = result.get("safety_score", 70)
        adjusted = int(base * 0.6 + auth * 0.4)
        result["safety_score"] = min(adjusted, 100)
        if auth < 50:
            result["risk_level"] = "HIGH"
            result["red_flags"] = result.get("red_flags", []) + ["Low authenticity score — possible fake followers"]
        _set(ck, result)
        print(f"[Agent:BrandSafety] Risk={result.get('risk_level')} for {influencer.get('username','')}")
        return result

    safety = min(int(auth), 100)
    return {
        "safety_score":        safety,
        "risk_level":          "LOW" if safety >= 70 else "MEDIUM" if safety >= 45 else "HIGH",
        "red_flags":           [] if safety >= 70 else ["Low authenticity score"],
        "green_flags":         ["Verified engagement patterns"] if auth >= 75 else [],
        "competitor_mentions": False,
        "content_consistency": "mixed",
        "recommendation":      "safe to proceed" if safety >= 70 else "review first",
    }


# =============================================================================
# AGENT 5 — Competitor Intelligence
# =============================================================================
def competitor_intel(brand_category: str, brand_niche: str) -> dict:
    """
    Analyzes what type of influencers competitors in this space typically use
    and recommends a differentiated strategy.

    Returns:
        {
          "competitor_strategy":   "what competitors typically do",
          "typical_influencer":    "profile of typical competitor influencer",
          "differentiation":       "how to stand out in influencer selection",
          "recommended_tiers":     ["mid-tier", "nano"],
          "untapped_niches":       ["niche competitors ignore"],
          "insight":               "key strategic insight"
        }
    """
    ck = _ck("competitor_intel", brand_category, brand_niche)
    cached = _get(ck)
    if cached:
        return cached

    prompt = f"""You are a competitive intelligence expert specialising in influencer marketing.

Brand context:
- Product category: {brand_category}
- Target niche: {brand_niche}

Based on your knowledge of influencer marketing patterns in this space:

1. What do COMPETITORS typically do for influencer marketing?
2. What types of influencers do they usually pick?
3. What niches or creators are UNDERUTILISED (competitive gap)?
4. What differentiation strategy would give this brand an edge?

Return ONLY valid JSON:
{{
  "competitor_strategy": "2-sentence description of what competitors typically do",
  "typical_influencer": "profile of influencer competitors usually pick",
  "differentiation": "specific way to stand out in influencer selection",
  "recommended_tiers": ["tier1", "tier2"],
  "untapped_niches": ["niche1", "niche2"],
  "insight": "single most valuable strategic insight for this brand"
}}"""

    result = _gemini(prompt, max_tokens=600)
    if result:
        _set(ck, result)
        print(f"[Agent:CompetitorIntel] Analyzed {brand_category}")
        return result

    return {
        "competitor_strategy": "Most competitors focus on macro-influencers for reach",
        "typical_influencer":  "Generic lifestyle influencers with broad audiences",
        "differentiation":     "Target authentic micro-influencers with high engagement",
        "recommended_tiers":   ["micro", "mid-tier"],
        "untapped_niches":     [brand_niche],
        "insight":             "Authenticity outperforms follower count in this category",
    }


# =============================================================================
# AGENT 6 — Influencer Comparison Agent
# =============================================================================
def compare_influencers(influencers: list[dict], brief: dict) -> dict:
    """
    Compares 2-3 influencers side-by-side for a specific campaign.
    Gemini goes beyond raw numbers to explain nuanced fit differences.

    Returns:
        {
          "winner":          {"id": "...", "username": "...", "reason": "..."},
          "ranking":         [{"rank":1, "id":"...", "username":"...", "score":85, "summary":"..."}],
          "comparison":      {"engagement": "...", "audience": "...", "content": "..."},
          "recommendation":  "2-sentence actionable recommendation for the brand"
        }
    """
    if not influencers:
        return {}
    ck = _ck("compare", [i.get("id","") for i in influencers], brief.get("category",""))
    cached = _get(ck)
    if cached:
        return cached

    profiles = []
    for inf in influencers:
        captions = inf.get("sample_captions", [])
        profiles.append({
            "id":               inf.get("id",""),
            "username":         inf.get("username",""),
            "niche":            inf.get("niche",""),
            "followers":        inf.get("followers_count",0),
            "engagement_rate":  inf.get("engagement_rate",0),
            "authenticity":     inf.get("authenticity_score",0),
            "ratefluencer":     inf.get("ratefluencer_score",0),
            "growth":           inf.get("growth_score",0),
            "bio":              (inf.get("bio","") or "")[:150],
            "recent_content":   captions[:2],
        })

    prompt = f"""You are a senior influencer marketing strategist.

A brand needs to choose between these influencers for their campaign.

Campaign:
- Product: {brief.get('category','')}
- Description: {brief.get('product_description','')}
- Goal: {brief.get('campaign_goal','Awareness')}

Influencer profiles:
{json.dumps(profiles, indent=2)}

Compare them specifically for THIS campaign. Go beyond numbers — consider content style, audience alignment, and brand fit.

Return ONLY valid JSON:
{{
  "winner": {{
    "id": "influencer_id",
    "username": "username",
    "reason": "2 sentences explaining why they win for this specific campaign"
  }},
  "ranking": [
    {{"rank": 1, "id": "...", "username": "...", "score": 90, "summary": "one sentence strength"}},
    {{"rank": 2, "id": "...", "username": "...", "score": 75, "summary": "one sentence strength"}},
    {{"rank": 3, "id": "...", "username": "...", "score": 60, "summary": "one sentence strength"}}
  ],
  "comparison": {{
    "engagement":  "who has better engagement quality and why",
    "audience":    "whose audience fits the campaign target better",
    "content":     "whose content style aligns better with the brand"
  }},
  "recommendation": "actionable 2-sentence recommendation for the brand manager"
}}"""

    result = _gemini(prompt, max_tokens=700)
    if result:
        _set(ck, result)
        winner = result.get("winner", {}).get("username", "")
        print(f"[Agent:Compare] Winner: {winner} among {[i['username'] for i in profiles]}")
        return result

    # Fallback: rank by ratefluencer score
    ranked = sorted(influencers, key=lambda x: x.get("ratefluencer_score", 0), reverse=True)
    return {
        "winner": {"id": ranked[0].get("id",""), "username": ranked[0].get("username",""),
                   "reason": f"Highest Ratefluencer score ({ranked[0].get('ratefluencer_score',0):.0f}/100)"},
        "ranking": [{"rank": i+1, "id": inf.get("id",""), "username": inf.get("username",""),
                     "score": inf.get("ratefluencer_score",0),
                     "summary": f"Score: {inf.get('ratefluencer_score',0):.0f}, ER: {inf.get('engagement_rate',0):.1f}%"}
                    for i, inf in enumerate(ranked)],
        "comparison": {"engagement": "See individual scores", "audience": "See profiles", "content": "Review manually"},
        "recommendation": f"@{ranked[0].get('username','')} has the strongest overall score for this campaign.",
    }


# =============================================================================
# AGENT 8 — Budget & ROI Estimator
# =============================================================================

# Estimated cost per post by tier (INR ranges)
TIER_COST_INR = {
    "nano":    (3_000,   15_000),
    "micro":   (15_000,  80_000),
    "mid":     (80_000,  400_000),
    "macro":   (400_000, 2_000_000),
    "mega":    (2_000_000, 10_000_000),
}

def budget_roi_estimator(budget_inr: int, brief: dict, influencers: list[dict]) -> dict:
    """
    Given a budget + list of candidate influencers, recommends the optimal
    mix and estimates campaign ROI.

    ML part: calculates reach, impressions, estimated conversions per influencer
    Gemini part: reasons about strategic allocation and explains the mix

    Returns:
        {
          "recommended_mix":    [{"influencer": {...}, "allocation": 50000, "posts": 2}],
          "total_reach":        number,
          "estimated_impressions": number,
          "estimated_conversions": number,
          "roi_multiplier":     float (e.g. 3.2 = 3.2x return),
          "budget_breakdown":   {...},
          "gemini_strategy":    "strategic reasoning"
        }
    """
    ck = _ck("budget_roi", budget_inr, brief.get("category",""), [i.get("id","") for i in influencers[:5]])
    cached = _get(ck)
    if cached:
        return cached

    # ── ML-based reach estimation ────────────────────────────────────────
    candidates = []
    for inf in influencers[:10]:
        tier  = (inf.get("tier","micro") or "micro").lower()
        lo, hi = TIER_COST_INR.get(tier, (20000, 100000))
        cost_per_post = int((lo + hi) / 2)
        followers     = inf.get("followers_count", 10000)
        er            = inf.get("engagement_rate", 3.0) / 100
        auth          = inf.get("authenticity_score", 70) / 100
        rf_score      = inf.get("ratefluencer_score", 50) / 100

        # Impressions = followers × avg view rate (higher ER = higher view rate)
        impressions_per_post = int(followers * (0.15 + er * 2))
        # Engagement = impressions × ER (weighted by authenticity)
        engagements = int(impressions_per_post * er * auth)
        # Estimated conversions depend on campaign goal
        goal = brief.get("campaign_goal","Awareness").lower()
        conv_rate = 0.01 if "conversion" in goal else 0.005
        conversions = int(engagements * conv_rate * rf_score)
        # Cost efficiency = impressions per rupee
        efficiency = impressions_per_post / max(cost_per_post, 1)

        candidates.append({
            "id":               inf.get("id",""),
            "username":         inf.get("username",""),
            "tier":             tier,
            "followers":        followers,
            "er":               er,
            "cost_per_post":    cost_per_post,
            "impressions":      impressions_per_post,
            "engagements":      engagements,
            "conversions":      conversions,
            "efficiency":       round(efficiency, 4),
            "rf_score":         round(rf_score, 2),
        })

    # Sort by efficiency × rf_score (best bang per rupee with quality weight)
    candidates.sort(key=lambda x: x["efficiency"] * x["rf_score"], reverse=True)

    # ── Greedy budget allocation ─────────────────────────────────────────
    remaining   = budget_inr
    selected    = []
    total_reach = 0
    total_impr  = 0
    total_conv  = 0

    for c in candidates:
        if remaining <= 0:
            break
        posts = max(1, min(3, remaining // c["cost_per_post"]))
        if posts == 0:
            continue
        alloc = posts * c["cost_per_post"]
        if alloc > remaining:
            posts = 1
            alloc = c["cost_per_post"]
        if alloc > remaining:
            continue
        remaining   -= alloc
        total_reach += c["followers"]
        total_impr  += c["impressions"] * posts
        total_conv  += c["conversions"] * posts
        selected.append({
            "influencer": {k: c[k] for k in ["id","username","tier","followers","er"]},
            "posts":     posts,
            "allocation": alloc,
            "impressions": c["impressions"] * posts,
        })

    spent       = budget_inr - remaining
    avg_cpm     = round(spent / max(total_impr, 1) * 1000, 2)
    roi_mult    = round(total_conv * 500 / max(spent, 1), 2)  # assume ₹500 avg order value

    base_result = {
        "recommended_mix":        selected,
        "total_reach":            total_reach,
        "estimated_impressions":  total_impr,
        "estimated_engagements":  int(total_impr * 0.04),
        "estimated_conversions":  total_conv,
        "budget_spent":           spent,
        "budget_remaining":       remaining,
        "avg_cpm_inr":            avg_cpm,
        "roi_multiplier":         roi_mult,
        "budget_breakdown":       {
            "total":    budget_inr,
            "spent":    spent,
            "reserved": remaining,
            "per_post": {c["influencer"]["username"]: c["allocation"] for c in selected},
        },
    }

    # ── Gemini strategic reasoning ───────────────────────────────────────
    mix_summary = [{"username": s["influencer"]["username"], "tier": s["influencer"]["tier"],
                    "posts": s["posts"], "allocation_inr": s["allocation"]} for s in selected[:5]]
    prompt = f"""You are a media buying strategist for influencer campaigns in India.

Campaign: {brief.get('category','')} | Goal: {brief.get('campaign_goal','Awareness')}
Total budget: ₹{budget_inr:,}
Recommended influencer mix: {json.dumps(mix_summary)}
Estimated impressions: {total_impr:,} | Conversions: {total_conv:,} | ROI: {roi_mult}x

In 2 sentences, explain WHY this mix is optimal for this campaign and one tip to improve results.

Return ONLY valid JSON:
{{
  "strategy": "2-sentence explanation of why this mix works",
  "tip": "one specific actionable tip to boost ROI further"
}}"""

    g = _gemini(prompt, max_tokens=200)
    if g:
        base_result["gemini_strategy"] = g.get("strategy", "")
        base_result["gemini_tip"]      = g.get("tip", "")

    _set(ck, base_result)
    print(f"[Agent:BudgetROI] Budget ₹{budget_inr:,} → {len(selected)} influencers, {total_impr:,} impressions")
    return base_result
