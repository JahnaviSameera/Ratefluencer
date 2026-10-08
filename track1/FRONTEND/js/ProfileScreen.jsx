/* Ratefluencer AI — Screen 3: Influencer Profile Deep Dive */
(function () {
  const { useState, useEffect } = React;
  const RF = window.RF;
  const { L, formatFollowers, formatNum, fmtPct, fmtScore, scoreHex, titleCase, NicheBadge, TierBadge, Avatar, Dial, Skeleton } = RF;
  const { AreaTrend } = window.RFCharts;
  const api = window.RFApi;

  function cleanReason(r) {
    return (r || "")
      .replace(/^[✓⚠]\s*/u, "")
      .replace(/semantic fit/gi, "content fit")
      .replace(/semantic/gi, "content");
  }

  function bestFor(inf) {
    const saveRate = inf.save_rate || 0;
    const followers = inf.followers_count || 0;
    const ter = inf.true_engagement_rate || 0;
    if (saveRate > 0.04)    return { label: "Best for Conversions",    color: "#22c55e", Icon: L.ShoppingBag };
    if (followers > 200000) return { label: "Best for Awareness",      color: "#2563eb", Icon: L.Megaphone };
    if (ter > 5)            return { label: "Best for Engagement",     color: "#db2777", Icon: L.Heart };
    return                         { label: "Best for Brand Building", color: "#7c3aed", Icon: L.Sparkles };
  }

  function estCostRange(followers) {
    if (!followers)          return null;
    if (followers < 10000)   return "Est. ₹2K–₹8K / post";
    if (followers < 50000)   return "Est. ₹8K–₹25K / post";
    if (followers < 200000)  return "Est. ₹25K–₹80K / post";
    if (followers < 1000000) return "Est. ₹80K–₹3L / post";
    return "Est. ₹3L+ / post";
  }

  function Section({ icon, title, sub, right, children, accent }) {
    const Ico = icon;
    return React.createElement("section", { className: "rf-section" },
      React.createElement("div", { className: "rf-section-head" },
        React.createElement("div", { className: "rf-section-titlewrap" },
          Ico ? React.createElement("span", { className: "rf-section-icon", style: { background: (accent || "#7c3aed") + "1f", color: accent || "#7c3aed" } }, React.createElement(Ico, { size: 18 })) : null,
          React.createElement("div", null,
            React.createElement("h2", { className: "rf-section-title" }, title),
            sub ? React.createElement("p", { className: "rf-section-sub" }, sub) : null),
        ),
        right || null,
      ),
      children,
    );
  }

  function StatCard({ label, value, sub, subColor, icon }) {
    const Ico = icon;
    return React.createElement("div", { className: "rf-statcard" },
      React.createElement("div", { className: "rf-statcard-top" },
        React.createElement("span", { className: "rf-statcard-label" }, label),
        Ico ? React.createElement(Ico, { size: 15, className: "rf-statcard-ico" }) : null),
      React.createElement("div", { className: "rf-statcard-value" }, value),
      sub ? React.createElement("div", { className: "rf-statcard-sub", style: subColor ? { color: subColor } : null }, sub) : null,
    );
  }

  function AuthFactor({ f }) {
    // Map raw backend snake_case keys → readable labels
    const KEY_LABELS = {
      real_followers_pct:        "Real Followers",
      bot_followers_pct:         "Bot Followers",
      suspicious_followers_pct:  "Suspicious Followers",
      comment_spam_ratio:        "Comment Spam",
      unique_commenters_ratio:   "Unique Commenters",
      spike_ratio:               "Follower Spike",
      follower_following_ratio:  "Follower / Following",
      profile_completeness:      "Profile Completeness",
      engagement_vs_benchmark:   "ER vs Benchmark",
      engagement_consistency:    "Engagement Consistency",
      posting_regularity:        "Posting Regularity",
      avg_comment_length:        "Avg Comment Length",
      gemini_comment_quality:    "Comment Quality",
    };
    var rawKey = (f.key || "").toLowerCase().replace(/\s+/g, "_");
    var label  = KEY_LABELS[rawKey]
                 || f.key.replace(/_/g, " ").replace(/\b\w/g, function(c) { return c.toUpperCase(); });

    // Normalize value + unit
    // Backend sends 0–1 fractions for % metrics (e.g. 0.873 = 87.3%)
    var displayValue = f.value;
    var displayUnit  = f.unit;

    if ((f.unit === "%" || f.unit === "/1.0") && f.value >= 0 && f.value <= 1) {
      // 0–1 decimal fraction → convert to percentage
      displayValue = Math.round(f.value * 1000) / 10;
      displayUnit  = "%";
    } else if (f.unit === "%" && f.value > 100) {
      // Ratio like Follower/Following 10062 — not a real %, show as ×
      displayValue = Number(f.value).toLocaleString("en-IN", { maximumFractionDigits: 1 });
      displayUnit  = "×";
    }

    // Bar fill (0–100)
    var frac;
    if (f.unit === "x") {
      frac = Math.min(100, (f.value / 3) * 100);
    } else if (f.signed) {
      frac = Math.min(100, (Math.abs(f.value) / 5) * 100);
    } else if ((f.unit === "%" || f.unit === "/1.0") && f.value >= 0 && f.value <= 1) {
      frac = f.value * 100;
    } else if (f.unit === "%" && f.value > 100) {
      frac = 100;
    } else {
      frac = Math.min(100, typeof displayValue === "number" ? displayValue : f.value);
    }

    var color  = f.good ? "#16a34a" : "#dc2626";
    var prefix = f.signed && f.value > 0 ? "+" : "";
    var suffix = displayUnit === "%" ? "%" : (displayUnit === "×" || displayUnit === "x") ? "×" : "";
    var valTxt = prefix + displayValue + suffix;

    return React.createElement("div", { className: "rf-factor" },
      React.createElement("div", { className: "rf-factor-head" },
        React.createElement("span", { className: "rf-factor-label" },
          React.createElement(f.good ? L.CheckCircle2 : L.AlertTriangle, { size: 14, style: { color } }), label),
        React.createElement("b", { className: "rf-factor-val", style: { color } }, valTxt)),
      React.createElement("div", { className: "rf-factor-track" },
        React.createElement("div", { className: "rf-factor-fill", style: { width: frac + "%", background: color } })),
    );
  }

  function AddToCampaignBtn({ inf, activeCampaignId, addToCollabProfile }) {
    const [state, setState] = React.useState("idle"); // idle | added | already
    function handle() {
      var ok = addToCollabProfile();
      setState(ok ? "added" : "already");
      setTimeout(function() { setState("idle"); }, 2500);
    }
    var label = state === "added" ? "✓ Added to campaign!" : state === "already" ? "Already shortlisted" : "+ Add to Campaign";
    var bg    = state === "added" ? "#f0fdf4" : state === "already" ? "#f8f9ff" : "linear-gradient(135deg,#16a34a,#15803d)";
    var color = state === "added" ? "#16a34a" : state === "already" ? "#7c3aed" : "#fff";
    var border= state !== "idle"  ? "1px solid #bbf7d0" : "none";
    return React.createElement("button", {
      onClick: handle,
      style: {
        display: "flex", alignItems: "center", gap: 6,
        padding: "8px 16px", borderRadius: 8, border: border, cursor: "pointer",
        background: bg, color: color, fontSize: 12, fontWeight: 700,
        whiteSpace: "nowrap", transition: "all 0.2s",
      }
    }, React.createElement(L.Bookmark, { size: 13 }), label);
  }

  function ProfileScreen({ initial, onBack, fromSearch, activeCampaignId }) {
    const [inf, setInf] = useState(initial);
    const [loading, setLoading] = useState(!initial || !initial.auth);
    const [error, setError] = useState(null);

    function load() {
      setError(null); setLoading(true);
      api.getInfluencer(initial.id).then((full) => {
        if (!full) { setError("Profile not found."); setLoading(false); return; }
        // preserve brand match data from search if present
        setInf({ ...full, brand_match: initial.brand_match, match_reasons: initial.match_reasons, match_warnings: initial.match_warnings });
        setLoading(false);
      }).catch(() => { setError("Couldn’t load this profile."); setLoading(false); });
    }
    useEffect(load, [initial.id]);

    if (loading) {
      return React.createElement("div", { className: "rf-profile" },
        React.createElement("button", { className: "rf-backbtn", onClick: onBack },
          React.createElement(L.ArrowLeft, { size: 16 }), fromSearch ? "Back to results" : "Back to discovery"),
        React.createElement("div", { style: { marginTop: 16 } },
          React.createElement(Skeleton, { w: "100%", h: 180, r: 18 }),
          React.createElement(Skeleton, { w: "100%", h: 120, r: 18, style: { marginTop: 18 } }),
          React.createElement(Skeleton, { w: "100%", h: 300, r: 18, style: { marginTop: 18 } })));
    }
    if (error) {
      return React.createElement("div", { className: "rf-profile" },
        React.createElement("button", { className: "rf-backbtn", onClick: onBack }, React.createElement(L.ArrowLeft, { size: 16 }), "Back"),
        React.createElement("div", { className: "rf-errorcard rf-errorcard-wide" }, React.createElement(L.WifiOff, { size: 22 }),
          React.createElement("div", { className: "rf-errorcard-title" }, error),
          React.createElement("button", { className: "rf-btn rf-btn-ghost", onClick: load }, React.createElement(L.RotateCcw, { size: 15 }), "Retry")));
    }

    const erUp = inf.engagement_rate >= inf.benchmark;
    const d7 = Math.round(inf.followers_30d_delta * 0.24);
    const series = api.simSeries(inf);
    const g = inf.growth, a = inf.auth;

    // Add-to-campaign helper (inline)
    function addToCollabProfile() {
      if (!activeCampaignId) return false;
      var campaigns = [];
      try { campaigns = JSON.parse(localStorage.getItem('rf_campaigns') || '[]'); } catch(e) {}
      var camp = campaigns.find(function(c) { return c.id === activeCampaignId; });
      if (!camp) return false;
      var collabs = [];
      try { collabs = JSON.parse(localStorage.getItem('rf_collabs') || '[]'); } catch(e) {}
      var key = String(inf.id) + '_' + activeCampaignId;
      if (collabs.find(function(c) { return c.id === key; })) return false;
      collabs.unshift({
        id: key, creatorId: String(inf.id),
        creator: {
          id: inf.id, username: inf.username, full_name: inf.full_name,
          niche: inf.niche, followers_count: inf.followers_count,
          ratefluencer_score: inf.ratefluencer_score, tier: inf.tier, is_verified: inf.is_verified,
        },
        campaignId: activeCampaignId, campaignName: camp.name,
        status: 'Shortlisted', date: new Date().toISOString(),
      });
      localStorage.setItem('rf_collabs', JSON.stringify(collabs));
      return true;
    }

    return React.createElement("div", { className: "rf-profile" },
      React.createElement("button", { className: "rf-backbtn", onClick: onBack },
        React.createElement(L.ArrowLeft, { size: 16 }), fromSearch ? "Back to results" : "Back to discovery"),

      // ── header ──
      React.createElement("div", { className: "rf-card rf-profile-head" },
        React.createElement("div", { className: "rf-profile-id" },
          React.createElement(Avatar, { name: inf.full_name, niche: inf.niche, size: 88, username: inf.username }),
          React.createElement("div", null,
            React.createElement("div", { className: "rf-profile-user" }, "@" + inf.username,
              inf.is_verified ? React.createElement(L.BadgeCheck, { size: 22, className: "rf-verified" }) : null),
            React.createElement("div", { className: "rf-profile-name" }, inf.full_name),
            React.createElement("div", { className: "rf-row-badges", style: { marginTop: 10 } },
              React.createElement(NicheBadge, { niche: inf.niche }), React.createElement(TierBadge, { tier: inf.tier })),
            React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 8, marginTop: 10, flexWrap: "wrap" } },
              (function() {
                const bf = bestFor(inf);
                return React.createElement("span", { style: {
                  display: "inline-flex", alignItems: "center", gap: 5,
                  padding: "4px 10px", borderRadius: 999,
                  border: "1px solid " + bf.color + "44", background: bf.color + "18",
                  color: bf.color, fontSize: 11, fontWeight: 700,
                } }, React.createElement(bf.Icon, { size: 12 }), bf.label);
              })(),
              estCostRange(inf.followers_count) && React.createElement("span", { style: {
                display: "inline-flex", alignItems: "center", gap: 5,
                padding: "4px 10px", borderRadius: 999,
                border: "1px solid rgba(15,23,42,0.08)", background: "rgba(15,23,42,0.05)",
                color: "#94a3b8", fontSize: 11, fontWeight: 700,
              } }, React.createElement(L.DollarSign, { size: 12 }), estCostRange(inf.followers_count)),
            ),
          ),
        ),
        React.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 12, alignItems: "flex-end" } },
          activeCampaignId ? React.createElement(AddToCampaignBtn, { inf, activeCampaignId, addToCollabProfile }) : null,
          React.createElement("div", { className: "rf-dials" },
            React.createElement(Dial, { value: inf.ratefluencer_score, label: "Ratefluencer™" }),
            React.createElement(Dial, { value: inf.authenticity_score, label: "Real Audience", color: "#16a34a" }),
            React.createElement(Dial, { value: inf.growth_score, label: "Growth", color: "#2563eb" }),
            React.createElement(Dial, { value: inf.campaign_success_score, label: "Campaign Fit", color: "#db2777" }),
          ),
        ),
      ),

      // ── stats grid ──
      React.createElement("div", { className: "rf-statgrid" },
        React.createElement(StatCard, { icon: L.Users, label: "Followers", value: formatFollowers(inf.followers_count),
          sub: (d7 >= 0 ? "▲ +" : "▼ ") + formatNum(Math.abs(d7)) + " · 7d", subColor: d7 >= 0 ? "#16a34a" : "#dc2626" }),
        React.createElement(StatCard, { icon: erUp ? L.TrendingUp : L.TrendingDown, label: "Engagement Rate", value: fmtPct(inf.engagement_rate),
          sub: (erUp ? "Above" : "Below") + " " + fmtPct(inf.benchmark) + " benchmark", subColor: erUp ? "#16a34a" : "#dc2626" }),
        React.createElement(StatCard, { icon: L.Heart, label: "Avg Likes", value: formatNum(inf.avg_likes) }),
        React.createElement(StatCard, { icon: L.MessageCircle, label: "Avg Comments", value: formatNum(inf.avg_comments) }),
        React.createElement(StatCard, { icon: L.Play, label: "Avg Video Views", value: formatNum(inf.avg_video_views) }),
        React.createElement(StatCard, { icon: L.CalendarClock, label: "Posts / Week", value: inf.posts_per_week }),
        React.createElement(StatCard, { icon: L.Activity, label: "True Engagement", value: fmtPct(inf.true_engagement_rate) }),
        React.createElement(StatCard, { icon: L.Bookmark, label: "Save Rate", value: fmtPct((inf.save_rate || 0) * 100) }),
        React.createElement(StatCard, { icon: L.Share2, label: "Share Rate", value: fmtPct((inf.share_rate || 0) * 100) }),
      ),

      // ── brand match (search only) ──
      fromSearch && inf.brand_match != null ? React.createElement(Section, { icon: L.Target, title: "Why this creator fits your campaign", accent: "#7c3aed",
        sub: "Based on content alignment, audience demographics, and campaign objectives." },
        React.createElement("div", { className: "rf-match-layout" },
          React.createElement("div", { className: "rf-card rf-match-gauge" },
            React.createElement(Dial, { value: inf.brand_match, size: 150, color: "#7c3aed", sub: "match score" }),
            React.createElement("div", { className: "rf-match-verdict" }, inf.brand_match >= 75 ? "🎯 Excellent fit" : inf.brand_match >= 55 ? "👍 Good fit" : "⚠️ Possible fit"),
            inf.expected_outcome ? React.createElement("div", { style: { fontSize: 12, color: "#94a3b8", marginTop: 6, textAlign: "center" } },
              "Expected: ", React.createElement("b", { style: { color: "#0f172a" } }, inf.expected_outcome)) : null,
          ),
          React.createElement("div", { className: "rf-card rf-match-reasons" },
            // Gemini ROI reasoning
            inf.why_good_match ? React.createElement("div", { style: {
              padding: "10px 14px", borderRadius: 8, background: "rgba(124,108,255,0.1)",
              border: "1px solid rgba(124,108,255,0.2)", marginBottom: 12,
              fontSize: 13, color: "#c4b5fd", lineHeight: 1.6
            } }, "✦ ", inf.why_good_match) : null,
            // Audience alignment
            inf.audience_alignment ? React.createElement("div", { style: {
              fontSize: 12, color: "#64748b", marginBottom: 10, display: "flex", alignItems: "center", gap: 6
            } }, React.createElement(L.Users, { size: 13 }),
              "Audience alignment: ",
              React.createElement("b", { style: { color: inf.audience_alignment >= 70 ? "#4ade80" : inf.audience_alignment >= 50 ? "#facc15" : "#f87171" } },
                inf.audience_alignment + "%")) : null,
            // Match reasons from semantic analysis
            (inf.match_reasons || []).map((r, i) => React.createElement("div", { key: "r" + i, className: "rf-reason" },
              React.createElement(L.Check, { size: 15, style: { color: "#16a34a" } }), cleanReason(r))),
            (inf.match_warnings || []).map((w, i) => React.createElement("div", { key: "w" + i, className: "rf-reason" },
              React.createElement(L.AlertTriangle, { size: 15, style: { color: "#d97706" } }), cleanReason(w))),
            // Relevant content they post
            inf.sample_captions && inf.sample_captions.length > 0 ? React.createElement("div", { style: { marginTop: 12 } },
              React.createElement("div", { style: { fontSize: 11, color: "#64748b", fontWeight: 700, textTransform: "uppercase", marginBottom: 8 } }, "Their recent content"),
              inf.sample_captions.slice(0, 2).map((cap, i) => React.createElement("div", { key: i, style: {
                padding: "8px 12px", borderRadius: 7, background: "rgba(15,23,42,0.04)",
                border: "1px solid rgba(15,23,42,0.06)", marginBottom: 6,
                fontSize: 12, color: "#94a3b8", lineHeight: 1.5
              } }, "📹 ", cap))) : null,
            React.createElement("div", { className: "rf-audiencefit" },
              React.createElement("div", { className: "rf-audiencefit-block" },
                React.createElement("div", { className: "rf-mini-label" }, "Audience age"),
                Object.entries(inf.audience.age).map(([k, v]) => React.createElement("div", { key: k, className: "rf-agebar" },
                  React.createElement("span", { className: "rf-agebar-k" }, k),
                  React.createElement("div", { className: "rf-agebar-track" }, React.createElement("div", { className: "rf-agebar-fill", style: { width: v + "%" } })),
                  React.createElement("span", { className: "rf-agebar-v" }, v + "%")))),
              React.createElement("div", { className: "rf-audiencefit-block" },
                React.createElement("div", { className: "rf-mini-label" }, "Top countries"),
                Object.entries(inf.audience.country).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k, v]) =>
                  React.createElement("div", { key: k, className: "rf-country" }, React.createElement(L.MapPin, { size: 13 }), k, React.createElement("b", null, v + "%")))),
            ),
          ),
        )) : null,

      // ── charts ──
      React.createElement(Section, { icon: L.LineChart, title: "Performance trends", accent: "#2563eb",
        sub: "Performance trajectory over the past 30 days." },
        React.createElement("div", { className: "rf-chartgrid" },
          React.createElement(AreaTrend, { data: series.followers, color: "#7c3aed", label: "Followers", sub: formatFollowers(inf.followers_count) + " now", valueFmt: formatFollowers }),
          React.createElement(AreaTrend, { data: series.er, color: "#db2777", label: "Engagement Rate", sub: fmtPct(inf.engagement_rate), valueFmt: (v) => v + "%" }),
          React.createElement(AreaTrend, { data: series.likes, color: "#2563eb", label: "Average Likes", sub: formatNum(inf.avg_likes) + " avg", valueFmt: formatNum }),
          React.createElement(AreaTrend, { data: series.comments, color: "#16a34a", label: "Average Comments", sub: formatNum(inf.avg_comments) + " avg", valueFmt: formatNum }),
        )),

      // ── authenticity ──
      a ? React.createElement(Section, { icon: L.ShieldCheck, title: "Audience Quality Check", accent: "#16a34a",
        sub: "Independent analysis of follower authenticity and engagement health.",
        right: React.createElement("span", { className: "rf-verdict rf-verdict-" + (a.verdict === "Trusted" ? "ok" : a.verdict === "Caution" ? "warn" : "bad") },
          React.createElement(a.verdict === "Trusted" ? L.ShieldCheck : L.ShieldAlert, { size: 15 }),
          a.verdict === "Trusted" ? "Verified" : a.verdict === "Caution" ? "Review Needed" : "Risk Detected") },
        React.createElement("div", { className: "rf-card rf-factors" },
          React.createElement("div", { className: "rf-factorgrid" }, (a.factors || []).map((f) => React.createElement(AuthFactor, { key: f.key, f }))),
        )) : null,

      // ── growth ──
      g && g.followers ? React.createElement(Section, { icon: L.Rocket, title: "Growth Forecast", accent: "#2563eb",
        sub: "Projected follower reach and engagement over the next 90 days." },
        React.createElement("div", { className: "rf-growthcards" },
          [["30d", g.followers["30d"]], ["60d", g.followers["60d"]], ["90d", g.followers["90d"]]].map(([k, v]) =>
            React.createElement("div", { key: k, className: "rf-card rf-growthcard" },
              React.createElement("div", { className: "rf-growth-k" }, "In " + k),
              React.createElement("div", { className: "rf-growth-v" }, formatFollowers(inf.followers_count + (v || 0))),
              React.createElement("div", { className: "rf-growth-delta", style: { color: (v || 0) >= 0 ? "#16a34a" : "#dc2626" } },
                ((v || 0) >= 0 ? "+" : "") + formatNum(v || 0) + " followers"))),
          g.er ? React.createElement("div", { className: "rf-card rf-growthcard rf-growthcard-er" },
            React.createElement("div", { className: "rf-growth-k" }, "ER forecast"),
            React.createElement("div", { className: "rf-er-forecast" },
              React.createElement("div", null, React.createElement("span", { className: "rf-er-f-v" }, (g.er["30d"] || 0) + "%"), React.createElement("span", { className: "rf-er-f-k" }, "30d")),
              React.createElement("div", null, React.createElement("span", { className: "rf-er-f-v" }, (g.er["60d"] || 0) + "%"), React.createElement("span", { className: "rf-er-f-k" }, "60d"))),
          ) : null,
        ),
        React.createElement("div", { className: "rf-card rf-drivers" },
          React.createElement("div", { className: "rf-card-head" }, React.createElement("span", { className: "rf-card-title" }, "Growth drivers")),
          React.createElement("table", { className: "rf-drivertable" },
            React.createElement("tbody", null, (g.drivers || []).map((d, i) => React.createElement("tr", { key: i },
              React.createElement("td", null, d.factor), React.createElement("td", { className: "rf-driver-v" }, d.value))))),
        )) : null,

      // ── hashtags + brands ──
      React.createElement("div", { className: "rf-pilllayout" },
        React.createElement(Section, { icon: L.Hash, title: "Top hashtags", accent: "#0891b2" },
          React.createElement("div", { className: "rf-pillrow" }, (inf.top_hashtags || []).map((h) => React.createElement("span", { key: h, className: "rf-tag" }, h)))),
        React.createElement(Section, { icon: L.Briefcase, title: "Past brand categories", accent: "#d97706" },
          React.createElement("div", { className: "rf-pillrow" }, (inf.past_brand_categories || []).map((c) => React.createElement("span", { key: c, className: "rf-tag rf-tag-brand" }, c)))),
      ),

      // ── Agent 3: Outreach Email ──
      React.createElement(OutreachPanel, { inf, fromSearch, initial, activeCampaignId }),
    );
  }

  function OutreachPanel({ inf, fromSearch, initial, activeCampaignId }) {
    const [open,      setOpen]    = React.useState(false);
    const [loading,   setLoading] = React.useState(false);
    const [email,     setEmail]   = React.useState(null);
    const [copied,    setCopied]  = React.useState(false);
    const [category,  setCategory]= React.useState(initial?.brand_match ? "" : "");

    async function generate() {
      setLoading(true);
      try {
        const res = await fetch(`${window.RFApi.BASE}/api/outreach`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            influencer_id:       inf.id,
            category:            category || inf.niche || "",
            product_description: category || "",
            campaign_goal:       "Awareness",
          }),
        });
        if (!res.ok) throw new Error("Failed");
        const data = await res.json();
        setEmail(data);
        // Auto-update collaboration status → Contacted
        if (activeCampaignId) {
          try {
            var collabs = JSON.parse(localStorage.getItem('rf_collabs') || '[]');
            var key = String(inf.id) + '_' + activeCampaignId;
            var idx = collabs.findIndex(function(c) { return c.id === key; });
            if (idx >= 0 && collabs[idx].status === 'Shortlisted') {
              collabs[idx].status = 'Contacted';
              localStorage.setItem('rf_collabs', JSON.stringify(collabs));
            }
          } catch(ex) {}
        }
      } catch(e) {
        setEmail({ subject: "Error", body: "Could not generate email. Please try again.", hook: "", cta: "" });
      } finally {
        setLoading(false);
      }
    }

    function copyEmail() {
      if (!email) return;
      navigator.clipboard.writeText(`Subject: ${email.subject}\n\n${email.body}`);
      setCopied(true); setTimeout(() => setCopied(false), 2000);
    }

    return React.createElement(Section, { icon: L.Mail, title: "Generate outreach email", accent: "#7c3aed",
      sub: "AI-crafted personalised pitch referencing their actual content." },
      !open
        ? React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 12 } },
            React.createElement("input", {
              className: "rf-input", placeholder: "Your product (e.g. yoga mats, protein powder)",
              value: category, onChange: (e) => setCategory(e.target.value),
              style: { flex: 1 },
            }),
            React.createElement("button", {
              className: "rf-btn rf-btn-primary", type: "button",
              onClick: () => { setOpen(true); generate(); },
              disabled: !category,
              style: { display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap" },
            }, React.createElement(L.Mail, { size: 15 }), "Generate Email"),
          )
        : React.createElement("div", null,
            loading
              ? React.createElement("div", { style: { padding: 20, textAlign: "center", color: "#94a3b8" } },
                  React.createElement("div", { className: "rf-spinner", style: { margin: "0 auto 8px" } }),
                  "Drafting your personalised outreach email…")
              : email && React.createElement("div", null,
                  React.createElement("div", { style: {
                    background: "rgba(124,108,255,0.08)", border: "1px solid rgba(124,108,255,0.2)",
                    borderRadius: 10, padding: 16, marginBottom: 12,
                  } },
                    React.createElement("div", { style: { fontSize: 11, color: "#7c6cff", fontWeight: 700, textTransform: "uppercase", marginBottom: 6 } }, "Subject"),
                    React.createElement("div", { style: { color: "#0f172a", fontWeight: 600, marginBottom: 14 } }, email.subject),
                    React.createElement("div", { style: { fontSize: 11, color: "#7c6cff", fontWeight: 700, textTransform: "uppercase", marginBottom: 6 } }, "Email body"),
                    React.createElement("div", { style: { color: "#334155", fontSize: 13, lineHeight: 1.7, whiteSpace: "pre-wrap" } }, email.body),
                    email.cta && React.createElement("div", { style: {
                      marginTop: 12, padding: "8px 12px", background: "rgba(15,23,42,0.05)",
                      borderRadius: 7, fontSize: 12, color: "#94a3b8",
                    } }, "CTA: ", React.createElement("b", { style: { color: "#0f172a" } }, email.cta)),
                  ),
                  React.createElement("div", { style: { display: "flex", gap: 10 } },
                    React.createElement("button", {
                      className: "rf-btn rf-btn-primary", type: "button", onClick: copyEmail,
                      style: { display: "flex", alignItems: "center", gap: 6 },
                    }, React.createElement(L.Copy, { size: 14 }), copied ? "Copied!" : "Copy Email"),
                    React.createElement("button", {
                      className: "rf-btn rf-btn-ghost", type: "button",
                      onClick: () => { setEmail(null); generate(); },
                    }, React.createElement(L.RotateCcw, { size: 14 }), "Regenerate"),
                    React.createElement("button", {
                      className: "rf-btn rf-btn-ghost", type: "button",
                      onClick: () => { setOpen(false); setEmail(null); },
                    }, "Close"),
                  ),
                ),
          ),
    );
  }

  window.RFProfile = ProfileScreen;
})();
