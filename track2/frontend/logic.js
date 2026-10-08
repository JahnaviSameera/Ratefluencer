/* ============================================================
   AI Generator — core logic (Gemini calls, prompts, scoring)
   Plain JS, attached to window. Loaded before the babel scripts.
   ============================================================ */

window.GEMINI_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent";

window.NICHES = [
  "Artificial Intelligence",
  "Creator Economy",
  "Startups",
  "Finance",
  "Technology",
  "Business",
];

window.NICHE_WEIGHTS = {
  "Artificial Intelligence": 0.92,
  "Creator Economy": 0.88,
  "Startups": 0.75,
  "Finance": 0.70,
  "Technology": 0.68,
  "Business": 0.65,
};

/* ---------- small helpers ---------- */
window.delay = (ms) => new Promise((r) => setTimeout(r, ms));

window.countWords = (s) =>
  (typeof s === "string" ? s : "").trim().split(/\s+/).filter(Boolean).length;

window.countHashtags = (s) => {
  if (Array.isArray(s)) return s.length;
  return (((s || "") + "").match(/#/g) || []).length;
};

window.fmtNum = (n) => {
  if (n == null || isNaN(n)) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(n >= 10_000 ? 0 : 1) + "K";
  return Math.round(n).toString();
};

/* ---------- prompts ---------- */
window.buildTrendPrompt = (niche) => `Find 5 trending topics right now in ${niche}.
Return a JSON array of exactly 5 objects, sorted by score descending.
Each object must have these keys:
{
  "phrase": string,
  "score": number (0-100),
  "urgency": one of "breaking" | "rising" | "established",
  "why_trending": string (1 sentence),
  "content_angle": string (best short-form reel angle),
  "target_audience": string (2-3 words),
  "velocity": number,
  "acceleration": number
}`;

window.buildScriptPrompt = (niche, trends) => `You are a viral short-form content strategist for the ${niche} niche.
For each of these 3 trending topics, generate a complete content package.
Topics (keep the same order):
${trends.map((t, i) => `${i + 1}) ${t.phrase}`).join("\n")}

Return a JSON array of exactly 3 objects, one per topic in the same order.
Each object must have these keys:
{
  "hook": string (a punchy 8-15 word opening line for a reel),
  "story": string (2-3 sentences),
  "insights": array of exactly 3 short strings,
  "cta": string (call to action — encourage follow/comment/share/save/tag),
  "estimated_duration_seconds": number,
  "linkedin_post": string,
  "linkedin_hashtags": array of strings,
  "instagram_caption": string (aim for 40-60 words),
  "instagram_hashtags": array of strings (aim for 10-12),
  "thumbnail_title": string (very short, punchy),
  "thumbnail_subtitle": string (short)
}`;

/* ---------- Gemini call with one stricter retry ---------- */
window.extractJson = (text) => {
  if (!text) throw new Error("Empty response");
  let t = text.trim();
  // strip ```json ... ``` fences if present
  const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) t = fence[1].trim();
  // grab the outermost array/object if there's surrounding prose
  const firstArr = t.indexOf("[");
  const firstObj = t.indexOf("{");
  let start = -1;
  if (firstArr === -1) start = firstObj;
  else if (firstObj === -1) start = firstArr;
  else start = Math.min(firstArr, firstObj);
  if (start > 0) {
    const open = t[start];
    const close = open === "[" ? "]" : "}";
    const end = t.lastIndexOf(close);
    if (end > start) t = t.slice(start, end + 1);
  }
  return JSON.parse(t);
};

window.callGeminiRaw = async (apiKey, prompt) => {
  const body = {
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: {
      temperature: 0.7,
      response_mime_type: "application/json",
    },
  };
  const res = await fetch(`${window.GEMINI_URL}?key=${encodeURIComponent(apiKey)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const e = await res.json();
      detail = e?.error?.message || "";
    } catch (_) {}
    throw new Error(`Gemini ${res.status}${detail ? " · " + detail : ""}`);
  }
  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  return text;
};

// Runs the prompt, parses JSON; on invalid JSON retries ONCE with a stricter prompt.
window.runGemini = async (apiKey, prompt) => {
  let text = await window.callGeminiRaw(apiKey, prompt);
  try {
    return window.extractJson(text);
  } catch (_) {
    const stricter =
      prompt +
      "\n\nIMPORTANT: Respond with ONLY raw, valid JSON. No markdown, no code fences, no commentary, no trailing text.";
    text = await window.callGeminiRaw(apiKey, stricter);
    return window.extractJson(text); // if this throws, caller shows error state
  }
};

/* ---------- Stage 3: virality scoring (pure JS, no API) ---------- */
window.scoreScript = (script, trend, niche) => {
  script = script || {};
  const hook = script.hook || "";
  const hookWords = window.countWords(hook);
  let hookStrength = 0;
  if (/\d/.test(hook)) hookStrength += 0.4;
  if (hook.trim().endsWith("?")) hookStrength += 0.3;
  if (hookWords >= 8 && hookWords <= 15) hookStrength += 0.3;
  hookStrength = Math.min(1, hookStrength);

  const urgency = ((trend && trend.urgency) || "").toLowerCase();
  const trendUrgency =
    urgency === "breaking" ? 1.0 : urgency === "rising" ? 0.67 : 0.33;

  const nicheWeight = window.NICHE_WEIGHTS[niche] != null ? window.NICHE_WEIGHTS[niche] : 0.65;

  const insights = Array.isArray(script.insights) ? script.insights : [];
  const insightCount = Math.min(1, insights.length / 3);

  const cta = (script.cta || "").toLowerCase();
  const ctaKeywords = ["follow", "comment", "share", "save", "tag"];
  const ctaHits = ctaKeywords.filter((k) => cta.includes(k)).length;
  const ctaStrength = Math.min(1, ctaHits / 2);

  const capWords = window.countWords(script.instagram_caption);
  const captionLength =
    capWords >= 40 && capWords <= 60
      ? 1
      : Math.max(0, 1 - Math.abs(50 - capWords) / 50);

  const tags = window.countHashtags(script.instagram_hashtags);
  const hashtagCount =
    tags >= 10 && tags <= 12 ? 1 : Math.max(0, 1 - Math.abs(11 - tags) / 11);

  const factors = [
    { key: "Hook strength", value: hookStrength, weight: 0.25 },
    { key: "Trend urgency", value: trendUrgency, weight: 0.15 },
    { key: "Niche weight", value: nicheWeight, weight: 0.15 },
    { key: "Insight depth", value: insightCount, weight: 0.15 },
    { key: "CTA strength", value: ctaStrength, weight: 0.1 },
    { key: "Caption length", value: captionLength, weight: 0.1 },
    { key: "Hashtag count", value: hashtagCount, weight: 0.1 },
  ];
  const score = Math.round(
    factors.reduce((s, f) => s + f.value * f.weight, 0) * 100
  );
  return { score, factors };
};

window.predictMetrics = (score) => {
  const views = Math.round(Math.exp(score / 15) * 100);
  return {
    views,
    likes: Math.round(views * 0.06),
    shares: Math.round(views * 0.012),
    saves: Math.round(views * 0.018),
  };
};

window.verdictOf = (score) => {
  if (score >= 70) return { label: "High", emoji: "🔥", tone: "high" };
  if (score >= 40) return { label: "Medium", emoji: "📈", tone: "mid" };
  return { label: "Low", emoji: "📉", tone: "low" };
};

window.topFactors = (factors, n = 5) =>
  [...factors].sort((a, b) => b.value * b.weight - a.value * a.weight).slice(0, n);

/* ============================================================
   Backend API — calls the FastAPI server at localhost:8000
   Falls back to direct Gemini if backend is unreachable.
   ============================================================ */
window.API_BASE = "http://localhost:8000";

window.callBackend = async (endpoint, body) => {
  const res = await fetch(`${window.API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail || ""; } catch (_) {}
    throw new Error(`Server error ${res.status}${detail ? ": " + detail : ""}`);
  }
  return res.json();
};

window.fetchTrends = async (niche) => {
  const data = await window.callBackend("/api/trends", {
    niche: niche.toLowerCase(),
    top_n: 5,
  });
  return data.trends || [];
};

window.fetchScripts = async (niche, trends) => {
  const data = await window.callBackend("/api/scripts", {
    niche: niche.toLowerCase(),
    trends,
    top_n: 3,
  });
  return data.scripts || [];
};

window.fetchVirality = async (scripts) => {
  const data = await window.callBackend("/api/virality", { scripts });
  return data.virality || [];
};

/* ============================================================
   Sample data — powers the "View sample run" demo so the
   dashboard is fully presentable without a live API key.
   ============================================================ */
window.SAMPLE_NICHE = "Artificial Intelligence";

window.SAMPLE_TRENDS = [
  {
    phrase: "Agentic AI replacing SaaS workflows",
    score: 94,
    urgency: "breaking",
    why_trending: "Enterprises are swapping point-tools for autonomous agents that chain tasks end to end.",
    content_angle: "Show one agent doing a 6-tool workflow in 30 seconds",
    target_audience: "founders, operators",
    velocity: 88,
    acceleration: 41,
  },
  {
    phrase: "On-device small language models",
    score: 87,
    urgency: "rising",
    why_trending: "New 3B-param models now run offline on phones with near-cloud quality.",
    content_angle: "Run an LLM with airplane mode on — live demo",
    target_audience: "developers, privacy fans",
    velocity: 72,
    acceleration: 33,
  },
  {
    phrase: "AI evals as the new moat",
    score: 81,
    urgency: "rising",
    why_trending: "Teams realize their eval suite, not the model, is the real competitive edge.",
    content_angle: "Why your prompt is worthless without evals",
    target_audience: "ML engineers",
    velocity: 64,
    acceleration: 27,
  },
  {
    phrase: "Context windows hit 10M tokens",
    score: 76,
    urgency: "established",
    why_trending: "Massive context is reshaping RAG architectures and doc workflows.",
    content_angle: "Drop a whole codebase into one prompt",
    target_audience: "builders",
    velocity: 51,
    acceleration: 12,
  },
  {
    phrase: "AI voice clones in customer support",
    score: 69,
    urgency: "established",
    why_trending: "Brands deploy cloned voices to cut support costs at scale.",
    content_angle: "Can you tell which agent is AI?",
    target_audience: "CX leaders",
    velocity: 44,
    acceleration: 9,
  },
];

window.SAMPLE_SCRIPTS = [
  {
    hook: "5 SaaS tools just got replaced by 1 AI agent — here's how",
    story:
      "A solo founder wired up a single agent to handle research, drafting, scheduling, and follow-up. The stack that used to cost $400/mo collapsed into one prompt. The team didn't shrink — the busywork did.",
    insights: [
      "Agents win when tasks chain — not on single-shot answers.",
      "The bottleneck moved from doing work to reviewing it.",
      "Your tool budget is now a context-engineering budget.",
    ],
    cta: "Follow for the full agent build, and comment 'STACK' to get the workflow.",
    estimated_duration_seconds: 38,
    linkedin_post:
      "We replaced 5 SaaS subscriptions with a single agentic workflow last month. Research, drafting, scheduling, follow-up — one agent, one context window. The lesson wasn't 'AI is magic.' It was that most software is just glue between steps, and agents are better glue. Here's what we kept, what we cut, and the 3 places it still needs a human.",
    linkedin_hashtags: ["#AgenticAI", "#Automation", "#FutureOfWork", "#SaaS", "#AItools"],
    instagram_caption:
      "We deleted 5 SaaS tools and replaced them with one AI agent that chains the whole workflow end to end. It didn't shrink the team — it killed the busywork and freed us to actually think. Save this before your next renewal and tag a founder who needs it. 👇",
    instagram_hashtags: [
      "#agenticai","#aitools","#automation","#startup","#founders","#productivity","#futureofwork","#aiagents","#buildinpublic","#techreels","#saas",
    ],
    thumbnail_title: "1 AGENT > 5 TOOLS",
    thumbnail_subtitle: "The stack is collapsing",
  },
  {
    hook: "Your phone just ran a real LLM with the wifi off — how?",
    story:
      "A new 3B-parameter model loads entirely on-device and answers offline with near-cloud quality. No latency, no data leaving the phone, no API bill. The demo: airplane mode on, full conversation still flowing.",
    insights: [
      "Small models closed most of the quality gap this year.",
      "On-device means privacy and zero marginal cost per call.",
      "The next app wave is offline-first AI.",
    ],
    cta: "Save this and share it with a dev who still thinks you need the cloud.",
    estimated_duration_seconds: 31,
    linkedin_post:
      "I ran a capable language model on my phone in airplane mode today. 3B parameters, fully on-device, near-instant. The implications are bigger than the demo: privacy by default, zero per-call cost, and a whole category of offline-first AI apps that just became possible. Cloud isn't dead — but 'always-on connection required' is.",
    linkedin_hashtags: ["#OnDeviceAI", "#SLM", "#EdgeAI", "#Privacy", "#MobileAI"],
    instagram_caption:
      "Airplane mode is ON and this language model is still answering — fully on-device, no cloud, no data leaving the phone. Near-instant, private, and free per call. This is the start of offline-first AI, and most people have no idea it's already here. Save it and tag a developer. ✈️",
    instagram_hashtags: [
      "#ondeviceai","#ai","#machinelearning","#privacy","#edgeai","#mobiledev","#techreels","#llm","#developer","#innovation","#smartphone","#offlineai",
    ],
    thumbnail_title: "LLM. NO WIFI.",
    thumbnail_subtitle: "Runs on your phone",
  },
  {
    hook: "Why your AI prompt is worthless without this one thing",
    story:
      "Two teams shipped the same model. One had a rigorous eval suite; the other shipped on vibes. Six months later only one could safely change a single line of their prompt. Evals — not the model — were the moat.",
    insights: [
      "Models are commoditizing; your eval set is proprietary.",
      "Without evals you can't tell a fix from a regression.",
      "Great evals turn prompt-tuning from guessing into engineering.",
    ],
    cta: "Comment 'EVALS' and I'll send the starter eval template — and follow for part 2.",
    estimated_duration_seconds: 34,
    linkedin_post:
      "Hot take that's aging well: your eval suite is a bigger moat than your model. Anyone can call the same API. What they can't copy is your curated set of hard cases, your scoring rubric, and the institutional knowledge of what 'good' looks like for your users. We treat evals like tests now — nothing ships without them.",
    linkedin_hashtags: ["#AIEvals", "#MLOps", "#LLMOps", "#AIEngineering", "#Quality"],
    instagram_caption:
      "Everyone obsesses over the model. The real moat is your evals — the hard test cases only you have. Without them you can't tell a fix from a regression, and you're shipping on vibes. Treat evals like unit tests. Save this and comment EVALS for the template. 🧪",
    instagram_hashtags: [
      "#aievals","#machinelearning","#mlops","#aiengineering","#llm","#datascience","#techreels","#prompting","#ai","#softwareengineering","#buildinpublic",
    ],
    thumbnail_title: "EVALS = THE MOAT",
    thumbnail_subtitle: "Not the model",
  },
];
