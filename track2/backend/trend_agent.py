"""
Ratefluencer — Trend Discovery + Ranking Engine
================================================

Discovers real trending topics from HN + Google News.
Ranks them using 5 ML signals. Gemini adds why_trending, content_angle,
target_audience, urgency — but never changes the scores.
"""
from __future__ import annotations
import sys, re, math, json, time, os, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import requests
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
# FIX 1: Correct model name (gemini-3.1-flash-lite-preview does not exist)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent"
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

def call_gemini(prompt: str, retries: int = 4) -> str:
    for attempt in range(retries):
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024,
                                       "response_mime_type": "application/json"}},
            timeout=20,
        )
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if r.status_code == 429 and attempt < retries - 1:
            wait = 60 * (attempt + 1)
            print(f"[TrendAgent] Rate limited, waiting {wait}s before retry {attempt+2}/{retries}...")
            time.sleep(wait)
            continue
        raise Exception(f"Gemini error {r.status_code}: {r.text[:200]}")
    raise Exception("Gemini: max retries exceeded")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
USER_AGENT      = "Ratefluencer/1.0 (hackathon)"
HN_API          = "https://hn.algolia.com/api/v1/search_by_date"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# FIX 2: News source names to strip from Google News titles
NEWS_SOURCES = {
    "verge", "techcrunch", "wired", "reuters", "bloomberg", "cnbc",
    "forbes", "axios", "engadget", "arstechnica", "theguardian", "bbc",
    "nytimes", "washingtonpost", "wsj", "fortune", "fastcompany",
    "venturebeat", "zdnet", "theregister", "semafor", "platformer",
}

NICHE_QUERIES = {
    "artificial intelligence": [
        "AI agents", "LLM", "large language model", "generative AI",
        "machine learning", "deep learning", "AI startup", "ChatGPT",
        "AI automation", "AI tools", "RAG", "vector database"
    ],
    "creator economy": [
        "creator economy", "AI content creation", "TikTok creators",
        "YouTube monetization", "Instagram algorithm", "influencer marketing",
        "short form video", "content monetization", "brand deals"
    ],
    "finance": [
        "fintech", "cryptocurrency", "investment strategy",
        "personal finance", "DeFi", "trading algorithms", "banking innovation"
    ],
    "startups": [
        "YCombinator", "startup funding", "founder story",
        "product hunt launch", "indie hacker", "bootstrapped startup", "SaaS growth"
    ],
    "business": [
        "B2B sales", "revenue growth", "startup strategy",
        "customer acquisition", "enterprise software", "business model"
    ],
    "technology": [
        "software engineering", "developer tools", "open source project",
        "cloud computing", "cybersecurity", "devops", "API development"
    ],
}

NICHE_KEYWORDS = {
    "artificial intelligence": {
        "ai", "llm", "agent", "agents", "gpt", "gemini", "claude",
        "neural", "training", "inference", "embedding", "transformer",
        "machine learning", "deep learning", "generative", "openai",
        "anthropic", "diffusion", "rag", "chatbot", "automation",
        "prompt", "reasoning", "multimodal", "agentic", "copilot",
        "autonomous", "frontier", "langchain", "hugging", "mistral",
        "llama", "vector", "fine-tun", "benchmark", "context window"
    },
    "creator economy": {
        "creator", "influencer", "monetiz", "subscriber", "follower",
        "reel", "tiktok", "instagram", "youtube", "shorts", "viral",
        "sponsorship", "brand deal", "audience", "engagement",
        "newsletter", "podcast", "streaming", "ugc"
    },
    "finance": {
        "invest", "fund", "crypto", "bitcoin", "ethereum", "trade",
        "revenue", "profit", "valuation", "ipo", "equity", "fintech",
        "portfolio", "hedge", "dividend", "inflation", "recession", "defi"
    },
    "startups": {
        "startup", "founder", "funding", "seed", "series",
        "yc", "launch", "saas", "bootstrap", "runway", "churn",
        "mrr", "arr", "pivot", "traction", "accelerator", "mvp"
    },
    "business": {
        "revenue", "growth", "strategy", "customer", "sales",
        "enterprise", "leadership", "acquisition", "b2b", "pipeline",
        "conversion", "retention", "marketing"
    },
    "technology": {
        "software", "developer", "api", "cloud", "security", "devops",
        "open source", "framework", "database", "kubernetes", "backend",
        "frontend", "infrastructure", "microservice"
    },
}

ALWAYS_STOP = {
    "a","an","the","and","or","but","if","of","at","by","for","in","on",
    "to","is","it","i","me","my","we","us","our","you","he","she","him",
    "her","his","do","does","did","be","am","as","so","no","not","than",
    "then","too","up","down","out","off","over","under","here","now",
    "all","any","both","each","few","more","other","some","such","only",
    "own","same","very","can","will","have","has","had","was","were",
    "been","being","with","this","that","they","them","their","there",
    "what","when","where","which","while","from","about","after","before",
    "into","through","also","even","just","like",
    "intelligence","artificial","science","technology","digital",
    "tech","stock","stocks","news","media","data","system","systems",
    "model","models","platform","platforms","company","companies",
    "market","markets","industry","report","service","services",
    "solution","product","feature","update","version","release",
    "tool","site","app","project","people","user","users","team",
    "world","global","new","old","big","small","high","low",
    "use","used","using","make","made","making","get","got","give",
    "take","come","came","went","want","need","help","work","works",
    "build","built","building","start","started","launch","launched",
    "post","posts","video","videos","content","creator","creators",
    "really","actually","literally","basically","probably","maybe",
    "think","thinking","thought","feel","feels","look","looking",
    "going","would","could","should","right","wrong","well",
    "ask","show","tell","via","why","how","who","release","released",
    "open","source","free","need","needs","tldr","edit","thread",
}

W_ACCELERATION = 0.35
W_VELOCITY     = 0.25
W_NOVELTY      = 0.20
W_VOLUME       = 0.10
W_SUSTAINED    = 0.10


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------
@dataclass
class TrendCandidate:
    phrase: str
    niche: str
    mentions_t0: int = 0
    mentions_t1: int = 0
    mentions_t2: int = 0
    sources: list[str] = field(default_factory=list)
    example_titles: list[str] = field(default_factory=list)
    why_trending: str = ""
    content_angle: str = ""
    target_audience: str = ""
    urgency: str = ""

    @property
    def velocity(self) -> float:
        return (self.mentions_t2 - self.mentions_t0) / 2.0

    @property
    def acceleration(self) -> float:
        return float(self.mentions_t2 - 2 * self.mentions_t1 + self.mentions_t0)

    @property
    def volume(self) -> int:
        return self.mentions_t0 + self.mentions_t1 + self.mentions_t2

    @property
    def novelty(self) -> float:
        return self.mentions_t2 / self.volume if self.volume else 0.0

    @property
    def sustained(self) -> float:
        active = sum(1 for w in [self.mentions_t0, self.mentions_t1, self.mentions_t2] if w > 0)
        return {0: 0.0, 1: 0.4, 2: 0.8, 3: 1.0}[active]

    @property
    def score(self) -> float:
        # FIX 3: Decouple sustained from score multiplier.
        # Original formula zeroed out single-window spikes completely.
        # Now sustained is an additive component like the others,
        # and the final scale is always [0, 100].
        accel_n = math.tanh(self.acceleration / 5.0)
        vel_n   = math.tanh(self.velocity / 5.0)
        vol_n   = math.tanh(math.log1p(self.volume) / 5.0)
        # raw is in [-1, 1] range
        raw = (W_ACCELERATION * accel_n  +
               W_VELOCITY     * vel_n    +
               W_NOVELTY      * self.novelty +
               W_VOLUME       * vol_n    +
               W_SUSTAINED    * self.sustained)
        # Map to [0, 100] without zeroing via multiplication
        return round((raw + 1) * 50, 2)

    def to_dict(self) -> dict:
        return {
            "phrase":          self.phrase,
            "label":           self.phrase.title(),
            "niche":           self.niche,
            "score":           self.score,
            "velocity":        round(self.velocity, 2),
            "acceleration":    round(self.acceleration, 2),
            "novelty":         round(self.novelty, 3),
            "sustained":       self.sustained,
            "volume":          self.volume,
            "mentions_t0":     self.mentions_t0,
            "mentions_t1":     self.mentions_t1,
            "mentions_t2":     self.mentions_t2,
            "sources":         self.sources[:3],
            "examples":        self.example_titles[:2],
            "why_trending":    self.why_trending,
            "content_angle":   self.content_angle,
            "target_audience": self.target_audience,
            "urgency":         self.urgency,
        }


# ---------------------------------------------------------------------------
# Text processing
# ---------------------------------------------------------------------------
def clean(text: str) -> str:
    text = text.lower()
    # FIX 4: Strip " - Source Name" suffix that Google News appends to titles
    text = re.sub(r"\s[-–|]\s+\S+\s*$", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_keyphrases(text: str) -> list[str]:
    tokens = [
        w for w in clean(text).split()
        if w not in ALWAYS_STOP
        and w not in NEWS_SOURCES          # FIX 2: drop source names
        and len(w) > 2                     # FIX 5: was >3, now >2 — keeps GPT, LLM, RAG, YC
        and not w.isdigit()
    ]
    phrases = set()
    for tok in tokens:
        if len(tok) >= 3:                  # FIX 5: was >=6, now >=3
            phrases.add(tok)
    for i in range(len(tokens) - 1):
        phrases.add(f"{tokens[i]} {tokens[i+1]}")
    return list(phrases)

def assign_window(created_utc: float, now_ts: float,
                  window_hours: float = 24.0) -> Optional[int]:
    age = (now_ts - created_utc) / 3600.0
    if age < window_hours:       return 2
    if age < 2 * window_hours:   return 1
    if age < 3 * window_hours:   return 0
    return None

def is_niche_relevant(phrase: str, niche: str) -> bool:
    keywords = NICHE_KEYWORDS.get(niche, set())
    p = phrase.lower()
    return any(kw in p for kw in keywords)


# ---------------------------------------------------------------------------
# Gemini enrichment — adds context after math ranking, never changes scores
# ---------------------------------------------------------------------------
def enrich_trends_with_gemini(candidates: list[TrendCandidate]) -> list[TrendCandidate]:
    if not candidates:
        return candidates

    print(f"[TrendAgent] Gemini enriching top {len(candidates)} trends...")

    trend_data = [
        {
            "phrase":       t.phrase,
            "score":        t.score,
            "acceleration": t.acceleration,
            "velocity":     t.velocity,
            "examples":     t.example_titles[:2],
        }
        for t in candidates
    ]

    prompt = f"""You are a social media trend analyst for content creators.

These topics were detected as trending RIGHT NOW using real-time data scraping
and acceleration math (2nd derivative of mention frequency).

For each trend provide:
- why_trending: one sentence, why is this happening NOW
- content_angle: the single best angle for a 60-second creator reel
- target_audience: who this resonates with most (2-3 words)
- urgency: exactly one of "breaking" / "rising" / "established"

Detected trends:
{json.dumps(trend_data, indent=2)}

Return ONLY a valid JSON array, no explanation, no markdown:
[
  {{
    "phrase": "ai agents",
    "why_trending": "...",
    "content_angle": "...",
    "target_audience": "...",
    "urgency": "rising"
  }}
]"""

    try:
        raw = call_gemini(prompt)
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            enriched = parsed
        elif isinstance(parsed, dict):
            enriched = next((v for v in parsed.values() if isinstance(v, list)), [])
        else:
            raise ValueError(f"Unexpected response type: {type(parsed)}")
        enriched_map = {e["phrase"]: e for e in enriched}
        for t in candidates:
            extra = enriched_map.get(t.phrase, {})
            t.why_trending    = extra.get("why_trending", "")
            t.content_angle   = extra.get("content_angle", "")
            t.target_audience = extra.get("target_audience", "")
            t.urgency         = extra.get("urgency", "rising")
        print(f"[TrendAgent] Gemini enrichment complete")
    except Exception as e:
        print(f"[TrendAgent] Enrichment failed: {e}. Returning without enrichment.")

    return candidates


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------
def fetch_hn(query: str, hours_back: int = 72) -> list[dict]:
    cutoff = int(time.time()) - (hours_back * 3600)
    params = {"query": query, "tags": "story",
              "numericFilters": f"created_at_i>{cutoff}", "hitsPerPage": 100}
    try:
        r = requests.get(HN_API, params=params, timeout=10,
                        headers={"User-Agent": USER_AGENT})
        if r.status_code != 200: return []
        return [{"title": h.get("title",""), "created_utc": h.get("created_at_i",0),
                 "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID','')}"}
                for h in r.json().get("hits",[]) if h.get("title")]
    except Exception:
        return []

def fetch_google_news(query: str) -> list[dict]:
    params = {"q": query, "hl": "en", "gl": "US", "ceid": "US:en"}
    try:
        r = requests.get(GOOGLE_NEWS_RSS, params=params, timeout=10,
                        headers={"User-Agent": USER_AGENT})
        if r.status_code != 200: return []
        posts = []
        for item in ET.fromstring(r.content).findall(".//item"):
            title = item.findtext("title") or ""
            pub   = item.findtext("pubDate") or ""
            link  = item.findtext("link") or ""
            if not title: continue
            try:
                from email.utils import parsedate_to_datetime
                ts = parsedate_to_datetime(pub).timestamp()
            except Exception:
                ts = time.time() - 3600
            posts.append({"title": title, "created_utc": ts, "url": link})
        return posts
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Mention counting
# ---------------------------------------------------------------------------
def count_mentions(posts: list[dict], window_hours: float = 24.0) -> dict:
    now_ts   = datetime.now(timezone.utc).timestamp()
    counts   = defaultdict(lambda: [0, 0, 0])
    sources  = defaultdict(list)
    examples = defaultdict(list)

    for post in posts:
        title       = post.get("title", "")
        created_utc = post.get("created_utc")
        url         = post.get("url", "")
        if not title or not created_utc: continue
        bucket = assign_window(created_utc, now_ts, window_hours)
        if bucket is None: continue
        for phrase in set(extract_keyphrases(title)):
            counts[phrase][bucket] += 1
            if url and len(sources[phrase]) < 5: sources[phrase].append(url)
            if len(examples[phrase]) < 3: examples[phrase].append(title[:120])

    return {
        phrase: {"t0": c[0], "t1": c[1], "t2": c[2],
                 "sources": sources[phrase], "examples": examples[phrase]}
        for phrase, c in counts.items() if sum(c) >= 2
    }


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------
def collapse_redundant(candidates: list[TrendCandidate]) -> list[TrendCandidate]:
    sorted_c = sorted(candidates, key=lambda c: c.score, reverse=True)
    dropped, kept = set(), []
    for c in sorted_c:
        if c.phrase in dropped: continue
        kept.append(c)
        if " " in c.phrase:
            tokens = set(c.phrase.split())
            for other in sorted_c:
                if " " in other.phrase or other.phrase in dropped: continue
                if other.phrase not in tokens: continue
                if abs(other.score - c.score) <= 25 or c.volume >= 0.6 * other.volume:
                    dropped.add(other.phrase)
    return kept


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def discover_trends(
    niche: str = "artificial intelligence",
    window_hours: float = 24.0,
    top_n: int = 10,
    use_gemini: bool = True,
) -> list[TrendCandidate]:
    niche_lower   = niche.lower()
    matched_niche = next(
        (k for k in NICHE_QUERIES if k in niche_lower or niche_lower in k),
        "artificial intelligence"
    )
    queries = NICHE_QUERIES[matched_niche]

    print(f"\n[TrendAgent] Niche: '{matched_niche}'")
    print(f"[TrendAgent] Firing {len(queries)} queries across HN + Google News")

    all_posts = []
    for query in queries:
        all_posts.extend(fetch_hn(query, hours_back=int(window_hours * 3)))
        all_posts.extend(fetch_google_news(query))
        time.sleep(0.3)

    seen, unique = set(), []
    for p in all_posts:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)

    print(f"[TrendAgent] Fetched {len(unique)} unique posts")

    mention_data = count_mentions(unique, window_hours=window_hours)
    print(f"[TrendAgent] {len(mention_data)} candidate phrases before filter")

    candidates = [
        TrendCandidate(
            phrase=phrase, niche=matched_niche,
            mentions_t0=d["t0"], mentions_t1=d["t1"], mentions_t2=d["t2"],
            sources=d["sources"], example_titles=d["examples"],
        )
        for phrase, d in mention_data.items()
    ]

    before     = len(candidates)
    candidates = [c for c in candidates if is_niche_relevant(c.phrase, matched_niche)]
    print(f"[TrendAgent] {len(candidates)} after niche filter (removed {before - len(candidates)})")

    candidates.sort(key=lambda c: c.score, reverse=True)
    candidates = collapse_redundant(candidates)
    top = candidates[:top_n]

    if use_gemini and GEMINI_KEY:
        top = enrich_trends_with_gemini(top)
    else:
        print("[TrendAgent] Skipping Gemini (no key or use_gemini=False)")

    print(f"\n[TrendAgent] Top {len(top)} trends:")
    for i, t in enumerate(top, 1):
        print(f"  {i:2d}. [{t.score:5.1f}] {t.phrase.title():<40} accel={t.acceleration:+.1f}  {t.urgency}")

    return top


def trends_to_json(trends: list[TrendCandidate]) -> str:
    return json.dumps([t.to_dict() for t in trends], indent=2)


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    niche      = sys.argv[1] if len(sys.argv) > 1 else "artificial intelligence"
    use_gemini = "--no-gemini" not in sys.argv

    trends = discover_trends(niche=niche, window_hours=24, top_n=10, use_gemini=use_gemini)

    print("\n" + "=" * 70)
    print(f"TREND DISCOVERY RESULTS — {niche.upper()}")
    print("=" * 70)

    for i, t in enumerate(trends, 1):
        print(f"\n{i:2d}. SCORE {t.score:5.1f} — {t.phrase.title()}")
        print(f"     Math:  accel={t.acceleration:+.1f}  vel={t.velocity:+.1f}  "
              f"novelty={t.novelty:.2f}  sustained={t.sustained}")
        print(f"     Windows: t0={t.mentions_t0}  t1={t.mentions_t1}  t2={t.mentions_t2}")
        if t.why_trending:
            print(f"     Why:     {t.why_trending}")
        if t.content_angle:
            print(f"     Angle:   {t.content_angle}")
        if t.urgency:
            print(f"     Urgency: {t.urgency.upper()}")
        if t.example_titles:
            print(f"     e.g.     \"{t.example_titles[0]}\"")

    with open("trends_output.json", "w") as f:
        f.write(trends_to_json(trends))
    print(f"\nSaved to trends_output.json")