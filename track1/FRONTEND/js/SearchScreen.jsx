/* Ratefluencer AI — Screen 1: Brand Search */
(function () {
  const { useState, useEffect } = React;
  const { L, formatFollowers, formatNum, fmtPct, fmtScore, titleCase, nicheHex, NICHE_SHORT, FillBar, Skeleton, Avatar, NicheBadge, scoreHex } = window.RF;
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

  const QUICK_TEMPLATES = [
    { icon: "Rocket",       label: "Product Launch",   color: "#7c3aed",
      category: "New product launch campaign", goal: "Awareness",
      desc: "Launching a new product and looking for creators who can build buzz, drive reach, and convert followers into early adopters." },
    { icon: "ShoppingBag",  label: "Festive Sale",     color: "#db2777",
      category: "Festive / seasonal sale campaign", goal: "Conversions",
      desc: "Running a festive promotion and need creators who can drive direct sales, share codes, and convert their audience." },
    { icon: "Smartphone",   label: "App Install",      color: "#0891b2",
      category: "Mobile app install campaign", goal: "Conversions",
      desc: "Driving app installs for a mobile product. Looking for creators with high save rates and tech-savvy audiences." },
    { icon: "Megaphone",    label: "Brand Awareness",  color: "#d97706",
      category: "Brand awareness and reach campaign", goal: "Awareness",
      desc: "Building brand presence with large, engaged audiences. Focus on reach, impressions, and brand recall." },
  ];

  const CAMPAIGN_WINS = [
    {
      brand: "Organic skincare brand", niche: "Beauty & Skincare", creators: 4, reach: "1.4M", roi: "4.1x", type: "Product Launch",
      logo: "🌿",
      tagline: "From zero buzz to 1.4M impressions in 3 weeks",
      story: "A Bengaluru-based D2C skincare brand was launching their first-ever serum. They had a great product but zero creator presence. Ratefluencer matched them with 4 micro-creators in the Beauty & Skincare niche — all with audience quality scores above 78.",
      outcome: "The campaign generated 1.4M organic impressions, 42K profile visits, and converted 3,800 first-time buyers — all within the first 3 weeks of launch.",
      quote: "We shortlisted 4 creators in under 10 minutes. Each one felt handpicked — because they were.",
      quotePerson: "Founder, Organic Skincare Brand",
      phases: [
        { icon: "FileText", label: "Brief submitted", detail: "Product launch, Beauty niche, ₹2L budget" },
        { icon: "Users",    label: "4 creators matched", detail: "Avg score 81 · Avg 68K followers" },
        { icon: "Video",    label: "Content live in 9 days", detail: "4 reels + 12 stories" },
        { icon: "TrendingUp", label: "1.4M reach achieved", detail: "4.1x ROI in 3 weeks" },
      ],
      metrics: [
        { label: "Impressions", value: "1.4M" },
        { label: "New buyers",  value: "3,800" },
        { label: "Avg score",   value: "81" },
        { label: "ROI",         value: "4.1x" },
      ],
    },
    {
      brand: "D2C fitness supplement", niche: "Fitness", creators: 3, reach: "920K", roi: "3.6x", type: "Festive Sale",
      logo: "💪",
      tagline: "3 creators. 920K reach. Festive season dominance.",
      story: "A protein supplement brand wanted to ride the Diwali wave but had failed with generic influencer campaigns before. Ratefluencer identified 3 fitness creators with high save-rates — the key signal for conversion-focused campaigns.",
      outcome: "Sales jumped 3.6x vs the previous festive season. The brand saw 920K combined reach and a 22% coupon redemption rate — one of the highest in the category.",
      quote: "The save-rate filter was a game-changer. These creators actually drove purchases, not just views.",
      quotePerson: "Marketing Head, D2C Fitness Brand",
      phases: [
        { icon: "FileText",   label: "Festive brief created", detail: "Conversion goal · ₹1.5L budget" },
        { icon: "ShieldCheck", label: "3 high-converter creators", detail: "Save rate > 4.2% · Fitness niche" },
        { icon: "Video",      label: "Content during peak week", detail: "6 reels with promo codes" },
        { icon: "TrendingUp", label: "3.6x ROI on sale day", detail: "22% coupon redemption" },
      ],
      metrics: [
        { label: "Reach",       value: "920K" },
        { label: "Redemptions", value: "22%" },
        { label: "Avg save rate", value: "4.2%" },
        { label: "ROI",         value: "3.6x" },
      ],
    },
    {
      brand: "EdTech mobile app", niche: "Entrepreneurship", creators: 2, reach: "680K", roi: "5.3x", type: "App Install",
      logo: "📱",
      tagline: "₹18 cost-per-install. 5.3x return. Two creators.",
      story: "An edtech startup needed app installs fast before a funding round. With a lean budget, they couldn't afford to waste money on creators who just drove vanity metrics. Ratefluencer's engagement depth scoring flagged 2 Entrepreneurship creators whose audiences were actively seeking productivity tools.",
      outcome: "12,400 verified app installs at ₹18 CPI — 60% below industry average. The campaign directly contributed to crossing 50K DAU before the funding pitch.",
      quote: "We hit our DAU target 11 days ahead of schedule. The audience match was scarily accurate.",
      quotePerson: "Growth Lead, EdTech App",
      phases: [
        { icon: "Smartphone",  label: "App install brief", detail: "Conversion goal · Entrepreneurship niche" },
        { icon: "Target",      label: "2 precision creators", detail: "Audience: startup founders 25–35" },
        { icon: "Video",       label: "Tutorial-style content", detail: "Deep-dive reels + link-in-bio" },
        { icon: "TrendingUp",  label: "12,400 installs · ₹18 CPI", detail: "5.3x ROI vs paid ads baseline" },
      ],
      metrics: [
        { label: "App installs", value: "12.4K" },
        { label: "Cost / install", value: "₹18" },
        { label: "DAU impact",  value: "+50K" },
        { label: "ROI",         value: "5.3x" },
      ],
    },
  ];

  function QuickTemplatePicker({ onPick }) {
    return React.createElement("div", { style: { marginBottom: 16 } },
      React.createElement("div", { style: {
        fontSize: 11, fontWeight: 700, color: "#64748b",
        textTransform: "uppercase", letterSpacing: "0.06em",
        marginBottom: 9, display: "flex", alignItems: "center", gap: 6,
      } }, React.createElement(L.Zap, { size: 12, color: "#7c3aed" }), "Quick start — pick a campaign type"),
      React.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 } },
        QUICK_TEMPLATES.map(function(t) {
          const Ico = L[t.icon];
          return React.createElement("button", {
            key: t.label, type: "button",
            onClick: function() { onPick(t); },
            style: {
              display: "flex", alignItems: "center", gap: 8,
              padding: "9px 12px", borderRadius: 10, cursor: "pointer",
              border: "1px solid " + t.color + "44",
              background: t.color + "12",
              color: t.color, fontSize: 12, fontWeight: 700,
              transition: "all 0.18s", textAlign: "left",
            },
          }, Ico ? React.createElement(Ico, { size: 14 }) : null, t.label);
        }),
      ),
    );
  }

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

  function SuccessStoryModal({ story, onClose, onReplicate }) {
    if (!story) return null;
    const phases = story.phases || [];
    return React.createElement(React.Fragment, null,
      // backdrop
      React.createElement("div", {
        onClick: onClose,
        style: {
          position: "fixed", inset: 0, zIndex: 1000,
          background: "rgba(15,23,42,0.45)",
          backdropFilter: "blur(3px)",
          animation: "rf-fadein 0.18s ease",
        }
      }),
      // modal card
      React.createElement("div", {
        style: {
          position: "fixed", top: "50%", left: "50%", zIndex: 1001,
          transform: "translate(-50%, -50%)",
          background: "#ffffff", borderRadius: 20,
          width: "min(560px, 95vw)", maxHeight: "88vh", overflowY: "auto",
          boxShadow: "0 24px 64px rgba(15,23,42,0.22)",
          animation: "rf-slideup 0.22s ease",
        }
      },
        // header band
        React.createElement("div", { style: {
          background: "linear-gradient(135deg,#6d28d9,#4f46e5)",
          padding: "28px 28px 22px", borderRadius: "20px 20px 0 0",
          position: "relative",
        } },
          React.createElement("button", {
            onClick: onClose,
            style: {
              position: "absolute", top: 16, right: 16,
              background: "rgba(255,255,255,0.15)", border: "none",
              color: "#fff", borderRadius: 8, width: 32, height: 32,
              cursor: "pointer", fontSize: 18, lineHeight: "32px", textAlign: "center",
              display: "flex", alignItems: "center", justifyContent: "center",
            }
          }, React.createElement(L.X, { size: 16 })),
          React.createElement("div", { style: { fontSize: 36, marginBottom: 10 } }, story.logo),
          React.createElement("div", { style: {
            display: "inline-flex", alignItems: "center", gap: 5,
            background: "rgba(255,255,255,0.18)", color: "#fff",
            fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.07em",
            padding: "3px 10px", borderRadius: 99, marginBottom: 10,
          } }, React.createElement(L.Trophy, { size: 11 }), "Success Story"),
          React.createElement("div", { style: { fontSize: 20, fontWeight: 800, color: "#fff", lineHeight: 1.3, marginBottom: 6 } }, story.tagline),
          React.createElement("div", { style: { fontSize: 13, color: "rgba(255,255,255,0.75)" } }, story.brand + " · " + story.niche),
        ),
        // body
        React.createElement("div", { style: { padding: "24px 28px" } },
          // key metrics strip
          React.createElement("div", { style: {
            display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
            gap: 10, marginBottom: 24,
          } },
            story.metrics.map(function(m) {
              return React.createElement("div", { key: m.label, style: {
                background: "#f8f9ff", borderRadius: 12, padding: "12px 10px",
                textAlign: "center", border: "1px solid #e8ecf5",
              } },
                React.createElement("div", { style: { fontSize: 18, fontWeight: 800, color: "#6d28d9" } }, m.value),
                React.createElement("div", { style: { fontSize: 10, color: "#64748b", fontWeight: 700, marginTop: 3, textTransform: "uppercase", letterSpacing: "0.04em" } }, m.label),
              );
            }),
          ),
          // story text
          React.createElement("div", { style: { fontSize: 14, color: "#334155", lineHeight: 1.7, marginBottom: 20 } }, story.story),
          React.createElement("div", { style: { fontSize: 14, color: "#334155", lineHeight: 1.7, marginBottom: 22 } }, story.outcome),
          // phases timeline
          React.createElement("div", { style: { marginBottom: 22 } },
            React.createElement("div", { style: { fontSize: 12, fontWeight: 800, color: "#0f172a", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 } }, "How it unfolded"),
            phases.map(function(p, idx) {
              const Ico = L[p.icon] || L.Circle;
              return React.createElement("div", { key: idx, style: {
                display: "flex", gap: 12, alignItems: "flex-start",
                paddingBottom: idx < phases.length - 1 ? 14 : 0,
              } },
                React.createElement("div", { style: {
                  width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
                  background: "#ede9fe", display: "flex", alignItems: "center", justifyContent: "center",
                  position: "relative",
                } },
                  React.createElement(Ico, { size: 14, color: "#7c3aed" }),
                  idx < phases.length - 1 && React.createElement("div", { style: {
                    position: "absolute", bottom: -14, left: "50%", transform: "translateX(-50%)",
                    width: 2, height: 14, background: "#e0d9ff",
                  } }),
                ),
                React.createElement("div", { style: { paddingTop: 4 } },
                  React.createElement("div", { style: { fontSize: 13, fontWeight: 700, color: "#0f172a" } }, p.label),
                  React.createElement("div", { style: { fontSize: 12, color: "#64748b", marginTop: 2 } }, p.detail),
                ),
              );
            }),
          ),
          // quote
          React.createElement("div", { style: {
            background: "linear-gradient(135deg,rgba(109,40,217,0.06),rgba(79,70,229,0.06))",
            border: "1px solid #e0d9ff", borderLeft: "3px solid #7c3aed",
            borderRadius: 12, padding: "14px 18px", marginBottom: 24,
          } },
            React.createElement("div", { style: { fontSize: 14, color: "#334155", fontStyle: "italic", lineHeight: 1.6, marginBottom: 8 } },
              "“" + story.quote + "”"),
            React.createElement("div", { style: { fontSize: 11, fontWeight: 700, color: "#7c3aed" } }, "— " + story.quotePerson),
          ),
          // CTA
          React.createElement("button", {
            onClick: function() { onReplicate(story); onClose(); },
            style: {
              width: "100%", padding: "14px", borderRadius: 12, border: "none",
              background: "linear-gradient(135deg,#6d28d9,#4f46e5)",
              color: "#fff", fontSize: 14, fontWeight: 800, cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            }
          },
            React.createElement(L.Copy, { size: 16 }), "Run a similar campaign for my brand →"
          ),
        ),
      ),
    );
  }

  function StatsPanel({ stats, loading, onViewCreator, onPickCampaign }) {
    const [topCreators, setTopCreators] = useState([]);
    const [hoverCreator, setHoverCreator] = useState(null);
    const [hoverCampaign, setHoverCampaign] = useState(null);
    const [activeStory, setActiveStory] = useState(null);
    useEffect(function() {
      api.getInfluencers({ sort_by: "ratefluencer_score", limit: 3 })
        .then(function(res) { setTopCreators(res.items || []); })
        .catch(function() {});
    }, []);

    if (loading) {
      return React.createElement("div", { className: "rf-statspanel" },
        React.createElement("div", { className: "rf-stat-grid" },
          [0, 1, 2, 3].map((i) => React.createElement("div", { key: i, className: "rf-stattile" },
            React.createElement(Skeleton, { w: 44, h: 44, r: 12 }),
            React.createElement("div", { style: { flex: 1 } }, React.createElement(Skeleton, { w: "60%", h: 18 }), React.createElement(Skeleton, { w: "40%", h: 11, style: { marginTop: 8 } })),
          )),
        ),
        React.createElement("div", { className: "rf-card", style: { marginTop: 16 } },
          [0, 1, 2].map((i) => React.createElement("div", { key: i, style: { display: "flex", gap: 12, alignItems: "center", padding: "14px 0", borderBottom: i < 2 ? "1px solid #262c36" : "none" } },
            React.createElement(Skeleton, { w: 44, h: 44, r: 44 }),
            React.createElement("div", { style: { flex: 1 } }, React.createElement(Skeleton, { w: "55%", h: 14 }), React.createElement(Skeleton, { w: "35%", h: 10, style: { marginTop: 8 } })),
            React.createElement(Skeleton, { w: 38, h: 28, r: 6 }),
          )),
        ),
      );
    }
    if (!stats) return null;

    return React.createElement("div", { className: "rf-statspanel" },
      React.createElement("div", { className: "rf-panel-eyebrow" },
        React.createElement(L.BarChart3, { size: 14 }), "Platform at a glance"),
      React.createElement("h2", { className: "rf-panel-title" }, "Access ",
        React.createElement("span", { className: "rf-grad-text" }, formatNum(stats.total_influencers)), " verified creators"),
      React.createElement("p", { className: "rf-panel-desc" }, "Every creator is scored across 24 quality signals — engagement authenticity, growth momentum, and brand fit. Brief once, shortlist with confidence."),
      React.createElement("div", { className: "rf-stat-grid" },
        React.createElement(StatTile, { icon: L.Users, value: formatNum(stats.total_influencers), label: "Creators indexed", accent: "#7c3aed" }),
        React.createElement(StatTile, { icon: L.Heart, value: fmtPct(stats.avg_engagement_rate), label: "Avg engagement rate", accent: "#db2777" }),
        React.createElement(StatTile, { icon: L.ShieldCheck, value: fmtScore(stats.avg_authenticity), label: "Avg audience quality", accent: "#16a34a" }),
        React.createElement(StatTile, { icon: L.Sparkles, value: fmtScore(stats.avg_ratefluencer_score), label: "Avg creator score", accent: "#ffd700" }),
      ),
      React.createElement("div", { className: "rf-card", style: { marginTop: 16 } },
        React.createElement("div", { className: "rf-card-head" },
          React.createElement("span", { className: "rf-card-title" }, "Top creators right now"),
          React.createElement("span", { className: "rf-card-meta", style: { color: "#7c3aed" } }, "Highest scored · Live"),
        ),
        topCreators.length === 0
          ? [0, 1, 2].map(function(i) {
              return React.createElement("div", { key: i, style: { display: "flex", gap: 12, alignItems: "center", padding: "14px 0", borderBottom: i < 2 ? "1px solid #262c36" : "none" } },
                React.createElement(Skeleton, { w: 44, h: 44, r: 44 }),
                React.createElement("div", { style: { flex: 1 } }, React.createElement(Skeleton, { w: "55%", h: 14 }), React.createElement(Skeleton, { w: "35%", h: 10, style: { marginTop: 8 } })),
                React.createElement(Skeleton, { w: 38, h: 28, r: 6 }),
              );
            })
          : topCreators.map(function(inf, i) {
              const sc = scoreHex(inf.ratefluencer_score);
              const isHov = hoverCreator === inf.id;
              return React.createElement("div", { key: inf.id,
                onClick: function() { onViewCreator && onViewCreator(inf); },
                onMouseEnter: function() { setHoverCreator(inf.id); },
                onMouseLeave: function() { setHoverCreator(null); },
                style: {
                  display: "flex", alignItems: "center", gap: 12,
                  padding: "10px 10px",
                  margin: "3px -10px",
                  borderRadius: 10,
                  borderBottom: !isHov && i < topCreators.length - 1 ? "1px solid #262c36" : "1px solid transparent",
                  cursor: "pointer",
                  background: isHov ? "rgba(124,58,237,0.10)" : "transparent",
                  transition: "background 0.15s",
                },
              },
                React.createElement(Avatar, { name: inf.full_name, niche: inf.niche, size: 46, username: inf.username }),
                React.createElement("div", { style: { flex: 1, minWidth: 0 } },
                  React.createElement("div", { style: { fontWeight: 700, fontSize: 13.5, color: "#0f172a", display: "flex", alignItems: "center", gap: 5, overflow: "hidden" } },
                    "@" + inf.username,
                    inf.is_verified ? React.createElement(L.BadgeCheck, { size: 14, color: "#2563eb" }) : null,
                  ),
                  React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 6, marginTop: 4 } },
                    React.createElement(NicheBadge, { niche: inf.niche }),
                    React.createElement("span", { style: { fontSize: 11, color: "#64748b", fontWeight: 600 } }, formatFollowers(inf.followers_count) + " followers"),
                  ),
                ),
                React.createElement("div", { style: { textAlign: "right", flexShrink: 0, display: "flex", alignItems: "center", gap: 6 } },
                  React.createElement("div", null,
                    React.createElement("div", { style: { fontSize: 20, fontWeight: 800, color: sc, lineHeight: 1 } }, Math.round(inf.ratefluencer_score)),
                    React.createElement("div", { style: { fontSize: 10, color: "#64748b", fontWeight: 700, textTransform: "uppercase", marginTop: 2 } }, "score"),
                  ),
                  React.createElement(L.ChevronRight, { size: 15, style: { color: isHov ? "#a78bfa" : "transparent", transition: "color 0.15s" } }),
                ),
              );
            }),
      ),
      React.createElement("div", { className: "rf-card", style: { marginTop: 14 } },
        React.createElement("div", { className: "rf-card-head" },
          React.createElement("span", { className: "rf-card-title" }, "Recent campaign outcomes"),
          React.createElement("span", { className: "rf-card-meta", style: { color: "#4ade80" } }, "Last 30 days"),
        ),
        CAMPAIGN_WINS.map(function(w, i) {
          const isHov = hoverCampaign === i;
          return React.createElement("div", { key: i,
            onClick: function() { setActiveStory(w); },
            onMouseEnter: function() { setHoverCampaign(i); },
            onMouseLeave: function() { setHoverCampaign(null); },
            style: {
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "10px 10px", margin: "3px -10px", borderRadius: 8,
              borderBottom: !isHov && i < CAMPAIGN_WINS.length - 1 ? "1px solid #e8ecf5" : "1px solid transparent",
              cursor: "pointer",
              background: isHov ? "rgba(74,222,128,0.07)" : "transparent",
              transition: "background 0.15s",
            },
          },
            React.createElement("div", null,
              React.createElement("div", { style: { fontSize: 13, fontWeight: 700, color: "#0f172a" } }, w.brand),
              React.createElement("div", { style: { fontSize: 11, color: "#64748b", marginTop: 2 } },
                w.type + " · " + w.creators + " creators · " + w.niche),
              isHov && React.createElement("div", { style: { fontSize: 10, color: "#7c3aed", fontWeight: 700, marginTop: 3, display: "flex", alignItems: "center", gap: 3 } },
                React.createElement(L.BookOpen, { size: 10 }), " Read success story"),
            ),
            React.createElement("div", { style: { textAlign: "right" } },
              React.createElement("div", { style: { fontSize: 15, fontWeight: 800, color: "#16a34a" } }, w.roi + " ROI"),
              React.createElement("div", { style: { fontSize: 11, color: "#64748b" } }, w.reach + " reach"),
            ),
          );
        }),
      ),
      React.createElement(SuccessStoryModal, {
        story: activeStory,
        onClose: function() { setActiveStory(null); },
        onReplicate: function(s) {
          const matchedTemplate = QUICK_TEMPLATES.find(function(t) { return t.label === s.type; });
          if (onPickCampaign && matchedTemplate) onPickCampaign(matchedTemplate);
        },
      }),
    );
  }

  function SearchScreen({ onResults, initialBrief, onViewCreator }) {
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

    function saveNewCampaign(brief, results) {
      var id = Date.now().toString();
      var campaigns = [];
      try { campaigns = JSON.parse(localStorage.getItem('rf_campaigns') || '[]'); } catch(e) {}
      campaigns.unshift({
        id: id,
        name: brief.category || brief.niche || 'New Campaign',
        brief: brief,
        status: 'Planning',
        date: new Date().toISOString(),
        matchedCount: (results && results.total) || 0,
      });
      localStorage.setItem('rf_campaigns', JSON.stringify(campaigns.slice(0, 30)));
      localStorage.setItem('rf_active_campaign', id);
      return id;
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
      api.search(brief).then((res) => {
        setSearching(false);
        var campId = saveNewCampaign(brief, res);
        onResults(brief, res, campId);
      }).catch(() => { setSearching(false); setError("Search failed. Please retry."); });
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
          React.createElement("p", { className: "rf-form-sub" }, "Describe your brief — we rank the right creators for you in seconds."),
          React.createElement("div", { style: { display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap" } },
            ["5,364 creators indexed", "20 niches covered", "Live quality scoring"].map(function(item) {
              return React.createElement("span", { key: item, style: {
                display: "inline-flex", alignItems: "center", gap: 4,
                fontSize: 11, fontWeight: 700, color: "#4ade80",
              } }, React.createElement(L.Check, { size: 11 }), item);
            }),
          ),
        ),
        React.createElement(QuickTemplatePicker, { onPick: function(t) { setCategory(t.category); setDesc(t.desc); setGoal(t.goal); } }),
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
        React.createElement(Field, { label: "Min audience quality", hint: React.createElement("b", { className: "rf-slider-val" }, minAuth > 0 ? minAuth + " / 100" : "No minimum") },
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
          : React.createElement(StatsPanel, { stats, loading, onViewCreator, onPickCampaign: function(t) { setCategory(t.category); setDesc(t.desc); setGoal(t.goal); } }),
      ),
    );
  }

  window.RFSearch = SearchScreen;
})();
