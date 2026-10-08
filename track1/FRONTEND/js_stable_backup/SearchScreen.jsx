/* Ratefluencer AI — Screen 1: Brand Search */
(function () {
  const { useState, useEffect } = React;
  const { L, formatFollowers, formatNum, fmtPct, fmtScore, titleCase, nicheHex, NICHE_SHORT, FillBar, Skeleton } = window.RF;
  const api = window.RFApi;

  const NICHES = [
    "Fitness", "Health & Wellness", "Yoga & Meditation", "Nutrition & Diet",
    "Fashion", "Beauty & Skincare", "Lifestyle Vlogging", "Parenting & Family",
    "Travel", "Food & Cooking", "Home Decor & Interior", "DIY & Crafts",
    "Technology", "Gaming", "Finance & Investing", "Entrepreneurship",
    "Sports & Athletics", "Mental Health", "Music & Dance", "Comedy & Entertainment",
  ];
  const AGES = ["18-24", "25-34", "35-44", "45+"];
  const COUNTRIES = ["India", "USA", "UK", "UAE", "Singapore", "Canada", "Australia", "Germany", "France", "Brazil"];
  const GOALS = ["Awareness", "Conversions", "Engagement"];
  const MAXF = 25_000_000;

  function Field({ label, hint, children }) {
    return React.createElement("label", { className: "rf-field" },
      React.createElement("span", { className: "rf-field-label" }, label),
      children,
      hint ? React.createElement("span", { className: "rf-field-hint" }, hint) : null,
    );
  }

  function Select({ value, onChange, placeholder, options, render }) {
    return React.createElement("div", { className: "rf-selectwrap" },
      React.createElement("select", { className: "rf-input rf-select", value, onChange: (e) => onChange(e.target.value) },
        React.createElement("option", { value: "" }, placeholder),
        options.map((o) => React.createElement("option", { key: o, value: o }, render ? render(o) : o)),
      ),
      React.createElement(L.ChevronDown, { size: 16, className: "rf-select-caret" }),
    );
  }

  function StatTile({ icon, value, label, accent }) {
    const Ico = icon;
    return React.createElement("div", { className: "rf-stattile" },
      React.createElement("div", { className: "rf-stattile-icon", style: { background: accent + "1f", color: accent } },
        React.createElement(Ico, { size: 20 })),
      React.createElement("div", null,
        React.createElement("div", { className: "rf-stattile-value" }, value),
        React.createElement("div", { className: "rf-stattile-label" }, label),
      ),
    );
  }

  function StatsPanel({ stats, loading }) {
    if (loading) {
      return React.createElement("div", { className: "rf-statspanel" },
        React.createElement("div", { className: "rf-stat-grid" },
          [0, 1, 2, 3].map((i) => React.createElement("div", { key: i, className: "rf-stattile" },
            React.createElement(Skeleton, { w: 44, h: 44, r: 12 }),
            React.createElement("div", { style: { flex: 1 } }, React.createElement(Skeleton, { w: "60%", h: 18 }), React.createElement(Skeleton, { w: "40%", h: 11, style: { marginTop: 8 } })),
          )),
        ),
        React.createElement("div", { className: "rf-card", style: { marginTop: 16 } },
          [0, 1, 2, 3, 4, 5].map((i) => React.createElement(Skeleton, { key: i, w: "100%", h: 26, style: { marginBottom: 12 } })),
        ),
      );
    }
    if (!stats) return null;
    const maxN = Math.max(...stats.niche_breakdown.map((n) => n.count));
    return React.createElement("div", { className: "rf-statspanel" },
      React.createElement("div", { className: "rf-panel-eyebrow" },
        React.createElement(L.BarChart3, { size: 14 }), "Platform snapshot"),
      React.createElement("h2", { className: "rf-panel-title" }, "Live across ",
        React.createElement("span", { className: "rf-grad-text" }, formatNum(stats.total_reach)), " followers"),
      React.createElement("p", { className: "rf-panel-desc" }, "Every creator is scored on engagement, authenticity and growth — so you brief once and shortlist with confidence."),
      React.createElement("div", { className: "rf-stat-grid" },
        React.createElement(StatTile, { icon: L.Users, value: formatNum(stats.total_influencers), label: "Influencers tracked", accent: "#7c3aed" }),
        React.createElement(StatTile, { icon: L.Heart, value: fmtPct(stats.avg_engagement_rate), label: "Avg engagement rate", accent: "#db2777" }),
        React.createElement(StatTile, { icon: L.ShieldCheck, value: fmtScore(stats.avg_authenticity), label: "Avg authenticity", accent: "#16a34a" }),
        React.createElement(StatTile, { icon: L.Sparkles, value: fmtScore(stats.avg_ratefluencer_score), label: "Avg Ratefluencer™", accent: "#ffd700" }),
      ),
      React.createElement("div", { className: "rf-card", style: { marginTop: 16 } },
        React.createElement("div", { className: "rf-card-head" },
          React.createElement("span", { className: "rf-card-title" }, "Creators by niche"),
          React.createElement("span", { className: "rf-card-meta" }, stats.niche_breakdown.length + " categories"),
        ),
        React.createElement("div", { className: "rf-nichebars" },
          stats.niche_breakdown.map((n) => React.createElement("div", { key: n.niche, className: "rf-nichebar-row" },
            React.createElement("span", { className: "rf-nichebar-label" },
              React.createElement("span", { className: "rf-dot", style: { background: nicheHex(n.niche) } }),
              NICHE_SHORT[n.niche] || titleCase(n.niche)),
            React.createElement("div", { className: "rf-nichebar-track" },
              React.createElement("div", { className: "rf-nichebar-fill", style: { width: (n.count / maxN) * 100 + "%", background: nicheHex(n.niche) } })),
            React.createElement("span", { className: "rf-nichebar-count" }, n.count),
          )),
        ),
      ),
    );
  }

  function SearchScreen({ onResults, initialBrief }) {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searching, setSearching] = useState(false);
    const [optimizing, setOptimizing] = useState(false);
    const [optimized, setOptimized] = useState(false);
    const [error, setError] = useState(null);
    const b = initialBrief || {};
    const [category, setCategory] = useState(b.category || "");
    const [desc, setDesc] = useState(b.product_description || "");
    const [niche, setNiche] = useState(b.niche || "");
    const [age, setAge] = useState(b.target_age_group || "");
    const [country, setCountry] = useState(b.target_country || "");
    const [goal, setGoal] = useState(b.campaign_goal || "");
    const [minF, setMinF] = useState(b.min_followers || 0);
    const [minAuth, setMinAuth] = useState(b.min_authenticity || 0);
    const [keywords, setKeywords] = useState(b.keywords ? b.keywords.join(", ") : "");

    // Sync form fields when initialBrief changes (e.g. launched from trend alert)
    useEffect(() => {
      if (!initialBrief) return;
      if (initialBrief.category)            setCategory(initialBrief.category);
      if (initialBrief.product_description) setDesc(initialBrief.product_description);
      if (initialBrief.niche)               setNiche(initialBrief.niche);
      if (initialBrief.campaign_goal)       setGoal(initialBrief.campaign_goal);
      if (initialBrief.target_age_group)    setAge(initialBrief.target_age_group);
      if (initialBrief.target_country)      setCountry(initialBrief.target_country);
      if (initialBrief.keywords)            setKeywords(
        Array.isArray(initialBrief.keywords)
          ? initialBrief.keywords.join(", ")
          : initialBrief.keywords
      );
    }, [initialBrief]);

    function loadStats() {
      setLoading(true); setError(null);
      api.getStats().then((s) => { setStats(s); setLoading(false); })
        .catch((e) => { setError("Could not load platform stats."); setLoading(false); });
    }
    useEffect(loadStats, []);

    // ── Agent 1: Optimize Brief ──
    async function optimizeBrief() {
      if (!category && !desc) return;
      setOptimizing(true);
      try {
        const res = await fetch(`${window.RFApi.BASE}/api/optimize-brief`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ category, product_description: desc, niche, campaign_goal: goal, keywords }),
        });
        if (!res.ok) throw new Error("Optimization failed");
        const data = await res.json();

        // Auto-fill form with optimized values
        if (data.refined_brief) {
          if (data.refined_brief.product_description) setDesc(data.refined_brief.product_description);
          if (data.refined_brief.target_audience)     setAge("");
        }
        if (data.target_niches && data.target_niches[0]) setNiche(data.target_niches[0]);
        if (data.keywords && data.keywords.length)        setKeywords(data.keywords.join(", "));
        setOptimized(true);
        setTimeout(() => setOptimized(false), 3000);
      } catch(e) {
        setError("Brief optimization failed — try again.");
      } finally {
        setOptimizing(false);
      }
    }

    function submit(e) {
      e && e.preventDefault();
      const brief = {
        category, product_description: desc, niche, target_age_group: age,
        target_country: country, campaign_goal: goal,
        keywords: keywords.split(",").map((k) => k.trim()).filter(Boolean),
        min_followers: minF || 0, min_authenticity: minAuth || 0, top_n: 12,
      };
      setSearching(true);
      api.search(brief).then((res) => { setSearching(false); onResults(brief, res); })
        .catch(() => { setSearching(false); setError("Search failed. Please retry."); });
    }

    return React.createElement("div", { className: "rf-search" },
      // ── left form ──
      React.createElement("form", { className: "rf-search-form", onSubmit: submit },
        React.createElement("div", { className: "rf-form-head" },
          React.createElement("div", { className: "rf-form-eyebrow" }, React.createElement(L.Target, { size: 14 }), "Campaign brief"),
          React.createElement("div", { style: { display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 10 } },
            React.createElement("h1", { className: "rf-form-title" }, "Find your perfect ", React.createElement("span", { className: "rf-grad-text" }, "creator")),
            React.createElement("button", {
              type: "button",
              onClick: optimizeBrief,
              disabled: optimizing || (!category && !desc),
              style: {
                display: "flex", alignItems: "center", gap: 6,
                padding: "8px 16px", borderRadius: 8, border: "none", cursor: "pointer",
                background: optimized
                  ? "rgba(34,197,94,0.2)"
                  : "linear-gradient(135deg,#7c3aed,#06b6d4)",
                color: optimized ? "#4ade80" : "#fff",
                fontSize: 12, fontWeight: 700, whiteSpace: "nowrap",
                opacity: (!category && !desc) ? 0.4 : 1,
              }
            },
              optimizing ? "✦ Optimizing…" : optimized ? "✓ Brief Optimized!" : "✦ Optimize with AI"
            ),
          ),
          React.createElement("p", { className: "rf-form-sub" }, "Tell us about the campaign — we’ll rank India’s creators by brand fit."),
        ),
        React.createElement(Field, { label: "Campaign category" },
          React.createElement("input", { className: "rf-input", value: category, onChange: (e) => setCategory(e.target.value), placeholder: "e.g. AI productivity app launch" })),
        React.createElement(Field, { label: "Product description" },
          React.createElement("textarea", { className: "rf-input rf-textarea", value: desc, onChange: (e) => setDesc(e.target.value), rows: 3, placeholder: "What are you promoting, and what makes it special?" })),
        React.createElement("div", { className: "rf-field-row" },
          React.createElement(Field, { label: "Niche" }, React.createElement(Select, { value: niche, onChange: setNiche, placeholder: "Any niche", options: NICHES, render: titleCase })),
          React.createElement(Field, { label: "Campaign goal" }, React.createElement(Select, { value: goal, onChange: setGoal, placeholder: "Any goal", options: GOALS })),
        ),
        React.createElement("div", { className: "rf-field-row" },
          React.createElement(Field, { label: "Target age group" }, React.createElement(Select, { value: age, onChange: setAge, placeholder: "Any age", options: AGES })),
          React.createElement(Field, { label: "Target country" }, React.createElement(Select, { value: country, onChange: setCountry, placeholder: "Any country", options: COUNTRIES })),
        ),
        React.createElement(Field, { label: "Min followers", hint: React.createElement("b", { className: "rf-slider-val" }, minF > 0 ? formatFollowers(minF) + "+" : "No minimum") },
          React.createElement("input", { type: "range", className: "rf-slider", min: 0, max: MAXF, step: 50000, value: minF, onChange: (e) => setMinF(+e.target.value) })),
        React.createElement(Field, { label: "Min authenticity score", hint: React.createElement("b", { className: "rf-slider-val" }, minAuth > 0 ? minAuth + " / 100" : "No minimum") },
          React.createElement("input", { type: "range", className: "rf-slider", min: 0, max: 100, step: 1, value: minAuth, onChange: (e) => setMinAuth(+e.target.value) })),
        React.createElement(Field, { label: "Keywords", hint: "Comma separated" },
          React.createElement("input", { className: "rf-input", value: keywords, onChange: (e) => setKeywords(e.target.value), placeholder: "saas, automation, founders" })),
        React.createElement("button", { type: "submit", className: "rf-btn rf-btn-primary rf-btn-block", disabled: searching },
          searching ? React.createElement(React.Fragment, null, React.createElement("span", { className: "rf-spinner" }), "Scoring creators…")
                    : React.createElement(React.Fragment, null, React.createElement(L.Search, { size: 18 }), "Find influencers", React.createElement(L.ArrowRight, { size: 18 }))),
        error ? React.createElement("div", { className: "rf-inline-error" }, React.createElement(L.AlertTriangle, { size: 14 }), error) : null,
      ),
      // ── right panel ──
      React.createElement("div", { className: "rf-search-right" },
        error && !loading ? React.createElement("div", { className: "rf-errorcard" },
          React.createElement(L.WifiOff, { size: 22 }),
          React.createElement("div", { className: "rf-errorcard-title" }, "Couldn’t load stats"),
          React.createElement("button", { className: "rf-btn rf-btn-ghost", onClick: loadStats }, React.createElement(L.RotateCcw, { size: 15 }), "Retry"))
          : React.createElement(StatsPanel, { stats, loading }),
      ),
    );
  }

  window.RFSearch = SearchScreen;
})();
