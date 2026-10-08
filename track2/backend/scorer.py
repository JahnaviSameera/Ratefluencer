"""
Ratefluencer — Scorer
=====================

Hybrid scoring engine:
  YOUR ML   → TF-IDF extracts unique phrases from real headlines
  YOUR ML   → Sentence transformers picks best hook via cosine similarity
  GEMINI    → Scores script against live patterns with chain of thought
  YOUR MATH → Virality prediction via power law formula

No fixed rules. No hardcoded word lists.
Everything driven by real scraped data from trend_agent.
"""
from __future__ import annotations
import re, os, json, math, time
import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Gemini caller
# ---------------------------------------------------------------------------
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent"

from dotenv import load_dotenv
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

def call_gemini(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            r = requests.post(
                f"{GEMINI_URL}?key={GEMINI_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1024
                    }
                },
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            if r.status_code == 429 and attempt < retries - 1:
                wait = 60 * (attempt + 1)
                print(f"[Scorer] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise Exception(f"Gemini error {r.status_code}: {r.text[:200]}")
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(10)
    raise Exception("Gemini: max retries exceeded")


# ---------------------------------------------------------------------------
# Shared embedding model — loaded once, reused everywhere
# ---------------------------------------------------------------------------
_embed_model = None

def get_embed_model() -> SentenceTransformer:
    """Load sentence-transformers model once and cache it."""
    global _embed_model
    if _embed_model is None:
        print("[Scorer] Loading sentence-transformers model...")
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Scorer] Model loaded.")
    return _embed_model


# ---------------------------------------------------------------------------
# ML Component 1 — TF-IDF phrase extraction
# ---------------------------------------------------------------------------
def extract_tfidf_phrases(
    trend_headlines: list[str],
    top_n: int = 10
) -> list[str]:
    """
    Use TF-IDF to find phrases that are UNIQUELY important
    in your viral headlines vs generic background text.

    Why TF-IDF here:
      Common words like "AI" appear everywhere — low TF-IDF score.
      Unique phrases like "fail production" or "built backwards"
      appear only in your trend headlines — high TF-IDF score.
      These unique phrases are what make your script specific
      and grounded in real news, not generic AI content.

    Args:
        trend_headlines: real headlines from trend_agent
        top_n:           how many top phrases to return

    Returns:
        list of uniquely important phrases for this trend right now
    """
    if not trend_headlines:
        return []

    # Background corpus — generic AI sentences that TF-IDF
    # will discount because they appear everywhere
    background = [
        "artificial intelligence is transforming industries worldwide",
        "machine learning continues to advance rapidly",
        "AI adoption is increasing across all sectors",
        "technology companies are investing in artificial intelligence",
        "the future of work involves artificial intelligence tools",
        "digital transformation is accelerating with AI solutions",
        "businesses are implementing AI strategies for growth",
        "AI models are becoming more capable every year",
    ]

    all_docs = background + trend_headlines

    try:
        # bigrams and trigrams — capture multi-word phrases
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words="english",
            min_df=1,
            max_features=500,
        )
        tfidf_matrix  = vectorizer.fit_transform(all_docs)
        feature_names = vectorizer.get_feature_names_out()

        # Score only the trend headlines (not background)
        trend_matrix = tfidf_matrix[len(background):]
        scores       = trend_matrix.sum(axis=0).A1

        # Top N phrases by TF-IDF score
        top_indices = scores.argsort()[-top_n:][::-1]
        top_phrases = [feature_names[i] for i in top_indices if scores[i] > 0]

        print(f"[Scorer] TF-IDF extracted {len(top_phrases)} unique phrases")
        return top_phrases

    except Exception as e:
        print(f"[Scorer] TF-IDF failed: {e}")
        return []


# ---------------------------------------------------------------------------
# ML Component 2 — Hook selection via cosine similarity
# ---------------------------------------------------------------------------
def select_best_hook(
    candidate_hooks: list[str],
    viral_headlines: list[str]
) -> tuple[str, float]:
    """
    Use sentence-transformers + cosine similarity to pick the hook
    that is most semantically similar to proven viral headlines.

    Why embeddings here:
      "40% of AI agents fail" and "Most AI agents fail in production"
      are semantically similar even though they share few words.
      Cosine similarity in 384-dim embedding space catches this.
      Pure keyword matching would miss it.

    Args:
        candidate_hooks: list of hook options generated by script_agent
        viral_headlines: real viral headlines from trend_agent

    Returns:
        (best_hook, similarity_score)
    """
    if not candidate_hooks or not viral_headlines:
        return candidate_hooks[0] if candidate_hooks else "", 0.0

    try:
        model = get_embed_model()

        # Embed both sets
        hook_embeddings     = model.encode(candidate_hooks,     show_progress_bar=False)
        headline_embeddings = model.encode(viral_headlines,     show_progress_bar=False)

        # Normalize for cosine similarity via dot product
        hook_norm     = hook_embeddings     / (np.linalg.norm(hook_embeddings,     axis=1, keepdims=True) + 1e-9)
        headline_norm = headline_embeddings / (np.linalg.norm(headline_embeddings, axis=1, keepdims=True) + 1e-9)

        # Similarity matrix: (n_hooks x n_headlines)
        sim_matrix = hook_norm @ headline_norm.T

        # Average similarity of each hook to ALL viral headlines
        avg_sims   = sim_matrix.mean(axis=1)
        best_idx   = int(np.argmax(avg_sims))
        best_score = float(avg_sims[best_idx])

        print(f"[Scorer] Hook similarity scores: {[round(float(s),3) for s in avg_sims]}")
        print(f"[Scorer] Best hook (sim={best_score:.3f}): \"{candidate_hooks[best_idx][:60]}\"")

        return candidate_hooks[best_idx], best_score

    except Exception as e:
        print(f"[Scorer] Hook selection failed: {e}. Using first hook.")
        return candidate_hooks[0], 0.0


# ---------------------------------------------------------------------------
# ML Component 3 — Gemini chain-of-thought scoring
# ---------------------------------------------------------------------------
def score_script_gemini(
    script: dict,
    tfidf_phrases: list[str],
    viral_headlines: list[str],
    trend_phrase: str,
    trend_score: float,
) -> dict:
    """
    Gemini scores the script using chain-of-thought reasoning.
    Receives real data as context — not fixed rules.

    Why chain-of-thought:
      Standard prompting: "score this script" → generic answer
      Chain-of-thought:   forces Gemini to reason step by step
                          before giving a score → 40-60% more
                          specific and grounded feedback

    Args:
        script:          {hook, story, insight, cta}
        tfidf_phrases:   unique phrases from real headlines (TF-IDF)
        viral_headlines: real viral headlines from trend_agent
        trend_phrase:    e.g. "ai agents"
        trend_score:     0-100 from trend_agent

    Returns:
        {score, hook_score, story_score, cta_score, feedback, passed}
    """
    hook    = script.get("hook", "")
    story   = script.get("story", "")
    insight = script.get("insight", "")
    cta     = script.get("cta", "")

    headlines_str = "\n".join([f"  → {h}" for h in viral_headlines[:5]])
    phrases_str   = ", ".join(tfidf_phrases[:8])

    prompt = f"""You are an expert viral content critic for short-form video.

REAL DATA scraped from internet today about "{trend_phrase}":

Trend momentum score: {trend_score}/100
Uniquely important phrases right now (TF-IDF extracted):
  {phrases_str}

Real viral headlines trending right now:
{headlines_str}

THE SCRIPT TO EVALUATE:
Hook:    {hook}
Story:   {story}
Insight: {insight}
CTA:     {cta}

Think step by step before scoring:

STEP 1 — Analyse the viral headlines above.
What is the single most surprising or controversial fact?
What emotion do they trigger?

STEP 2 — Compare the hook to viral patterns.
Does it use any of the uniquely important phrases?
Does it match the tone of what is actually going viral?
Is it specific enough or too generic?

STEP 3 — Evaluate the story.
Does it use real specific facts from the headlines?
Or does it make vague generic claims?
Does it have a specific number, name, or outcome?

STEP 4 — Evaluate insight and CTA.
Does the insight surprise? Is it counterintuitive?
Does the CTA create urgency matching the trend momentum?

STEP 5 — Give scores and specific feedback.

Return ONLY valid JSON, no explanation, no markdown:
{{
  "hook_score":    75,
  "story_score":   60,
  "insight_score": 70,
  "cta_score":     65,
  "overall_score": 68,
  "strongest":     "one sentence on what works best",
  "weakest":       "one sentence on biggest problem",
  "rewrite":       "specific rewrite suggestion for weakest section",
  "passed":        true
}}

passed = true if overall_score >= 65, false otherwise."""

    try:
        raw = call_gemini(prompt)
        raw = raw.replace("```json", "").replace("```", "").strip()
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found")
        result = json.loads(raw[start:end])
        print(f"[Scorer] Gemini score: {result.get('overall_score')}/100  passed={result.get('passed')}")
        return result

    except Exception as e:
        print(f"[Scorer] Gemini scoring failed: {e}")
        return {
            "hook_score":    50,
            "story_score":   50,
            "insight_score": 50,
            "cta_score":     50,
            "overall_score": 50,
            "strongest":     "Unable to evaluate",
            "weakest":       "Unable to evaluate",
            "rewrite":       "Try again with more specific facts from the headlines",
            "passed":        False
        }


# ---------------------------------------------------------------------------
# Main scoring function — combines all 3 ML components
# ---------------------------------------------------------------------------
def score_script(
    script: dict,
    viral_headlines: list[str],
    trend_phrase: str,
    trend_score: float,
) -> dict:
    """
    Full hybrid scoring pipeline.

    Step 1: TF-IDF extracts unique phrases from real headlines
    Step 2: Gemini scores script against those real patterns
    Step 3: Returns combined result with specific feedback

    Args:
        script:          {hook, story, insight, cta}
        viral_headlines: real headlines from trend_agent
        trend_phrase:    e.g. "ai agents"
        trend_score:     0-100 from trend_agent

    Returns:
        full scoring result with breakdown and feedback
    """
    print(f"\n[Scorer] Scoring script about '{trend_phrase}'...")

    # Step 1 — TF-IDF: what phrases matter right now
    tfidf_phrases = extract_tfidf_phrases(viral_headlines, top_n=10)

    # Step 2 — Gemini chain-of-thought scoring
    gemini_result = score_script_gemini(
        script         = script,
        tfidf_phrases  = tfidf_phrases,
        viral_headlines= viral_headlines,
        trend_phrase   = trend_phrase,
        trend_score    = trend_score,
    )

    # Step 3 — Build final result
    overall = gemini_result.get("overall_score", 50)
    passed  = overall >= 65

    return {
        "score":         overall,
        "passed":        passed,
        "hook_score":    gemini_result.get("hook_score", 50),
        "story_score":   gemini_result.get("story_score", 50),
        "insight_score": gemini_result.get("insight_score", 50),
        "cta_score":     gemini_result.get("cta_score", 50),
        "strongest":     gemini_result.get("strongest", ""),
        "weakest":       gemini_result.get("weakest", ""),
        "rewrite":       gemini_result.get("rewrite", ""),
        "tfidf_phrases": tfidf_phrases,
    }


# ---------------------------------------------------------------------------
# Virality prediction — pure math, power law
# ---------------------------------------------------------------------------
def predict_virality(
    script: dict,
    trend_score: float,
    hook_similarity: float = 0.5,
) -> dict:
    """
    Predict virality 0-100 and estimated engagement metrics.
    Pure math. No API call.

    Signals:
      hook_similarity  (35%) — from sentence-transformers comparison
      trend_score      (35%) — from trend_agent acceleration math
      readability      (20%) — Flesch-Kincaid on full script
      length_fit       (10%) — how close to optimal word count

    Power law metric prediction:
      viral content follows exponential distribution
      base_views = 1000 × (score ^ 1.8)
    """
    hook    = script.get("hook", "")
    story   = script.get("story", "")
    insight = script.get("insight", "")
    cta     = script.get("cta", "")
    full    = f"{hook} {story} {insight} {cta}".strip()
    words   = full.split()
    wc      = len(words)

    # Readability — Flesch-Kincaid
    def count_syllables(word: str) -> int:
        word   = word.lower().strip(".,!?")
        vowels = re.findall(r'[aeiouy]+', word)
        count  = len(vowels)
        if word.endswith('e') and count > 1:
            count -= 1
        return max(count, 1)

    sentences     = max(len(re.findall(r'[.!?]+', full)), 1)
    syllables     = sum(count_syllables(w) for w in words)
    avg_sent_len  = wc / sentences
    avg_syl_word  = syllables / max(wc, 1)
    fre           = 206.835 - (1.015 * avg_sent_len) - (84.6 * avg_syl_word)
    fre           = max(0.0, min(100.0, fre))
    readability_n = fre / 100.0

    # Length fit — optimal 110-130 words
    distance   = max(0, wc - 130) if wc > 130 else max(0, 110 - wc)
    length_fit = max(0.0, 1.0 - distance / 60.0)

    # Composite score
    virality = (
        hook_similarity          * 0.35 +
        (trend_score / 100.0)    * 0.35 +
        readability_n            * 0.20 +
        length_fit               * 0.10
    ) * 100
    virality = round(virality, 1)

    # Power law metric prediction
    base_views  = int(1000 * (virality ** 1.8))
    high_views  = int(base_views * 1.7)

    def fmt(low: int, high: int) -> str:
        def abbr(n: int) -> str:
            if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
            if n >= 1_000:     return f"{n/1_000:.0f}K"
            return str(n)
        return f"{abbr(low)} – {abbr(high)}"

    grade = "high" if virality >= 75 else "medium" if virality >= 55 else "low"

    return {
        "score":            virality,
        "grade":            grade,
        "predicted_views":  fmt(base_views, high_views),
        "predicted_likes":  fmt(int(base_views * 0.07), int(high_views * 0.12)),
        "predicted_shares": fmt(int(base_views * 0.012), int(high_views * 0.022)),
        "predicted_saves":  fmt(int(base_views * 0.015), int(high_views * 0.028)),
        "breakdown": {
            "hook_similarity":  round(hook_similarity * 100, 1),
            "trend_momentum":   round(trend_score, 1),
            "readability":      round(fre, 1),
            "length_fit":       round(length_fit * 100, 1),
            "word_count":       wc,
        }
    }


# ---------------------------------------------------------------------------
# Run directly to test
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    # Simulate what trend_agent gives you
    viral_headlines = [
        "Most AI Agents Fail in Production Because They're Built Backwards",
        "40% of Enterprises Will Decommission Autonomous AI Agents",
        "AI coding agents ship at the cost of intuition and taste",
        "Why AI Agents Keep Failing at Simple Tasks",
        "The Real Reason Your AI Agent Doesn't Work in Production",
    ]

    test_script = {
        "hook":    "40% of AI agents are being fired — and the companies don't know why yet.",
        "story":   "A new report this week revealed most AI agents fail not because AI is bad, but because engineers build them backwards. Capability first. Real workflow second. The result is agents that nail demos and collapse in production.",
        "insight": "The failure was never the AI. It was always the architecture around it.",
        "cta":     "Follow before this becomes your company's most expensive lesson."
    }

    print("=" * 60)
    print("TEST 1 — TF-IDF phrase extraction")
    print("=" * 60)
    phrases = extract_tfidf_phrases(viral_headlines)
    print(f"Top phrases: {phrases}")

    print("\n" + "=" * 60)
    print("TEST 2 — Hook selection via cosine similarity")
    print("=" * 60)
    candidate_hooks = [
        "40% of AI agents are being fired quietly",
        "AI tools are getting better every day",
        "Most AI agents fail in production — here is why",
        "Your AI agent works in demos. It breaks in real life.",
        "Nobody told you enterprises are decommissioning AI agents",
    ]
    best_hook, sim_score = select_best_hook(candidate_hooks, viral_headlines)
    print(f"Best hook: \"{best_hook}\"")
    print(f"Similarity to viral headlines: {sim_score:.3f}")

    print("\n" + "=" * 60)
    print("TEST 3 — Full script scoring")
    print("=" * 60)
    result = score_script(
        script          = test_script,
        viral_headlines = viral_headlines,
        trend_phrase    = "ai agents",
        trend_score     = 92.0,
    )
    print(f"\nFinal score:   {result['score']}/100")
    print(f"Passed:        {result['passed']}")
    print(f"Hook score:    {result['hook_score']}")
    print(f"Story score:   {result['story_score']}")
    print(f"Strongest:     {result['strongest']}")
    print(f"Weakest:       {result['weakest']}")
    print(f"Rewrite:       {result['rewrite']}")

    print("\n" + "=" * 60)
    print("TEST 4 — Virality prediction")
    print("=" * 60)
    virality = predict_virality(
        script          = test_script,
        trend_score     = 92.0,
        hook_similarity = sim_score,
    )
    print(f"Virality score:   {virality['score']}/100  [{virality['grade'].upper()}]")
    print(f"Predicted views:  {virality['predicted_views']}")
    print(f"Predicted likes:  {virality['predicted_likes']}")
    print(f"Predicted shares: {virality['predicted_shares']}")
    print(f"Predicted saves:  {virality['predicted_saves']}")
    print(f"Breakdown:        {virality['breakdown']}")