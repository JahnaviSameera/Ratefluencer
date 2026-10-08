"""
Ratefluencer — Script Generation Engine
========================================

Takes top trends from trend_agent.discover_trends() and generates
for each trend (in one Gemini call):
  - 30-60s reel script  (hook, story, insights, cta)
  - LinkedIn post       (professional tone, hooks, hashtags)
  - Instagram caption   (casual tone, CTA, hashtags)
  - Thumbnail text      (title + subtitle)

Output: list of GeneratedContent dicts, also saved to scripts_output.json
"""
from __future__ import annotations
import sys, json, os, time
sys.stdout.reconfigure(encoding="utf-8")
import requests
from dataclasses import dataclass, field
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent"
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

def call_gemini(prompt: str, retries: int = 4) -> str:
    for attempt in range(retries):
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 8192,
                    "response_mime_type": "application/json",
                },
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if r.status_code == 429 and attempt < retries - 1:
            wait = 60 * (attempt + 1)
            print(f"[ScriptGen] Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        raise Exception(f"Gemini error {r.status_code}: {r.text[:200]}")
    raise Exception("Gemini: max retries exceeded")


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------
@dataclass
class GeneratedContent:
    trend_phrase:   str
    trend_score:    float
    niche:          str
    urgency:        str
    why_trending:   str
    content_angle:  str
    target_audience: str

    # Generated fields
    hook:           str = ""
    story:          str = ""
    insights:       list[str] = field(default_factory=list)
    cta:            str = ""
    estimated_duration_seconds: int = 0

    linkedin_post:  str = ""
    linkedin_hashtags: list[str] = field(default_factory=list)

    instagram_caption: str = ""
    instagram_hashtags: list[str] = field(default_factory=list)

    thumbnail_title:    str = ""
    thumbnail_subtitle: str = ""

    def to_dict(self) -> dict:
        return {
            "trend_phrase":    self.trend_phrase,
            "trend_score":     self.trend_score,
            "niche":           self.niche,
            "urgency":         self.urgency,
            "why_trending":    self.why_trending,
            "content_angle":   self.content_angle,
            "target_audience": self.target_audience,
            "reel_script": {
                "hook":       self.hook,
                "story":      self.story,
                "insights":   self.insights,
                "cta":        self.cta,
                "estimated_duration_seconds": self.estimated_duration_seconds,
            },
            "linkedin": {
                "post":      self.linkedin_post,
                "hashtags":  self.linkedin_hashtags,
            },
            "instagram": {
                "caption":   self.instagram_caption,
                "hashtags":  self.instagram_hashtags,
            },
            "thumbnail": {
                "title":    self.thumbnail_title,
                "subtitle": self.thumbnail_subtitle,
            },
        }


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
SYSTEM_CONTEXT = """You are a viral content strategist who writes scripts for
short-form creators (YouTube Shorts, Instagram Reels, TikTok) and professional
LinkedIn content. Your scripts are punchy, fact-dense, and optimised for
maximum watch-time and shareability."""


def _get_few_shot_block(trends: list[dict]) -> str:
    """
    Fetch real Instagram caption examples relevant to the current trends
    from the Instagram corpus (built by train_from_instagram.py).
    Returns a formatted block to inject into the prompt.
    """
    try:
        from caption_trainer import get_relevant_examples, format_few_shot_block
        phrase = trends[0].get("phrase", "") if trends else ""
        niche  = trends[0].get("niche",  "") if trends else ""
        examples = get_relevant_examples(phrase, niche, n=4)
        if examples:
            return format_few_shot_block(examples, label="Instagram captions from this niche")
    except Exception:
        pass
    return ""


def build_prompt(trends: list[dict], n_variants: int = 1) -> str:
    trend_block = json.dumps(
        [
            {
                "phrase":          t.get("phrase"),
                "score":           t.get("score"),
                "niche":           t.get("niche"),
                "urgency":         t.get("urgency", "rising"),
                "why_trending":    t.get("why_trending", ""),
                "content_angle":   t.get("content_angle", ""),
                "target_audience": t.get("target_audience", ""),
                "example_headlines": t.get("examples", [])[:2],
            }
            for t in trends
        ],
        indent=2,
    )

    few_shot = _get_few_shot_block(trends)

    variants_instruction = ""
    if n_variants > 1:
        variants_instruction = f"""
IMPORTANT: For EACH trend, generate {n_variants} DISTINCT variants.
Return a flat JSON array with {len(trends) * n_variants} objects total.
Each object must include a "variant_num" field (1, 2, or {n_variants}) and
"phrase" matching the trend. Vary the hook style, tone, and angle across variants.
"""

    return f"""{SYSTEM_CONTEXT}
{few_shot}
Below are trending topics detected RIGHT NOW using real-time data.
For EACH trend, generate ALL of the following in a single JSON response.
{variants_instruction}
TRENDS:
{trend_block}

OUTPUT FORMAT — return a JSON array with one object per trend{' per variant' if n_variants > 1 else ''}:
[
  {{
    "phrase": "exact phrase from input",
    {"\"variant_num\": 1," if n_variants > 1 else ""}
    "hook": "Opening line — must grab attention in first 3 seconds. Use a SPECIFIC number, stat, or surprising fact. Max 2 sentences.",
    "story": "The narrative body — context, why it matters now, one concrete example or case. 4-6 sentences. Conversational tone.",
    "insights": ["Insight 1 — specific, memorable, tweetable", "Insight 2", "Insight 3"],
    "cta": "Single clear call to action that creates urgency. Use words like 'follow', 'comment', 'save', 'tag'.",
    "estimated_duration_seconds": 45,
    "linkedin_post": "Full LinkedIn post. Professional but human tone. Start with a bold hook (no 'I am excited to share'). Include the story, 2-3 insights as short paragraphs, end with a question to drive comments. 150-200 words.",
    "linkedin_hashtags": ["#AI", "#Startups"],
    "instagram_caption": "Instagram caption. Casual, energetic, human. 2-3 short punchy sentences. Include 1 emoji. End with a direct question to drive comments. 40-60 words. Write like a real person, not a press release.",
    "instagram_hashtags": ["#AItools", "#CreatorEconomy"],
    "thumbnail_title": "5 words max. Bold number or power word.",
    "thumbnail_subtitle": "3-4 words. Adds curiosity."
  }}
]

Rules:
- Every field is required. No nulls, no empty strings.
- insights must be a list of exactly 3 strings.
- linkedin_hashtags: 3-5 tags. instagram_hashtags: 8-12 tags.
- estimated_duration_seconds: integer between 30 and 60.
- instagram_caption MUST feel human and conversational, not corporate.
- hook MUST contain a specific number or statistic.
- Return ONLY the JSON array. No markdown fences, no explanation."""



# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
def parse_gemini_response(raw: str, trends: list[dict]) -> list[GeneratedContent]:
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Find the first complete JSON array using a bracket counter
    # (handles model returning extra text or a second JSON block after the first)
    start = raw.find("[")
    if start == -1:
        raise ValueError(f"No JSON array in response.\nRaw: {raw[:300]}")
    depth, end = 0, -1
    in_str, escape = False, False
    for i, ch in enumerate(raw[start:], start):
        if escape:
            escape = False; continue
        if ch == "\\" and in_str:
            escape = True; continue
        if ch == '"':
            in_str = not in_str; continue
        if in_str:
            continue
        if ch == "[": depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i; break
    if end == -1:
        raise ValueError(f"Unclosed JSON array in response.\nRaw: {raw[:300]}")
    try:
        parsed = json.loads(raw[start:end+1])
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse Gemini response: {e}\nRaw: {raw[:300]}")

    if isinstance(parsed, dict):
        parsed = next((v for v in parsed.values() if isinstance(v, list)), [parsed])

    trend_map = {t["phrase"]: t for t in trends}
    results = []

    for item in parsed:
        phrase = item.get("phrase", "")
        trend  = trend_map.get(phrase, {})

        gc = GeneratedContent(
            trend_phrase    = phrase,
            trend_score     = trend.get("score", 0),
            niche           = trend.get("niche", ""),
            urgency         = trend.get("urgency", "rising"),
            why_trending    = trend.get("why_trending", ""),
            content_angle   = trend.get("content_angle", ""),
            target_audience = trend.get("target_audience", ""),

            hook            = item.get("hook", ""),
            story           = item.get("story", ""),
            insights        = item.get("insights", []),
            cta             = item.get("cta", ""),
            estimated_duration_seconds = int(item.get("estimated_duration_seconds", 45)),

            linkedin_post      = item.get("linkedin_post", ""),
            linkedin_hashtags  = item.get("linkedin_hashtags", []),

            instagram_caption  = item.get("instagram_caption", ""),
            instagram_hashtags = item.get("instagram_hashtags", []),

            thumbnail_title    = item.get("thumbnail_title", ""),
            thumbnail_subtitle = item.get("thumbnail_subtitle", ""),
        )
        results.append(gc)

    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_scripts(
    trends: list[dict],
    top_n: int = 3,
    n_variants: int = 1,
    auto_rank: bool = False,
) -> list[GeneratedContent]:
    """
    trends:      list of dicts from trend_agent
    top_n:       how many trends to generate scripts for
    n_variants:  generate N variants per trend and optionally auto-rank
    auto_rank:   if True + n_variants>1, score all variants and return only winners
    """
    if not GEMINI_KEY:
        raise EnvironmentError("GEMINI_API_KEY not set in environment / .env")

    sorted_trends = sorted(trends, key=lambda t: t.get("score", 0), reverse=True)
    selected      = sorted_trends[:top_n]

    print(f"\n[ScriptGen] Generating {n_variants} variant(s) for {len(selected)} trends...")
    for t in selected:
        print(f"  → [{t.get('score', 0):5.1f}] {t.get('phrase', '').title()}")

    prompt = build_prompt(selected, n_variants=n_variants)
    raw    = call_gemini(prompt)
    results = parse_gemini_response(raw, selected)

    print(f"[ScriptGen] Generated {len(results)} content packages")

    # Auto-rank: if multiple variants requested, score each and keep winners only
    if auto_rank and n_variants > 1:
        try:
            from caption_trainer import rank_variants
            # Group by phrase, rank within each group, keep best
            groups: dict[str, list] = {}
            for s in results:
                groups.setdefault(s.trend_phrase, []).append(s.to_dict())

            winners = []
            for phrase, variants in groups.items():
                trend_ctx = next((t for t in selected if t.get("phrase") == phrase), {})
                ranked    = rank_variants(variants, trend=trend_ctx)
                winner_d  = ranked["winner"]
                # Re-wrap as GeneratedContent
                gc = GeneratedContent(
                    trend_phrase    = winner_d.get("trend_phrase", phrase),
                    trend_score     = winner_d.get("trend_score", 0),
                    niche           = winner_d.get("niche", ""),
                    urgency         = winner_d.get("urgency", "rising"),
                    why_trending    = winner_d.get("why_trending", ""),
                    content_angle   = winner_d.get("content_angle", ""),
                    target_audience = winner_d.get("target_audience", ""),
                    hook            = winner_d.get("hook", ""),
                    story           = winner_d.get("story", ""),
                    insights        = winner_d.get("insights", []),
                    cta             = winner_d.get("cta", ""),
                    estimated_duration_seconds = int(winner_d.get("estimated_duration_seconds", 45)),
                    linkedin_post      = winner_d.get("linkedin_post", ""),
                    linkedin_hashtags  = winner_d.get("linkedin_hashtags", []),
                    instagram_caption  = winner_d.get("instagram_caption", ""),
                    instagram_hashtags = winner_d.get("instagram_hashtags", []),
                    thumbnail_title    = winner_d.get("thumbnail_title", ""),
                    thumbnail_subtitle = winner_d.get("thumbnail_subtitle", ""),
                )
                gc._variant_scores = ranked["scores"]
                winners.append(gc)
            print(f"[ScriptGen] Auto-ranked → returning {len(winners)} winners")
            return winners
        except Exception as e:
            print(f"[ScriptGen] Auto-rank failed ({e}), returning all variants")

    return results


def scripts_to_json(scripts: list[GeneratedContent]) -> str:
    return json.dumps([s.to_dict() for s in scripts], indent=2)


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------
def print_scripts(scripts: list[GeneratedContent]) -> None:
    for i, s in enumerate(scripts, 1):
        sep = "=" * 70
        print(f"\n{sep}")
        print(f"#{i}  [{s.trend_score:.1f}]  {s.trend_phrase.title()}  |  {s.urgency.upper()}")
        print(sep)

        print(f"\n--- REEL SCRIPT ({s.estimated_duration_seconds}s) ---")
        print(f"HOOK:    {s.hook}")
        print(f"STORY:   {s.story}")
        for j, ins in enumerate(s.insights, 1):
            print(f"  [{j}] {ins}")
        print(f"CTA:     {s.cta}")

        print(f"\n--- THUMBNAIL ---")
        print(f"Title:    {s.thumbnail_title}")
        print(f"Subtitle: {s.thumbnail_subtitle}")

        print(f"\n--- LINKEDIN ---")
        print(s.linkedin_post)
        print("  " + "  ".join(s.linkedin_hashtags))

        print(f"\n--- INSTAGRAM ---")
        print(s.instagram_caption)
        print("  " + "  ".join(s.instagram_hashtags))


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    # If trends_output.json exists (from trend_agent), use it.
    # Otherwise generate a minimal stub for testing without running trend_agent.
    trends_file = "trends_output.json"
    if os.path.exists(trends_file):
        with open(trends_file) as f:
            trends = json.load(f)
        print(f"[ScriptGen] Loaded {len(trends)} trends from {trends_file}")
    else:
        print("[ScriptGen] No trends_output.json found — using test stub")
        trends = [
            {
                "phrase": "ai agents",
                "score": 87.4,
                "niche": "artificial intelligence",
                "urgency": "breaking",
                "why_trending": "Multiple major labs released autonomous agent frameworks this week.",
                "content_angle": "Show exactly what an AI agent can do that a chatbot cannot.",
                "target_audience": "developers, founders",
                "examples": ["OpenAI launches Operator agent", "Google DeepMind agent beats humans at X"],
            },
            {
                "phrase": "rag pipeline",
                "score": 74.1,
                "niche": "artificial intelligence",
                "urgency": "rising",
                "why_trending": "Enterprises are replacing fine-tuning with RAG for cost reasons.",
                "content_angle": "3 mistakes every team makes when building their first RAG system.",
                "target_audience": "ML engineers",
                "examples": ["Why RAG beats fine-tuning for most use cases"],
            },
            {
                "phrase": "llm inference cost",
                "score": 68.9,
                "niche": "artificial intelligence",
                "urgency": "rising",
                "why_trending": "Token prices dropped 80% in 6 months — changing startup economics.",
                "content_angle": "How falling inference costs are making AI products 10x more viable.",
                "target_audience": "founders, PMs",
                "examples": ["Inference costs hit new lows as competition heats up"],
            },
        ]

    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    scripts = generate_scripts(trends, top_n=top_n)
    print_scripts(scripts)

    out_file = "scripts_output.json"
    with open(out_file, "w") as f:
        f.write(scripts_to_json(scripts))
    print(f"\n[ScriptGen] Saved to {out_file}")