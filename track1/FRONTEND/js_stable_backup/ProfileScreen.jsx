/* Ratefluencer AI — Screen 3: Influencer Profile Deep Dive */
(function () {
  const { useState, useEffect } = React;
  const RF = window.RF;
  const { L, formatFollowers, formatNum, fmtPct, fmtScore, scoreHex, titleCase, NicheBadge, TierBadge, Avatar, Dial, Skeleton } = RF;
  const { AreaTrend } = window.RFCharts;
  const api = window.RFApi;

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
    let frac;
    if (f.unit === "x") frac = Math.min(100, (f.value / 3) * 100);
    else if (f.signed) frac = Math.min(100, (Math.abs(f.value) / 5) * 100);
    else frac = Math.min(100, f.value);
    const color = f.good ? "#16a34a" : "#dc2626";
    const valTxt = (f.signed && f.value > 0 ? "+" : "") + f.value + (f.unit === "%" ? "%" : f.unit === "x" ? "×" : "");
    return React.createElement("div", { className: "rf-factor" },
      React.createElement("div", { className: "rf-factor-head" },
        React.createElement("span", { className: "rf-factor-label" },
          React.createElement(f.good ? L.CheckCircle2 : L.AlertTriangle, { size: 14, style: { color } }), f.key),
        React.createElement("b", { className: "rf-factor-val", style: { color } }, valTxt)),
      React.createElement("div", { className: "rf-factor-track" },
        React.createElement("div", { className: "rf-factor-fill", style: { width: frac + "%", background: color } })),
    );
  }

  function ProfileScreen({ initial, onBack, fromSearch }) {
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
          ),
        ),
        React.createElement("div", { className: "rf-dials" },
          React.createElement(Dial, { value: inf.ratefluencer_score, label: "Ratefluencer™" }),
          React.createElement(Dial, { value: inf.authenticity_score, label: "Authenticity", color: "#16a34a" }),
          React.createElement(Dial, { value: inf.growth_score, label: "Growth", color: "#2563eb" }),
          React.createElement(Dial, { value: inf.campaign_success_score, label: "Campaign Fit", color: "#db2777" }),
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
        React.createElement(StatCard, { icon: L.Bookmark, label: "Save Rate", value: fmtPct(inf.save_rate) }),
        React.createElement(StatCard, { icon: L.Share2, label: "Share Rate", value: fmtPct(inf.share_rate) }),
      ),

      // ── brand match (search only) ──
      fromSearch && inf.brand_match != null ? React.createElement(Section, { icon: L.Target, title: "Why this influencer fits your campaign", accent: "#7c3aed",
        sub: "AI-scored on content alignment, audience fit, and campaign goals." },
        React.createElement("div", { className: "rf-match-layout" },
          React.createElement("div", { className: "rf-card rf-match-gauge" },
            React.createElement(Dial, { value: inf.brand_match, size: 150, color: "#7c3aed", sub: "match score" }),
            React.createElement("div", { className: "rf-match-verdict" }, inf.brand_match >= 75 ? "🎯 Excellent fit" : inf.brand_match >= 55 ? "👍 Good fit" : "⚠️ Possible fit"),
            inf.expected_outcome ? React.createElement("div", { style: { fontSize: 12, color: "#94a3b8", marginTop: 6, textAlign: "center" } },
              "Expected: ", React.createElement("b", { style: { color: "#e2e8f0" } }, inf.expected_outcome)) : null,
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
              React.createElement(L.Check, { size: 15, style: { color: "#16a34a" } }), r)),
            (inf.match_warnings || []).map((w, i) => React.createElement("div", { key: "w" + i, className: "rf-reason" },
              React.createElement(L.AlertTriangle, { size: 15, style: { color: "#d97706" } }), w)),
            // Relevant content they post
            inf.sample_captions && inf.sample_captions.length > 0 ? React.createElement("div", { style: { marginTop: 12 } },
              React.createElement("div", { style: { fontSize: 11, color: "#64748b", fontWeight: 700, textTransform: "uppercase", marginBottom: 8 } }, "Their recent content"),
              inf.sample_captions.slice(0, 2).map((cap, i) => React.createElement("div", { key: i, style: {
                padding: "8px 12px", borderRadius: 7, background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)", marginBottom: 6,
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
      React.createElement(Section, { icon: L.LineChart, title: "30-day trends", accent: "#2563eb",
        sub: "Simulated daily series from on-platform signals." },
        React.createElement("div", { className: "rf-chartgrid" },
          React.createElement(AreaTrend, { data: series.followers, color: "#7c3aed", label: "Followers", sub: formatFollowers(inf.followers_count) + " now", valueFmt: formatFollowers }),
          React.createElement(AreaTrend, { data: series.er, color: "#db2777", label: "Engagement Rate", sub: fmtPct(inf.engagement_rate), valueFmt: (v) => v + "%" }),
          React.createElement(AreaTrend, { data: series.likes, color: "#2563eb", label: "Average Likes", sub: formatNum(inf.avg_likes) + " avg", valueFmt: formatNum }),
          React.createElement(AreaTrend, { data: series.comments, color: "#16a34a", label: "Average Comments", sub: formatNum(inf.avg_comments) + " avg", valueFmt: formatNum }),
        )),

      // ── authenticity ──
      a ? React.createElement(Section, { icon: L.ShieldCheck, title: "Fake follower detection", accent: "#16a34a",
        sub: "Signals scored to flag inauthentic reach.",
        right: React.createElement("span", { className: "rf-verdict rf-verdict-" + (a.verdict === "Trusted" ? "ok" : a.verdict === "Caution" ? "warn" : "bad") },
          React.createElement(a.verdict === "Trusted" ? L.ShieldCheck : L.ShieldAlert, { size: 15 }), a.verdict) },
        React.createElement("div", { className: "rf-card rf-factors" },
          React.createElement("div", { className: "rf-factorgrid" }, (a.factors || []).map((f) => React.createElement(AuthFactor, { key: f.key, f }))),
        )) : null,

      // ── growth ──
      g && g.followers ? React.createElement(Section, { icon: L.Rocket, title: "Growth prediction", accent: "#2563eb",
        sub: "Forecast follower & engagement trajectory." },
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
      React.createElement(OutreachPanel, { inf, fromSearch, initial }),
    );
  }

  function OutreachPanel({ inf, fromSearch, initial }) {
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
                  "Gemini is drafting a personalised pitch…")
              : email && React.createElement("div", null,
                  React.createElement("div", { style: {
                    background: "rgba(124,108,255,0.08)", border: "1px solid rgba(124,108,255,0.2)",
                    borderRadius: 10, padding: 16, marginBottom: 12,
                  } },
                    React.createElement("div", { style: { fontSize: 11, color: "#7c6cff", fontWeight: 700, textTransform: "uppercase", marginBottom: 6 } }, "Subject"),
                    React.createElement("div", { style: { color: "#e2e8f0", fontWeight: 600, marginBottom: 14 } }, email.subject),
                    React.createElement("div", { style: { fontSize: 11, color: "#7c6cff", fontWeight: 700, textTransform: "uppercase", marginBottom: 6 } }, "Email body"),
                    React.createElement("div", { style: { color: "#cbd5e1", fontSize: 13, lineHeight: 1.7, whiteSpace: "pre-wrap" } }, email.body),
                    email.cta && React.createElement("div", { style: {
                      marginTop: 12, padding: "8px 12px", background: "rgba(255,255,255,0.05)",
                      borderRadius: 7, fontSize: 12, color: "#94a3b8",
                    } }, "CTA: ", React.createElement("b", { style: { color: "#e2e8f0" } }, email.cta)),
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
